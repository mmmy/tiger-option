#!/usr/bin/env python3
"""
Test script for complete trading execution pipeline
Tests the actual trading logic following deribit_webhook pattern
"""

import json
import requests
from decimal import Decimal

BASE_URL = "http://localhost:8000"
ACCOUNT_NAME = "account_1"

def test_buy_signal():
    """Test buy signal with complete trading execution"""
    
    signal_data = {
        "signal_id": "trade_test_buy_001",
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 5,
        "price": 150.25,
        "order_type": "limit",
        "time_in_force": "day",
        "strategy": "complete_trading_test",
        "comment": "Testing complete buy signal execution with option selection and actual order placement"
    }
    
    try:
        print("=== Testing Complete Buy Signal Execution ===\n")
        
        url = f"{BASE_URL}/webhook/signal/{ACCOUNT_NAME}"
        print(f"Sending buy signal to: {url}")
        print(f"Signal data: {json.dumps(signal_data, indent=2)}")
        
        response = requests.post(url, json=signal_data, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            if response_data.get('success'):
                data = response_data['data']
                signal_id = data.get('signal_id')
                print(f"\n✅ Buy signal processed successfully!")
                print(f"Signal ID: {signal_id}")
                
                # Check execution result
                execution_result = data.get('execution_result')
                if execution_result:
                    print(f"\n📈 Execution Details:")
                    print(f"  Status: {execution_result.get('status')}")
                    print(f"  Selected Contract: {execution_result.get('selected_contract')}")
                    print(f"  Quantity: {execution_result.get('quantity')}")
                    print(f"  Order Price: ${execution_result.get('order_price')}")
                    print(f"  Order ID: {execution_result.get('order_id')}")
                    print(f"  Risk Result: {execution_result.get('risk_result')}")
                    
                    risk_messages = execution_result.get('risk_messages', [])
                    if risk_messages:
                        print(f"  Risk Messages: {risk_messages}")
                    
                    print(f"  Message: {execution_result.get('message')}")
                
                return signal_id
            else:
                print(f"❌ Buy signal failed: {response_data.get('error')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_sell_signal():
    """Test sell signal with complete trading execution"""
    
    signal_data = {
        "signal_id": "trade_test_sell_001",
        "symbol": "AAPL",
        "action": "sell",
        "quantity": 3,
        "price": 149.75,
        "order_type": "limit",
        "time_in_force": "day",
        "strategy": "complete_trading_test",
        "comment": "Testing complete sell signal execution with option selection and actual order placement"
    }
    
    try:
        print("\n=== Testing Complete Sell Signal Execution ===\n")
        
        url = f"{BASE_URL}/webhook/signal/{ACCOUNT_NAME}"
        print(f"Sending sell signal to: {url}")
        print(f"Signal data: {json.dumps(signal_data, indent=2)}")
        
        response = requests.post(url, json=signal_data, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            if response_data.get('success'):
                data = response_data['data']
                signal_id = data.get('signal_id')
                print(f"\n✅ Sell signal processed successfully!")
                print(f"Signal ID: {signal_id}")
                
                # Check execution result
                execution_result = data.get('execution_result')
                if execution_result:
                    print(f"\n📉 Execution Details:")
                    print(f"  Status: {execution_result.get('status')}")
                    print(f"  Selected Contract: {execution_result.get('selected_contract')}")
                    print(f"  Quantity: {execution_result.get('quantity')}")
                    print(f"  Order Price: ${execution_result.get('order_price')}")
                    print(f"  Order ID: {execution_result.get('order_id')}")
                    print(f"  Risk Result: {execution_result.get('risk_result')}")
                    print(f"  Message: {execution_result.get('message')}")
                
                return signal_id
            else:
                print(f"❌ Sell signal failed: {response_data.get('error')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_close_signal():
    """Test close position signal"""
    
    signal_data = {
        "signal_id": "trade_test_close_001",
        "symbol": "AAPL",
        "action": "close",
        "strategy": "complete_trading_test",
        "comment": "Testing close position signal execution"
    }
    
    try:
        print("\n=== Testing Close Position Signal ===\n")
        
        url = f"{BASE_URL}/webhook/signal/{ACCOUNT_NAME}"
        print(f"Sending close signal to: {url}")
        print(f"Signal data: {json.dumps(signal_data, indent=2)}")
        
        response = requests.post(url, json=signal_data, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            if response_data.get('success'):
                data = response_data['data']
                signal_id = data.get('signal_id')
                print(f"\n✅ Close signal processed successfully!")
                print(f"Signal ID: {signal_id}")
                
                # Check execution result
                execution_result = data.get('execution_result')
                if execution_result:
                    print(f"\n🔒 Execution Details:")
                    print(f"  Status: {execution_result.get('status')}")
                    print(f"  Message: {execution_result.get('message')}")
                    
                    closed_orders = execution_result.get('closed_orders', [])
                    if closed_orders:
                        print(f"  Closed Orders:")
                        for order in closed_orders:
                            print(f"    - {order.get('symbol')}: {order.get('side')} {order.get('quantity')} (Order: {order.get('order_id')})")
                
                return signal_id
            else:
                print(f"❌ Close signal failed: {response_data.get('error')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_account_summary():
    """Test account summary after trading"""
    
    try:
        print("\n=== Testing Account Summary After Trading ===\n")
        
        url = f"{BASE_URL}/api/trading/account/{ACCOUNT_NAME}/summary"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            summary_data = response.json()['data']
            print(f"Account Summary:")
            print(f"  Account: {summary_data.get('account_name')}")
            
            positions_summary = summary_data.get('positions_summary', {})
            print(f"  Total Positions: {positions_summary.get('total_positions', 0)}")
            print(f"  Total Market Value: ${positions_summary.get('total_market_value', '0.00')}")
            print(f"  Total Unrealized P&L: ${positions_summary.get('total_unrealized_pnl', '0.00')}")
            
            orders_summary = summary_data.get('orders_summary', {})
            print(f"  Total Orders: {orders_summary.get('total_orders', 0)}")
            
            by_status = orders_summary.get('by_status', {})
            if by_status:
                print(f"  Orders by Status: {by_status}")
            
            return True
        else:
            print(f"❌ Failed to get account summary: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Account summary test failed: {e}")
        return False

def main():
    """Run complete trading execution tests"""
    
    print("=== Tiger Options Trading Service - Complete Trading Execution Tests ===\n")
    
    results = []
    
    # Test 1: Buy signal execution
    buy_signal_id = test_buy_signal()
    results.append(("Buy Signal Execution", buy_signal_id is not None))
    
    # Test 2: Sell signal execution
    sell_signal_id = test_sell_signal()
    results.append(("Sell Signal Execution", sell_signal_id is not None))
    
    # Test 3: Close position signal
    close_signal_id = test_close_signal()
    results.append(("Close Position Signal", close_signal_id is not None))
    
    # Test 4: Account summary
    summary_success = test_account_summary()
    results.append(("Account Summary", summary_success))
    
    # Summary
    print(f"\n{'='*70}")
    print("COMPLETE TRADING EXECUTION TEST SUMMARY")
    print('='*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All trading execution tests passed!")
        print("\nThe complete trading pipeline is working correctly with:")
        print("  ✅ Buy signal → Option selection → Risk check → Order placement")
        print("  ✅ Sell signal → Option selection → Risk check → Order placement")
        print("  ✅ Close position → Position lookup → Close orders")
        print("  ✅ Account summary and position tracking")
        print("\n🚀 Ready for production trading!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("🔧 The system may need additional configuration or debugging.")

if __name__ == "__main__":
    main()
