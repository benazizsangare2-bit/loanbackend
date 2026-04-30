from mailjet_rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Mailjet client
mailjet = Client(
    auth=(os.getenv("MAILJET_API_KEY"), os.getenv("MAILJET_API_SECRET")),
    version='v3.1'
)

FROM_EMAIL = os.getenv("MAILJET_FROM_EMAIL")
FROM_NAME = os.getenv("MAILJET_FROM_NAME")

def send_email(to_email: str, subject: str, html_content: str, text_content: str = None):
    """Send email using Mailjet"""
    data = {
        'Messages': [
            {
                "From": {
                    "Email": FROM_EMAIL,
                    "Name": FROM_NAME
                },
                "To": [
                    {
                        "Email": to_email,
                        "Name": to_email.split('@')[0]
                    }
                ],
                "Subject": subject,
                "TextPart": text_content or html_content.replace('<', '').replace('>', ''),
                "HTMLPart": html_content
            }
        ]
    }
    
    result = mailjet.send.create(data=data)
    
    if result.status_code == 200:
        return True, "Email sent successfully"
    else:
        return False, f"Failed to send email: {result.json()}"

def send_otp_email(to_email: str, otp_code: str, user_name: str):
    """Send OTP verification email"""
    subject = "Verify Your Email - Loan Management System"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .otp-code {{ font-size: 32px; font-weight: bold; text-align: center; padding: 20px; letter-spacing: 5px; }}
            .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Email Verification</h2>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Thank you for registering with our Loan Management System. Please use the following OTP code to verify your email address:</p>
                <div class="otp-code">{otp_code}</div>
                <p>This OTP code will expire in {os.getenv('OTP_EXPIRY_MINUTES', 10)} minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Loan Management System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Email Verification
    
    Hello {user_name},
    
    Thank you for registering with our Loan Management System. Please use the following OTP code to verify your email address:
    
    {otp_code}
    
    This OTP code will expire in {os.getenv('OTP_EXPIRY_MINUTES', 10)} minutes.
    
    If you didn't request this, please ignore this email.
    """
    
    return send_email(to_email, subject, html_content, text_content)

def send_password_reset_email(to_email: str, reset_token: str, user_name: str):
    """Send password reset email"""
    subject = "Password Reset Request - Loan Management System"
    
    # This would be your frontend URL
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #ff9800; color: white; padding: 10px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #ff9800;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Password Reset Request</h2>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p>{reset_link}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email and your password will remain unchanged.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Loan Management System. All rights reserved.</p>
            </div>
        </div>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    Hello {user_name},
    
    We received a request to reset your password. Use the following link:
    
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you didn't request this, please ignore this email.
    """
    
    return send_email(to_email, subject, html_content, text_content)