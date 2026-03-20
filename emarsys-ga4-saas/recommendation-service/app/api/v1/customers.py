from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid

from sqlalchemy import or_
from app.db.session import get_db
from app.api.deps import get_current_user, resolve_customer
from app.db.models import User, Customer, CustomerSegment

router = APIRouter()

BATCH_LIMIT = 1000


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class CustomerBatchItem(BaseModel):
    customer_id: str
    name: str
    customer_add_id: Optional[str] = None
    document: Optional[str] = None
    customer_type: Optional[str] = None
    source_created_at: Optional[datetime] = None


class CustomerPatchItem(BaseModel):
    customer_id: str
    name: Optional[str] = None
    customer_add_id: Optional[str] = None
    document: Optional[str] = None
    customer_type: Optional[str] = None
    source_created_at: Optional[datetime] = None


class CustomerDeleteRequest(BaseModel):
    customer_ids: List[str]


class BatchResponse(BaseModel):
    created: int
    updated: int
    unchanged: int
    errors: List[str] = []


def _serialize_customer(c: Customer) -> dict:
    return {
        "id": str(c.id),
        "tenant_id": str(c.tenant_id),
        "customer_id": c.customer_id,
        "customer_add_id": c.customer_add_id,
        "name": c.name,
        "document": c.document,
        "customer_type": c.customer_type,
        "source_created_at": c.source_created_at,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


# ------------------------------------------------------------------ #
# GET
# ------------------------------------------------------------------ #

@router.get("/")
def list_customers(
    q: Optional[str] = None,
    customer_type: Optional[str] = None,
    lifecycle_segment: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if limit > BATCH_LIMIT:
        raise HTTPException(422, f"limit máximo é {BATCH_LIMIT}")

    tenant_id = current_user.tenant_id
    query = db.query(Customer).filter(Customer.tenant_id == tenant_id)

    if q:
        safe_q = q.replace("%", r"\%").replace("_", r"\_")
        query = query.filter(or_(
            Customer.name.ilike(f"%{safe_q}%", escape="\\"),
            Customer.customer_id.ilike(f"%{safe_q}%", escape="\\"),
            Customer.customer_add_id.ilike(f"%{safe_q}%", escape="\\"),
        ))
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)
    if lifecycle_segment:
        seg_subq = (
            db.query(CustomerSegment.customer_id)
            .filter(
                CustomerSegment.tenant_id == tenant_id,
                CustomerSegment.lifecycle_segment == lifecycle_segment,
            )
            .subquery()
        )
        query = query.filter(Customer.id.in_(seg_subq))

    total = query.count()
    customers = query.order_by(Customer.name).offset(skip).limit(limit).all()

    return {"items": [_serialize_customer(c) for c in customers], "total": total, "skip": skip, "limit": limit}


@router.get("/{customer_ref}")
def get_customer(
    customer_ref: str,
    id_type: str = "customer_id",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = resolve_customer(db, current_user.tenant_id, customer_ref, id_type)
    return _serialize_customer(customer)


# ------------------------------------------------------------------ #
# POST /batch  (upsert)
# ------------------------------------------------------------------ #

@router.post("/batch", response_model=BatchResponse)
def upsert_customers_batch(
    items: List[CustomerBatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} clientes por chamada.")

    customer_ids = [i.customer_id for i in items]
    existing = db.query(Customer.customer_id).filter(
        Customer.tenant_id == current_user.tenant_id,
        Customer.customer_id.in_(customer_ids)
    ).all()
    existing_set = {row.customer_id for row in existing}

    records = []
    for item in items:
        records.append({
            "id": uuid.uuid4(),
            "tenant_id": current_user.tenant_id,
            "customer_id": item.customer_id,
            "customer_add_id": item.customer_add_id,
            "name": item.name,
            "document": item.document,
            "customer_type": item.customer_type,
            "source_created_at": item.source_created_at,
        })

    stmt = pg_insert(Customer).values(records)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_customer_tenant_customerid',
        set_={
            "customer_add_id": stmt.excluded.customer_add_id,
            "name": stmt.excluded.name,
            "document": stmt.excluded.document,
            "customer_type": stmt.excluded.customer_type,
            "source_created_at": stmt.excluded.source_created_at,
        }
    )
    db.execute(stmt)
    db.commit()

    incoming_set = set(customer_ids)
    created = len(incoming_set - existing_set)
    updated = len(incoming_set & existing_set)

    return BatchResponse(created=created, updated=updated, unchanged=0)


# ------------------------------------------------------------------ #
# PATCH /batch  (atualização parcial)
# ------------------------------------------------------------------ #

@router.patch("/batch", response_model=BatchResponse)
def patch_customers_batch(
    items: List[CustomerPatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} clientes por chamada.")

    customer_ids = [i.customer_id for i in items]
    existing = db.query(Customer).filter(
        Customer.tenant_id == current_user.tenant_id,
        Customer.customer_id.in_(customer_ids)
    ).all()
    existing_map = {c.customer_id: c for c in existing}

    updated = 0
    errors = []

    for item in items:
        customer = existing_map.get(item.customer_id)
        if not customer:
            errors.append(f"Cliente não encontrado: {item.customer_id}")
            continue

        if item.name is not None:
            customer.name = item.name
        if item.customer_add_id is not None:
            customer.customer_add_id = item.customer_add_id
        if item.document is not None:
            customer.document = item.document
        if item.customer_type is not None:
            customer.customer_type = item.customer_type
        if item.source_created_at is not None:
            customer.source_created_at = item.source_created_at

        updated += 1

    db.commit()
    return BatchResponse(created=0, updated=updated, unchanged=0, errors=errors)


# ------------------------------------------------------------------ #
# DELETE /batch
# ------------------------------------------------------------------ #

@router.delete("/batch", response_model=BatchResponse)
def delete_customers_batch(
    body: CustomerDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(body.customer_ids) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} clientes por chamada.")

    db.query(Customer).filter(
        Customer.tenant_id == current_user.tenant_id,
        Customer.customer_id.in_(body.customer_ids)
    ).delete(synchronize_session=False)

    db.commit()
    return BatchResponse(created=0, updated=0, unchanged=0)
