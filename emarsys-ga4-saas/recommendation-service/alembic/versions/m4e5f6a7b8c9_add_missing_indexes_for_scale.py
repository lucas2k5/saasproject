"""Add missing composite and FK indexes for scale

Revision ID: m4e5f6a7b8c9
Revises: l3d4e5f6a7b8
Create Date: 2026-03-19
"""
from alembic import op

revision = 'm4e5f6a7b8c9'
down_revision = 'l3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # Composite indexes for hot query paths
    # ------------------------------------------------------------------ #

    # orders: idx_orders_tenant_customer_date already exists (a1b2c3d4e5f6)
    #         with [tenant_id, customer_id, ordered_at DESC] — SKIP

    op.create_index('idx_prices_tenant_store_product', 'product_prices',
                    ['tenant_id', 'store_id', 'product_id'])

    op.create_index('idx_stock_tenant_store_product', 'product_stock',
                    ['tenant_id', 'store_id', 'product_id'])

    # customer_recommendations_current: idx_recrec_tenant_customer_algo
    # already exists (h9c0d1e2f3a4) with same columns — SKIP

    op.create_index('idx_offers_tenant_dates', 'offers',
                    ['tenant_id', 'start_at', 'end_at'])

    # product_similars: idx_prodsim_tenant_product exists with [tenant_id, product_id].
    # Adding a wider index that also covers rank lookups.
    op.create_index('idx_prodsim_tenant_product_rank', 'product_similars',
                    ['tenant_id', 'product_id', 'rank'])

    op.create_index('idx_topseller_tenant_store_rank', 'store_top_sellers',
                    ['tenant_id', 'store_id', 'rank'])

    op.create_index('idx_cos_tenant_customer', 'customer_order_summary',
                    ['tenant_id', 'customer_id'])

    op.create_index('idx_cs_tenant_customer', 'customer_segments',
                    ['tenant_id', 'customer_id'])

    op.create_index('idx_order_items_order_product', 'order_items',
                    ['order_id', 'product_id'])

    # ------------------------------------------------------------------ #
    # FK indexes (prevent slow CASCADE deletes and JOIN scans)
    # ------------------------------------------------------------------ #

    op.create_index('idx_offer_products_product', 'offer_products',
                    ['product_id'])

    op.create_index('idx_topseller_product', 'store_top_sellers',
                    ['product_id'])

    op.create_index('idx_prodsim_similar', 'product_similars',
                    ['similar_product_id'])

    op.create_index('idx_recrec_store', 'customer_recommendations_current',
                    ['store_id'])

    op.create_index('idx_orders_channel', 'orders',
                    ['channel_id'])

    op.create_index('idx_orders_store', 'orders',
                    ['store_id'])


def downgrade() -> None:
    # FK indexes
    op.drop_index('idx_orders_store', table_name='orders')
    op.drop_index('idx_orders_channel', table_name='orders')
    op.drop_index('idx_recrec_store', table_name='customer_recommendations_current')
    op.drop_index('idx_prodsim_similar', table_name='product_similars')
    op.drop_index('idx_topseller_product', table_name='store_top_sellers')
    op.drop_index('idx_offer_products_product', table_name='offer_products')

    # Composite indexes
    op.drop_index('idx_order_items_order_product', table_name='order_items')
    op.drop_index('idx_cs_tenant_customer', table_name='customer_segments')
    op.drop_index('idx_cos_tenant_customer', table_name='customer_order_summary')
    op.drop_index('idx_topseller_tenant_store_rank', table_name='store_top_sellers')
    op.drop_index('idx_prodsim_tenant_product_rank', table_name='product_similars')
    op.drop_index('idx_offers_tenant_dates', table_name='offers')
    op.drop_index('idx_stock_tenant_store_product', table_name='product_stock')
    op.drop_index('idx_prices_tenant_store_product', table_name='product_prices')
