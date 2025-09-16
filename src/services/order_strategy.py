"""
Order Strategy Implementation for Tiger Options Trading Service

This module implements various order strategies for options trading,
including market orders, limit orders, stop orders, and advanced strategies.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from enum import Enum

from ..models import (
    OptionContract,
    TradeSignal,
    OrderType,
    OrderSide,
    TigerOrder
)
from ..config import AccountConfig


logger = logging.getLogger(__name__)


class OrderStrategy(Enum):
    """Order execution strategies"""
    MARKET = "market"                    # Market order - immediate execution
    LIMIT = "limit"                      # Limit order at specified price
    LIMIT_MIDPOINT = "limit_midpoint"    # Limit order at bid-ask midpoint
    LIMIT_AGGRESSIVE = "limit_aggressive" # Aggressive limit order (closer to market)
    LIMIT_CONSERVATIVE = "limit_conservative" # Conservative limit order (better price)
    STOP_LOSS = "stop_loss"             # Stop loss order
    BRACKET = "bracket"                  # Bracket order (entry + stop + target)


class PriceCalculationMethod(Enum):
    """Methods for calculating order prices"""
    BID_ASK_MIDPOINT = "bid_ask_midpoint"
    LAST_PRICE = "last_price"
    BID_PRICE = "bid_price"
    ASK_PRICE = "ask_price"
    THEORETICAL_PRICE = "theoretical_price"


class OrderStrategyService:
    """
    Order strategy service for options trading
    
    Implements various order strategies and price calculation methods
    to optimize order execution based on market conditions.
    """
    
    def __init__(self, account_config: AccountConfig):
        """Initialize order strategy service"""
        self.account_config = account_config
        self.logger = logging.getLogger(f"{__name__}.{account_config.name}")
    
    def create_order(
        self,
        signal: TradeSignal,
        contract: OptionContract,
        strategy: OrderStrategy = OrderStrategy.LIMIT_MIDPOINT,
        quantity: Optional[Decimal] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an order based on signal, contract, and strategy
        
        Args:
            signal: Trading signal
            contract: Selected option contract
            strategy: Order execution strategy
            quantity: Order quantity (uses signal quantity if not specified)
            
        Returns:
            Order parameters dictionary or None if order cannot be created
        """
        
        try:
            # Determine order quantity
            order_quantity = quantity or signal.quantity
            if not order_quantity or order_quantity <= 0:
                self.logger.error("Invalid order quantity")
                return None
            
            # Calculate order price based on strategy
            order_price = self._calculate_order_price(contract, strategy, signal.action)
            
            if order_price is None and strategy != OrderStrategy.MARKET:
                self.logger.error(f"Could not calculate price for strategy: {strategy.value}")
                return None
            
            # Determine order type
            order_type = self._get_order_type(strategy)
            
            # Create order parameters
            order_params = {
                "symbol": contract.symbol,
                "order_type": order_type,
                "side": signal.action,
                "quantity": order_quantity,
                "price": order_price,
                "time_in_force": signal.time_in_force or "day",
                "strategy": strategy.value,
                "signal_id": signal.signal_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Add strategy-specific parameters
            if strategy == OrderStrategy.STOP_LOSS:
                order_params["stop_price"] = self._calculate_stop_price(contract, signal.action)
            
            self.logger.info(
                f"Created {strategy.value} order: {contract.symbol} "
                f"{signal.action.value} {order_quantity} @ {order_price}"
            )
            
            return order_params
            
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return None
    
    def _calculate_order_price(
        self,
        contract: OptionContract,
        strategy: OrderStrategy,
        side: OrderSide
    ) -> Optional[Decimal]:
        """Calculate order price based on strategy and market data"""
        
        if strategy == OrderStrategy.MARKET:
            return None  # Market orders don't need price
        
        try:
            if strategy == OrderStrategy.LIMIT:
                # Use signal price if available, otherwise midpoint
                return self._get_price_by_method(contract, PriceCalculationMethod.BID_ASK_MIDPOINT)
            
            elif strategy == OrderStrategy.LIMIT_MIDPOINT:
                return self._get_price_by_method(contract, PriceCalculationMethod.BID_ASK_MIDPOINT)
            
            elif strategy == OrderStrategy.LIMIT_AGGRESSIVE:
                # For buy orders, use ask price (or close to it)
                # For sell orders, use bid price (or close to it)
                if side == OrderSide.BUY:
                    ask_price = self._get_price_by_method(contract, PriceCalculationMethod.ASK_PRICE)
                    if ask_price:
                        return ask_price * Decimal("0.99")  # Slightly below ask
                else:
                    bid_price = self._get_price_by_method(contract, PriceCalculationMethod.BID_PRICE)
                    if bid_price:
                        return bid_price * Decimal("1.01")  # Slightly above bid
                
                # Fallback to midpoint
                return self._get_price_by_method(contract, PriceCalculationMethod.BID_ASK_MIDPOINT)
            
            elif strategy == OrderStrategy.LIMIT_CONSERVATIVE:
                # For buy orders, use bid price (or below)
                # For sell orders, use ask price (or above)
                if side == OrderSide.BUY:
                    bid_price = self._get_price_by_method(contract, PriceCalculationMethod.BID_PRICE)
                    if bid_price:
                        return bid_price * Decimal("1.01")  # Slightly above bid
                else:
                    ask_price = self._get_price_by_method(contract, PriceCalculationMethod.ASK_PRICE)
                    if ask_price:
                        return ask_price * Decimal("0.99")  # Slightly below ask
                
                # Fallback to midpoint
                return self._get_price_by_method(contract, PriceCalculationMethod.BID_ASK_MIDPOINT)
            
            else:
                # Default to midpoint
                return self._get_price_by_method(contract, PriceCalculationMethod.BID_ASK_MIDPOINT)
                
        except Exception as e:
            self.logger.error(f"Error calculating order price: {e}")
            return None
    
    def _get_price_by_method(
        self,
        contract: OptionContract,
        method: PriceCalculationMethod
    ) -> Optional[Decimal]:
        """Get price using specified calculation method"""
        
        try:
            if method == PriceCalculationMethod.BID_ASK_MIDPOINT:
                if contract.bid and contract.ask:
                    return (contract.bid + contract.ask) / 2
            
            elif method == PriceCalculationMethod.LAST_PRICE:
                if contract.last_price:
                    return contract.last_price
            
            elif method == PriceCalculationMethod.BID_PRICE:
                if contract.bid:
                    return contract.bid
            
            elif method == PriceCalculationMethod.ASK_PRICE:
                if contract.ask:
                    return contract.ask
            
            elif method == PriceCalculationMethod.THEORETICAL_PRICE:
                # Use theoretical value if available, otherwise midpoint
                if hasattr(contract, 'theoretical_price') and contract.theoretical_price:
                    return contract.theoretical_price
                elif contract.bid and contract.ask:
                    return (contract.bid + contract.ask) / 2
            
            # Fallback chain: last -> midpoint -> bid -> ask
            if contract.last_price:
                return contract.last_price
            elif contract.bid and contract.ask:
                return (contract.bid + contract.ask) / 2
            elif contract.bid:
                return contract.bid
            elif contract.ask:
                return contract.ask
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting price by method {method.value}: {e}")
            return None
    
    def _get_order_type(self, strategy: OrderStrategy) -> OrderType:
        """Get order type based on strategy"""
        
        if strategy == OrderStrategy.MARKET:
            return OrderType.MARKET
        elif strategy == OrderStrategy.STOP_LOSS:
            return OrderType.STOP
        else:
            return OrderType.LIMIT
    
    def _calculate_stop_price(
        self,
        contract: OptionContract,
        side: OrderSide,
        stop_percentage: Decimal = Decimal("0.10")
    ) -> Optional[Decimal]:
        """Calculate stop price for stop loss orders"""
        
        try:
            current_price = self._get_price_by_method(
                contract, PriceCalculationMethod.BID_ASK_MIDPOINT
            )
            
            if not current_price:
                return None
            
            if side == OrderSide.BUY:
                # For buy orders, stop below current price
                return current_price * (1 - stop_percentage)
            else:
                # For sell orders, stop above current price
                return current_price * (1 + stop_percentage)
                
        except Exception as e:
            self.logger.error(f"Error calculating stop price: {e}")
            return None
    
    def create_bracket_order(
        self,
        signal: TradeSignal,
        contract: OptionContract,
        profit_target_pct: Decimal = Decimal("0.20"),
        stop_loss_pct: Decimal = Decimal("0.10")
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Create a bracket order (entry + profit target + stop loss)
        
        Args:
            signal: Trading signal
            contract: Option contract
            profit_target_pct: Profit target percentage
            stop_loss_pct: Stop loss percentage
            
        Returns:
            List of order parameters for bracket order
        """
        
        try:
            # Create entry order
            entry_order = self.create_order(
                signal, contract, OrderStrategy.LIMIT_MIDPOINT
            )
            
            if not entry_order:
                return None
            
            entry_price = entry_order.get("price")
            if not entry_price:
                return None
            
            orders = [entry_order]
            
            # Create profit target order (opposite side)
            profit_side = OrderSide.SELL if signal.action == OrderSide.BUY else OrderSide.BUY
            profit_price = entry_price * (1 + profit_target_pct) if signal.action == OrderSide.BUY else entry_price * (1 - profit_target_pct)
            
            profit_order = {
                "symbol": contract.symbol,
                "order_type": OrderType.LIMIT,
                "side": profit_side,
                "quantity": signal.quantity,
                "price": profit_price,
                "time_in_force": "gtc",  # Good till cancelled
                "strategy": "bracket_profit",
                "signal_id": signal.signal_id,
                "parent_order": "entry",
                "created_at": datetime.now().isoformat()
            }
            orders.append(profit_order)
            
            # Create stop loss order
            stop_price = entry_price * (1 - stop_loss_pct) if signal.action == OrderSide.BUY else entry_price * (1 + stop_loss_pct)
            
            stop_order = {
                "symbol": contract.symbol,
                "order_type": OrderType.STOP,
                "side": profit_side,  # Same side as profit target
                "quantity": signal.quantity,
                "stop_price": stop_price,
                "time_in_force": "gtc",
                "strategy": "bracket_stop",
                "signal_id": signal.signal_id,
                "parent_order": "entry",
                "created_at": datetime.now().isoformat()
            }
            orders.append(stop_order)
            
            self.logger.info(
                f"Created bracket order: entry @ {entry_price}, "
                f"profit @ {profit_price}, stop @ {stop_price}"
            )
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Error creating bracket order: {e}")
            return None
    
    def validate_order_parameters(self, order_params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate order parameters
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        
        errors = []
        
        # Required fields
        required_fields = ["symbol", "order_type", "side", "quantity"]
        for field in required_fields:
            if field not in order_params or order_params[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate quantity
        if "quantity" in order_params:
            try:
                quantity = Decimal(str(order_params["quantity"]))
                if quantity <= 0:
                    errors.append("Quantity must be positive")
                elif quantity > self.account_config.max_position_size:
                    errors.append(f"Quantity exceeds max position size: {self.account_config.max_position_size}")
            except (ValueError, TypeError):
                errors.append("Invalid quantity format")
        
        # Validate price for limit orders
        if order_params.get("order_type") == OrderType.LIMIT:
            if "price" not in order_params or order_params["price"] is None:
                errors.append("Price required for limit orders")
            else:
                try:
                    price = Decimal(str(order_params["price"]))
                    if price <= 0:
                        errors.append("Price must be positive")
                except (ValueError, TypeError):
                    errors.append("Invalid price format")
        
        # Validate stop price for stop orders
        if order_params.get("order_type") == OrderType.STOP:
            if "stop_price" not in order_params or order_params["stop_price"] is None:
                errors.append("Stop price required for stop orders")
            else:
                try:
                    stop_price = Decimal(str(order_params["stop_price"]))
                    if stop_price <= 0:
                        errors.append("Stop price must be positive")
                except (ValueError, TypeError):
                    errors.append("Invalid stop price format")
        
        return len(errors) == 0, errors
