from pydantic import BaseModel, EmailStr
from typing import Optional

class OTPVerify(BaseModel):
    """Schema for OTP verification"""
    email: EmailStr
    otp_code: str

class OTPRequest(BaseModel):
    """Schema for requesting OTP"""
    email: EmailStr

class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str
    new_password: str
    confirm_password: str

class PasswordChange(BaseModel):
    """Schema for changing password (logged in user)"""
    old_password: str
    new_password: str
    confirm_password: str