"""
Risk Management Module for Tiger Options Trading Service

This module implements comprehensive risk management controls including
position limits, stop losses, drawdown protection, and portfolio risk monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from enum import Enum

from ..models import (
    Position,
    TradeSignal,
    OptionContract,
    OrderSide
)
from ..config import AccountConfig
from .position_manager import PositionManager


logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCheckResult(Enum):
    """Risk check results"""
    APPROVED = "approved"
    REJECTED = "rejected"
    WARNING = "warning"
    REQUIRES_REVIEW = "requires_review"


class RiskManager:
    """
    Comprehensive risk management service
    
    Implements multiple layers of risk controls including position limits,
    stop losses, drawdown protection, and real-time risk monitoring.
    """
    
    def __init__(self, account_config: AccountConfig, position_manager: PositionManager):
        """Initialize risk manager"""
        self.account_config = account_config
        self.position_manager = position_manager
        self.logger = logging.getLogger(f"{__name__}.{account_config.name}")
        
        # Risk configuration (would be loaded from config in production)
        self.risk_config = {
            "max_daily_loss": getattr(account_config, 'max_daily_loss', Decimal('5000')),
            "max_position_value": getattr(account_config, 'max_position_value', Decimal('50000')),
            "stop_loss_percentage": getattr(account_config, 'stop_loss_percentage', Decimal('0.05')),
            "max_portfolio_delta": Decimal('100'),
            "max_concentration_pct": Decimal('0.30'),  # 30% max per underlying
            "max_open_positions": 20,
            "min_days_to_expiry": 3,
            "max_vega_exposure": Decimal('1000'),
            "max_theta_decay": Decimal('500')
        }
        
        # Track daily P&L for drawdown monitoring
        self._daily_pnl_start = None
        self._daily_pnl_current = Decimal('0')
    
    def check_trade_risk(
        self,
        signal: TradeSignal,
        contract: OptionContract,
        quantity: Decimal
    ) -> Tuple[RiskCheckResult, List[str], Dict[str, Any]]:
        """
        Comprehensive risk check for a proposed trade
        
        Args:
            signal: Trading signal
            contract: Option contract to trade
            quantity: Proposed quantity
            
        Returns:
            Tuple of (result, warnings/errors, risk_metrics)
        """
        
        warnings = []
        errors = []
        risk_metrics = {}
        
        try:
            # 1. Position size checks
            size_ok, size_errors = self._check_position_size_limits(
                contract.symbol, quantity
            )
            if not size_ok:
                errors.extend(size_errors)
            
            # 2. Portfolio concentration checks
            conc_ok, conc_warnings = self._check_concentration_limits(
                contract.symbol, quantity
            )
            if not conc_ok:
                warnings.extend(conc_warnings)
            
            # 3. Daily loss limit checks
            loss_ok, loss_errors = self._check_daily_loss_limits()
            if not loss_ok:
                errors.extend(loss_errors)
            
            # 4. Greeks exposure checks
            greeks_ok, greeks_warnings = self._check_greeks_exposure(
                contract, quantity, signal.action
            )
            if not greeks_ok:
                warnings.extend(greeks_warnings)
            
            # 5. Expiration checks
            exp_ok, exp_warnings = self._check_expiration_risk(contract)
            if not exp_ok:
                warnings.extend(exp_warnings)
            
            # 6. Liquidity checks
            liq_ok, liq_warnings = self._check_liquidity_risk(contract)
            if not liq_ok:
                warnings.extend(liq_warnings)
            
            # 7. Market hours and volatility checks
            market_ok, market_warnings = self._check_market_conditions()
            if not market_ok:
                warnings.extend(market_warnings)
            
            # Calculate risk metrics
            risk_metrics = self._calculate_trade_risk_metrics(
                signal, contract, quantity
            )
            
            # Determine overall result
            if errors:
                result = RiskCheckResult.REJECTED
            elif len(warnings) > 3:
                result = RiskCheckResult.REQUIRES_REVIEW
            elif warnings:
                result = RiskCheckResult.WARNING
            else:
                result = RiskCheckResult.APPROVED
            
            # Log risk check result
            self.logger.info(
                f"Risk check for {contract.symbol}: {result.value} "
                f"({len(errors)} errors, {len(warnings)} warnings)"
            )
            
            return result, errors + warnings, risk_metrics
            
        except Exception as e:
            self.logger.error(f"Error in risk check: {e}")
            return RiskCheckResult.REJECTED, [f"Risk check error: {str(e)}"], {}
    
    def _check_position_size_limits(
        self, 
        symbol: str, 
        quantity: Decimal
    ) -> Tuple[bool, List[str]]:
        """Check position size limits"""
        
        errors = []
        
        try:
            # Check individual position limit
            current_position = self.position_manager.get_position(symbol)
            current_qty = Decimal(str(current_position.quantity)) if current_position else Decimal('0')
            new_total_qty = abs(current_qty + quantity)
            
            if new_total_qty > self.account_config.max_position_size:
                errors.append(
                    f"Position size limit exceeded: {new_total_qty} > {self.account_config.max_position_size}"
                )
            
            # Check total number of positions
            all_positions = self.position_manager.get_all_positions()
            if len(all_positions) >= self.risk_config["max_open_positions"]:
                errors.append(
                    f"Maximum open positions limit reached: {len(all_positions)}"
                )
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Position size check error: {str(e)}"]
    
    def _check_concentration_limits(
        self, 
        symbol: str, 
        quantity: Decimal
    ) -> Tuple[bool, List[str]]:
        """Check portfolio concentration limits"""
        
        warnings = []
        
        try:
            # Extract underlying symbol
            underlying = self._extract_underlying(symbol)
            
            # Get current positions for this underlying
            underlying_positions = self.position_manager.get_positions_by_underlying(underlying)
            underlying_value = sum(float(pos.market_value or 0) for pos in underlying_positions)
            
            # Get total portfolio value
            metrics = self.position_manager.calculate_portfolio_metrics()
            total_value = metrics.get('total_market_value', 0)
            
            if total_value > 0:
                concentration = underlying_value / total_value
                max_concentration = float(self.risk_config["max_concentration_pct"])
                
                if concentration > max_concentration:
                    warnings.append(
                        f"High concentration in {underlying}: {concentration:.1%} > {max_concentration:.1%}"
                    )
            
            return len(warnings) == 0, warnings
            
        except Exception as e:
            return False, [f"Concentration check error: {str(e)}"]
    
    def _check_daily_loss_limits(self) -> Tuple[bool, List[str]]:
        """Check daily loss limits"""
        
        errors = []
        
        try:
            # Calculate current daily P&L
            current_pnl = self._calculate_daily_pnl()
            max_loss = self.risk_config["max_daily_loss"]
            
            if current_pnl < -max_loss:
                errors.append(
                    f"Daily loss limit exceeded: ${current_pnl:.2f} < -${max_loss:.2f}"
                )
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Daily loss check error: {str(e)}"]
    
    def _check_greeks_exposure(
        self, 
        contract: OptionContract, 
        quantity: Decimal, 
        side: OrderSide
    ) -> Tuple[bool, List[str]]:
        """Check Greeks exposure limits"""
        
        warnings = []
        
        try:
            # Get current portfolio Greeks
            metrics = self.position_manager.calculate_portfolio_metrics()
            current_delta = Decimal(str(metrics.get('portfolio_delta', 0)))
            current_vega = Decimal(str(metrics.get('portfolio_vega', 0)))
            current_theta = Decimal(str(metrics.get('portfolio_theta', 0)))
            
            # Estimate new Greeks (simplified - would need real option pricing)
            contract_delta = getattr(contract, 'delta', Decimal('0.5'))
            contract_vega = getattr(contract, 'vega', Decimal('10'))
            contract_theta = getattr(contract, 'theta', Decimal('-5'))
            
            multiplier = quantity if side == OrderSide.BUY else -quantity
            
            new_delta = current_delta + (contract_delta * multiplier)
            new_vega = current_vega + (contract_vega * multiplier)
            new_theta = current_theta + (contract_theta * multiplier)
            
            # Check limits
            if abs(new_delta) > self.risk_config["max_portfolio_delta"]:
                warnings.append(
                    f"Portfolio delta limit exceeded: {new_delta:.2f}"
                )
            
            if abs(new_vega) > self.risk_config["max_vega_exposure"]:
                warnings.append(
                    f"Vega exposure limit exceeded: {new_vega:.2f}"
                )
            
            if new_theta < -self.risk_config["max_theta_decay"]:
                warnings.append(
                    f"Theta decay limit exceeded: {new_theta:.2f}"
                )
            
            return len(warnings) == 0, warnings
            
        except Exception as e:
            return False, [f"Greeks check error: {str(e)}"]
    
    def _check_expiration_risk(self, contract: OptionContract) -> Tuple[bool, List[str]]:
        """Check expiration-related risks"""
        
        warnings = []
        
        try:
            if contract.expiry:
                expiry_date = contract.expiry
                if isinstance(expiry_date, str):
                    expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                
                days_to_expiry = (expiry_date - datetime.now()).days
                min_days = int(self.risk_config["min_days_to_expiry"])
                
                if days_to_expiry < min_days:
                    warnings.append(
                        f"Option expires soon: {days_to_expiry} days < {min_days} days minimum"
                    )
                
                # Check for weekend/holiday expiry
                if expiry_date.weekday() >= 5:  # Saturday or Sunday
                    warnings.append("Option expires on weekend - check settlement rules")
            
            return len(warnings) == 0, warnings
            
        except Exception as e:
            return False, [f"Expiration check error: {str(e)}"]
    
    def _check_liquidity_risk(self, contract: OptionContract) -> Tuple[bool, List[str]]:
        """Check liquidity-related risks"""
        
        warnings = []
        
        try:
            # Check volume
            if hasattr(contract, 'volume') and contract.volume is not None:
                if contract.volume < 10:
                    warnings.append(f"Low volume: {contract.volume} contracts")
            
            # Check bid-ask spread
            if contract.bid and contract.ask and contract.bid > 0 and contract.ask > 0:
                spread = float(contract.ask) - float(contract.bid)
                spread_pct = spread / float(contract.ask)
                
                if spread_pct > 0.10:  # 10% spread threshold
                    warnings.append(f"Wide bid-ask spread: {spread_pct:.1%}")
            
            # Check open interest
            if hasattr(contract, 'open_interest') and contract.open_interest is not None:
                if contract.open_interest < 50:
                    warnings.append(f"Low open interest: {contract.open_interest}")
            
            return len(warnings) == 0, warnings
            
        except Exception as e:
            return False, [f"Liquidity check error: {str(e)}"]
    
    def _check_market_conditions(self) -> Tuple[bool, List[str]]:
        """Check market conditions and trading hours"""
        
        warnings = []
        
        try:
            now = datetime.now()
            
            # Check if it's a trading day (simplified)
            if now.weekday() >= 5:  # Weekend
                warnings.append("Trading on weekend - limited liquidity expected")
            
            # Check trading hours (simplified - US market hours)
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            if now < market_open or now > market_close:
                warnings.append("Trading outside regular market hours")
            
            return len(warnings) == 0, warnings
            
        except Exception as e:
            return False, [f"Market conditions check error: {str(e)}"]
    
    def _calculate_trade_risk_metrics(
        self,
        signal: TradeSignal,
        contract: OptionContract,
        quantity: Decimal
    ) -> Dict[str, Any]:
        """Calculate risk metrics for the proposed trade"""
        
        try:
            # Estimate trade value
            price = contract.last_price or contract.ask or Decimal('5.00')
            trade_value = price * quantity
            
            # Get portfolio metrics
            portfolio_metrics = self.position_manager.calculate_portfolio_metrics()
            portfolio_value = portfolio_metrics.get('total_market_value', 0)
            
            # Calculate risk metrics
            position_size_pct = float(trade_value) / max(portfolio_value, 1) if portfolio_value > 0 else 0
            
            return {
                "trade_value": float(trade_value),
                "position_size_percentage": position_size_pct,
                "portfolio_value": portfolio_value,
                "estimated_max_loss": float(trade_value),  # Simplified
                "risk_reward_ratio": 2.0,  # Placeholder
                "probability_of_profit": 0.6,  # Placeholder
                "days_to_expiry": self._get_days_to_expiry(contract),
                "liquidity_score": self._calculate_liquidity_score(contract)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trade risk metrics: {e}")
            return {}
    
    def _calculate_daily_pnl(self) -> Decimal:
        """Calculate current daily P&L"""
        
        try:
            # In a real implementation, this would track P&L from market open
            # For now, use unrealized P&L as proxy
            metrics = self.position_manager.calculate_portfolio_metrics()
            return Decimal(str(metrics.get('total_unrealized_pnl', 0)))
            
        except Exception:
            return Decimal('0')
    
    def _extract_underlying(self, option_symbol: str) -> str:
        """Extract underlying symbol from option symbol"""
        
        try:
            if '  ' in option_symbol:
                return option_symbol.split('  ')[0].strip()
            
            import re
            match = re.match(r'^([A-Z]+)', option_symbol)
            if match:
                return match.group(1)
            
            return option_symbol
            
        except Exception:
            return option_symbol
    
    def _get_days_to_expiry(self, contract: OptionContract) -> int:
        """Get days to expiry for contract"""
        
        try:
            if contract.expiry:
                expiry_date = contract.expiry
                if isinstance(expiry_date, str):
                    expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                
                return (expiry_date - datetime.now()).days
            
            return 0
            
        except Exception:
            return 0
    
    def _calculate_liquidity_score(self, contract: OptionContract) -> float:
        """Calculate liquidity score (0-1, higher is better)"""
        
        try:
            score = 0.0
            
            # Volume component
            volume = getattr(contract, 'volume', 0) or 0
            if volume > 100:
                score += 0.4
            elif volume > 10:
                score += 0.2
            
            # Spread component
            if contract.bid and contract.ask and contract.bid > 0 and contract.ask > 0:
                spread_pct = (float(contract.ask) - float(contract.bid)) / float(contract.ask)
                if spread_pct < 0.05:
                    score += 0.4
                elif spread_pct < 0.10:
                    score += 0.2
            
            # Open interest component
            open_interest = getattr(contract, 'open_interest', 0) or 0
            if open_interest > 500:
                score += 0.2
            elif open_interest > 100:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5  # Default moderate score
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        
        try:
            portfolio_metrics = self.position_manager.calculate_portfolio_metrics()
            daily_pnl = self._calculate_daily_pnl()
            
            # Calculate risk level
            risk_level = RiskLevel.LOW
            if abs(daily_pnl) > self.risk_config["max_daily_loss"] * Decimal('0.8'):
                risk_level = RiskLevel.HIGH
            elif abs(daily_pnl) > self.risk_config["max_daily_loss"] * Decimal('0.5'):
                risk_level = RiskLevel.MEDIUM
            
            return {
                "risk_level": risk_level.value,
                "daily_pnl": float(daily_pnl),
                "daily_loss_limit": float(self.risk_config["max_daily_loss"]),
                "portfolio_value": portfolio_metrics.get('total_market_value', 0),
                "position_count": portfolio_metrics.get('total_positions', 0),
                "portfolio_delta": portfolio_metrics.get('portfolio_delta', 0),
                "portfolio_vega": portfolio_metrics.get('portfolio_vega', 0),
                "portfolio_theta": portfolio_metrics.get('portfolio_theta', 0),
                "risk_metrics": portfolio_metrics.get('risk_metrics', {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating risk summary: {e}")
            return {"error": str(e)}
