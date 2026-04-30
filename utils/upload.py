import os
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, HTTPException
import uuid

# Get the base directory of your project
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "loan_applications"

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def ensure_upload_directories(user_id: int, application_id: int):
    """Create user and application folders if they don't exist"""
    user_dir = UPLOAD_DIR / str(user_id)
    app_dir = user_dir / str(application_id)
    
    app_dir.mkdir(parents=True, exist_ok=True)
    
    return app_dir

def validate_file(file: UploadFile):
    """Validate file type and size"""
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # File size will be checked when reading
    return True

def generate_unique_filename(original_filename: str):
    """Generate unique filename to avoid conflicts"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    extension = os.path.splitext(original_filename)[1].lower()
    
    return f"{timestamp}_{unique_id}{extension}"

async def save_upload_file(file: UploadFile, user_id: int, application_id: int, document_type: str):
    """Save uploaded file and return the stored path"""
    
    # Validate file
    validate_file(file)
    
    # Create directories
    app_dir = ensure_upload_directories(user_id, application_id)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Create final file path
    file_path = app_dir / unique_filename
    
    # Save file
    try:
        contents = await file.read()
        
        # Check file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Max 5MB")
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return relative path to store in database
        relative_path = f"uploads/loan_applications/{user_id}/{application_id}/{unique_filename}"
        
        return relative_path
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

def delete_old_file(file_path: str):
    """Delete old file when replacing with new one"""
    if file_path:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            full_path.unlink()