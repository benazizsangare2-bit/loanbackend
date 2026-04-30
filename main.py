# main.py
"""
Main application entry point.
This is like your main.go file.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.connection import engine, Base
from routers import loan_application, userauth, staffauth, loan_admin, upload
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Create database tables automatically on startup
# This is equivalent to your InitDatabase() in Go
# Base.metadata.create_all reads all classes that inherit from Base
# (like User, Loan) and creates their tables if they don't exist
print("Checking database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables ready")

# Create FastAPI application instance
app = FastAPI(
    
    title=os.getenv("APP_NAME", "Loan Management System"),
    description="Digital loan management system API",
    version="1.0.0",
    debug=os.getenv("DEBUG", "False").lower() == "true"
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js default port
        "http://127.0.0.1:3000",
        # Add your production frontend URL here when deployed
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include all routers (API endpoint groups)
# This is like calling your route functions in main.go
app.include_router(userauth.clientrouter)
app.include_router(staffauth.router)
app.include_router(loan_application.loanrouter)
app.include_router(loan_admin.adminrouter)
app.include_router(upload.uploadrouter)
# Root endpoint for basic health check
@app.get("/")
def read_root():
    """
    Root endpoint - returns basic API information.
    Use this to test if the server is running.
    """
    return {
        "message": "Loan Management System API",
        "status": "running",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """
    Health check endpoint - useful for monitoring.
    Returns simple status to confirm the service is alive.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)