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
    statements = [
        "ALTER TABLE centres ADD contact_number VARCHAR(20)",
        "ALTER TABLE centres ADD is_paused BOOLEAN",
        "ALTER TABLE centres ADD total_counters INT",
        "ALTER TABLE centres ADD active_counters INT",
        "ALTER TABLE centres ADD distance_km FLOAT",
        "ALTER TABLE centres ADD rating FLOAT",
        "ALTER TABLE counters ADD current_booking_id INT",
        "ALTER TABLE counters ADD is_available BOOLEAN",
        "ALTER TABLE counters ADD is_deleted BOOLEAN",
        "ALTER TABLE counters ADD created_at DATETIME",
        "ALTER TABLE counters ADD updated_at DATETIME",
        "ALTER TABLE bookings ADD assigned_counter INT",
        "ALTER TABLE bookings ADD call_time DATETIME",
        "ALTER TABLE bookings ADD serving_at DATETIME",
        "ALTER TABLE bookings ADD completed_at DATETIME",
        "ALTER TABLE bookings ADD token_display VARCHAR(50)",
        "ALTER TABLE bookings ADD arrival_time DATETIME",
        "ALTER TABLE bookings ADD is_deleted BOOLEAN",
        "ALTER TABLE bookings ADD created_at DATETIME",
        "ALTER TABLE bookings ADD updated_at DATETIME",
        "ALTER TABLE admins ADD centre_id INT",
        "ALTER TABLE notifications ADD booking_id INT",
        "ALTER TABLE notifications ADD centre_id INT",
        "ALTER TABLE notifications ADD updated_at DATETIME",
    ]

    results = []
    for stmt in statements:
        try:
            with bind_engine.begin() as conn:
                conn.execute(text(stmt))
            results.append(f"SUCCESS: {stmt}")
        except Exception as e:
            results.append(f"SKIPPED/EXISTS: {stmt} ({e})")
    return results
