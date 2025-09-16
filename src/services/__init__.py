"""
Services layer package for Tiger Options Trading Service
"""

# Tiger API clients
from .tiger_client import TigerClient, TigerClientError
from .mock_tiger_client import MockTigerClient
from .tiger_client_factory import (
    TigerClientFactory,
    TigerClientType,
    create_tiger_client,
    get_tiger_client,
    get_tiger_client_by_name,
)

# Authentication service
from .auth_service import (
    AuthService,
    AuthenticationError,
    get_auth_service,
    initialize_auth_service,
)

# Signal validation and processing
from .signal_validator import (
    SignalValidator,
    SignalValidationError,
    get_signal_validator,
)
from .signal_processor import (
    SignalProcessor,
    SignalProcessingError,
    get_signal_processor,
)

# Enhanced trading services
from .enhanced_signal_processor import EnhancedSignalProcessor
from .option_selector import OptionSelector, SelectionStrategy
from .order_strategy import OrderStrategyService, OrderStrategy
from .position_manager import PositionManager
from .risk_manager import RiskManager, RiskCheckResult

__all__ = [
    # Tiger clients
    "TigerClient",
    "TigerClientError",
    "MockTigerClient",
    "TigerClientFactory",
    "TigerClientType",
    "create_tiger_client",
    "get_tiger_client",
    "get_tiger_client_by_name",

    # Authentication
    "AuthService",
    "AuthenticationError",
    "get_auth_service",
    "initialize_auth_service",

    # Signal validation and processing
    "SignalValidator",
    "SignalValidationError",
    "get_signal_validator",
    "SignalProcessor",
    "SignalProcessingError",
    "get_signal_processor",

    # Enhanced trading services
    "EnhancedSignalProcessor",
    "OptionSelector",
    "SelectionStrategy",
    "OrderStrategyService",
    "OrderStrategy",
    "PositionManager",
    "RiskManager",
    "RiskCheckResult",
]
