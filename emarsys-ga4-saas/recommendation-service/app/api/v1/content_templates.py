# backend/app/api/v1/content_templates.py
"""
CRUD de templates de conteúdo personalizado.

Templates Jinja2/JSON configurados pelo tenant, 1 por (canal, offer_type).
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jinja2 import Environment, BaseLoader, TemplateSyntaxError

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, ContentTemplate, VALID_TEMPLATE_OFFER_TYPES
from app.services.content_service import _render_email_modular, MASTER_EMAIL_LAYOUT, DEFAULT_FOOTER_HTML

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_CHANNELS = {"email", "whatsapp", "push"}


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class TemplateCreate(BaseModel):
    channel: str
    offer_type: str
    name: str
    body: str
    is_active: bool = True

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    body: Optional[str] = None
    is_active: Optional[bool] = None

class PreviewRequest(BaseModel):
    customer_name: str = "Maria Silva"


def _serialize(t: ContentTemplate) -> dict:
    return {
        "id": str(t.id),
        "tenant_id": t.tenant_id,
        "channel": t.channel,
        "offer_type": t.offer_type,
        "name": t.name,
        "body": t.body,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


# ------------------------------------------------------------------ #
# Endpoints
# ------------------------------------------------------------------ #

@router.get("/templates")
def list_templates(
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = current_user.tenant_id
    q = db.query(ContentTemplate).filter(ContentTemplate.tenant_id == tenant_id)
    if channel:
        q = q.filter(ContentTemplate.channel == channel)
    q = q.order_by(ContentTemplate.channel, ContentTemplate.offer_type)
    return [_serialize(t) for t in q.all()]


@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.tenant_id == current_user.tenant_id,
    ).first()
    if not t:
        raise HTTPException(404, "Template não encontrado")
    return _serialize(t)


@router.post("/templates")
def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.channel not in VALID_CHANNELS:
        raise HTTPException(422, f"Canal inválido. Use: {', '.join(sorted(VALID_CHANNELS))}")
    if data.offer_type not in VALID_TEMPLATE_OFFER_TYPES:
        raise HTTPException(422, f"Tipo de oferta inválido. Use: {', '.join(sorted(VALID_TEMPLATE_OFFER_TYPES))}")

    tenant_id = current_user.tenant_id
    existing = db.query(ContentTemplate).filter(
        ContentTemplate.tenant_id == tenant_id,
        ContentTemplate.channel == data.channel,
        ContentTemplate.offer_type == data.offer_type,
    ).first()
    if existing:
        raise HTTPException(409, f"Já existe template para {data.channel}/{data.offer_type}")

    t = ContentTemplate(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        channel=data.channel,
        offer_type=data.offer_type,
        name=data.name,
        body=data.body,
        is_active=data.is_active,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _serialize(t)


@router.put("/templates/{template_id}")
def update_template(
    template_id: str,
    data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.tenant_id == current_user.tenant_id,
    ).first()
    if not t:
        raise HTTPException(404, "Template não encontrado")

    if data.name is not None:
        t.name = data.name
    if data.body is not None:
        t.body = data.body
    if data.is_active is not None:
        t.is_active = data.is_active

    db.commit()
    db.refresh(t)
    return _serialize(t)


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.tenant_id == current_user.tenant_id,
    ).first()
    if not t:
        raise HTTPException(404, "Template não encontrado")

    db.delete(t)
    db.commit()
    return {"deleted": True}


def _sample_product_for_offer_type(offer_type: str) -> dict:
    """Retorna 1 produto sample adequado ao offer_type para preview de card."""
    samples = {
        "COMBO": {
            "name": "Kit Churrasco Completo",
            "image_url": "https://placehold.co/120x120?text=Kit",
            "base_price": 89.90,
            "has_offer": True, "offer_type": "COMBO",
            "offer_price": 69.90, "offer_name": "Combo Churrasco -22%",
            "category": "Alimentos > Carnes", "layout": "full",
        },
        "PROGRESSIVE": {
            "name": "Cerveja Premium 350ml",
            "image_url": "https://placehold.co/120x120?text=Cerveja",
            "base_price": 7.90,
            "has_offer": True, "offer_type": "PROGRESSIVE",
            "offer_price": 5.90, "offer_name": "10% na 2a, 20% na 3a",
            "category": "Bebidas > Alcoólicas", "layout": "full",
        },
        "BUY_X_GET_PRODUCT": {
            "name": "Whisky 1L",
            "image_url": "https://placehold.co/120x120?text=Whisky",
            "base_price": 129.90,
            "has_offer": True, "offer_type": "BUY_X_GET_PRODUCT",
            "offer_price": 129.90, "offer_name": "Compre 1 Ganhe 1 Copo",
            "category": "Bebidas > Destilados", "layout": "full",
        },
        "DIRECT_DISCOUNT": {
            "name": "Café Premium 500g",
            "image_url": "https://placehold.co/120x120?text=Cafe",
            "base_price": 29.90,
            "has_offer": True, "offer_type": "DIRECT_DISCOUNT",
            "offer_price": 22.90, "offer_name": "Desconto Direto 23%",
            "category": "Alimentos > Bebidas", "layout": "grid",
        },
        "TAKE_X_PAY_Y": {
            "name": "Sabão em Pó 1kg",
            "image_url": "https://placehold.co/120x120?text=Sabao",
            "base_price": 15.90,
            "has_offer": True, "offer_type": "TAKE_X_PAY_Y",
            "offer_price": 12.90, "offer_name": "Leve 3 Pague 2",
            "category": "Limpeza", "layout": "grid",
        },
        "CASHBACK": {
            "name": "Amaciante 2L",
            "image_url": "https://placehold.co/120x120?text=Amac",
            "base_price": 12.90,
            "has_offer": True, "offer_type": "CASHBACK",
            "offer_price": 12.90, "offer_name": "10% Cashback",
            "category": "Limpeza", "layout": "grid",
        },
    }
    return samples.get(offer_type, {
        "name": "Leite Integral 1L",
        "image_url": "https://placehold.co/120x120?text=Leite",
        "base_price": 6.50,
        "has_offer": False, "offer_type": offer_type,
        "offer_price": None, "offer_name": None,
        "category": "Alimentos > Laticínios", "layout": "grid",
    })


@router.post("/templates/{template_id}/preview")
def preview_template(
    template_id: str,
    data: PreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Renderiza preview de um template individual.
    - Email card: renderiza com 1 produto sample como {{p}}
    - Email __FOOTER__: renderiza com store_name, store_address, offers_valid_until
    - WhatsApp/Push: sem mudança
    """
    t = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.tenant_id == current_user.tenant_id,
    ).first()
    if not t:
        raise HTTPException(404, "Template não encontrado")

    try:
        env = Environment(loader=BaseLoader(), autoescape=False)

        if t.channel == "email" and t.offer_type == "__FOOTER__":
            rendered = env.from_string(t.body).render(
                store_name="Loja Centro",
                store_address="Rua das Flores, 123 - Centro",
                offers_valid_until="31/03/2026",
            )
        elif t.channel == "email":
            sample = _sample_product_for_offer_type(t.offer_type)
            rendered = env.from_string(t.body).render(p=sample)
        else:
            # WhatsApp / Push — mantém comportamento original
            sample_products = [
                _sample_product_for_offer_type("COMBO"),
                _sample_product_for_offer_type("DIRECT_DISCOUNT"),
                _sample_product_for_offer_type("__GENERIC__"),
            ]
            rendered = env.from_string(t.body).render(
                customer_name=data.customer_name,
                products=sample_products,
                product=sample_products[0],
                store_name="Loja Centro",
                store_address="Rua das Flores, 123 - Centro",
                offers_valid_until="31/03/2026",
            )
    except TemplateSyntaxError as e:
        raise HTTPException(422, f"Erro de sintaxe no template: {e}")
    except Exception as e:
        raise HTTPException(422, f"Erro ao renderizar: {e}")

    return {
        "channel": t.channel,
        "offer_type": t.offer_type,
        "rendered": rendered,
    }


@router.post("/templates/preview-assembled")
def preview_assembled(
    data: PreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Monta preview completo do email com master layout + todos os card templates + footer.
    Usa dados sample para simular um email real.
    """
    tenant_id = current_user.tenant_id
    templates = db.query(ContentTemplate).filter(
        ContentTemplate.tenant_id == tenant_id,
        ContentTemplate.channel == "email",
        ContentTemplate.is_active == True,
    ).all()

    card_templates: dict[str, ContentTemplate] = {}
    footer_template = None
    for t in templates:
        if t.offer_type == "__FOOTER__":
            footer_template = t
        else:
            card_templates[t.offer_type] = t

    if not card_templates:
        raise HTTPException(404, "Nenhum card template de email ativo encontrado")

    # Produtos sample variados para demonstrar o layout misto
    sample_products = [
        _sample_product_for_offer_type("COMBO"),
        _sample_product_for_offer_type("DIRECT_DISCOUNT"),
        _sample_product_for_offer_type("TAKE_X_PAY_Y"),
        _sample_product_for_offer_type("CASHBACK"),
        _sample_product_for_offer_type("__GENERIC__"),
    ]

    try:
        env = Environment(loader=BaseLoader(), autoescape=False)
        # Pre-compile templates for the new signature
        compiled_cards = {ot: env.from_string(tpl.body) for ot, tpl in card_templates.items()}
        compiled_footer = env.from_string(footer_template.body) if footer_template else env.from_string(DEFAULT_FOOTER_HTML)
        compiled_master = env.from_string(MASTER_EMAIL_LAYOUT)
        rendered = _render_email_modular(
            env,
            compiled_cards,
            compiled_footer,
            compiled_master,
            sample_products,
            data.customer_name,
            {"name": "Loja Centro", "address": "Rua das Flores, 123 - Centro"},
            "31/03/2026",
        )
    except TemplateSyntaxError as e:
        raise HTTPException(422, f"Erro de sintaxe no template: {e}")
    except Exception as e:
        raise HTTPException(422, f"Erro ao renderizar email montado: {e}")

    return {
        "channel": "email",
        "rendered": rendered,
    }
