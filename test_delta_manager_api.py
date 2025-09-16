#!/usr/bin/env python3
"""
Test script for Delta Manager API endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', 'N/A')}")
            print(f"Message: {result.get('message', 'N/A')}")
            
            # Print data summary
            data = result.get('data')
            if isinstance(data, list):
                print(f"Data: {len(data)} items")
                if data and len(data) > 0:
                    print(f"First item: {json.dumps(data[0], indent=2)[:200]}...")
            elif isinstance(data, dict):
                print(f"Data keys: {list(data.keys())}")
            else:
                print(f"Data: {data}")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Test all Delta Manager API endpoints"""
    print("🐅 Testing Tiger Options Delta Manager API")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test endpoints
    endpoints = [
        "/api/accounts",
        "/api/accounts/account_1/summary",
        "/api/accounts/account_1/positions",
        "/api/accounts/account_1/orders",
        "/api/accounts/account_1/trades",
    ]
    
    results = []
    
    for endpoint in endpoints:
        success = test_api_endpoint(endpoint)
        results.append((endpoint, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for endpoint, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {endpoint}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Delta Manager API is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the server logs for details.")

if __name__ == "__main__":
    main()
