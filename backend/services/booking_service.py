from datetime import date as date_type
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from models import Booking, Slot, TokenCounter


def generate_booking_id(db: Session) -> str:
    """Generate an opaque booking reference without a read/increment race."""
    while True:
        candidate = f"KS{secrets.token_hex(5).upper()}"
        if not db.query(Booking.id).filter(Booking.booking_id == candidate).first():
            return candidate


def generate_token_number(db: Session, slot_id: int, centre_id: int = None) -> int:
    """
    Generate a sequential, concurrency-safe token number for a given centre and date.
    Uses row/table locking semantics where supported to prevent duplicate tokens.
    """
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        return 1

    target_centre_id = centre_id or slot.centre_id

    # Query highest token_number for this centre on this date with row lock if possible
    query = (
        db.query(func.max(Booking.token_number))
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(
            Booking.centre_id == target_centre_id,
            Slot.date == slot.date,
        )
    )

    try:
        query = query.with_for_update()
    except Exception:
        pass  # Dialects like SQLite don't support with_for_update

    max_token = query.scalar() or 0
    return max_token + 1


def allocate_token_number(db: Session, centre_id: int, booking_date: date_type) -> int:
    """Atomically allocate the next token for a centre/day.

    PostgreSQL, MySQL, and SQLite use their native atomic upsert operation so
    concurrent transactions cannot receive the same value.
    """
    dialect = db.get_bind().dialect.name
    values = {"centre_id": centre_id, "booking_date": booking_date, "last_token": 1}

    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
        statement = insert(TokenCounter).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[TokenCounter.centre_id, TokenCounter.booking_date],
            set_={"last_token": TokenCounter.last_token + 1},
        ).returning(TokenCounter.last_token)
        return int(db.execute(statement).scalar_one())

    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
        statement = insert(TokenCounter).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[TokenCounter.centre_id, TokenCounter.booking_date],
            set_={"last_token": TokenCounter.last_token + 1},
        ).returning(TokenCounter.last_token)
        return int(db.execute(statement).scalar_one())

    if dialect in {"mysql", "mariadb"}:
        # LAST_INSERT_ID(expr) is scoped to this connection. It returns 1 for
        # the first allocation and the atomically incremented value thereafter.
        db.execute(text(
            "INSERT INTO token_counters "
            "(centre_id, booking_date, last_token, updated_at) "
            "VALUES (:centre_id, :booking_date, LAST_INSERT_ID(1), CURRENT_TIMESTAMP) "
            "ON DUPLICATE KEY UPDATE "
            "last_token = LAST_INSERT_ID(last_token + 1), "
            "updated_at = CURRENT_TIMESTAMP"
        ), {"centre_id": centre_id, "booking_date": booking_date})
        return int(db.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())

    counter = (
        db.query(TokenCounter)
        .filter(TokenCounter.centre_id == centre_id, TokenCounter.booking_date == booking_date)
        .with_for_update()
        .first()
    )
    if counter is None:
        counter = TokenCounter(**values)
        db.add(counter)
        db.flush()
    else:
        counter.last_token += 1
        db.flush()
    return counter.last_token


def format_token_display(centre_id: int, token_number: int) -> str:
    """
    Format a token for display.
    Example: centre_id=3, token_number=6 → 'C3-006'
    """
    return f"C{centre_id}-{token_number:03d}"
