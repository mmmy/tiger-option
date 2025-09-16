"""
Database models for Tiger Options Trading Service
"""

from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field


class TradeRecord(BaseModel):
    """Trade record model"""
    
    # Primary key
    id: Optional[int] = Field(default=None, description="Record ID")
    
    # Trade identification
    trade_id: str = Field(description="Unique trade ID")
    order_id: str = Field(description="Order ID")
    account_name: str = Field(description="Account name")
    
    # Instrument information
    symbol: str = Field(description="Symbol")
    underlying_symbol: Optional[str] = Field(default=None, description="Underlying symbol")
    instrument_type: str = Field(description="Instrument type (stock/option)")
    
    # Trade details
    side: str = Field(description="Trade side (buy/sell)")
    quantity: Decimal = Field(description="Trade quantity")
    price: Decimal = Field(description="Trade price")
    amount: Decimal = Field(description="Trade amount")
    currency: str = Field(description="Currency")
    
    # Option specific fields
    option_type: Optional[str] = Field(default=None, description="Option type (call/put)")
    strike_price: Optional[Decimal] = Field(default=None, description="Strike price")
    expiry_date: Optional[datetime] = Field(default=None, description="Expiry date")
    
    # Fees and costs
    commission: Optional[Decimal] = Field(default=None, description="Commission")
    fees: Optional[Decimal] = Field(default=None, description="Other fees")
    
    # Timestamps
    trade_time: datetime = Field(description="Trade execution time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation time")
    
    # Metadata
    strategy_id: Optional[str] = Field(default=None, description="Strategy ID")
    signal_id: Optional[str] = Field(default=None, description="Signal ID")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class PositionRecord(BaseModel):
    """Position record model"""
    
    # Primary key
    id: Optional[int] = Field(default=None, description="Record ID")
    
    # Position identification
    account_name: str = Field(description="Account name")
    symbol: str = Field(description="Symbol")
    underlying_symbol: Optional[str] = Field(default=None, description="Underlying symbol")
    instrument_type: str = Field(description="Instrument type")
    
    # Position details
    quantity: Decimal = Field(description="Position quantity")
    avg_cost: Decimal = Field(description="Average cost")
    market_price: Optional[Decimal] = Field(default=None, description="Current market price")
    market_value: Optional[Decimal] = Field(default=None, description="Current market value")
    
    # P&L information
    unrealized_pnl: Optional[Decimal] = Field(default=None, description="Unrealized P&L")
    realized_pnl: Optional[Decimal] = Field(default=None, description="Realized P&L")
    
    # Option specific fields
    option_type: Optional[str] = Field(default=None, description="Option type")
    strike_price: Optional[Decimal] = Field(default=None, description="Strike price")
    expiry_date: Optional[datetime] = Field(default=None, description="Expiry date")
    
    # Greeks (for options)
    delta: Optional[Decimal] = Field(default=None, description="Delta")
    gamma: Optional[Decimal] = Field(default=None, description="Gamma")
    theta: Optional[Decimal] = Field(default=None, description="Theta")
    vega: Optional[Decimal] = Field(default=None, description="Vega")
    implied_volatility: Optional[Decimal] = Field(default=None, description="Implied volatility")
    
    # Timestamps
    position_date: datetime = Field(description="Position date")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    # Metadata
    currency: str = Field(description="Currency")
    multiplier: int = Field(default=1, description="Contract multiplier")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class OrderRecord(BaseModel):
    """Order record model"""
    
    # Primary key
    id: Optional[int] = Field(default=None, description="Record ID")
    
    # Order identification
    order_id: str = Field(description="Order ID")
    account_name: str = Field(description="Account name")
    
    # Instrument information
    symbol: str = Field(description="Symbol")
    underlying_symbol: Optional[str] = Field(default=None, description="Underlying symbol")
    instrument_type: str = Field(description="Instrument type")
    
    # Order details
    order_type: str = Field(description="Order type")
    side: str = Field(description="Order side")
    quantity: Decimal = Field(description="Order quantity")
    price: Optional[Decimal] = Field(default=None, description="Order price")
    stop_price: Optional[Decimal] = Field(default=None, description="Stop price")
    time_in_force: str = Field(description="Time in force")
    
    # Order status
    status: str = Field(description="Order status")
    filled_quantity: Decimal = Field(default=Decimal('0'), description="Filled quantity")
    avg_fill_price: Optional[Decimal] = Field(default=None, description="Average fill price")
    
    # Option specific fields
    option_type: Optional[str] = Field(default=None, description="Option type")
    strike_price: Optional[Decimal] = Field(default=None, description="Strike price")
    expiry_date: Optional[datetime] = Field(default=None, description="Expiry date")
    
    # Timestamps
    created_at: datetime = Field(description="Order creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    filled_at: Optional[datetime] = Field(default=None, description="Fill time")
    
    # Metadata
    currency: str = Field(description="Currency")
    commission: Optional[Decimal] = Field(default=None, description="Commission")
    signal_id: Optional[str] = Field(default=None, description="Signal ID")
    strategy_id: Optional[str] = Field(default=None, description="Strategy ID")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }


class SignalRecord(BaseModel):
    """Signal record model"""
    
    # Primary key
    id: Optional[int] = Field(default=None, description="Record ID")
    
    # Signal identification
    signal_id: str = Field(description="Unique signal ID")
    account_name: str = Field(description="Account name")
    
    # Signal details
    symbol: str = Field(description="Symbol")
    side: str = Field(description="Signal side")
    action: str = Field(description="Signal action")
    quantity: Decimal = Field(description="Signal quantity")
    price: Decimal = Field(description="Signal price")
    
    # Original webhook data
    webhook_payload: Dict[str, Any] = Field(description="Original webhook payload")
    
    # Processing status
    status: str = Field(description="Processing status")
    error_message: Optional[str] = Field(default=None, description="Error message")
    
    # Results
    orders_created: Optional[int] = Field(default=None, description="Number of orders created")
    total_quantity_filled: Optional[Decimal] = Field(default=None, description="Total quantity filled")
    
    # Timestamps
    received_at: datetime = Field(description="Signal received time")
    processed_at: Optional[datetime] = Field(default=None, description="Signal processed time")
    completed_at: Optional[datetime] = Field(default=None, description="Signal completed time")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }
