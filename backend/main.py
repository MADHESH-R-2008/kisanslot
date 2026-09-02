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
)

# Create all tables on startup
Base.metadata.create_all(bind=engine)

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
