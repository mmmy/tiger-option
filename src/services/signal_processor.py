"""
Signal processing service for handling validated trading signals
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from ..models import (
    TradeSignal,
    SignalValidationResult,
    WebhookSignal,
    OptionContract,
    OrderType,
    OrderSide
)
from ..config import AccountConfig
from .signal_validator import get_signal_validator
from .auth_service import get_auth_service
from .option_selector import OptionSelector, SelectionStrategy
from .order_strategy import OrderStrategyService, OrderStrategy
from .position_manager import PositionManager
from .risk_manager import RiskManager, RiskCheckResult


logger = logging.getLogger(__name__)


class SignalProcessingError(Exception):
    """Signal processing error"""
    pass


class SignalProcessor:
    """Service for processing validated trading signals"""
    
    def __init__(self):
        """Initialize signal processor"""
        self.validator = get_signal_validator()
        self.auth_service = get_auth_service()

        # Signal processing queue (in-memory for now)
        self._processing_queue: List[TradeSignal] = []
        self._processing_status: Dict[str, str] = {}

        # Account-specific services cache
        self._account_services: Dict[str, Dict[str, Any]] = {}

        logger.info("Signal processor initialized")

    def _get_account_services(self, account_name: str) -> Optional[Dict[str, Any]]:
        """Get or create account-specific services"""

        if account_name not in self._account_services:
            account_config = self.auth_service.get_account_config(account_name)
            if not account_config:
                return None

            # Initialize account-specific services
            position_manager = PositionManager(account_config)
            risk_manager = RiskManager(account_config, position_manager)
            option_selector = OptionSelector(account_config)
            order_strategy = OrderStrategyService(account_config)

            self._account_services[account_name] = {
                "config": account_config,
                "position_manager": position_manager,
                "risk_manager": risk_manager,
                "option_selector": option_selector,
                "order_strategy": order_strategy
            }

        return self._account_services[account_name]

    async def process_webhook_signal(
        self,
        signal: WebhookSignal,
        account_config: AccountConfig,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a webhook signal end-to-end"""
        
        signal_id = request_id or f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Step 1: Validate signal
            validation_result = self.validator.validate_signal(signal, account_config)
            
            if not validation_result.is_valid:
                logger.warning(f"Signal validation failed [{signal_id}]: {validation_result.errors}")
                return {
                    "signal_id": signal_id,
                    "status": "validation_failed",
                    "validation_result": validation_result.dict(),
                    "processed_at": datetime.now().isoformat()
                }
            
            # Step 2: Convert to trade signal
            trade_signal = self.validator.convert_to_trade_signal(
                signal, account_config, signal_id
            )
            
            # Step 3: Queue for processing
            await self._queue_signal_for_processing(trade_signal)
            
            logger.info(f"Signal queued for processing [{signal_id}]: {trade_signal.symbol} {trade_signal.action}")
            
            return {
                "signal_id": signal_id,
                "status": "queued",
                "trade_signal": {
                    "symbol": trade_signal.symbol,
                    "action": trade_signal.action,
                    "quantity": str(trade_signal.quantity) if trade_signal.quantity else None,
                    "order_type": trade_signal.order_type,
                },
                "validation_result": validation_result.dict(),
                "queued_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook signal [{signal_id}]: {e}")
            raise SignalProcessingError(f"Failed to process signal: {str(e)}")
    
    async def _queue_signal_for_processing(self, trade_signal: TradeSignal):
        """Queue a trade signal for processing"""
        
        # Add to processing queue
        self._processing_queue.append(trade_signal)
        self._processing_status[trade_signal.signal_id] = "queued"
        
        # In a real implementation, this would:
        # 1. Add to a proper message queue (Redis, RabbitMQ, etc.)
        # 2. Persist to database
        # 3. Trigger background processing
        
        logger.debug(f"Signal queued: {trade_signal.signal_id}")
    
    async def process_queued_signals(self) -> Dict[str, Any]:
        """Process all queued signals (placeholder implementation)"""
        
        processed_count = 0
        failed_count = 0
        results = []
        
        # Process signals from queue
        while self._processing_queue:
            trade_signal = self._processing_queue.pop(0)
            
            try:
                result = await self._process_single_signal(trade_signal)
                results.append(result)
                
                if result["status"] == "processed":
                    processed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process signal {trade_signal.signal_id}: {e}")
                failed_count += 1
                results.append({
                    "signal_id": trade_signal.signal_id,
                    "status": "error",
                    "error": str(e),
                    "processed_at": datetime.now().isoformat()
                })
        
        return {
            "processed_count": processed_count,
            "failed_count": failed_count,
            "total_count": processed_count + failed_count,
            "results": results,
            "processed_at": datetime.now().isoformat()
        }
    
    async def _process_single_signal(self, trade_signal: TradeSignal) -> Dict[str, Any]:
        """Process a single trade signal with actual trading logic"""

        signal_id = trade_signal.signal_id
        logger.info(f"Processing single signal: {signal_id}, action: {trade_signal.action}")

        try:
            # Update status
            self._processing_status[signal_id] = "processing"

            # Get Tiger client for the account
            client = self.auth_service.get_client(trade_signal.account_name)
            if not client:
                raise SignalProcessingError(f"Failed to get client for account: {trade_signal.account_name}")

            # Get account configuration
            account_config = self.auth_service.get_account_config(trade_signal.account_name)
            if not account_config:
                raise SignalProcessingError(f"Failed to get account config for: {trade_signal.account_name}")

            # Execute trading logic based on action
            if trade_signal.action.lower() in ["buy", "sell"]:
                result = await self._execute_option_trade(trade_signal, client, account_config)
            elif trade_signal.action.lower() == "close":
                result = await self._execute_close_position(trade_signal, client, account_config)
            elif trade_signal.action.lower() == "close_all":
                result = await self._execute_close_all_positions(trade_signal, client, account_config)
            else:
                raise SignalProcessingError(f"Unknown action: {trade_signal.action}")

            # Update status
            self._processing_status[signal_id] = "completed"

            logger.info(f"Signal processed successfully [{signal_id}]: {result.get('message', 'Success')}")
            return result

        except Exception as e:
            self._processing_status[signal_id] = "failed"
            logger.error(f"Failed to process signal [{signal_id}]: {e}")

            return {
                "signal_id": signal_id,
                "status": "failed",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    def get_signal_status(self, signal_id: str) -> Optional[str]:
        """Get processing status of a signal"""
        return self._processing_status.get(signal_id)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        
        status_counts = {}
        for status in self._processing_status.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "queue_length": len(self._processing_queue),
            "total_signals": len(self._processing_status),
            "status_counts": status_counts,
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_completed_signals(self) -> int:
        """Clear completed signals from status tracking"""
        
        completed_signals = [
            signal_id for signal_id, status in self._processing_status.items()
            if status in ["completed", "failed"]
        ]
        
        for signal_id in completed_signals:
            del self._processing_status[signal_id]
        
        logger.info(f"Cleared {len(completed_signals)} completed signals from tracking")
        return len(completed_signals)
    
    async def validate_and_process_signal(
        self,
        signal: WebhookSignal,
        account_name: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convenience method to validate and process a signal"""
        
        # Get account configuration
        account_config = self.auth_service.get_enabled_account_config(account_name)
        if not account_config:
            raise SignalProcessingError(f"Account not found or disabled: {account_name}")
        
        # Process the signal
        return await self.process_webhook_signal(signal, account_config, request_id)

    async def _execute_option_trade(
        self,
        trade_signal: TradeSignal,
        client,
        account_config: AccountConfig
    ) -> Dict[str, Any]:
        """Execute option trade (buy/sell)"""

        try:
            logger.info(f"Executing option trade for signal: {trade_signal.signal_id}, symbol: {trade_signal.symbol}, action: {trade_signal.action}")

            # Get account services
            services = self._get_account_services(trade_signal.account_name)
            if not services:
                raise SignalProcessingError("Failed to get account services")

            logger.info(f"Account services initialized for: {trade_signal.account_name}")

            # Get current market price (mock for now)
            current_price = trade_signal.price or Decimal('150.00')

            # Step 1: Get option chain
            option_chain = await self._get_option_chain(trade_signal.symbol, client)
            if not option_chain:
                raise SignalProcessingError("No option chain available")

            # Step 2: Select option contract
            selected_contract = services["option_selector"].select_option_contract(
                trade_signal, option_chain, current_price, SelectionStrategy.ATM
            )
            if not selected_contract:
                raise SignalProcessingError("No suitable option contract found")

            # Step 3: Determine position size
            suggested_quantity = services["position_manager"].suggest_position_sizing(
                selected_contract.symbol, trade_signal.quantity
            )

            # Step 4: Risk check
            risk_result, risk_messages, risk_metrics = services["risk_manager"].check_trade_risk(
                trade_signal, selected_contract, suggested_quantity
            )
            if risk_result == RiskCheckResult.REJECTED:
                raise SignalProcessingError(f"Trade rejected by risk management: {'; '.join(risk_messages)}")

            # Step 5: Create order
            order_params = services["order_strategy"].create_order(
                trade_signal, selected_contract, OrderStrategy.LIMIT_MIDPOINT, suggested_quantity
            )
            if not order_params:
                raise SignalProcessingError("Failed to create order parameters")

            # Step 6: Place order
            order_id = client.place_order(
                symbol=order_params["symbol"],
                order_type=OrderType(order_params["order_type"]),
                side=OrderSide(order_params["side"]),
                quantity=Decimal(str(order_params["quantity"])),
                price=Decimal(str(order_params["price"])) if order_params.get("price") else None,
                stop_price=Decimal(str(order_params["stop_price"])) if order_params.get("stop_price") else None,
                time_in_force=order_params.get("time_in_force", "day")
            )

            if not order_id:
                raise SignalProcessingError("Failed to place order with broker")

            # Update position manager
            services["position_manager"].update_position_after_order(
                selected_contract.symbol, order_params["side"], suggested_quantity, order_id
            )

            return {
                "signal_id": trade_signal.signal_id,
                "status": "processed",
                "account_name": trade_signal.account_name,
                "symbol": trade_signal.symbol,
                "action": trade_signal.action,
                "selected_contract": selected_contract.symbol,
                "quantity": float(suggested_quantity),
                "order_price": float(order_params["price"]) if order_params.get("price") else None,
                "order_id": order_id,
                "risk_result": risk_result.value,
                "risk_messages": risk_messages,
                "processed_at": datetime.now().isoformat(),
                "message": f"Option trade executed successfully: {selected_contract.symbol}"
            }

        except Exception as e:
            logger.error(f"Failed to execute option trade: {e}")
            raise SignalProcessingError(f"Option trade execution failed: {str(e)}")

    async def _execute_close_position(
        self,
        trade_signal: TradeSignal,
        client,
        account_config: AccountConfig
    ) -> Dict[str, Any]:
        """Execute close position"""

        try:
            # Get account services
            services = self._get_account_services(trade_signal.account_name)
            if not services:
                raise SignalProcessingError("Failed to get account services")

            # Get current positions
            positions = client.get_positions()
            if not positions:
                return {
                    "signal_id": trade_signal.signal_id,
                    "status": "processed",
                    "account_name": trade_signal.account_name,
                    "symbol": trade_signal.symbol,
                    "action": trade_signal.action,
                    "message": "No positions to close",
                    "processed_at": datetime.now().isoformat()
                }

            # Find positions for the symbol
            symbol_positions = [p for p in positions if trade_signal.symbol in p.get('symbol', '')]

            if not symbol_positions:
                return {
                    "signal_id": trade_signal.signal_id,
                    "status": "processed",
                    "account_name": trade_signal.account_name,
                    "symbol": trade_signal.symbol,
                    "action": trade_signal.action,
                    "message": f"No positions found for symbol {trade_signal.symbol}",
                    "processed_at": datetime.now().isoformat()
                }

            # Close each position
            closed_orders = []
            for position in symbol_positions:
                position_symbol = position.get('symbol')
                position_quantity = abs(Decimal(str(position.get('quantity', 0))))

                if position_quantity <= 0:
                    continue

                # Determine close side (opposite of current position)
                current_side = position.get('side', 'long')
                close_side = OrderSide.SELL if current_side.lower() == 'long' else OrderSide.BUY

                # Place close order
                order_id = client.place_order(
                    symbol=position_symbol,
                    order_type=OrderType.MARKET,
                    side=close_side,
                    quantity=position_quantity,
                    time_in_force="day"
                )

                if order_id:
                    closed_orders.append({
                        "symbol": position_symbol,
                        "quantity": float(position_quantity),
                        "side": close_side.value,
                        "order_id": order_id
                    })

                    # Update position manager
                    services["position_manager"].update_position_after_order(
                        position_symbol, close_side.value, position_quantity, order_id
                    )

            return {
                "signal_id": trade_signal.signal_id,
                "status": "processed",
                "account_name": trade_signal.account_name,
                "symbol": trade_signal.symbol,
                "action": trade_signal.action,
                "closed_orders": closed_orders,
                "message": f"Closed {len(closed_orders)} positions for {trade_signal.symbol}",
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            raise SignalProcessingError(f"Close position failed: {str(e)}")

    async def _execute_close_all_positions(
        self,
        trade_signal: TradeSignal,
        client,
        account_config: AccountConfig
    ) -> Dict[str, Any]:
        """Execute close all positions"""

        try:
            # Get account services
            services = self._get_account_services(trade_signal.account_name)
            if not services:
                raise SignalProcessingError("Failed to get account services")

            # Get all current positions
            positions = client.get_positions()
            if not positions:
                return {
                    "signal_id": trade_signal.signal_id,
                    "status": "processed",
                    "account_name": trade_signal.account_name,
                    "action": trade_signal.action,
                    "message": "No positions to close",
                    "processed_at": datetime.now().isoformat()
                }

            # Close all positions
            closed_orders = []
            for position in positions:
                position_symbol = position.get('symbol')
                position_quantity = abs(Decimal(str(position.get('quantity', 0))))

                if position_quantity <= 0:
                    continue

                # Determine close side (opposite of current position)
                current_side = position.get('side', 'long')
                close_side = OrderSide.SELL if current_side.lower() == 'long' else OrderSide.BUY

                # Place close order
                order_id = client.place_order(
                    symbol=position_symbol,
                    order_type=OrderType.MARKET,
                    side=close_side,
                    quantity=position_quantity,
                    time_in_force="day"
                )

                if order_id:
                    closed_orders.append({
                        "symbol": position_symbol,
                        "quantity": float(position_quantity),
                        "side": close_side.value,
                        "order_id": order_id
                    })

                    # Update position manager
                    services["position_manager"].update_position_after_order(
                        position_symbol, close_side.value, position_quantity, order_id
                    )

            return {
                "signal_id": trade_signal.signal_id,
                "status": "processed",
                "account_name": trade_signal.account_name,
                "action": trade_signal.action,
                "closed_orders": closed_orders,
                "message": f"Closed all {len(closed_orders)} positions",
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            raise SignalProcessingError(f"Close all positions failed: {str(e)}")

    async def _get_option_chain(self, symbol: str, client) -> List[OptionContract]:
        """Get option chain for symbol"""

        try:
            logger.info(f"Getting option chain for symbol: {symbol}")
            # Get option chain from client
            option_chain_data = client.get_option_chain(symbol)
            logger.info(f"Received option chain data: {len(option_chain_data) if option_chain_data else 0} contracts")

            if not option_chain_data:
                logger.warning(f"No option chain data for symbol: {symbol}")
                return []

            # Convert to OptionContract objects
            option_contracts = []
            for contract_data in option_chain_data:
                try:
                    # Parse expiry date
                    expiry_str = contract_data.get('expiry', '2025-01-17T00:00:00')
                    if 'T' in expiry_str:
                        expiry = datetime.fromisoformat(expiry_str.replace('T', ' ').replace('Z', ''))
                    else:
                        expiry = datetime.strptime(expiry_str, '%Y-%m-%d')

                    contract = OptionContract(
                        symbol=contract_data.get('symbol', ''),
                        underlying=symbol,
                        strike=Decimal(str(contract_data.get('strike', 0))),
                        expiry=expiry,
                        option_type=contract_data.get('option_type', 'call'),
                        bid=Decimal(str(contract_data.get('bid', 0))),
                        ask=Decimal(str(contract_data.get('ask', 0))),
                        last_price=Decimal(str(contract_data.get('last_price', 0))),
                        volume=contract_data.get('volume', 0),
                        open_interest=contract_data.get('open_interest', 0)
                    )
                    option_contracts.append(contract)
                except Exception as e:
                    logger.warning(f"Failed to parse option contract: {e}")
                    continue

            return option_contracts

        except Exception as e:
            logger.error(f"Failed to get option chain for {symbol}: {e}")
            return []

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        
        total_signals = len(self._processing_status)
        if total_signals == 0:
            return {
                "total_signals": 0,
                "success_rate": 0.0,
                "status_breakdown": {},
                "queue_length": len(self._processing_queue)
            }
        
        status_counts = {}
        for status in self._processing_status.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        
        completed_count = status_counts.get("completed", 0)
        success_rate = (completed_count / total_signals) * 100 if total_signals > 0 else 0.0
        
        return {
            "total_signals": total_signals,
            "success_rate": round(success_rate, 2),
            "status_breakdown": status_counts,
            "queue_length": len(self._processing_queue),
            "timestamp": datetime.now().isoformat()
        }


# Global processor instance
_signal_processor: Optional[SignalProcessor] = None


def get_signal_processor() -> SignalProcessor:
    """Get global signal processor instance"""
    global _signal_processor
    
    if _signal_processor is None:
        _signal_processor = SignalProcessor()
    
    return _signal_processor
