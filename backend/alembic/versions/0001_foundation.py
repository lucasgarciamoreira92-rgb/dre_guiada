"""Foundation: companies and monthly periods."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("cnpj", sa.String(18)),
        sa.Column("segment", sa.String(120)),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("guided_mode", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_company_name"),
    )
    op.create_table(
        "periods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False
        ),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "completion_percentage", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("reopened_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "company_id", "month", "year", name="uq_period_company_month_year"
        ),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_period_month"),
        sa.CheckConstraint("year BETWEEN 1900 AND 2100", name="ck_period_year"),
        sa.CheckConstraint(
            "completion_percentage BETWEEN 0 AND 100", name="ck_period_completion"
        ),
        sa.CheckConstraint(
            "status IN ('draft','provisional','ready','closed','reopened')",
            name="ck_period_status",
        ),
    )
    op.create_index("ix_periods_company_id", "periods", ["company_id"])


def downgrade():
    op.drop_index("ix_periods_company_id", table_name="periods")
    op.drop_table("periods")
    op.drop_table("companies")
