from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, Channel, Store, ChannelStore

router = APIRouter()

BATCH_LIMIT = 1000


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class StoreInChannel(BaseModel):
    store_id: str
    name: str


class ChannelBatchItem(BaseModel):
    channel_id: str
    name: str
    type: str
    store_mode: str = "single"      # single | multi
    is_active: bool = True
    stores: List[StoreInChannel] = []


class ChannelPatchItem(BaseModel):
    channel_id: str
    name: Optional[str] = None
    type: Optional[str] = None
    store_mode: Optional[str] = None
    is_active: Optional[bool] = None
    stores: Optional[List[StoreInChannel]] = None   # None = não mexe nos vínculos


class ChannelDeleteRequest(BaseModel):
    channel_ids: List[str]


class ChannelResponse(BaseModel):
    id: str
    tenant_id: str
    channel_id: str
    name: str
    type: str
    store_mode: str
    is_active: bool

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    created: int
    updated: int
    unchanged: int
    errors: List[str] = []


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _sync_channel_stores(channel_uuid: uuid.UUID, stores: List[StoreInChannel],
                          tenant_id: str, db: Session):
    """Upserta lojas e recria vínculos do canal."""
    if not stores:
        return

    # Upsert das lojas
    store_records = [
        {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "store_id": s.store_id,
            "name": s.name,
        }
        for s in stores
    ]
    stmt = pg_insert(Store).values(store_records)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_store_tenant_storeid',
        set_={"name": stmt.excluded.name}
    )
    db.execute(stmt)
    db.flush()

    # Carrega UUIDs das lojas recém upsertadas
    store_ids_ext = [s.store_id for s in stores]
    db_stores = db.query(Store.id, Store.store_id).filter(
        Store.tenant_id == tenant_id,
        Store.store_id.in_(store_ids_ext)
    ).all()
    store_uuid_map = {row.store_id: row.id for row in db_stores}

    # Remove vínculos anteriores e recria
    db.query(ChannelStore).filter(ChannelStore.channel_id == channel_uuid).delete(
        synchronize_session=False
    )
    if store_uuid_map:
        link_records = [
            {
                "id": uuid.uuid4(),
                "tenant_id": tenant_id,
                "channel_id": channel_uuid,
                "store_id": store_uuid_map[s.store_id],
            }
            for s in stores
            if s.store_id in store_uuid_map
        ]
        db.execute(pg_insert(ChannelStore).values(link_records).on_conflict_do_nothing(
            constraint='uq_channelstore_channel_store'
        ))


# ------------------------------------------------------------------ #
# GET
# ------------------------------------------------------------------ #

@router.get("/", response_model=List[ChannelResponse])
def list_channels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if limit > BATCH_LIMIT:
        raise HTTPException(422, f"limit máximo é {BATCH_LIMIT}")
    return db.query(Channel).filter(
        Channel.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()


@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(
    channel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    channel = db.query(Channel).filter(
        Channel.tenant_id == current_user.tenant_id,
        Channel.channel_id == channel_id
    ).first()
    if not channel:
        raise HTTPException(404, "Canal não encontrado")
    return channel


# ------------------------------------------------------------------ #
# POST /batch  (upsert + lojas embutidas)
# ------------------------------------------------------------------ #

@router.post("/batch", response_model=BatchResponse)
def upsert_channels_batch(
    items: List[ChannelBatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} canais por chamada.")

    tenant_id = current_user.tenant_id
    channel_ids = [i.channel_id for i in items]

    existing = db.query(Channel.channel_id, Channel.id).filter(
        Channel.tenant_id == tenant_id,
        Channel.channel_id.in_(channel_ids)
    ).all()
    existing_map = {row.channel_id: row.id for row in existing}

    records = [
        {
            "id": existing_map.get(i.channel_id, uuid.uuid4()),
            "tenant_id": tenant_id,
            "channel_id": i.channel_id,
            "name": i.name,
            "type": i.type,
            "store_mode": i.store_mode,
            "is_active": i.is_active,
        }
        for i in items
    ]

    stmt = pg_insert(Channel).values(records)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_channel_tenant_channelid',
        set_={
            "name": stmt.excluded.name,
            "type": stmt.excluded.type,
            "store_mode": stmt.excluded.store_mode,
            "is_active": stmt.excluded.is_active,
        }
    )
    db.execute(stmt)
    db.flush()

    # Recarrega UUIDs para sincronizar lojas
    db_channels = db.query(Channel.channel_id, Channel.id).filter(
        Channel.tenant_id == tenant_id,
        Channel.channel_id.in_(channel_ids)
    ).all()
    channel_uuid_map = {row.channel_id: row.id for row in db_channels}

    for item in items:
        if item.stores:
            _sync_channel_stores(
                channel_uuid_map[item.channel_id],
                item.stores,
                tenant_id,
                db
            )

    db.commit()

    incoming_set = set(channel_ids)
    created = len(incoming_set - set(existing_map.keys()))
    updated = len(incoming_set & set(existing_map.keys()))
    return BatchResponse(created=created, updated=updated, unchanged=0)


# ------------------------------------------------------------------ #
# PATCH /batch
# ------------------------------------------------------------------ #

@router.patch("/batch", response_model=BatchResponse)
def patch_channels_batch(
    items: List[ChannelPatchItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} canais por chamada.")

    tenant_id = current_user.tenant_id
    channel_ids = [i.channel_id for i in items]
    existing = db.query(Channel).filter(
        Channel.tenant_id == tenant_id,
        Channel.channel_id.in_(channel_ids)
    ).all()
    existing_map = {c.channel_id: c for c in existing}

    updated = 0
    errors = []

    for item in items:
        channel = existing_map.get(item.channel_id)
        if not channel:
            errors.append(f"Canal não encontrado: {item.channel_id}")
            continue

        if item.name is not None:
            channel.name = item.name
        if item.type is not None:
            channel.type = item.type
        if item.store_mode is not None:
            channel.store_mode = item.store_mode
        if item.is_active is not None:
            channel.is_active = item.is_active

        if item.stores is not None:
            db.flush()
            _sync_channel_stores(channel.id, item.stores, tenant_id, db)

        updated += 1

    db.commit()
    return BatchResponse(created=0, updated=updated, unchanged=0, errors=errors)


# ------------------------------------------------------------------ #
# DELETE /batch
# ------------------------------------------------------------------ #

@router.delete("/batch", response_model=BatchResponse)
def delete_channels_batch(
    body: ChannelDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(body.channel_ids) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} canais por chamada.")

    db.query(Channel).filter(
        Channel.tenant_id == current_user.tenant_id,
        Channel.channel_id.in_(body.channel_ids)
    ).delete(synchronize_session=False)

    db.commit()
    return BatchResponse(created=0, updated=0, unchanged=0)
