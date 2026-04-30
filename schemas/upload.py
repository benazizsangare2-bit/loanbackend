from pydantic import BaseModel
from typing import Optional

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    document_type: str
    file_path: str
    message: str

class DocumentType(str):
    """Document types for loan applications"""
    NATIONAL_ID = "national_id"
    PROOF_OF_ADDRESS = "proof_of_address"
    SALARY_SLIP = "salary_slip"
    BUSINESS_LICENSE = "business_license"
    BANK_STATEMENT = "bank_statement"
    COLLATERAL_DOCUMENT = "collateral_document"