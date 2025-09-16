#!/usr/bin/env python3
"""
Test single trade execution
"""

import json
import requests

def test_single_buy():
    signal_data = {
        "signal_id": "final_test_001",
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 2,
        "price": 150.50,
        "order_type": "limit",
        "strategy": "final_test"
    }
    
    response = requests.post(
        "http://localhost:8000/webhook/signal/account_1",
        json=signal_data,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_single_buy()
