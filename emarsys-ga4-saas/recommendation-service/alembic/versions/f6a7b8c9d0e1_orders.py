"""orders: Order + OrderItem

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'orders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('order_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_id', UUID(as_uuid=True),
                  sa.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('channel_id', UUID(as_uuid=True),
                  sa.ForeignKey('channels.id', ondelete='SET NULL'), nullable=True),
        sa.Column('store_id', UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='delivered'),
        sa.Column('gross_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('discount_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('tax_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('net_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('ordered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'order_id', name='uq_order_tenant_orderid'),
    )

    op.create_table(
        'order_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('order_id', UUID(as_uuid=True),
                  sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', sa.String(),
                  sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('product_external_id', sa.String(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('discount_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('net_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('is_promo', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade():
    op.drop_table('order_items')
    op.drop_table('orders')
