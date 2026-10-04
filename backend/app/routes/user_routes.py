from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import User, Favorite, SearchHistory, Alert, Route, Stop
from ..schemas import UserResponse, UserUpdate, PasswordChange, UserDashboardStats, AlertResponse
from ..security import verify_password, hash_password
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_update.full_name:
        current_user.full_name = user_update.full_name.strip()
    if user_update.phone is not None:
        current_user.phone = user_update.phone.strip()
    if user_update.email:
        email_clean = user_update.email.strip().lower()
        # Check email uniqueness
        existing = db.query(User).filter(User.email == email_clean, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email is already used by another account.")
        current_user.email = email_clean

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/password")
def change_password(
    pwd_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(pwd_data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password does not match.")
    
    current_user.password_hash = hash_password(pwd_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Password changed successfully."}

@router.delete("/me")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.delete(current_user)
    db.commit()
    return {"message": "Your account has been deleted successfully."}
