"""
API routes for Tiger Options Trading Service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional, Any

from ..models import (
    ApiResponse,
    HealthStatus,
    ServiceStatus,
    ConfigValidationResult,
    TigerAccount,
    Position,
)
from ..services import get_auth_service, AuthService
from ..config import get_settings


# Create main router
router = APIRouter()

# Health check router
health_router = APIRouter(prefix="/health", tags=["health"])

# System router
system_router = APIRouter(prefix="/api", tags=["system"])

# Account router
account_router = APIRouter(prefix="/api/accounts", tags=["accounts"])

# Trading router
trading_router = APIRouter(prefix="/api/trading", tags=["trading"])


# Health Check Endpoints

@health_router.get("", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    settings = get_settings()
    
    # Basic health status
    health_status = HealthStatus(
        status="healthy",
        service="tiger-options-trading",
        version="1.0.0"
    )
    
    # Check database status (placeholder)
    health_status.database = "healthy"
    
    # Check Tiger API status
    try:
        auth_service = get_auth_service()
        enabled_accounts = auth_service.get_enabled_account_names()
        
        if enabled_accounts:
            # Test one account connection
            first_account = enabled_accounts[0]
            connection_ok = auth_service.test_connection(first_account)
            health_status.tiger_api = "healthy" if connection_ok else "unhealthy"
        else:
            health_status.tiger_api = "no_accounts"
    except Exception:
        health_status.tiger_api = "error"
    
    return health_status


# System Endpoints

@system_router.get("/status", response_model=ServiceStatus)
async def get_service_status():
    """Get service status information"""
    settings = get_settings()
    auth_service = get_auth_service()
    
    # Get account summary
    account_summary = auth_service.get_account_summary()
    
    return ServiceStatus(
        service_name="tiger-options-trading",
        version="1.0.0",
        environment="development" if settings.is_development else "production",
        started_at=datetime.now(),  # Would be actual start time in real implementation
        mock_mode=settings.use_mock_mode,
        test_environment=settings.use_test_environment,
        total_accounts=account_summary["total_accounts"],
        enabled_accounts=account_summary["enabled_accounts"],
        account_names=account_summary["account_names"],
        uptime_seconds=0.0,  # Would be calculated in real implementation
    )


@system_router.get("/config/validate", response_model=ApiResponse[ConfigValidationResult])
async def validate_configuration():
    """Validate current configuration"""
    try:
        auth_service = get_auth_service()
        validation_result = auth_service.reload_configuration()
        
        return ApiResponse(
            success=validation_result.is_valid,
            message="Configuration validation completed",
            data=validation_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration validation failed: {str(e)}"
        )


@system_router.post("/config/reload", response_model=ApiResponse[ConfigValidationResult])
async def reload_configuration():
    """Reload configuration from files"""
    try:
        auth_service = get_auth_service()
        validation_result = auth_service.reload_configuration()
        
        return ApiResponse(
            success=True,
            message="Configuration reloaded successfully",
            data=validation_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration reload failed: {str(e)}"
        )


# Account Endpoints

@account_router.get("", response_model=ApiResponse[List[str]])
async def list_accounts():
    """List all account names"""
    auth_service = get_auth_service()
    account_names = auth_service.get_enabled_account_names()
    
    return ApiResponse(
        success=True,
        message=f"Found {len(account_names)} enabled accounts",
        data=account_names
    )


@account_router.get("/{account_name}/info", response_model=ApiResponse[TigerAccount])
async def get_account_info(account_name: str):
    """Get account information"""
    auth_service = get_auth_service()
    
    # Validate account
    if not auth_service.is_account_valid(account_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found or disabled: {account_name}"
        )
    
    # Get client and account info
    client = auth_service.get_client(account_name)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client for account: {account_name}"
        )
    
    account_info = client.get_account_info()
    if not account_info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account information for: {account_name}"
        )
    
    return ApiResponse(
        success=True,
        message="Account information retrieved successfully",
        data=account_info
    )


@account_router.get("/{account_name}/test-connection", response_model=ApiResponse[Dict[str, Any]])
async def test_account_connection(account_name: str):
    """Test connection to Tiger API for the account"""

    try:
        auth_service = get_auth_service()

        # Validate account
        if not auth_service.is_account_valid(account_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found or disabled: {account_name}"
            )

        # Get client and test connection
        client = auth_service.get_client(account_name)
        if not client:
            return ApiResponse(
                success=False,
                message="Connection test failed - unable to create client",
                data={
                    "account_name": account_name,
                    "connection_status": "failed",
                    "test_timestamp": datetime.now().isoformat()
                }
            )

        # Test connection by getting account info
        account_info = client.get_account_info()
        connection_ok = account_info is not None

        return ApiResponse(
            success=connection_ok,
            message="Connection test successful" if connection_ok else "Connection test failed",
            data={
                "account_name": account_name,
                "connection_status": "connected" if connection_ok else "disconnected",
                "test_timestamp": datetime.now().isoformat(),
                "account_info_available": account_info is not None
            }
        )

    except Exception as e:
        logger.error(f"Connection test failed for {account_name}: {e}")
        return ApiResponse(
            success=False,
            message="Connection test failed",
            data={
                "account_name": account_name,
                "connection_status": "error",
                "error": str(e),
                "test_timestamp": datetime.now().isoformat()
            }
        )


@account_router.get("/{account_name}/positions", response_model=ApiResponse[List[Position]])
async def get_account_positions(account_name: str):
    """Get account positions"""
    auth_service = get_auth_service()
    
    # Validate account
    if not auth_service.is_account_valid(account_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found or disabled: {account_name}"
        )
    
    # Get client and positions
    client = auth_service.get_client(account_name)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client for account: {account_name}"
        )
    
    positions = client.get_positions()
    
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(positions)} positions",
        data=positions
    )


@account_router.post("/{account_name}/test", response_model=ApiResponse[bool])
async def test_account_connection(account_name: str):
    """Test account connection"""
    auth_service = get_auth_service()
    
    # Validate account
    if not auth_service.is_account_valid(account_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found or disabled: {account_name}"
        )
    
    # Test connection
    connection_ok = auth_service.test_connection(account_name)
    
    return ApiResponse(
        success=connection_ok,
        message="Connection test successful" if connection_ok else "Connection test failed",
        data=connection_ok
    )


# Trading Endpoints

@trading_router.get("/status", response_model=ApiResponse[Dict[str, bool]])
async def get_trading_status():
    """Get trading status for all accounts"""
    auth_service = get_auth_service()
    connection_status = auth_service.test_all_connections()
    
    return ApiResponse(
        success=True,
        message="Trading status retrieved",
        data=connection_status
    )


# Import webhook routes
from .webhook_routes import webhook_router

# Import market data routes
from .market_routes import market_router

# Import trading routes
from .trading_routes import trading_router as api_trading_router

# Import account management routes
from .account_routes import router as account_management_router

# Add API-level health check
@router.get("/api/health", response_model=ApiResponse[Dict[str, Any]])
async def api_health_check():
    """API-level health check"""

    auth_service = get_auth_service()
    enabled_accounts = auth_service.get_enabled_account_names()

    # Test account connections
    connection_status = {}
    for account_name in enabled_accounts:
        try:
            client = auth_service.get_client(account_name)
            connection_status[account_name] = client is not None
        except Exception:
            connection_status[account_name] = False

    return ApiResponse(
        success=True,
        message="API service is healthy",
        data={
            "service": "api",
            "status": "healthy",
            "enabled_accounts": len(enabled_accounts),
            "account_names": enabled_accounts,
            "connection_status": connection_status,
            "timestamp": datetime.now().isoformat()
        }
    )


# Include all routers in main router
router.include_router(health_router)
router.include_router(system_router)
router.include_router(account_router)
router.include_router(trading_router)
router.include_router(webhook_router)
router.include_router(market_router)
router.include_router(api_trading_router)
router.include_router(account_management_router)


# Add missing import
from datetime import datetime
