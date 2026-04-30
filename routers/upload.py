from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database import models
from utils import upload as upload_utils
from utils import auth as auth_utils
from utils import loan_application as loan_app_utils
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas import upload as upload_schemas

uploadrouter = APIRouter(prefix="/uploads", tags=["uploads"])
security = HTTPBearer()

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

@uploadrouter.post("/loan-document", response_model=upload_schemas.DocumentUploadResponse)
async def upload_loan_document(
    file: UploadFile = File(...),
    application_id: int = Form(...),
    document_type: str = Form(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document for a loan application
    
    document_type can be:
    - national_id
    - proof_of_address
    - salary_slip
    - business_license
    - bank_statement
    - collateral_document
    """
    
    # Verify application belongs to user and is in draft status
    application = loan_app_utils.get_application_by_id(db, application_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if application.status != "draft":
        raise HTTPException(status_code=400, detail=f"Cannot upload documents for application with status: {application.status}")
    
    # Map document type to database column
    document_column_map = {
        "national_id": "national_id_document_path",
        "proof_of_address": "proof_of_address_path",
        "salary_slip": "salary_slip_path",
        "business_license": "business_license_path",
        "bank_statement": "bank_statement_path",
        "collateral_document": "collateral_document_path"
    }
    
    if document_type not in document_column_map:
        raise HTTPException(status_code=400, detail=f"Invalid document type. Allowed: {', '.join(document_column_map.keys())}")
    
    # Delete old file if it exists
    old_file_path = getattr(application, document_column_map[document_type])
    if old_file_path:
        upload_utils.delete_old_file(old_file_path)
    
    # Save new file
    try:
        saved_path = await upload_utils.save_upload_file(
            file, 
            current_user.user_id, 
            application_id, 
            document_type
        )
        
        # Update database with file path
        setattr(application, document_column_map[document_type], saved_path)
        db.commit()
        
        return {
            "document_type": document_type,
            "file_path": saved_path,
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")