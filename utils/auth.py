"""
Authentication utilities: password hashing and JWT token handling.
This is similar to your Go auth helpers.
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Password hashing configuration
# This uses bcrypt algorithm (same as Go's bcrypt)
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-a-real-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 720))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    Equivalent to bcrypt.CompareHashAndPassword in Go.
    
    Args:
        plain_password: The password provided by user during login
        hashed_password: The stored hash from database
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    Equivalent to bcrypt.GenerateFromPassword in Go.
    
    Args:
        password: The plain text password to hash
    
    Returns:
        The hashed password string
    """
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    Similar to JWT signing in Go.
    
    Args:
        data: Dictionary containing claims (like user email)
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token string
    
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None