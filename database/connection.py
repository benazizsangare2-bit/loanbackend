# database/connection.py
"""
This file handles the database connection for the application.

"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This reads your DATABASE_URL from .env
load_dotenv()

# Get database URL from environment variable
#DATABASE_URL = os.getenv("DATABASE_URL")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create the database engine
# This is the actual connection to PostgreSQL
engine = create_engine(DATABASE_URL)

# Create a session factory
# SessionLocal() creates a new session for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for all models (tables)
# Your table classes will inherit from this
Base = declarative_base()

def get_db():
    """
    Dependency function to get a database session.
    This will be used in your API routes.
    
    In Go terms, this is like injecting a database connection
    into your handlers. FastAPI will call this automatically.
    
    Usage in routes:
        def my_route(db: Session = Depends(get_db)):
            # use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Always close the session when done
        db.close()