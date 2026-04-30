from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LoanApplicationStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LoanApplicationCreate(BaseModel):
    """Schema for creating a loan application with new model fields."""

    # 1) Personal information
    full_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    date_of_birth: Optional[date] = None
    national_id: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    email_address: Optional[str] = Field(None, max_length=100)
    marital_status: Optional[str] = Field(None, max_length=20)
    number_of_dependents: Optional[int] = Field(None, ge=0)

    # 2) Address information
    residential_address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field("DRC", max_length=100)
    gps_location: Optional[str] = Field(None, max_length=100)

    # 3) Employment / business details
    employment_status: Optional[str] = Field(None, max_length=50)
    employer_name: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    monthly_salary: Optional[float] = Field(None, ge=0)
    length_of_employment_years: Optional[int] = Field(None, ge=0)
    business_name: Optional[str] = Field(None, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)
    business_location: Optional[str] = Field(None, max_length=200)
    monthly_business_income: Optional[float] = Field(None, ge=0)
    years_in_business: Optional[int] = Field(None, ge=0)

    # 4) Financial information
    monthly_income: Optional[float] = Field(None, ge=0)
    other_income_sources: Optional[str] = Field(None, max_length=200)
    other_income_amount: Optional[float] = Field(None, ge=0)
    monthly_expenses: Optional[float] = Field(None, ge=0)
    has_existing_loans: bool = False
    existing_loan_details: Optional[str] = None
    savings_balance: Optional[float] = Field(None, ge=0)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)

    # 5) Loan details
    amount_requested: Optional[float] = Field(None, gt=0)
    loan_purpose: Optional[str] = Field(None, max_length=200)
    duration_requested: Optional[int] = Field(None, gt=0, le=120)
    preferred_repayment_method: Optional[str] = Field(None, max_length=50)
    has_collateral: bool = False
    collateral_description: Optional[str] = None
    has_guarantor: bool = False

    # 6) Guarantor information
    guarantor_name: Optional[str] = Field(None, max_length=100)
    guarantor_relationship: Optional[str] = Field(None, max_length=50)
    guarantor_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    guarantor_address: Optional[str] = Field(None, max_length=200)
    guarantor_occupation: Optional[str] = Field(None, max_length=100)
    guarantor_id_number: Optional[str] = Field(None, max_length=50)

    # 7) Document paths
    national_id_document_path: Optional[str] = Field(None, max_length=500)
    proof_of_address_path: Optional[str] = Field(None, max_length=500)
    salary_slip_path: Optional[str] = Field(None, max_length=500)
    business_license_path: Optional[str] = Field(None, max_length=500)
    bank_statement_path: Optional[str] = Field(None, max_length=500)
    collateral_document_path: Optional[str] = Field(None, max_length=500)


class LoanApplicationResponse(LoanApplicationCreate):
    """Schema for loan application response."""

    application_id: int
    user_id: int
    status: str
    reviewed_by: Optional[str]
    review_notes: Optional[str]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


     
class LoanApplicationUpdate(BaseModel):
    """Schema for partial updates - all fields optional"""
    # Personal Information
    full_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    national_id: Optional[str] = None
    marital_status: Optional[str] = None
    number_of_dependents: Optional[int] = None
    
    # Address
    residential_address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    gps_location: Optional[str] = None
    
    # Employment
    employment_status: Optional[str] = None
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    monthly_salary: Optional[float] = None
    length_of_employment_years: Optional[int] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_location: Optional[str] = None
    monthly_business_income: Optional[float] = None
    years_in_business: Optional[int] = None
    
    # Financial
    monthly_income: Optional[float] = None
    other_income_sources: Optional[str] = None
    other_income_amount: Optional[float] = None
    monthly_expenses: Optional[float] = None
    has_existing_loans: Optional[bool] = None
    existing_loan_details: Optional[str] = None
    savings_balance: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    
    # Loan Details
    amount_requested: Optional[float] = None
    loan_purpose: Optional[str] = None
    duration_requested: Optional[int] = None
    preferred_repayment_method: Optional[str] = None
    has_collateral: Optional[bool] = None
    collateral_description: Optional[str] = None
    has_guarantor: Optional[bool] = None
    
    # Guarantor
    guarantor_name: Optional[str] = None
    guarantor_relationship: Optional[str] = None
    guarantor_phone: Optional[str] = None
    guarantor_address: Optional[str] = None
    guarantor_occupation: Optional[str] = None
    guarantor_id_number: Optional[str] = None
    
    # Document paths
    national_id_document_path: Optional[str] = None
    proof_of_address_path: Optional[str] = None
    salary_slip_path: Optional[str] = None
    business_license_path: Optional[str] = None
    bank_statement_path: Optional[str] = None
    collateral_document_path: Optional[str] = None