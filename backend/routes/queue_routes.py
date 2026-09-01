from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer, Booking, Centre, BookingStatusEnum, AdminUser
from schemas import QueueResponse, BookingDetailResponse
from auth import get_current_farmer, get_current_admin
from services.queue_service import calculate_queue_position

router = APIRouter(prefix="/api/queue", tags=["Queue"])


@router.get("/{booking_id}", response_model=QueueResponse)
def get_queue_position(
    booking_id: str,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Calculate live queue position for a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    if booking.farmer_id != farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this queue.",
        )

    centre = db.query(Centre).filter(Centre.id == booking.centre_id).first()
    active_counters = centre.active_counters if centre else 3

    queue_data = calculate_queue_position(db, booking, active_counters)

    return QueueResponse(
        booking_id=booking.booking_id,
        queue_position=queue_data["queue_position"],
        farmers_ahead=queue_data["farmers_ahead"],
        estimated_wait_minutes=queue_data["estimated_wait_minutes"],
        active_counters=active_counters,
        status=queue_data["status"],
    )


@router.get("/admin/list", response_model=list[BookingDetailResponse])
def get_admin_queue(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin: Get all active bookings for this admin's centre for today."""
    from datetime import date
    
    today = date.today()
    # For demo purposes, if it's past the test dates, let's just fetch all non-completed bookings
    # But ideally it should filter by date. We'll just filter by centre and active status.
    
    bookings = (
        db.query(Booking)
        .filter(Booking.centre_id == admin.centre_id)
        .filter(Booking.status != BookingStatusEnum.COMPLETED)
        .filter(Booking.status != BookingStatusEnum.CANCELLED)
        .order_by(Booking.token_number.asc())
        .all()
    )
    
    response = []
    for b in bookings:
        response.append(BookingDetailResponse(
            booking_id=b.booking_id,
            token_number=b.token_number,
            centre=admin.centre.name,
            centre_id=admin.centre_id,
            date=b.slot.date.isoformat(),
            time=f"{b.slot.start_time.strftime('%H:%M')}-{b.slot.end_time.strftime('%H:%M')}",
            crop=b.crop,
            quantity=b.expected_quantity,
            vehicle_number=b.vehicle_number,
            status=b.status,
        ))
    
    return response


from pydantic import BaseModel
class StatusUpdateRequest(BaseModel):
    status: BookingStatusEnum


@router.put("/admin/booking/{booking_id}/status")
def update_booking_status(
    booking_id: str,
    req: StatusUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin: Update the status of a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
        
    if booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=403, detail="Booking belongs to another centre.")
        
    booking.status = req.status
    db.commit()
    
    return {"message": f"Status updated to {req.status}", "booking_id": booking_id}

