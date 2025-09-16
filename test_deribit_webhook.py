#!/usr/bin/env python3
"""
Test script for deribit-compatible webhook endpoint
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_deribit_webhook():
    """Test the deribit-compatible webhook endpoint"""
    
    # Sample payload matching deribit_webhook format
    deribit_payload = {
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
        "qtyType": "fixed",
        "alertMessage": "Test signal from TradingView",
        "comment": "Opening AAPL long position",
        "tv_id": 12345,
        "delta1": 0.5,
        "n": 30,
        "delta2": 0.6
    }
    
    print("🧪 Testing deribit-compatible webhook endpoint")
    print("=" * 60)
    print(f"📡 Sending payload to: {BASE_URL}/webhook/signal")
    print(f"📋 Payload: {json.dumps(deribit_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/signal",
            json=deribit_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📝 Success: {result.get('success')}")
            print(f"💬 Message: {result.get('message')}")
            print(f"🆔 Request ID: {result.get('request_id')}")
            
            # Print data details
            data = result.get('data', {})
            if data:
                print("\n📊 Response Data:")
                for key, value in data.items():
                    print(f"  • {key}: {value}")
            
            return True
        else:
            print("❌ FAILED!")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

def test_original_webhook():
    """Test the original webhook endpoint for comparison"""
    
    # Sample payload for original format
    original_payload = {
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 10,
        "price": 150.50,
        "order_type": "market",
        "strategy": "test_strategy",
        "comment": "Test signal"
    }
    
    print("\n🔄 Testing original webhook endpoint for comparison")
    print("=" * 60)
    print(f"📡 Sending payload to: {BASE_URL}/webhook/signal/account_1")
    print(f"📋 Payload: {json.dumps(original_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/signal/account_1",
            json=original_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📝 Success: {result.get('success')}")
            print(f"💬 Message: {result.get('message')}")
            return True
        else:
            print("❌ FAILED!")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

def test_invalid_payload():
    """Test with invalid payload to check error handling"""
    
    # Invalid payload missing required fields
    invalid_payload = {
        "accountName": "account_1",
        "side": "buy",
        # Missing required fields: symbol, size, qtyType
    }
    
    print("\n⚠️  Testing invalid payload (error handling)")
    print("=" * 60)
    print(f"📡 Sending invalid payload to: {BASE_URL}/webhook/signal")
    print(f"📋 Payload: {json.dumps(invalid_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/signal",
            json=invalid_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if not result.get('success'):
                print("✅ ERROR HANDLING WORKS!")
                print(f"💬 Error Message: {result.get('message')}")
                print(f"❌ Error Details: {result.get('error')}")
                return True
            else:
                print("❌ UNEXPECTED SUCCESS - should have failed!")
                return False
        else:
            print("❌ UNEXPECTED STATUS CODE!")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

def main():
    """Run all webhook tests"""
    print("🐅 Tiger Options Webhook Compatibility Test")
    print("Testing deribit_webhook format compatibility")
    print("=" * 80)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    results = []
    
    # Test 1: deribit-compatible webhook
    results.append(("Deribit-compatible webhook", test_deribit_webhook()))
    
    # Test 2: Original webhook (for comparison)
    results.append(("Original webhook format", test_original_webhook()))
    
    # Test 3: Error handling
    results.append(("Error handling test", test_invalid_payload()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Webhook compatibility is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the server logs for details.")

if __name__ == "__main__":
    main()
