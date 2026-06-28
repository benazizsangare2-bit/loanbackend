import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.connection import get_db

logger = logging.getLogger(__name__)
from database import models
from schemas import signature as signature_schemas
from utils import signature as signature_utils
from utils import auth as auth_utils
from utils import loan_application as loan_app_utils
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

signaturerouter = APIRouter(prefix="/signature", tags=["loan signatures"])
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = auth_utils.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@signaturerouter.get("/agreement/{agreement_id}/status")
def get_signature_status(
    agreement_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if an agreement has been signed"""
    
    # Verify agreement belongs to user
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == agreement_id,
        models.LoanAgreement.user_id == current_user.user_id
    ).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    status_data = signature_utils.get_agreement_signature_status(db, agreement_id, current_user.user_id)
    
    if not status_data:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    return {"success": True, "data": status_data}

@signaturerouter.post("/agreement/{agreement_id}/sign")
def sign_agreement(
    agreement_id: int,
    signature_data: signature_schemas.SignatureRequest,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sign a loan agreement"""
    
    # Get client IP
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Create signature
    signature, message = signature_utils.create_signature(
        db, agreement_id, current_user.user_id, signature_data, client_ip, user_agent
    )
    
    if not signature:
        raise HTTPException(status_code=400, detail=message)
    
    # Send confirmation emails (non-critical — run after response)
    try:
        signature_utils.send_signature_confirmation_emails(
            db, agreement_id, current_user.user_id, signature_data.signed_name
        )
    except Exception:
        logger.exception("Failed to send signature confirmation emails for agreement_id=%s", agreement_id)
    
    return {
        "success": True,
        "message": message,
        "agreement_id": agreement_id,
        "signed_at": signature.signed_at.isoformat() if signature.signed_at else None,
        "signature_id": signature.signature_id
    }

@signaturerouter.get("/agreement/{agreement_id}/document")
def get_signed_agreement_document(
    agreement_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the signed agreement document data"""
    
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == agreement_id,
        models.LoanAgreement.user_id == current_user.user_id
    ).first()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    signature = db.query(models.LoanAgreementSignature).filter(
        models.LoanAgreementSignature.agreement_id == agreement_id,
        models.LoanAgreementSignature.is_valid == True
    ).first()
    
    # Get application data for terms display
    application = db.query(models.LoanApplication).filter(
        models.LoanApplication.application_id == agreement.application_id
    ).first()
    
    return {
        "agreement_id": agreement.agreement_id,
        "client_name": current_user.name,
        "client_email": current_user.email,
        "client_phone": application.phone_number if application else None,
        "approved_amount": agreement.approved_amount,
        "interest_rate": agreement.interest_rate,
        "duration_months": agreement.duration_months,
        "monthly_payment": agreement.monthly_payment,
        "total_repayment": agreement.total_repayment,
        "approval_date": agreement.approval_date,
        "disbursement_date": agreement.disbursement_date,
        "first_payment_date": agreement.first_payment_date,
        "signature": {
            "signed_name": signature.signed_name if signature else None,
            "signed_at": signature.signed_at if signature else None,
            "ip_address": signature.ip_address if signature else None
        } if signature else None,
        "is_signed": signature is not None
    }