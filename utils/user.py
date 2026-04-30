"""
Database helper functions for common operations.
This centralizes database queries so you don't repeat code.
"""

from datetime import datetime, timedelta
import os
from sqlalchemy.orm import Session
from database import models
from utils import auth as  auth_utils
from schemas import user as user_schemas
import random, string
from utils.email import send_otp_email, send_password_reset_email


def generate_otp():
    """Generate a 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=6))



def create_user_with_otp(db: Session, user_data: user_schemas.UserCreate)-> models.User:
    """Create user and send OTP for verification"""
    # Check if user exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user and existing_user.is_email_verified:
        return None, "Email already registered"
    
   
     # If user exists but not verified, update OTP
    if existing_user and not existing_user.is_email_verified:
        existing_user.otp_code = otp
        existing_user.otp_expiry = otp_expiry
        # Don't update other fields
        db.commit()
        user = existing_user
    else:
        # Create user but mark as not verified
        hashed_password = auth_utils.get_password_hash(user_data.password)
    
    # Generate OTP
    otp = generate_otp()
    otp_expiry = datetime.now() + timedelta(minutes=int(os.getenv("OTP_EXPIRY_MINUTES", 10)))
    
    # Create user
    db_user = models.User(
        name=user_data.name,
        email=user_data.email,
        profession=user_data.profession,
        phone_number=user_data.phone_number,
        hashed_password=hashed_password,
        otp_code=otp,
        otp_expiry=otp_expiry,
        is_email_verified=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send OTP email
    success, message = send_otp_email(user_data.email, otp, user_data.name)
    
    if not success:
        # Log error but don't fail user creation
        print(f"Failed to send OTP: {message}")
    
    return db_user, "User created. Please verify your email with the OTP sent."


def verify_otp(db: Session, email: str, otp_code: str):
    """Verify user with OTP - only now mark as verified"""
    user = get_user_by_email(db, email)
    if not user:
        return False, "User not found"
    
    if user.is_email_verified:
        return False, "Email already verified"
    
    if user.otp_code != otp_code:
        return False, "Invalid OTP code"
    
    if user.otp_expiry < datetime.now():
        return False, "OTP has expired"
    
    # Mark as verified - account becomes active
    user.is_email_verified = True
    user.otp_code = None
    user.otp_expiry = None
    db.commit()
    
    return True, "Email verified successfully"

def resend_otp(db: Session, email: str):
    """Resend OTP to user"""
    user = get_user_by_email(db, email)
    if not user:
        return False, "User not found"
    
    if user.is_email_verified:
        return False, "Email already verified"
    
    # Generate new OTP
    otp = generate_otp()
    otp_expiry = datetime.now() + datetime.timedelta(minutes=int(os.getenv("OTP_EXPIRY_MINUTES", 10)))
    
    user.otp_code = otp
    user.otp_expiry = otp_expiry
    db.commit()
    
    # Send new OTP
    success, message = send_otp_email(email, otp, user.name)
    
    if success:
        return True, "OTP resent successfully"
    else:
        return False, f"Failed to send OTP: {message}"

def create_password_reset_token(db: Session, email: str):
    """Create password reset token and send email"""
    user = get_user_by_email(db, email)
    if not user:
        return False, "User not found"
    
    # Generate reset token
    reset_token = auth_utils.create_access_token(data={"sub": email, "type": "password_reset"})
    reset_expiry = datetime.now() + datetime.timedelta(hours=1)
    
    user.reset_token = reset_token
    user.reset_token_expiry = reset_expiry
    db.commit()
    
    # Send reset email
    success, message = send_password_reset_email(email, reset_token, user.name)
    
    if success:
        return True, "Password reset email sent"
    else:
        return False, f"Failed to send reset email: {message}"

def reset_password(db: Session, token: str, new_password: str):
    """Reset password using token"""
    # Decode token
    payload = auth_utils.decode_access_token(token)
    if not payload:
        return False, "Invalid or expired token"
    
    if payload.get("type") != "password_reset":
        return False, "Invalid token type"
    
    email = payload.get("sub")
    user = get_user_by_email(db, email)
    
    if not user:
        return False, "User not found"
    
    # Check if token matches and not expired
    if user.reset_token != token:
        return False, "Invalid token"
    
    if user.reset_token_expiry < datetime.now():
        return False, "Token has expired"
    
    # Update password
    user.hashed_password = auth_utils.get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
    
    return True, "Password reset successfully"

def change_password(db: Session, user_id: int, old_password: str, new_password: str):
    """Change password for logged in user"""
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        return False, "User not found"
    
    # Verify old password
    if not auth_utils.verify_password(old_password, user.hashed_password):
        return False, "Incorrect old password"
    
    # Update to new password
    user.hashed_password = auth_utils.get_password_hash(new_password)
    db.commit()
    
    return True, "Password changed successfully"
    

def get_user_by_email(db: Session, email: str) -> models.User:
    """
    Get a user by email address.
    
    Args:
        db: Database session
        email: User's email address
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> models.User:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: User's ID
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.user_id == user_id).first() 
