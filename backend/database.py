from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_settings

settings = get_settings()

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./"):
    base_dir = Path(__file__).resolve().parent.parent
    db_file = base_dir / db_url.replace("sqlite:///./", "")
    db_url = f"sqlite:///{db_file.as_posix()}"

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_up_to_date(bind_engine):
    """Safely auto-migrate missing columns for MySQL/PostgreSQL/SQLite."""
    from sqlalchemy import text
    migrations = [
        ("centres", "contact_number", "VARCHAR(20)", "NULL"),
        ("centres", "is_paused", "BOOLEAN", "FALSE"),
        ("centres", "total_counters", "INT", "3"),
        ("centres", "active_counters", "INT", "3"),
        ("centres", "distance_km", "FLOAT", "0.0"),
        ("centres", "rating", "FLOAT", "4.5"),
        ("bookings", "assigned_counter", "INT", "NULL"),
        ("bookings", "call_time", "DATETIME", "NULL"),
        ("bookings", "serving_at", "DATETIME", "NULL"),
        ("bookings", "completed_at", "DATETIME", "NULL"),
        ("bookings", "token_display", "VARCHAR(50)", "''"),
    ]

    with bind_engine.connect() as conn:
        for table, column, col_type, default in migrations:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default};"))
                conn.commit()
            except Exception:
                pass
