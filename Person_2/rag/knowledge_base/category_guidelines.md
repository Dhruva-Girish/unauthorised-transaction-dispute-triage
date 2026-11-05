# Dispute Complaint Classification Guidelines & Taxonomy

## Classification Schema
Disputes must be categorized into one of the following authoritative categories:

1. **unauthorized_transaction**:
   - Customer indicates they did not make, authorize, or participate in the transaction.
   - Keywords/Phrases: "not mine", "unauthorized", "unauthorised", "did not authorize", "scam", "stolen card", "hacked account".
   - Non-negotiable requirement: Always set `requires_human_review = true` and `status = under_review`.

2. **duplicate_payment**:
   - Customer reports multiple debits for a single purchase.
   - Keywords/Phrases: "charged twice", "duplicate", "double charge", "billed two times".
   - Requirement: Query duplicate detection tool within a 10-minute window.

3. **goods_not_received**:
   - Customer paid for merchandise or services that failed to arrive.
   - Keywords/Phrases: "never delivered", "not received", "didn't arrive", "package missing".
   - Requirement: Request merchant delivery tracking evidence.

4. **billing_dispute**:
   - Customer disputes charge amount, arithmetic errors, currency conversions, or post-cancellation subscription charges.
   - Keywords/Phrases: "wrong amount", "charged more than receipt", "billing error", "canceled subscription".

5. **other**:
   - Legitimate card dispute that does not fit into the standard four categories (e.g. defective merchandise, returned goods without refund credit).

6. **unknown**:
   - Ambiguous, unparseable, or missing customer narrative. Case requires customer re-engagement for clarification.
