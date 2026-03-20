# backend/app/api/v1/lifecycle.py
"""
Endpoints de ciclo de vida do cliente.

- POST /lifecycle/enqueue  — enfileira job de segmentação para o tenant
- GET  /lifecycle/status   — status dos jobs do tenant
- GET  /customers/{customer_ref}/lifecycle — indicadores + segmento de um cliente
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal, SessionReplica
from app.api.deps import get_current_user, resolve_customer
from app.db.models import (
    User, Customer, CustomerSegment, CustomerOrderSummary, SegmentJob,
)
from app.services.lifecycle_service import compute_segments_for_tenant

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------ #
# POST /lifecycle/enqueue
# ------------------------------------------------------------------ #

@router.post("/enqueue")
def enqueue_lifecycle_job(
    priority: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enfileira job de segmentação para o tenant do usuário.
    Não enfileira se já existe job queued ou running.
    priority=0 (urgente, manual), priority=1 (scheduler).
    """
    tenant_id = current_user.tenant_id

    # Checa se já existe job ativo
    existing = db.query(SegmentJob).filter(
        SegmentJob.tenant_id == tenant_id,
        SegmentJob.status.in_(["queued", "running"]),
    ).first()

    if existing:
        return {
            "enqueued": False,
            "message": f"Job já {existing.status} (id={existing.id})",
            "job_id": str(existing.id),
            "status": existing.status,
        }

    job = SegmentJob(
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
# POST /lifecycle/run  — roda o cálculo inline (BackgroundTask)
# ------------------------------------------------------------------ #

def _run_lifecycle_inline(job_id: uuid.UUID, tenant_id: str):
    """Executa o cálculo de segmentos em background (sem worker separado)."""
    db_primary = SessionLocal()
    try:
        job = db_primary.query(SegmentJob).get(job_id)
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
        processed = compute_segments_for_tenant(db_read, db_write, tenant_id)

        db_done = SessionLocal()
        try:
            job = db_done.query(SegmentJob).get(job_id)
            if job:
                job.status = "done"
                job.finished_at = datetime.now(timezone.utc)
                job.customers_processed = processed
                db_done.commit()
        finally:
            db_done.close()

        logger.info("Lifecycle inline: tenant=%s, %d clientes", tenant_id, processed)

    except Exception as e:
        logger.exception("Lifecycle inline falhou: tenant=%s", tenant_id)
        db_fail = SessionLocal()
        try:
            job = db_fail.query(SegmentJob).get(job_id)
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


@router.post("/reset")
def reset_stuck_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marca como failed jobs travados em queued/running há mais de 30 minutos."""
    tenant_id = current_user.tenant_id
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)

    stuck = db.query(SegmentJob).filter(
        SegmentJob.tenant_id == tenant_id,
        SegmentJob.status.in_(["queued", "running"]),
        SegmentJob.queued_at < cutoff,
    ).all()

    for job in stuck:
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.error_msg = "Reset manual — job travado após reinício do servidor"
    db.commit()

    return {"reset": len(stuck)}


@router.post("/run")
def run_lifecycle_now(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria job e roda o cálculo de segmentos em background (sem worker separado).
    Ideal para dev ou tenants pequenos.
    Auto-reseta jobs travados há mais de 30 minutos antes de verificar duplicatas.
    """
    tenant_id = current_user.tenant_id

    # Auto-reset jobs travados (servidor reiniciou no meio do cálculo)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    stuck = db.query(SegmentJob).filter(
        SegmentJob.tenant_id == tenant_id,
        SegmentJob.status.in_(["queued", "running"]),
        SegmentJob.queued_at < cutoff,
    ).all()
    for job in stuck:
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.error_msg = "Auto-reset — job travado após reinício do servidor"
    if stuck:
        db.commit()

    existing = db.query(SegmentJob).filter(
        SegmentJob.tenant_id == tenant_id,
        SegmentJob.status.in_(["queued", "running"]),
    ).first()

    if existing:
        return {
            "started": False,
            "message": f"Job já {existing.status}",
            "job_id": str(existing.id),
            "status": existing.status,
        }

    job = SegmentJob(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        status="queued",
        priority=0,
        triggered_by="api_inline",
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(_run_lifecycle_inline, job.id, tenant_id)

    return {
        "started": True,
        "job_id": str(job.id),
        "status": "queued",
    }


# ------------------------------------------------------------------ #
# GET /lifecycle/status
# ------------------------------------------------------------------ #

@router.get("/status")
def lifecycle_status(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna os jobs de segmentação do tenant (mais recentes primeiro)."""
    tenant_id = current_user.tenant_id

    total = db.query(SegmentJob).filter(SegmentJob.tenant_id == tenant_id).count()

    jobs = (
        db.query(SegmentJob)
        .filter(SegmentJob.tenant_id == tenant_id)
        .order_by(SegmentJob.queued_at.desc())
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
# GET /customers/{customer_ref}/lifecycle
# ------------------------------------------------------------------ #

@router.get("/customers/{customer_ref}")
def get_customer_lifecycle(
    customer_ref: str,
    id_type: str = "customer_id",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna indicadores + segmento de ciclo de vida de um cliente.
    id_type: customer_id (default) | customer_add_id | internal
    """
    tenant_id = current_user.tenant_id
    customer = resolve_customer(db, tenant_id, customer_ref, id_type)

    segment = db.query(CustomerSegment).filter(
        CustomerSegment.tenant_id == tenant_id,
        CustomerSegment.customer_id == customer.id,
    ).first()

    summary = db.query(CustomerOrderSummary).filter(
        CustomerOrderSummary.tenant_id == tenant_id,
        CustomerOrderSummary.customer_id == customer.id,
    ).first()

    result = {
        "customer_id": str(customer.id),
        "customer_ref": customer.customer_id,
        "name": customer.name,
    }

    if segment:
        result["lifecycle"] = {
            "segment": segment.lifecycle_segment,
            "computed_at": segment.computed_at,
            "indicators": {
                "recency_days": segment.recency_days,
                "number_of_invoices": segment.number_of_invoices,
                "monetary_total": segment.monetary_total,
                "avg_ticket": segment.avg_ticket,
                "ticket_trend": segment.ticket_trend,
                "purchase_velocity_trend": segment.purchase_velocity_trend,
                "avg_days_between": segment.avg_days_between,
                "purchase_regularity": segment.purchase_regularity,
                "distinct_articles": segment.distinct_articles,
                "category_diversity": segment.category_diversity,
                "promo_ratio": segment.promo_ratio,
                "return_rate": segment.return_rate,
                "repeat_product_ratio": segment.repeat_product_ratio,
                "days_as_customer": segment.days_as_customer,
                "p_alive": segment.p_alive,
                "expected_transactions": segment.expected_transactions,
            },
            "preferences": {
                "top_5_products": segment.top_5_products,
                "top_5_categories": segment.top_5_categories,
                "preferred_channel": segment.preferred_channel,
            },
        }
    else:
        result["lifecycle"] = None

    if summary:
        result["summary"] = {
            "total_orders": summary.total_orders,
            "total_value": summary.total_value,
            "first_order_at": summary.first_order_at,
            "last_order_at": summary.last_order_at,
            "orders_90d": summary.orders_90d,
            "value_90d": summary.value_90d,
        }
    else:
        result["summary"] = None

    return result
