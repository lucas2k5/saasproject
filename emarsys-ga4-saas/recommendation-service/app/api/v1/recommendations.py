# backend/app/api/v1/recommendations.py
"""
Endpoints de recomendação personalizada.

- POST /recommendations/run         — roda inline (BackgroundTask, dev/tenants pequenos)
- POST /recommendations/enqueue     — enfileira para worker
- GET  /recommendations/status      — status dos jobs
- GET  /recommendations/{customer_ref} — recomendações real-time para um cliente
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
from app.db.models import User, Customer, RecommendationJob, ContentJob, ContentTemplate
from app.services.recommendation_service import RecommendationService, cleanup_history
from app.services.content_service import ContentService

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------ #
# POST /recommendations/run  — inline (BackgroundTask)
# ------------------------------------------------------------------ #

def _auto_run_content_inline(tenant_id: str):
    """Executa ContentJob automaticamente (inline) se o tenant tem templates ativos."""
    db_check = SessionLocal()
    try:
        has_templates = db_check.query(ContentTemplate).filter(
            ContentTemplate.tenant_id == tenant_id,
            ContentTemplate.is_active == True,
        ).first()
        if not has_templates:
            return
        existing = db_check.query(ContentJob).filter(
            ContentJob.tenant_id == tenant_id,
            ContentJob.status.in_(["queued", "running"]),
        ).first()
        if existing:
            return
        job = ContentJob(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            status="running",
            priority=1,
            triggered_by="auto_after_recommendation",
            started_at=datetime.now(timezone.utc),
        )
        db_check.add(job)
        db_check.commit()
        job_id = job.id
        logger.info("ContentJob auto-started para tenant %s (inline)", tenant_id)
    except Exception:
        logger.exception("Falha ao criar ContentJob para tenant %s", tenant_id)
        return
    finally:
        db_check.close()

    # Executar inline
    db_read = SessionReplica()
    try:
        counters = ContentService.run_for_tenant(tenant_id, db_read)

        db_done = SessionLocal()
        try:
            j = db_done.query(ContentJob).get(job_id)
            if j:
                j.status = "done"
                j.finished_at = datetime.now(timezone.utc)
                j.customers_processed = counters["customers_processed"]
                j.emails_generated = counters["emails"]
                j.images_generated = counters["images"]
                j.push_generated = counters["push"]
                db_done.commit()
        finally:
            db_done.close()

        logger.info("ContentJob %s: concluído inline — %s", job_id, counters)

    except Exception as e:
        logger.exception("ContentJob %s: falhou inline", job_id)
        db_fail = SessionLocal()
        try:
            j = db_fail.query(ContentJob).get(job_id)
            if j:
                j.status = "failed"
                j.finished_at = datetime.now(timezone.utc)
                j.error_msg = str(e)[:500]
                db_fail.commit()
        finally:
            db_fail.close()
    finally:
        db_read.close()


def _run_recommendation_inline(job_id: uuid.UUID, tenant_id: str):
    """Executa top sellers + recomendações em background (sem worker separado)."""
    db_primary = SessionLocal()
    try:
        job = db_primary.query(RecommendationJob).get(job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db_primary.commit()
    finally:
        db_primary.close()

    db_write = SessionLocal()
    db_read = SessionReplica()
    try:
        # Top sellers
        RecommendationService.compute_top_sellers(db_write, tenant_id)

        # Recomendações
        total = RecommendationService.run_for_tenant(tenant_id, db_read)

        # Limpeza
        cleanup_history(db_write)

        db_done = SessionLocal()
        try:
            job = db_done.query(RecommendationJob).get(job_id)
            if job:
                job.status = "done"
                job.finished_at = datetime.now(timezone.utc)
                job.customers_processed = total
                db_done.commit()
        finally:
            db_done.close()

        # Auto-run content job inline
        _auto_run_content_inline(tenant_id)

        logger.info("Recommendation inline: tenant=%s, %d recs", tenant_id, total)

    except Exception as e:
        logger.exception("Recommendation inline falhou: tenant=%s", tenant_id)
        db_fail = SessionLocal()
        try:
            job = db_fail.query(RecommendationJob).get(job_id)
            if job:
                job.status = "failed"
                job.finished_at = datetime.now(timezone.utc)
                job.error_msg = str(e)[:500]
                db_fail.commit()
        finally:
            db_fail.close()
    finally:
        db_read.close()
        db_write.close()


@router.post("/run")
def run_recommendations_now(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria job e roda recomendações em background (sem worker separado).
    Auto-reseta jobs travados há mais de 60 minutos.
    """
    tenant_id = current_user.tenant_id

    # Auto-reset jobs travados
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
    stuck = db.query(RecommendationJob).filter(
        RecommendationJob.tenant_id == tenant_id,
        RecommendationJob.status.in_(["queued", "running"]),
        RecommendationJob.queued_at < cutoff,
    ).all()
    for job in stuck:
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.error_msg = "Auto-reset — job travado"
    if stuck:
        db.commit()

    existing = db.query(RecommendationJob).filter(
        RecommendationJob.tenant_id == tenant_id,
        RecommendationJob.status.in_(["queued", "running"]),
    ).first()

    if existing:
        return {
            "started": False,
            "message": f"Job já {existing.status}",
            "job_id": str(existing.id),
            "status": existing.status,
        }

    job = RecommendationJob(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        status="queued",
        priority=0,
        triggered_by="api_inline",
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(_run_recommendation_inline, job.id, tenant_id)

    return {
        "started": True,
        "job_id": str(job.id),
        "status": "queued",
    }


# ------------------------------------------------------------------ #
# POST /recommendations/enqueue — para worker
# ------------------------------------------------------------------ #

@router.post("/enqueue")
def enqueue_recommendation_job(
    priority: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enfileira job de recomendação para o worker."""
    tenant_id = current_user.tenant_id

    existing = db.query(RecommendationJob).filter(
        RecommendationJob.tenant_id == tenant_id,
        RecommendationJob.status.in_(["queued", "running"]),
    ).first()

    if existing:
        return {
            "enqueued": False,
            "message": f"Job já {existing.status}",
            "job_id": str(existing.id),
            "status": existing.status,
        }

    job = RecommendationJob(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        status="queued",
        priority=priority,
        triggered_by="api",
    )
    db.add(job)
    db.commit()

    return {
        "enqueued": True,
        "job_id": str(job.id),
        "status": "queued",
    }


# ------------------------------------------------------------------ #
# GET /recommendations/status
# ------------------------------------------------------------------ #

@router.get("/status")
def recommendation_status(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna os jobs de recomendação do tenant (mais recentes primeiro)."""
    tenant_id = current_user.tenant_id

    total = db.query(RecommendationJob).filter(
        RecommendationJob.tenant_id == tenant_id
    ).count()

    jobs = (
        db.query(RecommendationJob)
        .filter(RecommendationJob.tenant_id == tenant_id)
        .order_by(RecommendationJob.queued_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = [
        {
            "id": str(j.id),
            "status": j.status,
            "priority": j.priority,
            "triggered_by": j.triggered_by,
            "queued_at": j.queued_at,
            "started_at": j.started_at,
            "finished_at": j.finished_at,
            "customers_processed": j.customers_processed,
            "error_msg": j.error_msg,
        }
        for j in jobs
    ]

    return {"items": items, "total": total, "skip": skip, "limit": limit}


# ------------------------------------------------------------------ #
# GET /recommendations/{customer_ref}  — real-time
# ------------------------------------------------------------------ #

@router.get("/{customer_ref}")
def get_customer_recommendations(
    customer_ref: str,
    algorithm: Optional[str] = None,
    limit: int = 6,
    id_type: str = "customer_id",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna recomendações real-time para um cliente.
    Re-filtra estoque sobre o rank pré-computado.
    id_type: customer_id (default) | customer_add_id | internal
    """
    tenant_id = current_user.tenant_id
    customer = resolve_customer(db, tenant_id, customer_ref, id_type)

    results = RecommendationService.get_realtime_recommendations(
        db, tenant_id, str(customer.id), algorithm=algorithm, limit=limit,
    )

    return {
        "customer_id": str(customer.id),
        "customer_ref": customer.customer_id,
        "name": customer.name,
        "recommendations": results,
    }


# ------------------------------------------------------------------ #
# POST /recommendations/batch  — real-time para múltiplos clientes
# ------------------------------------------------------------------ #

class RecommendationBatchRequest(BaseModel):
    ids: list[str]
    id_type: str = "customer_id"
    algorithm: Optional[str] = None
    limit: int = 6


@router.post("/batch")
def batch_recommendations(
    body: RecommendationBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna recomendações real-time para uma lista de clientes."""
    tenant_id = current_user.tenant_id
    customers = resolve_customers(db, tenant_id, body.ids, body.id_type)
    if not customers:
        return {"items": [], "total": 0}

    items = []
    for customer in customers:
        results = RecommendationService.get_realtime_recommendations(
            db, tenant_id, str(customer.id), algorithm=body.algorithm, limit=body.limit,
        )
        items.append({
            "customer_id": str(customer.id),
            "customer_ref": customer.customer_id,
            "customer_add_id": customer.customer_add_id,
            "name": customer.name,
            "recommendations": results,
        })

    return {"items": items, "total": len(items)}
