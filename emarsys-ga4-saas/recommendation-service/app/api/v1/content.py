# backend/app/api/v1/content.py
"""
Endpoints de consumo de conteúdo personalizado + jobs.

- POST /content/run            — gera conteúdo inline (BackgroundTask)
- POST /content/enqueue        — enfileira para worker
- GET  /content/status         — status dos jobs
- GET  /content/email/{ref}    — HTML de 1 cliente
- GET  /content/whatsapp/{ref} — URL imagem de 1 cliente
- GET  /content/push/{ref}     — push imagem de 1 cliente
- POST /content/email/batch    — batch emails por lista de IDs
- POST /content/whatsapp/batch — batch URLs por lista de IDs
- POST /content/push/batch     — batch push por lista de IDs
- POST /content/test-s3        — testa credenciais S3

Todos os endpoints de cliente aceitam query param id_type:
  customer_id (default) | customer_add_id | internal
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal, SessionReplica
from app.api.deps import get_current_user, resolve_customer, resolve_customers
from app.db.models import (
    User, TenantConfig, Customer, ContentJob,
    ContentEmail, ContentWhatsapp, ContentPush,
)
from app.services.content_service import ContentService

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class BatchRequest(BaseModel):
    ids: list[str]
    id_type: str = "customer_id"
    algorithm: str = "pessoal"


def _refresh_presigned_if_needed(db: Session, row, config: TenantConfig):
    """Regenera presigned URL se expirada."""
    if not row.image_s3_key or not row.presigned_expires_at:
        return
    if row.presigned_expires_at > datetime.now(timezone.utc):
        return
    try:
        url, expires = ContentService.regenerate_presigned_url(config, row.image_s3_key)
        row.image_url = url
        row.presigned_expires_at = expires
        db.commit()
    except Exception:
        logger.warning("Falha ao regenerar presigned URL para %s", row.image_s3_key, exc_info=True)


def _get_config(db: Session, tenant_id: str) -> TenantConfig:
    config = db.query(TenantConfig).filter(TenantConfig.tenant_id == tenant_id).first()
    if not config:
        raise HTTPException(404, "TenantConfig não encontrado")
    return config


# ------------------------------------------------------------------ #
# POST /content/run — inline
# ------------------------------------------------------------------ #

def _run_content_inline(job_id: uuid.UUID, tenant_id: str, channels: Optional[list[str]]):
    db_primary = SessionLocal()
    try:
        job = db_primary.query(ContentJob).get(job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db_primary.commit()
    finally:
        db_primary.close()

    db_read = SessionReplica()
    try:
        counters = ContentService.run_for_tenant(tenant_id, db_read, channels=channels)

        db_done = SessionLocal()
        try:
            job = db_done.query(ContentJob).get(job_id)
            if job:
                job.status = "done"
                job.finished_at = datetime.now(timezone.utc)
                job.customers_processed = counters["customers_processed"]
                job.emails_generated = counters["emails"]
                job.images_generated = counters["images"]
                job.push_generated = counters["push"]
                db_done.commit()
        finally:
            db_done.close()

    except Exception as e:
        logger.exception("Content inline falhou: tenant=%s", tenant_id)
        db_fail = SessionLocal()
        try:
            job = db_fail.query(ContentJob).get(job_id)
            if job:
                job.status = "failed"
                job.finished_at = datetime.now(timezone.utc)
                job.error_msg = str(e)[:500]
                db_fail.commit()
        finally:
            db_fail.close()
    finally:
        db_read.close()


@router.post("/run")
def run_content_now(
    background_tasks: BackgroundTasks,
    channels: Optional[list[str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id

    # Auto-reset stuck jobs
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
    stuck = db.query(ContentJob).filter(
        ContentJob.tenant_id == tenant_id,
        ContentJob.status.in_(["queued", "running"]),
        ContentJob.queued_at < cutoff,
    ).all()
    for j in stuck:
        j.status = "failed"
        j.finished_at = datetime.now(timezone.utc)
        j.error_msg = "Auto-reset — job travado"
    if stuck:
        db.commit()

    existing = db.query(ContentJob).filter(
        ContentJob.tenant_id == tenant_id,
        ContentJob.status.in_(["queued", "running"]),
    ).first()
    if existing:
        return {"started": False, "message": f"Job já {existing.status}", "job_id": str(existing.id), "status": existing.status}

    job = ContentJob(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        status="queued",
        priority=0,
        triggered_by="api_inline",
        channels=channels,
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(_run_content_inline, job.id, tenant_id, channels)
    return {"started": True, "job_id": str(job.id), "status": "queued"}


# ------------------------------------------------------------------ #
# POST /content/enqueue
# ------------------------------------------------------------------ #

@router.post("/enqueue")
def enqueue_content_job(
    channels: Optional[list[str]] = None,
    priority: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    existing = db.query(ContentJob).filter(
        ContentJob.tenant_id == tenant_id,
        ContentJob.status.in_(["queued", "running"]),
    ).first()
    if existing:
        return {"enqueued": False, "message": f"Job já {existing.status}", "job_id": str(existing.id), "status": existing.status}

    job = ContentJob(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        status="queued",
        priority=priority,
        triggered_by="api",
        channels=channels,
    )
    db.add(job)
    db.commit()
    return {"enqueued": True, "job_id": str(job.id), "status": "queued"}


# ------------------------------------------------------------------ #
# GET /content/status
# ------------------------------------------------------------------ #

@router.get("/status")
def content_status(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    total = db.query(ContentJob).filter(ContentJob.tenant_id == tenant_id).count()
    jobs = (
        db.query(ContentJob)
        .filter(ContentJob.tenant_id == tenant_id)
        .order_by(ContentJob.queued_at.desc())
        .offset(skip).limit(limit).all()
    )
    items = [
        {
            "id": str(j.id),
            "status": j.status,
            "priority": j.priority,
            "triggered_by": j.triggered_by,
            "channels": j.channels,
            "queued_at": j.queued_at,
            "started_at": j.started_at,
            "finished_at": j.finished_at,
            "customers_processed": j.customers_processed,
            "emails_generated": j.emails_generated,
            "images_generated": j.images_generated,
            "push_generated": j.push_generated,
            "error_msg": j.error_msg,
        }
        for j in jobs
    ]
    return {"items": items, "total": total, "skip": skip, "limit": limit}


# ------------------------------------------------------------------ #
# Individual content endpoints
# ------------------------------------------------------------------ #

@router.get("/email/{customer_ref}")
def get_email(
    customer_ref: str,
    algorithm: str = "pessoal",
    id_type: str = "customer_id",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    customer = resolve_customer(db, tenant_id, customer_ref, id_type)
    row = db.query(ContentEmail).filter(
        ContentEmail.tenant_id == tenant_id,
        ContentEmail.customer_id == customer.id,
        ContentEmail.algorithm == algorithm,
    ).first()
    if not row:
        raise HTTPException(404, f"Conteúdo email ({algorithm}) não encontrado para este cliente")
    return {
        "customer_external_id": row.customer_external_id,
        "customer_add_id": row.customer_add_id,
        "customer_name": row.customer_name,
        "algorithm": row.algorithm,
        "html_body": row.html_body,
        "products_count": row.products_count,
        "computed_at": row.computed_at,
    }


@router.get("/whatsapp/{customer_ref}")
def get_whatsapp(
    customer_ref: str,
    algorithm: str = "pessoal",
    id_type: str = "customer_id",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    customer = resolve_customer(db, tenant_id, customer_ref, id_type)
    config = _get_config(db, tenant_id)
    row = db.query(ContentWhatsapp).filter(
        ContentWhatsapp.tenant_id == tenant_id,
        ContentWhatsapp.customer_id == customer.id,
        ContentWhatsapp.algorithm == algorithm,
    ).first()
    if not row:
        raise HTTPException(404, f"Conteúdo whatsapp ({algorithm}) não encontrado para este cliente")
    _refresh_presigned_if_needed(db, row, config)
    return {
        "customer_external_id": row.customer_external_id,
        "customer_add_id": row.customer_add_id,
        "customer_name": row.customer_name,
        "algorithm": row.algorithm,
        "image_url": row.image_url,
        "products_count": row.products_count,
        "presigned_expires_at": row.presigned_expires_at,
        "computed_at": row.computed_at,
    }


@router.get("/push/{customer_ref}")
def get_push(
    customer_ref: str,
    algorithm: str = "pessoal",
    id_type: str = "customer_id",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    customer = resolve_customer(db, tenant_id, customer_ref, id_type)
    config = _get_config(db, tenant_id)
    row = db.query(ContentPush).filter(
        ContentPush.tenant_id == tenant_id,
        ContentPush.customer_id == customer.id,
        ContentPush.algorithm == algorithm,
    ).first()
    if not row:
        raise HTTPException(404, f"Conteúdo push ({algorithm}) não encontrado para este cliente")
    _refresh_presigned_if_needed(db, row, config)
    return {
        "customer_external_id": row.customer_external_id,
        "customer_add_id": row.customer_add_id,
        "customer_name": row.customer_name,
        "algorithm": row.algorithm,
        "image_url": row.image_url,
        "presigned_expires_at": row.presigned_expires_at,
        "computed_at": row.computed_at,
    }


# ------------------------------------------------------------------ #
# Batch endpoints
# ------------------------------------------------------------------ #

@router.post("/email/batch")
def batch_emails(
    body: BatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna conteúdo email para uma lista de clientes."""
    tenant_id = current_user.tenant_id
    customers = resolve_customers(db, tenant_id, body.ids, body.id_type)
    if not customers:
        return {"items": [], "total": 0}
    cid_set = {c.id for c in customers}
    rows = db.query(ContentEmail).filter(
        ContentEmail.tenant_id == tenant_id,
        ContentEmail.algorithm == body.algorithm,
        ContentEmail.customer_id.in_(cid_set),
    ).all()
    return {
        "items": [
            {
                "customer_external_id": r.customer_external_id,
                "customer_add_id": r.customer_add_id,
                "customer_name": r.customer_name,
                "algorithm": r.algorithm,
                "html_body": r.html_body,
                "products_count": r.products_count,
                "computed_at": r.computed_at,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/whatsapp/batch")
def batch_whatsapp(
    body: BatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna conteúdo WhatsApp para uma lista de clientes."""
    tenant_id = current_user.tenant_id
    customers = resolve_customers(db, tenant_id, body.ids, body.id_type)
    if not customers:
        return {"items": [], "total": 0}
    cid_set = {c.id for c in customers}
    config = _get_config(db, tenant_id)
    rows = db.query(ContentWhatsapp).filter(
        ContentWhatsapp.tenant_id == tenant_id,
        ContentWhatsapp.algorithm == body.algorithm,
        ContentWhatsapp.customer_id.in_(cid_set),
    ).all()
    for r in rows:
        _refresh_presigned_if_needed(db, r, config)
    return {
        "items": [
            {
                "customer_external_id": r.customer_external_id,
                "customer_add_id": r.customer_add_id,
                "customer_name": r.customer_name,
                "algorithm": r.algorithm,
                "image_url": r.image_url,
                "products_count": r.products_count,
                "presigned_expires_at": r.presigned_expires_at,
                "computed_at": r.computed_at,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/push/batch")
def batch_push(
    body: BatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna conteúdo push para uma lista de clientes."""
    tenant_id = current_user.tenant_id
    customers = resolve_customers(db, tenant_id, body.ids, body.id_type)
    if not customers:
        return {"items": [], "total": 0}
    cid_set = {c.id for c in customers}
    config = _get_config(db, tenant_id)
    rows = db.query(ContentPush).filter(
        ContentPush.tenant_id == tenant_id,
        ContentPush.algorithm == body.algorithm,
        ContentPush.customer_id.in_(cid_set),
    ).all()
    for r in rows:
        _refresh_presigned_if_needed(db, r, config)
    return {
        "items": [
            {
                "customer_external_id": r.customer_external_id,
                "customer_add_id": r.customer_add_id,
                "customer_name": r.customer_name,
                "algorithm": r.algorithm,
                "image_url": r.image_url,
                "presigned_expires_at": r.presigned_expires_at,
                "computed_at": r.computed_at,
            }
            for r in rows
        ],
        "total": len(rows),
    }


# ------------------------------------------------------------------ #
# POST /content/test-s3
# ------------------------------------------------------------------ #

@router.post("/test-s3")
def test_s3(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = _get_config(db, current_user.tenant_id)
    return ContentService.test_s3(config)
