from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Counter, AdminUser, Centre
from schemas import CounterResponse, CounterCreateRequest, CounterUpdateRequest
from auth import get_current_admin

router = APIRouter(prefix="/api/counters", tags=["Counters"])

@router.get("/", response_model=list[CounterResponse])
def list_counters(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = admin.centre_id
    if not centre_id:
        raise HTTPException(status_code=400, detail="Admin not assigned to a centre")
    counters = db.query(Counter).filter(Counter.centre_id == centre_id, Counter.is_deleted == False).all()
    return counters

@router.post("/", response_model=CounterResponse)
def create_counter(req: CounterCreateRequest, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = admin.centre_id
    if not centre_id:
        raise HTTPException(status_code=400, detail="Admin not assigned to a centre")
    counter = Counter(
        centre_id=centre_id,
        name=req.name,
        status=req.status if req.status else "ACTIVE",
        is_available=req.is_available if req.is_available is not None else True,
    )
    db.add(counter)
    db.commit()
    db.refresh(counter)
    return counter

@router.put("/{counter_id}", response_model=CounterResponse)
def update_counter(counter_id: int, req: CounterUpdateRequest, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = admin.centre_id
    counter = db.query(Counter).filter(Counter.id == counter_id, Counter.centre_id == centre_id, Counter.is_deleted == False).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    if req.name is not None:
        counter.name = req.name
    if req.status is not None:
        counter.status = req.status
    if req.is_available is not None:
        counter.is_available = req.is_available
    db.commit()
    db.refresh(counter)
    return counter

@router.delete("/{counter_id}")
def delete_counter(counter_id: int, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = admin.centre_id
    counter = db.query(Counter).filter(Counter.id == counter_id, Counter.centre_id == centre_id, Counter.is_deleted == False).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    counter.is_deleted = True
    db.commit()
    return {"message": "Counter soft‑deleted"}
