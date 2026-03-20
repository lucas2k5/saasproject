from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, Customer
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from app.services.ai_service import AIService

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna estatísticas vitais do sistema para o Dashboard.
    """
    tenant_id = current_user.tenant_id
    now = datetime.now(timezone.utc)

    # 1. Contagem SQL — single round-trip with subqueries
    row = db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM products WHERE tenant_id = :tid) as products,
            (SELECT COUNT(*) FROM categories WHERE tenant_id = :tid) as categories,
            (SELECT COUNT(*) FROM channels WHERE tenant_id = :tid) as channels,
            (SELECT COUNT(*) FROM stores WHERE tenant_id = :tid) as stores,
            (SELECT COUNT(*) FROM customers WHERE tenant_id = :tid) as customers,
            (SELECT COUNT(*) FROM product_prices WHERE tenant_id = :tid) as prices,
            (SELECT COUNT(*) FROM product_stock WHERE tenant_id = :tid) as stock_items,
            (SELECT COUNT(*) FROM orders WHERE tenant_id = :tid) as orders,
            (SELECT COUNT(*) FROM order_items WHERE tenant_id = :tid) as order_items,
            (SELECT COUNT(*) FROM offers WHERE tenant_id = :tid) as offers,
            (SELECT COUNT(*) FROM offers WHERE tenant_id = :tid AND start_at <= :now AND end_at >= :now) as active_offers
    """), {"tid": tenant_id, "now": now}).fetchone()

    total_products = row.products

    # 2. Contagem Qdrant (Vetores)
    try:
        qdrant_info = AIService.get_collection_info(tenant_id)
        total_vectors = qdrant_info.get("points_count", 0)
    except Exception as e:
        print(f"Erro ao conectar Qdrant: {e}")
        total_vectors = 0

    # 3. Status de Sincronia
    sync_status = "synced"
    if total_vectors < total_products:
        sync_status = "indexing"

    return {
        "products": {
            "total": total_products,
            "active": total_products
        },
        "categories": row.categories,
        "channels": row.channels,
        "stores": row.stores,
        "customers": row.customers,
        "prices": row.prices,
        "stock_items": row.stock_items,
        "orders": row.orders,
        "order_items": row.order_items,
        "offers": row.offers,
        "active_offers": row.active_offers,
        "ai_index": {
            "total_vectors": total_vectors,
            "status": sync_status,
            "percentage": int((total_vectors / total_products * 100)) if total_products > 0 else 0
        },
        "tenant": {
            "id": tenant_id,
            "name": f"Tenant {tenant_id}"
        }
    }


@router.get("/stats/lifecycle")
def get_lifecycle_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna estatísticas de ciclo de vida dos clientes para o Dashboard.
    """
    tenant_id = current_user.tenant_id

    ALL_SEGMENTS = ["Prospect", "OneTime", "NonEngaged", "StuckInMiddle", "LoyalRunner", "LoyalStar"]

    total_customers = db.query(Customer).filter(Customer.tenant_id == tenant_id).count()

    # segment_distribution — SQL GROUP BY, all 6 always present
    seg_rows = db.execute(text("""
        SELECT lifecycle_segment, COUNT(*) as cnt
        FROM customer_segments
        WHERE tenant_id = :tid
        GROUP BY lifecycle_segment
    """), {"tid": tenant_id}).fetchall()

    seg_counts: dict[str, int] = {s: 0 for s in ALL_SEGMENTS}
    for r in seg_rows:
        if r.lifecycle_segment in seg_counts:
            seg_counts[r.lifecycle_segment] = r.cnt

    segment_distribution = [{"segment": s, "count": seg_counts[s]} for s in ALL_SEGMENTS]
    total_segmented = sum(seg_counts.values())

    # recency_buckets — SQL CASE WHEN
    recency_rows = db.execute(text("""
        SELECT
            SUM(CASE WHEN recency_days <= 30 THEN 1 ELSE 0 END) as d0_30,
            SUM(CASE WHEN recency_days > 30 AND recency_days <= 60 THEN 1 ELSE 0 END) as d31_60,
            SUM(CASE WHEN recency_days > 60 AND recency_days <= 90 THEN 1 ELSE 0 END) as d61_90,
            SUM(CASE WHEN recency_days > 90 AND recency_days <= 180 THEN 1 ELSE 0 END) as d91_180,
            SUM(CASE WHEN recency_days > 180 AND recency_days <= 365 THEN 1 ELSE 0 END) as d181_365,
            SUM(CASE WHEN recency_days > 365 THEN 1 ELSE 0 END) as d365_plus
        FROM customer_segments
        WHERE tenant_id = :tid AND recency_days IS NOT NULL
    """), {"tid": tenant_id}).fetchone()

    recency_labels = ["0–30d", "31–60d", "61–90d", "91–180d", "181–365d", "+365d"]
    recency_counts = [
        recency_rows.d0_30 or 0,
        recency_rows.d31_60 or 0,
        recency_rows.d61_90 or 0,
        recency_rows.d91_180 or 0,
        recency_rows.d181_365 or 0,
        recency_rows.d365_plus or 0,
    ]
    recency_buckets = [{"label": recency_labels[i], "count": recency_counts[i]} for i in range(6)]

    # p_alive_buckets — SQL CASE WHEN
    p_alive_row = db.execute(text("""
        SELECT
            SUM(CASE WHEN p_alive <= 0.20 THEN 1 ELSE 0 END) as p0_20,
            SUM(CASE WHEN p_alive > 0.20 AND p_alive <= 0.40 THEN 1 ELSE 0 END) as p20_40,
            SUM(CASE WHEN p_alive > 0.40 AND p_alive <= 0.60 THEN 1 ELSE 0 END) as p40_60,
            SUM(CASE WHEN p_alive > 0.60 AND p_alive <= 0.80 THEN 1 ELSE 0 END) as p60_80,
            SUM(CASE WHEN p_alive > 0.80 THEN 1 ELSE 0 END) as p80_100
        FROM customer_segments
        WHERE tenant_id = :tid AND p_alive IS NOT NULL
    """), {"tid": tenant_id}).fetchone()

    p_alive_labels = ["0–20%", "20–40%", "40–60%", "60–80%", "80–100%"]
    p_alive_counts = [
        p_alive_row.p0_20 or 0,
        p_alive_row.p20_40 or 0,
        p_alive_row.p40_60 or 0,
        p_alive_row.p60_80 or 0,
        p_alive_row.p80_100 or 0,
    ]
    p_alive_buckets = [{"label": p_alive_labels[i], "count": p_alive_counts[i]} for i in range(5)]

    # avg_ticket_by_segment — SQL GROUP BY + AVG
    ticket_rows = db.execute(text("""
        SELECT lifecycle_segment, AVG(avg_ticket) as avg_ticket
        FROM customer_segments
        WHERE tenant_id = :tid AND avg_ticket > 0
        GROUP BY lifecycle_segment
        ORDER BY avg_ticket DESC
    """), {"tid": tenant_id}).fetchall()

    avg_ticket_by_segment = [
        {"segment": r.lifecycle_segment, "avg_ticket": round(float(r.avg_ticket), 2)}
        for r in ticket_rows
        if r.lifecycle_segment in seg_counts
    ]

    # frequency_buckets — distribuição de frequência de compras
    freq_row = db.execute(text("""
        SELECT
            SUM(CASE WHEN number_of_invoices = 1 THEN 1 ELSE 0 END) as f1,
            SUM(CASE WHEN number_of_invoices BETWEEN 2 AND 3 THEN 1 ELSE 0 END) as f2_3,
            SUM(CASE WHEN number_of_invoices BETWEEN 4 AND 5 THEN 1 ELSE 0 END) as f4_5,
            SUM(CASE WHEN number_of_invoices BETWEEN 6 AND 10 THEN 1 ELSE 0 END) as f6_10,
            SUM(CASE WHEN number_of_invoices BETWEEN 11 AND 20 THEN 1 ELSE 0 END) as f11_20,
            SUM(CASE WHEN number_of_invoices > 20 THEN 1 ELSE 0 END) as f21_plus
        FROM customer_segments
        WHERE tenant_id = :tid AND number_of_invoices IS NOT NULL
    """), {"tid": tenant_id}).fetchone()
    frequency_buckets = [
        {"label": "1", "count": freq_row.f1 or 0},
        {"label": "2–3", "count": freq_row.f2_3 or 0},
        {"label": "4–5", "count": freq_row.f4_5 or 0},
        {"label": "6–10", "count": freq_row.f6_10 or 0},
        {"label": "11–20", "count": freq_row.f11_20 or 0},
        {"label": "21+", "count": freq_row.f21_plus or 0},
    ]

    # ticket_trend_buckets — tendência de ticket (90d vs prev 90d)
    tt_row = db.execute(text("""
        SELECT
            SUM(CASE WHEN ticket_trend < 0.5 THEN 1 ELSE 0 END) as falling_hard,
            SUM(CASE WHEN ticket_trend >= 0.5 AND ticket_trend < 0.8 THEN 1 ELSE 0 END) as falling,
            SUM(CASE WHEN ticket_trend >= 0.8 AND ticket_trend <= 1.2 THEN 1 ELSE 0 END) as stable,
            SUM(CASE WHEN ticket_trend > 1.2 AND ticket_trend <= 1.5 THEN 1 ELSE 0 END) as rising,
            SUM(CASE WHEN ticket_trend > 1.5 THEN 1 ELSE 0 END) as rising_hard
        FROM customer_segments
        WHERE tenant_id = :tid AND ticket_trend IS NOT NULL
    """), {"tid": tenant_id}).fetchone()
    ticket_trend_buckets = [
        {"label": "Caindo muito (<0.5)", "count": tt_row.falling_hard or 0},
        {"label": "Caindo (0.5–0.8)", "count": tt_row.falling or 0},
        {"label": "Estável (0.8–1.2)", "count": tt_row.stable or 0},
        {"label": "Subindo (1.2–1.5)", "count": tt_row.rising or 0},
        {"label": "Subindo muito (>1.5)", "count": tt_row.rising_hard or 0},
    ]

    # velocity_trend_buckets — tendência de velocidade de compra
    vt_row = db.execute(text("""
        SELECT
            SUM(CASE WHEN purchase_velocity_trend < 0.5 THEN 1 ELSE 0 END) as decel_hard,
            SUM(CASE WHEN purchase_velocity_trend >= 0.5 AND purchase_velocity_trend < 0.8 THEN 1 ELSE 0 END) as decel,
            SUM(CASE WHEN purchase_velocity_trend >= 0.8 AND purchase_velocity_trend <= 1.2 THEN 1 ELSE 0 END) as stable,
            SUM(CASE WHEN purchase_velocity_trend > 1.2 AND purchase_velocity_trend <= 1.5 THEN 1 ELSE 0 END) as accel,
            SUM(CASE WHEN purchase_velocity_trend > 1.5 THEN 1 ELSE 0 END) as accel_hard
        FROM customer_segments
        WHERE tenant_id = :tid AND purchase_velocity_trend IS NOT NULL
    """), {"tid": tenant_id}).fetchone()
    velocity_trend_buckets = [
        {"label": "Desacelerando muito", "count": vt_row.decel_hard or 0},
        {"label": "Desacelerando", "count": vt_row.decel or 0},
        {"label": "Estável", "count": vt_row.stable or 0},
        {"label": "Acelerando", "count": vt_row.accel or 0},
        {"label": "Acelerando muito", "count": vt_row.accel_hard or 0},
    ]

    # channel_distribution — canal preferido dos clientes
    channel_rows = db.execute(text("""
        SELECT preferred_channel, COUNT(*) as cnt
        FROM customer_segments
        WHERE tenant_id = :tid AND preferred_channel IS NOT NULL
        GROUP BY preferred_channel
        ORDER BY cnt DESC
    """), {"tid": tenant_id}).fetchall()
    channel_distribution = [{"channel": r.preferred_channel, "count": r.cnt} for r in channel_rows]

    # category_diversity_buckets — diversidade de categorias compradas
    cd_row = db.execute(text("""
        SELECT
            SUM(CASE WHEN category_diversity = 1 THEN 1 ELSE 0 END) as c1,
            SUM(CASE WHEN category_diversity BETWEEN 2 AND 3 THEN 1 ELSE 0 END) as c2_3,
            SUM(CASE WHEN category_diversity BETWEEN 4 AND 5 THEN 1 ELSE 0 END) as c4_5,
            SUM(CASE WHEN category_diversity BETWEEN 6 AND 10 THEN 1 ELSE 0 END) as c6_10,
            SUM(CASE WHEN category_diversity > 10 THEN 1 ELSE 0 END) as c11_plus
        FROM customer_segments
        WHERE tenant_id = :tid AND category_diversity IS NOT NULL
    """), {"tid": tenant_id}).fetchone()
    category_diversity_buckets = [
        {"label": "1", "count": cd_row.c1 or 0},
        {"label": "2–3", "count": cd_row.c2_3 or 0},
        {"label": "4–5", "count": cd_row.c4_5 or 0},
        {"label": "6–10", "count": cd_row.c6_10 or 0},
        {"label": "11+", "count": cd_row.c11_plus or 0},
    ]

    # promo_ratio_buckets — dependência de promoção
    pr_row = db.execute(text("""
        SELECT
            SUM(CASE WHEN promo_ratio = 0 THEN 1 ELSE 0 END) as p0,
            SUM(CASE WHEN promo_ratio > 0 AND promo_ratio <= 0.25 THEN 1 ELSE 0 END) as p1_25,
            SUM(CASE WHEN promo_ratio > 0.25 AND promo_ratio <= 0.50 THEN 1 ELSE 0 END) as p26_50,
            SUM(CASE WHEN promo_ratio > 0.50 AND promo_ratio <= 0.75 THEN 1 ELSE 0 END) as p51_75,
            SUM(CASE WHEN promo_ratio > 0.75 THEN 1 ELSE 0 END) as p76_100
        FROM customer_segments
        WHERE tenant_id = :tid AND promo_ratio IS NOT NULL
    """), {"tid": tenant_id}).fetchone()
    promo_ratio_buckets = [
        {"label": "0%", "count": pr_row.p0 or 0},
        {"label": "1–25%", "count": pr_row.p1_25 or 0},
        {"label": "26–50%", "count": pr_row.p26_50 or 0},
        {"label": "51–75%", "count": pr_row.p51_75 or 0},
        {"label": "76–100%", "count": pr_row.p76_100 or 0},
    ]

    # tenure_buckets — tempo como cliente
    tn_row = db.execute(text("""
        SELECT
            SUM(CASE WHEN days_as_customer <= 90 THEN 1 ELSE 0 END) as t0_90,
            SUM(CASE WHEN days_as_customer > 90 AND days_as_customer <= 180 THEN 1 ELSE 0 END) as t91_180,
            SUM(CASE WHEN days_as_customer > 180 AND days_as_customer <= 365 THEN 1 ELSE 0 END) as t181_365,
            SUM(CASE WHEN days_as_customer > 365 AND days_as_customer <= 730 THEN 1 ELSE 0 END) as t1_2y,
            SUM(CASE WHEN days_as_customer > 730 AND days_as_customer <= 1095 THEN 1 ELSE 0 END) as t2_3y,
            SUM(CASE WHEN days_as_customer > 1095 THEN 1 ELSE 0 END) as t3y_plus
        FROM customer_segments
        WHERE tenant_id = :tid AND days_as_customer IS NOT NULL
    """), {"tid": tenant_id}).fetchone()
    tenure_buckets = [
        {"label": "0–3m", "count": tn_row.t0_90 or 0},
        {"label": "3–6m", "count": tn_row.t91_180 or 0},
        {"label": "6m–1a", "count": tn_row.t181_365 or 0},
        {"label": "1–2a", "count": tn_row.t1_2y or 0},
        {"label": "2–3a", "count": tn_row.t2_3y or 0},
        {"label": "3a+", "count": tn_row.t3y_plus or 0},
    ]

    # top_recommended_products — top 10 produtos mais recomendados
    top_products = db.execute(text("""
        SELECT product_name, product_external_id, COUNT(*) as cnt
        FROM customer_recommendations_current
        WHERE tenant_id = :tid
        GROUP BY product_name, product_external_id
        ORDER BY cnt DESC
        LIMIT 10
    """), {"tid": tenant_id}).fetchall()
    top_recommended_products = [
        {"name": r.product_name, "external_id": r.product_external_id, "count": r.cnt}
        for r in top_products
    ]

    # top_recommended_categories — top 10 categorias mais recomendadas
    top_cats = db.execute(text("""
        SELECT product_category->>0 as cat_name, COUNT(*) as cnt
        FROM customer_recommendations_current
        WHERE tenant_id = :tid AND product_category IS NOT NULL
        GROUP BY product_category->>0
        ORDER BY cnt DESC
        LIMIT 10
    """), {"tid": tenant_id}).fetchall()
    top_recommended_categories = [
        {"category": r.cat_name, "count": r.cnt}
        for r in top_cats
    ]

    return {
        "segment_distribution": segment_distribution,
        "recency_buckets": recency_buckets,
        "p_alive_buckets": p_alive_buckets,
        "avg_ticket_by_segment": avg_ticket_by_segment,
        "total_segmented": total_segmented,
        "total_customers": total_customers,
        "frequency_buckets": frequency_buckets,
        "ticket_trend_buckets": ticket_trend_buckets,
        "velocity_trend_buckets": velocity_trend_buckets,
        "channel_distribution": channel_distribution,
        "category_diversity_buckets": category_diversity_buckets,
        "promo_ratio_buckets": promo_ratio_buckets,
        "tenure_buckets": tenure_buckets,
        "top_recommended_products": top_recommended_products,
        "top_recommended_categories": top_recommended_categories,
    }


@router.get("/stats/revenue")
def get_revenue_stats(
    months_back: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Receita realizada (histórico mensal) + previsão (próximos 3 meses).
    Previsão usa expected_transactions * avg_ticket do BG/NBD.
    """
    tenant_id = current_user.tenant_id
    now = datetime.now(timezone.utc)

    # ---- Receita realizada: últimos N meses agrupados por mês ----
    start_date = (now - relativedelta(months=months_back)).replace(day=1)

    actual_rows = db.execute(text("""
        SELECT
            TO_CHAR(ordered_at, 'YYYY-MM') as month,
            SUM(net_value) as revenue,
            COUNT(DISTINCT id) as orders,
            COUNT(DISTINCT customer_id) as customers
        FROM orders
        WHERE tenant_id = :tid AND ordered_at >= :start
        GROUP BY TO_CHAR(ordered_at, 'YYYY-MM')
        ORDER BY month
    """), {"tid": tenant_id, "start": start_date}).fetchall()

    actual = [
        {
            "month": r.month,
            "revenue": round(float(r.revenue), 2),
            "orders": r.orders,
            "customers": r.customers,
        }
        for r in actual_rows
    ]

    # ---- Previsão: soma de (expected_transactions * avg_ticket) por cliente ----
    # expected_transactions = pedidos esperados nos próximos 90 dias (BG/NBD)
    forecast_row = db.execute(text("""
        SELECT
            SUM(expected_transactions * avg_ticket) as total_forecast_90d,
            COUNT(*) as customers_with_forecast,
            AVG(expected_transactions) as avg_expected_txn,
            AVG(avg_ticket) as avg_ticket
        FROM customer_segments
        WHERE tenant_id = :tid
          AND expected_transactions IS NOT NULL
          AND expected_transactions > 0
          AND avg_ticket IS NOT NULL
          AND avg_ticket > 0
    """), {"tid": tenant_id}).fetchone()

    total_forecast_90d = float(forecast_row.total_forecast_90d or 0)
    customers_with_forecast = forecast_row.customers_with_forecast or 0

    # Distribui proporcionalmente nos próximos 3 meses (1/3 cada)
    forecast = []
    for i in range(1, 4):
        future_month = now + relativedelta(months=i)
        month_str = future_month.strftime("%Y-%m")
        forecast.append({
            "month": month_str,
            "revenue": round(total_forecast_90d / 3, 2),
        })

    # ---- Métricas resumo ----
    # Mês atual (parcial)
    current_month = now.strftime("%Y-%m")
    current_month_row = db.execute(text("""
        SELECT
            COALESCE(SUM(net_value), 0) as revenue,
            COUNT(DISTINCT id) as orders
        FROM orders
        WHERE tenant_id = :tid
          AND TO_CHAR(ordered_at, 'YYYY-MM') = :month
    """), {"tid": tenant_id, "month": current_month}).fetchone()

    # Mês anterior completo
    prev_month = (now - relativedelta(months=1)).strftime("%Y-%m")
    prev_month_row = db.execute(text("""
        SELECT COALESCE(SUM(net_value), 0) as revenue
        FROM orders
        WHERE tenant_id = :tid
          AND TO_CHAR(ordered_at, 'YYYY-MM') = :month
    """), {"tid": tenant_id, "month": prev_month}).fetchone()

    # Média mensal dos últimos 6 meses
    avg_6m_row = db.execute(text("""
        SELECT COALESCE(AVG(monthly_rev), 0) as avg_revenue
        FROM (
            SELECT SUM(net_value) as monthly_rev
            FROM orders
            WHERE tenant_id = :tid
              AND ordered_at >= :start_6m
            GROUP BY TO_CHAR(ordered_at, 'YYYY-MM')
        ) sub
    """), {"tid": tenant_id, "start_6m": (now - relativedelta(months=6)).replace(day=1)}).fetchone()

    return {
        "actual": actual,
        "forecast": forecast,
        "summary": {
            "current_month": current_month,
            "current_month_revenue": round(float(current_month_row.revenue), 2),
            "current_month_orders": current_month_row.orders,
            "prev_month_revenue": round(float(prev_month_row.revenue), 2),
            "avg_monthly_revenue_6m": round(float(avg_6m_row.avg_revenue), 2),
            "forecast_next_90d": round(total_forecast_90d, 2),
            "forecast_monthly_avg": round(total_forecast_90d / 3, 2),
            "customers_with_forecast": customers_with_forecast,
        },
    }
