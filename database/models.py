"""
This file defines your database tables (like schema.go in Go).
Each class here represents a table in PostgreSQL.
"""

from sqlalchemy import Column, Date, Integer, String, Boolean, DateTime, Float, Text, Index, CheckConstraint
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func
from database.connection import Base
from sqlalchemy.orm import relationship 


## USERS TABLE
class User(Base):
    """
    Users table - stores all user accounts
    This is like your users table in Go's schema.go
    """
    __tablename__ = "users"
    
    # Primary key
    user_id = Column(Integer, primary_key=True, index=True)
    
    # User information
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    profession = Column(String(100), nullable=False, index=True)
    phone_number = Column(String(14), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Timestamps (automatically handled)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Password reset functionality
    reset_token = Column (String(255), nullable=True)
    reset_token_expiry = Column (DateTime(timezone=True), nullable=True)
    
    # Soft delete (mark as deleted without actually deleting)
    is_deleted = Column(Boolean, default=False)

    # Verify provided email is correct  
    is_email_verified = Column(Boolean, default=False)
    otp_code = Column(String(255), nullable=True)
    otp_expiry = Column(DateTime(timezone=True), nullable=True)
    


# STAFF TABLE
class Staff(Base):
    """Staff table - employees who manage the system"""
    __tablename__ = "staff"
    
    employee_id = Column(String(50), primary_key=True, index=True)
    
    # Login credentials
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Employment information
    employee_name = Column(String(100), nullable=False)
    employee_phone = Column(String(100), nullable=False, index=True)
    position = Column(String(100), nullable=False)
    
    # Permissions
    can_approve_loans = Column(Boolean, default=False)
    can_disburse_loans = Column(Boolean, default=False)
    can_record_payments = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    hired_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())



# LOAN FORM SUBMISSION TABLE
# Add a cancel endpoint for users to withdraw pending applications
# Require new application if rejected

class LoanApplication(Base):
    """Loan Applications table - complete application with document paths"""
    __tablename__ = "loan_applications"
    __table_args__ = (
        CheckConstraint('monthly_salary >= 0 OR monthly_salary IS NULL', name='ck_monthly_salary_non_negative'),
        CheckConstraint('monthly_business_income >= 0 OR monthly_business_income IS NULL', name='ck_monthly_business_income_non_negative'),
        CheckConstraint('length_of_employment_years >= 0 OR length_of_employment_years IS NULL', name='ck_length_of_employment_non_negative'),
        CheckConstraint('years_in_business >= 0 OR years_in_business IS NULL', name='ck_years_in_business_non_negative'),
        CheckConstraint('monthly_income >= 0 OR monthly_income IS NULL', name='ck_monthly_income_non_negative'),
        CheckConstraint('monthly_expenses >= 0 OR monthly_expenses IS NULL', name='ck_monthly_expenses_non_negative'),
        CheckConstraint('savings_balance >= 0 OR savings_balance IS NULL', name='ck_savings_balance_non_negative'),
        CheckConstraint('other_income_amount >= 0 OR other_income_amount IS NULL', name='ck_other_income_non_negative'),
        CheckConstraint('number_of_dependents >= 0 OR number_of_dependents IS NULL', name='ck_dependents_non_negative'),
        CheckConstraint('amount_requested > 0 OR amount_requested IS NULL', name='ck_amount_positive'),
        CheckConstraint('duration_requested > 0 OR duration_requested IS NULL', name='ck_duration_positive'),
        CheckConstraint('duration_requested <= 60 OR duration_requested IS NULL', name='ck_duration_max_60'),
    )
    
    # Primary key
    application_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    
    # ===== STATUS =====
    status = Column(String(50), default="draft")  # draft, pending, under_review, approved, rejected, cancelled
    
    # ===== 1) PERSONAL INFORMATION =====
    full_name = Column(String(100), nullable=True)
    gender = Column(String(10), nullable=True)  # male, female, other
    date_of_birth = Column(Date, nullable=True)
    national_id = Column(String(50), nullable=True)
    phone_number = Column(String(20), nullable=True)
    email_address = Column(String(100), nullable=True)
    marital_status = Column(String(20), nullable=True)  # single, married, divorced, widowed
    number_of_dependents = Column(Integer, nullable=True)
    
    # ===== 2) ADDRESS INFORMATION =====
    residential_address = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="DRC")
    gps_location = Column(String(100), nullable=True)
    
    # ===== 3) EMPLOYMENT / BUSINESS DETAILS =====
    employment_status = Column(String(50), nullable=True)  # employed, self_employed, unemployed
    
    # If employed
    employer_name = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    monthly_salary = Column(Float, nullable=True)
    length_of_employment_years = Column(Integer, nullable=True)
    
    # If self-employed
    business_name = Column(String(200), nullable=True)
    business_type = Column(String(100), nullable=True)
    business_location = Column(String(200), nullable=True)
    monthly_business_income = Column(Float, nullable=True)
    years_in_business = Column(Integer, nullable=True)
    
    # ===== 4) FINANCIAL INFORMATION =====
    monthly_income = Column(Float, nullable=True)
    other_income_sources = Column(String(200), nullable=True)
    other_income_amount = Column(Float, nullable=True)
    monthly_expenses = Column(Float, nullable=True)
    has_existing_loans = Column(Boolean, default=False)
    existing_loan_details = Column(Text, nullable=True)
    savings_balance = Column(Float, nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    
    # ===== 5) LOAN DETAILS =====
    amount_requested = Column(Float, nullable=True)
    loan_purpose = Column(String(200), nullable=True)  # business, school, emergency, etc.
    duration_requested = Column(Integer, nullable=True)  # months
    preferred_repayment_method = Column(String(50), nullable=True)  # bank transfer, mobile money, cash
    has_collateral = Column(Boolean, default=False)
    collateral_description = Column(Text, nullable=True)
    has_guarantor = Column(Boolean, default=False)
    
    # ===== 6) GUARANTOR INFORMATION =====
    guarantor_name = Column(String(100), nullable=True)
    guarantor_relationship = Column(String(50), nullable=True)
    guarantor_phone = Column(String(20), nullable=True)
    guarantor_address = Column(String(200), nullable=True)
    guarantor_occupation = Column(String(100), nullable=True)
    guarantor_id_number = Column(String(50), nullable=True)
    
    # ===== 7) DOCUMENT PATHS (stored as file paths, not files themselves) =====
    national_id_document_path = Column(String(500), nullable=True)
    proof_of_address_path = Column(String(500), nullable=True)
    salary_slip_path = Column(String(500), nullable=True)
    business_license_path = Column(String(500), nullable=True)
    bank_statement_path = Column(String(500), nullable=True)
    collateral_document_path = Column(String(500), nullable=True)
    
    # ===== ADMIN FIELDS =====
    reviewed_by = Column(String(50), nullable=True)
    review_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # ===== TIMESTAMPS =====
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    loan_agreement = relationship("LoanAgreement", back_populates="application", uselist=False)


## LOAN AGREEMENT TABLE
class LoanAgreement(Base):
    """Loan Agreements table - final approved loan with official terms"""
    __tablename__ = "loan_agreements"
    
    agreement_id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.application_id"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Final approved terms (from admin)
    approved_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)  # Annual percentage rate
    duration_months = Column(Integer, nullable=False)
    
    # Calculated values
    monthly_payment = Column(Float, nullable=False)
    total_repayment = Column(Float, nullable=False)
    total_interest = Column(Float, nullable=False)
    
    # Dates
    approval_date = Column(DateTime(timezone=True), server_default=func.now())
    disbursement_date = Column(DateTime(timezone=True), nullable=True)
    first_payment_date = Column(DateTime(timezone=True), nullable=True)
    final_payment_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    # Status
    status = Column(String(50), default="approved")  # approved, disbursed, active, completed, defaulted
    
    # Admin who approved/disbursed
    approved_by = Column(String(50), nullable=True)
    disbursed_by = Column(String(50), nullable=True)
    
    # Notes
    approval_notes = Column(Text, nullable=True)
    disbursement_notes = Column(Text, nullable=True)

    signing_status = Column(String(20), default="pending")  # pending, signed, expired, revoked
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    application = relationship("LoanApplication", back_populates="loan_agreement")
    user = relationship("User")
    payment_schedule = relationship("LoanRepaymentSchedule", back_populates="loan_agreement", cascade="all, delete-orphan")
    payments = relationship("LoanPayment", back_populates="loan_agreement", cascade="all, delete-orphan")
    signature = relationship("LoanAgreementSignature", back_populates="agreement", uselist=False)


class LoanRepaymentSchedule(Base):
    """Repayment schedule - automatically generated when loan is approved"""
    __tablename__ = "loan_repayment_schedules"
    
    loanrepaymentid = Column(Integer, primary_key=True, index=True)
    loan_agreement_id = Column(Integer, ForeignKey("loan_agreements.agreement_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Installment details
    installment_number = Column(Integer, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True) # this stays null until the loan is disbursed
    amount_due = Column(Float, nullable=False)
    principal_due = Column(Float, nullable=False)
    interest_due = Column(Float, nullable=False)
    remaining_principal = Column(Float, nullable=False)  # After this payment

    # NEW FIELDS - Add these
    late_fee = Column(Float, default=0.0)
    total_due = Column(Float, nullable=False)  # amount_due + late_fee
    late_fee_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Payment tracking
    status = Column(String(50), default="pending")  # pending, paid, partial, late, defaulted
    paid_amount = Column(Float, default=0.0)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    
    # Late payment tracking
    days_late = Column(Integer, default=0)
    penalty_amount = Column(Float, default=0.0)
    penalty_paid = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    loan_agreement = relationship("LoanAgreement", back_populates="payment_schedule")
    user = relationship("User")

# FOR RECORDING ACTUAL PAYMENTS 
class LoanPayment(Base):
    """Loan Payments - records actual payments made by client"""
    __tablename__ = "loan_payments"
    
    __table_args__ = (
        Index('ix_loan_payments_unique_reference', 'loan_agreement_id', 'reference_number',
              unique=True,
              postgresql_where="reference_number IS NOT NULL"),
    )
    
    loanpaymentid = Column(Integer, primary_key=True, index=True)
    loan_agreement_id = Column(Integer, ForeignKey("loan_agreements.agreement_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Payment details
    amount_paid = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String(50), nullable=False)  # cash, bank_transfer, mobile_money
    
    # How it was allocated
    principal_paid = Column(Float, nullable=False)
    interest_paid = Column(Float, nullable=False)
    penalty_paid = Column(Float, default=0.0)

    
    # Which installments this covers (e.g., "1,2,3" or "1-3")
    installments_covered = Column(String(200), nullable=True)
    
    # Reference
    reference_number = Column(String(100), nullable=True)
    receipt_path = Column(String(500), nullable=True)  # Uploaded receipt image
    
    # Admin who recorded this
    recorded_by = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    loan_agreement = relationship("LoanAgreement", back_populates="payments")
    user = relationship("User")


class AuditLog(Base):
    """Audit log for tracking all administrative actions on loans"""
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False)  # approve, reject, review, disburse, record_payment, recalculate_late_fees
    performed_by = Column(String(50), nullable=False)  # employee_id
    target_type = Column(String(50), nullable=False)  # loan_application, loan_agreement, loan_payment
    target_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LoanAgreementSignature (Base):
    __tablename__= "loan_agreement_signatures"

    signature_id = Column (Integer, primary_key=True, index=True)
    agreement_id = Column (Integer, ForeignKey ("loan_agreements.agreement_id"), nullable=False)
    user_id = Column (Integer, ForeignKey ("users.user_id"), nullable =False )
    signed_name = Column (String(255), nullable=False)
    agreed_to_terms = Column (Boolean, default=True)
    signature_hash = Column (String(255), nullable = True)
    signed_at = Column (DateTime(timezone=True), server_default=func.now())
    ip_address = Column (String(45), nullable = True)
    user_agent = Column (String(45), nullable = True)
    signature_type = Column (String(20), default="typed")
    verification_token = Column (String(255), nullable = True) #for emal verification
    token_expires_at = Column (DateTime(timezone=True))
    is_valid = Column (Boolean, default=True)

     # Relationships
    agreement = relationship("LoanAgreement", back_populates="signature")
    user = relationship("User")

    