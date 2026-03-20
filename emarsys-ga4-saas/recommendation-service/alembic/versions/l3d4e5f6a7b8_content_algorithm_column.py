"""Add algorithm column to content tables and update unique constraints

Revision ID: l3d4e5f6a7b8
Revises: k2c3d4e5f6a7
Create Date: 2026-03-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'l3d4e5f6a7b8'
down_revision = 'k2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add algorithm column with default for existing rows
    for table in ('content_email', 'content_whatsapp', 'content_push'):
        op.add_column(table, sa.Column('algorithm', sa.String(), nullable=False, server_default='pessoal'))

    # Drop old unique constraints
    op.drop_constraint('uq_contentemail_tenant_customer', 'content_email', type_='unique')
    op.drop_constraint('uq_contentwhatsapp_tenant_customer', 'content_whatsapp', type_='unique')
    op.drop_constraint('uq_contentpush_tenant_customer', 'content_push', type_='unique')

    # Create new unique constraints including algorithm
    op.create_unique_constraint('uq_contentemail_tenant_customer_algo', 'content_email',
                                ['tenant_id', 'customer_id', 'algorithm'])
    op.create_unique_constraint('uq_contentwhatsapp_tenant_customer_algo', 'content_whatsapp',
                                ['tenant_id', 'customer_id', 'algorithm'])
    op.create_unique_constraint('uq_contentpush_tenant_customer_algo', 'content_push',
                                ['tenant_id', 'customer_id', 'algorithm'])


def downgrade() -> None:
    # Drop new constraints
    op.drop_constraint('uq_contentemail_tenant_customer_algo', 'content_email', type_='unique')
    op.drop_constraint('uq_contentwhatsapp_tenant_customer_algo', 'content_whatsapp', type_='unique')
    op.drop_constraint('uq_contentpush_tenant_customer_algo', 'content_push', type_='unique')

    # Delete non-pessoal rows to avoid duplicate violations when restoring old constraint
    op.execute("DELETE FROM content_email WHERE algorithm != 'pessoal'")
    op.execute("DELETE FROM content_whatsapp WHERE algorithm != 'pessoal'")
    op.execute("DELETE FROM content_push WHERE algorithm != 'pessoal'")

    # Restore old constraints
    op.create_unique_constraint('uq_contentemail_tenant_customer', 'content_email',
                                ['tenant_id', 'customer_id'])
    op.create_unique_constraint('uq_contentwhatsapp_tenant_customer', 'content_whatsapp',
                                ['tenant_id', 'customer_id'])
    op.create_unique_constraint('uq_contentpush_tenant_customer', 'content_push',
                                ['tenant_id', 'customer_id'])

    # Drop algorithm columns
    for table in ('content_email', 'content_whatsapp', 'content_push'):
        op.drop_column(table, 'algorithm')
