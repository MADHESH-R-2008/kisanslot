from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer
from schemas import FarmerRegisterRequest, FarmerLoginRequest, TokenResponse, FarmerBrief
from auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: FarmerRegisterRequest, db: Session = Depends(get_db)):
    """Register a new farmer and return a JWT token."""

    # Check if mobile already exists
    existing = db.query(Farmer).filter(Farmer.mobile == req.mobile).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A farmer with this mobile number is already registered.",
        )

    # Check if farmer_id already exists
    existing_fid = db.query(Farmer).filter(Farmer.farmer_id == req.farmer_id).first()
    if existing_fid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A farmer with this Farmer ID is already registered.",
        )

    # Create farmer
    farmer = Farmer(
        name=req.name,
        mobile=req.mobile,
        farmer_id=req.farmer_id,
        village=req.village,
        district=req.district,
        state=req.state,
        crop=req.crop,
        expected_quantity=req.expected_quantity,
        password_hash=hash_password(req.password),
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    # Generate JWT
    token = create_access_token(data={"sub": str(farmer.id)})

    return TokenResponse(
        access_token=token,
        farmer=FarmerBrief(id=farmer.id, name=farmer.name, farmer_id=farmer.farmer_id),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: FarmerLoginRequest, db: Session = Depends(get_db)):
    """Authenticate a farmer and return a JWT token."""

    farmer = db.query(Farmer).filter(Farmer.mobile == req.mobile).first()
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this mobile number.",
        )

    if not verify_password(req.password, farmer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password. Please try again.",
        )

    token = create_access_token(data={"sub": str(farmer.id)})

    return TokenResponse(
        access_token=token,
        farmer=FarmerBrief(id=farmer.id, name=farmer.name, farmer_id=farmer.farmer_id),
    )
