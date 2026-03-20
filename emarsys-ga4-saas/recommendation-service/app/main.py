import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
import uuid

from fastapi import FastAPI
from app.api.v1 import auth, products, search, recommend, dashboards, tenant_config, customers, channels, stores, prices, stock, offers, orders, lifecycle, recommendations, admin_cleanup, content_templates, content, api_keys
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.models import Base, SegmentJob, RecommendationJob, ContentJob, User
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# Isso cria as tabelas no Postgres automaticamente
Base.metadata.create_all(bind=engine)


# ------------------------------------------------------------------ #
# Scheduler: enfileira jobs de segmentação diariamente às 2h UTC
# ------------------------------------------------------------------ #

async def _lifecycle_scheduler():
    """Loop que enfileira jobs de segmentação para cada tenant às 2h UTC."""
    while True:
        try:
            # Calcula tempo até próximas 2h UTC
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            wait_secs = (next_run - now).total_seconds()
            logger.info("Scheduler: próximo ciclo em %.0f segundos (às %s UTC)", wait_secs, next_run.strftime("%H:%M"))
            await asyncio.sleep(wait_secs)

            # Enfileira jobs para todos os tenants
            db = SessionLocal()
            try:
                tenant_ids = [
                    row[0] for row in
                    db.query(User.tenant_id).distinct().all()
                ]

                enqueued_seg = 0
                enqueued_rec = 0
                for tid in tenant_ids:
                    # Lifecycle jobs
                    existing_seg = db.query(SegmentJob).filter(
                        SegmentJob.tenant_id == tid,
                        SegmentJob.status.in_(["queued", "running"]),
                    ).first()
                    if not existing_seg:
                        db.add(SegmentJob(
                            id=uuid.uuid4(),
                            tenant_id=tid,
                            status="queued",
                            priority=1,
                            triggered_by="scheduler",
                        ))
                        enqueued_seg += 1

                    # Recommendation jobs
                    existing_rec = db.query(RecommendationJob).filter(
                        RecommendationJob.tenant_id == tid,
                        RecommendationJob.status.in_(["queued", "running"]),
                    ).first()
                    if not existing_rec:
                        db.add(RecommendationJob(
                            id=uuid.uuid4(),
                            tenant_id=tid,
                            status="queued",
                            priority=1,
                            triggered_by="scheduler",
                        ))
                        enqueued_rec += 1

                db.commit()
                logger.info("Scheduler: %d lifecycle + %d recommendation jobs para %d tenants",
                            enqueued_seg, enqueued_rec, len(tenant_ids))
            finally:
                db.close()

        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Erro no scheduler de lifecycle")
            await asyncio.sleep(60)


def _reset_stuck_jobs():
    """Reset jobs travados em queued/running após reinício do servidor."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        stuck_seg = db.query(SegmentJob).filter(
            SegmentJob.status.in_(["queued", "running"]),
        ).all()
        for job in stuck_seg:
            job.status = "failed"
            job.finished_at = now
            job.error_msg = "Auto-reset — servidor reiniciado"

        stuck_rec = db.query(RecommendationJob).filter(
            RecommendationJob.status.in_(["queued", "running"]),
        ).all()
        for job in stuck_rec:
            job.status = "failed"
            job.finished_at = now
            job.error_msg = "Auto-reset — servidor reiniciado"

        stuck_content = db.query(ContentJob).filter(
            ContentJob.status.in_(["queued", "running"]),
        ).all()
        for job in stuck_content:
            job.status = "failed"
            job.finished_at = now
            job.error_msg = "Auto-reset — servidor reiniciado"

        total = len(stuck_seg) + len(stuck_rec) + len(stuck_content)
        if total:
            db.commit()
            logger.info("Startup: %d jobs travados resetados (%d seg + %d rec + %d content)",
                        total, len(stuck_seg), len(stuck_rec), len(stuck_content))
    except Exception:
        logger.exception("Erro ao resetar jobs travados no startup")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Reset jobs travados, inicia scheduler, cancela no shutdown."""
    _reset_stuck_jobs()
    task = asyncio.create_task(_lifecycle_scheduler())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

tags_metadata = [
    # --- Acesso ---
    {"name": "Autenticação",              "description": "Login e registro de usuários"},

    # --- Catálogo ---
    {"name": "Produtos",                  "description": "Gestão de catálogo de produtos"},
    {"name": "Preços",                    "description": "Preços por canal e loja"},
    {"name": "Estoque",                   "description": "Estoque por canal e loja"},
    {"name": "Ofertas",                   "description": "Promoções por produto, canal, loja e audiência"},
    {"name": "Pedidos",                   "description": "Histórico de pedidos e itens"},

    # --- Clientes ---
    {"name": "Clientes",                  "description": "Gestão de clientes"},

    # --- Canais & Lojas ---
    {"name": "Canais",                    "description": "Canais de venda (web, app, loja física, televendas)"},
    {"name": "Lojas",                     "description": "Lojas físicas e virtuais"},

    # --- Configuração ---
    {"name": "Configurações do Tenant",   "description": "Parâmetros gerais do tenant"},
    {"name": "Dashboard",                 "description": "Métricas e painéis"},

    # --- IA ---
    {"name": "Busca",                     "description": "Busca semântica e híbrida no catálogo"},
    {"name": "Recomendação",              "description": "Modelos de recomendação por contexto"},
    {"name": "Ciclo de Vida",             "description": "Segmentação e indicadores de lifecycle do cliente"},
    {"name": "Recomendação Personalizada", "description": "Recomendações por cliente (pessoal, descoberta, top sellers)"},
    {"name": "Conteúdo Personalizado",    "description": "Templates e conteúdo renderizado por canal (email, whatsapp, push)"},
    {"name": "API Keys",                   "description": "Gerenciamento de API Keys para acesso programático"},
]

app = FastAPI(title="SaaS AI Recommender API", openapi_tags=tags_metadata, lifespan=lifespan, redirect_slashes=False)

# --- CORS
if settings.CORS_ORIGINS.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, PUT, DELETE
    allow_headers=["*"], # Permite enviar Tokens JWT
)
# -------------------------------------------------

app.include_router(auth.router,         prefix="/api/v1/auth",       tags=["Autenticação"])
app.include_router(products.router,     prefix="/api/v1/products",   tags=["Produtos"])
app.include_router(prices.router,       prefix="/api/v1/prices",     tags=["Preços"])
app.include_router(stock.router,        prefix="/api/v1/stock",      tags=["Estoque"])
app.include_router(customers.router,    prefix="/api/v1/customers",  tags=["Clientes"])
app.include_router(channels.router,     prefix="/api/v1/channels",   tags=["Canais"])
app.include_router(stores.router,       prefix="/api/v1/stores",     tags=["Lojas"])
app.include_router(offers.router,       prefix="/api/v1/offers",     tags=["Ofertas"])
app.include_router(orders.router,       prefix="/api/v1/orders",     tags=["Pedidos"])
app.include_router(tenant_config.router,prefix="/api/v1/config",     tags=["Configurações do Tenant"])
app.include_router(dashboards.router,   prefix="/api/v1/dashboards", tags=["Dashboard"])
app.include_router(search.router,       prefix="/api/v1/search",     tags=["Busca"])
app.include_router(recommend.router,    prefix="/api/v1/recommend",  tags=["Recomendação"])
app.include_router(lifecycle.router,        prefix="/api/v1/lifecycle",        tags=["Ciclo de Vida"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations",  tags=["Recomendação Personalizada"])
app.include_router(content_templates.router, prefix="/api/v1/content",          tags=["Conteúdo Personalizado"])
app.include_router(content.router,         prefix="/api/v1/content",          tags=["Conteúdo Personalizado"])
app.include_router(admin_cleanup.router,  prefix="/api/v1/admin",             tags=["Administração"])
app.include_router(api_keys.router,      prefix="/api/v1",               tags=["API Keys"])

@app.get("/")
def root():
    return {"status": "Sistema Online", "version": "1.0.0"}