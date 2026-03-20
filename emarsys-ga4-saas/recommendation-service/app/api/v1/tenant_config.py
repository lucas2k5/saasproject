import uuid
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, TenantConfig, SegmentJob
from app.api.v1.lifecycle import _run_lifecycle_inline

logger = logging.getLogger(__name__)

router = APIRouter()

_DEFAULTS = dict(
    price_threshold_low=0.9,
    price_threshold_high=1.1,
    similarity_threshold=0.7,
    recommendation_limit=10,
    recommendation_category_level=0,
    onetime_days_as_customer_min=60,
    onetime_p_alive_max=0.3,
    nonengaged_p_alive_max=0.2,
    nonengaged_recency_min=180,
    nonengaged_velocity_trend_max=0.3,
    loyalstar_regularity_max=0.6,
    loyalstar_velocity_trend_min=0.9,
    loyalstar_ticket_trend_min=0.9,
    loyalstar_category_diversity_min=3,
    loyalstar_p_alive_min=0.7,
    loyalrunner_regularity_max=0.8,
    loyalrunner_velocity_trend_min=0.9,
    loyalrunner_p_alive_min=0.5,
)

# Defaults separados para campos S3/content (não editáveis via PUT /config)
_S3_DEFAULTS = dict(
    s3_bucket_name=None,
    s3_access_key=None,
    s3_secret_key=None,
    s3_region="us-east-1",
    s3_presigned_expiration_hours=168,
    content_max_products_email=6,
    content_max_products_whatsapp=3,
    content_max_products_push=1,
)


class ConfigUpdate(BaseModel):
    # IA & Recomendações
    price_threshold_low: float
    price_threshold_high: float
    similarity_threshold: float
    recommendation_limit: int
    recommendation_category_level: int

    # OneTime
    onetime_days_as_customer_min: int
    onetime_p_alive_max: float

    # NonEngaged
    nonengaged_p_alive_max: float
    nonengaged_recency_min: int
    nonengaged_velocity_trend_max: float

    # LoyalStar
    loyalstar_regularity_max: float
    loyalstar_velocity_trend_min: float
    loyalstar_ticket_trend_min: float
    loyalstar_category_diversity_min: int
    loyalstar_p_alive_min: float

    # LoyalRunner
    loyalrunner_regularity_max: float
    loyalrunner_velocity_trend_min: float
    loyalrunner_p_alive_min: float

    class Config:
        from_attributes = True


def _config_to_dict(config: TenantConfig) -> dict:
    """Serializa TenantConfig para dict com defaults para colunas novas (nullable)."""
    d = {}
    for field, default in _DEFAULTS.items():
        val = getattr(config, field, None)
        d[field] = val if val is not None else default
    # S3 + content fields
    for field, default in _S3_DEFAULTS.items():
        val = getattr(config, field, None)
        # Mask secret key
        if field == "s3_secret_key" and val:
            d[field] = "***"
        elif field == "s3_access_key" and val:
            d[field] = val[:4] + "***" + val[-4:] if len(val) > 8 else "***"
        else:
            d[field] = val if val is not None else default
    d["id"] = config.id
    d["tenant_id"] = config.tenant_id
    d["config_suggestions"] = config.config_suggestions or {}
    d["suggested_at"] = config.suggested_at.isoformat() if config.suggested_at else None
    return d


@router.get("/")
def get_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(TenantConfig).filter(TenantConfig.tenant_id == current_user.tenant_id).first()
    if not config:
        config = TenantConfig(tenant_id=current_user.tenant_id, **_DEFAULTS)
        db.add(config)
        db.commit()
        db.refresh(config)
    return _config_to_dict(config)


_VALIDATION_RULES: dict = {
    "price_threshold_low":              (float, 0.0, 2.0),
    "price_threshold_high":             (float, 0.0, 5.0),
    "similarity_threshold":             (float, 0.0, 1.0),
    "recommendation_limit":             (int, 1, 100),
    "recommendation_category_level":    (int, 0, 5),
    "onetime_days_as_customer_min":     (int, 1, 730),
    "onetime_p_alive_max":              (float, 0.0, 1.0),
    "nonengaged_p_alive_max":           (float, 0.0, 1.0),
    "nonengaged_recency_min":           (int, 1, 730),
    "nonengaged_velocity_trend_max":    (float, 0.0, 10.0),
    "loyalstar_regularity_max":         (float, 0.0, 10.0),
    "loyalstar_velocity_trend_min":     (float, 0.0, 10.0),
    "loyalstar_ticket_trend_min":       (float, 0.0, 10.0),
    "loyalstar_category_diversity_min": (int, 0, 100),
    "loyalstar_p_alive_min":            (float, 0.0, 1.0),
    "loyalrunner_regularity_max":       (float, 0.0, 10.0),
    "loyalrunner_velocity_trend_min":   (float, 0.0, 10.0),
    "loyalrunner_p_alive_min":          (float, 0.0, 1.0),
}


@router.put("/")
def update_config(
    config_in: ConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(TenantConfig).filter(TenantConfig.tenant_id == current_user.tenant_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found. Use GET to create a default config first.")

    errors = []
    for field, (typ, lo, hi) in _VALIDATION_RULES.items():
        val = getattr(config_in, field, None)
        if val is not None and not (lo <= val <= hi):
            errors.append(f"{field} deve estar entre {lo} e {hi} (recebido: {val})")
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    for field in _DEFAULTS:
        setattr(config, field, getattr(config_in, field))

    db.commit()
    db.refresh(config)
    return _config_to_dict(config)


@router.post("/apply-suggestions")
def apply_suggestions(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aplica todas as sugestões calculadas pelo job ao TenantConfig atual
    e dispara recalculação dos segmentos em background.
    """
    tenant_id = current_user.tenant_id

    config = db.query(TenantConfig).filter(TenantConfig.tenant_id == tenant_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found.")
    if not config.config_suggestions:
        raise HTTPException(status_code=400, detail="No suggestions available.")

    applied = []
    for field, value in config.config_suggestions.items():
        if hasattr(config, field) and value is not None:
            setattr(config, field, value)
            applied.append(field)

    config.config_suggestions = {}
    config.suggested_at = None
    db.commit()
    db.refresh(config)

    # Dispara recalculação dos segmentos com os novos thresholds
    existing = db.query(SegmentJob).filter(
        SegmentJob.tenant_id == tenant_id,
        SegmentJob.status.in_(["queued", "running"]),
    ).first()

    job_id = None
    if not existing:
        job = SegmentJob(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            status="queued",
            priority=0,
            triggered_by="apply_suggestions",
        )
        db.add(job)
        db.commit()
        job_id = job.id
        background_tasks.add_task(_run_lifecycle_inline, job_id, tenant_id)
        logger.info("Tenant %s: recalculação disparada após apply-suggestions", tenant_id)

    return {
        **_config_to_dict(config),
        "applied_fields": applied,
        "recalculating": job_id is not None,
        "job_id": str(job_id) if job_id else None,
    }


class S3ConfigUpdate(BaseModel):
    s3_bucket_name: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str = "us-east-1"
    s3_presigned_expiration_hours: int = 168
    content_max_products_email: int = 6
    content_max_products_whatsapp: int = 3
    content_max_products_push: int = 1


_S3_VALIDATION = {
    "s3_presigned_expiration_hours": (int, 1, 720),
    "content_max_products_email": (int, 1, 20),
    "content_max_products_whatsapp": (int, 1, 5),
    "content_max_products_push": (int, 1, 3),
}


@router.put("/s3")
def update_s3_config(
    config_in: S3ConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza configurações de S3 e limites de conteúdo."""
    config = db.query(TenantConfig).filter(TenantConfig.tenant_id == current_user.tenant_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found. Use GET to create a default config first.")

    errors = []
    for field, (typ, lo, hi) in _S3_VALIDATION.items():
        val = getattr(config_in, field, None)
        if val is not None and not (lo <= val <= hi):
            errors.append(f"{field} deve estar entre {lo} e {hi} (recebido: {val})")
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    for field in _S3_DEFAULTS:
        new_val = getattr(config_in, field, None)
        # Don't overwrite secret with masked value
        if field == "s3_secret_key" and new_val == "***":
            continue
        if field == "s3_access_key" and new_val and "***" in new_val:
            continue
        if new_val is not None:
            setattr(config, field, new_val)

    db.commit()
    db.refresh(config)
    return _config_to_dict(config)
