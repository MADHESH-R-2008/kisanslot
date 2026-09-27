"""Add district-scoped MASTER access control."""
from alembic import op
import sqlalchemy as sa

revision = "20260927_04"
down_revision = "20260927_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "districts" not in tables:
        op.create_table(
            "districts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False, unique=True),
            sa.Column("code", sa.String(30), nullable=False, unique=True),
            sa.Column("state", sa.String(255), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    centre_columns = {c["name"] for c in inspector.get_columns("centres")}
    if "district_id" not in centre_columns:
        op.add_column("centres", sa.Column("district_id", sa.Integer(), nullable=True))
        op.create_index("ix_centres_district_id", "centres", ["district_id"])
        op.create_foreign_key("fk_centres_district_id", "centres", "districts", ["district_id"], ["id"])

    admin_columns = {c["name"] for c in inspector.get_columns("admins")}
    additions = {
        "full_name": sa.Column("full_name", sa.String(255), nullable=True),
        "mobile": sa.Column("mobile", sa.String(20), nullable=True),
        "district_id": sa.Column("district_id", sa.Integer(), nullable=True),
        "updated_at": sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    }
    for name, column in additions.items():
        if name not in admin_columns:
            op.add_column("admins", column)
    if "district_id" not in admin_columns:
        op.create_index("ix_admins_district_id", "admins", ["district_id"])
        op.create_foreign_key("fk_admins_district_id", "admins", "districts", ["district_id"], ["id"])
    if "mobile" not in admin_columns:
        op.create_unique_constraint("uq_admins_mobile", "admins", ["mobile"])

    if bind.dialect.name in {"mysql", "mariadb"}:
        op.execute(sa.text("ALTER TABLE admins MODIFY role ENUM('FARMER','CENTRE_OPERATOR','ADMIN','MASTER','SUPER_ADMIN') NOT NULL"))
    else:
        with op.batch_alter_table("admins") as batch:
            batch.alter_column("role", existing_type=sa.String(), type_=sa.Enum("FARMER", "CENTRE_OPERATOR", "ADMIN", "MASTER", "SUPER_ADMIN", name="roleenum"), existing_nullable=False)

    if "masters" not in tables:
        op.create_table(
            "masters", sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("admins.id"), nullable=False, unique=True),
            sa.Column("district_id", sa.Integer(), sa.ForeignKey("districts.id"), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
    if "operators" not in tables:
        op.create_table(
            "operators", sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("admins.id"), nullable=False, unique=True),
            sa.Column("centre_id", sa.Integer(), sa.ForeignKey("centres.id"), nullable=False, index=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    audit_columns = {c["name"] for c in inspector.get_columns("audit_logs")}
    if "role" not in audit_columns:
        op.add_column("audit_logs", sa.Column("role", sa.String(30), nullable=True))
    if "district_id" not in audit_columns:
        op.add_column("audit_logs", sa.Column("district_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_audit_logs_district_id", "audit_logs", "districts", ["district_id"], ["id"])


def downgrade() -> None:
    pass
