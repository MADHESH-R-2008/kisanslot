from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer
from schemas import FarmerResponse, FarmerUpdateRequest
from auth import get_current_farmer

router = APIRouter(prefix="/api/farmers", tags=["Farmers"])


@router.get("/me", response_model=FarmerResponse)
def get_profile(farmer: Farmer = Depends(get_current_farmer)):
    """Return the logged-in farmer's profile."""
    return farmer


@router.put("/me", response_model=FarmerResponse)
def update_profile(
    req: FarmerUpdateRequest,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Update the logged-in farmer's profile fields."""
    if req.name is not None:
        farmer.name = req.name
    if req.village is not None:
        farmer.village = req.village
    if req.district is not None:
        farmer.district = req.district
    if req.state is not None:
        farmer.state = req.state
    if req.crop is not None:
        farmer.crop = req.crop
    if req.expected_quantity is not None:
        farmer.expected_quantity = req.expected_quantity

    db.commit()
    db.refresh(farmer)
    return farmer
