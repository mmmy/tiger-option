#!/usr/bin/env python3
"""
Test script for webhook endpoints
"""

import json
import requests
from decimal import Decimal

def test_webhook_signal():
    """Test webhook signal endpoint"""
    
    # Test data
    signal_data = {
        "signal_id": "test_signal_001",
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 100,
        "price": 150.50,
        "order_type": "limit",
        "time_in_force": "day",
        "strategy": "test_strategy",
        "comment": "Test webhook signal"
    }
    
    url = "http://localhost:8000/webhook/signal/account_1"
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"Testing webhook endpoint: {url}")
        print(f"Signal data: {json.dumps(signal_data, indent=2)}")
        
        response = requests.post(url, json=signal_data, headers=headers, timeout=10)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        else:
            print(f"Response Text: {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

def test_webhook_health():
    """Test webhook health endpoint"""
    
    url = "http://localhost:8000/webhook/health"
    
    try:
        print(f"\nTesting webhook health: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"Response Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

def test_accounts_list():
    """Test accounts list endpoint"""
    
    url = "http://localhost:8000/api/accounts"
    
    try:
        print(f"\nTesting accounts list: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"Response Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

def test_queue_status():
    """Test queue status endpoint"""
    
    url = "http://localhost:8000/webhook/queue/status"
    
    try:
        print(f"\nTesting queue status: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"Response Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Tiger Options Trading Service - Webhook Tests ===\n")
    
    tests = [
        ("Webhook Health", test_webhook_health),
        ("Accounts List", test_accounts_list),
        ("Queue Status", test_queue_status),
        ("Webhook Signal", test_webhook_signal),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"\n✅ {test_name}: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
