
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
class ApproveRequest(BaseModel):
    approved_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    duration_months: Optional[int] = None
    approval_notes: Optional[str] = None

@adminrouter.put("/{application_id}/approve")
def approve_application(
    application_id: int,
    params: ApproveRequest,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve a loan application with custom terms"""
    
    if not current_staff.can_approve_loans:
        raise HTTPException(status_code=403, detail="You don't have permission to approve loans")
    
    application, message = loan_app_utils.approve_application(
        db, application_id, current_staff.employee_id,
        params.approved_amount, params.interest_rate, params.duration_months, params.approval_notes
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


def _serialize_schedule_item(item):
    return {
        "installment_number": item.installment_number,
        "due_date": item.due_date.isoformat() if item.due_date else None,
        "amount_due": item.amount_due,
        "principal_due": item.principal_due,
        "interest_due": item.interest_due,
        "remaining_principal": item.remaining_principal,
        "late_fee": item.late_fee or 0.0,
        "total_due": item.total_due,
        "status": item.status,
        "paid_amount": item.paid_amount or 0.0,
        "paid_date": item.paid_date.isoformat() if item.paid_date else None,
        "days_late": item.days_late or 0,
    }


# CREATE THE REPAY SCHEDULE FOR A CLIENT 
@adminrouter.get("/my-loans/{loan_agreement_id}/schedule")
def get_repayment_schedule(
    loan_agreement_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get repayment schedule for a specific loan (client access)"""
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == loan_agreement_id,
        models.LoanAgreement.user_id == current_user.user_id
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Loan not found")
    schedule = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id
    ).order_by(models.LoanRepaymentSchedule.installment_number).all()
    return {
        "loan_agreement_id": loan_agreement_id,
        "approved_amount": agreement.approved_amount,
        "interest_rate": agreement.interest_rate,
        "monthly_payment": agreement.monthly_payment,
        "total_repayment": agreement.total_repayment,
        "disbursement_date": agreement.disbursement_date.isoformat() if agreement.disbursement_date else None,
        "first_payment_date": agreement.first_payment_date.isoformat() if agreement.first_payment_date else None,
        "schedule": [_serialize_schedule_item(s) for s in schedule]
    }


@adminrouter.get("/admin/my-loans/{loan_agreement_id}/schedule")
def get_admin_repayment_schedule(
    loan_agreement_id: int,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get repayment schedule for a specific loan (admin access)"""
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == loan_agreement_id
    ).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Loan not found")
    schedule = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id
    ).order_by(models.LoanRepaymentSchedule.installment_number).all()
    return {
        "loan_agreement_id": loan_agreement_id,
        "approved_amount": agreement.approved_amount,
        "interest_rate": agreement.interest_rate,
        "monthly_payment": agreement.monthly_payment,
        "total_repayment": agreement.total_repayment,
        "disbursement_date": agreement.disbursement_date.isoformat() if agreement.disbursement_date else None,
        "first_payment_date": agreement.first_payment_date.isoformat() if agreement.first_payment_date else None,
        "schedule": [_serialize_schedule_item(s) for s in schedule]
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

    # FUNCTION TO MANUALLY CALCULATE LATE FEE RECALCULATION FOR ALL LOANS 
@adminrouter.post("/admin/recalculate-late-fees")
def recalculate_all_late_fees(
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Manually trigger late fee recalculation for all loans"""
    
    if not current_staff.can_approve_loans:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    updated_count = loan_app_utils.update_daily_late_fees(db)
    
    return {"message": f"Late fees recalculated successfully", "updated_installments": updated_count}


# GET THE LIST OF ALL LOAN AGREEMENTS (Admin only)
@adminrouter.get("/admin/agreements", response_model=list)
def get_all_agreements(
    skip: int = 0,
    limit: int = 100,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all loan agreements in the system (admin only)"""
    agreements = db.query(models.LoanAgreement).order_by(models.LoanAgreement.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for agreement in agreements:
        signature = db.query(models.LoanAgreementSignature).filter(
            models.LoanAgreementSignature.agreement_id == agreement.agreement_id,
            models.LoanAgreementSignature.is_valid == True
        ).first()
        
        application = db.query(models.LoanApplication).filter(
            models.LoanApplication.application_id == agreement.application_id
        ).first()
        
        result.append({
            "agreement_id": agreement.agreement_id,
            "application_id": agreement.application_id,
            "user_id": agreement.user_id,
            "client_name": agreement.user.name if agreement.user else (application.full_name if application else None),
            "client_email": agreement.user.email if agreement.user else (application.email_address if application else None),
            "approved_amount": agreement.approved_amount,
            "interest_rate": agreement.interest_rate,
            "duration_months": agreement.duration_months,
            "monthly_payment": agreement.monthly_payment,
            "total_repayment": agreement.total_repayment,
            "status": agreement.status,
            "signing_status": agreement.signing_status,
            "approval_date": agreement.approval_date,
            "disbursement_date": agreement.disbursement_date,
            "created_at": agreement.created_at,
            "signature": {
                "signed_name": signature.signed_name if signature else None,
                "signed_at": signature.signed_at if signature else None,
                "ip_address": signature.ip_address if signature else None
            } if signature else None,
            "is_signed": signature is not None
        })
    return result


# GET DETAILS OF A SPECIFIC AGREEMENT (Admin only)
@adminrouter.get("/admin/agreements/{agreement_id}")
def get_admin_agreement_detail(
    agreement_id: int,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed single agreement terms, signatures, and schedule"""
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == agreement_id
    ).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
        
    signature = db.query(models.LoanAgreementSignature).filter(
        models.LoanAgreementSignature.agreement_id == agreement_id,
        models.LoanAgreementSignature.is_valid == True
    ).first()
    
    application = db.query(models.LoanApplication).filter(
        models.LoanApplication.application_id == agreement.application_id
    ).first()
    
    schedule = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == agreement_id
    ).order_by(models.LoanRepaymentSchedule.installment_number).all()
    
    return {
        "agreement_id": agreement.agreement_id,
        "application_id": agreement.application_id,
        "user_id": agreement.user_id,
        "client_name": agreement.user.name if agreement.user else (application.full_name if application else None),
        "client_email": agreement.user.email if agreement.user else (application.email_address if application else None),
        "client_phone": application.phone_number if application else None,
        "approved_amount": agreement.approved_amount,
        "interest_rate": agreement.interest_rate,
        "duration_months": agreement.duration_months,
        "monthly_payment": agreement.monthly_payment,
        "total_repayment": agreement.total_repayment,
        "total_interest": agreement.total_interest,
        "approval_date": agreement.approval_date,
        "disbursement_date": agreement.disbursement_date,
        "first_payment_date": agreement.first_payment_date,
        "final_payment_date": agreement.final_payment_date,
        "completed_date": agreement.completed_date,
        "status": agreement.status,
        "signing_status": agreement.signing_status,
        "approved_by": agreement.approved_by,
        "disbursed_by": agreement.disbursed_by,
        "approval_notes": agreement.approval_notes,
        "created_at": agreement.created_at,
        "updated_at": agreement.updated_at,
        "signature": {
            "signed_name": signature.signed_name if signature else None,
            "signed_at": signature.signed_at if signature else None,
            "ip_address": signature.ip_address if signature else None,
            "user_agent": signature.user_agent if signature else None,
            "signature_type": signature.signature_type if signature else None
        } if signature else None,
        "is_signed": signature is not None,
        "schedule": [
            {
                "installment_number": item.installment_number,
                "due_date": item.due_date,
                "amount_due": item.amount_due,
                "principal_due": item.principal_due,
                "interest_due": item.interest_due,
                "remaining_principal": item.remaining_principal,
                "late_fee": item.late_fee,
                "total_due": item.total_due,
                "status": item.status,
                "paid_amount": item.paid_amount,
                "paid_date": item.paid_date
            }
            for item in schedule
        ]
    }


# PATCH endpoint for updating an application by admin
@adminrouter.patch("/admin/application/{application_id}")
def update_application_admin(
    application_id: int,
    update_data: loan_app_schemas.LoanApplicationUpdate,
    current_staff = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update application fields partially as an administrator"""
    application = loan_app_utils.get_application_by_id_admin(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    for key, value in update_dict.items():
        if hasattr(application, key):
            setattr(application, key, value)
            
    db.commit()
    db.refresh(application)
    return {"message": "Application updated successfully by admin", "application_id": application.application_id}