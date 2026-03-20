# backend/app/services/lifecycle_service.py
"""
Serviço de ciclo de vida do cliente.

Responsabilidades:
1. update_summary_for_customers() — atualiza customer_order_summary após batch de pedidos (Tx2)
2. compute_segments_for_tenant() — calcula indicadores + segmento para todos os clientes de um tenant
"""
from datetime import datetime, timedelta, timezone
from collections import Counter
from statistics import mean, stdev
from typing import List, Optional, Dict, Any
import logging
import uuid

import pandas as pd
from lifetimes import BetaGeoFitter

from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import (
    Customer, Order, OrderItem, Channel,
    CustomerOrderSummary, CustomerSegment, TenantConfig,
)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# 1. UPDATE SUMMARY (chamado no POST /orders/batch — Tx2 separada)
# ------------------------------------------------------------------ #

def update_summary_for_customers(
    db: Session,
    tenant_id: str,
    customer_uuids: List[uuid.UUID],
):
    """
    Recalcula customer_order_summary para os clientes afetados.
    Chamado em transação separada (Tx2) após o commit dos pedidos (Tx1).
    Se falhar, log warning — o job diário corrige.
    """
    if not customer_uuids:
        return

    now = datetime.now(timezone.utc)
    d90 = now - timedelta(days=90)
    d180 = now - timedelta(days=180)

    # Pré-carrega mapa de canais para channel_counts
    channels = db.query(Channel).filter(Channel.tenant_id == tenant_id).all()
    channel_type_map: Dict[uuid.UUID, str] = {c.id: (c.type or "unknown") for c in channels}

    for cid in customer_uuids:
        try:
            _rebuild_summary_for_customer(db, tenant_id, cid, now, d90, d180, channel_type_map)
        except Exception:
            logger.exception("Falha ao atualizar summary do cliente %s", cid)
            db.rollback()
            continue

    try:
        db.commit()
    except Exception:
        logger.exception("Falha ao commitar Tx2 da summary (tenant=%s)", tenant_id)
        db.rollback()


def _rebuild_summary_for_customer(
    db: Session,
    tenant_id: str,
    customer_uuid: uuid.UUID,
    now: datetime,
    d90: datetime,
    d180: datetime,
    channel_type_map: Dict[uuid.UUID, str],
):
    """Recalcula summary completa de um cliente a partir de orders+items."""
    orders = (
        db.query(Order)
        .filter(Order.tenant_id == tenant_id, Order.customer_id == customer_uuid)
        .order_by(Order.ordered_at.desc())
        .all()
    )

    if not orders:
        return

    order_ids = [o.id for o in orders]
    items = db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all()

    # --- Agregados básicos ---
    total_orders = len(orders)
    total_value = sum(o.net_value or 0 for o in orders)
    first_order_at = min(o.ordered_at for o in orders)
    last_order_at = max(o.ordered_at for o in orders)

    # --- Janelas 90d ---
    orders_90d = sum(1 for o in orders if o.ordered_at >= d90)
    value_90d = sum(o.net_value or 0 for o in orders if o.ordered_at >= d90)
    orders_prev_90d = sum(1 for o in orders if d180 <= o.ordered_at < d90)
    value_prev_90d = sum(o.net_value or 0 for o in orders if d180 <= o.ordered_at < d90)

    # --- Recent order dates (últimas 30) ---
    sorted_dates = sorted([o.ordered_at for o in orders], reverse=True)[:30]
    recent_order_dates = [dt.isoformat() for dt in sorted_dates]

    # --- Itens ---
    total_items = sum(i.quantity for i in items)
    sku_counts: Counter = Counter()
    category_counts: Counter = Counter()
    promo_items = 0

    for item in items:
        sku_counts[item.product_external_id] += item.quantity
        if item.is_promo or (item.discount_amount and item.discount_amount > 0):
            promo_items += item.quantity

    distinct_skus = len(sku_counts)
    repeat_skus = sum(1 for c in sku_counts.values() if c > 1)

    # --- Returned orders ---
    returned_orders = sum(1 for o in orders if o.status == "returned")

    # --- Top SKUs (top 10 por frequência) ---
    top_skus = dict(sku_counts.most_common(10))

    # --- Top Categories (via Product lookup seria ideal, mas para simplificar usamos o que temos) ---
    # Nota: top_categories e channel_counts exigem joins extras
    # Usamos channel do Order para channel_counts
    channel_counts: Counter = Counter()
    for o in orders:
        if o.channel_id:
            ch_type = channel_type_map.get(o.channel_id, "unknown")
            channel_counts[ch_type] += 1

    # top_categories: precisa do product.category — fazemos com o que temos nos items
    # Busca categorias dos produtos em batch
    product_ext_ids = list(sku_counts.keys())
    if product_ext_ids:
        from app.db.models import Product
        products = (
            db.query(Product.external_id, Product.category)
            .filter(Product.tenant_id == tenant_id, Product.external_id.in_(product_ext_ids))
            .all()
        )
        prod_cat_map = {}
        for ext_id, cat in products:
            if cat:
                # category é JSON — pode ser {"l1": "Alimentos", "l2": "Biscoitos"} ou string
                if isinstance(cat, dict):
                    cat_name = cat.get("l1") or cat.get("name") or next(iter(cat.values()), None)
                elif isinstance(cat, str):
                    cat_name = cat
                else:
                    cat_name = None
                if cat_name:
                    prod_cat_map[ext_id] = cat_name

        for ext_id, qty in sku_counts.items():
            cat_name = prod_cat_map.get(ext_id)
            if cat_name:
                category_counts[cat_name] += qty

    top_categories = dict(category_counts.most_common(10))

    # --- Upsert na summary ---
    existing = (
        db.query(CustomerOrderSummary)
        .filter(
            CustomerOrderSummary.tenant_id == tenant_id,
            CustomerOrderSummary.customer_id == customer_uuid,
        )
        .first()
    )

    values = dict(
        total_orders=total_orders,
        total_value=round(total_value, 2),
        first_order_at=first_order_at,
        last_order_at=last_order_at,
        orders_90d=orders_90d,
        value_90d=round(value_90d, 2),
        orders_prev_90d=orders_prev_90d,
        value_prev_90d=round(value_prev_90d, 2),
        recent_order_dates=recent_order_dates,
        total_items=total_items,
        distinct_skus=distinct_skus,
        repeat_skus=repeat_skus,
        promo_items=promo_items,
        returned_orders=returned_orders,
        top_skus=top_skus,
        top_categories=top_categories,
        channel_counts=dict(channel_counts),
    )

    if existing:
        for k, v in values.items():
            setattr(existing, k, v)
    else:
        db.add(CustomerOrderSummary(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_uuid,
            **values,
        ))

    db.flush()


# ------------------------------------------------------------------ #
# 2. COMPUTE SEGMENTS (chamado pelo worker)
# ------------------------------------------------------------------ #

_THRESHOLD_DEFAULTS = dict(
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


def _load_thresholds(db: Session, tenant_id: str) -> Dict[str, Any]:
    """Carrega thresholds de segmentação do TenantConfig; usa defaults se não existir."""
    config = db.query(TenantConfig).filter(TenantConfig.tenant_id == tenant_id).first()
    result = {}
    for field, default in _THRESHOLD_DEFAULTS.items():
        val = getattr(config, field, None) if config else None
        result[field] = val if val is not None else default
    return result


def compute_segments_for_tenant(
    db_read: Session,
    db_write: Session,
    tenant_id: str,
) -> int:
    """
    Calcula indicadores + segmento para todos os clientes de um tenant.

    - db_read: sessão da replica (leitura)
    - db_write: sessão do primary (escrita)

    Retorna o número de clientes processados.
    """
    now = datetime.now(timezone.utc)
    d90 = now - timedelta(days=90)
    d180 = now - timedelta(days=180)

    # Carrega thresholds configuráveis (usa db_read pois TenantConfig é leitura)
    thresholds = _load_thresholds(db_read, tenant_id)

    # 1. Lê todos os summaries do tenant (replica)
    summaries = (
        db_read.query(CustomerOrderSummary)
        .filter(CustomerOrderSummary.tenant_id == tenant_id)
        .all()
    )

    logger.info("Tenant %s: %d summaries encontrados", tenant_id, len(summaries))
    if not summaries:
        return 0

    # Lê todos os clientes para days_as_customer
    customers = (
        db_read.query(Customer.id, Customer.created_at)
        .filter(Customer.tenant_id == tenant_id)
        .all()
    )
    customer_created = {c.id: c.created_at for c in customers}

    # Calcula p75 do avg_ticket para o tenant (para LoyalStar)
    avg_tickets = []
    for s in summaries:
        if s.total_orders and s.total_orders > 0:
            avg_tickets.append(s.total_value / s.total_orders)

    p75_ticket = _percentile(avg_tickets, 75) if avg_tickets else 0

    # --- BG/NBD: fit 1x por tenant ---
    logger.info("Tenant %s: iniciando BG/NBD", tenant_id)
    bgnbd_lookup = _fit_bgnbd(summaries, now)
    logger.info("Tenant %s: BG/NBD concluído (%d clientes com p_alive)", tenant_id, len(bgnbd_lookup))

    # 2. Para cada cliente, calcula indicadores e classifica
    processed = 0
    chunk_size = 100
    segments_buffer: List[Dict[str, Any]] = []

    for s in summaries:
        bgnbd = bgnbd_lookup.get(s.customer_id, {})
        indicators = _compute_indicators(s, now, d90, d180, customer_created, p75_ticket, bgnbd)
        segment = _classify_segment(indicators, thresholds)

        segments_buffer.append(dict(
            tenant_id=tenant_id,
            customer_id=s.customer_id,
            **indicators,
            lifecycle_segment_next=segment,
            computed_at=now,
        ))
        processed += 1

        if len(segments_buffer) >= chunk_size:
            _upsert_segments_chunk(db_write, segments_buffer)
            segments_buffer.clear()

    if segments_buffer:
        _upsert_segments_chunk(db_write, segments_buffer)

    # 3. Swap atômico: lifecycle_segment = lifecycle_segment_next
    db_write.execute(
        text("""
            UPDATE customer_segments
            SET lifecycle_segment = lifecycle_segment_next,
                lifecycle_segment_next = NULL
            WHERE tenant_id = :tid
              AND lifecycle_segment_next IS NOT NULL
        """),
        {"tid": tenant_id},
    )
    db_write.commit()

    logger.info("Tenant %s: %d clientes segmentados", tenant_id, processed)

    # 4. Calcula sugestões de thresholds baseadas na distribuição atual
    try:
        all_segs = db_write.query(CustomerSegment).filter(CustomerSegment.tenant_id == tenant_id).all()
        _compute_threshold_suggestions(db_write, tenant_id, all_segs)
        db_write.commit()
    except Exception:
        logger.exception("Tenant %s: falha ao calcular sugestões de thresholds", tenant_id)
        db_write.rollback()

    return processed


def _fit_bgnbd(
    summaries: List[CustomerOrderSummary],
    now: datetime,
) -> Dict[Any, Dict[str, float]]:
    """
    Fita o modelo BG/NBD nos dados do tenant e retorna p_alive + expected_transactions por cliente.

    Parâmetros do BG/NBD por cliente:
    - frequency: número de compras repetidas (total_orders - 1)
    - recency: tempo entre primeira e última compra (em dias)
    - T: tempo desde a primeira compra até agora (em dias)

    Retorna dict: { customer_id: { "p_alive": float, "expected_transactions": float } }
    Retorna {} se dados insuficientes (< 10 clientes com frequency > 0).
    """
    rows = []
    for s in summaries:
        if not s.total_orders or s.total_orders < 1 or not s.first_order_at:
            continue

        frequency = max(s.total_orders - 1, 0)
        T = (now - s.first_order_at).days
        if T <= 0:
            T = 1

        if s.last_order_at and s.first_order_at:
            recency = (s.last_order_at - s.first_order_at).days
        else:
            recency = 0

        rows.append({
            "customer_id": s.customer_id,
            "frequency": frequency,
            "recency": recency,
            "T": T,
        })

    if not rows:
        return {}

    df = pd.DataFrame(rows)

    # Precisa de clientes com frequency > 0 para o modelo convergir
    repeat_buyers = df[df["frequency"] > 0]
    if len(repeat_buyers) < 10:
        logger.info("BG/NBD: poucos repeat buyers (%d), usando proxy", len(repeat_buyers))
        return {}

    try:
        logger.info("BG/NBD: iniciando fit com %d clientes (%d repeat buyers)", len(df), len(repeat_buyers))
        bgf = BetaGeoFitter(penalizer_coef=0.5)
        bgf.fit(df["frequency"], df["recency"], df["T"], max_iter=200, tol=1e-5)

        result = {}
        for _, row in df.iterrows():
            cid = row["customer_id"]
            p_alive_raw = bgf.conditional_probability_alive(
                row["frequency"], row["recency"], row["T"]
            )
            exp_txn_raw = bgf.conditional_expected_number_of_purchases_up_to_time(
                90, row["frequency"], row["recency"], row["T"]
            )

            # lifetimes retorna numpy arrays/scalars — converter para float nativo
            pa = p_alive_raw.item() if hasattr(p_alive_raw, 'item') else float(p_alive_raw)
            et = exp_txn_raw.item() if hasattr(exp_txn_raw, 'item') else float(exp_txn_raw)

            result[cid] = {
                "p_alive": round(pa, 4),
                "expected_transactions": round(et, 4),
            }

        logger.info("BG/NBD: fitado com sucesso (%d clientes, %d repeat buyers)",
                     len(df), len(repeat_buyers))
        return result

    except Exception:
        logger.exception("BG/NBD: falha no fit — usando proxy")
        return {}


def _compute_indicators(
    s: CustomerOrderSummary,
    now: datetime,
    d90: datetime,
    d180: datetime,
    customer_created: dict,
    p75_ticket: float,
    bgnbd: Dict[str, float] = None,
) -> Dict[str, Any]:
    """Calcula os 14 indicadores a partir do summary."""

    # --- RFM ---
    recency_days = (now - s.last_order_at).days if s.last_order_at else None
    number_of_invoices = s.total_orders or 0
    monetary_total = s.total_value or 0
    avg_ticket = (monetary_total / number_of_invoices) if number_of_invoices > 0 else 0

    # --- Tendência ---
    avg_ticket_90d = (s.value_90d / s.orders_90d) if s.orders_90d and s.orders_90d > 0 else 0
    avg_ticket_prev = (s.value_prev_90d / s.orders_prev_90d) if s.orders_prev_90d and s.orders_prev_90d > 0 else 0
    ticket_trend = (avg_ticket_90d / avg_ticket_prev) if avg_ticket_prev > 0 else None

    orders_90d = s.orders_90d or 0
    orders_prev_90d = s.orders_prev_90d or 0
    purchase_velocity_trend = (orders_90d / orders_prev_90d) if orders_prev_90d > 0 else None

    # --- Cadência (a partir de recent_order_dates) ---
    avg_days_between = None
    purchase_regularity = None  # CoV

    dates = _parse_recent_dates(s.recent_order_dates)
    if len(dates) >= 2:
        # Recalcula janelas 90d a partir das datas reais (mais preciso que o summary)
        sorted_dates = sorted(dates, reverse=True)
        intervals = [
            (sorted_dates[i] - sorted_dates[i + 1]).days
            for i in range(len(sorted_dates) - 1)
        ]
        if intervals:
            avg_days_between = mean(intervals)
            if len(intervals) >= 2 and avg_days_between > 0:
                purchase_regularity = stdev(intervals) / avg_days_between
            else:
                purchase_regularity = 0.0

    # --- Variedade ---
    distinct_articles = s.distinct_skus or 0
    category_diversity = len(s.top_categories) if s.top_categories else 0

    # --- Comportamento ---
    promo_ratio = (s.promo_items / s.total_items) if s.total_items and s.total_items > 0 else 0
    return_rate = (s.returned_orders / s.total_orders) if s.total_orders and s.total_orders > 0 else 0
    repeat_product_ratio = (s.repeat_skus / s.distinct_skus) if s.distinct_skus and s.distinct_skus > 0 else 0

    # --- Preferências ---
    top_5_products = list((s.top_skus or {}).keys())[:5]
    top_5_categories = list((s.top_categories or {}).keys())[:5]
    preferred_channel = max(s.channel_counts, key=s.channel_counts.get) if s.channel_counts else None

    # --- Tempo como cliente ---
    created = customer_created.get(s.customer_id)
    days_as_customer = (now - created).days if created else None

    # --- BG/NBD ---
    if bgnbd:
        p_alive_val = bgnbd.get("p_alive")
        expected_transactions_val = bgnbd.get("expected_transactions")
    else:
        # Proxy quando BG/NBD não disponível
        if avg_days_between and avg_days_between > 0:
            p_alive_val = round(1 / (1 + (recency_days or 0) / avg_days_between), 4)
        else:
            p_alive_val = 0.1 if number_of_invoices > 0 else None
        expected_transactions_val = None

    return dict(
        recency_days=recency_days,
        number_of_invoices=number_of_invoices,
        monetary_total=round(monetary_total, 2),
        avg_ticket=round(avg_ticket, 2),
        ticket_trend=round(ticket_trend, 4) if ticket_trend is not None else None,
        purchase_velocity_trend=round(purchase_velocity_trend, 4) if purchase_velocity_trend is not None else None,
        avg_days_between=round(avg_days_between, 2) if avg_days_between is not None else None,
        purchase_regularity=round(purchase_regularity, 4) if purchase_regularity is not None else None,
        distinct_articles=distinct_articles,
        category_diversity=category_diversity,
        promo_ratio=round(promo_ratio, 4),
        return_rate=round(return_rate, 4),
        repeat_product_ratio=round(repeat_product_ratio, 4),
        top_5_products=top_5_products,
        top_5_categories=top_5_categories,
        preferred_channel=preferred_channel,
        days_as_customer=days_as_customer,
        p_alive=p_alive_val,
        expected_transactions=expected_transactions_val,
        # Extras usados na classificação mas não salvos como coluna separada
        _p75_ticket=p75_ticket,
        _orders_90d=orders_90d,
        _orders_prev_90d=orders_prev_90d,
    )


def _classify_segment(ind: Dict[str, Any], thresholds: Dict[str, Any] = None) -> str:
    """
    Classifica o segmento de ciclo de vida — rule-based, primeiro match ganha.

    Ordem: Prospect → OneTime → NonEngaged → LoyalStar → LoyalRunner → StuckInMiddle

    Usa p_alive do BG/NBD (quando disponível) para decisões de churn.
    Os thresholds vêm do TenantConfig (configuráveis via UI).
    """
    t = thresholds or _THRESHOLD_DEFAULTS

    invoices = ind["number_of_invoices"]
    recency = ind["recency_days"]
    days_as = ind["days_as_customer"]
    regularity = ind["purchase_regularity"]
    velocity_trend = ind["purchase_velocity_trend"]
    avg_ticket = ind["avg_ticket"]
    ticket_trend = ind["ticket_trend"]
    category_div = ind["category_diversity"]
    p75 = ind["_p75_ticket"]
    orders_90d = ind["_orders_90d"]
    p_alive = ind.get("p_alive") or 0.1

    # 1. Prospect — sem pedidos
    if invoices == 0:
        return "Prospect"

    # 2. OneTime — 1 pedido, cliente antigo o suficiente, baixa probabilidade de voltar
    if (invoices == 1
            and days_as is not None
            and days_as > t["onetime_days_as_customer_min"]
            and p_alive < t["onetime_p_alive_max"]):
        return "OneTime"

    # 3. NonEngaged — p_alive baixo OU sumiu há muito tempo com queda forte
    if p_alive < t["nonengaged_p_alive_max"]:
        return "NonEngaged"
    if (recency is not None and recency > t["nonengaged_recency_min"]) and (
        velocity_trend is not None and velocity_trend < t["nonengaged_velocity_trend_max"]
    ):
        return "NonEngaged"
    if (recency is not None and recency > t["nonengaged_recency_min"]) and velocity_trend is None:
        return "NonEngaged"

    # 4. LoyalStar — regular, rápido, ticket alto, diversificado, vivo
    if (regularity is not None and regularity <= t["loyalstar_regularity_max"]
            and orders_90d >= 1
            and velocity_trend is not None and velocity_trend >= t["loyalstar_velocity_trend_min"]
            and avg_ticket >= p75
            and ticket_trend is not None and ticket_trend >= t["loyalstar_ticket_trend_min"]
            and category_div is not None and category_div >= t["loyalstar_category_diversity_min"]
            and p_alive >= t["loyalstar_p_alive_min"]):
        return "LoyalStar"

    # 5. LoyalRunner — regular com velocidade mantida e vivo
    if (regularity is not None and regularity <= t["loyalrunner_regularity_max"]
            and velocity_trend is not None and velocity_trend >= t["loyalrunner_velocity_trend_min"]
            and p_alive >= t["loyalrunner_p_alive_min"]):
        return "LoyalRunner"

    # 6. StuckInMiddle — fallback
    return "StuckInMiddle"


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _compute_threshold_suggestions(
    db: Session,
    tenant_id: str,
    segments: List[CustomerSegment],
) -> None:
    """
    Calcula sugestões de thresholds baseadas em percentis da distribuição real.
    Requer pelo menos 20 clientes com dados. Salva em TenantConfig.config_suggestions.

    Lógica de percentis:
    - nonengaged_p_alive_max    → p20 de p_alive   (20% mais baixos são "mortos")
    - loyalstar_p_alive_min     → p70 de p_alive   (30% mais vivos são candidatos a star)
    - loyalrunner_p_alive_min   → p50 de p_alive   (metade superior)
    - nonengaged_recency_min    → p75 de recency   (quartil de maior recência)
    - nonengaged_velocity_max   → p20 de velocity  (20% com maior queda de ritmo)
    - loyalstar_velocity_min    → p60 de velocity  (60% superiores em ritmo)
    - loyalrunner_velocity_min  → p50 de velocity  (mediana)
    - loyalstar_regularity_max  → p30 de regularity (30% mais regulares)
    - loyalrunner_regularity_max→ p50 de regularity (mediana)
    - loyalstar_ticket_trend_min→ p50 de ticket_trend
    - loyalstar_category_div_min→ p65 de category_diversity
    - onetime_days_min          → p50 de days_as_customer (clientes com 1 pedido)
    - onetime_p_alive_max       → p60 de p_alive (clientes com 1 pedido)
    """
    if len(segments) < 20:
        logger.info("Tenant %s: poucos clientes (%d) para calcular sugestões", tenant_id, len(segments))
        return

    def pct_float(values: List[float], p: float) -> Optional[float]:
        if not values:
            return None
        return round(_percentile(values, p), 2)

    def pct_int(values: List[float], p: float) -> Optional[int]:
        v = pct_float(values, p)
        return max(1, int(v)) if v is not None else None

    # --- Extrai valores não-nulos ---
    p_alive_vals = [s.p_alive for s in segments if s.p_alive is not None]
    recency_vals = [float(s.recency_days) for s in segments if s.recency_days is not None]
    regularity_vals = [s.purchase_regularity for s in segments if s.purchase_regularity is not None]
    velocity_vals = [s.purchase_velocity_trend for s in segments if s.purchase_velocity_trend is not None]
    ticket_trend_vals = [s.ticket_trend for s in segments if s.ticket_trend is not None]
    category_div_vals = [float(s.category_diversity) for s in segments if s.category_diversity is not None]

    # Clientes com exatamente 1 pedido (para OneTime)
    onetime_segs = [s for s in segments if s.number_of_invoices == 1]
    days_as_vals = [float(s.days_as_customer) for s in onetime_segs if s.days_as_customer is not None]
    onetime_p_alive_vals = [s.p_alive for s in onetime_segs if s.p_alive is not None]

    suggestions: Dict[str, Any] = {}

    if p_alive_vals:
        v = pct_float(p_alive_vals, 20)
        if v is not None:
            suggestions['nonengaged_p_alive_max'] = v
        v = pct_float(p_alive_vals, 70)
        if v is not None:
            suggestions['loyalstar_p_alive_min'] = v
        v = pct_float(p_alive_vals, 50)
        if v is not None:
            suggestions['loyalrunner_p_alive_min'] = v

    if recency_vals:
        v = pct_int(recency_vals, 75)
        if v is not None:
            suggestions['nonengaged_recency_min'] = v

    if velocity_vals:
        v = pct_float(velocity_vals, 20)
        if v is not None:
            suggestions['nonengaged_velocity_trend_max'] = v
        v = pct_float(velocity_vals, 60)
        if v is not None:
            suggestions['loyalstar_velocity_trend_min'] = v
        v = pct_float(velocity_vals, 50)
        if v is not None:
            suggestions['loyalrunner_velocity_trend_min'] = v

    if regularity_vals:
        v = pct_float(regularity_vals, 30)
        if v is not None:
            suggestions['loyalstar_regularity_max'] = v
        v = pct_float(regularity_vals, 50)
        if v is not None:
            suggestions['loyalrunner_regularity_max'] = v

    if ticket_trend_vals:
        v = pct_float(ticket_trend_vals, 50)
        if v is not None:
            suggestions['loyalstar_ticket_trend_min'] = v

    if category_div_vals:
        v = pct_int(category_div_vals, 65)
        if v is not None:
            suggestions['loyalstar_category_diversity_min'] = v

    if days_as_vals:
        v = pct_int(days_as_vals, 50)
        if v is not None:
            suggestions['onetime_days_as_customer_min'] = v

    if onetime_p_alive_vals:
        v = pct_float(onetime_p_alive_vals, 60)
        if v is not None:
            suggestions['onetime_p_alive_max'] = v

    if not suggestions:
        return

    config = db.query(TenantConfig).filter(TenantConfig.tenant_id == tenant_id).first()
    if not config:
        return

    config.config_suggestions = suggestions
    config.suggested_at = datetime.now(timezone.utc)
    db.flush()
    logger.info("Tenant %s: sugestões de thresholds calculadas (%d campos)", tenant_id, len(suggestions))


def _upsert_segments_chunk(db: Session, chunks: List[Dict[str, Any]]):
    """Upsert batch de customer_segments no primary."""
    for row in chunks:
        # Remove campos internos (começam com _)
        clean = {k: v for k, v in row.items() if not k.startswith("_")}

        existing = (
            db.query(CustomerSegment)
            .filter(
                CustomerSegment.tenant_id == clean["tenant_id"],
                CustomerSegment.customer_id == clean["customer_id"],
            )
            .first()
        )

        if existing:
            for k, v in clean.items():
                if k not in ("tenant_id", "customer_id"):
                    setattr(existing, k, v)
        else:
            db.add(CustomerSegment(
                id=uuid.uuid4(),
                **clean,
            ))

    db.flush()


def _parse_recent_dates(dates_json) -> List[datetime]:
    """Converte lista de ISO strings para datetimes."""
    if not dates_json:
        return []
    result = []
    for d in dates_json:
        try:
            if isinstance(d, str):
                result.append(datetime.fromisoformat(d))
            elif isinstance(d, datetime):
                result.append(d)
        except (ValueError, TypeError):
            continue
    return result


def _percentile(data: List[float], pct: float) -> float:
    """Percentil simples sem numpy."""
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (pct / 100) * (len(sorted_data) - 1)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])
