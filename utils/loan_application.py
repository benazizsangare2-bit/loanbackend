from sqlalchemy.orm import Session
from database import models
from schemas import loanapplication as loan_app_schemas
from datetime import datetime, timedelta


def create_loan_application(
    db: Session, 
    user_id: int, 
    application_data: loan_app_schemas.LoanApplicationCreate
):
    """Create a new loan application"""
    db_application = models.LoanApplication(
        user_id=user_id,
        full_name=application_data.full_name,
        gender=application_data.gender,
        date_of_birth=application_data.date_of_birth,
        national_id=application_data.national_id,
        phone_number=application_data.phone_number,
        email_address=application_data.email_address,
        marital_status=application_data.marital_status,
        number_of_dependents=application_data.number_of_dependents,
        residential_address=application_data.residential_address,
        city=application_data.city,
        country=application_data.country,
        gps_location=application_data.gps_location,
        employment_status=application_data.employment_status,
        employer_name=application_data.employer_name,
        job_title=application_data.job_title,
        monthly_salary=application_data.monthly_salary,
        length_of_employment_years=application_data.length_of_employment_years,
        business_name=application_data.business_name,
        business_type=application_data.business_type,
        business_location=application_data.business_location,
        monthly_business_income=application_data.monthly_business_income,
        years_in_business=application_data.years_in_business,
        monthly_income=application_data.monthly_income,
        other_income_sources=application_data.other_income_sources,
        other_income_amount=application_data.other_income_amount,
        monthly_expenses=application_data.monthly_expenses,
        has_existing_loans=application_data.has_existing_loans,
        existing_loan_details=application_data.existing_loan_details,
        savings_balance=application_data.savings_balance,
        bank_name=application_data.bank_name,
        bank_account_number=application_data.bank_account_number,
        amount_requested=application_data.amount_requested,
        loan_purpose=application_data.loan_purpose,
        duration_requested=application_data.duration_requested,
        preferred_repayment_method=application_data.preferred_repayment_method,
        has_collateral=application_data.has_collateral,
        collateral_description=application_data.collateral_description,
        has_guarantor=application_data.has_guarantor,
        guarantor_name=application_data.guarantor_name,
        guarantor_relationship=application_data.guarantor_relationship,
        guarantor_phone=application_data.guarantor_phone,
        guarantor_address=application_data.guarantor_address,
        guarantor_occupation=application_data.guarantor_occupation,
        guarantor_id_number=application_data.guarantor_id_number,
        national_id_document_path=application_data.national_id_document_path,
        proof_of_address_path=application_data.proof_of_address_path,
        salary_slip_path=application_data.salary_slip_path,
        business_license_path=application_data.business_license_path,
        bank_statement_path=application_data.bank_statement_path,
        collateral_document_path=application_data.collateral_document_path,
        status="pending"
    )
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

# FUNCTION THAT CREATES A NEW DRAFT APPLICATION FOR EACH USERS 
def create_draft_application(db: Session, user_id: int):
    """Create a new empty draft application for a user"""
    # Check if user already has a draft
    existing_draft = db.query(models.LoanApplication).filter(
        models.LoanApplication.user_id == user_id,
        models.LoanApplication.status == "draft"
    ).first()
    
    if existing_draft:
        return existing_draft, "Draft already exists"
    
    # Create new draft with only user_id and status
    draft = models.LoanApplication(
        user_id=user_id,
        status="draft"
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    
    return draft, "New draft created"


# Function to update the draft application anytime before submitting
def update_application_partial(db: Session, application_id: int, user_id: int, update_data: dict):
    """Update only the fields provided in update_data"""
    application = db.query(models.LoanApplication).filter(
        models.LoanApplication.application_id == application_id,
        models.LoanApplication.user_id == user_id
    ).first()
    
    if not application:
        return None, "Application not found"
    
    if application.status != "draft":
        return None, f"Cannot update application with status: {application.status}. Only drafts can be edited."
    
    # Update only the fields that were provided
    for key, value in update_data.items():
        if hasattr(application, key) and value is not None:
            setattr(application, key, value)
    
    db.commit()
    db.refresh(application)
    
    return application, "Application updated successfully"


# function to get the user's draft application
def get_user_draft(db: Session, user_id: int):
    """Get the active draft application for a user"""
    draft = db.query(models.LoanApplication).filter(
        models.LoanApplication.user_id == user_id,
        models.LoanApplication.status == "draft"
    ).first()
    
    return draft

# Submit application at the end
def submit_application(db: Session, application_id: int, user_id: int):
    """Submit a draft application for review"""
    application = db.query(models.LoanApplication).filter(
        models.LoanApplication.application_id == application_id,
        models.LoanApplication.user_id == user_id
    ).first()
    
    if not application:
        return None, "Application not found"
    
    if application.status != "draft":
        return None, f"Cannot submit application with status: {application.status}"
    
    # Define required fields for submission (adjust as needed)
    required_fields = [
        "amount_requested", "loan_purpose", "duration_requested",
        "employment_status", "monthly_income",
        "residential_address", "city", "national_id"
    ]
    
    # Check which required fields are missing
    missing_fields = []
    for field in required_fields:
        if getattr(application, field) is None:
            missing_fields.append(field)
    
    if missing_fields:
        return None, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Update application status
    application.status = "pending"
    application.submitted_at = datetime.now()
    db.commit()
    db.refresh(application)
    
    return application, "Application submitted successfully"


# get a specific user's application
def get_user_applications(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all loan applications for a specific user"""
    return db.query(models.LoanApplication).filter(
        models.LoanApplication.user_id == user_id
    ).order_by(models.LoanApplication.created_at.desc()).offset(skip).limit(limit).all()

def get_application_by_id(db: Session, application_id: int):
    """Get a specific loan application by ID"""
    return db.query(models.LoanApplication).filter(
        models.LoanApplication.application_id == application_id
    ).first()

def get_all_applications(db: Session, status: str = None, skip: int = 0, limit: int = 100):
    """Get all loan applications (admin use)"""
    query = db.query(models.LoanApplication)
    if status:
        query = query.filter(models.LoanApplication.status == status)
    return query.order_by(models.LoanApplication.created_at.desc()).offset(skip).limit(limit).all()

def update_application_status(
    db: Session, 
    application_id: int, 
    status: str, 
    reviewed_by: str = None,
    review_notes: str = None,
    rejection_reason: str = None
):
    """Update loan application status (admin use)"""
    application = get_application_by_id(db, application_id)
    if application:
        application.status = status
        application.reviewed_at = datetime.now()
        if reviewed_by:
            application.reviewed_by = reviewed_by
        if review_notes:
            application.review_notes = review_notes
        if rejection_reason:
            application.rejection_reason = rejection_reason
        db.commit()
        db.refresh(application)
    return application


#Add Admin Functions for the loan application
def get_pending_applications(db: Session, skip: int = 0, limit: int = 100):
    """Get all pending applications for admin review"""
    return db.query(models.LoanApplication).filter(
        models.LoanApplication.status == "pending"
    ).order_by(models.LoanApplication.created_at.asc()).offset(skip).limit(limit).all()

def get_application_by_id_admin(db: Session, application_id: int):
    """Get application by ID without user restriction (admin use)"""
    return db.query(models.LoanApplication).filter(
        models.LoanApplication.application_id == application_id
    ).first()

def get_all_applications_admin(db: Session, status: str = None, skip: int = 0, limit: int = 100):
    """Get all applications with optional status filter (admin use)"""
    query = db.query(models.LoanApplication)
    if status:
        query = query.filter(models.LoanApplication.status == status)
    return query.order_by(models.LoanApplication.created_at.desc()).offset(skip).limit(limit).all()


def reject_application(
    db: Session, 
    application_id: int, 
    staff_id: str,
    rejection_reason: str,
    review_notes: str = None
):
    """Reject a loan application"""
    application = get_application_by_id_admin(db, application_id)
    if not application:
        return None
    
    if application.status not in ["pending", "under_review", "approved"]:
        raise ValueError(f"Cannot reject application with status: {application.status}. Expected 'pending' or 'under_review'")
    
    # Update application
    application.status = "rejected"
    application.reviewed_by = staff_id
    application.reviewed_at = datetime.now()
    application.rejection_reason = rejection_reason
    application.review_notes = review_notes
    
    db.commit()
    db.refresh(application)
    
    return application

def mark_under_review(
    db: Session, 
    application_id: int, 
    staff_id: str
):
    """Mark application as under review"""
    application = get_application_by_id_admin(db, application_id)
    if not application:
        return None
    
    if application.status not in ["pending", "under_review"]:
        raise ValueError(f"Application status is {application.status}, not pending")
    
    application.status = "under_review"
    application.reviewed_by = staff_id
    application.reviewed_at = datetime.now()
    
    db.commit()
    db.refresh(application)
    
    return application


def calculate_amortization_schedule(principal, annual_rate, months):
    """Calculate monthly payment and generate payment schedule"""
    monthly_rate = annual_rate / 100 / 12
    
    if monthly_rate == 0:
        monthly_payment = principal / months
    else:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    
    total_repayment = monthly_payment * months
    total_interest = total_repayment - principal
    
    # Generate individual payment schedule
    schedule = []
    remaining = principal
    
    for month in range(1, months + 1):
        interest_due = remaining * monthly_rate
        principal_due = monthly_payment - interest_due
        
        if month == months:  # Last month adjustment for rounding
            principal_due = remaining
            monthly_payment = principal_due + interest_due
        
        remaining -= principal_due
        
        schedule.append({
            "installment_number": month,
            "principal_due": round(principal_due, 2),
            "interest_due": round(interest_due, 2),
            "amount_due": round(principal_due + interest_due, 2),
            "remaining_principal": round(max(remaining, 0), 2)
        })
    
    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_repayment": round(total_repayment, 2),
        "total_interest": round(total_interest, 2),
        "schedule": schedule
    }

# CREATE LOAN AGREEMENT AND SCHEDULE FOR THE APPROVED APPLICATION
def approve_application(db: Session, application_id: int, staff_id: str, 
                        approved_amount: float = None, 
                        interest_rate: float = None,
                        duration_months: int = None,
                        disbursement_date: datetime = None,
                        approval_notes: str = None):
    """Approve a loan application - creates agreement and payment schedule"""
    
    application = get_application_by_id_admin(db, application_id)
    if not application:
        return None, "Application not found"
    
    if application.status not in ["pending", "under_review"]:
        return None, f"Cannot approve application with status: {application.status}"
    
    # Use provided values or defaults from application
    final_amount = approved_amount or application.amount_requested
    final_rate = interest_rate or 15.0  # Default 15% if not specified
    final_duration = duration_months or application.duration_requested
    
    # Calculate loan terms
    calculation = calculate_amortization_schedule(final_amount, final_rate, final_duration)
    
    # Create loan agreement
    agreement = models.LoanAgreement(
        application_id=application_id,
        user_id=application.user_id,
        approved_amount=final_amount,
        interest_rate=final_rate,
        duration_months=final_duration,
        monthly_payment=calculation["monthly_payment"],
        total_repayment=calculation["total_repayment"],
        total_interest=calculation["total_interest"],
        approval_date=datetime.now(),
        approved_by=staff_id,
        approval_notes=approval_notes,
        status="approved"
    )
    db.add(agreement)
    db.flush()  # Get agreement ID without committing
    
    # Generate repayment schedule
    for installment in calculation["schedule"]:
        
        schedule_item = models.LoanRepaymentSchedule(
            loan_agreement_id=agreement.agreement_id,
            user_id=application.user_id,
            installment_number=installment["installment_number"],
            due_date=None,
            amount_due=installment["amount_due"],
            principal_due=installment["principal_due"],
            interest_due=installment["interest_due"],
            remaining_principal=installment["remaining_principal"],
            status="pending"
        )
        db.add(schedule_item)
    
    # Update application status
    application.status = "approved"
    application.reviewed_by = staff_id
    application.reviewed_at = datetime.now()
    application.review_notes = approval_notes
    
    db.commit()
    
    return application, "Loan approved successfully"


# PROFF THAT THE CLIENT RECEIVED THEIR LOAN MONEY
def mark_disbursed(db: Session, loan_agreement_id: int, staff_id: str, 
                   disbursement_date: datetime = None, notes: str = None):
    """Mark loan as disbursed and calculate all due dates"""
    
    # Get the loan agreement
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == loan_agreement_id
    ).first()
    
    if not agreement:
        return None, "Loan agreement not found"
    
    # Only approved loans can be disbursed
    if agreement.status != "approved":
        return None, f"Cannot disburse loan with status: {agreement.status}. Expected 'approved'"
    
    # Set disbursement date (today if not provided)
    if disbursement_date is None:
        disbursement_date = datetime.now()
    
    # Update agreement
    agreement.disbursement_date = disbursement_date
    agreement.disbursed_by = staff_id
    agreement.status = "disbursed"
    agreement.first_payment_date = disbursement_date + timedelta(days=30)
    agreement.final_payment_date = disbursement_date + timedelta(days=30 * agreement.duration_months)
    
    # Get all schedule items for this loan
    schedule_items = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id
    ).order_by(models.LoanRepaymentSchedule.installment_number).all()
    
    if not schedule_items:
        return None, "No repayment schedule found for this loan"
    
    # Calculate and set due dates for each installment
    for item in schedule_items:
        # Due date = disbursement_date + (30 days × installment number)
        item.due_date = disbursement_date + timedelta(days=30 * item.installment_number)
        # Status remains "pending"
    
    db.commit()
    
    return agreement, "Loan disbursed successfully"


# RECORD PAYMENTS MADE WHEN STARTING TO PAY BACK
def record_payment(db: Session, loan_agreement_id: int, staff_id: str, 
                   amount_paid: float, payment_method: str, 
                   reference_number: str = None, notes: str = None):
    """
    Record a payment made by client
    Automatically allocates to oldest pending installment first
    """
    
    # Get loan agreement
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == loan_agreement_id
    ).first()
    
    if not agreement:
        return None, "Loan agreement not found"
    
    # Check if loan is in active/disbursed status
    if agreement.status not in ["disbursed", "active"]:
        return None, f"Cannot record payment for loan with status: {agreement.status}"
    
    # Get all pending installments (oldest first)
    pending_installments = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id,
        models.LoanRepaymentSchedule.status.in_(["pending", "partial"])
    ).order_by(models.LoanRepaymentSchedule.installment_number).all()
    
    if not pending_installments:
        return None, "No pending installments found for this loan"
    
    remaining_amount = amount_paid
    installments_affected = []
    total_principal = 0
    total_interest = 0
    
    # Apply payment to installments
    for installment in pending_installments:
        if remaining_amount <= 0:
            break
        
        # Calculate remaining due for this installment
        remaining_due = installment.amount_due - installment.paid_amount
        
        if remaining_amount >= remaining_due:
            # Full payment for this installment
            paid_principal = installment.principal_due - (installment.principal_due * (installment.paid_amount / installment.amount_due)) if installment.paid_amount > 0 else installment.principal_due
            paid_interest = installment.interest_due - (installment.interest_due * (installment.paid_amount / installment.amount_due)) if installment.paid_amount > 0 else installment.interest_due
            
            installment.status = "paid"
            installment.paid_amount = installment.amount_due
            installment.paid_date = datetime.now()
            
            total_principal += paid_principal
            total_interest += paid_interest
            remaining_amount -= remaining_due
            installments_affected.append(str(installment.installment_number))
            
        else:
            # Partial payment
            # Calculate ratio of payment to determine principal/interest split
            payment_ratio = remaining_amount / installment.amount_due
            paid_principal = round(installment.principal_due * payment_ratio, 2)
            paid_interest = round(installment.interest_due * payment_ratio, 2)
            
            installment.status = "partial"
            installment.paid_amount += remaining_amount
            installment.paid_date = datetime.now()
            
            total_principal += paid_principal
            total_interest += paid_interest
            installments_affected.append(f"{installment.installment_number}(partial)")
            remaining_amount = 0
    
    # Create payment record
    payment_record = models.LoanPayment(
        loan_agreement_id=loan_agreement_id,
        user_id=agreement.user_id,
        amount_paid=amount_paid,
        payment_date=datetime.now(),
        payment_method=payment_method,
        principal_paid=round(total_principal, 2),
        interest_paid=round(total_interest, 2),
        penalty_paid=0,
        installments_covered=",".join(installments_affected),
        reference_number=reference_number,
        recorded_by=staff_id,
        notes=notes
    )
    db.add(payment_record)
    
    # Check if all installments are paid
    remaining_pending = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id,
        models.LoanRepaymentSchedule.status.in_(["pending", "partial"])
    ).count()
    
    if remaining_pending == 0:
        agreement.status = "completed"
        agreement.completed_date = datetime.now()
    elif agreement.status == "disbursed":
        agreement.status = "active"
    
    db.commit()
    
    return payment_record, f"Payment recorded successfully. Affected installments: {','.join(installments_affected)}"