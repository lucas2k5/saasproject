from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.db.session import get_db, SessionLocal
from app.api.deps import get_current_user
from app.db.models import User, Order, OrderItem, Customer, Channel, Store, Product
from app.services.lifecycle_service import update_summary_for_customers

router = APIRouter()

BATCH_LIMIT = 5000  # linhas desnormalizadas (itens)


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class OrderRowItem(BaseModel):
    """Uma linha do CSV desnormalizado: cabeçalho do pedido + um item."""
    # Pedido
    order_id: str
    customer_ref: str                      # customer_id OU customer_add_id
    channel_id: Optional[str] = None
    store_id: Optional[str] = None
    status: str = "delivered"
    ordered_at: datetime
    gross_value: float = 0
    discount_value: float = 0
    tax_value: float = 0
    net_value: float = 0
    # Item
    product_external_id: str
    quantity: int = 1
    unit_price: float = 0
    discount_amount: float = 0
    tax_amount: float = 0
    net_price: float = 0
    is_promo: bool = False


class BatchResponse(BaseModel):
    orders_created: int
    orders_updated: int
    items_replaced: int
    errors: List[str] = []


# ------------------------------------------------------------------ #
# POST /batch  — upsert desnormalizado
# ------------------------------------------------------------------ #

@router.post("/batch", response_model=BatchResponse)
def upsert_orders_batch(
    rows: List[OrderRowItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(rows) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} linhas por chamada.")

    tenant_id = current_user.tenant_id
    errors: List[str] = []

    # ---- Pré-carrega lookups ----
    customer_refs = {r.customer_ref for r in rows}
    customers_by_ref = {}
    for c in db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.customer_id.in_(customer_refs)
    ).all():
        customers_by_ref[c.customer_id] = c.id
    for c in db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.customer_add_id.in_(customer_refs)
    ).all():
        customers_by_ref.setdefault(c.customer_add_id, c.id)

    channel_ext_ids = {r.channel_id for r in rows if r.channel_id}
    channel_map = {}
    if channel_ext_ids:
        for ch in db.query(Channel).filter(
            Channel.tenant_id == tenant_id,
            Channel.channel_id.in_(channel_ext_ids)
        ).all():
            channel_map[ch.channel_id] = ch.id

    store_ext_ids = {r.store_id for r in rows if r.store_id}
    store_map = {}
    if store_ext_ids:
        for s in db.query(Store).filter(
            Store.tenant_id == tenant_id,
            Store.store_id.in_(store_ext_ids)
        ).all():
            store_map[s.store_id] = s.id

    product_ext_ids = {r.product_external_id for r in rows}
    product_map = {}
    for p in db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.external_id.in_(product_ext_ids)
    ).all():
        product_map[p.external_id] = p.id

    # ---- Agrupa linhas por order_id ----
    orders_dict: dict = {}
    for row in rows:
        if row.order_id not in orders_dict:
            orders_dict[row.order_id] = {"header": row, "items": []}
        orders_dict[row.order_id]["items"].append(row)

    # ---- Busca pedidos existentes para saber created vs updated ----
    existing_order_ids = set(
        r.order_id for r in db.query(Order.order_id).filter(
            Order.tenant_id == tenant_id,
            Order.order_id.in_(orders_dict.keys())
        ).all()
    )

    orders_created = 0
    orders_updated = 0
    items_replaced = 0

    for order_id, data in orders_dict.items():
        header = data["header"]
        items = data["items"]

        customer_uuid = customers_by_ref.get(header.customer_ref)
        if not customer_uuid:
            errors.append(f"Pedido {order_id}: cliente não encontrado '{header.customer_ref}'")
            continue

        channel_uuid = channel_map.get(header.channel_id) if header.channel_id else None
        store_uuid = store_map.get(header.store_id) if header.store_id else None

        # Upsert do pedido
        order_uuid: uuid.UUID
        if order_id in existing_order_ids:
            order = db.query(Order).filter(
                Order.tenant_id == tenant_id,
                Order.order_id == order_id
            ).first()
            order.customer_id = customer_uuid
            order.channel_id = channel_uuid
            order.store_id = store_uuid
            order.status = header.status
            order.gross_value = header.gross_value
            order.discount_value = header.discount_value
            order.tax_value = header.tax_value
            order.net_value = header.net_value
            order.ordered_at = header.ordered_at
            order_uuid = order.id
            orders_updated += 1
        else:
            order_uuid = uuid.uuid4()
            db.add(Order(
                id=order_uuid,
                tenant_id=tenant_id,
                order_id=order_id,
                customer_id=customer_uuid,
                channel_id=channel_uuid,
                store_id=store_uuid,
                status=header.status,
                gross_value=header.gross_value,
                discount_value=header.discount_value,
                tax_value=header.tax_value,
                net_value=header.net_value,
                ordered_at=header.ordered_at,
            ))
            orders_created += 1

        # Full replace dos itens do pedido
        db.query(OrderItem).filter(OrderItem.order_id == order_uuid).delete(synchronize_session=False)

        for item in items:
            db.add(OrderItem(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                order_id=order_uuid,
                product_id=product_map.get(item.product_external_id),
                product_external_id=item.product_external_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                tax_amount=item.tax_amount,
                net_price=item.net_price,
                is_promo=item.is_promo,
            ))
            items_replaced += 1

    db.commit()  # Tx1: pedidos + itens

    # Tx2: atualiza summary dos clientes afetados (transação separada)
    affected_customer_uuids = list({
        customers_by_ref[data["header"].customer_ref]
        for data in orders_dict.values()
        if data["header"].customer_ref in customers_by_ref
    })
    if affected_customer_uuids:
        db_tx2 = SessionLocal()
        try:
            update_summary_for_customers(db_tx2, tenant_id, affected_customer_uuids)
        except Exception:
            import logging
            logging.getLogger(__name__).warning(
                "Tx2 summary falhou (tenant=%s) — job diário corrige", tenant_id
            )
        finally:
            db_tx2.close()

    return BatchResponse(
        orders_created=orders_created,
        orders_updated=orders_updated,
        items_replaced=items_replaced,
        errors=errors,
    )


# ------------------------------------------------------------------ #
# GET /
# ------------------------------------------------------------------ #

@router.get("/")
def list_orders(
    customer_ref: Optional[str] = None,
    status: Optional[str] = None,
    product_external_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if limit > 1000:
        raise HTTPException(422, "limit máximo é 1000")

    tenant_id = current_user.tenant_id
    query = db.query(Order).filter(Order.tenant_id == tenant_id)

    if status:
        query = query.filter(Order.status == status)

    if product_external_id:
        subq = db.query(OrderItem.order_id).filter(
            OrderItem.tenant_id == tenant_id,
            OrderItem.product_external_id == product_external_id
        ).subquery()
        query = query.filter(Order.id.in_(subq))

    if customer_ref:
        customer = db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            (Customer.customer_id == customer_ref) | (Customer.customer_add_id == customer_ref)
        ).first()
        if customer:
            query = query.filter(Order.customer_id == customer.id)
        else:
            return {"items": [], "total": 0, "skip": skip, "limit": limit}

    total = query.count()
    orders = query.order_by(Order.ordered_at.desc()).offset(skip).limit(limit).all()

    order_uuids = [o.id for o in orders]
    items = db.query(OrderItem).filter(OrderItem.order_id.in_(order_uuids)).all() if order_uuids else []
    items_by_order: dict = {}
    for item in items:
        items_by_order.setdefault(item.order_id, []).append(item)

    result = []
    for o in orders:
        order_items = items_by_order.get(o.id, [])
        result.append({
            "order_id": o.order_id,
            "customer_id": str(o.customer_id) if o.customer_id else None,
            "status": o.status,
            "ordered_at": o.ordered_at,
            "gross_value": o.gross_value,
            "discount_value": o.discount_value,
            "tax_value": o.tax_value,
            "net_value": o.net_value,
            "items_count": len(order_items),
            "items": [
                {
                    "product_external_id": i.product_external_id,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "discount_amount": i.discount_amount,
                    "tax_amount": i.tax_amount,
                    "net_price": i.net_price,
                    "is_promo": i.is_promo,
                }
                for i in order_items
            ],
        })

    return {"items": result, "total": total, "skip": skip, "limit": limit}
