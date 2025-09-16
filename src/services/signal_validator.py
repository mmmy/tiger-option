"""
Signal validation service for TradingView webhook signals
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from ..models import (
    WebhookSignal,
    TradeSignal,
    SignalValidationResult,
)
from ..config import AccountConfig


logger = logging.getLogger(__name__)


class SignalValidationError(Exception):
    """Signal validation error"""
    pass


class SignalValidator:
    """Service for validating trading signals"""
    
    def __init__(self):
        """Initialize signal validator"""
        # Symbol patterns for different asset types
        self.stock_pattern = re.compile(r'^[A-Z]{1,5}$')
        self.option_pattern = re.compile(r'^[A-Z]{1,5}\s+\d{6}[CP]\d{8}$')
        self.crypto_pattern = re.compile(r'^[A-Z]{3,10}[/-][A-Z]{3,10}$')
        
        # Valid values
        self.valid_actions = {"buy", "sell", "close", "close_all"}
        self.valid_order_types = {"market", "limit", "stop", "stop_limit", "trailing_stop"}
        self.valid_time_in_force = {"day", "gtc", "ioc", "fok"}
        
        logger.info("Signal validator initialized")
    
    def validate_signal(
        self, 
        signal: WebhookSignal, 
        account_config: AccountConfig
    ) -> SignalValidationResult:
        """Validate a trading signal against account configuration"""
        
        errors = []
        warnings = []
        
        try:
            # Basic field validation
            errors.extend(self._validate_required_fields(signal))
            errors.extend(self._validate_symbol_format(signal.symbol))
            errors.extend(self._validate_action(signal.action))
            errors.extend(self._validate_quantities(signal))
            errors.extend(self._validate_prices(signal))
            errors.extend(self._validate_order_parameters(signal))
            
            # Account-specific validation
            errors.extend(self._validate_against_account_config(signal, account_config))
            
            # Business logic validation
            warnings.extend(self._validate_business_logic(signal, account_config))
            
        except Exception as e:
            logger.error(f"Unexpected error during signal validation: {e}")
            errors.append(f"Validation error: {str(e)}")
        
        return SignalValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            action=signal.action
        )
    
    def _validate_required_fields(self, signal: WebhookSignal) -> List[str]:
        """Validate required fields are present and not empty"""
        errors = []
        
        if not signal.symbol or signal.symbol.strip() == "":
            errors.append("Symbol is required and cannot be empty")
        
        if not signal.action or signal.action.strip() == "":
            errors.append("Action is required and cannot be empty")
        
        return errors
    
    def _validate_symbol_format(self, symbol: str) -> List[str]:
        """Validate symbol format"""
        errors = []
        
        if not symbol:
            return errors
        
        symbol = symbol.strip().upper()
        
        # Check symbol length
        if len(symbol) < 1:
            errors.append("Symbol cannot be empty")
            return errors
        
        if len(symbol) > 50:
            errors.append("Symbol is too long (max 50 characters)")
        
        # Check for valid characters (basic check)
        if not re.match(r'^[A-Z0-9\s\.\-/]+$', symbol):
            errors.append("Symbol contains invalid characters")
        
        # Specific format validation
        if self._is_option_symbol(symbol):
            if not self.option_pattern.match(symbol):
                errors.append("Invalid option symbol format")
        elif self._is_crypto_symbol(symbol):
            if not self.crypto_pattern.match(symbol):
                errors.append("Invalid crypto symbol format")
        elif not self.stock_pattern.match(symbol) and not self._is_complex_symbol(symbol):
            errors.append("Invalid symbol format")
        
        return errors
    
    def _validate_action(self, action: str) -> List[str]:
        """Validate trading action"""
        errors = []
        
        if not action:
            return errors
        
        action_lower = action.lower().strip()
        
        if action_lower not in self.valid_actions:
            errors.append(f"Invalid action '{action}'. Must be one of: {', '.join(self.valid_actions)}")
        
        return errors
    
    def _validate_quantities(self, signal: WebhookSignal) -> List[str]:
        """Validate quantity values"""
        errors = []
        
        if signal.quantity is not None:
            if signal.quantity <= 0:
                errors.append("Quantity must be positive")
            
            if signal.quantity > Decimal('1000000'):
                errors.append("Quantity is too large (max 1,000,000)")
            
            # Check for reasonable decimal places
            if signal.quantity.as_tuple().exponent < -8:
                errors.append("Quantity has too many decimal places (max 8)")
        
        return errors
    
    def _validate_prices(self, signal: WebhookSignal) -> List[str]:
        """Validate price values"""
        errors = []
        
        if signal.price is not None:
            if signal.price <= 0:
                errors.append("Price must be positive")
            
            if signal.price > Decimal('1000000'):
                errors.append("Price is too high (max 1,000,000)")
        
        if signal.stop_price is not None:
            if signal.stop_price <= 0:
                errors.append("Stop price must be positive")
            
            if signal.stop_price > Decimal('1000000'):
                errors.append("Stop price is too high (max 1,000,000)")
        
        # Validate price relationships
        if (signal.price is not None and signal.stop_price is not None and 
            signal.order_type and signal.order_type.lower() == "stop_limit"):
            
            action_lower = signal.action.lower() if signal.action else ""
            
            if action_lower == "buy" and signal.stop_price <= signal.price:
                errors.append("For buy stop-limit orders, stop price should be above limit price")
            elif action_lower == "sell" and signal.stop_price >= signal.price:
                errors.append("For sell stop-limit orders, stop price should be below limit price")
        
        return errors
    
    def _validate_order_parameters(self, signal: WebhookSignal) -> List[str]:
        """Validate order type and time in force"""
        errors = []
        
        if signal.order_type:
            order_type_lower = signal.order_type.lower().strip()
            if order_type_lower not in self.valid_order_types:
                errors.append(f"Invalid order type '{signal.order_type}'. Must be one of: {', '.join(self.valid_order_types)}")
            
            # Validate price requirements for order types
            if order_type_lower in ["limit", "stop_limit"] and signal.price is None:
                errors.append(f"Price is required for {signal.order_type} orders")
            
            if order_type_lower in ["stop", "stop_limit"] and signal.stop_price is None:
                errors.append(f"Stop price is required for {signal.order_type} orders")
        
        if signal.time_in_force:
            tif_lower = signal.time_in_force.lower().strip()
            if tif_lower not in self.valid_time_in_force:
                errors.append(f"Invalid time in force '{signal.time_in_force}'. Must be one of: {', '.join(self.valid_time_in_force)}")
        
        return errors
    
    def _validate_against_account_config(self, signal: WebhookSignal, account_config: AccountConfig) -> List[str]:
        """Validate signal against account configuration"""
        errors = []
        
        # Check if account allows options trading
        if (not account_config.allow_options_trading and 
            signal.symbol and self._is_option_symbol(signal.symbol)):
            errors.append("Options trading is not enabled for this account")
        
        # Check position size limits
        if signal.quantity is not None:
            if signal.quantity > account_config.max_position_size:
                errors.append(f"Quantity {signal.quantity} exceeds max position size {account_config.max_position_size}")
        
        # Check if action is allowed
        if signal.action:
            action_lower = signal.action.lower()
            if action_lower in ["sell", "close"] and not account_config.allow_short_selling:
                # This is a simplified check - in reality you'd check current positions
                pass  # For now, allow all actions
        
        return errors
    
    def _validate_business_logic(self, signal: WebhookSignal, account_config: AccountConfig) -> List[str]:
        """Validate business logic and generate warnings"""
        warnings = []
        
        # Check for potentially risky operations
        if signal.quantity and signal.quantity > account_config.max_position_size * Decimal('0.5'):
            warnings.append("Large position size detected - consider risk management")
        
        # Check for market orders outside trading hours (simplified)
        if signal.order_type and signal.order_type.lower() == "market":
            current_hour = datetime.now().hour
            if current_hour < 9 or current_hour > 16:  # Simplified US market hours
                warnings.append("Market order outside typical trading hours")
        
        # Check for option expiry proximity (if option symbol)
        if signal.symbol and self._is_option_symbol(signal.symbol):
            # This would require parsing the option symbol to extract expiry
            # For now, just a placeholder warning
            warnings.append("Verify option expiry date before trading")
        
        return warnings
    
    def _is_option_symbol(self, symbol: str) -> bool:
        """Check if symbol is an option"""
        return " " in symbol and ("C" in symbol or "P" in symbol) and len(symbol) > 10
    
    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Check if symbol is a cryptocurrency pair"""
        return "/" in symbol or "-" in symbol
    
    def _is_complex_symbol(self, symbol: str) -> bool:
        """Check if symbol is a complex instrument (futures, etc.)"""
        return "." in symbol or len(symbol) > 5
    
    def convert_to_trade_signal(
        self, 
        signal: WebhookSignal, 
        account_config: AccountConfig,
        signal_id: Optional[str] = None
    ) -> TradeSignal:
        """Convert validated webhook signal to internal trade signal"""
        
        # Generate signal ID if not provided
        if not signal_id:
            signal_id = signal.signal_id or f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Determine quantity if not specified
        quantity = signal.quantity
        if quantity is None:
            quantity = account_config.default_position_size
        
        # Set defaults
        order_type = signal.order_type or "market"
        time_in_force = signal.time_in_force or "day"
        
        return TradeSignal(
            signal_id=signal_id,
            account_name=account_config.name,
            symbol=signal.symbol,
            action=signal.action.lower(),
            quantity=quantity,
            price=signal.price,
            stop_price=signal.stop_price,
            order_type=order_type.lower(),
            time_in_force=time_in_force.lower(),
            strategy=signal.strategy,
            comment=signal.comment,
            received_at=datetime.now(),
            metadata=signal.metadata or {}
        )


# Global validator instance
_signal_validator: Optional[SignalValidator] = None


def get_signal_validator() -> SignalValidator:
    """Get global signal validator instance"""
    global _signal_validator
    
    if _signal_validator is None:
        _signal_validator = SignalValidator()
    
    return _signal_validator
