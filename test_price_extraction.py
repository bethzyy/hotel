#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for price extraction enhancement
Tests various currency formats and price ranges
"""

import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.tavily import TavilyService

def test_price_extraction():
    """Test price extraction with various formats"""
    service = TavilyService(api_key='test')

    test_cases = [
        # (text, expected_price, expected_currency, description)
        ('$287 per night', 287, 'USD', 'USD per night'),
        ('Price: $272', 272, 'USD', 'USD with colon'),
        ('HK$1,019', 1019, 'HKD', 'HKD format'),
        ('NT$3,500', 3500, 'TWD', 'TWD format'),
        ('From $199', 199, 'USD', 'USD from price'),
        ('Starting at $249', 249, 'USD', 'USD starting at'),
        ('Best price: $189', 189, 'USD', 'USD best price'),
        ('RMB 888', 888, 'CNY', 'RMB format'),
        ('1,299 yuan', 1299, 'CNY', 'CNY with yuan suffix'),
        ('$272 - $362', 272, 'USD', 'USD range (lower)'),
        ('HK$800 - HK$1,200', 800, 'HKD', 'HKD range'),
        ('Price: EUR 150', 150, 'EUR', 'EUR format'),
        ('GBP 199', 199, 'GBP', 'GBP format'),
        # Edge cases - prices that should be filtered
        ('$5', None, 'CNY', 'Too low (filtered)'),
        ('$200000', None, 'CNY', 'Too high (filtered)'),
    ]

    print("\n" + "="*70)
    print("Price Extraction Test Results")
    print("="*70 + "\n")

    passed = 0
    failed = 0

    for text, expected_price, expected_currency, description in test_cases:
        price, currency = service._extract_price(text)

        if expected_price is None:
            # Should not extract a price
            if price is None:
                status = "[PASS]"
                passed += 1
            else:
                status = "[FAIL]"
                failed += 1
        elif price == expected_price and currency == expected_currency:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1

        # Safe print with encoding handling
        try:
            print(f"{status} {description}")
            if expected_price is not None:
                print(f"  Input: {text}")
                print(f"  Expected: {expected_price} {expected_currency} | Got: {price} {currency}")
            else:
                print(f"  Input: {text}")
                print(f"  Expected: No price | Got: {price} {currency}")
        except:
            print(f"{status} {description}")
            print(f"  Got: {price} {currency}")
        print()

    print("="*70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*70 + "\n")

    return failed == 0

if __name__ == '__main__':
    success = test_price_extraction()
    sys.exit(0 if success else 1)
