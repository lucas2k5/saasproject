"""segment thresholds in tenant_config

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # OneTime
    op.add_column('tenant_configs', sa.Column('onetime_days_as_customer_min', sa.Integer(), nullable=True, server_default='60'))
    op.add_column('tenant_configs', sa.Column('onetime_p_alive_max', sa.Float(), nullable=True, server_default='0.3'))

    # NonEngaged
    op.add_column('tenant_configs', sa.Column('nonengaged_p_alive_max', sa.Float(), nullable=True, server_default='0.2'))
    op.add_column('tenant_configs', sa.Column('nonengaged_recency_min', sa.Integer(), nullable=True, server_default='180'))
    op.add_column('tenant_configs', sa.Column('nonengaged_velocity_trend_max', sa.Float(), nullable=True, server_default='0.3'))

    # LoyalStar
    op.add_column('tenant_configs', sa.Column('loyalstar_regularity_max', sa.Float(), nullable=True, server_default='0.6'))
    op.add_column('tenant_configs', sa.Column('loyalstar_velocity_trend_min', sa.Float(), nullable=True, server_default='0.9'))
    op.add_column('tenant_configs', sa.Column('loyalstar_ticket_trend_min', sa.Float(), nullable=True, server_default='0.9'))
    op.add_column('tenant_configs', sa.Column('loyalstar_category_diversity_min', sa.Integer(), nullable=True, server_default='3'))
    op.add_column('tenant_configs', sa.Column('loyalstar_p_alive_min', sa.Float(), nullable=True, server_default='0.7'))

    # LoyalRunner
    op.add_column('tenant_configs', sa.Column('loyalrunner_regularity_max', sa.Float(), nullable=True, server_default='0.8'))
    op.add_column('tenant_configs', sa.Column('loyalrunner_velocity_trend_min', sa.Float(), nullable=True, server_default='0.9'))
    op.add_column('tenant_configs', sa.Column('loyalrunner_p_alive_min', sa.Float(), nullable=True, server_default='0.5'))


def downgrade() -> None:
    op.drop_column('tenant_configs', 'loyalrunner_p_alive_min')
    op.drop_column('tenant_configs', 'loyalrunner_velocity_trend_min')
    op.drop_column('tenant_configs', 'loyalrunner_regularity_max')
    op.drop_column('tenant_configs', 'loyalstar_p_alive_min')
    op.drop_column('tenant_configs', 'loyalstar_category_diversity_min')
    op.drop_column('tenant_configs', 'loyalstar_ticket_trend_min')
    op.drop_column('tenant_configs', 'loyalstar_velocity_trend_min')
    op.drop_column('tenant_configs', 'loyalstar_regularity_max')
    op.drop_column('tenant_configs', 'nonengaged_velocity_trend_max')
    op.drop_column('tenant_configs', 'nonengaged_recency_min')
    op.drop_column('tenant_configs', 'nonengaged_p_alive_max')
    op.drop_column('tenant_configs', 'onetime_p_alive_max')
    op.drop_column('tenant_configs', 'onetime_days_as_customer_min')
