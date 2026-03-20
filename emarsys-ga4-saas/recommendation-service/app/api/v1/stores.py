from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, Store

router = APIRouter()

BATCH_LIMIT = 1000


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class StoreBatchItem(BaseModel):
    store_id: str
    name: str
    address: Optional[str] = None
    is_active: bool = True


class StorePatchItem(BaseModel):
    store_id: str
    name: Optional[str] = None
    is_active: Optional[bool] = None


class StoreDeleteRequest(BaseModel):
    store_ids: List[str]


class StoreResponse(BaseModel):
    id: str
    tenant_id: str
    store_id: str
    name: str
    address: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    created: int
    updated: int
    unchanged: int
    errors: List[str] = []


# ------------------------------------------------------------------ #
# GET
# ------------------------------------------------------------------ #

@router.get("/", response_model=List[StoreResponse])
def list_stores(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if limit > BATCH_LIMIT:
        raise HTTPException(422, f"limit máximo é {BATCH_LIMIT}")
    return db.query(Store).filter(
        Store.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()


@router.get("/{store_id}", response_model=StoreResponse)
def get_store(
    store_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    store = db.query(Store).filter(
        Store.tenant_id == current_user.tenant_id,
        Store.store_id == store_id
    ).first()
    if not store:
        raise HTTPException(404, "Loja não encontrada")
    return store


# ------------------------------------------------------------------ #
# POST /batch
# ------------------------------------------------------------------ #

@router.post("/batch", response_model=BatchResponse)
def upsert_stores_batch(
    items: List[StoreBatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} lojas por chamada.")

    tenant_id = current_user.tenant_id
    store_ids = [i.store_id for i in items]

    existing = db.query(Store.store_id).filter(
        Store.tenant_id == tenant_id,
        Store.store_id.in_(store_ids)
    ).all()
    existing_set = {row.store_id for row in existing}

    records = [
        {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "store_id": i.store_id,
            "name": i.name,
            "address": i.address,
            "is_active": i.is_active,
        }
        for i in items
    ]

    stmt = pg_insert(Store).values(records)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_store_tenant_storeid',
        set_={
            "name": stmt.excluded.name,
            "address": stmt.excluded.address,
            "is_active": stmt.excluded.is_active,
        }
    )
    db.execute(stmt)
    db.commit()

    incoming_set = set(store_ids)
    return BatchResponse(
        created=len(incoming_set - existing_set),
        updated=len(incoming_set & existing_set),
        unchanged=0
    )


# ------------------------------------------------------------------ #
# PATCH /batch
# ------------------------------------------------------------------ #

@router.patch("/batch", response_model=BatchResponse)
def patch_stores_batch(
    items: List[StorePatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} lojas por chamada.")

    store_ids = [i.store_id for i in items]
    existing = db.query(Store).filter(
        Store.tenant_id == current_user.tenant_id,
        Store.store_id.in_(store_ids)
    ).all()
    existing_map = {s.store_id: s for s in existing}

    updated = 0
    errors = []

    for item in items:
        store = existing_map.get(item.store_id)
        if not store:
            errors.append(f"Loja não encontrada: {item.store_id}")
            continue
        if item.name is not None:
            store.name = item.name
        if item.is_active is not None:
            store.is_active = item.is_active
        updated += 1

    db.commit()
    return BatchResponse(created=0, updated=updated, unchanged=0, errors=errors)


# ------------------------------------------------------------------ #
# DELETE /batch
# ------------------------------------------------------------------ #

@router.delete("/batch", response_model=BatchResponse)
def delete_stores_batch(
    body: StoreDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(body.store_ids) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} lojas por chamada.")

    db.query(Store).filter(
        Store.tenant_id == current_user.tenant_id,
        Store.store_id.in_(body.store_ids)
    ).delete(synchronize_session=False)

    db.commit()
    return BatchResponse(created=0, updated=0, unchanged=0)
