def get_loan_approved_email(user_name, loan_amount, monthly_payment, interest_rate, duration, agreement_id):
    """Email when loan is approved"""
    subject = f"Your Loan Has Been Approved - {loan_amount} RWF"
    
    html = f"""
    <html>
    <body>
        <h2>Congratulations {user_name}!</h2>
        <p>Your loan application has been <strong>approved</strong>.</p>
        
        <h3>Loan Terms:</h3>
        <ul>
            <li>Amount: {loan_amount:,.0f} RWF</li>
            <li>Interest Rate: {interest_rate}%</li>
            <li>Duration: {duration} months</li>
            <li>Monthly Payment: {monthly_payment:,.0f} RWF</li>
        </ul>
        
        <p>You will receive a separate notification when the funds are disbursed.</p>
        <p>Follow this link to sign the loan agreement before your loan can be disbursed:</p>
        
        <p><a href="http://localhost:3000/dashboard/user/agree/{agreement_id}">View your loan agreement form</a></p>
    </body>
    </html>
    """
    return subject, html

def get_loan_disbursed_email(user_name, first_payment_date, monthly_payment):
    """Email when loan is disbursed"""
    subject = "Your Loan Has Been Disbursed"
    
    html = f"""
    <html>
    <body>
        <h2>Dear {user_name},</h2>
        <p>Your loan funds have been <strong>disbursed</strong> to your account.</p>
        
        <h3>Payment Information:</h3>
        <ul>
            <li>First Payment Due: {first_payment_date.strftime('%B %d, %Y')}</li>
            <li>Monthly Payment: {monthly_payment:,.0f} RWF</li>
        </ul>
        
        <p>Please ensure timely payment to avoid late fees.</p>
        
        <p><a href="http://localhost:3000/repayment-schedule">View your repayment schedule</a></p>
    </body>
    </html>
    """
    return subject, html

def get_payment_receipt_email(user_name, amount_paid, installment_numbers, remaining_balance,
                               payment_method=None, principal_paid=None, interest_paid=None,
                               penalty_paid=None, next_due_date=None, agreement_id=None):
    """Email when payment is recorded"""
    subject = f"Payment Receipt - {amount_paid:,.0f} RWF"
    
    penalty_html = f"<li>Late Fee Paid: {penalty_paid:,.0f} RWF</li>" if penalty_paid and penalty_paid > 0 else ""
    next_due_html = f"<li>Next Payment Due: {next_due_date}</li>" if next_due_date else ""
    dashboard_link = f'<p><a href="http://localhost:3000/dashboard/user/repayments/{agreement_id}">View your repayment schedule</a></p>' if agreement_id else ""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #28a745; color: white; padding: 15px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .amount {{ font-size: 28px; font-weight: bold; color: #28a745; text-align: center; padding: 15px; }}
            .details {{ margin: 15px 0; padding: 15px; background-color: white; border: 1px solid #ddd; border-radius: 5px; }}
            .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Payment Received</h2>
            </div>
            <div class="content">
                <p>Dear {user_name},</p>
                <p>We have recorded your payment of:</p>
                <div class="amount">{amount_paid:,.0f} RWF</div>

                <div class="details">
                    <h3>Payment Details:</h3>
                    <ul>
                        <li>Installments Covered: {installment_numbers}</li>
                        <li>Principal Paid: {principal_paid:,.0f} RWF</li>
                        <li>Interest Paid: {interest_paid:,.0f} RWF</li>
                        {penalty_html}
                        <li>Remaining Balance: {remaining_balance:,.0f} RWF</li>
                        {next_due_html}
                    </ul>
                    <p><strong>Method:</strong> {payment_method or "N/A"}</p>
                </div>

                {dashboard_link}

                <p>Thank you for your payment.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Loan Management System. All rights reserved.</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return subject, html


## Email template for sending the loan agreement form to the client once they sign it
def get_signature_confirmation_email(user_name: str, agreement_id: int, signed_name: str, signed_at: str):
    """Email when loan agreement is signed"""
    subject = f"Loan Agreement Signed - Confirmation"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #28a745; color: white; padding: 10px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .signature-block {{ border: 1px solid #ddd; padding: 15px; margin: 15px 0; background-color: white; }}
            .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Loan Agreement Signed Successfully</h2>
            </div>
            <div class="content">
                <p>Dear {user_name},</p>
                <p>Your loan agreement has been successfully signed on <strong>{signed_at}</strong>.</p>
                <div class="signature-block">
                    <p><strong>Signed by:</strong> {signed_name}</p>
                    <p><strong>Agreement ID:</strong> {agreement_id}</p>
                    <p><strong>Signature Type:</strong> Electronic (Typed Name)</p>
                </div>
                <p>Your loan will be disbursed within 1-2 business days.</p>
                <p><a href="http://localhost:3000/admin/loans/{agreement_id}">View your signed agreement</a></p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Loan Management System. All rights reserved.</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </html>
    """
    
    return subject, html


def get_admin_signature_notification_email(user_name: str, agreement_id: int, signed_name: str):
    """Email to admin when client signs agreement"""
    subject = f"Loan Agreement Signed - Agreement #{agreement_id}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #007bff; color: white; padding: 10px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Loan Agreement Signed</h2>
            </div>
            <div class="content">
                <p>A loan agreement has been signed:</p>
                <ul>
                    <li><strong>Client:</strong> {user_name}</li>
                    <li><strong>Agreement ID:</strong> {agreement_id}</li>
                    <li><strong>Signed by:</strong> {signed_name}</li>
                </ul>
                <p><a href="https://localhost:3000/admin/loans/{agreement_id}">View agreement in admin panel</a></p>
            </div>
        </div>
    </html>
    """
    
    return subject, html