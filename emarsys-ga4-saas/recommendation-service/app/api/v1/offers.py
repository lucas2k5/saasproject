from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, Offer, OfferProduct, OfferAudience, Product, Customer, VALID_OFFER_TYPES
from app.services.offer_utils import compute_promo_price

router = APIRouter()


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class OfferBatchItem(BaseModel):
    offer_id: str
    name: str
    type: str                               # Ver VALID_OFFER_TYPES em models.py
    mechanic_params: Dict[str, Any]
    trigger_products: List[str] = []        # SKUs dos produtos em promoção
    reward_products: List[str] = []         # SKUs do brinde/desconto (BUY_X_GET_Y e COMBO)
    start_at: datetime
    end_at: datetime
    channel_ids: List[str] = []             # IDs externos; vazio = todos
    store_ids: List[str] = []               # IDs externos; vazio = todas
    audience_type: str = "ALL"              # ALL | CUSTOMER_IDS | CUSTOMER_TYPE | LIFECYCLE_SEGMENT
    audience_value: List[str] = []          # refs de clientes (customer_id OU customer_add_id), tipos ou segmentos
    priority: int = 0


class OfferProductOut(BaseModel):
    product_external_id: str
    product_name: str
    base_price: float
    promo_price: float
    role: str


class OfferOut(BaseModel):
    offer_id: str
    name: str
    type: str
    mechanic_params: Dict[str, Any]
    products: List[OfferProductOut]
    start_at: datetime
    end_at: datetime
    channel_ids: Optional[List[str]]
    store_ids: Optional[List[str]]
    audience_type: str
    priority: int


class BatchInsertResponse(BaseModel):
    inserted: int
    errors: List[str] = []


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


# compute_promo_price importado de app.services.offer_utils


def _audience_applies(audience_type: str, audience_value: list,
                      customer_id: Optional[str], customer_add_id: Optional[str]) -> bool:
    if audience_type == "ALL":
        return True
    if audience_type == "CUSTOMER_IDS":
        refs = set(audience_value or [])
        return (customer_id and customer_id in refs) or (customer_add_id and customer_add_id in refs)
    # CUSTOMER_TYPE e LIFECYCLE_SEGMENT resolvidos externamente (fase 2)
    return False


# ------------------------------------------------------------------ #
# POST /batch  — full replace
# ------------------------------------------------------------------ #

@router.post("/batch", response_model=BatchInsertResponse)
def replace_offers_batch(
    items: List[OfferBatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id
    errors: List[str] = []

    # Validações básicas
    for item in items:
        if item.end_at <= item.start_at:
            errors.append(f"Oferta {item.offer_id}: end_at deve ser posterior a start_at")
        if item.type not in VALID_OFFER_TYPES:
            errors.append(
                f"Oferta {item.offer_id}: tipo '{item.type}' inválido. "
                f"Tipos aceitos: {', '.join(sorted(VALID_OFFER_TYPES))}"
            )

    if errors:
        raise HTTPException(422, detail=errors)

    # Pré-carrega produtos do tenant para resolver SKUs
    all_skus = set()
    for item in items:
        all_skus.update(item.trigger_products)
        all_skus.update(item.reward_products)

    product_map: dict = {}
    if all_skus:
        rows = db.query(Product.external_id, Product.id).filter(
            Product.tenant_id == tenant_id,
            Product.external_id.in_(all_skus)
        ).all()
        product_map = {r.external_id: r.id for r in rows}

    # Full replace dentro de transação explícita (savepoint) para atomicidade
    try:
        nested = db.begin_nested()

        db.query(Offer).filter(Offer.tenant_id == tenant_id).delete(synchronize_session=False)

        inserted = 0
        for item in items:
            offer_uuid = uuid.uuid4()
            offer = Offer(
                id=offer_uuid,
                tenant_id=tenant_id,
                offer_id=item.offer_id,
                name=item.name,
                type=item.type,
                mechanic_params=item.mechanic_params,
                channel_ids=item.channel_ids or None,
                store_ids=item.store_ids or None,
                start_at=item.start_at,
                end_at=item.end_at,
                priority=item.priority,
            )
            db.add(offer)

            # Produtos trigger
            for sku in item.trigger_products:
                pid = product_map.get(sku)
                if not pid:
                    errors.append(f"Oferta {item.offer_id}: produto não encontrado '{sku}'")
                    continue
                db.add(OfferProduct(offer_id=offer_uuid, product_id=pid, role="TRIGGER"))

            # Produtos reward (BUY_X_GET_Y, COMBO)
            for sku in item.reward_products:
                pid = product_map.get(sku)
                if not pid:
                    errors.append(f"Oferta {item.offer_id}: produto reward não encontrado '{sku}'")
                    continue
                db.add(OfferProduct(offer_id=offer_uuid, product_id=pid, role="REWARD"))

            # Audiência
            db.add(OfferAudience(
                offer_id=offer_uuid,
                audience_type=item.audience_type,
                audience_value=item.audience_value or None,
            ))

            inserted += 1

        nested.commit()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(500, detail="Falha ao substituir ofertas. Nenhuma oferta foi alterada.")

    return BatchInsertResponse(inserted=inserted, errors=errors)


# ------------------------------------------------------------------ #
# GET /active  — ofertas em vigor agora
# ------------------------------------------------------------------ #

@router.get("/active", response_model=List[OfferOut])
def get_active_offers(
    channel_id: Optional[str] = None,
    store_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    customer_add_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id
    now = datetime.now(timezone.utc)

    offers = db.query(Offer).filter(
        Offer.tenant_id == tenant_id,
        Offer.start_at <= now,
        Offer.end_at >= now,
    ).all()

    # Carrega audiências de uma vez
    offer_ids = [o.id for o in offers]
    audiences = db.query(OfferAudience).filter(
        OfferAudience.offer_id.in_(offer_ids)
    ).all() if offer_ids else []
    audience_map: dict = {}
    for a in audiences:
        audience_map.setdefault(a.offer_id, []).append(a)

    # Carrega produtos de uma vez
    op_rows = db.query(OfferProduct, Product).join(
        Product, OfferProduct.product_id == Product.id
    ).filter(OfferProduct.offer_id.in_(offer_ids)).all() if offer_ids else []
    products_map: dict = {}
    for op_row, prod in op_rows:
        products_map.setdefault(op_row.offer_id, []).append((op_row, prod))

    result = []
    for offer in offers:
        # Filtro de canal
        if offer.channel_ids and channel_id and channel_id not in offer.channel_ids:
            continue
        # Filtro de loja
        if offer.store_ids and store_id and store_id not in offer.store_ids:
            continue

        # Filtro de audiência
        auds = audience_map.get(offer.id, [])
        if not auds:
            continue  # oferta sem audiência definida é ignorada

        audience_ok = False
        for aud in auds:
            if _audience_applies(aud.audience_type, aud.audience_value or [],
                                  customer_id, customer_add_id):
                audience_ok = True
                audience_type_label = aud.audience_type
                break
        if not audience_ok:
            continue

        # Monta produtos com promo_price
        prods_out = []
        for op_row, prod in products_map.get(offer.id, []):
            promo_price = compute_promo_price(offer.type, offer.mechanic_params, prod.price or 0)
            prods_out.append(OfferProductOut(
                product_external_id=prod.external_id,
                product_name=prod.name,
                base_price=prod.price or 0,
                promo_price=promo_price,
                role=op_row.role,
            ))

        result.append(OfferOut(
            offer_id=offer.offer_id,
            name=offer.name,
            type=offer.type,
            mechanic_params=offer.mechanic_params,
            products=prods_out,
            start_at=offer.start_at,
            end_at=offer.end_at,
            channel_ids=offer.channel_ids,
            store_ids=offer.store_ids,
            audience_type=audience_type_label,
            priority=offer.priority,
        ))

    # Ordena por prioridade decrescente
    result.sort(key=lambda o: -o.priority)
    return result


# ------------------------------------------------------------------ #
# GET /  — listagem completa (admin)
# ------------------------------------------------------------------ #

@router.get("/", response_model=List[OfferOut])
def list_offers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id
    limit = min(limit, 200)
    offers = db.query(Offer).filter(Offer.tenant_id == tenant_id).offset(skip).limit(limit).all()

    offer_ids = [o.id for o in offers]
    audiences = db.query(OfferAudience).filter(
        OfferAudience.offer_id.in_(offer_ids)
    ).all() if offer_ids else []
    audience_map: dict = {}
    for a in audiences:
        audience_map.setdefault(a.offer_id, []).append(a)

    op_rows = db.query(OfferProduct, Product).join(
        Product, OfferProduct.product_id == Product.id
    ).filter(OfferProduct.offer_id.in_(offer_ids)).all() if offer_ids else []
    products_map: dict = {}
    for op_row, prod in op_rows:
        products_map.setdefault(op_row.offer_id, []).append((op_row, prod))

    result = []
    for offer in offers:
        auds = audience_map.get(offer.id, [])
        audience_type_label = auds[0].audience_type if auds else "ALL"

        prods_out = []
        for op_row, prod in products_map.get(offer.id, []):
            promo_price = compute_promo_price(offer.type, offer.mechanic_params, prod.price or 0)
            prods_out.append(OfferProductOut(
                product_external_id=prod.external_id,
                product_name=prod.name,
                base_price=prod.price or 0,
                promo_price=promo_price,
                role=op_row.role,
            ))

        result.append(OfferOut(
            offer_id=offer.offer_id,
            name=offer.name,
            type=offer.type,
            mechanic_params=offer.mechanic_params,
            products=prods_out,
            start_at=offer.start_at,
            end_at=offer.end_at,
            channel_ids=offer.channel_ids,
            store_ids=offer.store_ids,
            audience_type=audience_type_label,
            priority=offer.priority,
        ))

    return result
