from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer, Booking, Slot, Centre, BookingStatusEnum
from schemas import BookingCreateRequest, BookingResponse, BookingDetailResponse
from auth import get_current_farmer
from services.booking_service import allocate_token_number, generate_booking_id, format_token_display
from services.notification_service import create_notification

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    req: BookingCreateRequest,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Create a new booking with full validation."""

    # 1. Verify centre exists and is active
    centre = db.query(Centre).filter(Centre.id == req.centre_id, Centre.is_active == True).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement centre not found or is inactive.",
        )

    # 2. Verify slot exists and is active
    slot = db.query(Slot).filter(Slot.id == req.slot_id, Slot.is_active == True).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found or is inactive.",
        )

    # 3. Verify slot belongs to the centre
    if slot.centre_id != req.centre_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This slot does not belong to the selected centre.",
        )

    if slot.date < date.today() or (slot.date == date.today() and slot.end_time <= datetime.now().time()):
        raise HTTPException(status_code=400, detail="This slot has expired.")

    # 4. Atomically reserve capacity. The conditional UPDATE prevents overbooking.
    reserved = db.query(Slot).filter(
        Slot.id == req.slot_id,
        Slot.is_active.is_(True),
        Slot.booked_count < Slot.capacity,
    ).update({Slot.booked_count: Slot.booked_count + 1}, synchronize_session=False)
    if reserved != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot is no longer available.",
        )
    db.refresh(slot)

    # 5. Check for duplicate active booking (same farmer, same slot)
    existing = (
        db.query(Booking)
        .filter(
            Booking.farmer_id == farmer.id,
            Booking.slot_id == req.slot_id,
            Booking.status.notin_([
                BookingStatusEnum.COMPLETED,
                BookingStatusEnum.CANCELLED,
            ]),
        )
        .first()
    )
    if existing:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active booking for this slot.",
        )

    # 6. Generate booking ID and token number
    booking_id = generate_booking_id(db)
    token_number = allocate_token_number(db, req.centre_id, slot.date)

    # 7. Create booking
    booking = Booking(
        booking_id=booking_id,
        farmer_id=farmer.id,
        centre_id=req.centre_id,
        slot_id=req.slot_id,
        booking_date=slot.date,
        crop=req.crop,
        expected_quantity=req.expected_quantity,
        vehicle_number=req.vehicle_number.upper(),
        token_number=token_number,
        status=BookingStatusEnum.CONFIRMED,
    )
    db.add(booking)
    db.flush()

    # 8. Create dependent records in the same transaction.
    from models import Procurement, Payment, ProcurementStatusEnum, PaymentStatusEnum

    procurement = Procurement(
        booking_id=booking.id,
        quality_status="PENDING",
        rate=21.50,
        status=ProcurementStatusEnum.PENDING,
    )
    payment = Payment(
        booking_id=booking.id,
        amount=None,
        status=PaymentStatusEnum.PENDING,
    )
    db.add(procurement)
    db.add(payment)
    token_display = format_token_display(req.centre_id, token_number)
    try:
        create_notification(
            db=db,
            user_id=farmer.id,
            notification_type="BOOKING_CONFIRMED",
            title="Booking Confirmed",
            message=f"Your slot at {centre.name} has been confirmed.\nToken: {token_display}",
            booking_id=booking.id,
            centre_id=centre.id,
            commit=False,
        )
        db.commit()
        db.refresh(booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Booking conflict. Please try again.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to complete booking.")

    # 11. Broadcast queue update via WebSocket
    try:
        from routes.ws_routes import manager
        import json
        await manager.broadcast({
            "event": "BOOKING_CREATED",
            "centre_id": req.centre_id,
            "token": token_number,
            "token_display": token_display,
            "booking_id": booking.booking_id,
        }, req.centre_id)
    except Exception:
        pass

    return BookingResponse(
        booking_id=booking.booking_id,
        token_number=booking.token_number,
        token_display=format_token_display(booking.centre_id, booking.token_number),
        status=booking.status.value,
        centre=centre.name,
        date=slot.date.strftime("%Y-%m-%d"),
        start_time=slot.start_time.strftime("%H:%M"),
        end_time=slot.end_time.strftime("%H:%M"),
        crop=booking.crop,
        expected_quantity=booking.expected_quantity,
        vehicle_number=booking.vehicle_number,
        created_at=booking.created_at,
    )


@router.get("/my", response_model=list[BookingDetailResponse])
@router.get("", response_model=list[BookingDetailResponse])
def list_my_bookings(
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Return all bookings for the logged-in farmer."""
    bookings = (
        db.query(Booking)
        .filter(Booking.farmer_id == farmer.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    result = []
    for booking in bookings:
        slot = db.query(Slot).filter(Slot.id == booking.slot_id).first()
        centre = db.query(Centre).filter(Centre.id == booking.centre_id).first()
        result.append(
            BookingDetailResponse(
                booking_id=booking.booking_id,
                token_number=booking.token_number,
                token_display=format_token_display(booking.centre_id, booking.token_number),
                centre=centre.name if centre else "Unknown",
                centre_id=booking.centre_id,
                date=slot.date.strftime("%Y-%m-%d") if slot else "",
                time=f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}" if slot else "",
                crop=booking.crop,
                quantity=booking.expected_quantity,
                vehicle_number=booking.vehicle_number,
                status=booking.status.value,
            )
        )

    return result


@router.get("/{booking_id}", response_model=BookingDetailResponse)
def get_booking(
    booking_id: str,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Return booking details. Only the owner can access their booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    # Authorization: only the owner
    if booking.farmer_id != farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this booking.",
        )

    slot = db.query(Slot).filter(Slot.id == booking.slot_id).first()
    centre = db.query(Centre).filter(Centre.id == booking.centre_id).first()

    return BookingDetailResponse(
        booking_id=booking.booking_id,
        token_number=booking.token_number,
        token_display=format_token_display(booking.centre_id, booking.token_number),
        centre=centre.name if centre else "Unknown",
        centre_id=booking.centre_id,
        date=slot.date.strftime("%Y-%m-%d") if slot else "",
        time=f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}" if slot else "",
        crop=booking.crop,
        quantity=booking.expected_quantity,
        vehicle_number=booking.vehicle_number,
        status=booking.status.value,
    )


@router.put("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Cancel a booking by booking_id."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if booking.farmer_id != farmer.id:
        raise HTTPException(status_code=403, detail="You are not authorized to cancel this booking.")

    terminal_statuses = [
        BookingStatusEnum.COMPLETED,
        BookingStatusEnum.CANCELLED,
        BookingStatusEnum.SERVING,
        BookingStatusEnum.PROCESSING,
        BookingStatusEnum.NO_SHOW,
    ]
    if booking.status in terminal_statuses:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel booking with current status '{booking.status.value}'.",
        )

    booking.status = BookingStatusEnum.CANCELLED

    if booking.slot:
        booking.slot.booked_count = max(0, booking.slot.booked_count - 1)

    db.commit()

    try:
        from routes.queue_routes import broadcast_queue_update
        await broadcast_queue_update(booking.centre_id, db, event="BOOKING_CANCELLED", extra={
            "booking_id": booking.booking_id,
            "status": "CANCELLED",
        })
    except Exception:
        pass

    return {
        "message": "Booking cancelled successfully",
        "booking_id": booking_id,
        "status": booking.status.value,
    }
