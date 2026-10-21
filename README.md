# unauthorised-transaction-dispute-triage
ML-powered fraud detection and AI-agent-based card dispute triage with tool integration and Agent Ops monitoring.
Mini Project for the subject ML System Design & Agent Ops

## Fraud Detection Model (Member 1)

### Setup
```bash
pip install -r requirements.txt
```

### Train the model
Place the Kaggle Credit Card Fraud Detection dataset at `data/creditcard.csv`, then run:
```bash
python ml/train_model.py
```

### Run tests
```bash
python -m pytest ml/test_fraud_model.py -v
```

### Prediction interface
Import `predict_fraud` from `ml.fraud_model`.

Input: A dictionary containing exactly 30 features: `Time`, `V1`–`V28`, and `Amount`.

Output: A dictionary containing `fraud_probability` and `risk_level` (`low`, `medium`, or `high`).

**Note:** The model uses anonymized credit-card dataset features. Integration with the project's actual transaction schema requires feature mapping and validation.
