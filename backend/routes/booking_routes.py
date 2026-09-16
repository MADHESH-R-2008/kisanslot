from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer, Booking, Slot, Centre, BookingStatusEnum
from schemas import BookingCreateRequest, BookingResponse, BookingDetailResponse
from auth import get_current_farmer
from services.booking_service import generate_booking_id, generate_token_number, format_token_display
from services.notification_service import send_notification

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

    # 4. Check slot capacity
    if slot.booked_count >= slot.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot is already full. Please choose another time slot.",
        )

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active booking for this slot.",
        )

    # 6. Generate booking ID and token number
    booking_id = generate_booking_id(db)
    token_number = generate_token_number(db, req.slot_id, centre_id=req.centre_id)

    # 7. Create booking
    booking = Booking(
        booking_id=booking_id,
        farmer_id=farmer.id,
        centre_id=req.centre_id,
        slot_id=req.slot_id,
        crop=req.crop,
        expected_quantity=req.expected_quantity,
        vehicle_number=req.vehicle_number.upper(),
        token_number=token_number,
        status=BookingStatusEnum.CONFIRMED,
    )
    db.add(booking)

    # 8. Increment booked count on the slot
    slot.booked_count += 1

    db.commit()
    db.refresh(booking)

    # 9. Auto-create procurement and payment records
    from models import Procurement, Payment, ProcurementStatusEnum, PaymentStatusEnum

    procurement = Procurement(
        booking_id=booking.id,
        quality_status="PENDING",
        rate=21.50,
        status=ProcurementStatusEnum.PENDING,
    )
    payment = Payment(
        booking_id=booking.id,
        amount=req.expected_quantity * 21.50,
        status=PaymentStatusEnum.PENDING,
    )
    db.add(procurement)
    db.add(payment)
    db.commit()

    # 10. Send notification to farmer
    try:
        token_display = format_token_display(req.centre_id, token_number)
        send_notification(
            db,
            user_id=farmer.id,
            title="📅 Booking Confirmed",
            message=f"Token {token_display} confirmed at {centre.name} for {slot.date.strftime('%d %b %Y')} {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}.",
            type_str="BOOKING_CONFIRMED",
        )
    except Exception:
        pass

    # 11. Broadcast queue update via WebSocket
    try:
        from routes.ws_routes import manager
        import json
        await manager.broadcast({
            "event": "BOOKING_CREATED",
            "centre_id": req.centre_id,
            "token": token_number,
            "token_display": format_token_display(req.centre_id, token_number),
            "booking_id": booking.booking_id,
        }, req.centre_id)
    except Exception:
        pass

    return BookingResponse(
        booking_id=booking.booking_id,
        token_number=booking.token_number,
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
        centre=centre.name if centre else "Unknown",
        centre_id=booking.centre_id,
        date=slot.date.strftime("%Y-%m-%d") if slot else "",
        time=f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}" if slot else "",
        crop=booking.crop,
        quantity=booking.expected_quantity,
        vehicle_number=booking.vehicle_number,
        status=booking.status.value,
    )


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
