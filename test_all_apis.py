#!/usr/bin/env python3
"""
Comprehensive test script for all Tiger Options Trading Service APIs
"""

import json
import requests
from decimal import Decimal

BASE_URL = "http://localhost:8000"
ACCOUNT_NAME = "account_1"

def test_health_endpoints():
    """Test all health check endpoints"""
    
    endpoints = [
        "/health",
        "/api/health", 
        "/webhook/health",
        "/api/market/health",
        "/api/trading/health"
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            success = response.status_code == 200
            results.append((endpoint, success, response.status_code))
            
            if success:
                print(f"✅ {endpoint}: OK")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except Exception as e:
            results.append((endpoint, False, str(e)))
            print(f"❌ {endpoint}: ERROR - {e}")
    
    return results

def test_account_endpoints():
    """Test account management endpoints"""
    
    endpoints = [
        "/api/accounts",
        f"/api/accounts/{ACCOUNT_NAME}/info",
        f"/api/accounts/{ACCOUNT_NAME}/test-connection"
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            success = response.status_code == 200
            results.append((endpoint, success, response.status_code))
            
            if success:
                print(f"✅ {endpoint}: OK")
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = response.json()
                    if 'data' in data:
                        print(f"   Data: {json.dumps(data['data'], indent=2)[:200]}...")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except Exception as e:
            results.append((endpoint, False, str(e)))
            print(f"❌ {endpoint}: ERROR - {e}")
    
    return results

def test_market_endpoints():
    """Test market data endpoints"""
    
    endpoints = [
        f"/api/market/search/AAPL?account_name={ACCOUNT_NAME}",
        f"/api/market/search/TSLA?account_name={ACCOUNT_NAME}&limit=5",
        f"/api/market/option-expirations/AAPL?account_name={ACCOUNT_NAME}",
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            success = response.status_code == 200
            results.append((endpoint, success, response.status_code))
            
            if success:
                print(f"✅ {endpoint}: OK")
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = response.json()
                    if 'data' in data:
                        print(f"   Found {len(data['data']) if isinstance(data['data'], list) else 1} items")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except Exception as e:
            results.append((endpoint, False, str(e)))
            print(f"❌ {endpoint}: ERROR - {e}")
    
    return results

def test_trading_endpoints():
    """Test trading endpoints"""
    
    # Test GET endpoints first
    get_endpoints = [
        f"/api/trading/orders/{ACCOUNT_NAME}",
        f"/api/trading/positions/{ACCOUNT_NAME}",
        f"/api/trading/account/{ACCOUNT_NAME}/summary"
    ]
    
    results = []
    
    for endpoint in get_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            success = response.status_code == 200
            results.append((endpoint, success, response.status_code))
            
            if success:
                print(f"✅ {endpoint}: OK")
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = response.json()
                    if 'data' in data:
                        if isinstance(data['data'], list):
                            print(f"   Found {len(data['data'])} items")
                        else:
                            print(f"   Data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'N/A'}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except Exception as e:
            results.append((endpoint, False, str(e)))
            print(f"❌ {endpoint}: ERROR - {e}")
    
    return results

def test_webhook_endpoints():
    """Test webhook endpoints"""
    
    # Test webhook signal
    signal_data = {
        "signal_id": "test_comprehensive_001",
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 50,
        "price": 155.00,
        "order_type": "limit",
        "time_in_force": "day",
        "strategy": "comprehensive_test",
        "comment": "Comprehensive API test signal"
    }
    
    results = []
    
    try:
        # Send webhook signal
        url = f"{BASE_URL}/webhook/signal/{ACCOUNT_NAME}"
        response = requests.post(url, json=signal_data, timeout=10)
        
        success = response.status_code == 200
        results.append(("POST /webhook/signal", success, response.status_code))
        
        if success:
            print(f"✅ POST /webhook/signal/{ACCOUNT_NAME}: OK")
            data = response.json()
            if data.get('success'):
                signal_id = data['data'].get('signal_id')
                print(f"   Signal ID: {signal_id}")
        else:
            print(f"❌ POST /webhook/signal/{ACCOUNT_NAME}: {response.status_code}")
            
    except Exception as e:
        results.append(("POST /webhook/signal", False, str(e)))
        print(f"❌ POST /webhook/signal/{ACCOUNT_NAME}: ERROR - {e}")
    
    # Test queue status
    try:
        url = f"{BASE_URL}/webhook/queue/status"
        response = requests.get(url, timeout=10)
        
        success = response.status_code == 200
        results.append(("GET /webhook/queue/status", success, response.status_code))
        
        if success:
            print(f"✅ GET /webhook/queue/status: OK")
            data = response.json()
            if 'data' in data:
                queue_data = data['data']
                print(f"   Queue length: {queue_data.get('queue_length', 0)}")
                print(f"   Total signals: {queue_data.get('total_signals', 0)}")
        else:
            print(f"❌ GET /webhook/queue/status: {response.status_code}")
            
    except Exception as e:
        results.append(("GET /webhook/queue/status", False, str(e)))
        print(f"❌ GET /webhook/queue/status: ERROR - {e}")
    
    # Test queue processing
    try:
        url = f"{BASE_URL}/webhook/queue/process"
        response = requests.post(url, timeout=10)
        
        success = response.status_code == 200
        results.append(("POST /webhook/queue/process", success, response.status_code))
        
        if success:
            print(f"✅ POST /webhook/queue/process: OK")
            data = response.json()
            if 'data' in data:
                process_data = data['data']
                print(f"   Processed: {process_data.get('processed_count', 0)}")
                print(f"   Failed: {process_data.get('failed_count', 0)}")
        else:
            print(f"❌ POST /webhook/queue/process: {response.status_code}")
            
    except Exception as e:
        results.append(("POST /webhook/queue/process", False, str(e)))
        print(f"❌ POST /webhook/queue/process: ERROR - {e}")
    
    return results

def main():
    """Run comprehensive API tests"""
    
    print("=== Tiger Options Trading Service - Comprehensive API Tests ===\n")
    
    all_results = []
    
    test_suites = [
        ("Health Endpoints", test_health_endpoints),
        ("Account Endpoints", test_account_endpoints),
        ("Market Data Endpoints", test_market_endpoints),
        ("Trading Endpoints", test_trading_endpoints),
        ("Webhook Endpoints", test_webhook_endpoints),
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n{'='*60}")
        print(f"Testing: {suite_name}")
        print('='*60)
        
        try:
            results = test_func()
            all_results.extend(results)
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            all_results.append((suite_name, False, str(e)))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success, _ in all_results if success)
    total = len(all_results)
    
    for endpoint, success, status in all_results:
        status_str = "✅ PASSED" if success else "❌ FAILED"
        print(f"{endpoint}: {status_str} ({status})")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
