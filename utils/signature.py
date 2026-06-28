import logging
import traceback

from sqlalchemy.orm import Session
from database import models
from schemas import signature as signature_schemas
from datetime import datetime, timedelta
import hashlib
import hmac
import os
from utils.email import send_email
from utils.email_templates import get_signature_confirmation_email, get_admin_signature_notification_email

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
logger = logging.getLogger(__name__)

def generate_signature_hash(agreement_id: int, user_id: int, signed_name: str):
    """Generate a unique hash for signature verification"""
    data = f"{agreement_id}:{user_id}:{signed_name}:{datetime.now().isoformat()}"
    return hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()

def create_signature(
    db: Session,
    agreement_id: int,
    user_id: int,
    signature_data: signature_schemas.SignatureRequest,
    ip_address: str = None,
    user_agent: str = None
):
    """Record a signature for a loan agreement"""
    
    # Check if agreement exists and belongs to user
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == agreement_id,
        models.LoanAgreement.user_id == user_id
    ).first()
    
    if not agreement:
        return None, "Loan agreement not found"
    
    # Check if already signed
    existing = db.query(models.LoanAgreementSignature).filter(
        models.LoanAgreementSignature.agreement_id == agreement_id,
        models.LoanAgreementSignature.is_valid == True
    ).first()
    
    if existing:
        return None, "This agreement has already been signed"
    
    # Check if agreement is in correct state
    if agreement.signing_status != "pending":
        return None, f"Cannot sign agreement with status: {agreement.signing_status}"
    
    # Create signature record
    signature_hash = generate_signature_hash(agreement_id, user_id, signature_data.signed_name)
    
    signature = models.LoanAgreementSignature(
        agreement_id=agreement_id,
        user_id=user_id,
        signed_name=signature_data.signed_name.strip(),
        agreed_to_terms=signature_data.agreed_to_terms,
        signature_hash=signature_hash,
        ip_address=ip_address,
        user_agent=user_agent,
        signature_type="typed",
        is_valid=True
    )
    
    db.add(signature)
    
    # Update agreement signing status
    agreement.signing_status = "signed"
    
    db.commit()
    db.refresh(signature)
    
    return signature, "Agreement signed successfully"

def get_agreement_signature_status(db: Session, agreement_id: int, user_id: int):
    """Get signature status for an agreement"""
    
    agreement = db.query(models.LoanAgreement).filter(
        models.LoanAgreement.agreement_id == agreement_id,
        models.LoanAgreement.user_id == user_id
    ).first()
    
    if not agreement:
        return None
    
    signature = db.query(models.LoanAgreementSignature).filter(
        models.LoanAgreementSignature.agreement_id == agreement_id,
        models.LoanAgreementSignature.is_valid == True
    ).first()
    
    application = db.query(models.LoanApplication).filter(
        models.LoanApplication.application_id == agreement.application_id
    ).first()
    
    return {
        "is_signed": signature is not None,
        "signed_at": signature.signed_at if signature else None,
        "signed_by": signature.signed_name if signature else None,
        "signing_status": agreement.signing_status,
        "amount": agreement.approved_amount,
        "amount_requested": application.amount_requested if application else None,
        "duration": agreement.duration_months,
        "duration_requested": application.duration_requested if application else None,
        "interest_rate": agreement.interest_rate,
        "monthly_payment": agreement.monthly_payment,
        "total_repayment": agreement.total_repayment,
        "disbursement_date": agreement.disbursement_date,
        "first_payment_date": agreement.first_payment_date,
    }

def send_signature_confirmation_emails(db: Session, agreement_id: int, user_id: int, signed_name: str):
    """Send confirmation emails to client and admin after signing"""
    
    # Get user and agreement
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    agreement = db.query(models.LoanAgreement).filter(models.LoanAgreement.agreement_id == agreement_id).first()
    
    if not user or not agreement:
        return False, "User or agreement not found"
    
    signed_at = datetime.now().strftime("%B %d, %Y at %H:%M")
    
    # Send to client
    try:
        subject_client, html_client = get_signature_confirmation_email(
            user.name, agreement_id, signed_name, signed_at
        )
        send_email(user.email, subject_client, html_client)
    except Exception:
        logger.exception(
            "Failed sending client signature email for agreement_id=%s user_id=%s",
            agreement_id,
            user_id,
        )
    
    # Send to admin(s) - you can get admin emails from Staff table
    try:
        admins = db.query(models.Staff).filter(models.Staff.is_active == True).all()
        for admin in admins:
            try:
                subject_admin, html_admin = get_admin_signature_notification_email(
                    user.name, agreement_id, signed_name
                )
                send_email(admin.email, subject_admin, html_admin)
            except Exception:
                logger.exception(
                    "Failed sending admin signature email for agreement_id=%s admin_email=%s",
                    agreement_id,
                    admin.email,
                )
    except Exception:
        logger.exception(
            "Failed querying staff for signature notification agreement_id=%s",
            agreement_id,
        )
    
    return True, "Emails sent successfully"