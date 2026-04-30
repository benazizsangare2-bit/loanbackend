# You start the virtual invironment with this command: 
source venv/bin/activate

# You start the uvicorn server with this command: 
uvicorn main:app --reload --host 0.0.0.0 --port 8000


# Connect to the database
psql -U securityman -d loandb


# Complete and clear workflow for the loan core functionalities

# Part 1: Loan Approval Flow - What Does "Approved" Mean?
# The Trigger

    Admin clicks "Approve" button in admin dashboard

    System changes status from under_review → approved

    System generates the loan agreement with final terms

# What Client Receives

# Modern approach (recommended):

#  Email notification sent to client:

        Subject: "Your loan application has been approved"

        Content: Summary of approved terms (amount, interest rate, monthly payment)

        Link to login and view full agreement digitally

#  In-system notification (when logged in):

        Dashboard shows "Your loan is approved"

        Click to view full loan agreement page

#  Digital agreement page (in client portal):

        Shows all terms clearly

        Asks client to "Accept Agreement" button

        After acceptance, loan moves to disbursement_pending status

#  The Physical Signing Question

#  For a digital system (recommended):

    No physical signature

    Client clicks "I Accept" → timestamp recorded

    IP address and user agent logged for legal record

    This is legally binding in most jurisdictions (electronic signatures)

#  For systems requiring physical signature:

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

#	Due Date	Amount Due	Status	Actions
1	May 24, 2026	$444.24	Pending	-
2	Jun 24, 2026	$444.24	Paid	View Receipt
3	Jul 24, 2026	$444.24	Pending	-

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