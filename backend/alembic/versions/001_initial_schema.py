"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geography

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    op.create_table(
        "organizations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("plan", sa.String(20), server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("org_id", sa.String(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(200)),
        sa.Column("role", sa.String(20), server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "dispensaries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("slug", sa.String(200), unique=True),
        sa.Column("license_number", sa.String(100)),
        sa.Column("address", sa.String(500)),
        sa.Column("city", sa.String(100)),
        sa.Column("county", sa.String(100)),
        sa.Column("state", sa.String(2), server_default="NJ"),
        sa.Column("zip_code", sa.String(10)),
        sa.Column("lat", sa.Numeric(10, 7)),
        sa.Column("lng", sa.Numeric(10, 7)),
        sa.Column("geom", Geography(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("weedmaps_id", sa.String(100)),
        sa.Column("leafly_slug", sa.String(200)),
        sa.Column("jane_store_id", sa.String(100)),
        sa.Column("dutchie_id", sa.String(200)),
        sa.Column("treez_id", sa.String(100)),
        sa.Column("dispense_slug", sa.String(200)),
        sa.Column("primary_platform", sa.String(50)),
        sa.Column("website", sa.String(500)),
        sa.Column("phone", sa.String(20)),
        sa.Column("instagram", sa.String(100)),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("med_only", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_dispensaries_city", "dispensaries", ["city"])
    op.create_index("ix_dispensaries_county", "dispensaries", ["county"])
    op.execute("CREATE INDEX idx_dispensaries_geom ON dispensaries USING GIST(geom)")

    op.create_table(
        "deals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("dispensary_id", sa.String(), sa.ForeignKey("dispensaries.id"), nullable=False),
        sa.Column("source_platform", sa.String(50)),
        sa.Column("external_id", sa.String(200)),
        sa.Column("title", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("deal_type", sa.String(50)),
        sa.Column("discount_value", sa.Numeric(10, 2)),
        sa.Column("discount_unit", sa.String(20)),
        sa.Column("minimum_purchase", sa.Numeric(10, 2)),
        sa.Column("applicable_categories", postgresql.ARRAY(sa.String())),
        sa.Column("applicable_brands", postgresql.ARRAY(sa.String())),
        sa.Column("day_of_week", postgresql.ARRAY(sa.String())),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("raw_text", sa.Text()),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("dispensary_id", "source_platform", "external_id", name="uq_deal_source"),
    )
    op.create_index("ix_deals_dispensary_id", "deals", ["dispensary_id"])
    op.create_index("ix_deals_is_active", "deals", ["is_active"])

    op.create_table(
        "deal_history",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("deal_id", sa.String(), sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("change_type", sa.String(30)),
        sa.Column("old_data", postgresql.JSONB()),
        sa.Column("new_data", postgresql.JSONB()),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "menu_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("dispensary_id", sa.String(), sa.ForeignKey("dispensaries.id"), nullable=False),
        sa.Column("external_id", sa.String(200)),
        sa.Column("name", sa.String(500)),
        sa.Column("brand", sa.String(200)),
        sa.Column("category", sa.String(100)),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("thc_percent", sa.Numeric(5, 2)),
        sa.Column("cbd_percent", sa.Numeric(5, 2)),
        sa.Column("weight", sa.Numeric(10, 2)),
        sa.Column("current_price", sa.Numeric(10, 2)),
        sa.Column("sale_price", sa.Numeric(10, 2)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("dispensary_id", "external_id", name="uq_menu_item"),
    )
    op.create_index("ix_menu_items_dispensary_id", "menu_items", ["dispensary_id"])

    op.create_table(
        "price_changes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("item_id", sa.String(), sa.ForeignKey("menu_items.id"), nullable=False),
        sa.Column("dispensary_id", sa.String(), sa.ForeignKey("dispensaries.id"), nullable=False),
        sa.Column("old_price", sa.Numeric(10, 2)),
        sa.Column("new_price", sa.Numeric(10, 2)),
        sa.Column("change_amount", sa.Numeric(10, 2)),
        sa.Column("change_pct", sa.Numeric(6, 2)),
        sa.Column("change_type", sa.String(20)),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("org_id", sa.String(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("trigger_type", sa.String(50)),
        sa.Column("filter_config", postgresql.JSONB(), server_default="{}"),
        sa.Column("channels", postgresql.ARRAY(sa.String()), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alert_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("alert_id", sa.String(), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("deal_id", sa.String(), sa.ForeignKey("deals.id"), nullable=True),
        sa.Column("item_id", sa.String(), sa.ForeignKey("menu_items.id"), nullable=True),
        sa.Column("message", sa.Text()),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("channels_used", postgresql.ARRAY(sa.String())),
    )

    op.create_table(
        "scrape_sources",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("dispensary_id", sa.String(), sa.ForeignKey("dispensaries.id"), nullable=False),
        sa.Column("platform", sa.String(50)),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("config", postgresql.JSONB(), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_scrape_at", sa.DateTime(timezone=True)),
        sa.Column("next_scrape_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "scrape_jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source_id", sa.String(), sa.ForeignKey("scrape_sources.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("deals_found", sa.Integer(), server_default="0"),
        sa.Column("items_found", sa.Integer(), server_default="0"),
        sa.Column("errors", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in ["scrape_jobs", "scrape_sources", "alert_events", "alerts",
                  "price_changes", "menu_items", "deal_history", "deals",
                  "dispensaries", "users", "organizations"]:
        op.drop_table(table)
