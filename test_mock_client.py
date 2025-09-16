#!/usr/bin/env python3
"""
Test mock client directly
"""

from src.services.mock_tiger_client import MockTigerClient
from src.config import AccountConfig

def test_mock_client():
    # Create mock account config
    account_config = AccountConfig(
        name="test_account",
        description="Test account",
        account="test_account",
        private_key_path="test.pem",
        tiger_id="test_id",
        account_type="STANDARD",
        market="US",
        language="en_US",
        timezone="America/New_York",
        default_position_size=100
    )
    
    # Create mock client
    client = MockTigerClient(account_config)
    
    # Test get_option_chain
    print("Testing get_option_chain...")
    option_chain = client.get_option_chain("AAPL")
    print(f"Option chain length: {len(option_chain)}")
    
    if option_chain:
        print("First contract:")
        print(option_chain[0])
    else:
        print("No option chain data returned!")

if __name__ == "__main__":
    test_mock_client()
