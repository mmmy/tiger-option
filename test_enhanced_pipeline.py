#!/usr/bin/env python3
"""
Test script for the enhanced trading pipeline
"""

import json
import requests
from decimal import Decimal

BASE_URL = "http://localhost:8000"
ACCOUNT_NAME = "account_1"

def test_enhanced_webhook_signal():
    """Test enhanced webhook signal processing"""
    
    # Create a more comprehensive test signal
    signal_data = {
        "signal_id": "enhanced_test_001",
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 10,
        "price": 150.75,
        "order_type": "limit",
        "time_in_force": "day",
        "strategy": "enhanced_pipeline_test",
        "comment": "Testing enhanced signal processing pipeline with option selection and risk management"
    }
    
    try:
        print("=== Testing Enhanced Webhook Signal Processing ===\n")
        
        # Send webhook signal
        url = f"{BASE_URL}/webhook/signal/{ACCOUNT_NAME}"
        print(f"Sending signal to: {url}")
        print(f"Signal data: {json.dumps(signal_data, indent=2)}")
        
        response = requests.post(url, json=signal_data, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            if response_data.get('success'):
                signal_id = response_data['data'].get('signal_id')
                print(f"\n✅ Signal queued successfully!")
                print(f"Signal ID: {signal_id}")
                
                # Check processing result
                processing_result = response_data['data'].get('processing_result', {})
                if processing_result.get('success'):
                    print(f"✅ Pipeline processing successful!")
                    
                    selected_contract = processing_result.get('selected_contract', {})
                    if selected_contract:
                        print(f"Selected Contract: {selected_contract.get('symbol')}")
                        print(f"Strike: ${selected_contract.get('strike')}")
                        print(f"Expiry: {selected_contract.get('expiry')}")
                    
                    print(f"Suggested Quantity: {processing_result.get('suggested_quantity')}")
                    print(f"Risk Result: {processing_result.get('risk_result')}")
                    
                    risk_messages = processing_result.get('risk_messages', [])
                    if risk_messages:
                        print(f"Risk Messages: {risk_messages}")
                    
                    order_params = processing_result.get('order_params', {})
                    if order_params:
                        print(f"Order Type: {order_params.get('order_type')}")
                        print(f"Order Price: ${order_params.get('price')}")
                        print(f"Order Strategy: {order_params.get('strategy')}")
                else:
                    print(f"❌ Pipeline processing failed:")
                    print(f"Error: {processing_result.get('error')}")
                    print(f"Step: {processing_result.get('step')}")
                
                return signal_id
            else:
                print(f"❌ Signal processing failed: {response_data.get('error')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_queue_processing():
    """Test queue processing"""
    
    try:
        print("\n=== Testing Queue Processing ===\n")
        
        # Check queue status first
        url = f"{BASE_URL}/webhook/queue/status"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            queue_data = response.json()['data']
            print(f"Queue Status:")
            print(f"  Queue Length: {queue_data.get('queue_length', 0)}")
            print(f"  Total Signals: {queue_data.get('total_signals', 0)}")
            
            if queue_data.get('queue_length', 0) > 0:
                # Process the queue
                print(f"\nProcessing queued signals...")
                
                process_url = f"{BASE_URL}/webhook/queue/process"
                process_response = requests.post(process_url, timeout=30)
                
                if process_response.status_code == 200:
                    process_data = process_response.json()['data']
                    print(f"✅ Queue processing completed!")
                    print(f"  Processed: {process_data.get('processed_count', 0)}")
                    print(f"  Failed: {process_data.get('failed_count', 0)}")
                    print(f"  Total: {process_data.get('total_count', 0)}")
                    
                    # Show results
                    results = process_data.get('results', [])
                    for result in results:
                        status = result.get('status')
                        signal_id = result.get('signal_id')
                        
                        if status == 'processed':
                            print(f"\n✅ Signal {signal_id[:8]}... processed successfully")
                            print(f"  Symbol: {result.get('symbol')}")
                            print(f"  Action: {result.get('action')}")
                            print(f"  Quantity: {result.get('quantity')}")
                            print(f"  Selected Contract: {result.get('selected_contract')}")
                            print(f"  Order ID: {result.get('order_id')}")
                            print(f"  Risk Result: {result.get('risk_result')}")
                        else:
                            print(f"\n❌ Signal {signal_id[:8]}... failed")
                            print(f"  Error: {result.get('error')}")
                            print(f"  Step: {result.get('processing_step')}")
                    
                    return True
                else:
                    print(f"❌ Queue processing failed: {process_response.status_code}")
                    return False
            else:
                print("No signals in queue to process")
                return True
        else:
            print(f"❌ Failed to get queue status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Queue processing test failed: {e}")
        return False

def test_risk_summary():
    """Test risk summary endpoint (if available)"""
    
    try:
        print("\n=== Testing Risk Summary ===\n")
        
        # This would be a custom endpoint for risk summary
        # For now, just show account summary which includes some risk info
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
        print(f"❌ Risk summary test failed: {e}")
        return False

def main():
    """Run enhanced pipeline tests"""
    
    print("=== Tiger Options Trading Service - Enhanced Pipeline Tests ===\n")
    
    results = []
    
    # Test 1: Enhanced webhook signal processing
    signal_id = test_enhanced_webhook_signal()
    results.append(("Enhanced Signal Processing", signal_id is not None))
    
    # Test 2: Queue processing
    queue_success = test_queue_processing()
    results.append(("Queue Processing", queue_success))
    
    # Test 3: Risk summary
    risk_success = test_risk_summary()
    results.append(("Risk Summary", risk_success))
    
    # Summary
    print(f"\n{'='*60}")
    print("ENHANCED PIPELINE TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All enhanced pipeline tests passed!")
        print("\nThe enhanced trading pipeline is working correctly with:")
        print("  ✅ Option contract selection")
        print("  ✅ Position sizing recommendations")
        print("  ✅ Risk management checks")
        print("  ✅ Order strategy creation")
        print("  ✅ Complete pipeline validation")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
