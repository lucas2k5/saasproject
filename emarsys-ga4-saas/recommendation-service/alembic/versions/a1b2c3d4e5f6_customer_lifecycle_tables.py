"""Customer lifecycle: customer_order_summary + customer_segments + segment_jobs + indices

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-03-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # customer_order_summary
    # ------------------------------------------------------------------ #
    op.create_table(
        'customer_order_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('first_order_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_order_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('orders_90d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('value_90d', sa.Float(), nullable=False, server_default='0'),
        sa.Column('orders_prev_90d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('value_prev_90d', sa.Float(), nullable=False, server_default='0'),
        sa.Column('recent_order_dates', sa.JSON(), nullable=True),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('distinct_skus', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('repeat_skus', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('promo_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('returned_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('top_skus', sa.JSON(), nullable=True),
        sa.Column('top_categories', sa.JSON(), nullable=True),
        sa.Column('channel_counts', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'customer_id', name='uq_cos_tenant_customer'),
    )

    # ------------------------------------------------------------------ #
    # customer_segments
    # ------------------------------------------------------------------ #
    op.create_table(
        'customer_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        # RFM
        sa.Column('recency_days', sa.Integer(), nullable=True),
        sa.Column('number_of_invoices', sa.Integer(), nullable=True),
        sa.Column('monetary_total', sa.Float(), nullable=True),
        sa.Column('avg_ticket', sa.Float(), nullable=True),
        # Tendência
        sa.Column('ticket_trend', sa.Float(), nullable=True),
        sa.Column('purchase_velocity_trend', sa.Float(), nullable=True),
        # Cadência
        sa.Column('avg_days_between', sa.Float(), nullable=True),
        sa.Column('purchase_regularity', sa.Float(), nullable=True),
        # Variedade
        sa.Column('distinct_articles', sa.Integer(), nullable=True),
        sa.Column('category_diversity', sa.Integer(), nullable=True),
        # Comportamento
        sa.Column('promo_ratio', sa.Float(), nullable=True),
        sa.Column('return_rate', sa.Float(), nullable=True),
        sa.Column('repeat_product_ratio', sa.Float(), nullable=True),
        # Preferências
        sa.Column('top_5_products', sa.JSON(), nullable=True),
        sa.Column('top_5_categories', sa.JSON(), nullable=True),
        sa.Column('preferred_channel', sa.String(), nullable=True),
        sa.Column('days_as_customer', sa.Integer(), nullable=True),
        # Segmento (double-buffer)
        sa.Column('lifecycle_segment', sa.String(), nullable=True),
        sa.Column('lifecycle_segment_next', sa.String(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'customer_id', name='uq_cs_tenant_customer'),
    )

    # ------------------------------------------------------------------ #
    # segment_jobs
    # ------------------------------------------------------------------ #
    op.create_table(
        'segment_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('triggered_by', sa.String(), nullable=False, server_default='scheduler'),
        sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('customers_processed', sa.Integer(), nullable=True),
        sa.Column('error_msg', sa.Text(), nullable=True),
    )

    # ------------------------------------------------------------------ #
    # Índices adicionais
    # ------------------------------------------------------------------ #
    op.create_index('idx_orders_tenant_customer_date', 'orders',
                    ['tenant_id', 'customer_id', sa.text('ordered_at DESC')])
    op.create_index('idx_order_items_order', 'order_items', ['order_id'])
    op.create_index('idx_cos_tenant', 'customer_order_summary', ['tenant_id'])
    op.create_index('idx_cs_tenant_segment', 'customer_segments',
                    ['tenant_id', 'lifecycle_segment'])
    # Partial index para fila de jobs
    op.execute("""
        CREATE INDEX idx_sj_status_queue
        ON segment_jobs (status, queued_at)
        WHERE status IN ('queued', 'running')
    """)
    # Partial unique: max 1 job queued/running por tenant
    op.execute("""
        CREATE UNIQUE INDEX uq_sj_tenant_active
        ON segment_jobs (tenant_id)
        WHERE status IN ('queued', 'running')
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_sj_tenant_active")
    op.execute("DROP INDEX IF EXISTS idx_sj_status_queue")
    op.drop_index('idx_cs_tenant_segment', 'customer_segments')
    op.drop_index('idx_cos_tenant', 'customer_order_summary')
    op.drop_index('idx_order_items_order', 'order_items')
    op.drop_index('idx_orders_tenant_customer_date', 'orders')
    op.drop_table('segment_jobs')
    op.drop_table('customer_segments')
    op.drop_table('customer_order_summary')
