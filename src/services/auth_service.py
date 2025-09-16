"""
Authentication service for Tiger Brokers API
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..config import AccountConfig, ApiKeysConfig, load_api_keys_config
from ..models import ConfigValidationResult
from .tiger_client_factory import TigerClientFactory, TigerClientType


logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication related error"""
    pass


class AuthService:
    """Authentication service for managing Tiger API credentials and connections"""
    
    def __init__(self):
        """Initialize authentication service"""
        self._api_keys_config: Optional[ApiKeysConfig] = None
        self._account_configs: Dict[str, AccountConfig] = {}
        self._connection_status: Dict[str, bool] = {}
        self._last_validation: Optional[datetime] = None
        
        logger.info("Authentication service initialized")
    
    def load_configuration(self, config_file: Optional[str] = None) -> ConfigValidationResult:
        """Load and validate API keys configuration"""
        try:
            # Load configuration
            self._api_keys_config = load_api_keys_config(config_file)
            
            # Build account configs dictionary
            self._account_configs = {
                account.name: account 
                for account in self._api_keys_config.accounts
            }
            
            # Validate configuration
            validation_result = self._validate_configuration()
            self._last_validation = datetime.now()
            
            logger.info(f"Configuration loaded: {len(self._account_configs)} accounts")
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise AuthenticationError(f"Configuration loading failed: {e}")
    
    def _validate_configuration(self) -> ConfigValidationResult:
        """Validate the loaded configuration"""
        errors = []
        warnings = []
        valid_accounts = 0
        
        if not self._api_keys_config:
            errors.append("No configuration loaded")
            return ConfigValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                total_accounts=0,
                enabled_accounts=0,
                valid_accounts=0
            )
        
        enabled_accounts = len(self._api_keys_config.enabled_accounts)
        
        if enabled_accounts == 0:
            warnings.append("No enabled accounts found")
        
        # Validate each account
        for account in self._api_keys_config.accounts:
            account_errors = self._validate_account(account)
            
            if account_errors:
                for error in account_errors:
                    errors.append(f"Account '{account.name}': {error}")
            else:
                valid_accounts += 1
        
        is_valid = len(errors) == 0 and enabled_accounts > 0
        
        return ConfigValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            total_accounts=len(self._api_keys_config.accounts),
            enabled_accounts=enabled_accounts,
            valid_accounts=valid_accounts
        )
    
    def _validate_account(self, account: AccountConfig) -> List[str]:
        """Validate a single account configuration"""
        errors = []
        
        # Check required fields
        if not account.tiger_id:
            errors.append("Tiger ID is required")
        
        if not account.account:
            errors.append("Account number is required")
        
        if not account.private_key_path:
            errors.append("Private key path is required")
        
        # Check private key file
        if account.private_key_path:
            if not account.is_private_key_valid():
                errors.append(f"Private key file not found or not readable: {account.private_key_path}")
        
        # Validate settings
        if account.max_position_size <= 0:
            errors.append("Max position size must be positive")
        
        return errors
    
    def get_account_config(self, account_name: str) -> Optional[AccountConfig]:
        """Get account configuration by name"""
        return self._account_configs.get(account_name)
    
    def get_enabled_account_config(self, account_name: str) -> Optional[AccountConfig]:
        """Get enabled account configuration by name"""
        account = self.get_account_config(account_name)
        return account if account and account.enabled else None
    
    def get_all_account_configs(self) -> Dict[str, AccountConfig]:
        """Get all account configurations"""
        return self._account_configs.copy()
    
    def get_enabled_account_configs(self) -> Dict[str, AccountConfig]:
        """Get all enabled account configurations"""
        return {
            name: config 
            for name, config in self._account_configs.items() 
            if config.enabled
        }
    
    def get_account_names(self) -> List[str]:
        """Get list of all account names"""
        return list(self._account_configs.keys())
    
    def get_enabled_account_names(self) -> List[str]:
        """Get list of enabled account names"""
        return [
            name for name, config in self._account_configs.items() 
            if config.enabled
        ]
    
    def test_connection(self, account_name: str) -> bool:
        """Test connection for a specific account"""
        account_config = self.get_enabled_account_config(account_name)
        if not account_config:
            logger.error(f"Account not found or disabled: {account_name}")
            return False
        
        try:
            client = TigerClientFactory.get_client(account_config)
            success = client.test_connection()
            self._connection_status[account_name] = success
            
            if success:
                logger.info(f"Connection test successful for account: {account_name}")
            else:
                logger.error(f"Connection test failed for account: {account_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Connection test error for account {account_name}: {e}")
            self._connection_status[account_name] = False
            return False
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test connections for all enabled accounts"""
        results = {}
        enabled_configs = self.get_enabled_account_configs()
        
        for account_name, account_config in enabled_configs.items():
            results[account_name] = self.test_connection(account_name)
        
        return results
    
    def get_connection_status(self, account_name: str) -> Optional[bool]:
        """Get cached connection status for an account"""
        return self._connection_status.get(account_name)
    
    def get_all_connection_status(self) -> Dict[str, bool]:
        """Get cached connection status for all accounts"""
        return self._connection_status.copy()
    
    def get_client(self, account_name: str) -> Optional[TigerClientType]:
        """Get Tiger client for an account"""
        account_config = self.get_enabled_account_config(account_name)
        if not account_config:
            return None
        
        return TigerClientFactory.get_client(account_config)
    
    def get_all_clients(self) -> Dict[str, TigerClientType]:
        """Get Tiger clients for all enabled accounts"""
        clients = {}
        enabled_configs = self.get_enabled_account_configs()
        
        for account_name, account_config in enabled_configs.items():
            try:
                client = TigerClientFactory.get_client(account_config)
                clients[account_name] = client
            except Exception as e:
                logger.error(f"Failed to get client for account {account_name}: {e}")
        
        return clients
    
    def reload_configuration(self, config_file: Optional[str] = None) -> ConfigValidationResult:
        """Reload configuration and clear client cache"""
        # Clear client cache
        TigerClientFactory.clear_cache()
        self._connection_status.clear()
        
        # Reload configuration
        return self.load_configuration(config_file)
    
    def is_account_valid(self, account_name: str) -> bool:
        """Check if an account is valid and enabled"""
        account_config = self.get_account_config(account_name)
        if not account_config or not account_config.enabled:
            return False
        
        # Check if private key is valid
        return account_config.is_private_key_valid()
    
    def get_account_summary(self) -> Dict[str, any]:
        """Get summary of all accounts"""
        total_accounts = len(self._account_configs)
        enabled_accounts = len(self.get_enabled_account_configs())
        
        # Count accounts by status
        connected_accounts = sum(1 for status in self._connection_status.values() if status)
        failed_accounts = sum(1 for status in self._connection_status.values() if not status)
        
        return {
            "total_accounts": total_accounts,
            "enabled_accounts": enabled_accounts,
            "connected_accounts": connected_accounts,
            "failed_accounts": failed_accounts,
            "last_validation": self._last_validation.isoformat() if self._last_validation else None,
            "account_names": self.get_account_names(),
            "enabled_account_names": self.get_enabled_account_names(),
        }


# Global authentication service instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get global authentication service instance"""
    global _auth_service
    
    if _auth_service is None:
        _auth_service = AuthService()
        # Load configuration on first access
        try:
            _auth_service.load_configuration()
        except Exception as e:
            logger.warning(f"Failed to load configuration on startup: {e}")
    
    return _auth_service


def initialize_auth_service(config_file: Optional[str] = None) -> ConfigValidationResult:
    """Initialize authentication service with configuration"""
    auth_service = get_auth_service()
    return auth_service.load_configuration(config_file)
