
import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User


# =========================================================
# 1. CONFIGURATION
# =========================================================

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

try:
    TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
except ValueError as exc:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be a valid integer."
    ) from exc

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from .env")

if TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero."
    )

if JWT_ALGORITHM != "HS256":
    raise RuntimeError(
        "This authentication module currently expects HS256."
    )

if len(JWT_SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY should contain at least 32 bytes."
    )


# =========================================================
# 2. ROUTER AND SECURITY
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

password_hash = PasswordHash.recommended()

bearer_scheme = HTTPBearer(auto_error=False)


# =========================================================
# 3. REQUEST MODELS
# =========================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128
    )


# =========================================================
# 4. JWT TOKEN GENERATION
# =========================================================

def create_access_token(user_id: int) -> str:

    expires = datetime.now(timezone.utc) + timedelta(
        minutes=TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expires
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


# =========================================================
# 5. USER REGISTRATION
# =========================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):

    email = str(data.email).lower().strip()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    user = User(
        email=email,
        hashed_password=password_hash.hash(data.password)
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


# =========================================================
# 6. USER LOGIN
# =========================================================

@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    email = str(data.email).lower().strip()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not password_hash.verify(
        data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


# =========================================================
# 7. GET CURRENT AUTHENTICATED USER
# =========================================================

@router.get("/me")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db)
):

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise credentials_error

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_error

        user_id = int(subject)

        if user_id <= 0:
            raise credentials_error

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    user = db.get(User, user_id)

    if not user:
        raise credentials_error

    return {
        "id": user.id,
        "email": user.email
    }
