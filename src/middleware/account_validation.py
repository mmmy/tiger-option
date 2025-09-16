"""
Account validation middleware and dependencies
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services import get_auth_service, AuthService
from ..config import AccountConfig


logger = logging.getLogger(__name__)

# Optional security scheme for API key authentication
security = HTTPBearer(auto_error=False)


class AccountValidator:
    """Account validation utilities"""
    
    @staticmethod
    def validate_account_name(account_name: str, auth_service: AuthService) -> AccountConfig:
        """Validate account name and return account configuration"""
        
        # Check if account exists
        account_config = auth_service.get_account_config(account_name)
        if not account_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found: {account_name}"
            )
        
        # Check if account is enabled
        if not account_config.enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is disabled: {account_name}"
            )
        
        # Check if account configuration is valid
        if not auth_service.is_account_valid(account_name):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Account configuration is invalid: {account_name}"
            )
        
        return account_config
    
    @staticmethod
    def validate_account_access(
        account_name: str, 
        auth_service: AuthService,
        required_permissions: Optional[list] = None
    ) -> AccountConfig:
        """Validate account access with optional permission checks"""
        
        # Basic account validation
        account_config = AccountValidator.validate_account_name(account_name, auth_service)
        
        # Additional permission checks could be added here
        # For now, we just check if the account is accessible
        
        return account_config


# FastAPI Dependencies

def get_auth_service_dependency() -> AuthService:
    """Dependency to get authentication service"""
    return get_auth_service()


def validate_account_dependency(
    account_name: str,
    auth_service: AuthService = Depends(get_auth_service_dependency)
) -> AccountConfig:
    """FastAPI dependency to validate account name"""
    return AccountValidator.validate_account_name(account_name, auth_service)


def validate_account_access_dependency(
    account_name: str,
    auth_service: AuthService = Depends(get_auth_service_dependency)
) -> AccountConfig:
    """FastAPI dependency to validate account access"""
    return AccountValidator.validate_account_access(account_name, auth_service)


def get_optional_auth_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Get optional authentication token from request"""
    if credentials:
        return credentials.credentials
    return None


def require_auth_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Require authentication token from request"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def validate_webhook_request(request: Request) -> dict:
    """Validate webhook request and extract data"""
    
    # Check content type
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content-Type must be application/json"
        )
    
    # Additional webhook validation could be added here
    # For example, signature validation, rate limiting, etc.
    
    return {"validated": True}


class WebhookValidator:
    """Webhook request validation utilities"""
    
    @staticmethod
    def validate_webhook_signature(
        request: Request,
        payload: bytes,
        signature: Optional[str] = None,
        secret: Optional[str] = None
    ) -> bool:
        """Validate webhook signature (placeholder implementation)"""
        
        # This is a placeholder for webhook signature validation
        # In a real implementation, you would:
        # 1. Extract signature from headers
        # 2. Calculate expected signature using HMAC
        # 3. Compare signatures securely
        
        if not secret:
            # If no secret is configured, skip validation
            logger.warning("Webhook signature validation skipped - no secret configured")
            return True
        
        if not signature:
            logger.warning("Webhook signature validation failed - no signature provided")
            return False
        
        # Placeholder validation - always returns True
        # TODO: Implement proper HMAC signature validation
        logger.info("Webhook signature validation passed (placeholder)")
        return True
    
    @staticmethod
    def validate_webhook_source(request: Request) -> bool:
        """Validate webhook source IP or other identifiers"""
        
        # This is a placeholder for webhook source validation
        # In a real implementation, you might:
        # 1. Check source IP against allowlist
        # 2. Validate user agent
        # 3. Check for specific headers
        
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        logger.info(f"Webhook request from IP: {client_ip}, User-Agent: {user_agent}")
        
        # For now, allow all sources
        return True
    
    @staticmethod
    def validate_rate_limit(request: Request, account_name: str) -> bool:
        """Validate rate limiting for webhook requests"""
        
        # This is a placeholder for rate limiting
        # In a real implementation, you would:
        # 1. Track request counts per account/IP
        # 2. Implement sliding window or token bucket
        # 3. Return False if rate limit exceeded
        
        logger.debug(f"Rate limit check for account: {account_name}")
        
        # For now, no rate limiting
        return True


def validate_webhook_security(
    request: Request,
    account_name: str,
    payload: bytes = b"",
    auth_service: AuthService = Depends(get_auth_service_dependency)
) -> dict:
    """Comprehensive webhook security validation"""
    
    validator = WebhookValidator()
    
    # Validate account
    account_config = AccountValidator.validate_account_name(account_name, auth_service)
    
    # Validate webhook source
    if not validator.validate_webhook_source(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook source not allowed"
        )
    
    # Validate rate limiting
    if not validator.validate_rate_limit(request, account_name):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Validate signature if configured
    signature = request.headers.get("x-signature") or request.headers.get("x-hub-signature-256")
    webhook_secret = getattr(account_config, 'webhook_secret', None)
    
    if not validator.validate_webhook_signature(request, payload, signature, webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    return {
        "account_config": account_config,
        "validated": True,
        "source_ip": request.client.host if request.client else "unknown"
    }
