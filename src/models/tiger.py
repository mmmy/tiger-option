"""
Tiger Brokers API data models
"""

from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator


class Market(str, Enum):
    """Market enumeration"""
    US = "US"
    HK = "HK"
    CN = "CN"
    SG = "SG"


class Currency(str, Enum):
    """Currency enumeration"""
    USD = "USD"
    HKD = "HKD"
    CNY = "CNY"
    SGD = "SGD"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIAL_FILLED = "partial_filled"


class TimeInForce(str, Enum):
    """Time in force enumeration"""
    DAY = "day"
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill


class OptionType(str, Enum):
    """Option type enumeration"""
    CALL = "call"
    PUT = "put"


class TigerAccount(BaseModel):
    """Tiger account information"""
    
    account: str = Field(description="Account number")
    currency: Currency = Field(description="Account currency")
    buying_power: Decimal = Field(description="Buying power")
    cash: Decimal = Field(description="Cash balance")
    market_value: Decimal = Field(description="Market value")
    net_liquidation: Decimal = Field(description="Net liquidation value")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class OptionContract(BaseModel):
    """Option contract information"""
    
    symbol: str = Field(description="Option symbol")
    underlying_symbol: str = Field(description="Underlying symbol")
    strike: Decimal = Field(description="Strike price")
    expiry: datetime = Field(description="Expiry date")
    option_type: OptionType = Field(description="Option type (call/put)")
    multiplier: int = Field(default=100, description="Contract multiplier")
    
    # Market data
    bid: Optional[Decimal] = Field(default=None, description="Bid price")
    ask: Optional[Decimal] = Field(default=None, description="Ask price")
    last: Optional[Decimal] = Field(default=None, description="Last price")
    volume: Optional[int] = Field(default=None, description="Volume")
    open_interest: Optional[int] = Field(default=None, description="Open interest")
    
    # Greeks
    delta: Optional[Decimal] = Field(default=None, description="Delta")
    gamma: Optional[Decimal] = Field(default=None, description="Gamma")
    theta: Optional[Decimal] = Field(default=None, description="Theta")
    vega: Optional[Decimal] = Field(default=None, description="Vega")
    implied_volatility: Optional[Decimal] = Field(default=None, description="Implied volatility")
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate mid price from bid/ask"""
        if self.bid is not None and self.ask is not None:
            return (self.bid + self.ask) / 2
        return None
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate bid-ask spread"""
        if self.bid is not None and self.ask is not None:
            return self.ask - self.bid
        return None
    
    @property
    def is_call(self) -> bool:
        """Check if this is a call option"""
        return self.option_type == OptionType.CALL
    
    @property
    def is_put(self) -> bool:
        """Check if this is a put option"""
        return self.option_type == OptionType.PUT
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class TigerOrder(BaseModel):
    """Tiger order information"""
    
    order_id: str = Field(description="Order ID")
    account: str = Field(description="Account number")
    symbol: str = Field(description="Symbol")
    order_type: OrderType = Field(description="Order type")
    side: OrderSide = Field(description="Order side")
    quantity: Decimal = Field(description="Order quantity")
    price: Optional[Decimal] = Field(default=None, description="Order price")
    stop_price: Optional[Decimal] = Field(default=None, description="Stop price")
    time_in_force: TimeInForce = Field(description="Time in force")
    status: OrderStatus = Field(description="Order status")
    
    # Execution information
    filled_quantity: Decimal = Field(default=Decimal('0'), description="Filled quantity")
    avg_fill_price: Optional[Decimal] = Field(default=None, description="Average fill price")
    
    # Timestamps
    created_at: datetime = Field(description="Order creation time")
    updated_at: Optional[datetime] = Field(default=None, description="Last update time")
    
    # Additional information
    commission: Optional[Decimal] = Field(default=None, description="Commission")
    currency: Currency = Field(description="Currency")
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity"""
        return self.quantity - self.filled_quantity
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_active(self) -> bool:
        """Check if order is active (not filled, cancelled, or rejected)"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED]
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class Position(BaseModel):
    """Position information"""
    
    account: str = Field(description="Account number")
    symbol: str = Field(description="Symbol")
    quantity: Decimal = Field(description="Position quantity")
    avg_cost: Decimal = Field(description="Average cost")
    market_price: Optional[Decimal] = Field(default=None, description="Current market price")
    market_value: Optional[Decimal] = Field(default=None, description="Current market value")
    unrealized_pnl: Optional[Decimal] = Field(default=None, description="Unrealized P&L")
    realized_pnl: Optional[Decimal] = Field(default=None, description="Realized P&L")
    
    # Position metadata
    currency: Currency = Field(description="Currency")
    multiplier: int = Field(default=1, description="Contract multiplier")
    
    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.quantity < 0
    
    @property
    def is_flat(self) -> bool:
        """Check if position is flat"""
        return self.quantity == 0
    
    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value"""
        return abs(self.quantity) * self.avg_cost * self.multiplier
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class TradingSignal(BaseModel):
    """Processed trading signal"""
    
    # Original webhook data
    webhook_payload: Dict[str, Any] = Field(description="Original webhook payload")
    
    # Processed signal information
    account_name: str = Field(description="Account name")
    symbol: str = Field(description="Underlying symbol")
    action: Literal["open", "close", "reverse"] = Field(description="Trading action")
    side: OrderSide = Field(description="Order side")
    quantity: Decimal = Field(description="Order quantity")
    
    # Option selection criteria
    option_type: Optional[OptionType] = Field(default=None, description="Option type")
    strike_selection: Optional[str] = Field(default=None, description="Strike selection method")
    expiry_selection: Optional[str] = Field(default=None, description="Expiry selection method")
    
    # Risk management
    max_loss: Optional[Decimal] = Field(default=None, description="Maximum loss")
    max_position_size: Optional[Decimal] = Field(default=None, description="Maximum position size")
    
    # Metadata
    signal_id: str = Field(description="Unique signal ID")
    received_at: datetime = Field(default_factory=datetime.utcnow, description="Signal received time")
    processed_at: Optional[datetime] = Field(default=None, description="Signal processed time")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }
