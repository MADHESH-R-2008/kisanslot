from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import AdminUser, Farmer, RoleEnum
from config import get_settings

_settings = get_settings()
SECRET_KEY = _settings.SECRET_KEY
ALGORITHM = _settings.ALGORITHM

# OAuth2 scheme expects a token endpoint – we use the unified login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/unified-login")

def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        role: str = payload.get("role")
        centre_id = payload.get("centre_id")
        return {"user_id": user_id, "role": role, "centre_id": centre_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Return decoded JWT payload as a dict."""
    return decode_jwt(token)

def require_role(allowed_roles: List[RoleEnum]):
    """FastAPI dependency that ensures the caller's role is one of *allowed_roles*.
    Usage::
        @router.get("/admin")
        def admin_endpoint(user: dict = Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))):
            ...
    """
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in [r.value for r in allowed_roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return role_checker

async def get_current_farmer(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Validate that the JWT belongs to a farmer and return the ORM instance."""
    if user["role"] != RoleEnum.FARMER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer access required")
    farmer = db.query(Farmer).filter(Farmer.id == user["user_id"]).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer

async def get_current_admin(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Validate that the JWT belongs to an admin/operator and return the ORM instance."""
    if user["role"] not in [RoleEnum.CENTRE_OPERATOR.value, RoleEnum.ADMIN.value, RoleEnum.SUPER_ADMIN.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    admin = db.query(AdminUser).filter(AdminUser.id == user["user_id"]).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")
    return admin

async def enforce_operator_centre(centre_id: int, user: dict = Depends(get_current_user)):
    """Ensure a centre‑operator can only act on its assigned centre.
    Super admins bypass this check.
    """
    if user["role"] == RoleEnum.CENTRE_OPERATOR.value and user.get("centre_id") != centre_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator not assigned to this centre")
    return True

# New helper for admin or super admin permissions

def require_admin_or_super():
    """Dependency that permits ADMIN, CENTRE_OPERATOR, or SUPER_ADMIN roles."""
    return require_role([RoleEnum.ADMIN, RoleEnum.CENTRE_OPERATOR, RoleEnum.SUPER_ADMIN])
