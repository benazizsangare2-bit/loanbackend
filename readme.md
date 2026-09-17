# You start the virtual invironment with this command:

source venv/bin/activate

# You start the uvicorn server with this command:

uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Connect to the database

psql -U securityman -d loandb

# Open the psql super admin

sudo -u postgres psql

# To enter the docker database: 
docker exec -it postgres_db psql -U postgres -d loandb

# steps to get the backend infos

go to http://localhost:8000/openapi.json

install the generator from the frontend: <npm install --save-dev openapi-typescript>

add to package.json: <{
"scripts": {
"generate-api": "openapi-typescript lib/api/openapi.json -o lib/api/types.ts"
}
}>

run this from the frontend to generate the types: npm run generate-api


# Complete and clear workflow for the loan core functionalities

# Part 1: Loan Approval Flow - What Does "Approved" Mean?

# The Trigger

    Admin clicks "Approve" button in admin dashboard

    System changes status from under_review → approved

    System generates the loan agreement with final terms

# What Client Receives

# Modern approach (recommended):

# Email notification sent to client:

        Subject: "Your loan application has been approved"

        Content: Summary of approved terms (amount, interest rate, monthly payment)

        Link to login and view full agreement digitally

# In-system notification (when logged in):

        Dashboard shows "Your loan is approved"

        Click to view full loan agreement page

# Digital agreement page (in client portal):

        Shows all terms clearly

        Asks client to "Accept Agreement" button

        After acceptance, loan moves to disbursement_pending status

# The Physical Signing Question

# For a digital system (recommended):

    No physical signature

    Client clicks "I Accept" → timestamp recorded

    IP address and user agent logged for legal record

    This is legally binding in most jurisdictions (electronic signatures)

# For systems requiring physical signature:

    Admin downloads PDF of agreement

    Client signs physically

    Admin uploads signed PDF to system

    Admin marks "Agreement Signed"

# My recommendation: Start with digital acceptance. Add physical signature upload later if needed.

# Part 2: Disbursement - Marking Money Sent

    Admin receives proof of payment (bank transfer receipt, cash payment record, etc.)

    Admin goes to loan in admin dashboard

    Clicks "Mark as Disbursed"

    Uploads proof document (image/PDF) - optional but recommended

    Enters:

        Disbursement date

        Disbursement method (bank transfer, cash, cheque)

        Reference number (transaction ID)

        Notes (optional)

Where Proof is Stored

    Uploaded to server/storage

    Linked to disbursement record

    Admin can view/download later for audit

Minimum requirement: Reference number and date. Proof upload is good but not mandatory for MVP.
Part 3: Payment Schedule - How It's Displayed
In Client Portal (Read-only)

    Page or section: "My Loans" → Click specific loan → "Repayment Schedule"

    Display as table:

# Due Date Amount Due Status Actions

1 May 24, 2026 $444.24 Pending -
2 Jun 24, 2026 $444.24 Paid View Receipt
3 Jul 24, 2026 $444.24 Pending -

In Admin Portal (Management)

    Same table PLUS ability to:

        Record payment for any installment

        Mark as paid

        Add penalty

        View payment history

        View uploaded receipts

# Design Recommendation

    Single page showing current loan summary + payment schedule table

    Next payment highlighted prominently

    Late payments highlighted in red

# Part 4: Recording Cash Payments - Admin Flow

Admin Action:

    Opens loan in admin dashboard

    Clicks "Record Payment"

    Enters:

        Amount paid

        Payment date (today or past)

        Payment method (cash)

        Reference number (receipt number from physical receipt book)

        Upload photo of receipt (optional but recommended)

        Notes (e.g., "Paid at branch by client")

    Clicks "Save"

# System Action:

    Allocates payment to pending installments

    Updates loan balance

    If amount is full payment for current installment, marks it paid

    If overpayment, applies to next installment

    Generates receipt (PDF) for client

# To Ensure Integrity:

    Require admin to enter receipt number

    Receipt numbers should be unique per branch

    Photo upload strongly recommended for cash transactions

## Specific Order to Finish Backend:

    Loan agreement generation (creates payment schedule on approval)

    Payment recording endpoint (admin records payments)

    Loan summary endpoints (for client and admin dashboards)

    Admin stats endpoints (counts, totals, charts)

    File upload endpoints (receipts, agreements)

    Reminder system (email notifications)

# Testing Strategy for Backend:

# After each endpoint, test immediately with Swagger:

    Create loan application

    Approve it

    Verify payment schedule generated

    Record a payment

    Verify loan balance updated

    Check client loan summary

### two types of loans: simple interest and amortized loan

## Below is the amortization calculation

# Core Terms and Abbreviations

Term Abbreviation Meaning Example

Principal P The original loan amount borrowed 500,000 RWF

Annual Interest Rate APR Yearly interest percentage charged 10%

Monthly Interest Rate r Interest rate per month (APR ÷ 12) 0.8333%

Loan Term n Number of months to repay 12 months

Monthly Payment PMT Fixed amount paid each month 43,957.50 RWF

Total Repayment Total All monthly payments added together 527,490 RWF

Total Interest Interest Total Repayment - Principal 27,490 RWF

Remaining Balance Balance Principal still owed Changes each month

# The monthly payment calculation:

Monthly Payment = P × [r(1+r)^n] / [(1+r)^n - 1]

Where:
P = 500,000
r = 0.00833333
n = 12

(1+r)^n = (1.00833333)^12 = 1.104713

Monthly Payment = 500,000 × [0.00833333 × 1.104713] / [1.104713 - 1]
= 500,000 × [0.00920594] / [0.104713]
= 500,000 × 0.087915
= 43,957.50

# The total repayment (initial loan + the interests)

Total Repayment = Monthly Payment × 12
= 43,957.50 × 12
= 527,490.00

# The total interest calculation

Total Interest = Total Repayment - Principal
= 527,490 - 500,000
= 27,490.00

# Every monthly payment has TWO parts:

Monthly Payment = Principal Portion + Interest Portion

Portion What It Does Changes Over Time?
Interest Fee for borrowing money Decreases each month
Principal Pays down what you owe Increases each month


