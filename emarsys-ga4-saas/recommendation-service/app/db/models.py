from sqlalchemy import (
    Column, Integer, String, Float, JSON, ForeignKey,
    DateTime, Boolean, UniqueConstraint, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# ------------------------------------------------------------------ #
# Tipos de oferta — fonte única de verdade para todo o sistema
# ------------------------------------------------------------------ #
VALID_OFFER_TYPES = {
    "DIRECT_DISCOUNT",    # Desconto direto no preço (ex: 20% OFF, R$5 OFF)
    "TAKE_X_PAY_Y",       # Leve X pague Y do mesmo produto (ex: Leve 3 Pague 2)
    "BUY_X_GET_Y",        # Compre X do mesmo produto ganhe Y do mesmo (ex: Compre 2 Ganhe 1)
    "BUY_X_GET_PRODUCT",  # Compre X do produto A ganhe Y do produto B (ex: Compre cerveja ganhe copo)
    "PROGRESSIVE",        # Desconto progressivo por volume (ex: 10% na 2a, 20% na 3a)
    "COMBO",              # Kit/combo de produtos complementares com preço fechado
    "CASHBACK",           # Devolução de % do valor em crédito/carteira
}

# Inclui __GENERIC__ para uso em templates de conteúdo (fallback quando mix de tipos)
# __FOOTER__ = snippet de rodapé/disclaimer (apenas email)
VALID_TEMPLATE_OFFER_TYPES = VALID_OFFER_TYPES | {"__GENERIC__", "__FOOTER__"}


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    company_name = Column(String)
    tenant_id = Column(String, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApiKey(Base):
    """API Keys para acesso programático. Cada key pertence a um tenant."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)           # Ex: "ERP Produção"
    key_prefix = Column(String, nullable=False)      # Primeiros 8 chars (sk-xxxx) para identificação
    key_hash = Column(String, nullable=False)         # SHA-256 da key completa
    scopes = Column(JSON, nullable=False)             # Lista de scopes autorizados
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # null = nunca expira
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    path = Column(String, index=True)
    name = Column(String)
    level = Column(Integer)
    parent_path = Column(String, index=True, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'path', name='uq_category_tenant_path'),
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True)
    external_id = Column(String, index=True)
    name = Column(String)
    price = Column(Float, nullable=True)
    description = Column(String, nullable=True)
    enriched_text = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    category = Column(JSON)
    attributes = Column(JSON)
    is_active = Column(Boolean, default=True, nullable=False)
    data_hash = Column(String, nullable=True)
    purchase_cycle_type = Column(String, nullable=True)    # consumivel | semi_duravel | duravel | sazonal
    purchase_cycle_days = Column(Integer, nullable=True)   # ciclo estimado de recompra em dias
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'external_id', name='uq_product_tenant_extid'),
    )


class TenantConfig(Base):
    __tablename__ = "tenant_configs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True)

    # IA & Recomendações
    price_threshold_low = Column(Float, default=0.9)
    price_threshold_high = Column(Float, default=1.1)
    similarity_threshold = Column(Float, default=0.7)
    recommendation_limit = Column(Integer, default=10)
    recommendation_category_level = Column(Integer, default=0)

    # Segmento: OneTime
    onetime_days_as_customer_min = Column(Integer, default=60)
    onetime_p_alive_max = Column(Float, default=0.3)

    # Segmento: Leaver (churn confirmado)
    leaver_recency_min = Column(Integer, default=180)
    leaver_p_alive_max = Column(Float, default=0.15)
    leaver_invoices_min = Column(Integer, default=3)

    # Segmento: NonEngaged
    nonengaged_p_alive_max = Column(Float, default=0.2)
    nonengaged_recency_min = Column(Integer, default=180)
    nonengaged_velocity_trend_max = Column(Float, default=0.3)

    # Segmento: LoyalStar
    loyalstar_regularity_max = Column(Float, default=0.6)
    loyalstar_velocity_trend_min = Column(Float, default=0.9)
    loyalstar_ticket_trend_min = Column(Float, default=0.9)
    loyalstar_category_diversity_min = Column(Integer, default=3)
    loyalstar_p_alive_min = Column(Float, default=0.7)

    # Segmento: LoyalRunner
    loyalrunner_regularity_max = Column(Float, default=0.8)
    loyalrunner_velocity_trend_min = Column(Float, default=0.9)
    loyalrunner_p_alive_min = Column(Float, default=0.5)

    # Motor de Recomendação Personalizada
    rec_lookback_months = Column(Integer, default=12)
    rec_weight_frequency = Column(Float, default=0.5)
    rec_weight_value = Column(Float, default=0.3)
    rec_weight_recency = Column(Float, default=0.2)
    rec_require_offer = Column(Boolean, default=True)
    rec_results_per_algo = Column(Integer, default=6)
    rec_rank_depth = Column(Integer, default=30)
    rec_topsellers_window_days = Column(Integer, default=90)

    # S3 Storage (tenant-owned)
    s3_bucket_name = Column(String, nullable=True)
    s3_access_key = Column(String, nullable=True)
    s3_secret_key = Column(String, nullable=True)
    s3_region = Column(String, default='us-east-1')
    s3_presigned_expiration_hours = Column(Integer, default=168)

    # Limites de conteúdo por canal
    content_max_products_email = Column(Integer, default=6)
    content_max_products_whatsapp = Column(Integer, default=3)
    content_max_products_push = Column(Integer, default=1)

    # Sugestões automáticas (calculadas pelo job de lifecycle)
    config_suggestions = Column(JSON, nullable=True)
    suggested_at = Column(DateTime(timezone=True), nullable=True)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    customer_id = Column(String, nullable=False, index=True)       # ID no ERP
    customer_add_id = Column(String, nullable=True, index=True)    # ID no CRM
    name = Column(String, nullable=False)
    document = Column(String, nullable=True)
    customer_type = Column(String, nullable=True)
    source_created_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'customer_id', name='uq_customer_tenant_customerid'),
    )


class Channel(Base):
    __tablename__ = "channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    channel_id = Column(String, nullable=False, index=True)   # ID externo
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)                     # string livre (ex: web, app, loja_fisica)
    store_mode = Column(String, nullable=False, default='single')  # single | multi
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'channel_id', name='uq_channel_tenant_channelid'),
    )


class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    store_id = Column(String, nullable=False, index=True)    # ID externo
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'store_id', name='uq_store_tenant_storeid'),
    )


class ChannelStore(Base):
    """Vínculo entre canal e loja (apenas para canais com store_mode=multi)."""
    __tablename__ = "channel_stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey('channels.id', ondelete='CASCADE'), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        UniqueConstraint('channel_id', 'store_id', name='uq_channelstore_channel_store'),
    )


class ProductPrice(Base):
    __tablename__ = "product_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    product_id = Column(String, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey('channels.id', ondelete='CASCADE'), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='SET NULL'), nullable=True, index=True)
    price = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'product_id', 'channel_id', 'store_id',
                         name='uq_price_product_channel_store'),
    )


class ProductStock(Base):
    __tablename__ = "product_stock"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    product_id = Column(String, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey('channels.id', ondelete='CASCADE'), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='SET NULL'), nullable=True, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    available = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'product_id', 'channel_id', 'store_id',
                         name='uq_stock_product_channel_store'),
    )


class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    offer_id = Column(String, nullable=False, index=True)        # ID externo
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)                        # Ver VALID_OFFER_TYPES
    mechanic_params = Column(JSON, nullable=False, default=dict)
    channel_ids = Column(JSON, nullable=True)                    # null = todos os canais
    store_ids = Column(JSON, nullable=True)                      # null = todas as lojas
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)     # obrigatório
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'offer_id', name='uq_offer_tenant_offerid'),
    )


class OfferProduct(Base):
    """Produtos envolvidos na oferta — trigger (produto em promoção) ou reward (brinde/desconto)."""
    __tablename__ = "offer_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey('offers.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = Column(String, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    role = Column(String, nullable=False, default='TRIGGER')     # TRIGGER | REWARD | COMBO_MEMBER

    __table_args__ = (
        UniqueConstraint('offer_id', 'product_id', 'role', name='uq_offerproduct_offer_product_role'),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    order_id = Column(String, nullable=False, index=True)          # ID externo (ERP)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey('channels.id', ondelete='SET NULL'), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='SET NULL'), nullable=True)
    status = Column(String, nullable=False, default='delivered')
    gross_value = Column(Float, nullable=False, default=0)
    discount_value = Column(Float, nullable=False, default=0)
    tax_value = Column(Float, nullable=False, default=0)
    net_value = Column(Float, nullable=False, default=0)
    ordered_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'order_id', name='uq_order_tenant_orderid'),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = Column(String, ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True)
    product_external_id = Column(String, nullable=False)           # SKU original — preservado mesmo se produto for deletado
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, nullable=False, default=0)
    tax_amount = Column(Float, nullable=False, default=0)
    net_price = Column(Float, nullable=False, default=0)
    is_promo = Column(Boolean, nullable=False, default=False)


class OfferAudience(Base):
    """Segmentação da oferta — a quem ela se aplica."""
    __tablename__ = "offer_audiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey('offers.id', ondelete='CASCADE'), nullable=False, index=True)
    audience_type = Column(String, nullable=False)               # ALL | CUSTOMER_IDS | CUSTOMER_TYPE | LIFECYCLE_SEGMENT
    audience_value = Column(JSON, nullable=True)                 # lista de refs (customer_id OU customer_add_id), tipos ou segmentos


# ------------------------------------------------------------------ #
# Customer Lifecycle
# ------------------------------------------------------------------ #

class CustomerOrderSummary(Base):
    """Resumo incremental de pedidos por cliente. Atualizado no POST /orders/batch."""
    __tablename__ = "customer_order_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)

    total_orders = Column(Integer, nullable=False, default=0)
    total_value = Column(Float, nullable=False, default=0)
    first_order_at = Column(DateTime(timezone=True), nullable=True)
    last_order_at = Column(DateTime(timezone=True), nullable=True)

    # Janelas 90 dias (atualizadas no batch, recalculadas no job a partir de recent_order_dates)
    orders_90d = Column(Integer, nullable=False, default=0)
    value_90d = Column(Float, nullable=False, default=0)
    orders_prev_90d = Column(Integer, nullable=False, default=0)
    value_prev_90d = Column(Float, nullable=False, default=0)

    # Últimas 30 datas ISO para cálculo de CoV e janelagem no job
    recent_order_dates = Column(JSON, nullable=True)

    # Itens
    total_items = Column(Integer, nullable=False, default=0)
    distinct_skus = Column(Integer, nullable=False, default=0)
    repeat_skus = Column(Integer, nullable=False, default=0)       # SKUs comprados >1 vez
    promo_items = Column(Integer, nullable=False, default=0)       # itens com discount_amount > 0
    returned_orders = Column(Integer, nullable=False, default=0)   # pedidos status='returned'

    # Preferências (JSON)
    top_skus = Column(JSON, nullable=True)           # {"SKU1": 15, "SKU2": 8, ...} top 10
    top_categories = Column(JSON, nullable=True)     # {"categoria": count}
    channel_counts = Column(JSON, nullable=True)     # {"web": 45, "loja_fisica": 12}

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'customer_id', name='uq_cos_tenant_customer'),
    )


class CustomerSegment(Base):
    """Indicadores de ciclo de vida + segmento. Calculado pelo job diário."""
    __tablename__ = "customer_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)

    # RFM
    recency_days = Column(Integer, nullable=True)
    number_of_invoices = Column(Integer, nullable=True)
    monetary_total = Column(Float, nullable=True)
    avg_ticket = Column(Float, nullable=True)

    # Tendência
    ticket_trend = Column(Float, nullable=True)              # avg_ticket_90d / avg_ticket_prev_90d
    purchase_velocity_trend = Column(Float, nullable=True)   # orders_90d / orders_prev_90d

    # Cadência
    avg_days_between = Column(Float, nullable=True)
    purchase_regularity = Column(Float, nullable=True)       # CoV: std/avg

    # Variedade
    distinct_articles = Column(Integer, nullable=True)
    category_diversity = Column(Integer, nullable=True)

    # Comportamento
    promo_ratio = Column(Float, nullable=True)
    return_rate = Column(Float, nullable=True)
    repeat_product_ratio = Column(Float, nullable=True)

    # Preferências
    top_5_products = Column(JSON, nullable=True)
    top_5_categories = Column(JSON, nullable=True)
    preferred_channel = Column(String, nullable=True)
    days_as_customer = Column(Integer, nullable=True)

    # BG/NBD
    p_alive = Column(Float, nullable=True)                   # probabilidade de estar "vivo" (0-1)
    expected_transactions = Column(Float, nullable=True)     # transações esperadas nos próximos 90d

    # Segmento (double-buffer)
    lifecycle_segment = Column(String, nullable=True)        # visível pela API
    lifecycle_segment_next = Column(String, nullable=True)   # buffer do job, swapado no final

    computed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'customer_id', name='uq_cs_tenant_customer'),
    )


# ------------------------------------------------------------------ #
# Motor de Recomendação Personalizada
# ------------------------------------------------------------------ #

class ProductSimilar(Base):
    """Top N produtos similares pré-computados via Qdrant. Atualizado no reindex do catálogo."""
    __tablename__ = "product_similars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    product_id = Column(String, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    similar_product_id = Column(String, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)           # similaridade (0-1)
    price_ratio = Column(Float, nullable=True)      # preço_similar / preço_original

    __table_args__ = (
        UniqueConstraint('tenant_id', 'product_id', 'similar_product_id',
                         name='uq_prodsim_tenant_product_similar'),
    )


class StoreTopSeller(Base):
    """Top sellers por loja. Recalculado diariamente pelo job noturno."""
    __tablename__ = "store_top_sellers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='CASCADE'), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    product_id = Column(String, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    product_external_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    product_image_url = Column(String, nullable=True)
    total_qty_sold = Column(Integer, nullable=False, default=0)
    total_value = Column(Float, nullable=False, default=0)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'store_id', 'rank',
                         name='uq_topseller_tenant_store_rank'),
    )


class CustomerRecommendation(Base):
    """Rank de recomendações pré-computado (tabela current — acesso rápido para marketing e real-time)."""
    __tablename__ = "customer_recommendations_current"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='SET NULL'), nullable=True)
    algorithm = Column(String, nullable=False)          # pessoal | descoberta | topseller
    rank = Column(Integer, nullable=False)              # posição 1-30

    # Produto recomendado
    product_id = Column(String, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    product_external_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    product_image_url = Column(String, nullable=True)
    product_category = Column(JSON, nullable=True)
    score = Column(Float, nullable=False, default=0)

    # Substituição por similar (fallback chain)
    original_product_id = Column(String, nullable=True)  # NULL se não houve substituição

    # Preço e oferta
    base_price = Column(Float, nullable=True)
    has_offer = Column(Boolean, nullable=False, default=False)
    offer_id = Column(UUID(as_uuid=True), nullable=True)
    offer_type = Column(String, nullable=True)
    offer_price = Column(Float, nullable=True)
    offer_name = Column(String, nullable=True)
    offer_end_at = Column(DateTime(timezone=True), nullable=True)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    computed_date = Column(String, nullable=False)       # YYYY-MM-DD para referência

    __table_args__ = (
        UniqueConstraint('tenant_id', 'customer_id', 'algorithm', 'rank',
                         name='uq_recrec_tenant_cust_algo_rank'),
    )


class RecommendationJob(Base):
    """Fila de jobs para cálculo de recomendações. Mesmo padrão do SegmentJob."""
    __tablename__ = "recommendation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False, default='queued')   # queued | running | done | failed
    priority = Column(Integer, nullable=False, default=1)       # 0=urgente (manual), 1=normal
    triggered_by = Column(String, nullable=False, default='scheduler')  # scheduler | api | api_inline
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    customers_processed = Column(Integer, nullable=True)
    error_msg = Column(Text, nullable=True)


class SegmentJob(Base):
    """Fila de jobs para cálculo de segmentos. Processada por workers via SKIP LOCKED."""
    __tablename__ = "segment_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False, default='queued')   # queued | running | done | failed
    priority = Column(Integer, nullable=False, default=1)       # 0=urgente (manual), 1=normal
    triggered_by = Column(String, nullable=False, default='scheduler')  # scheduler | api
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    customers_processed = Column(Integer, nullable=True)
    error_msg = Column(Text, nullable=True)


# ------------------------------------------------------------------ #
# Motor de Conteúdo Personalizado
# ------------------------------------------------------------------ #

class ContentTemplate(Base):
    """Templates Jinja2 por canal e tipo de oferta. Tenant configura via CRUD."""
    __tablename__ = "content_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    channel = Column(String, nullable=False)        # email | whatsapp | push
    offer_type = Column(String, nullable=False)      # __GENERIC__ | DIRECT_DISCOUNT | TAKE_X_PAY_Y | ...
    name = Column(String, nullable=False)
    body = Column(Text, nullable=False)              # HTML Jinja2 (email/push) ou JSON config (whatsapp)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'channel', 'offer_type',
                         name='uq_contenttemplate_tenant_channel_offertype'),
    )


class ContentEmail(Base):
    """Email HTML renderizado por cliente + algoritmo. Gerado pelo content job."""
    __tablename__ = "content_email"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    algorithm = Column(String, nullable=False)  # pessoal | descoberta | topseller
    customer_external_id = Column(String, nullable=False)
    customer_add_id = Column(String, nullable=True)
    customer_name = Column(String, nullable=False)
    html_body = Column(Text, nullable=False)
    products_count = Column(Integer, nullable=False, default=0)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'customer_id', 'algorithm',
                         name='uq_contentemail_tenant_customer_algo'),
    )


class ContentWhatsapp(Base):
    """PNG para WhatsApp por cliente + algoritmo. Gerado via Pillow, hospedado no S3 do tenant."""
    __tablename__ = "content_whatsapp"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    algorithm = Column(String, nullable=False)  # pessoal | descoberta | topseller
    customer_external_id = Column(String, nullable=False)
    customer_add_id = Column(String, nullable=True)
    customer_name = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    image_s3_key = Column(String, nullable=False)
    products_count = Column(Integer, nullable=False, default=0)
    presigned_expires_at = Column(DateTime(timezone=True), nullable=False)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'customer_id', 'algorithm',
                         name='uq_contentwhatsapp_tenant_customer_algo'),
    )


class ContentPush(Base):
    """Push notification payload por cliente + algoritmo. Título + corpo + imagem (reusa S3)."""
    __tablename__ = "content_push"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    algorithm = Column(String, nullable=False)  # pessoal | descoberta | topseller
    customer_external_id = Column(String, nullable=False)
    customer_add_id = Column(String, nullable=True)
    customer_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    image_s3_key = Column(String, nullable=True)
    presigned_expires_at = Column(DateTime(timezone=True), nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'customer_id', 'algorithm',
                         name='uq_contentpush_tenant_customer_algo'),
    )


class ContentJob(Base):
    """Fila de jobs para geração de conteúdo. Disparado automaticamente após recomendação."""
    __tablename__ = "content_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False, default='queued')   # queued | running | done | failed
    priority = Column(Integer, nullable=False, default=1)
    triggered_by = Column(String, nullable=False, default='auto')
    channels = Column(JSON, nullable=True)                       # null = todos os canais
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    customers_processed = Column(Integer, nullable=True)
    emails_generated = Column(Integer, nullable=True)
    images_generated = Column(Integer, nullable=True)
    push_generated = Column(Integer, nullable=True)
    error_msg = Column(Text, nullable=True)
