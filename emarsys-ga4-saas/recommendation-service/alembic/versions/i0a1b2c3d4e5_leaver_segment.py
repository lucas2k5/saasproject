"""leaver segment — TenantConfig columns for Leaver thresholds

Revision ID: i0a1b2c3d4e5
Revises: h9c0d1e2f3a4
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa

revision = "i0a1b2c3d4e5"
down_revision = "h9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tenant_configs", sa.Column("leaver_recency_min", sa.Integer(), server_default="180"))
    op.add_column("tenant_configs", sa.Column("leaver_p_alive_max", sa.Float(), server_default="0.15"))
    op.add_column("tenant_configs", sa.Column("leaver_invoices_min", sa.Integer(), server_default="3"))


def downgrade():
    op.drop_column("tenant_configs", "leaver_invoices_min")
    op.drop_column("tenant_configs", "leaver_p_alive_max")
    op.drop_column("tenant_configs", "leaver_recency_min")
