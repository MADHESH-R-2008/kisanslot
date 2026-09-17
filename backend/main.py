from fastapi import FastAPI
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
)

from database import engine, Base, ensure_schema_up_to_date

# Create all tables & auto-migrate missing columns on startup
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
    allow_origins=["*"],  # Allow Flutter dev on any local address
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

@app.get("/api/seed", tags=["System"])
def seed_database():
    try:
        from seed import seed
        seed()
        return {"message": "Database seeded successfully! You can now log in."}
    except Exception as e:
        return {"error": f"Failed to seed database: {str(e)}"}
