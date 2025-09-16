"""
Common data models and utilities
"""

from datetime import datetime
from typing import Optional, Generic, TypeVar, List, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


T = TypeVar('T')


class ApiResponse(GenericModel, Generic[T]):
    """Generic API response wrapper"""
    
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthStatus(BaseModel):
    """Health check status"""
    
    status: str = Field(description="Overall status")
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    
    # Component statuses
    database: Optional[str] = Field(default=None, description="Database status")
    tiger_api: Optional[str] = Field(default=None, description="Tiger API status")
    
    # System metrics
    uptime: Optional[float] = Field(default=None, description="Uptime in seconds")
    memory_usage: Optional[float] = Field(default=None, description="Memory usage percentage")
    cpu_usage: Optional[float] = Field(default=None, description="CPU usage percentage")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ServiceStatus(BaseModel):
    """Service status information"""
    
    service_name: str = Field(description="Service name")
    version: str = Field(description="Service version")
    environment: str = Field(description="Environment (dev/test/prod)")
    started_at: datetime = Field(description="Service start time")
    
    # Configuration status
    mock_mode: bool = Field(description="Whether mock mode is enabled")
    test_environment: bool = Field(description="Whether test environment is used")
    
    # Account status
    total_accounts: int = Field(description="Total number of configured accounts")
    enabled_accounts: int = Field(description="Number of enabled accounts")
    account_names: List[str] = Field(description="List of account names")
    
    # System metrics
    uptime_seconds: float = Field(description="Uptime in seconds")
    memory_usage_mb: Optional[float] = Field(default=None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(default=None, description="CPU usage percentage")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """Error detail information"""
    
    error_code: str = Field(description="Error code")
    error_message: str = Field(description="Error message")
    error_type: str = Field(description="Error type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    # Context information
    request_id: Optional[str] = Field(default=None, description="Request ID")
    account_name: Optional[str] = Field(default=None, description="Account name")
    symbol: Optional[str] = Field(default=None, description="Symbol")
    
    # Stack trace (for debugging)
    stack_trace: Optional[str] = Field(default=None, description="Stack trace")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationParams(BaseModel):
    """Pagination parameters"""
    
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size


class PaginatedResponse(GenericModel, Generic[T]):
    """Paginated response wrapper"""
    
    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Page size")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> 'PaginatedResponse[T]':
        """Create paginated response"""
        total_pages = (total + page_size - 1) // page_size
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class MetricsData(BaseModel):
    """System metrics data"""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    
    # System metrics
    cpu_usage_percent: float = Field(description="CPU usage percentage")
    memory_usage_mb: float = Field(description="Memory usage in MB")
    memory_usage_percent: float = Field(description="Memory usage percentage")
    disk_usage_percent: float = Field(description="Disk usage percentage")
    
    # Application metrics
    active_connections: int = Field(description="Number of active connections")
    total_requests: int = Field(description="Total number of requests")
    successful_requests: int = Field(description="Number of successful requests")
    failed_requests: int = Field(description="Number of failed requests")
    
    # Trading metrics
    total_orders: int = Field(description="Total number of orders")
    successful_orders: int = Field(description="Number of successful orders")
    failed_orders: int = Field(description="Number of failed orders")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigValidationResult(BaseModel):
    """Configuration validation result"""
    
    is_valid: bool = Field(description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="List of errors")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    
    # Configuration details
    total_accounts: int = Field(description="Total number of accounts")
    enabled_accounts: int = Field(description="Number of enabled accounts")
    valid_accounts: int = Field(description="Number of valid accounts")
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
