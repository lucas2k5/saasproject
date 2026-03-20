# backend/app/workers/recommendation_worker.py
"""
Worker de recomendação personalizada.

Executa como processo separado: python -m app.workers.recommendation_worker
Lê da replica, escreve no primary.
Usa SELECT FOR UPDATE SKIP LOCKED para distribuição de trabalho.

Ordem de execução no noturno:
  1. Lifecycle (worker separado) — precisa estar pronto antes
  2. Top Sellers + Recomendação (este worker)
"""
import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.db.session import SessionLocal, SessionReplica
from app.db.models import RecommendationJob, ContentJob, ContentTemplate
from app.services.recommendation_service import RecommendationService, cleanup_history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 5


def claim_job(db_primary) -> RecommendationJob | None:
    """Tenta reservar o próximo job via SELECT FOR UPDATE SKIP LOCKED."""
    row = db_primary.execute(
        text("""
            SELECT id, tenant_id
            FROM recommendation_jobs
            WHERE status = 'queued'
            ORDER BY priority ASC, queued_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)
    ).fetchone()

    if not row:
        return None

    job_id = row[0]
    db_primary.execute(
        text("""
            UPDATE recommendation_jobs
            SET status = 'running', started_at = :now
            WHERE id = :jid
        """),
        {"jid": job_id, "now": datetime.now(timezone.utc)},
    )
    db_primary.commit()

    return db_primary.query(RecommendationJob).get(job_id)


def run_job(job: RecommendationJob):
    """Executa um job de recomendação: top sellers + recomendações + limpeza."""
    logger.info("Job %s: iniciando tenant=%s", job.id, job.tenant_id)

    db_write = SessionLocal()
    db_read = SessionReplica()

    try:
        # 1. Computa top sellers
        logger.info("Job %s: computando top sellers...", job.id)
        RecommendationService.compute_top_sellers(db_write, job.tenant_id)

        # 2. Computa recomendações para todos os clientes
        logger.info("Job %s: computando recomendações...", job.id)
        total = RecommendationService.run_for_tenant(job.tenant_id, db_read)

        # 3. Limpeza de histórico
        cleanup_history(db_write)

        # Marca como done
        db_done = SessionLocal()
        try:
            j = db_done.query(RecommendationJob).get(job.id)
            if j:
                j.status = "done"
                j.finished_at = datetime.now(timezone.utc)
                j.customers_processed = total
                db_done.commit()
        finally:
            db_done.close()

        # Auto-enqueue content job se tenant tem templates ativos
        _auto_enqueue_content(job.tenant_id)

        logger.info("Job %s: concluído — %d recomendações", job.id, total)

    except Exception as e:
        logger.exception("Job %s: falhou", job.id)
        db_fail = SessionLocal()
        try:
            j = db_fail.query(RecommendationJob).get(job.id)
            if j:
                j.status = "failed"
                j.finished_at = datetime.now(timezone.utc)
                j.error_msg = str(e)[:500]
                db_fail.commit()
        finally:
            db_fail.close()
    finally:
        db_read.close()
        db_write.close()


def _auto_enqueue_content(tenant_id: str):
    """Enfileira ContentJob automaticamente se o tenant tem templates ativos."""
    db = SessionLocal()
    try:
        has_templates = db.query(ContentTemplate).filter(
            ContentTemplate.tenant_id == tenant_id,
            ContentTemplate.is_active == True,
        ).first()
        if not has_templates:
            return

        existing = db.query(ContentJob).filter(
            ContentJob.tenant_id == tenant_id,
            ContentJob.status.in_(["queued", "running"]),
        ).first()
        if existing:
            return

        db.add(ContentJob(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            status="queued",
            priority=1,
            triggered_by="auto_after_recommendation",
        ))
        db.commit()
        logger.info("ContentJob auto-enqueued para tenant %s", tenant_id)
    except Exception:
        logger.exception("Falha ao auto-enqueue ContentJob para tenant %s", tenant_id)
    finally:
        db.close()


def main():
    """Loop principal do worker."""
    logger.info("Recommendation worker iniciado")

    while True:
        db = SessionLocal()
        try:
            job = claim_job(db)
            if job:
                db.close()
                run_job(job)
            else:
                db.close()
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Worker interrompido")
            break
        except Exception:
            logger.exception("Erro no loop do worker")
            try:
                db.close()
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
