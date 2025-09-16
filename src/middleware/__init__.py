"""
Middleware package for Tiger Options Trading Service
"""

# Error handling middleware
from .error_handler import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    CORSMiddleware,
    SecurityHeadersMiddleware,
)

# Account validation middleware and dependencies
from .account_validation import (
    AccountValidator,
    WebhookValidator,
    get_auth_service_dependency,
    validate_account_dependency,
    validate_account_access_dependency,
    get_optional_auth_token,
    require_auth_token,
    validate_webhook_request,
    validate_webhook_security,
)

__all__ = [
    # Error handling
    "ErrorHandlerMiddleware",
    "RequestLoggingMiddleware",
    "CORSMiddleware",
    "SecurityHeadersMiddleware",

    # Account validation
    "AccountValidator",
    "WebhookValidator",
    "get_auth_service_dependency",
    "validate_account_dependency",
    "validate_account_access_dependency",
    "get_optional_auth_token",
    "require_auth_token",
    "validate_webhook_request",
    "validate_webhook_security",
]
