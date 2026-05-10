"""Unit tests for OTP extraction logic (no real email connection needed)."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from otp_fetcher import OTPFetcher, OTP_PATTERNS
import re


def extract_otp_from_text(text: str):
    for pattern in OTP_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def test_amazon_style():
    text = "Your Amazon verification code is 847291"
    assert extract_otp_from_text(text) == "847291"

def test_walmart_style():
    text = "Walmart: Your one-time code is 391847. Do not share this code."
    assert extract_otp_from_text(text) == "391847"

def test_otp_prefix():
    text = "OTP: 123456"
    assert extract_otp_from_text(text) == "123456"

def test_code_prefix():
    text = "Your code: 9876 is valid for 10 minutes."
    assert extract_otp_from_text(text) == "9876"

def test_code_suffix():
    text = "482910 is your verification code"
    assert extract_otp_from_text(text) == "482910"

def test_no_otp():
    text = "Welcome to Amazon! Your order has been shipped."
    assert extract_otp_from_text(text) is None

def test_8digit():
    text = "Your secure code: 12345678"
    assert extract_otp_from_text(text) == "12345678"


if __name__ == "__main__":
    tests = [
        test_amazon_style,
        test_walmart_style,
        test_otp_prefix,
        test_code_prefix,
        test_code_suffix,
        test_no_otp,
        test_8digit,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")

    print(f"\n{passed}/{len(tests)} tests passed")
