"""
Position Management System for Tiger Options Trading Service

This module implements position tracking, management, and analysis
for options trading portfolios.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from enum import Enum
from collections import defaultdict

from ..models import (
    Position,
    OptionContract,
    TigerOrder,
    OrderSide,
    OptionType
)
from ..config import AccountConfig


logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """Position status types"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"
    EXPIRED = "expired"


class PositionType(Enum):
    """Position types"""
    LONG_CALL = "long_call"
    SHORT_CALL = "short_call"
    LONG_PUT = "long_put"
    SHORT_PUT = "short_put"
    SPREAD = "spread"
    STRADDLE = "straddle"
    STRANGLE = "strangle"


class PositionManager:
    """
    Position management service for options trading
    
    Tracks positions, calculates P&L, manages risk, and provides
    portfolio analysis functionality.
    """
    
    def __init__(self, account_config: AccountConfig):
        """Initialize position manager"""
        self.account_config = account_config
        self.logger = logging.getLogger(f"{__name__}.{account_config.name}")
        
        # In-memory position tracking (in production, this would use database)
        self._positions: Dict[str, Position] = {}
        self._position_history: List[Dict[str, Any]] = []
    
    def update_positions(self, positions: List[Position]) -> None:
        """
        Update current positions from broker data
        
        Args:
            positions: List of current positions from broker
        """
        
        try:
            # Clear existing positions
            self._positions.clear()
            
            # Add new positions
            for position in positions:
                if position.symbol:
                    self._positions[position.symbol] = position
            
            self.logger.info(f"Updated {len(positions)} positions")
            
            # Log position summary
            total_value = sum(
                float(pos.market_value or 0) for pos in positions
            )
            total_pnl = sum(
                float(pos.unrealized_pnl or 0) for pos in positions
            )
            
            self.logger.info(
                f"Portfolio summary: ${total_value:.2f} value, "
                f"${total_pnl:.2f} unrealized P&L"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol"""
        return self._positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """Get all current positions"""
        return list(self._positions.values())
    
    def get_positions_by_underlying(self, underlying: str) -> List[Position]:
        """Get all positions for a specific underlying asset"""
        
        positions = []
        for position in self._positions.values():
            # Extract underlying from option symbol
            if self._extract_underlying(position.symbol) == underlying.upper():
                positions.append(position)
        
        return positions
    
    def calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive portfolio metrics"""
        
        try:
            positions = list(self._positions.values())
            
            if not positions:
                return {
                    "total_positions": 0,
                    "total_market_value": 0.0,
                    "total_unrealized_pnl": 0.0,
                    "total_realized_pnl": 0.0,
                    "portfolio_delta": 0.0,
                    "portfolio_gamma": 0.0,
                    "portfolio_theta": 0.0,
                    "portfolio_vega": 0.0,
                    "by_underlying": {},
                    "by_position_type": {},
                    "risk_metrics": {}
                }
            
            # Basic metrics
            total_market_value = sum(float(pos.market_value or 0) for pos in positions)
            total_unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            total_realized_pnl = sum(float(pos.realized_pnl or 0) for pos in positions)
            
            # Greeks (if available)
            portfolio_delta = sum(float(getattr(pos, 'delta', 0) or 0) for pos in positions)
            portfolio_gamma = sum(float(getattr(pos, 'gamma', 0) or 0) for pos in positions)
            portfolio_theta = sum(float(getattr(pos, 'theta', 0) or 0) for pos in positions)
            portfolio_vega = sum(float(getattr(pos, 'vega', 0) or 0) for pos in positions)
            
            # Group by underlying
            by_underlying = defaultdict(lambda: {
                'positions': 0,
                'market_value': 0.0,
                'unrealized_pnl': 0.0,
                'delta': 0.0
            })
            
            for pos in positions:
                underlying = self._extract_underlying(pos.symbol)
                by_underlying[underlying]['positions'] += 1
                by_underlying[underlying]['market_value'] += float(pos.market_value or 0)
                by_underlying[underlying]['unrealized_pnl'] += float(pos.unrealized_pnl or 0)
                by_underlying[underlying]['delta'] += float(getattr(pos, 'delta', 0) or 0)
            
            # Group by position type
            by_position_type = defaultdict(lambda: {
                'positions': 0,
                'market_value': 0.0,
                'unrealized_pnl': 0.0
            })
            
            for pos in positions:
                pos_type = self._classify_position_type(pos)
                by_position_type[pos_type]['positions'] += 1
                by_position_type[pos_type]['market_value'] += float(pos.market_value or 0)
                by_position_type[pos_type]['unrealized_pnl'] += float(pos.unrealized_pnl or 0)
            
            # Risk metrics
            risk_metrics = self._calculate_risk_metrics(positions)
            
            return {
                "total_positions": len(positions),
                "total_market_value": total_market_value,
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_realized_pnl": total_realized_pnl,
                "portfolio_delta": portfolio_delta,
                "portfolio_gamma": portfolio_gamma,
                "portfolio_theta": portfolio_theta,
                "portfolio_vega": portfolio_vega,
                "by_underlying": dict(by_underlying),
                "by_position_type": dict(by_position_type),
                "risk_metrics": risk_metrics,
                "calculated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {e}")
            return {}
    
    def check_position_limits(self, symbol: str, quantity: Decimal) -> Tuple[bool, List[str]]:
        """
        Check if a new position would violate position limits
        
        Args:
            symbol: Symbol to check
            quantity: Proposed quantity
            
        Returns:
            Tuple of (is_allowed, list_of_violations)
        """
        
        violations = []
        
        try:
            # Check individual position size limit
            current_position = self.get_position(symbol)
            current_quantity = Decimal(str(current_position.quantity)) if current_position else Decimal('0')
            new_total_quantity = abs(current_quantity + quantity)
            
            if new_total_quantity > self.account_config.max_position_size:
                violations.append(
                    f"Position size limit exceeded: {new_total_quantity} > {self.account_config.max_position_size}"
                )
            
            # Check underlying concentration limit
            underlying = self._extract_underlying(symbol)
            underlying_positions = self.get_positions_by_underlying(underlying)
            underlying_value = sum(float(pos.market_value or 0) for pos in underlying_positions)
            
            # Assume max 50% concentration per underlying
            max_underlying_value = float(self.account_config.max_position_size) * 0.5
            if underlying_value > max_underlying_value:
                violations.append(
                    f"Underlying concentration limit exceeded: ${underlying_value:.2f} > ${max_underlying_value:.2f}"
                )
            
            # Check total portfolio value limit (if configured)
            if hasattr(self.account_config, 'max_portfolio_value'):
                metrics = self.calculate_portfolio_metrics()
                total_value = metrics.get('total_market_value', 0)
                if total_value > float(self.account_config.max_portfolio_value):
                    violations.append(
                        f"Portfolio value limit exceeded: ${total_value:.2f} > ${self.account_config.max_portfolio_value}"
                    )
            
            return len(violations) == 0, violations
            
        except Exception as e:
            self.logger.error(f"Error checking position limits: {e}")
            return False, [f"Error checking limits: {str(e)}"]
    
    def suggest_position_sizing(
        self,
        symbol: str,
        signal_quantity: Decimal,
        risk_percentage: Decimal = Decimal('0.02')
    ) -> Decimal:
        """
        Suggest optimal position size based on risk management rules
        
        Args:
            symbol: Symbol to trade
            signal_quantity: Requested quantity from signal
            risk_percentage: Maximum risk as percentage of portfolio
            
        Returns:
            Suggested position size
        """
        
        try:
            # Start with signal quantity
            suggested_quantity = signal_quantity
            
            # Apply account-level limits
            max_account_size = Decimal(str(self.account_config.max_position_size))
            suggested_quantity = min(suggested_quantity, max_account_size)
            
            # Apply default position size if signal quantity is too large
            default_size = Decimal(str(self.account_config.default_position_size))
            if suggested_quantity > default_size * 2:
                suggested_quantity = default_size
            
            # Apply risk-based sizing (simplified)
            metrics = self.calculate_portfolio_metrics()
            portfolio_value = metrics.get('total_market_value', 0)
            
            if portfolio_value > 0:
                max_risk_value = Decimal(str(portfolio_value)) * risk_percentage
                # Assume 10% of position value as risk (simplified)
                max_position_value = max_risk_value * 10
                
                # This would need actual option pricing to be accurate
                # For now, use a simple heuristic
                estimated_option_price = Decimal('5.00')  # $5 per contract
                max_contracts = max_position_value / estimated_option_price
                
                suggested_quantity = min(suggested_quantity, max_contracts)
            
            # Ensure minimum viable quantity
            min_quantity = Decimal('1')
            suggested_quantity = max(suggested_quantity, min_quantity)
            
            self.logger.info(
                f"Position sizing for {symbol}: requested {signal_quantity}, "
                f"suggested {suggested_quantity}"
            )
            
            return suggested_quantity
            
        except Exception as e:
            self.logger.error(f"Error suggesting position size: {e}")
            return signal_quantity
    
    def _extract_underlying(self, option_symbol: str) -> str:
        """Extract underlying symbol from option symbol"""
        
        try:
            # Handle different option symbol formats
            # Example: "AAPL  250117C00150000" -> "AAPL"
            if '  ' in option_symbol:
                return option_symbol.split('  ')[0].strip()
            
            # Fallback: assume first part before space or number
            import re
            match = re.match(r'^([A-Z]+)', option_symbol)
            if match:
                return match.group(1)
            
            return option_symbol
            
        except Exception:
            return option_symbol
    
    def _classify_position_type(self, position: Position) -> str:
        """Classify position type based on symbol and quantity"""
        
        try:
            # Determine if it's an option
            if self._is_option_symbol(position.symbol):
                # Determine call/put from symbol
                is_call = 'C' in position.symbol
                is_long = float(position.quantity or 0) > 0
                
                if is_call and is_long:
                    return PositionType.LONG_CALL.value
                elif is_call and not is_long:
                    return PositionType.SHORT_CALL.value
                elif not is_call and is_long:
                    return PositionType.LONG_PUT.value
                else:
                    return PositionType.SHORT_PUT.value
            else:
                return "stock"
                
        except Exception:
            return "unknown"
    
    def _is_option_symbol(self, symbol: str) -> bool:
        """Check if symbol is an option"""
        
        # Simple heuristic: options typically have spaces and C/P indicators
        return '  ' in symbol and ('C' in symbol or 'P' in symbol)
    
    def _calculate_risk_metrics(self, positions: List[Position]) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        
        try:
            if not positions:
                return {}
            
            # Calculate basic risk metrics
            total_value = sum(float(pos.market_value or 0) for pos in positions)
            total_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            
            # Value at Risk (simplified)
            var_1d = total_value * 0.02  # Assume 2% daily VaR
            
            # Maximum drawdown (would need historical data)
            max_drawdown = abs(min(0, total_pnl))
            
            # Concentration risk
            underlying_values = defaultdict(float)
            for pos in positions:
                underlying = self._extract_underlying(pos.symbol)
                underlying_values[underlying] += float(pos.market_value or 0)
            
            max_concentration = max(underlying_values.values()) / total_value if total_value > 0 else 0
            
            return {
                "value_at_risk_1d": var_1d,
                "max_drawdown": max_drawdown,
                "max_concentration": max_concentration,
                "position_count": len(positions),
                "underlying_count": len(underlying_values)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    def get_expiring_positions(self, days_ahead: int = 7) -> List[Position]:
        """Get positions expiring within specified days"""
        
        expiring = []
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        for position in self._positions.values():
            if self._is_option_symbol(position.symbol):
                # Extract expiry from symbol (simplified)
                # In practice, you'd need proper option symbol parsing
                try:
                    # This is a placeholder - real implementation would parse option symbols
                    # to extract expiry dates
                    expiring.append(position)
                except Exception:
                    continue
        
        return expiring
