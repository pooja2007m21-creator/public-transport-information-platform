from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..models import User
from ..schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from ..security import hash_password, verify_password, create_access_token
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if username or email exists
    existing = db.query(User).filter(
        or_(User.username == user_in.username.strip(), User.email == user_in.email.strip().lower())
    ).first()
    
    if existing:
        if existing.username.lower() == user_in.username.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken. Please choose another username."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered. Please login or use a different email."
            )

    new_user = User(
        full_name=user_in.full_name.strip(),
        username=user_in.username.strip(),
        email=user_in.email.strip().lower(),
        phone=user_in.phone.strip() if user_in.phone else None,
        password_hash=hash_password(user_in.password),
        role="USER",
        status="ACTIVE"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id), "role": new_user.role, "username": new_user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "full_name": new_user.full_name,
            "username": new_user.username,
            "email": new_user.email,
            "phone": new_user.phone,
            "role": new_user.role,
            "status": new_user.status
        }
    }

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    identifier = credentials.username_or_email.strip()
    user = db.query(User).filter(
        or_(User.username == identifier, User.email == identifier.lower())
    ).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your account is {user.status.lower()}. Please contact administrator."
        )

    token = create_access_token({"sub": str(user.id), "role": user.role, "username": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "status": user.status
        }
    }

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully."}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
