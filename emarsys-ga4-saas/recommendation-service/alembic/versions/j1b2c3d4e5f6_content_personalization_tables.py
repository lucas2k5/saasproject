"""content personalization tables — templates, content_email, content_whatsapp, content_push, content_jobs + S3 config

Revision ID: j1b2c3d4e5f6
Revises: i0a1b2c3d4e5
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "j1b2c3d4e5f6"
down_revision = "i0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    # --- TenantConfig: S3 + content columns ---
    op.add_column("tenant_configs", sa.Column("s3_bucket_name", sa.String(), nullable=True))
    op.add_column("tenant_configs", sa.Column("s3_access_key", sa.String(), nullable=True))
    op.add_column("tenant_configs", sa.Column("s3_secret_key", sa.String(), nullable=True))
    op.add_column("tenant_configs", sa.Column("s3_region", sa.String(), server_default="us-east-1"))
    op.add_column("tenant_configs", sa.Column("s3_presigned_expiration_hours", sa.Integer(), server_default="168"))
    op.add_column("tenant_configs", sa.Column("content_max_products_email", sa.Integer(), server_default="6"))
    op.add_column("tenant_configs", sa.Column("content_max_products_whatsapp", sa.Integer(), server_default="3"))
    op.add_column("tenant_configs", sa.Column("content_max_products_push", sa.Integer(), server_default="1"))

    # --- content_templates ---
    op.create_table(
        "content_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("offer_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "channel", "offer_type", name="uq_contenttemplate_tenant_channel_offertype"),
    )

    # --- content_email ---
    op.create_table(
        "content_email",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_external_id", sa.String(), nullable=False),
        sa.Column("customer_add_id", sa.String(), nullable=True),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("products_count", sa.Integer(), server_default="0"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "customer_id", name="uq_contentemail_tenant_customer"),
    )

    # --- content_whatsapp ---
    op.create_table(
        "content_whatsapp",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_external_id", sa.String(), nullable=False),
        sa.Column("customer_add_id", sa.String(), nullable=True),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("image_s3_key", sa.String(), nullable=False),
        sa.Column("products_count", sa.Integer(), server_default="0"),
        sa.Column("presigned_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "customer_id", name="uq_contentwhatsapp_tenant_customer"),
    )

    # --- content_push ---
    op.create_table(
        "content_push",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_external_id", sa.String(), nullable=False),
        sa.Column("customer_add_id", sa.String(), nullable=True),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("image_s3_key", sa.String(), nullable=True),
        sa.Column("presigned_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "customer_id", name="uq_contentpush_tenant_customer"),
    )

    # --- content_jobs ---
    op.create_table(
        "content_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("triggered_by", sa.String(), nullable=False, server_default="auto"),
        sa.Column("channels", sa.JSON(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("customers_processed", sa.Integer(), nullable=True),
        sa.Column("emails_generated", sa.Integer(), nullable=True),
        sa.Column("images_generated", sa.Integer(), nullable=True),
        sa.Column("push_generated", sa.Integer(), nullable=True),
        sa.Column("error_msg", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table("content_jobs")
    op.drop_table("content_push")
    op.drop_table("content_whatsapp")
    op.drop_table("content_email")
    op.drop_table("content_templates")
    op.drop_column("tenant_configs", "content_max_products_push")
    op.drop_column("tenant_configs", "content_max_products_whatsapp")
    op.drop_column("tenant_configs", "content_max_products_email")
    op.drop_column("tenant_configs", "s3_presigned_expiration_hours")
    op.drop_column("tenant_configs", "s3_region")
    op.drop_column("tenant_configs", "s3_secret_key")
    op.drop_column("tenant_configs", "s3_access_key")
    op.drop_column("tenant_configs", "s3_bucket_name")
