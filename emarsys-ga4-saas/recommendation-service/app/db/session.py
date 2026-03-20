from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


def json_serializer(obj):
    return json.dumps(obj, ensure_ascii=False)


# Pool sizing: pool_size conexões persistentes + max_overflow temporárias.
# API (gunicorn 4 workers × pool_size=10) = 40 conexões primary.
# Workers separados criam seus próprios engines.
_POOL_KWARGS = dict(
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,       # testa conexão antes de usar (evita stale TCP)
    pool_recycle=1800,         # recicla conexões a cada 30min (evita timeout do PG/Supabase)
    pool_timeout=30,           # espera máxima por conexão do pool
)

# ---- Primary (OLTP): API + escritas ----
engine = create_engine(
    settings.DATABASE_URL,
    json_serializer=json_serializer,
    **_POOL_KWARGS,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---- Replica (OLAP): leituras pesadas dos workers ----
# Fallback: se não configurado, usa primary (dev local com um banco só)
_replica_url = settings.DATABASE_URL_REPLICA or settings.DATABASE_URL
engine_replica = create_engine(
    _replica_url,
    json_serializer=json_serializer,
    **_POOL_KWARGS,
)
SessionReplica = sessionmaker(autocommit=False, autoflush=False, bind=engine_replica)

if _replica_url != settings.DATABASE_URL:
    logger.info("Read replica configurada: %s", _replica_url[:40] + "...")


def get_db():
    """Sessão primary para a API."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_replica_db():
    """Sessão replica para leituras pesadas (workers)."""
    db = SessionReplica()
    try:
        yield db
    finally:
        db.close()
