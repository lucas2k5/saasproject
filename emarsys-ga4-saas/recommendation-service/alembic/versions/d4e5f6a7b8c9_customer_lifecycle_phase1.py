"""Customer lifecycle phase 1: products update + customers, channels, stores, prices, stock

Revision ID: d4e5f6a7b8c9
Revises: c3de4f778899
Create Date: 2026-03-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3de4f778899'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # products — novos campos
    # ------------------------------------------------------------------ #
    op.add_column('products', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('products', sa.Column('data_hash', sa.String(), nullable=True))
    op.add_column('products', sa.Column('updated_at', sa.DateTime(timezone=True),
                                        server_default=sa.func.now(), nullable=True))

    # ------------------------------------------------------------------ #
    # customers
    # ------------------------------------------------------------------ #
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_add_id', sa.String(), nullable=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('document', sa.String(), nullable=True),
        sa.Column('customer_type', sa.String(), nullable=True),
        sa.Column('source_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'customer_id', name='uq_customer_tenant_customerid'),
    )

    # ------------------------------------------------------------------ #
    # channels
    # ------------------------------------------------------------------ #
    op.create_table(
        'channels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('channel_id', sa.String(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('store_mode', sa.String(), nullable=False, server_default='single'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'channel_id', name='uq_channel_tenant_channelid'),
    )

    # ------------------------------------------------------------------ #
    # stores
    # ------------------------------------------------------------------ #
    op.create_table(
        'stores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('store_id', sa.String(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'store_id', name='uq_store_tenant_storeid'),
    )

    # ------------------------------------------------------------------ #
    # channel_stores  (junção canal × loja)
    # ------------------------------------------------------------------ #
    op.create_table(
        'channel_stores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('channels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('channel_id', 'store_id', name='uq_channelstore_channel_store'),
    )

    # ------------------------------------------------------------------ #
    # product_prices
    # ------------------------------------------------------------------ #
    op.create_table(
        'product_prices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('product_id', sa.String(),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('channels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'product_id', 'channel_id', 'store_id',
                            name='uq_price_product_channel_store'),
    )

    # ------------------------------------------------------------------ #
    # product_stock
    # ------------------------------------------------------------------ #
    op.create_table(
        'product_stock',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('product_id', sa.String(),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('channels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('available', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'product_id', 'channel_id', 'store_id',
                            name='uq_stock_product_channel_store'),
    )


def downgrade() -> None:
    op.drop_table('product_stock')
    op.drop_table('product_prices')
    op.drop_table('channel_stores')
    op.drop_table('stores')
    op.drop_table('channels')
    op.drop_table('customers')
    op.drop_column('products', 'updated_at')
    op.drop_column('products', 'data_hash')
    op.drop_column('products', 'is_active')
