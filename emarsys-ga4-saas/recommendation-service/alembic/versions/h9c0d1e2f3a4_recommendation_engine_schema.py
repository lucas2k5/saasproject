"""recommendation engine schema — Product sazonalidade, TenantConfig rec fields,
ProductSimilars, StoreTopSellers, CustomerRecommendation (current + history particionada),
RecommendationJob

Revision ID: h9c0d1e2f3a4
Revises: g8b9c0d1e2f3
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'h9c0d1e2f3a4'
down_revision = 'g8b9c0d1e2f3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # Product — colunas de sazonalidade
    # ------------------------------------------------------------------ #
    op.add_column('products', sa.Column('purchase_cycle_type', sa.String(), nullable=True))
    op.add_column('products', sa.Column('purchase_cycle_days', sa.Integer(), nullable=True))

    # ------------------------------------------------------------------ #
    # TenantConfig — campos do motor de recomendação
    # ------------------------------------------------------------------ #
    op.add_column('tenant_configs', sa.Column('rec_lookback_months', sa.Integer(), nullable=True, server_default='12'))
    op.add_column('tenant_configs', sa.Column('rec_weight_frequency', sa.Float(), nullable=True, server_default='0.5'))
    op.add_column('tenant_configs', sa.Column('rec_weight_value', sa.Float(), nullable=True, server_default='0.3'))
    op.add_column('tenant_configs', sa.Column('rec_weight_recency', sa.Float(), nullable=True, server_default='0.2'))
    op.add_column('tenant_configs', sa.Column('rec_require_offer', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('tenant_configs', sa.Column('rec_results_per_algo', sa.Integer(), nullable=True, server_default='6'))
    op.add_column('tenant_configs', sa.Column('rec_rank_depth', sa.Integer(), nullable=True, server_default='30'))
    op.add_column('tenant_configs', sa.Column('rec_topsellers_window_days', sa.Integer(), nullable=True, server_default='90'))

    # ------------------------------------------------------------------ #
    # ProductSimilars
    # ------------------------------------------------------------------ #
    op.create_table(
        'product_similars',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('similar_product_id', sa.String(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('price_ratio', sa.Float(), nullable=True),
        sa.UniqueConstraint('tenant_id', 'product_id', 'similar_product_id',
                            name='uq_prodsim_tenant_product_similar'),
    )
    op.create_index('idx_prodsim_tenant_product', 'product_similars', ['tenant_id', 'product_id'])

    # ------------------------------------------------------------------ #
    # StoreTopSellers
    # ------------------------------------------------------------------ #
    op.create_table(
        'store_top_sellers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('store_id', UUID(as_uuid=True), sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_external_id', sa.String(), nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('product_image_url', sa.String(), nullable=True),
        sa.Column('total_qty_sold', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'store_id', 'rank',
                            name='uq_topseller_tenant_store_rank'),
    )
    op.create_index('idx_topseller_tenant_store', 'store_top_sellers', ['tenant_id', 'store_id'])

    # ------------------------------------------------------------------ #
    # CustomerRecommendation — current (não particionada)
    # ------------------------------------------------------------------ #
    op.create_table(
        'customer_recommendations_current',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('store_id', UUID(as_uuid=True), sa.ForeignKey('stores.id', ondelete='SET NULL'), nullable=True),
        sa.Column('algorithm', sa.String(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_external_id', sa.String(), nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('product_image_url', sa.String(), nullable=True),
        sa.Column('product_category', sa.JSON(), nullable=True),
        sa.Column('score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('original_product_id', sa.String(), nullable=True),
        sa.Column('base_price', sa.Float(), nullable=True),
        sa.Column('has_offer', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('offer_id', UUID(as_uuid=True), nullable=True),
        sa.Column('offer_type', sa.String(), nullable=True),
        sa.Column('offer_price', sa.Float(), nullable=True),
        sa.Column('offer_name', sa.String(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('computed_date', sa.String(), nullable=False),
        sa.UniqueConstraint('tenant_id', 'customer_id', 'algorithm', 'rank',
                            name='uq_recrec_tenant_cust_algo_rank'),
    )
    op.create_index('idx_recrec_tenant_customer', 'customer_recommendations_current',
                    ['tenant_id', 'customer_id'])
    op.create_index('idx_recrec_tenant_customer_algo', 'customer_recommendations_current',
                    ['tenant_id', 'customer_id', 'algorithm'])

    # ------------------------------------------------------------------ #
    # CustomerRecommendation — history (particionada por computed_date)
    # ------------------------------------------------------------------ #
    op.execute("""
        CREATE TABLE customer_recommendations_history (
            id UUID NOT NULL,
            tenant_id VARCHAR NOT NULL,
            customer_id UUID NOT NULL,
            store_id UUID,
            algorithm VARCHAR NOT NULL,
            rank INTEGER NOT NULL,
            product_id VARCHAR NOT NULL,
            product_external_id VARCHAR NOT NULL,
            product_name VARCHAR NOT NULL,
            product_image_url VARCHAR,
            product_category JSONB,
            score FLOAT NOT NULL DEFAULT 0,
            original_product_id VARCHAR,
            base_price FLOAT,
            has_offer BOOLEAN NOT NULL DEFAULT false,
            offer_id UUID,
            offer_type VARCHAR,
            offer_price FLOAT,
            offer_name VARCHAR,
            computed_at TIMESTAMPTZ DEFAULT now(),
            computed_date DATE NOT NULL,
            PRIMARY KEY (id, computed_date)
        ) PARTITION BY RANGE (computed_date);
    """)
    op.execute("""
        CREATE INDEX idx_rechist_tenant_customer_date
        ON customer_recommendations_history (tenant_id, customer_id, computed_date);
    """)
    op.execute("""
        CREATE INDEX idx_rechist_computed_date
        ON customer_recommendations_history (computed_date);
    """)

    # ------------------------------------------------------------------ #
    # RecommendationJob
    # ------------------------------------------------------------------ #
    op.create_table(
        'recommendation_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('triggered_by', sa.String(), nullable=False, server_default='scheduler'),
        sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('customers_processed', sa.Integer(), nullable=True),
        sa.Column('error_msg', sa.Text(), nullable=True),
    )
    op.create_index('idx_recjob_tenant', 'recommendation_jobs', ['tenant_id'])
    op.execute("""
        CREATE UNIQUE INDEX uq_recjob_tenant_active
        ON recommendation_jobs (tenant_id)
        WHERE status IN ('queued', 'running');
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS customer_recommendations_history CASCADE")
    op.drop_table('customer_recommendations_current')
    op.drop_table('recommendation_jobs')
    op.drop_table('store_top_sellers')
    op.drop_table('product_similars')

    op.drop_column('tenant_configs', 'rec_topsellers_window_days')
    op.drop_column('tenant_configs', 'rec_rank_depth')
    op.drop_column('tenant_configs', 'rec_results_per_algo')
    op.drop_column('tenant_configs', 'rec_require_offer')
    op.drop_column('tenant_configs', 'rec_weight_recency')
    op.drop_column('tenant_configs', 'rec_weight_value')
    op.drop_column('tenant_configs', 'rec_weight_frequency')
    op.drop_column('tenant_configs', 'rec_lookback_months')

    op.drop_column('products', 'purchase_cycle_days')
    op.drop_column('products', 'purchase_cycle_type')
