"""
Authentication routes - register and login endpoints for clients.
This is like your functions folder in Go, but with route decorators.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas import user as user_schemas
from fastapi.security import HTTPBearer
from utils import auth as auth_utils, user as user_utils
from schemas import otp as otp_schemas
from utils.user import user_schemas
from routers.loan_application import get_current_user

clientrouter = APIRouter(prefix="/client/auth", tags=["client authentication"])
security = HTTPBearer()

@clientrouter.post("/registerClient", response_model=user_schemas.UserResponse)
def register(
    user_data: user_schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user - OTP will be sent to email"""
    logger.info("POST /client/auth/registerClient — email=%s", user_data.email)

    # Check if user already exists
    existing_user = user_utils.get_user_by_email(db, user_data.email)
    if existing_user:
        logger.warning(
            "Register failed — email already registered: %s (verified=%s)",
            user_data.email,
            existing_user.is_email_verified,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with OTP
    new_user, message = user_utils.create_user_with_otp(db, user_data)
    if not new_user:
        logger.warning("Register failed — email=%s reason=%s", user_data.email, message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    logger.info("Register succeeded — user_id=%s email=%s", new_user.user_id, new_user.email)
    return new_user

@clientrouter.post("/verify-otp")
def verify_otp(
    otp_data: otp_schemas.OTPVerify,
    db: Session = Depends(get_db)
):
    """Verify user email with OTP"""
    success, message = user_utils.verify_otp(db, otp_data.email, otp_data.otp_code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}

@clientrouter.post("/resend-otp")
def resend_otp(
    request: otp_schemas.OTPRequest,
    db: Session = Depends(get_db)
):
    """Resend OTP to user email"""
    success, message = user_utils.resend_otp(db, request.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}

@clientrouter.post("/forgot-password")
def forgot_password(
    request: otp_schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset email"""
    success, message = user_utils.create_password_reset_token(db, request.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}

@clientrouter.post("/reset-password")
def reset_password(
    reset_data: otp_schemas.PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using token"""
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    success, message = user_utils.reset_password(db, reset_data.token, reset_data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}

@clientrouter.post("/change-password")
def change_password(
    password_data: otp_schemas.PasswordChange,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for logged in user"""
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    success, message = user_utils.change_password(
        db, 
        current_user.user_id, 
        password_data.old_password, 
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@clientrouter.post("/ClientLogin", response_model=user_schemas.Token)
def login(
    user_data: user_schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    logger.info("POST /client/auth/ClientLogin — email=%s", user_data.email)

    # Find user by email
    user = user_utils.get_user_by_email(db, user_data.email)
    if not user:
        logger.warning("Login failed — no user found for email=%s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if email is verified
    if not user.is_email_verified:
        logger.warning(
            "Login failed — email not verified: user_id=%s email=%s",
            user.user_id,
            user_data.email,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email first. Check your inbox or Spam folder for OTP."
        )
    
    # Verify password
    if not auth_utils.verify_password(user_data.password, user.hashed_password):
        logger.warning(
            "Login failed — incorrect password: user_id=%s email=%s",
            user.user_id,
            user_data.email,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    user_response = user_schemas.UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        profession=user.profession,
        phone_number=user.phone_number,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
    # Create access token
    access_token = auth_utils.create_access_token(data={"sub": user.email})
    logger.info("Login succeeded — user_id=%s email=%s", user.user_id, user.email)

    return {"access_token": access_token, "token_type": "bearer", "user":user_response}

@clientrouter.get("/users/me", response_model=user_schemas.UserResponse)
def get_current_user(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current logged-in user's profile"""
    return current_user