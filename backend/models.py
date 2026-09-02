import enum
from datetime import datetime, date, time

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Time,
    ForeignKey, Enum as SAEnum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


# ──────────────────────────────────────────────
# Status Enums
# ──────────────────────────────────────────────

class BookingStatusEnum(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    ARRIVED = "ARRIVED"
    VERIFIED = "VERIFIED"
    WAITING = "WAITING"
    CALLED = "CALLED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

class RoleEnum(str, enum.Enum):
    FARMER = "FARMER"
    CENTRE_OPERATOR = "CENTRE_OPERATOR"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

class ProcurementStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    QUALITY_CHECK = "QUALITY_CHECK"
    WEIGHING = "WEIGHING"
    COMPLETED = "COMPLETED"

class PaymentStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# ──────────────────────────────────────────────
# Farmer
# ──────────────────────────────────────────────

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    mobile = Column(String(15), unique=True, nullable=False, index=True)
    farmer_id = Column(String(20), unique=True, nullable=False, index=True)
    village = Column(String(255), nullable=False)
    district = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    crop = Column(String(100), nullable=False)
    expected_quantity = Column(Float, nullable=False, default=0.0)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bookings = relationship("Booking", back_populates="farmer", cascade="all, delete-orphan")

# ──────────────────────────────────────────────
# Procurement Centre
# ──────────────────────────────────────────────

class Centre(Base):
    __tablename__ = "centres"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    district = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    active_counters = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    distance_km = Column(Float, default=0.0)
    rating = Column(Float, default=4.5)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    slots = relationship("Slot", back_populates="centre", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="centre")

# ──────────────────────────────────────────────
# Slot
# ──────────────────────────────────────────────

class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    capacity = Column(Integer, default=25)
    booked_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationships
    centre = relationship("Centre", back_populates="slots")
    bookings = relationship("Booking", back_populates="slot")

    __table_args__ = (
        UniqueConstraint("centre_id", "date", "start_time", name="uq_centre_date_time"),
    )

# ──────────────────────────────────────────────
# Booking
# ──────────────────────────────────────────────

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(String(20), unique=True, nullable=False, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    crop = Column(String(100), nullable=False)
    expected_quantity = Column(Float, nullable=False)
    vehicle_number = Column(String(20), nullable=False)
    token_number = Column(Integer, nullable=False)
    status = Column(
        SAEnum(BookingStatusEnum, values_callable=lambda e: [x.value for x in e]),
        default=BookingStatusEnum.CONFIRMED,
        nullable=False,
    )
    arrival_time = Column(DateTime, nullable=True) # Track when they arrived
    call_time = Column(DateTime, nullable=True) # Track when they were called
    assigned_counter = Column(Integer, nullable=True) # Track which counter
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    farmer = relationship("Farmer", back_populates="bookings")
    centre = relationship("Centre", back_populates="bookings")
    slot = relationship("Slot", back_populates="bookings")
    procurement = relationship("Procurement", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")

# ──────────────────────────────────────────────
# Procurement
# ──────────────────────────────────────────────

class Procurement(Base):
    __tablename__ = "procurement"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    quality_status = Column(String(50), default="PENDING")
    actual_weight = Column(Float, nullable=True)
    rate = Column(Float, default=21.50)
    total_amount = Column(Float, nullable=True)
    status = Column(
        SAEnum(ProcurementStatusEnum, values_callable=lambda e: [x.value for x in e]),
        default=ProcurementStatusEnum.PENDING,
        nullable=False,
    )
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="procurement")

# ──────────────────────────────────────────────
# Payment
# ──────────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    amount = Column(Float, nullable=True)
    transaction_id = Column(String(100), nullable=True)
    status = Column(
        SAEnum(PaymentStatusEnum, values_callable=lambda e: [x.value for x in e]),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )
    payment_date = Column(DateTime, nullable=True)

    # Relationships
    booking = relationship("Booking", back_populates="payment")

# ──────────────────────────────────────────────
# System Users (Admins/Operators)
# ──────────────────────────────────────────────

class AdminUser(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SAEnum(RoleEnum, values_callable=lambda e: [x.value for x in e]),
        default=RoleEnum.CENTRE_OPERATOR,
        nullable=False,
    )
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=True) # Nullable for Master Admins
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    centre = relationship("Centre")

# ──────────────────────────────────────────────
# Notifications
# ──────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("farmers.id"), nullable=False) # Bound to farmers for now
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="INFO")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ──────────────────────────────────────────────
# Audit Logs
# ──────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), nullable=False) # String to handle both Farmer ID and Admin ID
    action = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

