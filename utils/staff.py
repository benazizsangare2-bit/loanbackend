from sqlalchemy.orm import Session
from database import models
from schemas import staff as staff_schemas
from utils import auth as auth_utils

def create_staff(db: Session, staff_data: staff_schemas.StaffCreate):
    """Create a new staff member"""
    hashed_password = auth_utils.get_password_hash(staff_data.password)
    
    db_staff = models.Staff(
        employee_id=staff_data.employee_id,
        employee_name=staff_data.employee_name,
        email=staff_data.email,
        employee_phone=staff_data.employee_phone,
        position=staff_data.position,
        hashed_password=hashed_password,
        can_approve_loans=staff_data.can_approve_loans,
        can_disburse_loans=staff_data.can_disburse_loans,
        can_record_payments=staff_data.can_record_payments
    )
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

def get_staff_by_email(db: Session, email: str):
    """Get staff member by email"""
    return db.query(models.Staff).filter(models.Staff.email == email).first()

def get_staff_by_id(db: Session, employee_id: str):
    """Get staff member by employee ID"""
    return db.query(models.Staff).filter(models.Staff.employee_id == employee_id).first()

def authenticate_staff(db: Session, email: str, password: str):
    """Authenticate staff member"""
    staff = get_staff_by_email(db, email)
    if not staff:
        return None
    if not auth_utils.verify_password(password, staff.hashed_password):
        return None
    if not staff.is_active:
        return None
    return staff