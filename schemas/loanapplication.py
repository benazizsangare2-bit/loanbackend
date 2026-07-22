import re
from datetime import date, datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field, validator, model_validator
from decimal import Decimal


class LoanApplicationStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


PHONE_REGEX = re.compile(r'^\+?[\d\s\-()]{7,20}$')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_phone(v: Optional[str]) -> Optional[str]:
    if v is not None and v.strip():
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            raise ValueError('Phone number must contain at least 10 digits')
        if len(digits) > 15:
            raise ValueError('Phone number must not exceed 15 digits')
    return v


MIN_AGE_YEARS = 18
MAX_DURATION_MONTHS = 60


def validate_not_future_date(v: Optional[date]) -> Optional[date]:
    if v is not None and v > date.today():
        raise ValueError('Date of birth cannot be in the future')
    if v is not None:
        age = (date.today().year - v.year - ((date.today().month, date.today().day) < (v.month, v.day)))
        if age < MIN_AGE_YEARS:
            raise ValueError(f'You must be at least {MIN_AGE_YEARS} years old')
    return v


def validate_not_future_date_str(v: Optional[str]) -> Optional[str]:
    if v is not None and v.strip():
        try:
            dt = datetime.strptime(v, '%Y-%m-%d').date()
            if dt > date.today():
                raise ValueError('Date of birth cannot be in the future')
            age = (date.today().year - dt.year - ((date.today().month, date.today().day) < (dt.month, dt.day)))
            if age < MIN_AGE_YEARS:
                raise ValueError(f'You must be at least {MIN_AGE_YEARS} years old')
        except ValueError:
            raise ValueError('Invalid date format. Expected YYYY-MM-DD')
    return v


class _LoanApplicationFields(BaseModel):
    """Common field definitions with all constraints.
    Used by Create and Update schemas for input validation.
    """
    full_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    date_of_birth: Optional[str] = None
    national_id: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    email_address: Optional[str] = Field(None, max_length=100)
    marital_status: Optional[str] = Field(None, max_length=20)
    number_of_dependents: Optional[int] = Field(None, ge=0)

    residential_address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    gps_location: Optional[str] = Field(None, max_length=100)

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

    monthly_income: Optional[float] = Field(None, ge=0)
    other_income_sources: Optional[str] = Field(None, max_length=200)
    other_income_amount: Optional[float] = Field(None, ge=0)
    monthly_expenses: Optional[float] = Field(None, ge=0)
    has_existing_loans: Optional[bool] = None
    existing_loan_details: Optional[str] = None
    savings_balance: Optional[float] = Field(None, ge=0)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)

    amount_requested: Optional[float] = Field(None, gt=0)
    loan_purpose: Optional[str] = Field(None, max_length=200)
    duration_requested: Optional[int] = Field(None, gt=0, le=60)
    preferred_repayment_method: Optional[str] = Field(None, max_length=50)
    has_collateral: Optional[bool] = None
    collateral_description: Optional[str] = None
    has_guarantor: Optional[bool] = None

    guarantor_name: Optional[str] = Field(None, max_length=100)
    guarantor_relationship: Optional[str] = Field(None, max_length=50)
    guarantor_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    guarantor_address: Optional[str] = Field(None, max_length=200)
    guarantor_occupation: Optional[str] = Field(None, max_length=100)
    guarantor_id_number: Optional[str] = Field(None, max_length=50)

    national_id_document_path: Optional[str] = Field(None, max_length=500)
    proof_of_address_path: Optional[str] = Field(None, max_length=500)
    salary_slip_path: Optional[str] = Field(None, max_length=500)
    business_license_path: Optional[str] = Field(None, max_length=500)
    bank_statement_path: Optional[str] = Field(None, max_length=500)
    collateral_document_path: Optional[str] = Field(None, max_length=500)


class LoanApplicationCreate(_LoanApplicationFields):
    """Schema for creating a loan application — with validation."""
    date_of_birth: Optional[date] = None
    country: Optional[str] = Field("DRC", max_length=100)
    has_existing_loans: bool = False
    has_collateral: bool = False
    has_guarantor: bool = False

    _validate_phone = validator('phone_number', 'guarantor_phone', allow_reuse=True)(validate_phone)
    _validate_dob = validator('date_of_birth', allow_reuse=True)(validate_not_future_date)

    @validator('email_address')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            if not EMAIL_REGEX.match(v):
                raise ValueError('Invalid email address format')
        return v


class LoanApplicationUpdate(_LoanApplicationFields):
    """Schema for partial updates — all fields optional, with validation."""

    _validate_phone = validator('phone_number', 'guarantor_phone', allow_reuse=True)(validate_phone)
    _validate_dob_str = validator('date_of_birth', allow_reuse=True)(validate_not_future_date_str)

    @validator('email_address')
    @classmethod
    def validate_email_update(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            if not EMAIL_REGEX.match(v):
                raise ValueError('Invalid email address format')
        return v


class _LoanApplicationResponseFields(BaseModel):
    """Response-only field definitions WITHOUT constraints.
    This prevents ResponseValidationError crashes when reading
    existing DB records that contain legacy invalid values.
    """
    full_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    national_id: Optional[str] = None
    phone_number: Optional[str] = None
    email_address: Optional[str] = None
    marital_status: Optional[str] = None
    number_of_dependents: Optional[int] = None

    residential_address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    gps_location: Optional[str] = None

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

    monthly_income: Optional[float] = None
    other_income_sources: Optional[str] = None
    other_income_amount: Optional[float] = None
    monthly_expenses: Optional[float] = None
    has_existing_loans: Optional[bool] = None
    existing_loan_details: Optional[str] = None
    savings_balance: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None

    amount_requested: Optional[float] = None
    loan_purpose: Optional[str] = None
    duration_requested: Optional[int] = None
    preferred_repayment_method: Optional[str] = None
    has_collateral: Optional[bool] = None
    collateral_description: Optional[str] = None
    has_guarantor: Optional[bool] = None

    guarantor_name: Optional[str] = None
    guarantor_relationship: Optional[str] = None
    guarantor_phone: Optional[str] = None
    guarantor_address: Optional[str] = None
    guarantor_occupation: Optional[str] = None
    guarantor_id_number: Optional[str] = None

    national_id_document_path: Optional[str] = None
    proof_of_address_path: Optional[str] = None
    salary_slip_path: Optional[str] = None
    business_license_path: Optional[str] = None
    bank_statement_path: Optional[str] = None
    collateral_document_path: Optional[str] = None


class LoanApplicationResponse(_LoanApplicationResponseFields):
    """Schema for loan application response.
    Does NOT enforce Field constraints so existing DB records
    with legacy invalid values won't crash the response.
    """

    application_id: int
    user_id: int
    status: str
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    agreement_id: Optional[int] = None

    @model_validator(mode='before')
    @classmethod
    def populate_agreement_id(cls, data: Any) -> Any:
        if hasattr(data, 'loan_agreement'):
            result = {}
            for col in data.__table__.columns:
                result[col.name] = getattr(data, col.name)
            result['agreement_id'] = data.loan_agreement.agreement_id if data.loan_agreement else None
            return result
        return data

    class Config:
        from_attributes = True


class RepaymentScheduleResponse(BaseModel):
    """Schema for repayment schedule with late fee info"""
    installment_number: int
    due_date: Optional[datetime] = None
    amount_due: float
    late_fee: float = 0.0
    total_due: float
    status: str
    paid_amount: float = 0.0
    paid_date: Optional[datetime] = None
    days_late: int = 0

    class Config:
        from_attributes = True


class LateFeeInfoResponse(BaseModel):
    """Schema for late fee information"""
    loan_id: int
    has_late_fees: bool
    late_installments: list
    total_late_fee_due: float
