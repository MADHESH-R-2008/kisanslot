from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from models import Farmer, AdminUser
from schemas import (
    FarmerRegisterRequest, FarmerLoginRequest, TokenResponse, FarmerBrief,
    AdminLoginRequest, AdminTokenResponse, MasterPasswordResetRequest,
    RefreshTokenRequest,
)
from auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_refresh_token, get_current_master_admin,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _farmer_tokens(farmer: Farmer) -> TokenResponse:
    claims = {"sub": str(farmer.id), "user_id": farmer.id, "role": "FARMER", "centre_id": None}
    return TokenResponse(
        access_token=create_access_token(data=claims),
        refresh_token=create_refresh_token(data=claims),
        farmer=FarmerBrief(id=farmer.id, name=farmer.name, farmer_id=farmer.farmer_id),
    )


@router.get("/init-db", tags=["System"])
@router.post("/init-db", tags=["System"])
def init_database():
    try:
        from database import engine, Base, ensure_schema_up_to_date
        Base.metadata.create_all(bind=engine)
        migration_results = ensure_schema_up_to_date(engine)
        from seed import seed
        seed()
        return {"status": "success", "message": "Database tables created and seeded successfully!", "migration_results": migration_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")


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
    return _farmer_tokens(farmer)


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

    return _farmer_tokens(farmer)


@router.post("/refresh", response_model=TokenResponse)
def refresh_farmer_session(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Issue a new access/refresh pair for an existing farmer session."""
    payload = decode_refresh_token(req.refresh_token)
    farmer = db.query(Farmer).filter(Farmer.id == int(payload["sub"])).first()
    if not farmer:
        raise HTTPException(status_code=401, detail="Farmer account no longer exists.")
    return _farmer_tokens(farmer)


@router.post("/admin/login", response_model=AdminTokenResponse)
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    """Authenticate an AdminUser and return a JWT token."""
    clean_username = req.username.strip()
    admin = db.query(AdminUser).filter(func.lower(AdminUser.username) == func.lower(clean_username)).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is inactive.")

    if not verify_password(req.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    # Note the 'role' field we added to the JWT payload in auth.py
    role_str = admin.role.value if hasattr(admin.role, 'value') else admin.role
    token = create_access_token(data={
        "sub": str(admin.id),
        "user_id": admin.id,
        "role": role_str,
        "centre_id": admin.centre_id,
        "district_id": admin.district_id,
    })

    return AdminTokenResponse(
        access_token=token,
        centre_id=admin.centre_id,
        district_id=admin.district_id,
        role=role_str
    )

class UnifiedLoginRequest(BaseModel):
    mobile: Optional[str] = None
    username: Optional[str] = None
    password: str

@router.post("/unified-login")
def unified_login(req: UnifiedLoginRequest, db: Session = Depends(get_db)):
    """Unified login supporting both farmer (mobile) and admin (username) authentication.
    Returns appropriate token response based on credentials.
    """
    if req.mobile:
        farmer = db.query(Farmer).filter(Farmer.mobile == req.mobile.strip()).first()
        if not farmer:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No farmer account found with this mobile number.")
        if not verify_password(req.password, farmer.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password for farmer account.")
        return _farmer_tokens(farmer)
    elif req.username:
        clean_username = req.username.strip()
        admin = db.query(AdminUser).filter(func.lower(AdminUser.username) == func.lower(clean_username)).first()
        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin username.")
        if not admin.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is inactive.")
        if not verify_password(req.password, admin.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password for admin account.")
        role_str = admin.role.value if hasattr(admin.role, 'value') else admin.role
        token = create_access_token(data={
            "sub": str(admin.id),
            "user_id": admin.id,
            "role": role_str,
            "centre_id": admin.centre_id,
            "district_id": admin.district_id,
        })
        return AdminTokenResponse(access_token=token, centre_id=admin.centre_id, district_id=admin.district_id, role=role_str)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide either mobile (farmer) or username (admin) for login.")


@router.post("/reset-admin", tags=["System"])
@router.get("/reset-admin", tags=["System"])
def reset_admin_credentials(
    db: Session = Depends(get_db),
):
    """Reset admin and centre operator credentials & assigned centre IDs."""
    from models import Centre, RoleEnum
    centres = db.query(Centre).all()
    if not centres:
        from seed import seed
        seed()
        centres = db.query(Centre).all()

    centre_c = db.query(Centre).filter(Centre.code == "CTR-C").first() or (centres[2] if len(centres) > 2 else centres[0])
    centre_a = db.query(Centre).filter(Centre.code == "CTR-A").first() or centres[0]
    centre_b = db.query(Centre).filter(Centre.code == "CTR-B").first() or (centres[1] if len(centres) > 1 else centres[0])

    users_to_reset = [
        {"username": "operator1", "password": "op123", "role": RoleEnum.CENTRE_OPERATOR, "centre_id": centre_c.id},
        {"username": "operator_a", "password": "op123", "role": RoleEnum.CENTRE_OPERATOR, "centre_id": centre_a.id},
        {"username": "operator_b", "password": "op123", "role": RoleEnum.CENTRE_OPERATOR, "centre_id": centre_b.id},
        {"username": "admin", "password": "admin123", "role": RoleEnum.ADMIN, "centre_id": centre_c.id},
        {"username": "super", "password": "super123", "role": RoleEnum.SUPER_ADMIN, "centre_id": None},
        {"username": "master", "password": "master123", "role": RoleEnum.SUPER_ADMIN, "centre_id": None},
    ]

    reset_summary = []
    for u in users_to_reset:
        user = db.query(AdminUser).filter(AdminUser.username == u["username"]).first()
        if not user:
            user = AdminUser(
                username=u["username"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
                centre_id=u["centre_id"],
            )
            db.add(user)
        else:
            user.password_hash = hash_password(u["password"])
            user.role = u["role"]
            user.centre_id = u["centre_id"]
            user.is_active = True
        reset_summary.append({
            "username": u["username"],
            "password": u["password"],
            "role": u["role"].value if hasattr(u["role"], 'value') else u["role"],
            "centre_id": u["centre_id"],
        })

    db.commit()
    return {
        "status": "Admin and Centre Operator credentials reset successfully",
        "accounts": reset_summary,
    }


@router.post("/master/reset-operator-password", tags=["Authentication"])
def master_reset_operator_password(
    req: MasterPasswordResetRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_master_admin),
):
    """Master Admin endpoint to reset password for any operator or admin account."""
    clean_username = req.username.strip()
    target_user = db.query(AdminUser).filter(func.lower(AdminUser.username) == func.lower(clean_username)).first()
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User '{req.username}' not found")

    target_user.password_hash = hash_password(req.new_password)
    db.commit()

    return {
        "message": f"Password for '{target_user.username}' reset successfully",
        "username": target_user.username,
        "centre_id": target_user.centre_id,
    }

