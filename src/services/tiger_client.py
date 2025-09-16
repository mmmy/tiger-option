"""
Tiger Brokers API client wrapper
"""

import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

try:
    from tigeropen.common.consts import Language, Market, TimelinePeriod, QuoteRight
    from tigeropen.common.response import TigerResponse
    from tigeropen.quote.quote_client import QuoteClient
    from tigeropen.trade.trade_client import TradeClient
    from tigeropen.tiger_open_config import TigerOpenClientConfig
    from tigeropen.common.util.signature_utils import read_private_key
    TIGEROPEN_AVAILABLE = True
except ImportError:
    # Mock classes for when tigeropen is not available
    TIGEROPEN_AVAILABLE = False

    class Language:
        en_US = "en_US"
        zh_CN = "zh_CN"
        zh_TW = "zh_TW"

    class Market:
        US = "US"
        HK = "HK"

    class QuoteClient:
        def __init__(self, config): pass

    class TradeClient:
        def __init__(self, config): pass

    class TigerOpenClientConfig:
        def __init__(self, sandbox_debug=True): pass

    def read_private_key(path):
        return "mock_private_key"

from ..config import AccountConfig
from ..models import (
    TigerAccount,
    OptionContract,
    TigerOrder,
    Position,
    Market as MarketEnum,
    Currency,
    OrderType,
    OrderSide,
    OptionType,
)


logger = logging.getLogger(__name__)


class TigerClientError(Exception):
    """Tiger client error"""
    pass


class TigerClient:
    """Tiger Brokers API client wrapper"""
    
    def __init__(self, account_config: AccountConfig):
        """Initialize Tiger client with account configuration"""
        if not TIGEROPEN_AVAILABLE:
            raise TigerClientError("tigeropen library is not available. Please install it or use mock mode.")

        self.account_config = account_config
        self.client_config = self._create_client_config()

        # Initialize clients
        self.quote_client = QuoteClient(self.client_config)
        self.trade_client = TradeClient(self.client_config)

        logger.info(f"Initialized Tiger client for account: {account_config.name}")
    
    def _create_client_config(self) -> TigerOpenClientConfig:
        """Create Tiger client configuration"""
        try:
            # Create client config
            client_config = TigerOpenClientConfig(
                sandbox_debug=self.account_config.sandbox_debug
            )
            
            # Set authentication
            client_config.private_key = read_private_key(
                str(self.account_config.private_key_file)
            )
            client_config.tiger_id = self.account_config.tiger_id
            client_config.account = self.account_config.account
            
            # Set language
            if self.account_config.language == "en_US":
                client_config.language = Language.en_US
            elif self.account_config.language == "zh_CN":
                client_config.language = Language.zh_CN
            elif self.account_config.language == "zh_TW":
                client_config.language = Language.zh_TW
            else:
                client_config.language = Language.en_US
            
            return client_config
            
        except Exception as e:
            raise TigerClientError(f"Failed to create client config: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to Tiger API"""
        try:
            # Test quote client
            market_status = self.quote_client.get_market_status(Market.US)
            if not market_status:
                return False
            
            # Test trade client
            accounts = self.trade_client.get_managed_accounts()
            if not accounts:
                return False
            
            logger.info(f"Connection test successful for account: {self.account_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed for account {self.account_config.name}: {e}")
            return False
    
    # Account Information Methods
    
    def get_account_info(self) -> Optional[TigerAccount]:
        """Get account information"""
        try:
            # Get account summary
            account_summary = self.trade_client.get_account_summary()
            if not account_summary:
                return None
            
            # Extract account data
            account_data = account_summary.iloc[0] if not account_summary.empty else None
            if not account_data:
                return None
            
            return TigerAccount(
                account=self.account_config.account,
                currency=Currency(self.account_config.default_currency),
                buying_power=Decimal(str(account_data.get('buyingPower', 0))),
                cash=Decimal(str(account_data.get('cash', 0))),
                market_value=Decimal(str(account_data.get('marketValue', 0))),
                net_liquidation=Decimal(str(account_data.get('netLiquidation', 0))),
            )
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
    
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            positions_df = self.trade_client.get_positions()
            if positions_df is None or positions_df.empty:
                return []
            
            positions = []
            for _, row in positions_df.iterrows():
                position = Position(
                    account=self.account_config.account,
                    symbol=row.get('symbol', ''),
                    quantity=Decimal(str(row.get('quantity', 0))),
                    avg_cost=Decimal(str(row.get('averageCost', 0))),
                    market_price=Decimal(str(row.get('marketPrice', 0))) if row.get('marketPrice') else None,
                    market_value=Decimal(str(row.get('marketValue', 0))) if row.get('marketValue') else None,
                    unrealized_pnl=Decimal(str(row.get('unrealizedPnl', 0))) if row.get('unrealizedPnl') else None,
                    realized_pnl=Decimal(str(row.get('realizedPnl', 0))) if row.get('realizedPnl') else None,
                    currency=Currency(self.account_config.default_currency),
                    multiplier=int(row.get('multiplier', 1)),
                )
                positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    # Quote Data Methods
    
    def get_option_expirations(self, symbol: str) -> List[datetime]:
        """Get option expiration dates for a symbol"""
        try:
            expirations_df = self.quote_client.get_option_expirations(symbols=[symbol])
            if expirations_df is None or expirations_df.empty:
                return []
            
            expirations = []
            for _, row in expirations_df.iterrows():
                timestamp = row.get('timestamp')
                if timestamp:
                    expiry = datetime.fromtimestamp(timestamp / 1000)  # Convert from milliseconds
                    expirations.append(expiry)
            
            return sorted(expirations)
            
        except Exception as e:
            logger.error(f"Failed to get option expirations for {symbol}: {e}")
            return []
    
    def get_option_chain(self, symbol: str, expiry: datetime) -> List[OptionContract]:
        """Get option chain for a symbol and expiry"""
        try:
            # Convert datetime to timestamp
            expiry_timestamp = int(expiry.timestamp() * 1000)
            
            # Get option chain
            chain_df = self.quote_client.get_option_chain(symbol, expiry_timestamp)
            if chain_df is None or chain_df.empty:
                return []
            
            contracts = []
            for _, row in chain_df.iterrows():
                # Parse option symbol to extract details
                option_symbol = row.get('symbol', '')
                strike = Decimal(str(row.get('strike', 0)))
                
                # Determine option type from symbol
                option_type = OptionType.CALL if 'C' in option_symbol else OptionType.PUT
                
                contract = OptionContract(
                    symbol=option_symbol,
                    underlying_symbol=symbol,
                    strike=strike,
                    expiry=expiry,
                    option_type=option_type,
                    multiplier=int(row.get('multiplier', 100)),
                    bid=Decimal(str(row.get('bid', 0))) if row.get('bid') else None,
                    ask=Decimal(str(row.get('ask', 0))) if row.get('ask') else None,
                    last=Decimal(str(row.get('last', 0))) if row.get('last') else None,
                    volume=int(row.get('volume', 0)) if row.get('volume') else None,
                    open_interest=int(row.get('openInterest', 0)) if row.get('openInterest') else None,
                    delta=Decimal(str(row.get('delta', 0))) if row.get('delta') else None,
                    gamma=Decimal(str(row.get('gamma', 0))) if row.get('gamma') else None,
                    theta=Decimal(str(row.get('theta', 0))) if row.get('theta') else None,
                    vega=Decimal(str(row.get('vega', 0))) if row.get('vega') else None,
                    implied_volatility=Decimal(str(row.get('impliedVol', 0))) if row.get('impliedVol') else None,
                )
                contracts.append(contract)
            
            return contracts
            
        except Exception as e:
            logger.error(f"Failed to get option chain for {symbol} expiry {expiry}: {e}")
            return []
    
    def get_option_quotes(self, symbols: List[str]) -> Dict[str, OptionContract]:
        """Get option quotes for multiple symbols"""
        try:
            quotes_df = self.quote_client.get_option_briefs(symbols)
            if quotes_df is None or quotes_df.empty:
                return {}
            
            quotes = {}
            for _, row in quotes_df.iterrows():
                symbol = row.get('symbol', '')
                if not symbol:
                    continue
                
                # Parse option details from symbol (simplified)
                # In real implementation, you'd need proper option symbol parsing
                strike = Decimal(str(row.get('strike', 0)))
                option_type = OptionType.CALL if 'C' in symbol else OptionType.PUT
                
                contract = OptionContract(
                    symbol=symbol,
                    underlying_symbol=symbol.split()[0],  # Simplified extraction
                    strike=strike,
                    expiry=datetime.now(),  # Would need proper parsing
                    option_type=option_type,
                    bid=Decimal(str(row.get('bid', 0))) if row.get('bid') else None,
                    ask=Decimal(str(row.get('ask', 0))) if row.get('ask') else None,
                    last=Decimal(str(row.get('last', 0))) if row.get('last') else None,
                    volume=int(row.get('volume', 0)) if row.get('volume') else None,
                    open_interest=int(row.get('openInterest', 0)) if row.get('openInterest') else None,
                )
                quotes[symbol] = contract
            
            return quotes
            
        except Exception as e:
            logger.error(f"Failed to get option quotes: {e}")
            return {}

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
        """Place an order and return order ID"""
        try:
            from tigeropen.trade.request.model import OrderParams
            from tigeropen.common.consts import OrderType as TigerOrderType

            # Convert our enums to Tiger enums
            tiger_order_type = self._convert_order_type(order_type)
            tiger_side = side.value.upper()

            # Create order parameters
            order = OrderParams()
            order.account = self.account_config.account
            order.symbol = symbol
            order.order_type = tiger_order_type
            order.action = tiger_side
            order.total_quantity = int(quantity)

            if price:
                order.limit_price = float(price)
            if stop_price:
                order.aux_price = float(stop_price)

            # Place order
            result = self.trade_client.place_order(order)
            if result and hasattr(result, 'order_id'):
                logger.info(f"Order placed successfully: {result.order_id}")
                return str(result.order_id)

            return None

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            result = self.trade_client.cancel_order(order_id)
            if result:
                logger.info(f"Order cancelled successfully: {order_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_orders(self, status: Optional[str] = None) -> List[TigerOrder]:
        """Get orders with optional status filter"""
        try:
            orders_df = self.trade_client.get_orders()
            if orders_df is None or orders_df.empty:
                return []

            orders = []
            for _, row in orders_df.iterrows():
                if status and row.get('status') != status:
                    continue

                order = TigerOrder(
                    order_id=str(row.get('orderId', '')),
                    account=self.account_config.account,
                    symbol=row.get('symbol', ''),
                    order_type=self._convert_tiger_order_type(row.get('orderType', '')),
                    side=OrderSide(row.get('action', '').lower()),
                    quantity=Decimal(str(row.get('totalQuantity', 0))),
                    price=Decimal(str(row.get('limitPrice', 0))) if row.get('limitPrice') else None,
                    stop_price=Decimal(str(row.get('auxPrice', 0))) if row.get('auxPrice') else None,
                    time_in_force=row.get('timeInForce', 'day').lower(),
                    status=self._convert_tiger_order_status(row.get('status', '')),
                    filled_quantity=Decimal(str(row.get('filledQuantity', 0))),
                    avg_fill_price=Decimal(str(row.get('avgFillPrice', 0))) if row.get('avgFillPrice') else None,
                    created_at=datetime.fromtimestamp(row.get('createTime', 0) / 1000) if row.get('createTime') else datetime.now(),
                    updated_at=datetime.fromtimestamp(row.get('updateTime', 0) / 1000) if row.get('updateTime') else None,
                    commission=Decimal(str(row.get('commission', 0))) if row.get('commission') else None,
                    currency=Currency(self.account_config.default_currency),
                )
                orders.append(order)

            return orders

        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []

    # Helper Methods

    def _convert_order_type(self, order_type: OrderType) -> str:
        """Convert our OrderType enum to Tiger order type"""
        mapping = {
            OrderType.MARKET: "MKT",
            OrderType.LIMIT: "LMT",
            OrderType.STOP: "STP",
            OrderType.STOP_LIMIT: "STP_LMT",
            OrderType.TRAILING_STOP: "TRAIL",
        }
        return mapping.get(order_type, "LMT")

    def _convert_tiger_order_type(self, tiger_order_type: str) -> OrderType:
        """Convert Tiger order type to our OrderType enum"""
        mapping = {
            "MKT": OrderType.MARKET,
            "LMT": OrderType.LIMIT,
            "STP": OrderType.STOP,
            "STP_LMT": OrderType.STOP_LIMIT,
            "TRAIL": OrderType.TRAILING_STOP,
        }
        return mapping.get(tiger_order_type, OrderType.LIMIT)

    def _convert_tiger_order_status(self, tiger_status: str) -> str:
        """Convert Tiger order status to our standard status"""
        mapping = {
            "PendingSubmit": "pending",
            "Submitted": "submitted",
            "Filled": "filled",
            "Cancelled": "cancelled",
            "Rejected": "rejected",
            "PartiallyFilled": "partial_filled",
        }
        return mapping.get(tiger_status, "unknown")
