"""
API Keys configuration loader for Tiger Options Trading Service
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, validator

from .settings import get_config_dir


class NotificationConfig(BaseModel):
    """Notification configuration"""
    webhook_url: Optional[str] = None
    timeout: int = Field(default=10000, description="Request timeout in milliseconds")
    retry_count: int = Field(default=3, description="Number of retry attempts")
    retry_delay: int = Field(default=1000, description="Delay between retries in milliseconds")
    enabled: bool = Field(default=True, description="Whether notifications are enabled")


class AccountConfig(BaseModel):
    """Tiger account configuration"""
    name: str = Field(description="Account name identifier")
    description: str = Field(description="Account description")
    tiger_id: str = Field(description="Tiger ID")
    private_key_path: str = Field(description="Path to private key file")
    account: str = Field(description="Account number")
    enabled: bool = Field(default=True, description="Whether account is enabled")
    
    # Environment settings
    sandbox_debug: bool = Field(default=True, description="Use test environment")
    language: str = Field(default="en_US", description="Language setting")
    
    # Trading settings
    default_currency: str = Field(default="USD", description="Default currency")
    allow_options_trading: bool = Field(default=True, description="Allow options trading")
    allow_short_selling: bool = Field(default=False, description="Allow short selling")
    max_position_size: int = Field(default=1000, description="Maximum position size")
    default_position_size: int = Field(default=100, description="Default position size")
    risk_level: str = Field(default="conservative", description="Risk level")
    
    # Notification settings
    notifications: Optional[NotificationConfig] = None
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language setting"""
        allowed_languages = ["en_US", "zh_CN", "zh_TW"]
        if v not in allowed_languages:
            raise ValueError(f"Language must be one of {allowed_languages}")
        return v
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        """Validate risk level"""
        allowed_levels = ["conservative", "moderate", "aggressive"]
        if v not in allowed_levels:
            raise ValueError(f"Risk level must be one of {allowed_levels}")
        return v
    
    @property
    def private_key_file(self) -> Path:
        """Get private key file path"""
        return Path(self.private_key_path).expanduser().resolve()
    
    def is_private_key_valid(self) -> bool:
        """Check if private key file exists and is readable"""
        try:
            return self.private_key_file.exists() and self.private_key_file.is_file()
        except Exception:
            return False


class GlobalSettings(BaseModel):
    """Global settings configuration"""
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    max_reconnect_attempts: int = Field(default=5, description="Maximum reconnect attempts")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    
    # Default order settings
    default_order_type: str = Field(default="limit", description="Default order type")
    default_time_in_force: str = Field(default="day", description="Default time in force")
    
    # Risk management
    global_max_daily_loss: float = Field(default=10000, description="Global max daily loss")
    global_max_position_exposure: float = Field(default=50000, description="Global max position exposure")
    
    # Logging and monitoring
    log_trades: bool = Field(default=True, description="Whether to log trades")
    log_level: str = Field(default="INFO", description="Log level")
    
    @validator('default_order_type')
    def validate_order_type(cls, v):
        """Validate order type"""
        allowed_types = ["limit", "market", "stop", "stop_limit"]
        if v not in allowed_types:
            raise ValueError(f"Order type must be one of {allowed_types}")
        return v
    
    @validator('default_time_in_force')
    def validate_time_in_force(cls, v):
        """Validate time in force"""
        allowed_values = ["day", "gtc", "ioc", "fok"]
        if v not in allowed_values:
            raise ValueError(f"Time in force must be one of {allowed_values}")
        return v


class ApiKeysConfig(BaseModel):
    """Complete API keys configuration"""
    accounts: List[AccountConfig] = Field(description="List of account configurations")
    settings: GlobalSettings = Field(default_factory=GlobalSettings, description="Global settings")
    
    @property
    def enabled_accounts(self) -> List[AccountConfig]:
        """Get list of enabled accounts"""
        return [account for account in self.accounts if account.enabled]
    
    def get_account(self, name: str) -> Optional[AccountConfig]:
        """Get account configuration by name"""
        for account in self.accounts:
            if account.name == name:
                return account
        return None
    
    def get_enabled_account(self, name: str) -> Optional[AccountConfig]:
        """Get enabled account configuration by name"""
        account = self.get_account(name)
        return account if account and account.enabled else None
    
    @property
    def account_names(self) -> List[str]:
        """Get list of all account names"""
        return [account.name for account in self.accounts]
    
    @property
    def enabled_account_names(self) -> List[str]:
        """Get list of enabled account names"""
        return [account.name for account in self.enabled_accounts]


class ApiKeysLoader:
    """API keys configuration loader"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize loader with optional config file path"""
        self.config_file = Path(config_file) if config_file else get_config_dir() / "apikeys.yml"
    
    def load(self) -> ApiKeysConfig:
        """Load API keys configuration from YAML file"""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"API keys configuration file not found: {self.config_file}\n"
                f"Please copy {get_config_dir() / 'apikeys.example.yml'} to {self.config_file} "
                f"and fill in your API credentials."
            )
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                raise ValueError("Configuration file is empty")
            
            return ApiKeysConfig(**data)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")
    
    def validate_config(self, config: ApiKeysConfig) -> List[str]:
        """Validate configuration and return list of warnings/errors"""
        warnings = []
        
        if not config.enabled_accounts:
            warnings.append("No enabled accounts found in configuration")
        
        for account in config.accounts:
            if account.enabled and not account.is_private_key_valid():
                warnings.append(f"Private key file not found for account '{account.name}': {account.private_key_path}")
        
        return warnings


# Global API keys configuration
_api_keys_config: Optional[ApiKeysConfig] = None


def load_api_keys_config(config_file: Optional[str] = None) -> ApiKeysConfig:
    """Load and cache API keys configuration"""
    global _api_keys_config
    
    if _api_keys_config is None:
        loader = ApiKeysLoader(config_file)
        _api_keys_config = loader.load()
        
        # Validate configuration
        warnings = loader.validate_config(_api_keys_config)
        if warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(warning)
    
    return _api_keys_config


def get_api_keys_config() -> ApiKeysConfig:
    """Get cached API keys configuration"""
    if _api_keys_config is None:
        return load_api_keys_config()
    return _api_keys_config


def reload_api_keys_config(config_file: Optional[str] = None) -> ApiKeysConfig:
    """Reload API keys configuration from file"""
    global _api_keys_config
    _api_keys_config = None
    return load_api_keys_config(config_file)
