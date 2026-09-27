from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes import (
    auth_routes,
    farmer_routes,
    centre_routes,
    slot_routes,
    booking_routes,
    queue_routes,
    procurement_routes,
    payment_routes,
    ws_routes,
    notification_routes,
    counter_routes,
    admin_routes,
    master_routes,
)

from database import engine, Base, ensure_schema_up_to_date
from auth import get_current_master_admin
from models import AdminUser
from config import get_settings

settings = get_settings()

# Local compatibility only. Production schema changes are applied with Alembic.
if settings.ENVIRONMENT.lower() == "development":
    Base.metadata.create_all(bind=engine)
    try:
        ensure_schema_up_to_date(engine)
    except Exception:
        pass

app = FastAPI(
    title="KisanSlot API",
    description="Smart Farmer Procurement & Queue Management System — Phase 2 Backend",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for Flutter development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_routes.router)
app.include_router(farmer_routes.router)
app.include_router(centre_routes.router)
app.include_router(slot_routes.router)
app.include_router(booking_routes.router)
app.include_router(queue_routes.router)
app.include_router(procurement_routes.router)
app.include_router(payment_routes.router)
app.include_router(ws_routes.router)
app.include_router(notification_routes.router)
app.include_router(counter_routes.router)
app.include_router(admin_routes.router)
app.include_router(master_routes.master_router)
app.include_router(master_routes.super_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": "KisanSlot API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

@app.post("/api/migrate", tags=["System"])
def migrate_database(_: AdminUser = Depends(get_current_master_admin)):
    try:
        from database import engine, ensure_schema_up_to_date
        res = ensure_schema_up_to_date(engine)
        return {"status": "Migration executed", "details": res}
    except Exception:
        raise HTTPException(status_code=500, detail="Database migration failed")


@app.post("/api/seed", tags=["System"])
def seed_database(_: AdminUser = Depends(get_current_master_admin)):
    try:
        from database import engine, ensure_schema_up_to_date
        migration_results = ensure_schema_up_to_date(engine)
        from seed import seed
        seed()
        return {"message": "Database seeded successfully! You can now log in.", "migration_results": migration_results}
    except Exception:
        raise HTTPException(status_code=500, detail="Database seed failed")
