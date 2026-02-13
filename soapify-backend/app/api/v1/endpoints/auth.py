from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import security
from app.models.models import User
from app.schemas.auth import UserRegister


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=security.get_password_hash(data.password),
        role=data.role or "doctor",
        specialization=data.specialization,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}


@router.post("/login")
def login_user(
    data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm uses `username` field
    user = db.query(User).filter(User.email == data.username).first()

    if not user or not security.verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = security.create_access_token(
        data={
            "sub": user.email,
            "role": user.role,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "name": user.full_name,
        "role": user.role,
    }
