import enum
from datetime import datetime, date, time

from sqlalchemy import (
    Column, Integer, String, Float, Numeric, Boolean, DateTime, Date, Time,
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
    SERVING = "SERVING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    SKIPPED = "SKIPPED"

class RoleEnum(str, enum.Enum):
    FARMER = "FARMER"
    CENTRE_OPERATOR = "CENTRE_OPERATOR"
    ADMIN = "ADMIN"
    MASTER = "MASTER"
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
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bookings = relationship("Booking", back_populates="farmer", cascade="all, delete-orphan")

# ──────────────────────────────────────────────
# Procurement Centre
# ──────────────────────────────────────────────

class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(30), nullable=False, unique=True)
    state = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Centre(Base):
    __tablename__ = "centres"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True, index=True)
    address = Column(Text, nullable=False)
    district = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    contact_number = Column(String(20), nullable=True)
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    total_counters = Column(Integer, default=3)
    active_counters = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    distance_km = Column(Float, default=0.0)
    rating = Column(Float, default=4.5)
    google_map_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("code", name="uq_centre_code"),)

    # Relationships
    slots = relationship("Slot", back_populates="centre", cascade="all, delete-orphan")

    # ──────────────────────────────────────────────
    # Counters
    # ──────────────────────────────────────────────
    counters = relationship("Counter", back_populates="centre", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="centre")
    district_ref = relationship("District")

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
    booking_date = Column(Date, nullable=False, default=date.today, index=True)
    is_deleted = Column(Boolean, default=False)
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
    serving_at = Column(DateTime, nullable=True)  # Phase 3.2: when serving started
    completed_at = Column(DateTime, nullable=True)  # Phase 3.2: when completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("centre_id", "booking_date", "token_number", name="uq_booking_centre_date_token"),
    )


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
    actual_weight = Column(Numeric(12, 3), nullable=True)
    rejected_quantity = Column(Numeric(12, 3), nullable=False, default=0)
    rate = Column(Numeric(12, 2), default=21.50)
    total_amount = Column(Numeric(14, 2), nullable=True)
    remarks = Column(Text, nullable=True)
    procurement_date = Column(DateTime, nullable=True)
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
    amount = Column(Numeric(14, 2), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    payment_method = Column(String(30), nullable=True)
    failure_reason = Column(Text, nullable=True)
    status = Column(
        SAEnum(PaymentStatusEnum, values_callable=lambda e: [x.value for x in e]),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )
    payment_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    booking = relationship("Booking", back_populates="payment")

# ──────────────────────────────────────────────
# System Users (Admins/Operators)
# ──────────────────────────────────────────────

class AdminUser(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # No changes needed here
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    mobile = Column(String(20), nullable=True, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SAEnum(RoleEnum, values_callable=lambda e: [x.value for x in e]),
        default=RoleEnum.CENTRE_OPERATOR,
        nullable=False,
    )
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=True) # Nullable for Master Admins
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    centre = relationship("Centre")
    district = relationship("District")


class MasterProfile(Base):
    __tablename__ = "masters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("admins.id"), nullable=False, unique=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class OperatorProfile(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("admins.id"), nullable=False, unique=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class NotificationTypeEnum(str, enum.Enum):
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    QUEUE_UPDATE = "QUEUE_UPDATE"
    FARMER_CALLED = "FARMER_CALLED"
    PROCUREMENT_STARTED = "PROCUREMENT_STARTED"
    PROCUREMENT_COMPLETED = "PROCUREMENT_COMPLETED"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CENTRE_UPDATE = "CENTRE_UPDATE"
    SYSTEM = "SYSTEM"

# ──────────────────────────────────────────────
# Notifications
# ──────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True, index=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=True, index=True)
    type = Column(String(50), nullable=False, index=True, default="SYSTEM")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, unique=True)
    booking_notifications = Column(Boolean, default=True)
    queue_notifications = Column(Boolean, default=True)
    procurement_notifications = Column(Boolean, default=True)
    payment_notifications = Column(Boolean, default=True)
    system_notifications = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    role = Column(String(30), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ──────────────────────────────────────────────
# Counter Model and Enum
# ──────────────────────────────────────────────

class CounterStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BUSY = "BUSY"
    MAINTENANCE = "MAINTENANCE"

class Counter(Base):
    __tablename__ = "counters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(SAEnum(CounterStatusEnum, values_callable=lambda e: [x.value for x in e]), default=CounterStatusEnum.ACTIVE, nullable=False)
    is_available = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)  # Phase 3.2

    centre = relationship("Centre", back_populates="counters")
    current_booking = relationship("Booking", foreign_keys=[current_booking_id])


class TokenCounter(Base):
    """Atomic per-centre/day token allocator used by booking transactions."""
    __tablename__ = "token_counters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    centre_id = Column(Integer, ForeignKey("centres.id"), nullable=False, index=True)
    booking_date = Column(Date, nullable=False, index=True)
    last_token = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("centre_id", "booking_date", name="uq_token_counter_centre_date"),
    )
