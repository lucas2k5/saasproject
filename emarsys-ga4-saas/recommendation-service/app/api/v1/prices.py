from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, Product, Channel, Store, ProductPrice

router = APIRouter()

BATCH_LIMIT = 1000


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class PriceBatchItem(BaseModel):
    product_external_id: str    # SKU do produto
    channel_id: str             # channel_id externo
    store_id: str               # obrigatório — todo preço deve estar vinculado a uma loja
    price: float


class PricePatchItem(BaseModel):
    product_external_id: str
    channel_id: str
    store_id: str
    price: float


class PriceDeleteItem(BaseModel):
    product_external_id: str
    channel_id: str
    store_id: str


class PriceDeleteRequest(BaseModel):
    items: List[PriceDeleteItem]


class PriceResponse(BaseModel):
    id: str
    product_id: str
    channel_id: str
    store_id: Optional[str]
    price: float

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    created: int
    updated: int
    unchanged: int
    errors: List[str] = []


# ------------------------------------------------------------------ #
# Helpers — resolve external IDs para UUIDs internos
# ------------------------------------------------------------------ #

def _resolve_refs(items: list, tenant_id: str, db: Session):
    """Retorna (product_map, channel_map, store_map) por external_id."""
    product_ext_ids = list({i.product_external_id for i in items})
    channel_ext_ids = list({i.channel_id for i in items})
    store_ext_ids = list({i.store_id for i in items if i.store_id})

    products = db.query(Product.external_id, Product.id).filter(
        Product.tenant_id == tenant_id,
        Product.external_id.in_(product_ext_ids)
    ).all()

    channels = db.query(Channel.channel_id, Channel.id).filter(
        Channel.tenant_id == tenant_id,
        Channel.channel_id.in_(channel_ext_ids)
    ).all()

    stores = db.query(Store.store_id, Store.id).filter(
        Store.tenant_id == tenant_id,
        Store.store_id.in_(store_ext_ids)
    ).all() if store_ext_ids else []

    return (
        {row.external_id: row.id for row in products},
        {row.channel_id: row.id for row in channels},
        {row.store_id: row.id for row in stores},
    )


# ------------------------------------------------------------------ #
# GET
# ------------------------------------------------------------------ #

@router.get("/", response_model=List[PriceResponse])
def list_prices(
    product_external_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if limit > BATCH_LIMIT:
        raise HTTPException(422, f"limit máximo é {BATCH_LIMIT}")

    query = db.query(ProductPrice).filter(ProductPrice.tenant_id == current_user.tenant_id)

    if product_external_id:
        product = db.query(Product.id).filter(
            Product.tenant_id == current_user.tenant_id,
            Product.external_id == product_external_id
        ).first()
        if product:
            query = query.filter(ProductPrice.product_id == product.id)

    if channel_id:
        channel = db.query(Channel.id).filter(
            Channel.tenant_id == current_user.tenant_id,
            Channel.channel_id == channel_id
        ).first()
        if channel:
            query = query.filter(ProductPrice.channel_id == channel.id)

    return query.offset(skip).limit(limit).all()


# ------------------------------------------------------------------ #
# POST /batch
# ------------------------------------------------------------------ #

@router.post("/batch", response_model=BatchResponse)
def upsert_prices_batch(
    items: List[PriceBatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} preços por chamada.")

    tenant_id = current_user.tenant_id
    product_map, channel_map, store_map = _resolve_refs(items, tenant_id, db)

    records = []
    errors = []

    for item in items:
        prod_id = product_map.get(item.product_external_id)
        chan_id = channel_map.get(item.channel_id)
        if not prod_id:
            errors.append(f"Produto não encontrado: {item.product_external_id}")
            continue
        if not chan_id:
            errors.append(f"Canal não encontrado: {item.channel_id}")
            continue

        store_uuid = store_map.get(item.store_id)
        if not store_uuid:
            errors.append(f"Loja não encontrada: {item.store_id}")
            continue

        records.append({
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "product_id": prod_id,
            "channel_id": chan_id,
            "store_id": store_uuid,
            "price": item.price,
        })

    if records:
        stmt = pg_insert(ProductPrice).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint='uq_price_product_channel_store',
            set_={"price": stmt.excluded.price}
        )
        db.execute(stmt)
        db.commit()

    return BatchResponse(created=len(records), updated=0, unchanged=0, errors=errors)


# ------------------------------------------------------------------ #
# PATCH /batch  (mesmo comportamento do POST para preços — só preço muda)
# ------------------------------------------------------------------ #

@router.patch("/batch", response_model=BatchResponse)
def patch_prices_batch(
    items: List[PricePatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Preço não tem campos parciais — delega ao upsert
    return upsert_prices_batch(items, db, current_user)


# ------------------------------------------------------------------ #
# DELETE /batch
# ------------------------------------------------------------------ #

@router.delete("/batch", response_model=BatchResponse)
def delete_prices_batch(
    body: PriceDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(body.items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} preços por chamada.")

    tenant_id = current_user.tenant_id
    product_map, channel_map, store_map = _resolve_refs(body.items, tenant_id, db)

    errors = []
    deleted = 0

    for item in body.items:
        prod_id = product_map.get(item.product_external_id)
        chan_id = channel_map.get(item.channel_id)
        if not prod_id or not chan_id:
            errors.append(f"Referência não encontrada: {item.product_external_id} / {item.channel_id}")
            continue

        store_uuid = store_map.get(item.store_id)
        if not store_uuid:
            errors.append(f"Loja não encontrada: {item.store_id}")
            continue

        q = db.query(ProductPrice).filter(
            ProductPrice.tenant_id == tenant_id,
            ProductPrice.product_id == prod_id,
            ProductPrice.channel_id == chan_id,
            ProductPrice.store_id == store_uuid,
        )
        deleted += q.delete(synchronize_session=False)

    db.commit()
    return BatchResponse(created=0, updated=0, unchanged=0, errors=errors)
