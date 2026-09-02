from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import Farmer, Booking, Centre, BookingStatusEnum, AdminUser
from schemas import QueueResponse, BookingDetailResponse, CentreQueueStatusResponse, QueueEntry
from auth import get_current_farmer
from dependencies import get_current_admin, require_admin_or_super
from services.queue_service import calculate_queue_position
from routes.ws_routes import manager

router = APIRouter(prefix="/api/queue", tags=["Queue"])

async def broadcast_queue_update(centre_id: int, db: Session):
    """Helper to recalculate basic stats and broadcast."""
    waiting_count = db.query(Booking).filter(
        Booking.centre_id == centre_id,
        Booking.status.in_([BookingStatusEnum.WAITING, BookingStatusEnum.ARRIVED, BookingStatusEnum.CONFIRMED])
    ).count()
    
    await manager.broadcast({
        "event": "QUEUE_UPDATED",
        "centre_id": centre_id,
        "waiting_count": waiting_count,
        "is_paused": db.query(Centre).filter(Centre.id == centre_id).first().is_paused
    }, centre_id)

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

@router.get("/centre/{centre_id}/status", response_model=CentreQueueStatusResponse)
def get_centre_queue_status(
    centre_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if admin.centre_id and admin.centre_id != centre_id and admin.role.value != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
        
    bookings = (db.query(Booking).filter(Booking.centre_id == centre_id)
        .filter(Booking.status.not_in([BookingStatusEnum.COMPLETED, BookingStatusEnum.CANCELLED]))
        .order_by(Booking.token_number.asc()).all())
    
    waiting_count, processing_count = 0, 0
    queue_entries = []
    pos = 1
    for b in bookings:
        status_str = b.status.value if hasattr(b.status, 'value') else b.status
        if status_str in ["WAITING", "ARRIVED", "CONFIRMED"]:
            waiting_count += 1
            queue_entries.append(QueueEntry(token=b.token_number, booking_id=b.booking_id, farmer_name=b.farmer.name, status=status_str, arrival_time=b.arrival_time, queue_position=pos))
            pos += 1
        elif status_str in ["CALLED", "PROCESSING"]:
            processing_count += 1
            queue_entries.append(QueueEntry(token=b.token_number, booking_id=b.booking_id, farmer_name=b.farmer.name, status=status_str, arrival_time=b.arrival_time, queue_position=None))
            
    completed_count = db.query(Booking).filter(Booking.centre_id == centre_id, Booking.status == BookingStatusEnum.COMPLETED).count()
    return CentreQueueStatusResponse(
        centre_id=centre_id,
        waiting_count=waiting_count,
        processing_count=processing_count,
        completed_count=completed_count,
        active_counters=centre.active_counters,
        is_paused=centre.is_paused,
        queue=queue_entries,
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
@router.post("/admin/queue/next")
async def call_next_farmer(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    from datetime import datetime
    centre_id = admin.centre_id
    if not centre_id: raise HTTPException(status_code=400, detail="No centre assigned.")
    next_booking = db.query(Booking).filter(Booking.centre_id == centre_id, Booking.status.in_([BookingStatusEnum.ARRIVED, BookingStatusEnum.WAITING, BookingStatusEnum.CONFIRMED])).order_by(Booking.token_number.asc()).first()
    if not next_booking: return {"message": "No farmers in queue", "booking": None}
    next_booking.status = BookingStatusEnum.CALLED
    next_booking.call_time = datetime.utcnow()
    db.commit()
    db.refresh(next_booking)
    await broadcast_queue_update(centre_id, db)
    return {"message": "Next farmer called", "booking_id": next_booking.booking_id, "token_number": next_booking.token_number, "status": next_booking.status.value}

@router.post("/admin/booking/{booking_id}/start")
async def start_processing(booking_id: str, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db), _=Depends(require_admin_or_super())):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking: raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.centre_id != admin.centre_id and admin.role.value != "SUPER_ADMIN": raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status != BookingStatusEnum.CALLED: raise HTTPException(status_code=400, detail=f"Cannot start processing. Current status: {booking.status}")
    booking.status = BookingStatusEnum.PROCESSING
    db.commit()
    await broadcast_queue_update(booking.centre_id, db)
    return {"message": "Processing started", "status": booking.status.value}

@router.post("/admin/booking/{booking_id}/complete")
async def complete_processing(booking_id: str, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db), _=Depends(require_admin_or_super())):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking: raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.centre_id != admin.centre_id and admin.role.value != "SUPER_ADMIN": raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status != BookingStatusEnum.PROCESSING: raise HTTPException(status_code=400, detail=f"Cannot complete. Current status: {booking.status}")
    booking.status = BookingStatusEnum.COMPLETED
    db.commit()
    await broadcast_queue_update(booking.centre_id, db)
    return {"message": "Processing completed", "status": booking.status.value}

@router.post("/admin/booking/{booking_id}/no_show")
async def mark_no_show(booking_id: str, admin: AdminUser = Depends(require_admin_or_super()), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking: raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.centre_id != admin.centre_id and admin.role.value != "SUPER_ADMIN": raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status != BookingStatusEnum.CALLED: raise HTTPException(status_code=400, detail="Only CALLED farmers can be marked as NO_SHOW.")
    booking.status = BookingStatusEnum.NO_SHOW
    db.commit()
    await broadcast_queue_update(booking.centre_id, db)
    return {"message": "Farmer marked as No Show", "status": booking.status.value}

@router.post("/booking/{booking_id}/cancel")
async def cancel_booking(booking_id: str, farmer: Farmer = Depends(get_current_farmer), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking: raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.farmer_id != farmer.id: raise HTTPException(status_code=403, detail="Unauthorized")
    if booking.status in [BookingStatusEnum.PROCESSING, BookingStatusEnum.COMPLETED, BookingStatusEnum.CANCELLED, BookingStatusEnum.NO_SHOW]: raise HTTPException(status_code=400, detail="Cannot cancel a booking in this state.")
    booking.status = BookingStatusEnum.CANCELLED
    if booking.slot: booking.slot.booked_count = max(0, booking.slot.booked_count - 1)
    db.commit()
    await broadcast_queue_update(booking.centre_id, db)
    return {"message": "Booking cancelled", "status": booking.status.value}
