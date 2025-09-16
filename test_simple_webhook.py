#!/usr/bin/env python3
"""
Simple test for deribit-compatible webhook endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_valid_payload():
    """Test with valid deribit-style payload"""
    
    payload = {
        "accountName": "account_1",
        "side": "buy",
        "exchange": "TIGER",
        "period": "1h",
        "marketPosition": "long",
        "prevMarketPosition": "flat",
        "symbol": "AAPL",
        "price": "150.50",
        "timestamp": "2025-09-09T21:30:00Z",
        "size": "10",
        "positionSize": "0",
        "id": "test_signal_001",
        "qtyType": "fixed"
    }
    
    print("🧪 Testing valid deribit-style payload")
    print(f"📡 URL: {BASE_URL}/webhook/signal")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/signal",
            json=payload,
            timeout=10
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('success')}")
            print(f"💬 Message: {result.get('message')}")
            print(f"🆔 Request ID: {result.get('request_id')}")
            return result.get('success', False)
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

def test_invalid_payload():
    """Test with invalid payload"""
    
    payload = {
        "accountName": "account_1",
        "side": "buy"
        # Missing required fields
    }
    
    print("\n⚠️  Testing invalid payload")
    print(f"📡 URL: {BASE_URL}/webhook/signal")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/signal",
            json=payload,
            timeout=10
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if not result.get('success'):
                print(f"✅ Error handling works!")
                print(f"💬 Message: {result.get('message')}")
                print(f"❌ Error: {result.get('error')}")
                return True
            else:
                print(f"❌ Unexpected success!")
                return False
        else:
            print(f"❌ Unexpected status: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

def main():
    """Run simple webhook tests"""
    print("🐅 Simple Tiger Webhook Test")
    print("=" * 50)
    
    results = []
    
    # Test 1: Valid payload
    results.append(("Valid payload", test_valid_payload()))
    
    # Test 2: Invalid payload
    results.append(("Invalid payload", test_invalid_payload()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")

if __name__ == "__main__":
    main()
