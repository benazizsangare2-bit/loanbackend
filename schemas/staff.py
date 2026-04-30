from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class StaffBase(BaseModel):
    """Base staff schema with common fields"""
    employee_id: str
    employee_name: str
    email: EmailStr
    employee_phone: str
    position: str

class StaffCreate(StaffBase):
    """Schema for creating a new staff member"""
    password: str
    can_approve_loans: bool = False
    can_disburse_loans: bool = False
    can_record_payments: bool = False

class StaffResponse(StaffBase):
    """Schema for Staff response"""
    employee_id: str
    employee_name: str
    email: EmailStr
    employee_phone: str
    position: str
    can_approve_loans: bool
    can_disburse_loans: bool
    can_record_payments: bool
    is_active: bool
    hired_date: datetime
    
    class Config:
        from_attributes = True

class StaffLogin(BaseModel):
    """Schema for Staff Login"""
    email: EmailStr
    password: str

class StaffToken(BaseModel):
    """Schema for staff JWT token response"""
    access_token: str
    token_type: str
    employee_id: str
    employee_name: str
    position: str

class StaffAction(BaseModel):
    """Schema for recording Staff actions"""
    staff_id: str
    action_type: str
    reference_id: int
    notes: Optional[str] = None