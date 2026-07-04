from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from database import models
from schemas import loanapplication as loan_app_schemas
from datetime import datetime, timedelta, date
from utils.email_templates import get_loan_approved_email, get_loan_disbursed_email, get_payment_receipt_email
from utils.email import send_email
import logging
import os

logger = logging.getLogger(__name__)


def create_audit_log(db: Session, action: str, performed_by: str,
                     target_type: str, target_id: int, details: str = None):
    """Create an audit log entry for administrative actions"""
    log_entry = models.AuditLog(
        action=action,
        performed_by=performed_by,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.add(log_entry)
    # Note: caller is responsible for commit


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
    apps = db.query(models.LoanApplication).options(
        joinedload(models.LoanApplication.loan_agreement)
    ).filter(
        models.LoanApplication.user_id == user_id
    ).order_by(models.LoanApplication.created_at.desc()).offset(skip).limit(limit).all()
    
    for app in apps:
        app.agreement_id = app.loan_agreement.agreement_id if app.loan_agreement else None
    
    return apps

def get_application_by_id(db: Session, application_id: int):
    """Get a specific loan application by ID"""
    app = db.query(models.LoanApplication).options(
        joinedload(models.LoanApplication.loan_agreement)
    ).filter(
        models.LoanApplication.application_id == application_id
    ).first()
    
    if app:
        app.agreement_id = app.loan_agreement.agreement_id if app.loan_agreement else None
    
    return app

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
    
    create_audit_log(db, "reject", staff_id, "loan_application", application_id,
                     f"Application rejected. Reason: {rejection_reason}")
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
    
    create_audit_log(db, "review", staff_id, "loan_application", application_id,
                     f"Application marked as under_review")
    db.commit()
    db.refresh(application)
    
    return application


def calculate_amortization_schedule(principal, annual_rate, months):
    """Calculate monthly payment and generate payment schedule"""
    monthly_rate = annual_rate / 100 / 12
    
    if monthly_rate == 0:
        monthly_payment = principal / months
    else:
        # Standard amortization formula
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

    monthly_payment = round(monthly_payment, 2)
    total_repayment = round (monthly_payment * months, 2)
    total_interest = round (total_repayment - principal, 2)
    
    # Generate individual payment schedule
    schedule = []
    remaining = principal
    
    for month in range(1, months + 1):
        interest_due = round (remaining * monthly_rate, 2)
        principal_due = round (monthly_payment - interest_due, 2)
        
        if month == months:  # Last month adjustment for rounding
            principal_due = round (remaining, 2)
            monthly_payment = round (principal_due + interest_due, 2)
        
        remaining = round (remaining - principal_due, 2)
        
        schedule.append({
            "installment_number": month,
            "principal_due": round(principal_due, 2),
            "interest_due": round(interest_due, 2),
            "amount_due": round(principal_due + interest_due, 2),
            "remaining_principal": round(max(remaining, 0), 2)
        })
    
    # Compute total_repayment from actual installment amounts to avoid rounding discrepancy
    total_repayment = round(sum(item["amount_due"] for item in schedule), 2)
    total_interest = round(total_repayment - principal, 2)
    
    return {
        "monthly_payment": monthly_payment,
        "total_repayment": total_repayment,
        "total_interest": total_interest,
        "schedule": schedule
    }

# CREATE LOAN AGREEMENT AND SCHEDULE FOR THE APPROVED APPLICATION
def approve_application(
    db: Session,
    application_id: int,
    staff_id: str,
    approved_amount: float = None,
    interest_rate: float = None,
    duration_months: int = None,
    approval_notes: str = None,
):
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
    approval_date = datetime.now()
    agreement = models.LoanAgreement(
        application_id=application_id,
        user_id=application.user_id,
        approved_amount=final_amount,
        interest_rate=final_rate,
        duration_months=final_duration,
        monthly_payment=calculation["monthly_payment"],
        total_repayment=calculation["total_repayment"],
        total_interest=calculation["total_interest"],
        approval_date=approval_date,
        first_payment_date=approval_date + timedelta(days=30),
        approved_by=staff_id,
        approval_notes=approval_notes,
        status="approved"
    )
    db.add(agreement)
    db.flush()  # Get agreement ID without committing
    
    # Generate repayment schedule
    for installment in calculation["schedule"]:
        due_date = approval_date + timedelta(days=30 * installment["installment_number"])
        
        schedule_item = models.LoanRepaymentSchedule(
            loan_agreement_id=agreement.agreement_id,
            user_id=application.user_id,
            installment_number=installment["installment_number"],
            due_date=due_date,
            amount_due=installment["amount_due"],
            principal_due=installment["principal_due"],
            interest_due=installment["interest_due"],
            remaining_principal=installment["remaining_principal"],
            total_due=installment["amount_due"],
            status="pending"
        )
        db.add(schedule_item)

    # Update application status
    application.status = "approved"
    application.reviewed_by = staff_id
    application.reviewed_at = datetime.now()
    application.review_notes = approval_notes
    
    create_audit_log(db, "approve", staff_id, "loan_application", application_id,
                     f"Loan approved. Amount: {final_amount}, Rate: {final_rate}%, Duration: {final_duration}m")
    db.commit()

    # After the commit, send the email (non-critical — don't rollback if it fails)
    try:
        user = db.query(models.User).filter(models.User.user_id == application.user_id).first()
        if user:
            subject, html = get_loan_approved_email(
                user.name,
                final_amount,
                calculation["monthly_payment"],
                final_rate,
                final_duration,
                agreement.agreement_id,
            )
            send_email(user.email, subject, html)
    except Exception:
        logger.exception("Failed to send approval email for application_id=%s", application_id)
    
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
    
     # Check if agreement is signed
    if agreement.signing_status != "signed":
        return None, "Cannot disburse: Agreement has not been signed by client"

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
    if notes:
        agreement.disbursement_notes = notes
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
    
    create_audit_log(db, "disburse", staff_id, "loan_agreement", loan_agreement_id,
                     f"Loan disbursed. Amount: {agreement.approved_amount}")
    db.commit()

    # Send email after commit — non-critical
    try:
        user = db.query(models.User).filter(models.User.user_id == agreement.user_id).first()
        if user:
            subject, html = get_loan_disbursed_email(
                user.name,
                agreement.first_payment_date,
                agreement.monthly_payment,
            )
            send_email(user.email, subject, html)
    except Exception:
        logger.exception("Failed to send disbursement email for agreement_id=%s", loan_agreement_id)
    
    return agreement, "Loan disbursed successfully"


# RECORD PAYMENTS MADE WHEN STARTING TO PAY BACK - AND CALCULATE AND APPLY LATE FEES
def record_payment(db: Session, loan_agreement_id: int, staff_id: str, 
                   amount_paid: float, payment_method: str, 
                   reference_number: str = None, notes: str = None,
                   payment_date: datetime = None):
    """Record a payment - late fee is already calculated by daily job"""
    
    # Lock the loan agreement row to prevent concurrent modifications
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == loan_agreement_id
    ).with_for_update().first()
    
    if not agreement:
        return None, "Loan agreement not found"
    
    if agreement.status not in ["disbursed", "active"]:
        return None, f"Cannot record payment for loan with status: {agreement.status}"
    
    # Validate payment_date is not in the future
    if payment_date is None:
        payment_date = datetime.now()
    elif payment_date.date() > date.today():
        return None, "Payment date cannot be in the future"
    
    # Check for duplicate reference_number
    if reference_number:
        existing_payment = db.query(models.LoanPayment).filter(
            and_(
                models.LoanPayment.loan_agreement_id == loan_agreement_id,
                models.LoanPayment.reference_number == reference_number
            )
        ).first()
        if existing_payment:
            return None, f"A payment with reference number '{reference_number}' already exists for this loan"
    
    # Lock and fetch pending installments (oldest first)
    pending_installments = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id,
        models.LoanRepaymentSchedule.status.in_(["pending", "late", "partial"])
    ).order_by(models.LoanRepaymentSchedule.installment_number).with_for_update().all()
    
    if not pending_installments:
        return None, "No pending installments found for this loan"
    
    # Calculate total outstanding balance to reject overpayments
    total_outstanding = sum(
        (item.total_due - item.paid_amount) for item in pending_installments
    )
    if amount_paid > round(total_outstanding, 2):
        return None, f"Payment amount ${amount_paid:.2f} exceeds total outstanding balance of ${total_outstanding:.2f}"
    
    remaining_amount = amount_paid
    installments_affected = []
    total_principal = 0
    total_interest = 0
    total_late_fee = 0
    
    for installment in pending_installments:
        if remaining_amount <= 0:
            break
        
        # Get total due (already includes late fee from daily job)
        total_due = installment.total_due
        remaining_due = total_due - installment.paid_amount
        
        if remaining_amount >= remaining_due:
            # Full payment for this installment
            # Calculate late fee portion for this installment
            late_fee_remaining = installment.late_fee - (installment.paid_amount if installment.paid_amount < installment.late_fee else 0)
            late_fee_portion = min(late_fee_remaining, remaining_amount) if late_fee_remaining > 0 else 0
            if late_fee_portion > 0:
                installment.penalty_paid = True 
            
            # Calculate normal payment portion
            normal_payment = remaining_due - late_fee_portion
            
            # Calculate principal/interest split from normal payment
            if installment.amount_due > 0:
                payment_ratio = normal_payment / installment.amount_due
                principal_portion = round(installment.principal_due * payment_ratio, 2)
                interest_portion = round(installment.interest_due * payment_ratio, 2)
            else:
                principal_portion = 0
                interest_portion = 0
            
            installment.status = "paid"
            installment.paid_amount = total_due
            installment.paid_date = payment_date
            
            total_principal += principal_portion
            total_interest += interest_portion
            total_late_fee += late_fee_portion
            remaining_amount -= remaining_due
            installments_affected.append(str(installment.installment_number))
            
        else:
            # Partial payment - apply to late fee first
            late_fee_remaining = installment.late_fee - max(0, installment.paid_amount)
            
            if late_fee_remaining > 0:
                late_fee_portion = min(late_fee_remaining, remaining_amount)
                total_late_fee += late_fee_portion
                installment.paid_amount += late_fee_portion
                remaining_amount -= late_fee_portion
            
            # If still money left, apply to normal payment
            if remaining_amount > 0:
                normal_remaining = installment.amount_due - max(0, installment.paid_amount - installment.late_fee)
                normal_portion = min(normal_remaining, remaining_amount)
                
                if installment.amount_due > 0:
                    payment_ratio = normal_portion / installment.amount_due
                    principal_portion = round(installment.principal_due * payment_ratio, 2)
                    interest_portion = round(installment.interest_due * payment_ratio, 2)
                else:
                    principal_portion = 0
                    interest_portion = 0
                
                total_principal += principal_portion
                total_interest += interest_portion
                installment.paid_amount += normal_portion
                remaining_amount -= normal_portion
            
            installment.status = "partial"
            installment.paid_date = payment_date
            installments_affected.append(f"{installment.installment_number}(partial)")
            break
    
    # Verify all payment amount is accounted for within precision limits
    allocated = round(total_principal + total_interest + total_late_fee, 2)
    if abs(allocated - amount_paid) > 0.02:
        # Adjust the largest component to absorb rounding
        diff = round(amount_paid - allocated, 2)
        total_principal = round(total_principal + diff, 2)
        logger.warning(f"Payment allocation rounding adjustment: {diff}")
    
    # Create payment record
    payment_record = models.LoanPayment(
        loan_agreement_id=loan_agreement_id,
        user_id=agreement.user_id,
        amount_paid=amount_paid,
        payment_date=payment_date,
        payment_method=payment_method,
        principal_paid=round(total_principal, 2),
        interest_paid=round(total_interest, 2),
        penalty_paid=round(total_late_fee, 2),
        installments_covered=",".join(installments_affected),
        reference_number=reference_number,
        recorded_by=staff_id,
        notes=notes
    )
    db.add(payment_record)
    
    # Check if all installments are paid
    remaining_pending = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id,
        models.LoanRepaymentSchedule.status.in_(["pending", "late", "partial"])
    ).count()
    
    if remaining_pending == 0:
        agreement.status = "completed"
        agreement.completed_date = datetime.now()
    elif agreement.status == "disbursed":
        agreement.status = "active"
    
    create_audit_log(db, "record_payment", staff_id, "loan_agreement", loan_agreement_id,
                     f"Payment ${amount_paid:.2f} recorded. Installments: {','.join(installments_affected)}. Method: {payment_method}")
    db.commit()
    
    # Send payment receipt email after commit
    try:
        user = db.query(models.User).filter(models.User.user_id == agreement.user_id).first()
        if user:
            # Compute remaining balance and next due date
            remaining_installments = db.query(models.LoanRepaymentSchedule).filter(
                models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id,
                models.LoanRepaymentSchedule.status.in_(["pending", "late", "partial"])
            ).order_by(models.LoanRepaymentSchedule.installment_number).all()
            remaining_balance = round(sum(
                (s.total_due - s.paid_amount) for s in remaining_installments
            ), 2) if remaining_installments else 0
            next_due = remaining_installments[0].due_date if remaining_installments else None

            subject, html = get_payment_receipt_email(
                user.name,
                amount_paid,
                ",".join(installments_affected),
                remaining_balance,
                payment_method=payment_method,
                principal_paid=round(total_principal, 2),
                interest_paid=round(total_interest, 2),
                penalty_paid=round(total_late_fee, 2),
                next_due_date=next_due.strftime('%B %d, %Y') if next_due else None,
                agreement_id=loan_agreement_id
            )
            send_email(user.email, subject, html)
    except Exception:
        logger.exception("Failed to send payment receipt email for agreement_id=%s", loan_agreement_id)
    
    return payment_record, f"Payment recorded successfully. Installments: {','.join(installments_affected)}"


# FUNCTION THAT RUNS DAILY TO GET THE FEES
def update_daily_late_fees(db: Session):
    """Run daily to update late fees for all overdue installments"""
    
    today = datetime.now().date()
    grace_days = int(os.getenv("LATE_FEE_GRACE_DAYS", 7))
    base_rate = float(os.getenv("LATE_FEE_BASE_RATE", 2.0))
    increment_rate = float(os.getenv("LATE_FEE_INCREMENT_RATE", 1.0))
    max_rate = float(os.getenv("LATE_FEE_MAX_RATE", 20.0))
    
    # Find all overdue installments needing late fee recalculation
    # Include partial (partially paid but overdue) and defaulted statuses
    overdue = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.due_date < today,
        models.LoanRepaymentSchedule.status.in_(["pending", "late", "partial", "defaulted"])
    ).all()
    
    updated_count = 0
    
    for installment in overdue:
        due_date = installment.due_date.date()
        days_late = (today - due_date).days
        
        # No fee during grace period
        if days_late <= grace_days:
            # Preserve "partial" status so partial payments aren't lost
            if installment.status != "partial":
                installment.status = "pending"
            installment.days_late = 0
            installment.late_fee = 0.0
        else:
            # Calculate late fee based on days late
            days_after_grace = days_late - grace_days
            additional_months = days_after_grace // 30
            rate = base_rate + (additional_months * increment_rate)
            rate = min(rate, max_rate)
            
            late_fee = installment.amount_due * (rate / 100)
            installment.late_fee = round(late_fee, 2)
            installment.status = "late"
            installment.days_late = days_late
            installment.late_fee_updated_at = datetime.now()
        
        # Update total due
        installment.total_due = installment.amount_due + installment.late_fee
        
        # If already partially paid, adjust total_due
        if installment.paid_amount > 0:
            if installment.paid_amount >= installment.total_due:
                installment.status = "paid"
        
        updated_count += 1
    
    if updated_count > 0:
        create_audit_log(db, "recalculate_late_fees", "system", "loan_agreement", 0,
                         f"Late fees recalculated for {updated_count} overdue installments")
    db.commit()
    return updated_count


def get_loans_for_payment(db: Session):
    """Get all loan agreements eligible for payment recording (disbursed or active) with computed fields"""
    agreements = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.status.in_(["disbursed", "active"])
    ).order_by(models.LoanAgreement.agreement_id.desc()).all()

    result = []
    for agreement in agreements:
        schedule_items = db.query(models.LoanRepaymentSchedule).filter(
            models.LoanRepaymentSchedule.loan_agreement_id == agreement.agreement_id
        ).order_by(models.LoanRepaymentSchedule.installment_number).all()

        total_paid = sum(
            item.paid_amount or 0 for item in schedule_items
        )
        outstanding_balance = round(agreement.total_repayment - total_paid, 2)

        pending_installments = [s for s in schedule_items if s.status in ("pending", "late", "partial")]
        remaining_installments = len(pending_installments)
        next_installment = pending_installments[0] if pending_installments else None

        application = db.query(models.LoanApplication).filter(
            models.LoanApplication.application_id == agreement.application_id
        ).first()

        client_name = agreement.user.name if agreement.user else (application.full_name if application else "Unknown")
        client_email = agreement.user.email if agreement.user else (application.email_address if application else None)
        client_phone = application.phone_number if application else None

        result.append({
            "agreement_id": agreement.agreement_id,
            "application_id": agreement.application_id,
            "user_id": agreement.user_id,
            "client_name": client_name,
            "client_email": client_email,
            "client_phone": client_phone,
            "approved_amount": agreement.approved_amount,
            "interest_rate": agreement.interest_rate,
            "duration_months": agreement.duration_months,
            "monthly_payment": agreement.monthly_payment,
            "total_repayment": agreement.total_repayment,
            "outstanding_balance": outstanding_balance,
            "total_paid": total_paid,
            "status": agreement.status,
            "signing_status": agreement.signing_status,
            "disbursement_date": agreement.disbursement_date,
            "first_payment_date": agreement.first_payment_date,
            "final_payment_date": agreement.final_payment_date,
            "next_due_date": next_installment.due_date.isoformat() if next_installment and next_installment.due_date else None,
            "next_installment_amount": next_installment.total_due if next_installment else 0,
            "remaining_installments": remaining_installments,
        })

    return result