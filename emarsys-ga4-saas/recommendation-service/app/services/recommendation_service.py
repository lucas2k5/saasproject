"""
Motor de Recomendação Personalizada — Serviço central.

3 algoritmos independentes:
  - Pessoal: cesta conhecida do cliente, rankeada por afinidade + sazonalidade
  - Descoberta: produtos similares nunca comprados, proporcional às categorias
  - Top Sellers: mais vendidos da loja preferida (fallback + principal para Prospects)

Processamento em chunks para escala (1M+ clientes).
Toda busca de similares via ProductSimilars (SQL) — zero Qdrant no noturno.
"""
import math
import uuid as uuid_mod
from datetime import datetime, timedelta, date, timezone
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.models import (
    TenantConfig, Customer, CustomerSegment, Order, OrderItem, Product,
    ProductSimilar, StoreTopSeller, CustomerRecommendation,
    ProductStock, ProductPrice, Offer, OfferProduct, OfferAudience,
    Store,
)
from app.services.offer_utils import compute_promo_price

CHUNK_SIZE = 5000


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _seasonality_multiplier(days_since_purchase: int, cycle_days: Optional[int]) -> float:
    """Multiplicador de sazonalidade sobre o score base."""
    if not cycle_days or cycle_days <= 0:
        return 1.0
    ratio = days_since_purchase / cycle_days
    if ratio < 0.5:
        return 0.3
    elif ratio < 0.8:
        return 0.7
    elif ratio <= 1.2:
        return 1.5
    elif ratio <= 2.0:
        return 1.2
    else:
        return 0.8


def _decay_recency(days: int, half_life: float = 30.0) -> float:
    """Decay exponencial: e^(-dias/meia_vida). Meia-vida fixa 30 dias."""
    if days <= 0:
        return 1.0
    return math.exp(-days / half_life)


def _compute_percentile_ranks(values: list[float]) -> list[float]:
    """
    Rank normalizado 0-1 para uma lista de valores.
    Maior valor = rank 1.0, menor = ~0.
    """
    n = len(values)
    if n <= 1:
        return [1.0] * n
    sorted_indices = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    for pos, idx in enumerate(sorted_indices):
        ranks[idx] = (pos + 1) / n
    return ranks


# ------------------------------------------------------------------ #
# Bulk data loaders — carregam tudo 1x em memória por tenant
# ------------------------------------------------------------------ #

def _load_product_map(db: Session, tenant_id: str) -> dict:
    """product_id (str) → {price, category, name, image_url, external_id, cycle_type, cycle_days}"""
    products = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.is_active == True
    ).all()
    return {
        str(p.id): {
            "id": str(p.id),
            "external_id": p.external_id,
            "name": p.name,
            "price": p.price or 0,
            "image_url": p.image_url,
            "category": p.category,
            "cycle_type": p.purchase_cycle_type,
            "cycle_days": p.purchase_cycle_days,
        }
        for p in products
    }


def _load_similars_map(db: Session, tenant_id: str) -> dict:
    """product_id → [(similar_product_id, rank, score, price_ratio), ...] ordenado por rank."""
    rows = db.query(ProductSimilar).filter(
        ProductSimilar.tenant_id == tenant_id
    ).order_by(ProductSimilar.product_id, ProductSimilar.rank).all()

    result = defaultdict(list)
    for r in rows:
        result[r.product_id].append({
            "similar_id": r.similar_product_id,
            "rank": r.rank,
            "score": r.score,
            "price_ratio": r.price_ratio,
        })
    return dict(result)


def _load_stock_dict(db: Session, tenant_id: str) -> dict:
    """(store_id_uuid, product_id_str) → {quantity, available}"""
    rows = db.query(ProductStock).filter(
        ProductStock.tenant_id == tenant_id
    ).all()
    return {
        (str(r.store_id), r.product_id): {
            "quantity": r.quantity,
            "available": r.available,
        }
        for r in rows
    }


def _load_price_dict(db: Session, tenant_id: str) -> dict:
    """(store_id_uuid_str, product_id_str) → price"""
    rows = db.query(ProductPrice).filter(
        ProductPrice.tenant_id == tenant_id
    ).all()
    return {
        (str(r.store_id), r.product_id): r.price
        for r in rows
    }


def _load_active_offers(db: Session, tenant_id: str) -> tuple[list, dict, dict]:
    """
    Retorna:
      - offers: lista de Offer objects ativos
      - offer_products: offer_id → [product_id, ...]
      - offer_audiences: offer_id → [OfferAudience, ...]
    """
    now = datetime.now(timezone.utc)
    offers = db.query(Offer).filter(
        Offer.tenant_id == tenant_id,
        Offer.start_at <= now,
        Offer.end_at >= now,
    ).all()

    offer_ids = [o.id for o in offers]
    if not offer_ids:
        return [], {}, {}

    # Produtos por oferta
    op_rows = db.query(OfferProduct).filter(
        OfferProduct.offer_id.in_(offer_ids)
    ).all()
    offer_products = defaultdict(list)
    for op in op_rows:
        offer_products[str(op.offer_id)].append(op.product_id)

    # Audiências por oferta
    aud_rows = db.query(OfferAudience).filter(
        OfferAudience.offer_id.in_(offer_ids)
    ).all()
    offer_audiences = defaultdict(list)
    for a in aud_rows:
        offer_audiences[str(a.offer_id)].append(a)

    return offers, dict(offer_products), dict(offer_audiences)


def _load_top_sellers(db: Session, tenant_id: str) -> dict:
    """store_id_str → [{product_id, product_external_id, product_name, product_image_url, rank}, ...]"""
    rows = db.query(StoreTopSeller).filter(
        StoreTopSeller.tenant_id == tenant_id
    ).order_by(StoreTopSeller.store_id, StoreTopSeller.rank).all()

    result = defaultdict(list)
    for r in rows:
        result[str(r.store_id)].append({
            "product_id": r.product_id,
            "product_external_id": r.product_external_id,
            "product_name": r.product_name,
            "product_image_url": r.product_image_url,
            "rank": r.rank,
        })
    return dict(result)


# ------------------------------------------------------------------ #
# Preferred store
# ------------------------------------------------------------------ #

def _compute_preferred_stores(db: Session, tenant_id: str) -> dict:
    """customer_id (UUID str) → store_id (UUID str). Baseado em frequência de pedidos."""
    result = db.execute(text("""
        SELECT customer_id, store_id, COUNT(*) as cnt
        FROM orders
        WHERE tenant_id = :tid AND store_id IS NOT NULL
        GROUP BY customer_id, store_id
        ORDER BY customer_id, cnt DESC
    """), {"tid": tenant_id}).fetchall()

    preferred = {}
    for row in result:
        cid = str(row[0])
        if cid not in preferred:  # primeiro = maior count (ORDER BY cnt DESC)
            preferred[cid] = str(row[1])
    return preferred


# ------------------------------------------------------------------ #
# Offer matching
# ------------------------------------------------------------------ #

def _find_best_offer_for_product(
    product_id: str,
    store_id: Optional[str],
    customer_segment: Optional[str],
    customer_type: Optional[str],
    customer_id_ext: Optional[str],
    offers: list,
    offer_products: dict,
    offer_audiences: dict,
) -> Optional[dict]:
    """
    Encontra a melhor oferta para um produto na loja do cliente.
    Retorna dict com offer_id, offer_type, offer_name, offer_price ou None.
    Menor preço vence (sem stacking).
    """
    best = None
    for offer in offers:
        oid = str(offer.id)

        # Verifica se o produto faz parte da oferta
        if product_id not in offer_products.get(oid, []):
            continue

        # Verifica se a oferta vale para a loja
        if offer.store_ids and store_id:
            if store_id not in [str(s) for s in offer.store_ids]:
                continue

        # Verifica audiência
        audiences = offer_audiences.get(oid, [])
        if audiences:
            qualifies = False
            for aud in audiences:
                if aud.audience_type == "ALL":
                    qualifies = True
                    break
                elif aud.audience_type == "LIFECYCLE_SEGMENT" and customer_segment:
                    if customer_segment in (aud.audience_value or []):
                        qualifies = True
                        break
                elif aud.audience_type == "CUSTOMER_TYPE" and customer_type:
                    if customer_type in (aud.audience_value or []):
                        qualifies = True
                        break
                elif aud.audience_type == "CUSTOMER_IDS" and customer_id_ext:
                    if customer_id_ext in (aud.audience_value or []):
                        qualifies = True
                        break
            if not qualifies:
                continue

        offer_info = {
            "offer_id": offer.id,
            "offer_type": offer.type,
            "offer_name": offer.name,
            "offer_end_at": offer.end_at,
            "mechanic_params": offer.mechanic_params or {},
            "_priority": offer.priority or 0,
        }

        if best is None:
            best = offer_info
        else:
            if offer_info["_priority"] > best["_priority"]:
                best = offer_info

    if best:
        best.pop("_priority", None)
    return best


# ------------------------------------------------------------------ #
# Check stock
# ------------------------------------------------------------------ #

def _has_stock(product_id: str, store_id: str, stock_dict: dict) -> bool:
    """Verifica se produto tem estoque disponível na loja."""
    key = (store_id, product_id)
    stock = stock_dict.get(key)
    if not stock:
        return False
    return stock["available"] and stock["quantity"] > 0


# ------------------------------------------------------------------ #
# Algoritmo Pessoal — Score de afinidade + sazonalidade
# ------------------------------------------------------------------ #

def _compute_personal_rank(
    purchase_history: list[dict],
    product_map: dict,
    weights: tuple[float, float, float],
    today: date,
) -> list[dict]:
    """
    Calcula rank pessoal para um cliente.
    purchase_history: [{product_id, total_qty, total_value, last_ordered_at}, ...]
    Retorna lista ordenada por score_final DESC.
    """
    if not purchase_history:
        return []

    w_freq, w_val, w_rec = weights

    # Extrair arrays
    freqs = [h["total_qty"] for h in purchase_history]
    values = [h["total_value"] for h in purchase_history]
    days_since = []
    for h in purchase_history:
        if h["last_ordered_at"]:
            delta = (today - h["last_ordered_at"].date()).days
            days_since.append(max(delta, 0))
        else:
            days_since.append(365)

    # Normalizar
    rank_freq = _compute_percentile_ranks(freqs)
    rank_val = _compute_percentile_ranks(values)
    decays = [_decay_recency(d) for d in days_since]

    results = []
    for i, h in enumerate(purchase_history):
        pid = h["product_id"]
        prod = product_map.get(pid)
        if not prod:
            continue

        score_base = (rank_freq[i] * w_freq) + (rank_val[i] * w_val) + (decays[i] * w_rec)
        mult = _seasonality_multiplier(days_since[i], prod.get("cycle_days"))
        score_final = score_base * mult

        results.append({
            "product_id": pid,
            "score": round(score_final, 6),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


# ------------------------------------------------------------------ #
# Algoritmo Descoberta — similares nunca comprados
# ------------------------------------------------------------------ #

def _compute_discovery_rank(
    purchase_history: list[dict],
    product_map: dict,
    similars_map: dict,
    depth: int,
) -> list[dict]:
    """
    Busca produtos similares que o cliente nunca comprou,
    proporcional às categorias do histórico.
    """
    if not purchase_history:
        return []

    purchased_ids = {h["product_id"] for h in purchase_history}

    # Distribuição por categoria (top-level)
    category_freq = defaultdict(float)
    total_freq = 0
    for h in purchase_history:
        prod = product_map.get(h["product_id"])
        if not prod or not prod["category"]:
            continue
        cat = prod["category"]
        if isinstance(cat, list) and cat:
            top_cat = str(cat[0]).split(" > ")[0].strip()
        elif isinstance(cat, str):
            top_cat = cat.split(" > ")[0].strip()
        else:
            continue
        category_freq[top_cat] += h["total_qty"]
        total_freq += h["total_qty"]

    if total_freq == 0:
        return []

    # Slots por categoria (proporcional)
    cat_slots = {}
    for cat, freq in category_freq.items():
        cat_slots[cat] = max(1, round((freq / total_freq) * depth))

    # Coletar similares por categoria
    seen = set(purchased_ids)
    results = []

    # Para cada produto comprado (ordenado por frequência), buscar similares
    sorted_history = sorted(purchase_history, key=lambda x: x["total_qty"], reverse=True)

    for h in sorted_history:
        pid = h["product_id"]
        prod = product_map.get(pid)
        if not prod:
            continue

        # Categoria top-level deste produto
        cat = prod["category"]
        if isinstance(cat, list) and cat:
            top_cat = str(cat[0]).split(" > ")[0].strip()
        elif isinstance(cat, str):
            top_cat = cat.split(" > ")[0].strip()
        else:
            continue

        remaining_slots = cat_slots.get(top_cat, 0)
        if remaining_slots <= 0:
            continue

        sims = similars_map.get(pid, [])
        for sim in sims:
            sim_id = sim["similar_id"]
            if sim_id in seen:
                continue
            if sim_id not in product_map:
                continue

            seen.add(sim_id)
            results.append({
                "product_id": sim_id,
                "score": round(sim["score"], 6),
            })
            cat_slots[top_cat] -= 1
            if cat_slots[top_cat] <= 0:
                break

        if len(results) >= depth:
            break

    return results[:depth]


# ------------------------------------------------------------------ #
# Fallback chain — substitui produtos sem estoque/oferta
# ------------------------------------------------------------------ #

def _apply_fallback_chain(
    ranked: list[dict],
    store_id: Optional[str],
    stock_dict: dict,
    price_dict: dict,
    product_map: dict,
    similars_map: dict,
    offers: list,
    offer_products: dict,
    offer_audiences: dict,
    customer_segment: Optional[str],
    customer_type: Optional[str],
    customer_id_ext: Optional[str],
    require_offer: bool,
    max_results: int,
) -> list[dict]:
    """
    Aplica filtro estoque + oferta com fallback chain.
    Retorna lista final de até max_results produtos com todos os dados.
    """
    final = []

    for item in ranked:
        if len(final) >= max_results:
            break

        pid = item["product_id"]
        result = _try_product(
            pid, item["score"], None, store_id, stock_dict, price_dict,
            product_map, offers, offer_products, offer_audiences,
            customer_segment, customer_type, customer_id_ext, require_offer,
        )
        if result:
            final.append(result)
            continue

        # Fallback: buscar similar com estoque + oferta
        sims = similars_map.get(pid, [])
        found = False

        # Fase 1: mesma faixa de preço (0.8 - 1.2)
        for sim in sims:
            pr = sim.get("price_ratio")
            if pr and 0.8 <= pr <= 1.2:
                r = _try_product(
                    sim["similar_id"], item["score"] * 0.95, pid,
                    store_id, stock_dict, price_dict, product_map,
                    offers, offer_products, offer_audiences,
                    customer_segment, customer_type, customer_id_ext, require_offer,
                )
                if r:
                    final.append(r)
                    found = True
                    break

        if found:
            continue

        # Fase 2: mais caro (price_ratio > 1.2)
        for sim in sims:
            pr = sim.get("price_ratio")
            if pr and pr > 1.2:
                r = _try_product(
                    sim["similar_id"], item["score"] * 0.9, pid,
                    store_id, stock_dict, price_dict, product_map,
                    offers, offer_products, offer_audiences,
                    customer_segment, customer_type, customer_id_ext, require_offer,
                )
                if r:
                    final.append(r)
                    found = True
                    break

        if found:
            continue

        # Fase 3: mais barato (price_ratio < 0.8)
        for sim in sims:
            pr = sim.get("price_ratio")
            if pr and pr < 0.8:
                r = _try_product(
                    sim["similar_id"], item["score"] * 0.85, pid,
                    store_id, stock_dict, price_dict, product_map,
                    offers, offer_products, offer_audiences,
                    customer_segment, customer_type, customer_id_ext, require_offer,
                )
                if r:
                    final.append(r)
                    found = True
                    break

        # Se nenhum similar serve → produto é ignorado, segue pro próximo

    return final


def _try_product(
    product_id: str,
    score: float,
    original_product_id: Optional[str],
    store_id: Optional[str],
    stock_dict: dict,
    price_dict: dict,
    product_map: dict,
    offers: list,
    offer_products: dict,
    offer_audiences: dict,
    customer_segment: Optional[str],
    customer_type: Optional[str],
    customer_id_ext: Optional[str],
    require_offer: bool,
) -> Optional[dict]:
    """Tenta usar um produto: verifica estoque + oferta. Retorna dict completo ou None."""
    prod = product_map.get(product_id)
    if not prod:
        return None

    # Verifica estoque
    if store_id and not _has_stock(product_id, store_id, stock_dict):
        return None

    # Preço base na loja
    base_price = None
    if store_id:
        base_price = price_dict.get((store_id, product_id))
    if base_price is None:
        base_price = prod["price"]

    # Verifica oferta
    offer_info = _find_best_offer_for_product(
        product_id, store_id, customer_segment, customer_type,
        customer_id_ext, offers, offer_products, offer_audiences,
    )

    has_offer = offer_info is not None
    if require_offer and not has_offer:
        return None

    # Calcula preço promocional
    offer_price = None
    if offer_info and base_price is not None:
        offer_price = compute_promo_price(
            offer_info["offer_type"],
            offer_info.get("mechanic_params", {}),
            base_price,
        )
        # Se preço promo == base, não faz sentido mostrar
        if offer_price == base_price:
            offer_price = None

    return {
        "product_id": product_id,
        "product_external_id": prod["external_id"],
        "product_name": prod["name"],
        "product_image_url": prod.get("image_url"),
        "product_category": prod.get("category"),
        "score": score,
        "original_product_id": original_product_id,
        "base_price": base_price,
        "has_offer": has_offer,
        "offer_id": offer_info["offer_id"] if offer_info else None,
        "offer_type": offer_info["offer_type"] if offer_info else None,
        "offer_price": offer_price,
        "offer_name": offer_info["offer_name"] if offer_info else None,
        "offer_end_at": offer_info["offer_end_at"] if offer_info else None,
    }


# ------------------------------------------------------------------ #
# Top Sellers — computar e salvar
# ------------------------------------------------------------------ #

class RecommendationService:

    @staticmethod
    def compute_top_sellers(db: Session, tenant_id: str, window_days: int = 90, top_n: int = 30):
        """
        Agrega vendas por loja nos últimos N dias e grava em store_top_sellers.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        rows = db.execute(text("""
            SELECT o.store_id, oi.product_id, oi.product_external_id,
                   SUM(oi.quantity) as total_qty, SUM(oi.net_price) as total_val
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.tenant_id = :tid
              AND o.store_id IS NOT NULL
              AND o.ordered_at >= :cutoff
              AND o.status != 'cancelled'
            GROUP BY o.store_id, oi.product_id, oi.product_external_id
            ORDER BY o.store_id, total_qty DESC
        """), {"tid": tenant_id, "cutoff": cutoff}).fetchall()

        # Agrupar por store e pegar top N
        store_products = defaultdict(list)
        for r in rows:
            store_id = str(r[0])
            store_products[store_id].append({
                "product_id": r[1],
                "product_external_id": r[2],
                "total_qty": r[3],
                "total_val": r[4],
            })

        # Carregar nomes dos produtos
        product_map = _load_product_map(db, tenant_id)

        # Limpar antigos
        db.query(StoreTopSeller).filter(
            StoreTopSeller.tenant_id == tenant_id
        ).delete(synchronize_session=False)

        now = datetime.now(timezone.utc)
        inserts = []
        for store_id, products in store_products.items():
            for rank_idx, p in enumerate(products[:top_n]):
                prod = product_map.get(p["product_id"])
                inserts.append({
                    "id": uuid_mod.uuid4(),
                    "tenant_id": tenant_id,
                    "store_id": store_id,
                    "rank": rank_idx + 1,
                    "product_id": p["product_id"],
                    "product_external_id": p["product_external_id"],
                    "product_name": prod["name"] if prod else p["product_external_id"],
                    "product_image_url": prod.get("image_url") if prod else None,
                    "total_qty_sold": p["total_qty"],
                    "total_value": p["total_val"],
                    "computed_at": now,
                })

        if inserts:
            db.bulk_insert_mappings(StoreTopSeller, inserts)

        db.commit()
        print(f"TopSellers: {len(inserts)} registros para {len(store_products)} lojas.")

    # ------------------------------------------------------------------ #
    # Orquestrador principal — processa todos os clientes de um tenant
    # ------------------------------------------------------------------ #

    @staticmethod
    def run_for_tenant(tenant_id: str, db: Session):
        """
        Processa recomendações para todos os clientes de um tenant.
        Chunks de CHUNK_SIZE clientes, grava em current + history.
        """
        print(f"\n{'='*60}")
        print(f"Recomendação: iniciando para tenant {tenant_id}")
        print(f"{'='*60}")

        # Carregar configurações
        config = db.query(TenantConfig).filter(
            TenantConfig.tenant_id == tenant_id
        ).first()

        lookback_months = config.rec_lookback_months if config else 12
        w_freq = config.rec_weight_frequency if config else 0.5
        w_val = config.rec_weight_value if config else 0.3
        w_rec = config.rec_weight_recency if config else 0.2
        require_offer = config.rec_require_offer if config else True
        results_per_algo = config.rec_results_per_algo if config else 6
        rank_depth = config.rec_rank_depth if config else 30
        topsellers_window = config.rec_topsellers_window_days if config else 90

        weights = (w_freq, w_val, w_rec)
        today = date.today()
        now = datetime.now(timezone.utc)
        computed_date_str = today.isoformat()
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_months * 30)

        # ---- Bulk loads (1x por tenant) ----
        print("Carregando dados do tenant...")
        product_map = _load_product_map(db, tenant_id)
        similars_map = _load_similars_map(db, tenant_id)
        stock_dict = _load_stock_dict(db, tenant_id)
        price_dict = _load_price_dict(db, tenant_id)
        offers, offer_products, offer_audiences = _load_active_offers(db, tenant_id)
        top_sellers_map = _load_top_sellers(db, tenant_id)
        preferred_stores = _compute_preferred_stores(db, tenant_id)

        print(f"  Produtos: {len(product_map)} | Similares: {sum(len(v) for v in similars_map.values())} | "
              f"Ofertas: {len(offers)} | Lojas c/ top sellers: {len(top_sellers_map)}")

        # ---- Carregar clientes com segmento ----
        customers = db.query(Customer).filter(
            Customer.tenant_id == tenant_id
        ).all()

        segments = {}
        seg_rows = db.query(CustomerSegment).filter(
            CustomerSegment.tenant_id == tenant_id
        ).all()
        for s in seg_rows:
            segments[str(s.customer_id)] = s

        print(f"  Clientes: {len(customers)} | Com segmento: {len(segments)}")

        # ---- Carregar histórico aggregado (1 query) ----
        history_rows = db.execute(text("""
            SELECT o.customer_id,
                   oi.product_id,
                   SUM(oi.quantity) as total_qty,
                   SUM(oi.net_price) as total_value,
                   MAX(o.ordered_at) as last_ordered_at
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.tenant_id = :tid
              AND o.ordered_at >= :cutoff
              AND o.status != 'cancelled'
            GROUP BY o.customer_id, oi.product_id
        """), {"tid": tenant_id, "cutoff": cutoff}).fetchall()

        # customer_id → [{product_id, total_qty, total_value, last_ordered_at}]
        customer_history = defaultdict(list)
        for r in history_rows:
            customer_history[str(r[0])].append({
                "product_id": r[1],
                "total_qty": r[2],
                "total_value": float(r[3]),
                "last_ordered_at": r[4],
            })

        print(f"  Histórico: {len(history_rows)} linhas cliente×produto")

        # ---- Limpar current (sessão de escrita separada) ----
        from app.db.session import SessionLocal
        db_write = SessionLocal()
        try:
            db_write.query(CustomerRecommendation).filter(
                CustomerRecommendation.tenant_id == tenant_id
            ).delete(synchronize_session=False)
            db_write.commit()
        except Exception:
            db_write.rollback()
            raise
        finally:
            db_write.close()

        # ---- Processar em chunks (commit por chunk) ----
        total_recs = 0
        total_chunks = (len(customers) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for chunk_idx in range(0, len(customers), CHUNK_SIZE):
            chunk = customers[chunk_idx:chunk_idx + CHUNK_SIZE]
            chunk_num = chunk_idx // CHUNK_SIZE + 1
            current_inserts = []
            history_inserts = []

            for customer in chunk:
                cid = str(customer.id)
                seg = segments.get(cid)
                segment_name = seg.lifecycle_segment if seg else None
                history = customer_history.get(cid, [])
                store_id = preferred_stores.get(cid)

                # Decidir algoritmos por segmento
                use_personal = segment_name not in (None, "Prospect")
                use_discovery = segment_name in ("StuckInMiddle", "LoyalRunner", "LoyalStar")
                use_topsellers = True  # sempre disponível como fallback

                # ---- Pessoal ----
                personal_final = []
                if use_personal and history:
                    personal_rank = _compute_personal_rank(history, product_map, weights, today)
                    personal_final = _apply_fallback_chain(
                        personal_rank[:rank_depth], store_id, stock_dict, price_dict,
                        product_map, similars_map, offers, offer_products, offer_audiences,
                        segment_name, customer.customer_type, customer.customer_id,
                        require_offer, rank_depth,
                    )

                # ---- Descoberta ----
                discovery_final = []
                if use_discovery and history:
                    discovery_rank = _compute_discovery_rank(
                        history, product_map, similars_map, rank_depth
                    )
                    # Excluir produtos já no pessoal
                    personal_pids = {r["product_id"] for r in personal_final}
                    discovery_rank = [r for r in discovery_rank if r["product_id"] not in personal_pids]

                    discovery_final = _apply_fallback_chain(
                        discovery_rank[:rank_depth], store_id, stock_dict, price_dict,
                        product_map, similars_map, offers, offer_products, offer_audiences,
                        segment_name, customer.customer_type, customer.customer_id,
                        require_offer, rank_depth,
                    )

                # ---- Top Sellers (fallback / principal para Prospects) ----
                topsellers_final = []
                if use_topsellers and store_id:
                    ts_list = top_sellers_map.get(store_id, [])
                    # Excluir produtos já recomendados nos outros algoritmos
                    already = {r["product_id"] for r in personal_final} | {r["product_id"] for r in discovery_final}
                    ts_rank = [
                        {"product_id": ts["product_id"], "score": 1.0 - (ts["rank"] / 100)}
                        for ts in ts_list if ts["product_id"] not in already
                    ]
                    # Top sellers já são populares, aplicar só filtro de estoque (sem fallback chain)
                    for ts in ts_rank[:rank_depth]:
                        r = _try_product(
                            ts["product_id"], ts["score"], None,
                            store_id, stock_dict, price_dict, product_map,
                            offers, offer_products, offer_audiences,
                            segment_name, customer.customer_type, customer.customer_id,
                            require_offer,
                        )
                        if r:
                            topsellers_final.append(r)
                        if len(topsellers_final) >= rank_depth:
                            break

                # ---- Montar registros ----
                for algo, items in [("pessoal", personal_final), ("descoberta", discovery_final), ("topseller", topsellers_final)]:
                    for rank_pos, item in enumerate(items[:rank_depth]):
                        rec = {
                            "id": uuid_mod.uuid4(),
                            "tenant_id": tenant_id,
                            "customer_id": customer.id,
                            "store_id": store_id,
                            "algorithm": algo,
                            "rank": rank_pos + 1,
                            "product_id": item["product_id"],
                            "product_external_id": item["product_external_id"],
                            "product_name": item["product_name"],
                            "product_image_url": item.get("product_image_url"),
                            "product_category": item.get("product_category"),
                            "score": item["score"],
                            "original_product_id": item.get("original_product_id"),
                            "base_price": item.get("base_price"),
                            "has_offer": item.get("has_offer", False),
                            "offer_id": item.get("offer_id"),
                            "offer_type": item.get("offer_type"),
                            "offer_price": item.get("offer_price"),
                            "offer_name": item.get("offer_name"),
                            "offer_end_at": item.get("offer_end_at"),
                            "computed_at": now,
                            "computed_date": computed_date_str,
                        }
                        current_inserts.append(rec)
                        # History recebe cópia com computed_date como Date (não string)
                        hist_rec = dict(rec)
                        hist_rec["id"] = uuid_mod.uuid4()
                        hist_rec["computed_date"] = today
                        history_inserts.append(hist_rec)

            # Bulk insert do chunk (sessão de escrita separada, commit por chunk)
            db_chunk = SessionLocal()
            try:
                if current_inserts:
                    db_chunk.bulk_insert_mappings(CustomerRecommendation, current_inserts)
                if history_inserts:
                    _insert_history_batch(db_chunk, history_inserts, today)
                db_chunk.commit()
            except Exception:
                db_chunk.rollback()
                raise
            finally:
                db_chunk.close()

            total_recs += len(current_inserts)
            print(f"  Chunk {chunk_num}/{total_chunks}: {len(chunk)} clientes → {len(current_inserts)} recomendações")

        print(f"\nRecomendação concluída: {total_recs} registros para {len(customers)} clientes.")
        return len(customers)

    # ------------------------------------------------------------------ #
    # Real-time: re-filtra estoque sobre current
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_realtime_recommendations(
        db: Session, tenant_id: str, customer_id: str, algorithm: Optional[str] = None, limit: int = 6
    ) -> list[dict]:
        """
        Lê o rank pré-computado (current) e re-filtra por estoque atual.
        Sem fallback chain, sem Qdrant.
        """
        query = db.query(CustomerRecommendation).filter(
            CustomerRecommendation.tenant_id == tenant_id,
            CustomerRecommendation.customer_id == customer_id,
        )
        if algorithm:
            query = query.filter(CustomerRecommendation.algorithm == algorithm)

        query = query.order_by(CustomerRecommendation.algorithm, CustomerRecommendation.rank)
        rows = query.all()

        if not rows:
            return []

        # Carregar estoque atual da loja preferida
        store_id = rows[0].store_id
        stock_dict = {}
        if store_id:
            stocks = db.query(ProductStock).filter(
                ProductStock.tenant_id == tenant_id,
                ProductStock.store_id == store_id,
            ).all()
            stock_dict = {
                (str(s.store_id), s.product_id): {"quantity": s.quantity, "available": s.available}
                for s in stocks
            }

        # Filtrar por estoque, agrupar por algoritmo
        results = defaultdict(list)
        for r in rows:
            algo = r.algorithm
            if len(results[algo]) >= limit:
                continue

            # Verifica estoque (se tem loja)
            if store_id and not _has_stock(r.product_id, str(store_id), stock_dict):
                continue

            results[algo].append({
                "rank": len(results[algo]) + 1,
                "algorithm": algo,
                "product_id": r.product_id,
                "product_external_id": r.product_external_id,
                "product_name": r.product_name,
                "product_image_url": r.product_image_url,
                "product_category": r.product_category,
                "score": r.score,
                "base_price": r.base_price,
                "has_offer": r.has_offer,
                "offer_type": r.offer_type,
                "offer_price": r.offer_price,
                "offer_name": r.offer_name,
                "original_product_id": r.original_product_id,
            })

        # Flatten
        flat = []
        for algo_results in results.values():
            flat.extend(algo_results)
        return flat


# ------------------------------------------------------------------ #
# History — insert na tabela particionada
# ------------------------------------------------------------------ #

def _insert_history_batch(db: Session, records: list[dict], computed_date: date):
    """
    Insere registros na tabela particionada history.
    Cria partição do dia automaticamente se não existir.
    """
    partition_name = f"customer_recommendations_history_{computed_date.strftime('%Y%m%d')}"

    # Criar partição se não existir (idempotente)
    start = computed_date.isoformat()
    end = (computed_date + timedelta(days=1)).isoformat()
    db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {partition_name}
        PARTITION OF customer_recommendations_history
        FOR VALUES FROM ('{start}') TO ('{end}');
    """))
    db.flush()

    # Bulk insert via raw SQL para performance
    if not records:
        return

    values_parts = []
    params = {}
    for i, rec in enumerate(records):
        keys = [
            f":id_{i}", f":tenant_id_{i}", f":customer_id_{i}", f":store_id_{i}",
            f":algorithm_{i}", f":rank_{i}", f":product_id_{i}", f":product_external_id_{i}",
            f":product_name_{i}", f":product_image_url_{i}", f":product_category_{i}",
            f":score_{i}", f":original_product_id_{i}", f":base_price_{i}",
            f":has_offer_{i}", f":offer_id_{i}", f":offer_type_{i}", f":offer_price_{i}",
            f":offer_name_{i}", f":offer_end_at_{i}", f":computed_at_{i}", f":computed_date_{i}",
        ]
        values_parts.append(f"({', '.join(keys)})")
        params[f"id_{i}"] = rec["id"]
        params[f"tenant_id_{i}"] = rec["tenant_id"]
        params[f"customer_id_{i}"] = rec["customer_id"]
        params[f"store_id_{i}"] = rec.get("store_id")
        params[f"algorithm_{i}"] = rec["algorithm"]
        params[f"rank_{i}"] = rec["rank"]
        params[f"product_id_{i}"] = rec["product_id"]
        params[f"product_external_id_{i}"] = rec["product_external_id"]
        params[f"product_name_{i}"] = rec["product_name"]
        params[f"product_image_url_{i}"] = rec.get("product_image_url")
        params[f"product_category_{i}"] = None  # JSONB — simplified for now
        params[f"score_{i}"] = rec["score"]
        params[f"original_product_id_{i}"] = rec.get("original_product_id")
        params[f"base_price_{i}"] = rec.get("base_price")
        params[f"has_offer_{i}"] = rec.get("has_offer", False)
        params[f"offer_id_{i}"] = rec.get("offer_id")
        params[f"offer_type_{i}"] = rec.get("offer_type")
        params[f"offer_price_{i}"] = rec.get("offer_price")
        params[f"offer_name_{i}"] = rec.get("offer_name")
        params[f"offer_end_at_{i}"] = rec.get("offer_end_at")
        params[f"computed_at_{i}"] = rec["computed_at"]
        params[f"computed_date_{i}"] = rec["computed_date"]

    # Inserir em batches de 1000 para evitar query muito grande
    BATCH = 1000
    for batch_start in range(0, len(values_parts), BATCH):
        batch_values = values_parts[batch_start:batch_start + BATCH]
        batch_params = {}
        for i in range(batch_start, min(batch_start + BATCH, len(values_parts))):
            for key in params:
                if key.endswith(f"_{i}"):
                    batch_params[key] = params[key]

        sql = f"""
            INSERT INTO customer_recommendations_history
            (id, tenant_id, customer_id, store_id, algorithm, rank, product_id,
             product_external_id, product_name, product_image_url, product_category,
             score, original_product_id, base_price, has_offer, offer_id, offer_type,
             offer_price, offer_name, offer_end_at, computed_at, computed_date)
            VALUES {', '.join(batch_values)}
        """
        db.execute(text(sql), batch_params)


# ------------------------------------------------------------------ #
# Limpeza de histórico
# ------------------------------------------------------------------ #

def cleanup_history(db: Session, retention_days: int = 30):
    """Remove partições mais antigas que retention_days."""
    cutoff = date.today() - timedelta(days=retention_days)
    # Lista partições da tabela
    result = db.execute(text("""
        SELECT inhrelid::regclass::text AS partition_name
        FROM pg_inherits
        WHERE inhparent = 'customer_recommendations_history'::regclass
        ORDER BY partition_name
    """)).fetchall()

    dropped = 0
    for row in result:
        pname = row[0]
        # Extrair data do nome: customer_recommendations_history_20260319
        try:
            date_str = pname.split("_")[-1]
            pdate = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
            if pdate < cutoff:
                db.execute(text(f"DROP TABLE IF EXISTS {pname}"))
                dropped += 1
                print(f"  Partição removida: {pname}")
        except (ValueError, IndexError):
            continue

    if dropped:
        db.commit()
        print(f"Limpeza: {dropped} partições removidas (> {retention_days} dias).")
    else:
        print(f"Limpeza: nenhuma partição para remover.")
