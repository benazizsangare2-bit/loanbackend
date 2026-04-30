"""
Pydantic models for user data validation.
These define the shape of data coming into and out of your API.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    """
    Base user schema with common fields.
    Think of this as a base struct that other structs inherit from.
    """
    name: str
    email: EmailStr  # Automatically validates email format
    profession: str
    phone_number: str

class UserCreate(UserBase):
    """
    Schema for creating a new user (what the client sends when registering).
    """
    password: str

class UserResponse(UserBase):
    """
    Schema for returning user data (what the API sends back).
    Notice we don't include the password hash for security.
    """
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        # This allows Pydantic to work with SQLAlchemy models
        from_attributes = True

class UserLogin(BaseModel):
    """
    Schema for login request.
    """
    email: EmailStr
    password: str

class Token(BaseModel):
    """
    Schema for JWT token response after login.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Schema for token payload (what's stored in the JWT).
    """
    email: Optional[str] = None