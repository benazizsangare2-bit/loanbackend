
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database import models
from routers.loan_application import get_current_user
from schemas import loanapplication as loan_app_schemas
from utils import loan_application as loan_app_utils
from utils import auth as auth_utils
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


adminrouter = APIRouter(prefix="/loans", tags=["loan applications"])
security = HTTPBearer()


# GET THE LIST OF THE CURRENT ADMINS 
def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current staff member and verify they are admin"""
    token = credentials.credentials
    payload = auth_utils.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check if this is a staff token
    if payload.get("type") != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    email = payload.get("sub")
    staff = db.query(models.Staff).filter(models.Staff.email == email).first()
    if not staff:
        raise HTTPException(status_code=401, detail="Staff not found")
    
    if not staff.is_active:
        raise HTTPException(status_code=403, detail="Staff account is deactivated")
    
    return staff  # Return staff directly, not a dictionary



# GET THE LIST OF ALL PENDING APPLICATIONS
@adminrouter.get("/pending", response_model=list[loan_app_schemas.LoanApplicationResponse])
def get_pending_applications(
    skip: int = 0,
    limit: int = 100,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all pending loan applications for review"""
    return loan_app_utils.get_pending_applications(db, skip, limit)


# GET ALL THE CURRENT LOAN APPLICATINO WITH FILTER
@adminrouter.get("/all", response_model=list[loan_app_schemas.LoanApplicationResponse])
def get_all_applications(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all loan applications with optional status filter"""
    return loan_app_utils.get_all_applications_admin(db, status, skip, limit)


# GET INFORMATION ABOUT A SPECIFIC LOAN APPLICATION
@adminrouter.get("/{application_id}", response_model=loan_app_schemas.LoanApplicationResponse)
def get_application_detail(
    application_id: int,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific application"""
    application = loan_app_utils.get_application_by_id_admin(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


# MARK AN APPLICATION AS UNDER_REVIEW 
@adminrouter.put("/{application_id}/review")
def mark_as_under_review(
    application_id: int,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark an application as under review"""
    try:
        application = loan_app_utils.mark_under_review(
            db, application_id, current_staff.employee_id
        )
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        return {"message": "Application marked as under review", "application_id": application_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# MARK AN APPLICATION AS APPROVED
@adminrouter.put("/{application_id}/approve")
def approve_application(
    application_id: int,
    approved_amount: Optional[float] = None,
    interest_rate: Optional[float] = None,
    duration_months: Optional[int] = None,
    approval_notes: Optional[str] = None,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve a loan application with custom terms"""
    
    if not current_staff.can_approve_loans:
        raise HTTPException(status_code=403, detail="You don't have permission to approve loans")
    
    application, message = loan_app_utils.approve_application(
        db, application_id, current_staff.employee_id,
        approved_amount, interest_rate, duration_months, approval_notes
    )
    
    if not application:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message, "application_id": application_id, "loan_agreement_id": application.loan_agreement.agreement_id}


# MARK AN APPLICATION AS REJECTED
@adminrouter.put("/{application_id}/reject")
def reject_application(
    application_id: int,
    rejection_reason: str,
    review_notes: Optional[str] = None,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reject a loan application"""
    # Check if staff has permission
    if not current_staff.can_approve_loans:
        raise HTTPException(status_code=403, detail="You don't have permission to reject loans")
    
    try:
        application = loan_app_utils.reject_application(
            db, application_id, current_staff.employee_id, rejection_reason, review_notes
        )
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        return {"message": "Application rejected", "application_id": application_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# NOTIFY THAT A LOAN PAYMENT AS BEEN DISBURSED TO THE CLIENT
@adminrouter.put("/loan-agreement/{loan_agreement_id}/disburse")
def disburse_loan(
    loan_agreement_id: int,
    disbursement_date: Optional[datetime] = None,
    notes: Optional[str] = None,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark loan as disbursed and calculate payment due dates"""
    
    # Check permission
    if not current_staff.can_disburse_loans:
        raise HTTPException(status_code=403, detail="You don't have permission to disburse loans")
    
    # Call the function
    agreement, message = loan_app_utils.mark_disbursed(
        db, loan_agreement_id, current_staff.employee_id, disbursement_date, notes
    )
    
    if not agreement:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "loan_agreement_id": loan_agreement_id,
        "disbursement_date": agreement.disbursement_date,
        "first_payment_date": agreement.first_payment_date,
        "final_payment_date": agreement.final_payment_date
    }


# CREATE THE REPAY SCHEDULE FOR A CLIENT 
@adminrouter.get("/my-loans/{loan_agreement_id}/schedule")
def get_repayment_schedule(
    loan_agreement_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get repayment schedule for a specific loan"""
    
    # Verify loan belongs to user
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == loan_agreement_id,
        models.LoanAgreement.user_id == current_user.user_id
    ).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Get schedule items
    schedule = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id
    ).order_by(models.LoanRepaymentSchedule.installment_number).all()
    
    return {
        "loan_agreement_id": loan_agreement_id,
        "approved_amount": agreement.approved_amount,
        "interest_rate": agreement.interest_rate,
        "monthly_payment": agreement.monthly_payment,
        "total_repayment": agreement.total_repayment,
        "disbursement_date": agreement.disbursement_date,
        "first_payment_date": agreement.first_payment_date,
        "schedule": schedule
    }


# PAYMENT ENDPOINT TO RECORD A PAYMENT MADE BY  
class PaymentRecord(BaseModel):
    """Schema for recording a payment"""
    amount_paid: float
    payment_method: str  # cash, bank_transfer, mobile_money
    reference_number: Optional[str] = None
    notes: Optional[str] = None

@adminrouter.post("/loan-agreement/{loan_agreement_id}/record-payment")
def record_payment(
    loan_agreement_id: int,
    payment_data: PaymentRecord,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Record a payment made by client"""
    
    # Check permission
    if not current_staff.can_record_payments:
        raise HTTPException(status_code=403, detail="You don't have permission to record payments")
    
    # Validate payment amount
    if payment_data.amount_paid <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")
    
    # Validate payment method
    valid_methods = ["cash", "bank transfer", "mobile money"]
    if payment_data.payment_method not in valid_methods:
        raise HTTPException(status_code=400, detail=f"Payment method must be one of: {valid_methods}")
    
    # Record the payment
    payment, message = loan_app_utils.record_payment(
        db, 
        loan_agreement_id, 
        current_staff.employee_id,
        payment_data.amount_paid,
        payment_data.payment_method,
        payment_data.reference_number,
        payment_data.notes
    )
    
    if not payment:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "payment_id": payment.loanpaymentid,
        "amount_paid": payment.amount_paid,
        "principal_paid": payment.principal_paid,
        "interest_paid": payment.interest_paid,
        "installments_covered": payment.installments_covered
    }