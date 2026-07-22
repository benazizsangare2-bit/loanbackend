from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database import models
from schemas import staff as staff_schemas
from utils import staff as staff_utils
from utils import auth as auth_utils
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/staff/auth", tags=["staff authentication"])
security = HTTPBearer()


def get_current_staff(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current logged-in staff member from JWT token"""
    token = credentials.credentials
    payload = auth_utils.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check if this is a staff token
    if payload.get("type") != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    email = payload.get("sub")
    staff = staff_utils.get_staff_by_email(db, email)
    if not staff:
        raise HTTPException(status_code=401, detail="Staff not found")
    
    if not staff.is_active:
        raise HTTPException(status_code=403, detail="Staff account is deactivated")
    
    return staff


@router.post("/register", response_model=staff_schemas.StaffResponse)
def register_staff(
    staff_data: staff_schemas.StaffCreate,
    # current_staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Register a new staff member (Admin only)"""
    # if not current_staff.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")
    # Check if email already exists
    existing_staff = staff_utils.get_staff_by_email(db, staff_data.email)
    if existing_staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if employee_id already exists
    existing_id = staff_utils.get_staff_by_id(db, staff_data.employee_id)
    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already exists"
        )
    
    return staff_utils.create_staff(db, staff_data)


@router.post("/login", response_model=staff_schemas.StaffToken)
def login_staff(
    login_data: staff_schemas.StaffLogin,
    db: Session = Depends(get_db)
):
    """Login staff member and return JWT token"""
    # Authenticate staff
    staff = staff_utils.authenticate_staff(db, login_data.email, login_data.password)
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = auth_utils.create_access_token(data={"sub": staff.email, "type": "staff"})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "employee_id": staff.employee_id,
        "employee_name": staff.employee_name,
        "position": staff.position
    }