"""
Tiger Options Trading Service
Main entry point for the FastAPI application
"""

import logging
import uvicorn
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse

from .config import get_settings, ensure_directories
from .services import initialize_auth_service
from .api.routes import router
from .middleware import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Tiger Options Trading Service...")

    # Ensure required directories exist
    ensure_directories()

    # Initialize authentication service
    try:
        validation_result = initialize_auth_service()
        if validation_result.has_errors:
            logger.error("Configuration validation failed:")
            for error in validation_result.errors:
                logger.error(f"  - {error}")
        else:
            logger.info(f"Configuration loaded: {validation_result.enabled_accounts} enabled accounts")

        if validation_result.has_warnings:
            logger.warning("Configuration warnings:")
            for warning in validation_result.warnings:
                logger.warning(f"  - {warning}")

    except Exception as e:
        logger.error(f"Failed to initialize authentication service: {e}")

    logger.info("Tiger Options Trading Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Tiger Options Trading Service...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title="Tiger Options Trading Service",
        description="A microservice for Tiger Brokers options trading via TradingView webhooks",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )

    # Add middleware (order matters - last added is executed first)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)

    # Include API routes
    app.include_router(router)

    # Mount static files
    app.mount("/static", StaticFiles(directory="public"), name="static")

    # Add exception handler for webhook validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        """Handle validation errors for webhook endpoints"""
        if request.url.path == "/webhook/signal":
            # Return deribit-style error response for webhook endpoint
            return JSONResponse(
                status_code=200,  # Return 200 like deribit_webhook
                content={
                    "success": False,
                    "message": "Invalid request body",
                    "error": f"Validation failed: {str(exc)}",
                    "request_id": f"req_{int(datetime.now().timestamp() * 1000)}",
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            # Default FastAPI validation error response for other endpoints
            return JSONResponse(
                status_code=422,
                content={"detail": exc.errors()}
            )

    # Root endpoint - serve homepage
    @app.get("/")
    async def root():
        """Root endpoint - serve homepage"""
        return FileResponse("public/index.html")

    # API info endpoint
    @app.get("/api")
    async def api_info():
        """API information endpoint"""
        return {
            "message": "Tiger Options Trading Service",
            "version": "1.0.0",
            "docs": "/docs" if settings.debug else "disabled",
            "environment": "development" if settings.is_development else "production",
            "mock_mode": settings.use_mock_mode
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
