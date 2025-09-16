"""
Enhanced Signal Processing Service for Tiger Options Trading Service

This module processes webhook signals through the complete trading pipeline:
validation -> option selection -> order strategy -> risk management -> execution
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal

from ..models import (
    WebhookSignal,
    TradeSignal,
    SignalValidationResult,
    OptionContract,
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


class EnhancedSignalProcessor:
    """
    Enhanced signal processing service
    
    Processes webhook signals through the complete trading pipeline:
    validation -> option selection -> order strategy -> risk management -> execution
    """
    
    def __init__(self):
        """Initialize enhanced signal processor"""
        self.validator = get_signal_validator()
        self.auth_service = get_auth_service()
        self.signal_queue: List[Dict[str, Any]] = []
        self.processed_signals: Dict[str, Dict[str, Any]] = {}
        
        # Account-specific services (initialized per account)
        self._account_services: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Enhanced signal processor initialized")
    
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
    
    async def process_signal(
        self, 
        webhook_signal: WebhookSignal, 
        account_name: str
    ) -> Dict[str, Any]:
        """
        Process a webhook signal through the complete trading pipeline
        
        Args:
            webhook_signal: The webhook signal to process
            account_name: Target account name
            
        Returns:
            Processing result with signal ID and status
        """
        
        # Generate unique signal ID
        signal_id = str(uuid.uuid4())
        
        try:
            # Get account services
            services = self._get_account_services(account_name)
            if not services:
                return {
                    "signal_id": signal_id,
                    "status": "validation_failed",
                    "error": f"Account not found: {account_name}",
                    "processed_at": datetime.now().isoformat()
                }
            
            # Step 1: Validate signal
            validation_result = self.validator.validate_signal(
                webhook_signal, services["config"]
            )
            
            if not validation_result.is_valid:
                logger.warning(f"Signal validation failed: {validation_result.errors}")
                return {
                    "signal_id": signal_id,
                    "status": "validation_failed",
                    "validation_result": validation_result.dict(),
                    "processed_at": datetime.now().isoformat()
                }
            
            # Step 2: Convert to trade signal
            trade_signal = self.validator.convert_to_trade_signal(
                webhook_signal, services["config"], signal_id
            )
            
            # Step 3: Enhanced processing pipeline
            processing_result = await self._process_trading_pipeline(
                trade_signal, services, signal_id
            )
            
            # Queue for execution
            queued_signal = {
                "signal_id": signal_id,
                "account_name": account_name,
                "webhook_signal": webhook_signal.dict(),
                "trade_signal": trade_signal.dict(),
                "validation_result": validation_result.dict(),
                "processing_result": processing_result,
                "status": "queued",
                "queued_at": datetime.now().isoformat(),
                "processed_at": None
            }
            
            self.signal_queue.append(queued_signal)
            
            logger.info(f"Signal queued successfully: {signal_id}")
            
            return {
                "signal_id": signal_id,
                "status": "queued",
                "trade_signal": {
                    "symbol": trade_signal.symbol,
                    "action": trade_signal.action,
                    "quantity": str(trade_signal.quantity) if trade_signal.quantity else None,
                    "order_type": trade_signal.order_type
                },
                "validation_result": validation_result.dict(),
                "processing_result": processing_result,
                "queued_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return {
                "signal_id": signal_id,
                "status": "error",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    async def _process_trading_pipeline(
        self,
        trade_signal: TradeSignal,
        services: Dict[str, Any],
        signal_id: str
    ) -> Dict[str, Any]:
        """Process signal through the complete trading pipeline"""
        
        try:
            # Get current market data (mock for now)
            current_price = trade_signal.price or Decimal('150.00')
            
            # Step 1: Get option chain
            option_chain = await self._get_option_chain(trade_signal.symbol, services)
            
            if not option_chain:
                return {
                    "success": False,
                    "error": "No option chain available",
                    "step": "option_chain_retrieval"
                }
            
            # Step 2: Select option contract
            selected_contract = services["option_selector"].select_option_contract(
                trade_signal, option_chain, current_price, SelectionStrategy.ATM
            )
            
            if not selected_contract:
                return {
                    "success": False,
                    "error": "No suitable option contract found",
                    "step": "option_selection"
                }
            
            # Step 3: Determine position size
            suggested_quantity = services["position_manager"].suggest_position_sizing(
                selected_contract.symbol, trade_signal.quantity
            )
            
            # Step 4: Risk check
            risk_result, risk_messages, risk_metrics = services["risk_manager"].check_trade_risk(
                trade_signal, selected_contract, suggested_quantity
            )
            
            if risk_result == RiskCheckResult.REJECTED:
                return {
                    "success": False,
                    "error": "Trade rejected by risk management",
                    "risk_messages": risk_messages,
                    "risk_metrics": risk_metrics,
                    "step": "risk_check"
                }
            
            # Step 5: Create order strategy
            order_params = services["order_strategy"].create_order(
                trade_signal, selected_contract, OrderStrategy.LIMIT_MIDPOINT, suggested_quantity
            )
            
            if not order_params:
                return {
                    "success": False,
                    "error": "Failed to create order parameters",
                    "step": "order_creation"
                }
            
            # Step 6: Validate order parameters
            is_valid, validation_errors = services["order_strategy"].validate_order_parameters(order_params)
            
            if not is_valid:
                return {
                    "success": False,
                    "error": "Order validation failed",
                    "validation_errors": validation_errors,
                    "step": "order_validation"
                }
            
            return {
                "success": True,
                "selected_contract": selected_contract.dict() if selected_contract else None,
                "suggested_quantity": float(suggested_quantity),
                "risk_result": risk_result.value,
                "risk_messages": risk_messages,
                "risk_metrics": risk_metrics,
                "order_params": order_params,
                "pipeline_completed": True
            }
            
        except Exception as e:
            logger.error(f"Error in trading pipeline: {e}")
            return {
                "success": False,
                "error": f"Pipeline error: {str(e)}",
                "step": "pipeline_execution"
            }
    
    async def _get_option_chain(self, symbol: str, services: Dict[str, Any]) -> List[OptionContract]:
        """Get option chain for symbol (mock implementation)"""
        
        try:
            # In real implementation, this would call the Tiger API
            # For now, return mock option contracts
            
            mock_contracts = []
            
            # Generate mock call options
            for strike in [140, 145, 150, 155, 160]:
                contract = OptionContract(
                    symbol=f"{symbol}  250117C{strike:08.0f}000",
                    underlying=symbol,
                    strike=Decimal(str(strike)),
                    expiry=datetime(2025, 1, 17),
                    option_type="call",
                    bid=Decimal('2.50'),
                    ask=Decimal('2.70'),
                    last_price=Decimal('2.60'),
                    volume=100,
                    open_interest=500
                )
                mock_contracts.append(contract)
            
            # Generate mock put options
            for strike in [140, 145, 150, 155, 160]:
                contract = OptionContract(
                    symbol=f"{symbol}  250117P{strike:08.0f}000",
                    underlying=symbol,
                    strike=Decimal(str(strike)),
                    expiry=datetime(2025, 1, 17),
                    option_type="put",
                    bid=Decimal('1.80'),
                    ask=Decimal('2.00'),
                    last_price=Decimal('1.90'),
                    volume=80,
                    open_interest=300
                )
                mock_contracts.append(contract)
            
            return mock_contracts
            
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return []
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        
        status_counts = {}
        for signal in self.signal_queue:
            status = signal.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "queue_length": len(self.signal_queue),
            "total_signals": len(self.signal_queue) + len(self.processed_signals),
            "status_counts": status_counts,
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_queued_signals(self) -> Dict[str, Any]:
        """Process all queued signals"""
        
        if not self.signal_queue:
            return {
                "processed_count": 0,
                "failed_count": 0,
                "total_count": 0,
                "results": [],
                "processed_at": datetime.now().isoformat()
            }
        
        processed_count = 0
        failed_count = 0
        results = []
        
        # Process signals (move to processed list)
        signals_to_process = self.signal_queue.copy()
        self.signal_queue.clear()
        
        for signal in signals_to_process:
            try:
                # Execute the trading pipeline result
                signal_id = signal["signal_id"]
                account_name = signal["account_name"]
                trade_signal = signal["trade_signal"]
                processing_result = signal.get("processing_result", {})
                
                if processing_result.get("success"):
                    # Mock order execution
                    order_params = processing_result.get("order_params", {})
                    order_id = f"mock_order_{signal_id}"
                    
                    # Update signal status
                    signal["status"] = "processed"
                    signal["processed_at"] = datetime.now().isoformat()
                    signal["order_id"] = order_id
                    
                    results.append({
                        "signal_id": signal_id,
                        "status": "processed",
                        "account_name": account_name,
                        "symbol": trade_signal["symbol"],
                        "action": trade_signal["action"],
                        "quantity": processing_result.get("suggested_quantity", trade_signal["quantity"]),
                        "selected_contract": processing_result.get("selected_contract", {}).get("symbol"),
                        "order_id": order_id,
                        "risk_result": processing_result.get("risk_result"),
                        "processed_at": signal["processed_at"],
                        "message": "Signal processed successfully through enhanced pipeline (mock mode)"
                    })
                    
                    processed_count += 1
                else:
                    # Processing failed
                    error_msg = processing_result.get("error", "Unknown processing error")
                    signal["status"] = "failed"
                    signal["processed_at"] = datetime.now().isoformat()
                    signal["error"] = error_msg
                    
                    results.append({
                        "signal_id": signal_id,
                        "status": "failed",
                        "account_name": account_name,
                        "error": error_msg,
                        "processing_step": processing_result.get("step"),
                        "processed_at": signal["processed_at"]
                    })
                    
                    failed_count += 1
                
                # Move to processed signals
                self.processed_signals[signal_id] = signal
                
            except Exception as e:
                logger.error(f"Error processing signal {signal.get('signal_id')}: {e}")
                
                # Update signal status to failed
                signal["status"] = "failed"
                signal["processed_at"] = datetime.now().isoformat()
                signal["error"] = str(e)
                
                # Move to processed signals
                signal_id = signal.get("signal_id", "unknown")
                self.processed_signals[signal_id] = signal
                
                results.append({
                    "signal_id": signal_id,
                    "status": "failed",
                    "error": str(e),
                    "processed_at": signal["processed_at"]
                })
                
                failed_count += 1
        
        logger.info(f"Processed {processed_count} signals, {failed_count} failed")
        
        return {
            "processed_count": processed_count,
            "failed_count": failed_count,
            "total_count": len(signals_to_process),
            "results": results,
            "processed_at": datetime.now().isoformat()
        }
