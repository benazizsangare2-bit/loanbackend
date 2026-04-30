from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database import models
from schemas import loanapplication as loan_app_schemas
from utils import loan_application as loan_app_utils
from utils import auth as auth_utils
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime

loanrouter = APIRouter(prefix="/loans", tags=["loan applications"])
security = HTTPBearer()

# GET THE CURRENT USER FROM THE JWT TOKEN
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = auth_utils.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# CREATE A NEW DRAFT APPLICATION FOR CLIENTS
@loanrouter.post("/draft/create")
def create_draft(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new draft application"""
    draft, message = loan_app_utils.create_draft_application(db, current_user.user_id)
    return {
        "application_id": draft.application_id,
        "status": draft.status,
        "message": message
    }


# PATCH FOR UPDATING THE APPLICATION ANYTIME
@loanrouter.patch("/application/{application_id}")
def update_application(
    application_id: int,
    update_data: loan_app_schemas.LoanApplicationUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application fields partially (for multi-step form)"""
    # Convert Pydantic model to dict, excluding None values
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    application, message = loan_app_utils.update_application_partial(
        db, application_id, current_user.user_id, update_dict
    )
    
    if not application:
        raise HTTPException(status_code=404, detail=message)
    
    return {"message": message, "application_id": application.application_id}

# GET THE CLIENT'S DRAFT APPLICATION 
@loanrouter.get("/draft")
def get_draft(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's draft application"""
    draft = loan_app_utils.get_user_draft(db, current_user.user_id)
    
    if not draft:
        raise HTTPException(status_code=404, detail="No draft application found")
    
    return draft

# SUBMIT THE FINAL DRAFT APPLICATION
@loanrouter.post("/application/{application_id}/submit")
def submit_application(
    application_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit the draft application for admin review"""
    application, message = loan_app_utils.submit_application(
        db, application_id, current_user.user_id
    )
    
    if not application:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message, "application_id": application.application_id, "status": application.status}


# GET A SPECIFIC APPLICATIONS BY ID
@loanrouter.get("/application/{application_id}")
def get_application_by_id(
    application_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific application by ID (for viewing submitted applications)"""
    application = loan_app_utils.get_application_by_id(db, application_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Users can only view their own applications
    if application.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return application

# GET ALL LOAN APPLICATION FOR A SPECIFIC CLIENT
@loanrouter.get("/my-applications", response_model=list[loan_app_schemas.LoanApplicationResponse])
def get_my_applications(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all loan applications for the current user"""
    applications = loan_app_utils.get_user_applications(db, current_user.user_id, skip, limit)
    return applications


# GET A SPECIFIC LOAN APPLICATION 
@loanrouter.get("/application/{application_id}", response_model=loan_app_schemas.LoanApplicationResponse)
def get_application(
    application_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific loan application by ID"""
    application = loan_app_utils.get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Users can only see their own applications
    if application.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return application

# ENDPOINT THAT LETS THE CLIENTS VIEW THEIR PAYMENTS HISTORY
@loanrouter.get("/my-loans/{loan_agreement_id}/payments")
def get_payment_history(
    loan_agreement_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment history for a specific loan"""
    
    # Verify loan belongs to user
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == loan_agreement_id,
        models.LoanAgreement.user_id == current_user.user_id
    ).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Get payment records
    payments = db.query(models.LoanPayment).filter(
        models.LoanPayment.loan_agreement_id == loan_agreement_id
    ).order_by(models.LoanPayment.payment_date.desc()).all()
    
    # Get summary
    total_paid = sum(p.amount_paid for p in payments)
    total_principal = sum(p.principal_paid for p in payments)
    total_interest = sum(p.interest_paid for p in payments)
    
    return {
        "loan_agreement_id": loan_agreement_id,
        "approved_amount": agreement.approved_amount,
        "monthly_payment": agreement.monthly_payment,
        "total_repayment": agreement.total_repayment,
        "total_paid_to_date": round(total_paid, 2),
        "total_principal_paid": round(total_principal, 2),
        "total_interest_paid": round(total_interest, 2),
        "remaining_balance": round(agreement.total_repayment - total_paid, 2),
        "payments": payments
    }


# END POINT FOR CLIENT TO VIEW THEIR NEXT PAYMENT FROM THEIR DASHBOARDS
@loanrouter.get("/my-loans/{loan_agreement_id}/next-payment")
def get_next_payment(
    loan_agreement_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the next upcoming payment for a loan"""
    
    # Verify loan belongs to user
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == loan_agreement_id,
        models.LoanAgreement.user_id == current_user.user_id
    ).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Find next pending installment
    next_payment = db.query(models.LoanRepaymentSchedule).filter(
        models.LoanRepaymentSchedule.loan_agreement_id == loan_agreement_id,
        models.LoanRepaymentSchedule.status.in_(["pending", "partial"])
    ).order_by(models.LoanRepaymentSchedule.installment_number).first()
    
    if not next_payment:
        return {
            "message": "No pending payments. Loan may be completed.",
            "loan_completed": agreement.status == "completed"
        }
    
    # Check if payment is late
    today = datetime.now().date()
    is_late = False
    days_late = 0
    
    if next_payment.due_date and next_payment.due_date.date() < today:
        is_late = True
        days_late = (today - next_payment.due_date.date()).days
    
    return {
        "installment_number": next_payment.installment_number,
        "due_date": next_payment.due_date,
        "amount_due": next_payment.amount_due,
        "remaining_due": round(next_payment.amount_due - next_payment.paid_amount, 2),
        "is_late": is_late,
        "days_late": days_late if is_late else 0,
        "status": next_payment.status
    }