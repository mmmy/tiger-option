"""
Data models package for Tiger Options Trading Service
"""

# Webhook models
from .webhook import (
    WebhookSignalPayload,
    WebhookResponse,
    WebhookOrderData,
    WebhookSignal,
    TradeSignal,
    SignalValidationResult,
)

# Tiger API models
from .tiger import (
    Market,
    Currency,
    OrderType,
    OrderSide,
    OrderStatus,
    TimeInForce,
    OptionType,
    TigerAccount,
    OptionContract,
    TigerOrder,
    Position,
    TradingSignal,
)

# Common models
from .common import (
    ApiResponse,
    HealthStatus,
    ServiceStatus,
    ErrorDetail,
    PaginationParams,
    PaginatedResponse,
    MetricsData,
    ConfigValidationResult,
)

# Database models
from .database import (
    TradeRecord,
    PositionRecord,
    OrderRecord,
    SignalRecord,
)

__all__ = [
    # Webhook models
    "WebhookSignalPayload",
    "WebhookResponse",
    "WebhookOrderData",

    # Tiger API models
    "Market",
    "Currency",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "TimeInForce",
    "OptionType",
    "TigerAccount",
    "OptionContract",
    "TigerOrder",
    "Position",
    "TradingSignal",

    # Common models
    "ApiResponse",
    "HealthStatus",
    "ServiceStatus",
    "ErrorDetail",
    "PaginationParams",
    "PaginatedResponse",
    "MetricsData",
    "ConfigValidationResult",

    # Database models
    "TradeRecord",
    "PositionRecord",
    "OrderRecord",
    "SignalRecord",
]
