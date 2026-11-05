"""
test_classification.py — Tests for Complaint Classification & Keyword Fallback (Unit 3.A)
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from classification.keyword_fallback import KeywordFallbackClassifier
from classification.gemini_classifier import GeminiClassifier


def test_keyword_unauthorized_classification():
    cat = KeywordFallbackClassifier.classify_text("I did not authorize this charge at 2 AM.")
    assert cat == "unauthorized_transaction"


def test_keyword_duplicate_classification():
    cat = KeywordFallbackClassifier.classify_text("I was charged twice for the same purchase.")
    assert cat == "duplicate_payment"


def test_keyword_goods_not_received():
    cat = KeywordFallbackClassifier.classify_text("My order was paid for but never arrived.")
    assert cat == "goods_not_received"


def test_keyword_billing_dispute():
    cat = KeywordFallbackClassifier.classify_text("There is a wrong amount and incorrect billing charge.")
    assert cat == "billing_dispute"


def test_keyword_unknown():
    cat = KeywordFallbackClassifier.classify_text("Hello there.")
    assert cat == "unknown"


def test_gemini_fallback_when_no_api_key():
    clf = GeminiClassifier(api_key="")
    res = clf.classify("I did not authorize this payment.", "TX1001")
    assert res["category"] == "unauthorized_transaction"
    assert res["fallback_used"] is True
