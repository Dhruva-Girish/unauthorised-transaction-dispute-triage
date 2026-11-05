# Bank Card Dispute Handling Policies & Investigation Standards

## 1. Unauthorized Transaction Claims (Fraud & Card Compromise)
- **Definition**: A transaction initiated without the cardholder's knowledge, authority, or consent.
- **Investigation Rule**: The presence of normal customer transaction data or low automated risk scores MUST NOT be used as sole grounds to deny a dispute. Cardholder assertion of non-authorization mandates human investigator review.
- **Immediate Safeguard**: If fraud probability is high (>= 0.50), the investigator must immediately evaluate placing a temporary block on the card token and review previous 48-hour activity.
- **Evidence Required**: Cardholder declaration of non-receipt/non-authorization, device geolocation analysis, IP mismatch verification, and customer history examination.

## 2. Duplicate Billing Disputes
- **Definition**: Multiple identical charges billed for a single purchase or service engagement.
- **Investigation Criteria**: Check whether another transaction exists with the same cardholder ID, identical merchant descriptor, matching currency, and exact amount within a 10-minute window.
- **Resolution Standard**: If verified identical charges occurred within 10 minutes, escalate for merchant duplicate credit request. If charges were separated by hours or days, request itemized receipts from the merchant.

## 3. Goods or Services Not Received
- **Definition**: The cardholder was billed for goods or services that were paid for but never delivered or provided.
- **Mandatory Procedure**: Request tracking confirmation, proof of delivery signature, or merchant fulfillment confirmation. Allow merchant a 10-day rebuttal window before filing formal chargeback.
- **Priority**: Medium priority; route to Merchant Disputed Transactions queue.

## 4. Subscription & Recurring Billing Disputes
- **Definition**: Recurring charges assessed after timely cancellation notification by the cardholder.
- **Evidence Required**: Customer cancellation confirmation email, date of cancellation request, and merchant terms of service regarding cancellation notice periods.
