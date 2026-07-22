from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from database import models
from datetime import datetime, date, timedelta

def get_dashboard_summary(db: Session):
    """Get overall dashboard summary statistics"""
    total_applications = db.query(models.LoanApplication).count()

    status_counts = db.query(
        models.LoanAgreement.status,
        func.count(models.LoanAgreement.agreement_id)
    ).group_by(models.LoanAgreement.status).all()
    status_map = dict(status_counts)

    total_disbursed_result = db.query(
        func.coalesce(func.sum(models.LoanAgreement.approved_amount), 0)
    ).filter(
        models.LoanAgreement.status.in_(["disbursed", "active", "completed", "defaulted"])
    ).scalar()

    total_repaid_result = db.query(
        func.coalesce(func.sum(models.LoanPayment.amount_paid), 0)
    ).scalar()

    total_interest_paid = db.query(
        func.coalesce(func.sum(models.LoanPayment.interest_paid), 0)
    ).scalar()

    total_late_fees = db.query(
        func.coalesce(func.sum(models.LoanPayment.penalty_paid), 0)
    ).scalar()

    total_completed_amount = db.query(
        func.coalesce(func.sum(models.LoanAgreement.approved_amount), 0)
    ).filter(models.LoanAgreement.status == "completed").scalar()

    total_active_amount = db.query(
        func.coalesce(func.sum(models.LoanAgreement.approved_amount), 0)
    ).filter(models.LoanAgreement.status.in_(["disbursed", "active"])).scalar()

    total_defaulted_amount = db.query(
        func.coalesce(func.sum(models.LoanAgreement.approved_amount), 0)
    ).filter(models.LoanAgreement.status == "defaulted").scalar()

    total_rejected = db.query(models.LoanApplication).filter(
        models.LoanApplication.status == "rejected"
    ).count()

    total_outstanding = round(float(total_disbursed_result) - float(total_repaid_result), 2)

    return {
        "total_applications": total_applications,
        "total_rejected": total_rejected,
        "total_approved": status_map.get("approved", 0),
        "total_disbursed": status_map.get("disbursed", 0),
        "total_active": status_map.get("active", 0),
        "total_completed": status_map.get("completed", 0),
        "total_defaulted": status_map.get("defaulted", 0),
        "total_amount_disbursed": round(float(total_disbursed_result), 2),
        "total_amount_repaid": round(float(total_repaid_result), 2),
        "total_amount_outstanding": total_outstanding,
        "total_interest_earned": round(float(total_interest_paid), 2),
        "total_late_fees_collected": round(float(total_late_fees), 2),
        "total_active_amount": round(float(total_active_amount), 2),
        "total_completed_amount": round(float(total_completed_amount), 2),
        "total_defaulted_amount": round(float(total_defaulted_amount), 2),
    }


def get_status_distribution(db: Session):
    """Get loan agreement status distribution for pie chart"""
    results = db.query(
        models.LoanAgreement.status,
        func.count(models.LoanAgreement.agreement_id)
    ).group_by(models.LoanAgreement.status).all()

    colors = {
        "approved": "#007bff",
        "disbursed": "#17a2b8",
        "active": "#28a745",
        "completed": "#6f42c1",
        "defaulted": "#dc3545",
    }
    return [
        {"status": status, "count": count, "color": colors.get(status, "#6c757d")}
        for status, count in results
    ]


def get_monthly_applications(db: Session, months: int = 12):
    """Get monthly loan application counts"""
    cutoff = datetime.now() - timedelta(days=months * 30)
    results = db.query(
        extract("year", models.LoanApplication.created_at).label("year"),
        extract("month", models.LoanApplication.created_at).label("month"),
        func.count(models.LoanApplication.application_id)
    ).filter(
        models.LoanApplication.created_at >= cutoff
    ).group_by("year", "month").order_by("year", "month").all()

    return [
        {"year": int(year), "month": int(month), "count": count}
        for year, month, count in results
    ]


def get_monthly_disbursements(db: Session, months: int = 12):
    """Get monthly disbursed amounts"""
    cutoff = datetime.now() - timedelta(days=months * 30)
    results = db.query(
        extract("year", models.LoanAgreement.disbursement_date).label("year"),
        extract("month", models.LoanAgreement.disbursement_date).label("month"),
        func.coalesce(func.sum(models.LoanAgreement.approved_amount), 0)
    ).filter(
        models.LoanAgreement.disbursement_date.isnot(None),
        models.LoanAgreement.disbursement_date >= cutoff
    ).group_by("year", "month").order_by("year", "month").all()

    return [
        {"year": int(year), "month": int(month), "amount": round(float(amount), 2)}
        for year, month, amount in results
    ]


def get_monthly_repayments(db: Session, months: int = 12):
    """Get monthly repayment amounts"""
    cutoff = datetime.now() - timedelta(days=months * 30)
    results = db.query(
        extract("year", models.LoanPayment.payment_date).label("year"),
        extract("month", models.LoanPayment.payment_date).label("month"),
        func.coalesce(func.sum(models.LoanPayment.amount_paid), 0)
    ).filter(
        models.LoanPayment.payment_date >= cutoff
    ).group_by("year", "month").order_by("year", "month").all()

    return [
        {"year": int(year), "month": int(month), "amount": round(float(amount), 2)}
        for year, month, amount in results
    ]


def get_top_borrowers(db: Session, limit: int = 10):
    """Get top borrowers by total repayment amount"""
    results = db.query(
        models.LoanAgreement.user_id,
        func.count(models.LoanAgreement.agreement_id).label("loan_count"),
        func.coalesce(func.sum(models.LoanAgreement.approved_amount), 0).label("total_borrowed"),
        func.coalesce(func.sum(models.LoanPayment.amount_paid), 0).label("total_repaid"),
    ).outerjoin(
        models.LoanPayment,
        models.LoanPayment.loan_agreement_id == models.LoanAgreement.agreement_id
    ).group_by(
        models.LoanAgreement.user_id
    ).order_by(
        func.coalesce(func.sum(models.LoanPayment.amount_paid), 0).desc()
    ).limit(limit).all()

    borrowers = []
    for user_id, loan_count, total_borrowed, total_repaid in results:
        user = db.query(models.User).filter(models.User.user_id == user_id).first()
        borrowers.append({
            "user_id": user_id,
            "name": user.name if user else "Unknown",
            "email": user.email if user else None,
            "total_loans": loan_count,
            "total_borrowed": round(float(total_borrowed), 2),
            "total_repaid": round(float(total_repaid), 2),
            "outstanding": round(float(total_borrowed) - float(total_repaid), 2),
        })

    return borrowers


def get_portfolio_summary(db: Session):
    """Get portfolio performance metrics"""
    summary = get_dashboard_summary(db)

    total_disbursed = summary["total_amount_disbursed"]
    total_repaid = summary["total_amount_repaid"]
    total_outstanding = summary["total_amount_outstanding"]

    portfolio_at_risk = db.query(
        func.coalesce(func.sum(models.LoanRepaymentSchedule.total_due - models.LoanRepaymentSchedule.paid_amount), 0)
    ).filter(
        models.LoanRepaymentSchedule.status.in_(["late", "defaulted"])
    ).scalar()

    active_loans_at_risk = db.query(
        func.count(models.LoanAgreement.agreement_id)
    ).filter(
        models.LoanAgreement.status.in_(["active", "disbursed"])
    ).count()

    recovery_rate = round(float(total_repaid) / float(total_disbursed), 4) if total_disbursed > 0 else 0

    return {
        "total_disbursed": summary["total_amount_disbursed"],
        "total_repaid": summary["total_amount_repaid"],
        "total_outstanding": total_outstanding,
        "total_interest_earned": summary["total_interest_earned"],
        "total_late_fees_collected": summary["total_late_fees_collected"],
        "portfolio_at_risk": round(float(portfolio_at_risk), 2),
        "active_loans_count": active_loans_at_risk,
        "recovery_rate": recovery_rate,
        "recovery_rate_percentage": round(recovery_rate * 100, 2),
    }


def get_loan_payments_report(db: Session, status: str = None,
                              start_date: date = None, end_date: date = None,
                              skip: int = 0, limit: int = 100):
    """Get loan payments report with optional filters"""
    query = db.query(models.LoanPayment).join(
        models.LoanAgreement,
        models.LoanPayment.loan_agreement_id == models.LoanAgreement.agreement_id
    ).join(
        models.User,
        models.LoanPayment.user_id == models.User.user_id
    )

    if status:
        query = query.filter(models.LoanAgreement.status == status)
    if start_date:
        query = query.filter(models.LoanPayment.payment_date >= start_date)
    if end_date:
        query = query.filter(models.LoanPayment.payment_date <= end_date)

    total = query.count()
    payments = query.order_by(models.LoanPayment.payment_date.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "payments": [
            {
                "payment_id": p.loanpaymentid,
                "loan_agreement_id": p.loan_agreement_id,
                "client_name": p.user.name if p.user else "Unknown",
                "amount_paid": p.amount_paid,
                "principal_paid": p.principal_paid,
                "interest_paid": p.interest_paid,
                "penalty_paid": p.penalty_paid,
                "payment_method": p.payment_method,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "reference_number": p.reference_number,
                "installments_covered": p.installments_covered,
                "recorded_by": p.recorded_by,
                "notes": p.notes,
            }
            for p in payments
        ]
    }


def get_loans_report(db: Session, status: str = None,
                      start_date: date = None, end_date: date = None,
                      skip: int = 0, limit: int = 100):
    """Get loans report with optional filters"""
    query = db.query(models.LoanAgreement).join(
        models.User,
        models.LoanAgreement.user_id == models.User.user_id
    )

    if status:
        query = query.filter(models.LoanAgreement.status == status)
    if start_date:
        query = query.filter(models.LoanAgreement.disbursement_date >= start_date)
    if end_date:
        query = query.filter(models.LoanAgreement.disbursement_date <= end_date)

    total = query.count()
    agreements = query.order_by(models.LoanAgreement.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for agreement in agreements:
        total_paid = db.query(
            func.coalesce(func.sum(models.LoanPayment.amount_paid), 0)
        ).filter(
            models.LoanPayment.loan_agreement_id == agreement.agreement_id
        ).scalar()

        result.append({
            "agreement_id": agreement.agreement_id,
            "client_name": agreement.user.name if agreement.user else "Unknown",
            "client_email": agreement.user.email if agreement.user else None,
            "approved_amount": agreement.approved_amount,
            "interest_rate": agreement.interest_rate,
            "duration_months": agreement.duration_months,
            "monthly_payment": agreement.monthly_payment,
            "total_repayment": agreement.total_repayment,
            "status": agreement.status,
            "disbursement_date": agreement.disbursement_date.isoformat() if agreement.disbursement_date else None,
            "completed_date": agreement.completed_date.isoformat() if agreement.completed_date else None,
            "total_paid": round(float(total_paid), 2),
            "outstanding": round(float(agreement.total_repayment) - float(total_paid), 2),
        })

    return {"total": total, "loans": result}


def get_rejection_analysis(db: Session):
    """Get rejection statistics and breakdown by reason"""
    total_rejected = db.query(models.LoanApplication).filter(
        models.LoanApplication.status == "rejected"
    ).count()

    recent_rejections = db.query(models.LoanApplication).filter(
        models.LoanApplication.status == "rejected"
    ).order_by(models.LoanApplication.reviewed_at.desc()).limit(5).all()

    reasons_query = db.query(
        models.LoanApplication.rejection_reason,
        func.count(models.LoanApplication.application_id)
    ).filter(
        models.LoanApplication.status == "rejected",
        models.LoanApplication.rejection_reason.isnot(None)
    ).group_by(models.LoanApplication.rejection_reason).order_by(
        func.count(models.LoanApplication.application_id).desc()
    ).all()

    total_rejected_amount = db.query(
        func.coalesce(func.sum(models.LoanApplication.amount_requested), 0)
    ).filter(models.LoanApplication.status == "rejected").scalar()

    return {
        "total_rejected": total_rejected,
        "total_rejected_amount": round(float(total_rejected_amount), 2),
        "reasons_distribution": [
            {"reason": reason, "count": count}
            for reason, count in reasons_query
        ],
        "recent_rejections": [
            {
                "application_id": app.application_id,
                "user_id": app.user_id,
                "full_name": app.full_name,
                "amount_requested": app.amount_requested,
                "rejection_reason": app.rejection_reason,
                "review_notes": app.review_notes,
                "reviewed_by": app.reviewed_by,
                "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
            }
            for app in recent_rejections
        ],
    }


def get_audit_logs_report(db: Session, action: str = None,
                           start_date: date = None, end_date: date = None,
                           skip: int = 0, limit: int = 100):
    """Get audit logs report with optional filters"""
    query = db.query(models.AuditLog)

    if action:
        query = query.filter(models.AuditLog.action == action)
    if start_date:
        query = query.filter(models.AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(models.AuditLog.created_at <= end_date)

    total = query.count()
    logs = query.order_by(models.AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "logs": [
            {
                "log_id": log.log_id,
                "action": log.action,
                "performed_by": log.performed_by,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }
