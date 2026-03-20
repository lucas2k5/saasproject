"""offers: Offer, OfferProduct, OfferAudience

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'offers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False, index=True),
        sa.Column('offer_id', sa.String(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('mechanic_params', JSON, nullable=False),
        sa.Column('channel_ids', JSON, nullable=True),
        sa.Column('store_ids', JSON, nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'offer_id', name='uq_offer_tenant_offerid'),
    )

    op.create_table(
        'offer_products',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('offer_id', UUID(as_uuid=True),
                  sa.ForeignKey('offers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', sa.String(),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='TRIGGER'),
        sa.UniqueConstraint('offer_id', 'product_id', 'role', name='uq_offerproduct_offer_product_role'),
    )

    op.create_table(
        'offer_audiences',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('offer_id', UUID(as_uuid=True),
                  sa.ForeignKey('offers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('audience_type', sa.String(), nullable=False),
        sa.Column('audience_value', JSON, nullable=True),
    )


def downgrade():
    op.drop_table('offer_audiences')
    op.drop_table('offer_products')
    op.drop_table('offers')
