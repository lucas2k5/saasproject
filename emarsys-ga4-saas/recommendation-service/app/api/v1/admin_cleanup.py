"""Endpoints de limpeza (purge) de entidades por tenant.

DELETE /admin/purge/{entity} — remove TODOS os registros da entidade para o tenant.
Projetado para facilitar reimportação de dados sem ruído de registros antigos.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import (
    User, Order, OrderItem, Customer, Offer, OfferProduct, OfferAudience,
    ProductPrice, ProductStock, CustomerOrderSummary, CustomerSegment,
    CustomerRecommendation, StoreTopSeller, ProductSimilar,
    SegmentJob, RecommendationJob,
    ContentTemplate, ContentEmail, ContentWhatsapp, ContentPush, ContentJob,
)

router = APIRouter()

# Mapa de entidades disponíveis para purge.
# Ordem importa quando há FKs — filhos antes dos pais.
ENTITY_MAP = {
    "order_items":       OrderItem,
    "orders":            Order,
    "offer_products":    OfferProduct,
    "offer_audiences":   OfferAudience,
    "offers":            Offer,
    "prices":            ProductPrice,
    "stock":             ProductStock,
    "customer_summary":  CustomerOrderSummary,
    "customer_segments": CustomerSegment,
    "customer_recs":     CustomerRecommendation,
    "top_sellers":       StoreTopSeller,
    "product_similars":  ProductSimilar,
    "segment_jobs":      SegmentJob,
    "rec_jobs":          RecommendationJob,
    "content_templates": ContentTemplate,
    "content_email":     ContentEmail,
    "content_whatsapp":  ContentWhatsapp,
    "content_push":      ContentPush,
    "content_jobs":      ContentJob,
}

# Grupos pré-definidos para limpeza em cascata
GROUPS = {
    "orders":      ["order_items", "orders", "customer_summary", "customer_segments", "customer_recs"],
    "offers":      ["offer_products", "offer_audiences", "offers"],
    "stock":       ["stock"],
    "prices":      ["prices"],
    "lifecycle":   ["customer_summary", "customer_segments"],
    "recs":        ["customer_recs", "top_sellers", "product_similars"],
    "jobs":        ["segment_jobs", "rec_jobs", "content_jobs"],
    "content":     ["content_email", "content_whatsapp", "content_push", "content_templates", "content_jobs"],
}


@router.delete("/purge/{entity}")
def purge_entity(
    entity: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove todos os registros de uma entidade (ou grupo) para o tenant atual."""
    tenant_id = current_user.tenant_id

    # Se for um grupo, resolve as entidades
    entities = GROUPS.get(entity, [entity])

    total_deleted = 0
    details = {}

    for ent in entities:
        model = ENTITY_MAP.get(ent)
        if not model:
            continue
        count = db.query(model).filter(model.tenant_id == tenant_id).delete(synchronize_session=False)
        details[ent] = count
        total_deleted += count

    db.commit()

    return {
        "entity": entity,
        "total_deleted": total_deleted,
        "details": details,
    }


@router.get("/purge/entities")
def list_purgeable_entities(
    current_user: User = Depends(get_current_user),
):
    """Lista as entidades e grupos disponíveis para purge."""
    return {
        "entities": list(ENTITY_MAP.keys()),
        "groups": {k: v for k, v in GROUPS.items()},
    }
