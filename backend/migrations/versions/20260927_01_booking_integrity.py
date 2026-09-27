"""Add concurrency-safe booking token infrastructure without deleting data."""
from alembic import op
import sqlalchemy as sa

revision = "20260927_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "centres" not in tables or "bookings" not in tables:
        from database import Base
        import models  # noqa: F401
        Base.metadata.create_all(bind=bind)
        return

    centre_columns = {column["name"] for column in inspector.get_columns("centres")}
    if "updated_at" not in centre_columns:
        op.add_column("centres", sa.Column("updated_at", sa.DateTime(), nullable=True))
        op.execute(sa.text("UPDATE centres SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))

    if "token_counters" not in tables:
        op.create_table(
            "token_counters",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("centre_id", sa.Integer(), sa.ForeignKey("centres.id"), nullable=False),
            sa.Column("booking_date", sa.Date(), nullable=False),
            sa.Column("last_token", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("centre_id", "booking_date", name="uq_token_counter_centre_date"),
        )
        op.create_index("ix_token_counters_centre_id", "token_counters", ["centre_id"])
        op.create_index("ix_token_counters_booking_date", "token_counters", ["booking_date"])

    booking_columns = {column["name"] for column in inspector.get_columns("bookings")}
    if "booking_date" not in booking_columns:
        op.add_column("bookings", sa.Column("booking_date", sa.Date(), nullable=True))
        op.execute(sa.text("UPDATE bookings SET booking_date = (SELECT slots.date FROM slots WHERE slots.id = bookings.slot_id) WHERE booking_date IS NULL"))
        with op.batch_alter_table("bookings") as batch:
            batch.alter_column("booking_date", existing_type=sa.Date(), nullable=False)
            batch.create_index("ix_bookings_booking_date", ["booking_date"])
            batch.create_unique_constraint("uq_booking_centre_date_token", ["centre_id", "booking_date", "token_number"])

    if bind.dialect.name == "postgresql":
        op.execute(sa.text(
            "INSERT INTO token_counters (centre_id, booking_date, last_token, updated_at) "
            "SELECT b.centre_id, b.booking_date, MAX(b.token_number), CURRENT_TIMESTAMP "
            "FROM bookings b WHERE b.booking_date IS NOT NULL GROUP BY b.centre_id, b.booking_date "
            "ON CONFLICT (centre_id, booking_date) DO NOTHING"
        ))
    elif bind.dialect.name == "sqlite":
        op.execute(sa.text(
            "INSERT OR IGNORE INTO token_counters (centre_id, booking_date, last_token, updated_at) "
            "SELECT b.centre_id, b.booking_date, MAX(b.token_number), CURRENT_TIMESTAMP "
            "FROM bookings b WHERE b.booking_date IS NOT NULL GROUP BY b.centre_id, b.booking_date"
        ))
    elif bind.dialect.name in {"mysql", "mariadb"}:
        op.execute(sa.text(
            "INSERT IGNORE INTO token_counters (centre_id, booking_date, last_token, updated_at) "
            "SELECT b.centre_id, b.booking_date, MAX(b.token_number), CURRENT_TIMESTAMP "
            "FROM bookings b WHERE b.booking_date IS NOT NULL GROUP BY b.centre_id, b.booking_date"
        ))

    payment_columns = {column["name"] for column in inspector.get_columns("payments")}
    if "transaction_id" in payment_columns:
        existing_indexes = {index["name"] for index in inspector.get_indexes("payments")}
        if "uq_payments_transaction_id" not in existing_indexes:
            op.create_index("uq_payments_transaction_id", "payments", ["transaction_id"], unique=True)


def downgrade() -> None:
    # Intentionally conservative: production data is not dropped automatically.
    pass
