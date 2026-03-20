# backend/app/workers/content_worker.py
"""
Worker de geração de conteúdo personalizado.

Executa como processo separado: python -m app.workers.content_worker
Disparado automaticamente após job de recomendação.
Usa SELECT FOR UPDATE SKIP LOCKED para distribuição de trabalho.
"""
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import text

from app.db.session import SessionLocal, SessionReplica
from app.db.models import ContentJob
from app.services.content_service import ContentService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 5


def claim_job(db_primary) -> ContentJob | None:
    """Tenta reservar o próximo content job via SELECT FOR UPDATE SKIP LOCKED."""
    row = db_primary.execute(
        text("""
            SELECT id, tenant_id
            FROM content_jobs
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
            UPDATE content_jobs
            SET status = 'running', started_at = :now
            WHERE id = :jid
        """),
        {"jid": job_id, "now": datetime.now(timezone.utc)},
    )
    db_primary.commit()

    return db_primary.query(ContentJob).get(job_id)


def run_job(job: ContentJob):
    """Executa um job de geração de conteúdo."""
    logger.info("ContentJob %s: iniciando tenant=%s", job.id, job.tenant_id)

    db_read = SessionReplica()

    try:
        channels = job.channels  # None = todos, ou lista ["email", "whatsapp"]
        counters = ContentService.run_for_tenant(job.tenant_id, db_read, channels=channels)

        db_done = SessionLocal()
        try:
            j = db_done.query(ContentJob).get(job.id)
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

        logger.info(
            "ContentJob %s: concluído — %d customers, %d emails, %d images, %d push",
            job.id, counters["customers_processed"], counters["emails"],
            counters["images"], counters["push"],
        )

    except Exception as e:
        logger.exception("ContentJob %s: falhou", job.id)
        db_fail = SessionLocal()
        try:
            j = db_fail.query(ContentJob).get(job.id)
            if j:
                j.status = "failed"
                j.finished_at = datetime.now(timezone.utc)
                j.error_msg = str(e)[:500]
                db_fail.commit()
        finally:
            db_fail.close()
    finally:
        db_read.close()


def main():
    """Loop principal do worker."""
    logger.info("Content worker iniciado")

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
            logger.exception("Erro no loop do content worker")
            try:
                db.close()
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
