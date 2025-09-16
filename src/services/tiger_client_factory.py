"""
Tiger client factory for creating appropriate client instances
"""

import logging
from typing import Union, Dict, Optional

from ..config import AccountConfig, get_settings
from .tiger_client import TigerClient
from .mock_tiger_client import MockTigerClient


logger = logging.getLogger(__name__)

# Type alias for client types
TigerClientType = Union[TigerClient, MockTigerClient]


class TigerClientFactory:
    """Factory for creating Tiger client instances"""
    
    _clients: Dict[str, TigerClientType] = {}
    
    @classmethod
    def create_client(cls, account_config: AccountConfig) -> TigerClientType:
        """Create a Tiger client instance based on configuration"""
        settings = get_settings()

        # Check if we should use mock mode or if tigeropen is not available
        try:
            from .tiger_client import TIGEROPEN_AVAILABLE
        except ImportError:
            TIGEROPEN_AVAILABLE = False

        if settings.use_mock_mode or not TIGEROPEN_AVAILABLE:
            logger.info(f"Creating Mock Tiger client for account: {account_config.name}")
            return MockTigerClient(account_config)
        else:
            logger.info(f"Creating real Tiger client for account: {account_config.name}")
            return TigerClient(account_config)
    
    @classmethod
    def get_client(cls, account_config: AccountConfig) -> TigerClientType:
        """Get or create a cached Tiger client instance"""
        account_name = account_config.name
        
        if account_name not in cls._clients:
            cls._clients[account_name] = cls.create_client(account_config)
        
        return cls._clients[account_name]
    
    @classmethod
    def get_client_by_name(cls, account_name: str, account_configs: Dict[str, AccountConfig]) -> Optional[TigerClientType]:
        """Get client by account name"""
        if account_name not in account_configs:
            logger.error(f"Account configuration not found: {account_name}")
            return None
        
        account_config = account_configs[account_name]
        if not account_config.enabled:
            logger.error(f"Account is disabled: {account_name}")
            return None
        
        return cls.get_client(account_config)
    
    @classmethod
    def clear_cache(cls):
        """Clear the client cache"""
        cls._clients.clear()
        logger.info("Tiger client cache cleared")
    
    @classmethod
    def remove_client(cls, account_name: str):
        """Remove a specific client from cache"""
        if account_name in cls._clients:
            del cls._clients[account_name]
            logger.info(f"Removed Tiger client from cache: {account_name}")
    
    @classmethod
    def test_all_connections(cls, account_configs: Dict[str, AccountConfig]) -> Dict[str, bool]:
        """Test connections for all enabled accounts"""
        results = {}
        
        for account_name, account_config in account_configs.items():
            if not account_config.enabled:
                continue
            
            try:
                client = cls.get_client(account_config)
                results[account_name] = client.test_connection()
            except Exception as e:
                logger.error(f"Failed to test connection for {account_name}: {e}")
                results[account_name] = False
        
        return results
    
    @classmethod
    def get_all_clients(cls, account_configs: Dict[str, AccountConfig]) -> Dict[str, TigerClientType]:
        """Get all clients for enabled accounts"""
        clients = {}
        
        for account_name, account_config in account_configs.items():
            if not account_config.enabled:
                continue
            
            try:
                client = cls.get_client(account_config)
                clients[account_name] = client
            except Exception as e:
                logger.error(f"Failed to create client for {account_name}: {e}")
        
        return clients


# Convenience functions

def create_tiger_client(account_config: AccountConfig) -> TigerClientType:
    """Create a Tiger client instance"""
    return TigerClientFactory.create_client(account_config)


def get_tiger_client(account_config: AccountConfig) -> TigerClientType:
    """Get or create a cached Tiger client instance"""
    return TigerClientFactory.get_client(account_config)


def get_tiger_client_by_name(account_name: str, account_configs: Dict[str, AccountConfig]) -> Optional[TigerClientType]:
    """Get Tiger client by account name"""
    return TigerClientFactory.get_client_by_name(account_name, account_configs)
