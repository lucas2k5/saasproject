# backend/app/workers/lifecycle_worker.py
"""
Worker de ciclo de vida do cliente.

Executa como processo separado: python -m app.workers.lifecycle_worker
Lê da replica, escreve no primary.
Usa SELECT FOR UPDATE SKIP LOCKED para distribuição de trabalho.
"""
import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.db.session import SessionLocal, SessionReplica
from app.db.models import SegmentJob
from app.services.lifecycle_service import compute_segments_for_tenant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 5  # segundos entre tentativas quando não há jobs


def claim_job(db_primary) -> SegmentJob | None:
    """
    Tenta reservar o próximo job da fila via SELECT FOR UPDATE SKIP LOCKED.
    Retorna o job ou None se não houver nada.
    """
    row = db_primary.execute(
        text("""
            SELECT id, tenant_id
            FROM segment_jobs
            WHERE status = 'queued'
            ORDER BY priority ASC, queued_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)
    ).fetchone()

    if not row:
        return None

    job_id = row[0]
    # Marca como running
    db_primary.execute(
        text("""
            UPDATE segment_jobs
            SET status = 'running', started_at = :now
            WHERE id = :jid
        """),
        {"jid": job_id, "now": datetime.now(timezone.utc)},
    )
    db_primary.commit()

    return db_primary.query(SegmentJob).get(job_id)


def run_job(job: SegmentJob):
    """Executa um job de segmentação."""
    logger.info("Job %s: iniciando tenant=%s", job.id, job.tenant_id)

    db_write = SessionLocal()
    db_read = SessionReplica()

    try:
        processed = compute_segments_for_tenant(db_read, db_write, job.tenant_id)

        # Marca como done
        db_primary = SessionLocal()
        try:
            j = db_primary.query(SegmentJob).get(job.id)
            if j:
                j.status = "done"
                j.finished_at = datetime.now(timezone.utc)
                j.customers_processed = processed
                db_primary.commit()
        finally:
            db_primary.close()

        logger.info("Job %s: concluído — %d clientes", job.id, processed)

    except Exception as e:
        logger.exception("Job %s: falhou", job.id)
        db_fail = SessionLocal()
        try:
            j = db_fail.query(SegmentJob).get(job.id)
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


def main():
    """Loop principal do worker."""
    logger.info("Lifecycle worker iniciado")

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
