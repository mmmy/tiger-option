"""
Webhook data models for TradingView signals
"""

from datetime import datetime
from typing import Optional, Literal, Dict, Any, List
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class WebhookSignalPayload(BaseModel):
    """TradingView webhook signal payload"""
    
    # Account and trading information
    account_name: str = Field(
        alias="accountName",
        description="Account name, corresponds to the name in apikeys configuration"
    )
    side: Literal["buy", "sell"] = Field(description="Trading direction: buy/sell")
    exchange: str = Field(description="Exchange name")
    period: str = Field(description="K-line period")
    
    # Market position information
    market_position: Literal["long", "short", "flat"] = Field(
        alias="marketPosition",
        description="Current market position"
    )
    prev_market_position: Literal["long", "short", "flat"] = Field(
        alias="prevMarketPosition", 
        description="Previous market position"
    )
    
    # Trading details
    symbol: str = Field(description="Trading pair symbol")
    price: str = Field(description="Current price")
    timestamp: str = Field(description="Timestamp")
    size: str = Field(description="Order quantity/contracts")
    position_size: str = Field(
        alias="positionSize",
        description="Current position size"
    )
    
    # Order identification
    id: str = Field(description="Strategy order ID")
    alert_message: Optional[str] = Field(
        default=None,
        alias="alertMessage",
        description="Alert message"
    )
    comment: Optional[str] = Field(default=None, description="Comment")
    
    # Quantity type
    qty_type: Literal["fixed", "cash"] = Field(
        alias="qtyType",
        description="Quantity type"
    )

    # TradingView specific fields
    tv_id: Optional[int] = Field(default=None, description="TradingView signal ID")

    # Optional delta fields for options trading
    delta1: Optional[float] = Field(default=None, description="Option Delta value for opening positions")
    n: Optional[int] = Field(default=None, description="Minimum expiry days for option selection")
    delta2: Optional[float] = Field(default=None, description="Target Delta value for recording to delta database")
    
    @validator('price', 'size', 'position_size')
    def validate_numeric_strings(cls, v):
        """Validate that numeric strings can be converted to Decimal"""
        try:
            Decimal(v)
            return v
        except Exception:
            raise ValueError(f"Invalid numeric value: {v}")
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate timestamp format"""
        try:
            # Try to parse as ISO format or Unix timestamp
            if v.isdigit():
                datetime.fromtimestamp(int(v))
            else:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except Exception:
            raise ValueError(f"Invalid timestamp format: {v}")
    
    @property
    def price_decimal(self) -> Decimal:
        """Get price as Decimal"""
        return Decimal(self.price)
    
    @property
    def size_decimal(self) -> Decimal:
        """Get size as Decimal"""
        return Decimal(self.size)
    
    @property
    def position_size_decimal(self) -> Decimal:
        """Get position size as Decimal"""
        return Decimal(self.position_size)
    
    @property
    def timestamp_datetime(self) -> datetime:
        """Get timestamp as datetime"""
        if self.timestamp.isdigit():
            return datetime.fromtimestamp(int(self.timestamp))
        else:
            return datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
    
    @property
    def is_opening_position(self) -> bool:
        """Check if this signal is opening a new position"""
        return self.prev_market_position == "flat" and self.market_position != "flat"
    
    @property
    def is_closing_position(self) -> bool:
        """Check if this signal is closing a position"""
        return self.prev_market_position != "flat" and self.market_position == "flat"
    
    @property
    def is_reversing_position(self) -> bool:
        """Check if this signal is reversing position"""
        return (
            self.prev_market_position != "flat" and 
            self.market_position != "flat" and 
            self.prev_market_position != self.market_position
        )


class WebhookResponse(BaseModel):
    """Webhook response format"""
    
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Response message")
    
    # Optional data for successful operations
    data: Optional[dict] = Field(default=None, description="Response data")
    
    # Optional error information
    error: Optional[str] = Field(default=None, description="Error message")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookOrderData(BaseModel):
    """Order data included in successful webhook responses"""
    
    order_id: Optional[str] = Field(default=None, description="Order ID")
    instrument_name: Optional[str] = Field(default=None, description="Instrument name")
    executed_quantity: Optional[Decimal] = Field(default=None, description="Executed quantity")
    executed_price: Optional[Decimal] = Field(default=None, description="Executed price")
    order_status: Optional[str] = Field(default=None, description="Order status")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


# Additional models for simplified webhook interface

class WebhookSignal(BaseModel):
    """Simplified webhook signal model for general use"""

    signal_id: Optional[str] = Field(default=None, description="Signal ID")
    symbol: str = Field(description="Trading symbol")
    action: str = Field(description="Trading action: buy, sell, close, close_all")
    quantity: Optional[Decimal] = Field(default=None, description="Order quantity")
    price: Optional[Decimal] = Field(default=None, description="Order price")
    stop_price: Optional[Decimal] = Field(default=None, description="Stop price")
    order_type: Optional[str] = Field(default="market", description="Order type")
    time_in_force: Optional[str] = Field(default="day", description="Time in force")
    strategy: Optional[str] = Field(default=None, description="Strategy name")
    comment: Optional[str] = Field(default=None, description="Comment")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @validator('action')
    def validate_action(cls, v):
        """Validate action field"""
        valid_actions = ["buy", "sell", "close", "close_all"]
        if v.lower() not in valid_actions:
            raise ValueError(f"Invalid action: {v}. Must be one of: {valid_actions}")
        return v.lower()

    @validator('order_type')
    def validate_order_type(cls, v):
        """Validate order type field"""
        if v is None:
            return "market"
        valid_types = ["market", "limit", "stop", "stop_limit"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid order type: {v}. Must be one of: {valid_types}")
        return v.lower()


class TradeSignal(BaseModel):
    """Internal trade signal after processing webhook"""
    signal_id: str
    account_name: str
    symbol: str
    action: str  # buy, sell, close, close_all
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    order_type: str = "market"  # market, limit, stop, stop_limit
    time_in_force: str = "day"  # day, gtc, ioc, fok
    strategy: Optional[str] = None
    comment: Optional[str] = None
    received_at: datetime
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SignalValidationResult(BaseModel):
    """Result of signal validation"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    signal_id: Optional[str] = None
    symbol: Optional[str] = None
    action: Optional[str] = None

    @property
    def has_errors(self) -> bool:
        """Check if validation has errors"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return len(self.warnings) > 0
