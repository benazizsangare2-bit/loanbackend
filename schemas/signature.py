from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class SignatureRequest(BaseModel):
    signed_name: str = Field(..., min_length=3, max_length=100)
    agreed_to_terms: bool = Field(..., description="Must be True to accept")
    
    @validator('agreed_to_terms')
    def must_agree(cls, v):
        if not v:
            raise ValueError('You must agree to the terms to sign')
        return v
    
    @validator('signed_name')
    def validate_name(cls, v):
        if len(v.strip().split()) < 2:
            raise ValueError('Please enter your full name (first and last name)')
        return v.strip()

class SignatureResponse(BaseModel):
    success: bool
    message: str
    agreement_id: int
    signed_at: datetime
    signature_id: int

class SignatureStatusResponse(BaseModel):
    is_signed: bool
    signed_at: Optional[datetime]
    signed_by: Optional[str]
    signing_status: str
    amount: Optional[float] = None
    amount_requested: Optional[float] = None
    duration: Optional[int] = None
    duration_requested: Optional[int] = None
    interest_rate: Optional[float] = None
    monthly_payment: Optional[float] = None
    total_repayment: Optional[float] = None
    disbursement_date: Optional[datetime] = None
    first_payment_date: Optional[datetime] = None

class LoanAgreementWithSignatureResponse(BaseModel):
    """Extended agreement response with signature info"""
    agreement_id: int
    application_id: int
    approved_amount: float
    interest_rate: float
    duration_months: int
    monthly_payment: float
    total_repayment: float
    total_interest: float
    approval_date: datetime
    signing_status: str
    is_signed: bool
    signed_at: Optional[datetime]
    signed_by: Optional[str]
    
    class Config:
        from_attributes = True