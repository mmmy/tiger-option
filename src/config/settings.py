"""
Configuration settings for Tiger Options Trading Service
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Server Configuration
    port: int = Field(default=8000, description="Server port")
    host: str = Field(default="0.0.0.0", description="Server host")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # Application Mode
    use_mock_mode: bool = Field(default=True, description="Use mock mode for development")
    use_test_environment: bool = Field(default=True, description="Use test environment")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./data/tiger_options.db",
        description="Database connection URL"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or text")
    log_file: str = Field(default="./logs/tiger_options.log", description="Log file path")
    log_max_size: int = Field(default=10485760, description="Max log file size in bytes")
    log_backup_count: int = Field(default=5, description="Number of log backup files")
    
    # Tiger API Configuration
    tiger_api_timeout: int = Field(default=30, description="Tiger API timeout in seconds")
    tiger_api_retry_count: int = Field(default=3, description="Tiger API retry count")
    tiger_api_retry_delay: int = Field(default=1, description="Tiger API retry delay in seconds")
    
    # Security
    secret_key: str = Field(default="dev-secret-key", description="Application secret key")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins"
    )
    
    # Trading Configuration
    default_order_type: str = Field(default="limit", description="Default order type")
    default_time_in_force: str = Field(default="day", description="Default time in force")
    max_position_size: int = Field(default=1000, description="Maximum position size")
    risk_management_enabled: bool = Field(default=True, description="Enable risk management")
    
    # Webhook Configuration
    webhook_secret: Optional[str] = Field(default=None, description="Webhook secret for validation")
    webhook_timeout: int = Field(default=30, description="Webhook timeout in seconds")
    
    # Monitoring and Alerts
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    alert_webhook_url: Optional[str] = Field(default=None, description="Alert webhook URL")
    
    # Development Settings
    testing: bool = Field(default=False, description="Testing mode")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.debug or self.use_mock_mode
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.is_development and not self.use_test_environment
    
    @property
    def log_file_path(self) -> Path:
        """Get log file path as Path object"""
        return Path(self.log_file)
    
    @property
    def database_path(self) -> Optional[Path]:
        """Get database file path for SQLite databases"""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            return Path(db_path)
        return None


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent


def get_config_dir() -> Path:
    """Get configuration directory"""
    return get_project_root() / "config"


def get_data_dir() -> Path:
    """Get data directory"""
    return get_project_root() / "data"


def get_logs_dir() -> Path:
    """Get logs directory"""
    return get_project_root() / "logs"


def ensure_directories():
    """Ensure required directories exist"""
    directories = [
        get_data_dir(),
        get_logs_dir(),
        settings.log_file_path.parent,
    ]
    
    if settings.database_path:
        directories.append(settings.database_path.parent)
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
