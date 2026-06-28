# scheduler.py for daily job
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from utils.loan_application import update_daily_late_fees
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_late_fee_update():
    """Run late fee update for all overdue loans"""
    db = SessionLocal()
    try:
        updated = update_daily_late_fees(db)
        logger.info(f"Updated {updated} overdue installments")
    except Exception as e:
        logger.error(f"Error updating late fees: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_late_fee_update()