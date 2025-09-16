"""
Mock Tiger Brokers API client for development and testing
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import random

from ..config import AccountConfig
from ..models import (
    TigerAccount,
    OptionContract,
    TigerOrder,
    Position,
    Currency,
    OrderType,
    OrderSide,
    OrderStatus,
    OptionType,
)


logger = logging.getLogger(__name__)


class MockTigerClient:
    """Mock Tiger Brokers API client for development and testing"""
    
    def __init__(self, account_config: AccountConfig):
        """Initialize mock Tiger client"""
        self.account_config = account_config
        
        # Mock data storage
        self._orders: Dict[str, TigerOrder] = {}
        self._positions: Dict[str, Position] = {}
        self._account_info = self._generate_mock_account()
        
        logger.info(f"Initialized Mock Tiger client for account: {account_config.name}")
    
    def _generate_mock_account(self) -> TigerAccount:
        """Generate mock account information"""
        return TigerAccount(
            account=self.account_config.account,
            currency=Currency(self.account_config.default_currency),
            buying_power=Decimal('100000.00'),
            cash=Decimal('50000.00'),
            market_value=Decimal('75000.00'),
            net_liquidation=Decimal('125000.00'),
        )
    
    def test_connection(self) -> bool:
        """Mock connection test - always returns True"""
        logger.info(f"Mock connection test successful for account: {self.account_config.name}")
        return True
    
    # Account Information Methods
    
    def get_account_info(self) -> Optional[TigerAccount]:
        """Get mock account information"""
        return self._account_info
    
    def get_positions(self) -> List[Position]:
        """Get mock positions"""
        return list(self._positions.values())
    
    # Quote Data Methods
    
    def get_option_expirations(self, symbol: str) -> List[datetime]:
        """Get mock option expiration dates"""
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        expirations = []
        
        # Generate weekly and monthly expirations
        for weeks in [1, 2, 3, 4, 8, 12, 16, 20]:
            expiry = base_date + timedelta(weeks=weeks)
            # Adjust to Friday
            expiry = expiry + timedelta(days=(4 - expiry.weekday()) % 7)
            expirations.append(expiry)
        
        return sorted(expirations)
    
    def get_option_chain(self, symbol: str, expiry: datetime) -> List[OptionContract]:
        """Get mock option chain"""
        # Mock current stock price
        current_price = Decimal('150.00')  # Mock price for testing
        
        contracts = []
        
        # Generate strikes around current price
        for strike_offset in range(-10, 11):
            strike = current_price + Decimal(str(strike_offset * 5))
            
            # Generate call option
            call_symbol = f"{symbol}  {expiry.strftime('%y%m%d')}C{strike:08.0f}000"
            call_contract = self._generate_mock_option_contract(
                call_symbol, symbol, strike, expiry, OptionType.CALL, current_price
            )
            contracts.append(call_contract)
            
            # Generate put option
            put_symbol = f"{symbol}  {expiry.strftime('%y%m%d')}P{strike:08.0f}000"
            put_contract = self._generate_mock_option_contract(
                put_symbol, symbol, strike, expiry, OptionType.PUT, current_price
            )
            contracts.append(put_contract)
        
        return contracts
    
    def _generate_mock_option_contract(
        self,
        symbol: str,
        underlying: str,
        strike: Decimal,
        expiry: datetime,
        option_type: OptionType,
        underlying_price: Decimal
    ) -> OptionContract:
        """Generate a mock option contract with realistic data"""
        
        # Calculate time to expiry in years
        days_to_expiry = (expiry - datetime.now()).days
        time_to_expiry = max(days_to_expiry / 365.0, 0.01)
        
        # Mock implied volatility
        iv = Decimal(str(random.uniform(0.15, 0.35)))
        
        # Simple Black-Scholes approximation for mock prices
        moneyness = underlying_price / strike
        if option_type == OptionType.CALL:
            intrinsic = max(underlying_price - strike, Decimal('0'))
            time_value = Decimal(str(random.uniform(0.5, 5.0))) * Decimal(str(time_to_expiry))
        else:
            intrinsic = max(strike - underlying_price, Decimal('0'))
            time_value = Decimal(str(random.uniform(0.5, 5.0))) * Decimal(str(time_to_expiry))
        
        theoretical_price = intrinsic + time_value
        
        # Generate bid/ask around theoretical price
        spread_pct = Decimal(str(random.uniform(0.02, 0.08)))
        spread = theoretical_price * spread_pct
        
        bid = max(theoretical_price - spread / 2, Decimal('0.01'))
        ask = theoretical_price + spread / 2
        last = bid + (ask - bid) * Decimal(str(random.random()))
        
        # Mock Greeks
        if option_type == OptionType.CALL:
            delta = Decimal(str(min(0.99, max(0.01, 0.5 + float(moneyness - 1) * 2))))
        else:
            delta = Decimal(str(max(-0.99, min(-0.01, -0.5 + float(moneyness - 1) * 2))))
        
        gamma = Decimal(str(random.uniform(0.001, 0.05)))
        theta = Decimal(str(random.uniform(-0.1, -0.01)))
        vega = Decimal(str(random.uniform(0.05, 0.3)))
        
        return OptionContract(
            symbol=symbol,
            underlying_symbol=underlying,
            strike=strike,
            expiry=expiry,
            option_type=option_type,
            multiplier=100,
            bid=bid,
            ask=ask,
            last=last,
            volume=random.randint(0, 1000),
            open_interest=random.randint(0, 5000),
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            implied_volatility=iv,
        )
    
    def get_option_quotes(self, symbols: List[str]) -> Dict[str, OptionContract]:
        """Get mock option quotes"""
        quotes = {}
        
        for symbol in symbols:
            # Parse symbol to extract details (simplified)
            underlying = symbol.split()[0] if ' ' in symbol else 'AAPL'
            strike = Decimal('150.00')  # Mock strike
            expiry = datetime.now() + timedelta(days=30)  # Mock expiry
            option_type = OptionType.CALL if 'C' in symbol else OptionType.PUT
            
            contract = self._generate_mock_option_contract(
                symbol, underlying, strike, expiry, option_type, Decimal('150.00')
            )
            quotes[symbol] = contract
        
        return quotes

    def get_account_summary(self) -> Dict[str, Any]:
        """Get mock account summary"""
        return {
            "net_liquidation": 100000.0,
            "total_cash": 50000.0,
            "available_funds": 45000.0,
            "buying_power": 90000.0,
            "currency": "USD"
        }

    def get_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get mock trade history"""
        trades = []
        for i in range(min(limit, 10)):  # Generate up to 10 mock trades
            trade = {
                "trade_time": (datetime.now() - timedelta(days=i)).isoformat(),
                "symbol": f"AAPL  250117C00150000",
                "underlying": "AAPL",
                "side": "buy" if i % 2 == 0 else "sell",
                "quantity": random.randint(1, 10),
                "price": round(random.uniform(1.0, 5.0), 2),
                "commission": round(random.uniform(0.5, 2.0), 2),
                "realized_pnl": round(random.uniform(-100, 100), 2)
            }
            trades.append(trade)
        return trades

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order (mock implementation)"""
        logger.info(f"Mock: Cancelling order {order_id}")
        return {
            "order_id": order_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat()
        }

    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position (mock implementation)"""
        logger.info(f"Mock: Closing position {symbol}")
        return {
            "symbol": symbol,
            "status": "closed",
            "closed_at": datetime.now().isoformat()
        }

    def get_option_chain(self, symbol: str) -> List[Dict[str, Any]]:
        """Get option chain for symbol (mock implementation)"""

        try:
            # Generate mock option chain data
            option_chain = []

            # Generate call options
            for strike in [140, 145, 150, 155, 160]:
                call_contract = {
                    "symbol": f"{symbol}  250117C{strike:08.0f}000",
                    "underlying": symbol,
                    "strike": strike,
                    "expiry": "2025-01-17T00:00:00",
                    "option_type": "call",
                    "bid": 2.50,
                    "ask": 2.70,
                    "last_price": 2.60,
                    "volume": 100,
                    "open_interest": 500
                }
                option_chain.append(call_contract)

            # Generate put options
            for strike in [140, 145, 150, 155, 160]:
                put_contract = {
                    "symbol": f"{symbol}  250117P{strike:08.0f}000",
                    "underlying": symbol,
                    "strike": strike,
                    "expiry": "2025-01-17T00:00:00",
                    "option_type": "put",
                    "bid": 1.80,
                    "ask": 2.00,
                    "last_price": 1.90,
                    "volume": 80,
                    "open_interest": 300
                }
                option_chain.append(put_contract)

            logger.info(f"Generated mock option chain for {symbol}: {len(option_chain)} contracts")
            return option_chain

        except Exception as e:
            logger.error(f"Failed to generate mock option chain for {symbol}: {e}")
            return []

    # Trading Methods
    
    def place_order(
        self,
        symbol: str,
        order_type: OrderType,
        side: OrderSide,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "day"
    ) -> Optional[str]:
        """Place a mock order"""
        order_id = str(uuid.uuid4())
        
        # Create mock order
        order = TigerOrder(
            order_id=order_id,
            account=self.account_config.account,
            symbol=symbol,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            status=OrderStatus.SUBMITTED,
            filled_quantity=Decimal('0'),
            avg_fill_price=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            commission=None,
            currency=Currency(self.account_config.default_currency),
        )
        
        self._orders[order_id] = order
        
        # Simulate order fill for market orders
        if order_type == OrderType.MARKET:
            self._simulate_order_fill(order_id)
        
        logger.info(f"Mock order placed: {order_id} for {symbol}")
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a mock order"""
        if order_id in self._orders:
            order = self._orders[order_id]
            if order.status in [OrderStatus.SUBMITTED, OrderStatus.PENDING]:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
                logger.info(f"Mock order cancelled: {order_id}")
                return True
        
        logger.warning(f"Cannot cancel order: {order_id}")
        return False
    
    def get_orders(self, status: Optional[str] = None) -> List[TigerOrder]:
        """Get mock orders"""
        orders = list(self._orders.values())
        
        if status:
            orders = [order for order in orders if order.status.value == status]
        
        return orders
    
    def _simulate_order_fill(self, order_id: str):
        """Simulate order fill for testing"""
        if order_id not in self._orders:
            return
        
        order = self._orders[order_id]
        
        # Simulate partial or full fill
        fill_ratio = random.uniform(0.8, 1.0)  # 80-100% fill
        filled_qty = order.quantity * Decimal(str(fill_ratio))
        
        # Mock fill price
        if order.price:
            fill_price = order.price * Decimal(str(random.uniform(0.99, 1.01)))
        else:
            fill_price = Decimal('150.00')  # Mock market price
        
        order.filled_quantity = filled_qty
        order.avg_fill_price = fill_price
        order.status = OrderStatus.FILLED if filled_qty == order.quantity else OrderStatus.PARTIAL_FILLED
        order.updated_at = datetime.now()
        
        # Update positions
        self._update_position(order.symbol, order.side, filled_qty, fill_price)
    
    def _update_position(self, symbol: str, side: OrderSide, quantity: Decimal, price: Decimal):
        """Update mock position"""
        if symbol not in self._positions:
            self._positions[symbol] = Position(
                account=self.account_config.account,
                symbol=symbol,
                quantity=Decimal('0'),
                avg_cost=Decimal('0'),
                market_price=price,
                market_value=Decimal('0'),
                unrealized_pnl=Decimal('0'),
                realized_pnl=Decimal('0'),
                currency=Currency(self.account_config.default_currency),
                multiplier=100 if 'option' in symbol.lower() else 1,
            )
        
        position = self._positions[symbol]
        
        # Update position quantity
        if side == OrderSide.BUY:
            new_quantity = position.quantity + quantity
        else:
            new_quantity = position.quantity - quantity
        
        # Update average cost
        if new_quantity != 0:
            total_cost = position.quantity * position.avg_cost + quantity * price
            position.avg_cost = total_cost / new_quantity
        
        position.quantity = new_quantity
        position.market_price = price
        position.market_value = new_quantity * price * position.multiplier
        
        # Remove position if quantity is zero
        if position.quantity == 0:
            del self._positions[symbol]
