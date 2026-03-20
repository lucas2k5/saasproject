# backend/app/services/content_service.py
"""
Motor de geração de conteúdo personalizado (Email HTML, WhatsApp PNG, Push).

Consome recomendações pré-computadas e templates Jinja2 do tenant para gerar
conteúdo pronto para envio por canal.
"""
import io
import json
import logging
import os
import uuid
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import boto3
import requests
from botocore.config import Config as BotoConfig
from jinja2 import Environment, BaseLoader
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import text
from sqlalchemy.orm import Session

from markupsafe import Markup

from app.db.models import (
    TenantConfig, ContentTemplate, ContentEmail, ContentWhatsapp, ContentPush,
    CustomerRecommendation, Customer, Store,
)
from app.db.session import SessionLocal

# Tipos de oferta que usam layout full-width (1 coluna) no email
COMPLEX_OFFER_TYPES = {"COMBO", "PROGRESSIVE", "BUY_X_GET_PRODUCT"}

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Master Email Layout — estrutura fixa, não editável pelo tenant
# Slots: customer_name, complex_cards_html, grid_cards_html, footer_html
# ------------------------------------------------------------------ #
MASTER_EMAIL_LAYOUT = """\
<html>
<body style="margin:0; padding:0; background-color:#f4f4f7; font-family:Arial, Helvetica, sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7; padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.06);">

  <!-- OFERTAS COMPLEXAS — Full width, 1 coluna -->
  {% if complex_cards_html %}
  <tr><td style="padding:16px 32px 4px;">
    <p style="margin:0; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#7C3AED;">Ofertas em destaque</p>
  </td></tr>
  {{complex_cards_html}}
  {% endif %}

  <!-- OFERTAS SIMPLES — Grid 2 colunas -->
  {% if grid_cards_html %}
  <tr><td style="padding:16px 32px 4px;">
    <p style="margin:0; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#7C3AED;">{% if complex_cards_html %}Mais produtos para voc\u00ea{% else %}Produtos selecionados{% endif %}</p>
  </td></tr>
  <tr><td style="padding:4px 24px 12px;">
    <table width="100%" cellpadding="0" cellspacing="0">
      {{grid_cards_html}}
    </table>
  </td></tr>
  {% endif %}

  <!-- CTA -->
  <tr><td style="padding:20px 32px; text-align:center;">
    <p style="margin:0; color:#6b7280; font-size:13px;">Aproveite as ofertas selecionadas para o seu perfil!</p>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="background:#f9fafb; padding:16px 32px; text-align:center; border-top:1px solid #e5e7eb;">
    {{footer_html}}
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

DEFAULT_FOOTER_HTML = """\
{% if offers_valid_until %}
<p style="margin:0 0 6px; font-size:11px; color:#6b7280; font-weight:600;">Ofertas v\u00e1lidas at\u00e9 {{offers_valid_until}}</p>
{% endif %}
{% if store_name %}
<p style="margin:0 0 4px; font-size:11px; color:#9ca3af;">{{store_name}}{% if store_address %} &mdash; {{store_address}}{% endif %}</p>
{% endif %}
<p style="margin:4px 0 0; font-size:10px; color:#9ca3af;">Produtos selecionados com base no seu hist\u00f3rico de compras. Ofertas sujeitas a disponibilidade.</p>"""

CHUNK_SIZE = 5000
FONT_PATH = str(Path(__file__).parent.parent / "assets" / "fonts" / "NotoSans-Regular.ttf")

# PNG constants
PNG_WIDTH = 600
PRODUCT_HEIGHT = 160
HEADER_HEIGHT = 80
FOOTER_HEIGHT = 60
THUMBNAIL_SIZE = (120, 120)
PADDING = 20


class ContentService:
    """Gera conteúdo personalizado para email, whatsapp e push."""

    @staticmethod
    def run_for_tenant(
        tenant_id: str,
        db: Session,
        channels: Optional[list[str]] = None,
    ) -> dict:
        """
        Gera conteúdo para todos os clientes com recomendações.

        Returns dict com contadores: customers_processed, emails, images, push.
        """
        config = db.query(TenantConfig).filter(TenantConfig.tenant_id == tenant_id).first()
        if not config:
            raise ValueError(f"TenantConfig não encontrado para {tenant_id}")

        # Canais a processar
        target_channels = set(channels or ["email", "whatsapp", "push"])

        # Carrega templates ativos
        templates = db.query(ContentTemplate).filter(
            ContentTemplate.tenant_id == tenant_id,
            ContentTemplate.is_active == True,
        ).all()

        template_map: dict[str, dict[str, ContentTemplate]] = {}
        for t in templates:
            if t.channel not in target_channels:
                continue
            template_map.setdefault(t.channel, {})[t.offer_type] = t

        if not template_map:
            logger.warning("Tenant %s: nenhum template ativo para canais %s", tenant_id, target_channels)
            return {"customers_processed": 0, "emails": 0, "images": 0, "push": 0}

        # S3 client (lazy) + limpeza de imagens antigas
        s3_client = None
        needs_s3 = ("whatsapp" in template_map or "push" in template_map) and config.s3_bucket_name
        if needs_s3:
            s3_client = _get_s3_client(config)
            _cleanup_s3_images(s3_client, config.s3_bucket_name, tenant_id)

        # Carrega mapa de customers (id → info)
        customer_rows = db.execute(text("""
            SELECT id, tenant_id, customer_id, customer_add_id, name
            FROM customers WHERE tenant_id = :tid
        """), {"tid": tenant_id}).fetchall()
        customer_map = {
            str(r[0]): {
                "id": r[0], "external_id": r[1 + 1], "add_id": r[3], "name": r[4],
            }
            for r in customer_rows
        }

        # Carrega lojas (id → {name, address})
        store_rows = db.execute(text("""
            SELECT id, name, address FROM stores WHERE tenant_id = :tid
        """), {"tid": tenant_id}).fetchall()
        store_map = {str(r[0]): {"name": r[1], "address": r[2]} for r in store_rows}

        # Limites por canal
        max_email = config.content_max_products_email or 6
        max_whatsapp = config.content_max_products_whatsapp or 3
        max_push = config.content_max_products_push or 1

        jinja_env = Environment(loader=BaseLoader(), autoescape=False)
        presign_hours = config.s3_presigned_expiration_hours or 168
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        counters = {"customers_processed": 0, "emails": 0, "images": 0, "push": 0}
        counted_customers: set[str] = set()

        # Pre-compile Jinja2 templates (once, outside the loop)
        compiled_card_templates: dict[str, object] = {}
        compiled_footer_template = None
        compiled_master_template = jinja_env.from_string(MASTER_EMAIL_LAYOUT)
        if "email" in template_map:
            for ot, tpl in template_map["email"].items():
                if ot == "__FOOTER__":
                    compiled_footer_template = jinja_env.from_string(tpl.body)
                else:
                    compiled_card_templates[ot] = jinja_env.from_string(tpl.body)
            if compiled_footer_template is None:
                compiled_footer_template = jinja_env.from_string(DEFAULT_FOOTER_HTML)

        # Chunked processing: query DISTINCT customer_ids, then process in batches
        all_customer_ids = db.execute(text("""
            SELECT DISTINCT customer_id FROM customer_recommendations_current
            WHERE tenant_id = :tid
        """), {"tid": tenant_id}).fetchall()
        all_customer_ids = [str(r[0]) for r in all_customer_ids]

        for chunk_start in range(0, len(all_customer_ids), CHUNK_SIZE):
            chunk_cids = all_customer_ids[chunk_start:chunk_start + CHUNK_SIZE]

            # Fetch recommendations only for this chunk of customers
            recs = db.execute(text("""
                SELECT customer_id, product_id, product_external_id, product_name,
                       product_image_url, product_category, base_price,
                       has_offer, offer_type, offer_price, offer_name, rank, algorithm, score,
                       offer_end_at, store_id
                FROM customer_recommendations_current
                WHERE tenant_id = :tid AND customer_id = ANY(:cids)
                ORDER BY customer_id, algorithm, rank
            """), {"tid": tenant_id, "cids": chunk_cids}).fetchall()

            # Agrupa por (customer_id, algorithm) + guarda store_id por customer
            recs_by_cust_algo: dict[tuple[str, str], list[dict]] = {}
            customer_store: dict[str, str] = {}  # customer_id → store_id
            for r in recs:
                cid = str(r[0])
                algo = r[12]
                if cid not in customer_store and r[15]:
                    customer_store[cid] = str(r[15])
                recs_by_cust_algo.setdefault((cid, algo), []).append({
                    "product_id": r[1],
                    "product_external_id": r[2],
                    "name": r[3],
                    "image_url": r[4],
                    "category": r[5],
                    "base_price": r[6],
                    "has_offer": r[7],
                    "offer_type": r[8],
                    "offer_price": r[9],
                    "offer_name": r[10],
                    "rank": r[11],
                    "algorithm": algo,
                    "score": r[13],
                    "offer_end_at": r[14],
                })

            email_rows = []
            whatsapp_rows = []
            push_rows = []

            for (cid, algo) in recs_by_cust_algo:
                cinfo = customer_map.get(cid)
                if not cinfo:
                    continue

                if cid not in counted_customers:
                    counters["customers_processed"] += 1
                    counted_customers.add(cid)

                products = recs_by_cust_algo[(cid, algo)]

                # Store info (mesma para todos os algoritmos do cliente)
                sid = customer_store.get(cid)
                store_info = store_map.get(sid, {}) if sid else {}

                # Menor data de expiração das ofertas deste algoritmo
                offer_dates = [p["offer_end_at"] for p in products if p.get("offer_end_at")]
                offers_valid_until = None
                if offer_dates:
                    min_date = min(offer_dates)
                    if hasattr(min_date, 'strftime'):
                        offers_valid_until = min_date.strftime("%d/%m/%Y")
                    else:
                        offers_valid_until = str(min_date)[:10]

                # --- EMAIL ---
                if "email" in template_map and compiled_card_templates:
                    try:
                        rendered = _render_email_modular(
                            jinja_env,
                            compiled_card_templates,
                            compiled_footer_template,
                            compiled_master_template,
                            products[:max_email],
                            cinfo["name"],
                            store_info,
                            offers_valid_until,
                        )
                        email_rows.append({
                            "id": uuid.uuid4(),
                            "tenant_id": tenant_id,
                            "customer_id": cinfo["id"],
                            "algorithm": algo,
                            "customer_external_id": cinfo["external_id"],
                            "customer_add_id": cinfo["add_id"],
                            "customer_name": cinfo["name"],
                            "html_body": rendered,
                            "products_count": len(products[:max_email]),
                            "computed_at": datetime.now(timezone.utc),
                        })
                        counters["emails"] += 1
                    except Exception:
                        logger.warning("Email render falhou para customer %s algo %s", cid, algo, exc_info=True)

                # --- WHATSAPP ---
                if "whatsapp" in template_map and s3_client:
                    wa_products = products[:max_whatsapp]
                    tpl = _select_template(template_map["whatsapp"], wa_products)
                    if tpl:
                        try:
                            png_bytes = _generate_whatsapp_png(
                                tpl, cinfo["name"], wa_products, jinja_env,
                                store_info=store_info,
                                offers_valid_until=offers_valid_until,
                            )
                            s3_key = f"{tenant_id}/content/{today_str}/{cid}_{algo}_whatsapp.png"
                            s3_client.put_object(
                                Bucket=config.s3_bucket_name,
                                Key=s3_key,
                                Body=png_bytes,
                                ContentType="image/png",
                            )
                            presigned_url = s3_client.generate_presigned_url(
                                "get_object",
                                Params={"Bucket": config.s3_bucket_name, "Key": s3_key},
                                ExpiresIn=presign_hours * 3600,
                            )
                            expires_at = datetime.now(timezone.utc) + timedelta(hours=presign_hours)
                            whatsapp_rows.append({
                                "id": uuid.uuid4(),
                                "tenant_id": tenant_id,
                                "customer_id": cinfo["id"],
                                "algorithm": algo,
                                "customer_external_id": cinfo["external_id"],
                                "customer_add_id": cinfo["add_id"],
                                "customer_name": cinfo["name"],
                                "image_url": presigned_url,
                                "image_s3_key": s3_key,
                                "products_count": len(wa_products),
                                "presigned_expires_at": expires_at,
                                "computed_at": datetime.now(timezone.utc),
                            })
                            counters["images"] += 1
                        except Exception:
                            logger.warning("WhatsApp PNG falhou para customer %s algo %s", cid, algo, exc_info=True)

                # --- PUSH (só imagem, sem texto) ---
                if "push" in template_map and s3_client and config.s3_bucket_name:
                    push_products = products[:max_push]
                    if push_products:
                        try:
                            push_png = _generate_push_png(
                                push_products,
                                store_info=store_info,
                                offers_valid_until=offers_valid_until,
                            )
                            img_key = f"{tenant_id}/content/{today_str}/{cid}_{algo}_push.png"
                            s3_client.put_object(
                                Bucket=config.s3_bucket_name,
                                Key=img_key,
                                Body=push_png,
                                ContentType="image/png",
                            )
                            img_url = s3_client.generate_presigned_url(
                                "get_object",
                                Params={"Bucket": config.s3_bucket_name, "Key": img_key},
                                ExpiresIn=presign_hours * 3600,
                            )
                            img_expires = datetime.now(timezone.utc) + timedelta(hours=presign_hours)
                            push_rows.append({
                                "id": uuid.uuid4(),
                                "tenant_id": tenant_id,
                                "customer_id": cinfo["id"],
                                "algorithm": algo,
                                "customer_external_id": cinfo["external_id"],
                                "customer_add_id": cinfo["add_id"],
                                "customer_name": cinfo["name"],
                                "title": "",
                                "body": "",
                                "image_url": img_url,
                                "image_s3_key": img_key,
                                "presigned_expires_at": img_expires,
                                "computed_at": datetime.now(timezone.utc),
                            })
                            counters["push"] += 1
                        except Exception:
                            logger.warning("Push PNG falhou para customer %s algo %s", cid, algo, exc_info=True)

            # Bulk upsert por chunk
            db_write = SessionLocal()
            try:
                if email_rows:
                    _bulk_upsert(db_write, "content_email", email_rows,
                                 conflict_cols=["tenant_id", "customer_id", "algorithm"],
                                 update_cols=["customer_external_id", "customer_add_id", "customer_name",
                                              "html_body", "products_count", "computed_at"])
                if whatsapp_rows:
                    _bulk_upsert(db_write, "content_whatsapp", whatsapp_rows,
                                 conflict_cols=["tenant_id", "customer_id", "algorithm"],
                                 update_cols=["customer_external_id", "customer_add_id", "customer_name",
                                              "image_url", "image_s3_key", "products_count",
                                              "presigned_expires_at", "computed_at"])
                if push_rows:
                    _bulk_upsert(db_write, "content_push", push_rows,
                                 conflict_cols=["tenant_id", "customer_id", "algorithm"],
                                 update_cols=["customer_external_id", "customer_add_id", "customer_name",
                                              "title", "body", "image_url", "image_s3_key",
                                              "presigned_expires_at", "computed_at"])
                db_write.commit()
            except Exception:
                db_write.rollback()
                raise
            finally:
                db_write.close()

        return counters

    @staticmethod
    def test_s3(config: TenantConfig) -> dict:
        """Testa conexão S3 com as credenciais do tenant."""
        if not config.s3_bucket_name or not config.s3_access_key or not config.s3_secret_key:
            return {"success": False, "error": "Credenciais S3 incompletas"}
        try:
            client = _get_s3_client(config)
            client.head_bucket(Bucket=config.s3_bucket_name)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)[:300]}

    @staticmethod
    def regenerate_presigned_url(config: TenantConfig, s3_key: str) -> tuple[str, datetime]:
        """Gera nova presigned URL a partir da key permanente."""
        client = _get_s3_client(config)
        hours = config.s3_presigned_expiration_hours or 168
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": config.s3_bucket_name, "Key": s3_key},
            ExpiresIn=hours * 3600,
        )
        expires = datetime.now(timezone.utc) + timedelta(hours=hours)
        return url, expires


# ------------------------------------------------------------------ #
# Helpers internos
# ------------------------------------------------------------------ #

def _get_s3_client(config: TenantConfig):
    return boto3.client(
        "s3",
        aws_access_key_id=config.s3_access_key,
        aws_secret_access_key=config.s3_secret_key,
        region_name=config.s3_region or "us-east-1",
        config=BotoConfig(signature_version="s3v4"),
    )


def _cleanup_s3_images(s3_client, bucket: str, tenant_id: str):
    """Remove todas as imagens antigas do tenant antes de gerar novas."""
    prefix = f"{tenant_id}/content/"
    deleted = 0
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            objects = page.get("Contents", [])
            if not objects:
                continue
            keys = [{"Key": obj["Key"]} for obj in objects]
            s3_client.delete_objects(Bucket=bucket, Delete={"Objects": keys})
            deleted += len(keys)
        if deleted:
            logger.info("S3 cleanup: removidos %d objetos em %s", deleted, prefix)
    except Exception as e:
        logger.warning("S3 cleanup falhou (continuando): %s", e)


def _prepare_email_products(products: list[dict]) -> list[dict]:
    """
    Prepara produtos para email:
    - Adiciona campo 'layout' (full / grid) baseado no offer_type
    - Ordena: complexas (full) primeiro, simples (grid) depois
    """
    for p in products:
        ot = p.get("offer_type") or ""
        p["layout"] = "full" if ot in COMPLEX_OFFER_TYPES else "grid"

    # Complexas primeiro, simples depois; dentro de cada grupo mantém rank original
    full = [p for p in products if p["layout"] == "full"]
    grid = [p for p in products if p["layout"] == "grid"]
    return full + grid


def _select_template(
    channel_templates: dict[str, ContentTemplate],
    products: list[dict],
) -> Optional[ContentTemplate]:
    """Seleciona template pelo offer_type dominante ou fallback genérico."""
    if not channel_templates:
        return None

    # Conta offer_types dos produtos
    offer_types = [p["offer_type"] for p in products if p.get("offer_type")]
    if offer_types:
        most_common = Counter(offer_types).most_common(1)[0][0]
        # Se todos são do mesmo tipo OU o mais comum tem maioria
        if most_common in channel_templates:
            return channel_templates[most_common]

    # Fallback genérico
    return channel_templates.get("__GENERIC__")



def _render_email_modular(
    jinja_env: Environment,
    compiled_cards: dict[str, object],
    compiled_footer,
    compiled_master,
    products: list[dict],
    customer_name: str,
    store_info: dict,
    offers_valid_until: Optional[str],
) -> str:
    """
    Renderiza email modular: master layout + card templates por produto + footer.

    compiled_cards: mapa offer_type → pre-compiled Jinja2 Template (excluindo __FOOTER__)
    compiled_footer: pre-compiled Jinja2 Template for footer
    compiled_master: pre-compiled Jinja2 Template for master layout
    """
    email_products = _prepare_email_products(products)

    full_products = [p for p in email_products if p["layout"] == "full"]
    grid_products = [p for p in email_products if p["layout"] == "grid"]

    # Renderiza cada card individual using pre-compiled templates
    def _render_card(product: dict) -> str:
        ot = product.get("offer_type") or ""
        tpl = compiled_cards.get(ot) or compiled_cards.get("__GENERIC__")
        if not tpl:
            return ""
        return tpl.render(p=product)

    # Full-width cards: cada um envolto em <tr><td>
    complex_parts = []
    for p in full_products:
        card_html = _render_card(p)
        if card_html:
            complex_parts.append(
                f'<tr><td style="padding:8px 32px;">{card_html}</td></tr>'
            )
    complex_cards_html = "\n".join(complex_parts)

    # Grid cards: montar em <tr> de 2 colunas
    grid_parts = []
    for idx, p in enumerate(grid_products):
        card_html = _render_card(p)
        if idx % 2 == 0:
            grid_parts.append("<tr>")
        grid_parts.append(
            f'<td width="50%" style="padding:8px; vertical-align:top;">{card_html}</td>'
        )
        if idx % 2 == 1 or idx == len(grid_products) - 1:
            # Pad célula vazia se ímpar no final
            if idx % 2 == 0:
                grid_parts.append('<td width="50%" style="padding:8px;"></td>')
            grid_parts.append("</tr>")
    grid_cards_html = "\n".join(grid_parts)

    # Footer (pre-compiled)
    footer_html = compiled_footer.render(
        store_name=store_info.get("name", ""),
        store_address=store_info.get("address", ""),
        offers_valid_until=offers_valid_until or "",
    )

    # Renderiza master layout com slots preenchidos (pre-compiled)
    return compiled_master.render(
        customer_name=customer_name,
        complex_cards_html=Markup(complex_cards_html),
        grid_cards_html=Markup(grid_cards_html),
        footer_html=Markup(footer_html),
    )


def _generate_whatsapp_png(
    template: ContentTemplate,
    customer_name: str,
    products: list[dict],
    jinja_env: Environment,
    store_info: Optional[dict] = None,
    offers_valid_until: Optional[str] = None,
) -> bytes:
    """Gera PNG para WhatsApp usando Pillow."""
    # Parse config do template
    try:
        tpl_config = json.loads(template.body)
    except (json.JSONDecodeError, TypeError):
        tpl_config = {}

    bg_color = tpl_config.get("bg_color", "#FFFFFF")
    accent_color = tpl_config.get("accent_color", "#7C3AED")
    footer_text = tpl_config.get("footer_text", "Aproveite!")

    # Renderiza textos Jinja2
    footer_rendered = jinja_env.from_string(footer_text).render(customer_name=customer_name)

    # Disclaimer lines
    store = store_info or {}
    disclaimer_lines = []
    if offers_valid_until:
        disclaimer_lines.append(f"Ofertas válidas até {offers_valid_until}")
    store_name = store.get("name", "")
    store_address = store.get("address", "")
    if store_name:
        line = store_name
        if store_address:
            line += f" — {store_address}"
        disclaimer_lines.append(line)
    disclaimer_lines.append("Ofertas sujeitas a disponibilidade.")

    # Calcula dimensões (footer maior para caber disclaimer)
    disclaimer_height = len(disclaimer_lines) * 16 + 10
    footer_total = FOOTER_HEIGHT + disclaimer_height
    n_products = len(products)
    canvas_height = PADDING + (PRODUCT_HEIGHT * n_products) + footer_total + PADDING

    img = Image.new("RGB", (PNG_WIDTH, canvas_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Fontes
    try:
        font_product = ImageFont.truetype(FONT_PATH, 16)
        font_price = ImageFont.truetype(FONT_PATH, 18)
        font_badge = ImageFont.truetype(FONT_PATH, 12)
        font_footer = ImageFont.truetype(FONT_PATH, 14)
        font_disclaimer = ImageFont.truetype(FONT_PATH, 11)
    except Exception:
        font_product = ImageFont.load_default()
        font_price = font_product
        font_badge = font_product
        font_footer = font_product
        font_disclaimer = font_product

    y = PADDING
    for p in products:
        # Thumbnail
        thumb = _download_thumbnail(p.get("image_url"))
        if thumb:
            img.paste(thumb, (PADDING, y + 10))

        text_x = PADDING + THUMBNAIL_SIZE[0] + 15

        # Nome do produto (truncado)
        name = (p.get("name") or "Produto")[:40]
        draw.text((text_x, y + 10), name, fill="#1F2937", font=font_product)

        # Categoria
        cat = p.get("category") or ""
        if isinstance(cat, (list, dict)):
            cat = str(cat)
        if cat:
            draw.text((text_x, y + 32), cat[:35], fill="#6B7280", font=font_badge)

        # Preço
        base = p.get("base_price")
        offer = p.get("offer_price")
        if offer and p.get("has_offer"):
            base_text = f"R${base:.2f}" if base else ""
            draw.text((text_x, y + 55), base_text, fill="#9CA3AF", font=font_product)
            price_text = f"R${offer:.2f}"
            draw.text((text_x, y + 78), price_text, fill=accent_color, font=font_price)

            badge_text = p.get("offer_name") or p.get("offer_type") or "OFERTA"
            badge_text = badge_text[:25]
            draw.rounded_rectangle(
                (text_x, y + 105, text_x + len(badge_text) * 7 + 16, y + 122),
                radius=4, fill=accent_color,
            )
            draw.text((text_x + 8, y + 107), badge_text, fill="#FFFFFF", font=font_badge)
        elif base:
            price_text = f"R${base:.2f}"
            draw.text((text_x, y + 55), price_text, fill="#1F2937", font=font_price)

        # Separador
        y += PRODUCT_HEIGHT
        if y < canvas_height - footer_total:
            draw.line([(PADDING, y - 5), (PNG_WIDTH - PADDING, y - 5)], fill="#E5E7EB", width=1)

    # Footer text (template)
    footer_y = canvas_height - footer_total + 10
    draw.text((PADDING, footer_y), footer_rendered, fill="#6B7280", font=font_footer)

    # Disclaimer / store info
    disclaimer_y = footer_y + 28
    draw.line([(PADDING, disclaimer_y - 6), (PNG_WIDTH - PADDING, disclaimer_y - 6)], fill="#E5E7EB", width=1)
    for line in disclaimer_lines:
        draw.text((PADDING, disclaimer_y), line, fill="#9CA3AF", font=font_disclaimer)
        disclaimer_y += 16

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


PUSH_IMG_WIDTH = 1024
PUSH_IMG_HEIGHT = 512
PUSH_THUMB_SIZE = (200, 200)


def _generate_push_png(
    products: list[dict],
    accent_color: str = "#7C3AED",
    store_info: Optional[dict] = None,
    offers_valid_until: Optional[str] = None,
) -> bytes:
    """Gera PNG compacto para push notification. Sem saudação, layout limpo."""
    bg_color = "#FFFFFF"

    img = Image.new("RGB", (PUSH_IMG_WIDTH, PUSH_IMG_HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font_name = ImageFont.truetype(FONT_PATH, 22)
        font_price = ImageFont.truetype(FONT_PATH, 26)
        font_badge = ImageFont.truetype(FONT_PATH, 14)
        font_cat = ImageFont.truetype(FONT_PATH, 14)
        font_disclaimer = ImageFont.truetype(FONT_PATH, 11)
    except Exception:
        font_name = ImageFont.load_default()
        font_price = font_name
        font_badge = font_name
        font_cat = font_name
        font_disclaimer = font_name

    n = len(products)
    if n == 0:
        return b""

    # Layout: produtos lado a lado com thumbnail grande
    card_width = (PUSH_IMG_WIDTH - 40) // n
    x = 20
    for p in products:
        thumb = _download_thumbnail(p.get("image_url"))
        if thumb:
            # Redimensionar para PUSH_THUMB_SIZE
            thumb = thumb.resize(PUSH_THUMB_SIZE)
            thumb_x = x + (card_width - PUSH_THUMB_SIZE[0]) // 2
            img.paste(thumb, (thumb_x, 20))

        text_x = x + 10
        text_center = x + card_width // 2
        y = 20 + PUSH_THUMB_SIZE[1] + 10

        # Nome (truncado, centralizado)
        name = (p.get("name") or "Produto")[:30]
        # Centralizar: calcular largura do texto
        try:
            name_bbox = draw.textbbox((0, 0), name, font=font_name)
            name_w = name_bbox[2] - name_bbox[0]
        except Exception:
            name_w = len(name) * 10
        draw.text((text_center - name_w // 2, y), name, fill="#1F2937", font=font_name)
        y += 28

        # Categoria
        cat = p.get("category") or ""
        if isinstance(cat, (list, dict)):
            cat = str(cat)
        if cat:
            cat = cat[:35]
            try:
                cat_bbox = draw.textbbox((0, 0), cat, font=font_cat)
                cat_w = cat_bbox[2] - cat_bbox[0]
            except Exception:
                cat_w = len(cat) * 7
            draw.text((text_center - cat_w // 2, y), cat, fill="#9CA3AF", font=font_cat)
        y += 20

        # Preço
        base = p.get("base_price")
        offer = p.get("offer_price")
        if offer and p.get("has_offer"):
            if base:
                base_text = f"R${base:.2f}"
                try:
                    bt_bbox = draw.textbbox((0, 0), base_text, font=font_cat)
                    bt_w = bt_bbox[2] - bt_bbox[0]
                except Exception:
                    bt_w = len(base_text) * 7
                draw.text((text_center - bt_w // 2, y), base_text, fill="#9CA3AF", font=font_cat)
                y += 18
            price_text = f"R${offer:.2f}"
            try:
                pt_bbox = draw.textbbox((0, 0), price_text, font=font_price)
                pt_w = pt_bbox[2] - pt_bbox[0]
            except Exception:
                pt_w = len(price_text) * 12
            draw.text((text_center - pt_w // 2, y), price_text, fill=accent_color, font=font_price)
            y += 32

            badge_text = p.get("offer_name") or p.get("offer_type") or "OFERTA"
            badge_text = badge_text[:25]
            try:
                badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
                badge_w = badge_bbox[2] - badge_bbox[0] + 16
            except Exception:
                badge_w = len(badge_text) * 8 + 16
            bx = text_center - badge_w // 2
            draw.rounded_rectangle(
                (bx, y, bx + badge_w, y + 20),
                radius=4, fill=accent_color,
            )
            draw.text((bx + 8, y + 3), badge_text, fill="#FFFFFF", font=font_badge)
        elif base:
            price_text = f"R${base:.2f}"
            try:
                pt_bbox = draw.textbbox((0, 0), price_text, font=font_price)
                pt_w = pt_bbox[2] - pt_bbox[0]
            except Exception:
                pt_w = len(price_text) * 12
            draw.text((text_center - pt_w // 2, y), price_text, fill="#1F2937", font=font_price)

        x += card_width

    # Disclaimer na parte inferior
    store = store_info or {}
    disc_parts = []
    if offers_valid_until:
        disc_parts.append(f"Válidas até {offers_valid_until}")
    store_name = store.get("name", "")
    if store_name:
        disc_parts.append(store_name)
    disc_parts.append("Sujeitas a disponibilidade")
    disc_text = " · ".join(disc_parts)
    try:
        disc_bbox = draw.textbbox((0, 0), disc_text, font=font_disclaimer)
        disc_w = disc_bbox[2] - disc_bbox[0]
    except Exception:
        disc_w = len(disc_text) * 6
    draw.text(
        ((PUSH_IMG_WIDTH - disc_w) // 2, PUSH_IMG_HEIGHT - 22),
        disc_text, fill="#9CA3AF", font=font_disclaimer,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _download_thumbnail(url: Optional[str]) -> Optional[Image.Image]:
    """Baixa imagem e redimensiona. Retorna None em caso de falha."""
    if not url:
        return _placeholder_thumb()
    try:
        resp = requests.get(url, timeout=5, stream=True)
        resp.raise_for_status()
        thumb = Image.open(io.BytesIO(resp.content))
        thumb = thumb.convert("RGB")
        thumb.thumbnail(THUMBNAIL_SIZE)
        # Pad to exact size
        padded = Image.new("RGB", THUMBNAIL_SIZE, "#F3F4F6")
        offset = ((THUMBNAIL_SIZE[0] - thumb.width) // 2, (THUMBNAIL_SIZE[1] - thumb.height) // 2)
        padded.paste(thumb, offset)
        return padded
    except Exception:
        return _placeholder_thumb()


def _placeholder_thumb() -> Image.Image:
    """Retângulo cinza placeholder."""
    img = Image.new("RGB", THUMBNAIL_SIZE, "#E5E7EB")
    draw = ImageDraw.Draw(img)
    draw.text((30, 50), "Sem\nimagem", fill="#9CA3AF")
    return img


def _bulk_upsert(
    db: Session,
    table: str,
    rows: list[dict],
    conflict_cols: list[str],
    update_cols: list[str],
):
    """INSERT ... ON CONFLICT DO UPDATE para PostgreSQL (executemany)."""
    if not rows:
        return

    cols = list(rows[0].keys())
    col_list = ", ".join(cols)
    val_placeholders = ", ".join(f":{c}" for c in cols)
    conflict = ", ".join(conflict_cols)
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

    sql = text(f"""
        INSERT INTO {table} ({col_list})
        VALUES ({val_placeholders})
        ON CONFLICT ({conflict}) DO UPDATE SET {updates}
    """)
    # executemany — single round-trip for all rows
    db.execute(sql, rows)
