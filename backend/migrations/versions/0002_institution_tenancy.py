"""Add institution ownership and tenant identifier mapping."""
from alembic import op
import sqlalchemy as sa

revision = "0002_institution_tenancy"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

TABLES = ("customers", "accounts", "devices", "beneficiaries", "transactions",
          "risk_signals", "risk_decisions", "cases", "interventions", "audit_logs")


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in TABLES:
        if table not in inspector.get_table_names():
            continue
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "institution_id" not in columns:
            op.add_column(table, sa.Column("institution_id", sa.String(length=32),
                nullable=False, server_default="default"))
        existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table)}
        index_name = f"ix_{table}_institution_id"
        if index_name not in existing_indexes:
            op.create_index(index_name, table, ["institution_id"], unique=False)

    if "tenant_identifiers" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "tenant_identifiers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("institution_id", sa.String(length=32), nullable=False),
            sa.Column("entity_type", sa.String(length=30), nullable=False),
            sa.Column("external_id", sa.String(length=160), nullable=False),
            sa.Column("internal_id", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("institution_id", "entity_type", "external_id", name="uq_tenant_identifier_external"),
            sa.UniqueConstraint("institution_id", "entity_type", "internal_id", name="uq_tenant_identifier_internal"),
        )
        op.create_index("ix_tenant_identifiers_institution_id", "tenant_identifiers", ["institution_id"], unique=False)


def downgrade():
    # Tenant data may have been written after deployment; keep rollback non-destructive.
    pass
