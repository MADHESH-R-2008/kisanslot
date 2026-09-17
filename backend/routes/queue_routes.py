from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from database import get_db
from models import (
    Farmer, Booking, Centre, Slot, Counter,
    BookingStatusEnum, CounterStatusEnum, AdminUser, Notification,
)
from schemas import (
    QueueResponse, BookingDetailResponse, CentreQueueStatusResponse,
    QueueEntry, QueueStatsResponse,
)
from auth import get_current_farmer
from dependencies import get_current_admin, require_admin_or_super
from services.queue_service import (
    calculate_queue_position, get_active_counter_count,
    get_available_counter, calculate_estimated_wait,
    WAITING_STATUSES, TERMINAL_STATUSES,
)
from services.booking_service import format_token_display
from services.notification_service import send_notification
from routes.ws_routes import manager

router = APIRouter(prefix="/api/queue", tags=["Queue"])


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

async def broadcast_queue_update(centre_id: int, db: Session, event: str = "QUEUE_UPDATED", extra: dict = None):
    """
    Phase 3.2: Rich broadcast with full queue data.
    """
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        return

    today = date.today()
    active_counters = get_active_counter_count(db, centre_id)

    # Count by status
    waiting_count = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(
            Booking.centre_id == centre_id,
            Slot.date == today,
            Booking.status.in_(WAITING_STATUSES),
        )
        .count()
    )

    serving_count = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(
            Booking.centre_id == centre_id,
            Slot.date == today,
            Booking.status.in_([BookingStatusEnum.CALLED, BookingStatusEnum.SERVING, BookingStatusEnum.PROCESSING]),
        )
        .count()
    )

    completed_count = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(
            Booking.centre_id == centre_id,
            Slot.date == today,
            Booking.status == BookingStatusEnum.COMPLETED,
        )
        .count()
    )

    payload = {
        "event": event,
        "centre_id": centre_id,
        "waiting_count": waiting_count,
        "serving_count": serving_count,
        "completed_count": completed_count,
        "active_counters": active_counters,
        "is_paused": centre.is_paused,
    }
    if extra:
        payload.update(extra)

    await manager.broadcast(payload, centre_id)


# ──────────────────────────────────────────────
# Farmer Endpoints
# ──────────────────────────────────────────────

@router.get("/{booking_id}", response_model=QueueResponse)
def get_queue_position(
    booking_id: str,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Calculate live queue position for a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    if booking.farmer_id != farmer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    active_counters = get_active_counter_count(db, booking.centre_id)
    queue_data = calculate_queue_position(db, booking, active_counters)

    # Find current serving/called token
    slot_date = booking.slot.date if booking.slot else date.today()
    current_serving_b = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(
            Booking.centre_id == booking.centre_id,
            Slot.date == slot_date,
            Booking.status.in_([BookingStatusEnum.CALLED, BookingStatusEnum.SERVING, BookingStatusEnum.PROCESSING]),
        )
        .order_by(Booking.token_number.asc())
        .first()
    )
    current_serving_token = (
        format_token_display(booking.centre_id, current_serving_b.token_number)
        if current_serving_b else None
    )

    # Get counter name if assigned
    counter_name = None
    if booking.assigned_counter:
        counter = db.query(Counter).filter(
            Counter.centre_id == booking.centre_id,
            Counter.id == booking.assigned_counter,
        ).first()
        counter_name = counter.name if counter else f"Counter {booking.assigned_counter}"

    formatted_token = format_token_display(booking.centre_id, booking.token_number)

    return QueueResponse(
        booking_id=booking.booking_id,
        token_number=formatted_token,
        token_display=formatted_token,
        queue_position=queue_data["queue_position"],
        farmers_ahead=queue_data["farmers_ahead"],
        estimated_wait_minutes=queue_data["estimated_wait_minutes"],
        current_serving_token=current_serving_token,
        active_counters=active_counters,
        status=queue_data["status"],
        assigned_counter=booking.assigned_counter,
        counter_name=counter_name,
    )


# ──────────────────────────────────────────────
# Admin/Operator Endpoints
# ──────────────────────────────────────────────

@router.get("/centre/{centre_id}/status", response_model=CentreQueueStatusResponse)
def get_centre_queue_status(
    centre_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # Centre-level authorization
    if admin.role.value == "CENTRE_OPERATOR" and admin.centre_id != centre_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this centre's queue.")
    if admin.role.value not in ["CENTRE_OPERATOR", "ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    today = date.today()
    active_counters = get_active_counter_count(db, centre_id)

    # Get today's bookings for this centre (active queue)
    bookings = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(
            Booking.centre_id == centre_id,
            Slot.date == today,
            Booking.status.notin_([BookingStatusEnum.COMPLETED, BookingStatusEnum.CANCELLED, BookingStatusEnum.NO_SHOW, BookingStatusEnum.SKIPPED]),
        )
        .order_by(Booking.token_number.asc())
        .all()
    )

    waiting_count, processing_count, serving_count = 0, 0, 0
    queue_entries = []
    pos = 1
    for b in bookings:
        status_str = b.status.value if hasattr(b.status, 'value') else b.status
        token_display = format_token_display(b.centre_id, b.token_number)

        # Counter name lookup
        counter_name = None
        if b.assigned_counter:
            counter = db.query(Counter).filter(Counter.id == b.assigned_counter).first()
            counter_name = counter.name if counter else f"Counter {b.assigned_counter}"

        if status_str in [s.value for s in WAITING_STATUSES]:
            waiting_count += 1
            wait_minutes = calculate_estimated_wait(pos - 1, active_counters)
            queue_entries.append(QueueEntry(
                token=b.token_number,
                token_display=token_display,
                booking_id=b.booking_id,
                farmer_name=b.farmer.name if b.farmer else "Farmer",
                crop=b.crop,
                produce_type=b.crop,
                quantity=b.expected_quantity,
                booking_time=b.created_at,
                status=status_str,
                arrival_time=b.arrival_time,
                queue_position=pos,
                assigned_counter=b.assigned_counter,
                counter_name=counter_name,
                estimated_wait_minutes=wait_minutes,
            ))
            pos += 1
        elif status_str in ["CALLED"]:
            processing_count += 1
            queue_entries.append(QueueEntry(
                token=b.token_number,
                token_display=token_display,
                booking_id=b.booking_id,
                farmer_name=b.farmer.name if b.farmer else "Farmer",
                crop=b.crop,
                produce_type=b.crop,
                quantity=b.expected_quantity,
                booking_time=b.created_at,
                status=status_str,
                arrival_time=b.arrival_time,
                queue_position=None,
                assigned_counter=b.assigned_counter,
                counter_name=counter_name,
                estimated_wait_minutes=0,
            ))
        elif status_str in ["SERVING", "PROCESSING"]:
            serving_count += 1
            queue_entries.append(QueueEntry(
                token=b.token_number,
                token_display=token_display,
                booking_id=b.booking_id,
                farmer_name=b.farmer.name if b.farmer else "Farmer",
                crop=b.crop,
                produce_type=b.crop,
                quantity=b.expected_quantity,
                booking_time=b.created_at,
                status=status_str,
                arrival_time=b.arrival_time,
                queue_position=None,
                assigned_counter=b.assigned_counter,
                counter_name=counter_name,
            ))


    completed_count = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == centre_id, Slot.date == today, Booking.status == BookingStatusEnum.COMPLETED)
        .count()
    )
    skipped_count = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == centre_id, Slot.date == today, Booking.status == BookingStatusEnum.SKIPPED)
        .count()
    )
    cancelled_count = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == centre_id, Slot.date == today, Booking.status == BookingStatusEnum.CANCELLED)
        .count()
    )

    return CentreQueueStatusResponse(
        centre_id=centre_id,
        waiting_count=waiting_count,
        processing_count=processing_count,
        serving_count=serving_count,
        completed_count=completed_count,
        skipped_count=skipped_count,
        cancelled_count=cancelled_count,
        active_counters=active_counters,
        is_paused=centre.is_paused,
        queue=queue_entries,
    )


@router.get("/centre/{centre_id}/stats", response_model=QueueStatsResponse)
def get_queue_stats(
    centre_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get today's queue statistics for a centre."""
    if admin.role.value == "CENTRE_OPERATOR" and admin.centre_id != centre_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this centre.")

    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    today = date.today()
    active_counters = get_active_counter_count(db, centre_id)

    # Base query for today's bookings at this centre
    base = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == centre_id, Slot.date == today)
    )

    total = base.count()
    waiting = base.filter(Booking.status.in_(WAITING_STATUSES)).count()
    serving = base.filter(Booking.status.in_([BookingStatusEnum.SERVING, BookingStatusEnum.PROCESSING, BookingStatusEnum.CALLED])).count()
    completed = base.filter(Booking.status == BookingStatusEnum.COMPLETED).count()
    skipped = base.filter(Booking.status == BookingStatusEnum.SKIPPED).count()
    cancelled = base.filter(Booking.status == BookingStatusEnum.CANCELLED).count()
    no_show = base.filter(Booking.status == BookingStatusEnum.NO_SHOW).count()

    # Average processing time (for completed bookings with both timestamps)
    avg_processing = 0.0
    completed_bookings = (
        base.filter(
            Booking.status == BookingStatusEnum.COMPLETED,
            Booking.serving_at.isnot(None),
            Booking.completed_at.isnot(None),
        ).all()
    )
    if completed_bookings:
        total_mins = sum(
            (b.completed_at - b.serving_at).total_seconds() / 60.0
            for b in completed_bookings
        )
        avg_processing = round(total_mins / len(completed_bookings), 1)

    # Average wait time (for bookings that have been called)
    avg_wait = 0.0
    called_bookings = (
        base.filter(
            Booking.call_time.isnot(None),
            Booking.created_at.isnot(None),
        ).all()
    )
    if called_bookings:
        total_wait = sum(
            (b.call_time - b.created_at).total_seconds() / 60.0
            for b in called_bookings
        )
        avg_wait = round(total_wait / len(called_bookings), 1)

    return QueueStatsResponse(
        centre_id=centre_id,
        total_bookings=total,
        waiting=waiting,
        serving=serving,
        completed=completed,
        skipped=skipped,
        cancelled=cancelled,
        no_show=no_show,
        active_counters=active_counters,
        average_processing_minutes=avg_processing,
        average_wait_minutes=avg_wait,
    )


@router.get("/admin/list", response_model=list[BookingDetailResponse])
def get_admin_queue(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    if admin.role.value not in ["CENTRE_OPERATOR", "ADMIN", "SUPER_ADMIN", "admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    query = db.query(Booking).filter(
        Booking.status.notin_([BookingStatusEnum.COMPLETED, BookingStatusEnum.CANCELLED])
    )

    # SUPER_ADMIN and ADMIN see all centres; operators see only their centre
    if admin.centre_id:
        query = query.filter(Booking.centre_id == admin.centre_id)

    bookings = query.order_by(Booking.token_number.asc()).all()

    return [BookingDetailResponse(
        booking_id=b.booking_id,
        token_number=b.token_number,
        centre=b.centre.name if b.centre else "Unknown",
        centre_id=b.centre_id,
        date=b.slot.date.isoformat(),
        time=f"{b.slot.start_time.strftime('%H:%M')}-{b.slot.end_time.strftime('%H:%M')}",
        crop=b.crop,
        quantity=b.expected_quantity,
        vehicle_number=b.vehicle_number,
        status=b.status.value if hasattr(b.status, 'value') else b.status
    ) for b in bookings]


from pydantic import BaseModel
class StatusUpdateRequest(BaseModel):
    status: BookingStatusEnum

@router.put("/admin/booking/{booking_id}/status")
async def update_booking_status(booking_id: str, req: StatusUpdateRequest, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.centre_id != admin.centre_id and admin.role.value != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
    booking.status = req.status
    db.commit()
    await broadcast_queue_update(booking.centre_id, db)
    return {"message": f"Status updated to {req.status}", "booking_id": booking_id}


@router.post("/admin/queue/pause")
async def pause_queue(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = admin.centre_id
    if not centre_id:
        raise HTTPException(status_code=400, detail="No centre assigned.")
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found.")
    centre.is_paused = True
    db.commit()
    await broadcast_queue_update(centre_id, db)
    return {"message": "Queue paused"}


@router.post("/admin/queue/resume")
async def resume_queue(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = admin.centre_id
    if not centre_id:
        raise HTTPException(status_code=400, detail="No centre assigned.")
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found.")
    centre.is_paused = False
    db.commit()
    await broadcast_queue_update(centre_id, db)
    return {"message": "Queue resumed"}


@router.post("/centres/{centre_id}/next")
@router.post("/admin/queue/next")
async def call_next_farmer(
    centre_id: Optional[int] = None,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Call the next eligible farmer in queue.
    Assigns an available counter, updates status to CALLED.
    Uses DB-level locking to prevent race conditions.
    """
    target_centre_id = centre_id or admin.centre_id
    if not target_centre_id:
        raise HTTPException(status_code=400, detail="No centre assigned.")

    if admin.role.value == "CENTRE_OPERATOR" and admin.centre_id != target_centre_id:
        raise HTTPException(status_code=403, detail="You are not authorized for this centre.")

    # Find next waiting farmer (ordered by token number)
    today = date.today()
    query = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(
            Booking.centre_id == target_centre_id,
            Slot.date == today,
            Booking.status.in_(WAITING_STATUSES),
        )
        .order_by(Booking.token_number.asc())
    )
    try:
        query = query.with_for_update()  # Row-level lock
    except Exception:
        pass

    next_booking = query.first()

    if not next_booking:
        return {"message": "No farmers in queue", "booking": None}

    # Find available counter
    counter = get_available_counter(db, target_centre_id)
    counter_name = None
    counter_num = 1

    if counter:
        counter.status = CounterStatusEnum.BUSY
        counter.current_booking_id = next_booking.id
        counter.is_available = False
        next_booking.assigned_counter = counter.id
        counter_name = counter.name
        counter_num = counter.id

    next_booking.status = BookingStatusEnum.CALLED
    next_booking.call_time = datetime.utcnow()

    db.commit()
    db.refresh(next_booking)

    token_str = format_token_display(target_centre_id, next_booking.token_number)

    # Send notification to farmer
    try:
        counter_info = f" at {counter_name}" if counter_name else ""
        send_notification(
            db,
            user_id=next_booking.farmer_id,
            title="🔔 Your Token Has Been Called!",
            message=f"Token {token_str} has been called{counter_info}. Please proceed immediately.",
            type_str="QUEUE_CALL",
        )
    except Exception:
        pass

    await broadcast_queue_update(target_centre_id, db, event="FARMER_CALLED", extra={
        "token": next_booking.token_number,
        "token_display": token_str,
        "booking_id": next_booking.booking_id,
        "status": "CALLED",
        "counter_name": counter_name,
        "counter_number": counter_num,
    })

    return {
        "message": "Next farmer called",
        "booking_id": next_booking.booking_id,
        "token_number": token_str,
        "token_display": token_str,
        "status": next_booking.status.value,
        "counter_number": counter_num,
        "counter": counter_name,
    }


@router.post("/{booking_id}/start")
@router.post("/admin/booking/{booking_id}/start")
async def start_serving(
    booking_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """CALLED → SERVING. Sets serving_at timestamp."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if admin.role.value == "CENTRE_OPERATOR" and booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status not in [BookingStatusEnum.CALLED]:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot start serving. Current status: {booking.status.value if hasattr(booking.status, 'value') else booking.status}",
        )

    booking.status = BookingStatusEnum.SERVING
    booking.serving_at = datetime.utcnow()
    db.commit()

    # Notify farmer
    try:
        token_display = format_token_display(booking.centre_id, booking.token_number)
        counter_name = "your counter"
        if booking.assigned_counter:
            counter = db.query(Counter).filter(Counter.id == booking.assigned_counter).first()
            counter_name = counter.name if counter else f"Counter {booking.assigned_counter}"
        send_notification(
            db,
            user_id=booking.farmer_id,
            title="🟢 Serving Started",
            message=f"Token {token_display} is now being served at {counter_name}.",
            type_str="SERVING_STARTED",
        )
    except Exception:
        pass

    await broadcast_queue_update(booking.centre_id, db, event="SERVING_STARTED", extra={
        "booking_id": booking.booking_id,
        "token_display": format_token_display(booking.centre_id, booking.token_number),
        "status": "SERVING",
    })

    return {"message": "Serving started", "status": booking.status.value}


@router.post("/{booking_id}/complete")
@router.post("/admin/booking/{booking_id}/complete")
async def complete_processing(
    booking_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """SERVING/PROCESSING → COMPLETED. Frees the counter."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if admin.role.value == "CENTRE_OPERATOR" and booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status not in [BookingStatusEnum.SERVING, BookingStatusEnum.PROCESSING]:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot complete. Current status: {booking.status.value if hasattr(booking.status, 'value') else booking.status}",
        )

    booking.status = BookingStatusEnum.COMPLETED
    booking.completed_at = datetime.utcnow()

    # Free the counter
    if booking.assigned_counter:
        counter = db.query(Counter).filter(Counter.id == booking.assigned_counter).first()
        if counter:
            counter.status = CounterStatusEnum.ACTIVE
            counter.current_booking_id = None
            counter.is_available = True

    db.commit()

    # Notify farmer
    try:
        token_display = format_token_display(booking.centre_id, booking.token_number)
        send_notification(
            db,
            user_id=booking.farmer_id,
            title="✅ Procurement Completed",
            message=f"Token {token_display}: Your procurement has been completed successfully.",
            type_str="COMPLETED",
        )
    except Exception:
        pass

    await broadcast_queue_update(booking.centre_id, db, event="COMPLETED", extra={
        "booking_id": booking.booking_id,
        "token_display": format_token_display(booking.centre_id, booking.token_number),
        "status": "COMPLETED",
    })

    return {"message": "Processing completed", "status": booking.status.value}


@router.post("/{booking_id}/skip")
@router.post("/admin/booking/{booking_id}/skip")
async def skip_farmer(
    booking_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """CALLED → SKIPPED. Frees the counter."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if admin.role.value == "CENTRE_OPERATOR" and booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status != BookingStatusEnum.CALLED:
        raise HTTPException(
            status_code=409,
            detail=f"Only CALLED farmers can be skipped. Current status: {booking.status.value if hasattr(booking.status, 'value') else booking.status}",
        )

    booking.status = BookingStatusEnum.SKIPPED

    # Free the counter
    if booking.assigned_counter:
        counter = db.query(Counter).filter(Counter.id == booking.assigned_counter).first()
        if counter:
            counter.status = CounterStatusEnum.ACTIVE
            counter.current_booking_id = None
            counter.is_available = True

    db.commit()

    # Notify farmer
    try:
        token_display = format_token_display(booking.centre_id, booking.token_number)
        send_notification(
            db,
            user_id=booking.farmer_id,
            title="⚠️ Token Skipped",
            message=f"Token {token_display} was skipped. Please contact the centre desk for assistance.",
            type_str="SKIPPED",
        )
    except Exception:
        pass

    await broadcast_queue_update(booking.centre_id, db, event="SKIPPED", extra={
        "booking_id": booking.booking_id,
        "token_display": format_token_display(booking.centre_id, booking.token_number),
        "status": "SKIPPED",
    })

    return {"message": "Farmer skipped", "status": booking.status.value}


@router.post("/admin/booking/{booking_id}/no_show")
async def mark_no_show(booking_id: str, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.centre_id != admin.centre_id and admin.role.value != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status != BookingStatusEnum.CALLED:
        raise HTTPException(status_code=409, detail="Only CALLED farmers can be marked as NO_SHOW.")

    booking.status = BookingStatusEnum.NO_SHOW

    # Free the counter
    if booking.assigned_counter:
        counter = db.query(Counter).filter(Counter.id == booking.assigned_counter).first()
        if counter:
            counter.status = CounterStatusEnum.ACTIVE
            counter.current_booking_id = None
            counter.is_available = True

    db.commit()
    await broadcast_queue_update(booking.centre_id, db)
    return {"message": "Farmer marked as No Show", "status": booking.status.value}


@router.post("/booking/{booking_id}/cancel")
async def cancel_booking(booking_id: str, farmer: Farmer = Depends(get_current_farmer), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.farmer_id != farmer.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status in [BookingStatusEnum.PROCESSING, BookingStatusEnum.SERVING, BookingStatusEnum.COMPLETED, BookingStatusEnum.CANCELLED, BookingStatusEnum.NO_SHOW]:
        raise HTTPException(status_code=409, detail="Cannot cancel a booking in this state.")

    booking.status = BookingStatusEnum.CANCELLED

    # Free counter if assigned
    if booking.assigned_counter:
        counter = db.query(Counter).filter(Counter.id == booking.assigned_counter).first()
        if counter:
            counter.status = CounterStatusEnum.ACTIVE
            counter.current_booking_id = None
            counter.is_available = True

    if booking.slot:
        booking.slot.booked_count = max(0, booking.slot.booked_count - 1)

    db.commit()
    await broadcast_queue_update(booking.centre_id, db)
    return {"message": "Booking cancelled", "status": booking.status.value}
