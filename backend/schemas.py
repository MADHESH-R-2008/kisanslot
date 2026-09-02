from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# ──────────────────────────────────────────────
# Auth Schemas
# ──────────────────────────────────────────────

class FarmerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    mobile: str = Field(..., min_length=10, max_length=10)
    farmer_id: str = Field(..., min_length=2, max_length=20)
    village: str = Field(..., min_length=2, max_length=255)
    district: str = Field(..., min_length=2, max_length=255)
    state: str = Field(..., min_length=2, max_length=255)
    crop: str = Field(..., min_length=2, max_length=100)
    expected_quantity: float = Field(..., gt=0)
    password: str = Field(..., min_length=4, max_length=128)


class FarmerLoginRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=10)
    password: str = Field(..., min_length=4)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    farmer: "FarmerBrief"


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    centre_id: Optional[int] = None
    role: str

class FarmerBrief(BaseModel):
    id: int
    name: str
    farmer_id: str

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# Farmer Schemas
# ──────────────────────────────────────────────

class FarmerResponse(BaseModel):
    id: int
    name: str
    mobile: str
    farmer_id: str
    village: str
    district: str
    state: str
    crop: str
    expected_quantity: float

    class Config:
        from_attributes = True

class FarmerUpdateRequest(BaseModel):
    name: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    crop: Optional[str] = None
    expected_quantity: Optional[float] = None

# ──────────────────────────────────────────────
# Centre Schemas
# ──────────────────────────────────────────────

class CentreResponse(BaseModel):
    id: int
    name: str
    address: str
    district: str
    state: str
    latitude: float
    longitude: float
    active_counters: int
    is_active: bool
    distance_km: float
    rating: float
    queue_count: int = 0
    estimated_wait_minutes: int = 0

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# Slot Schemas
# ──────────────────────────────────────────────

class SlotResponse(BaseModel):
    id: int
    start_time: str
    end_time: str
    capacity: int
    booked_count: int
    available: int
    is_active: bool

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# Booking Schemas
# ──────────────────────────────────────────────

class BookingCreateRequest(BaseModel):
    centre_id: int
    slot_id: int
    crop: str = Field(..., min_length=2, max_length=100)
    expected_quantity: float = Field(..., gt=0)
    vehicle_number: str = Field(..., min_length=2, max_length=20)

class BookingResponse(BaseModel):
    booking_id: str
    token_number: int
    status: str
    centre: str
    date: str
    start_time: str
    end_time: str
    crop: str
    expected_quantity: float
    vehicle_number: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BookingDetailResponse(BaseModel):
    booking_id: str
    token_number: int
    centre: str
    centre_id: int
    date: str
    time: str
    crop: str
    quantity: float
    vehicle_number: str
    status: str

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# Queue Schemas
# ──────────────────────────────────────────────

class QueueResponse(BaseModel):
    booking_id: str
    queue_position: int
    farmers_ahead: int
    estimated_wait_minutes: int
    active_counters: int
    status: str

class QueueEntry(BaseModel):
    token: int
    booking_id: str
    farmer_name: str
    status: str
    arrival_time: Optional[datetime] = None
    queue_position: Optional[int] = None

class CentreQueueStatusResponse(BaseModel):
    centre_id: int
    waiting_count: int
    processing_count: int
    completed_count: int
    active_counters: int
    queue: list[QueueEntry]

# ──────────────────────────────────────────────
# Procurement Schemas
# ──────────────────────────────────────────────

class ProcurementResponse(BaseModel):
    crop: str
    expected_quantity: float
    actual_weight: Optional[float] = None
    quality_status: str
    rate: float
    total_amount: Optional[float] = None
    status: str

class ProcurementUpdateRequest(BaseModel):
    quality_status: Optional[str] = None
    actual_weight: Optional[float] = None
    rate: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None

# ──────────────────────────────────────────────
# Payment Schemas
# ──────────────────────────────────────────────

class PaymentResponse(BaseModel):
    amount: Optional[float] = None
    transaction_id: Optional[str] = None
    status: str
    payment_date: Optional[datetime] = None

class PaymentUpdateRequest(BaseModel):
    amount: Optional[float] = None
    transaction_id: Optional[str] = None
    status: Optional[str] = None
    payment_date: Optional[datetime] = None

# ──────────────────────────────────────────────
# Notification Schemas
# ──────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
