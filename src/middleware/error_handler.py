"""
Global error handling middleware
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Union

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..models import ApiResponse, ErrorDetail
from ..services import AuthenticationError, TigerClientError


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Handle requests and catch exceptions"""
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI HTTP exceptions - let them pass through
            raise e
            
        except AuthenticationError as e:
            logger.error(f"Authentication error [{request_id}]: {e}")
            return self._create_error_response(
                request_id=request_id,
                error_code="AUTH_ERROR",
                error_message=str(e),
                error_type="AuthenticationError",
                status_code=401
            )
            
        except TigerClientError as e:
            logger.error(f"Tiger client error [{request_id}]: {e}")
            return self._create_error_response(
                request_id=request_id,
                error_code="TIGER_CLIENT_ERROR",
                error_message=str(e),
                error_type="TigerClientError",
                status_code=502
            )
            
        except ValueError as e:
            logger.error(f"Validation error [{request_id}]: {e}")
            return self._create_error_response(
                request_id=request_id,
                error_code="VALIDATION_ERROR",
                error_message=str(e),
                error_type="ValueError",
                status_code=400
            )
            
        except FileNotFoundError as e:
            logger.error(f"File not found error [{request_id}]: {e}")
            return self._create_error_response(
                request_id=request_id,
                error_code="FILE_NOT_FOUND",
                error_message=str(e),
                error_type="FileNotFoundError",
                status_code=404
            )
            
        except PermissionError as e:
            logger.error(f"Permission error [{request_id}]: {e}")
            return self._create_error_response(
                request_id=request_id,
                error_code="PERMISSION_ERROR",
                error_message=str(e),
                error_type="PermissionError",
                status_code=403
            )
            
        except Exception as e:
            # Log the full traceback for unexpected errors
            logger.error(f"Unexpected error [{request_id}]: {e}")
            logger.error(f"Traceback [{request_id}]:\n{traceback.format_exc()}")
            
            return self._create_error_response(
                request_id=request_id,
                error_code="INTERNAL_ERROR",
                error_message="An unexpected error occurred",
                error_type=type(e).__name__,
                status_code=500,
                include_traceback=True
            )
    
    def _create_error_response(
        self,
        request_id: str,
        error_code: str,
        error_message: str,
        error_type: str,
        status_code: int,
        include_traceback: bool = False
    ) -> JSONResponse:
        """Create standardized error response"""
        
        error_detail = ErrorDetail(
            error_code=error_code,
            error_message=error_message,
            error_type=error_type,
            request_id=request_id
        )
        
        if include_traceback:
            error_detail.stack_trace = traceback.format_exc()
        
        response_data = ApiResponse(
            success=False,
            message="Request failed",
            error=error_message,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status_code,
            content=response_data.dict()
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response information"""
        start_time = datetime.now()
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Log request
        logger.info(
            f"Request [{request_id}]: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log response
        logger.info(
            f"Response [{request_id}]: {response.status_code} "
            f"in {duration:.3f}s"
        )
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with configuration support"""
    
    def __init__(self, app, allowed_origins: list = None, allowed_methods: list = None, allowed_headers: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["*"]
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS headers"""
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = self._get_allowed_origin(request)
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            response.headers["Access-Control-Max-Age"] = "86400"
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        response.headers["Access-Control-Allow-Origin"] = self._get_allowed_origin(request)
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    def _get_allowed_origin(self, request: Request) -> str:
        """Get allowed origin for the request"""
        if "*" in self.allowed_origins:
            return "*"
        
        origin = request.headers.get("origin")
        if origin and origin in self.allowed_origins:
            return origin
        
        return self.allowed_origins[0] if self.allowed_origins else "*"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add CSP header for API endpoints
        if request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = "default-src 'none'"
        
        return response
