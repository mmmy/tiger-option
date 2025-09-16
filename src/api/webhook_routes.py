"""
Webhook API routes for receiving TradingView signals
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from ..models import (
    WebhookSignal,
    WebhookSignalPayload,
    ApiResponse,
    TradeSignal,
    SignalValidationResult,
)
from ..middleware import (
    validate_account_dependency,
    validate_webhook_security,
)
from ..config import AccountConfig
from ..services import get_auth_service, get_signal_processor


logger = logging.getLogger(__name__)

# Create webhook router
webhook_router = APIRouter(prefix="/webhook", tags=["webhook"])


@webhook_router.post("/signal", response_model=ApiResponse[Dict[str, Any]])
async def receive_deribit_style_signal(
    request: Request,
    payload: WebhookSignalPayload = Body(...)
):
    """
    Receive trading signal from TradingView webhook (deribit_webhook compatible format)

    This endpoint receives trading signals in the same format as deribit_webhook project.
    The signal includes account name in the payload and follows the deribit format.
    """

    request_id = f"req_{int(datetime.now().timestamp() * 1000)}_{hash(str(payload)) % 10000:04d}"

    logger.info(
        f"📡 [{request_id}] Received deribit-style webhook signal: account={payload.account_name}, "
        f"symbol={payload.symbol}, side={payload.side}, size={payload.size}"
    )

    try:
        # 1. Validate account exists
        auth_service = get_auth_service()
        if not auth_service.is_account_valid(payload.account_name):
            return ApiResponse(
                success=False,
                message=f"Account not found or disabled: {payload.account_name}",
                error="Invalid account",
                request_id=request_id
            )

        # 2. Convert deribit-style payload to internal signal format
        internal_signal = convert_deribit_payload_to_signal(payload, request_id)

        # 3. Process signal using signal processor
        processor = get_signal_processor()
        result = await processor.validate_and_process_signal(
            internal_signal, payload.account_name, request_id
        )

        # 7. Immediately process the signal (like deribit_webhook)
        if result["status"] == "queued":
            try:
                process_result = await processor.process_queued_signals()

                # Find our signal in the results
                signal_result = None
                for res in process_result.get("results", []):
                    if res.get("signal_id") == result.get("signal_id"):
                        signal_result = res
                        break

                if signal_result and signal_result.get("status") == "executed":
                    # Return success response in deribit format
                    return ApiResponse(
                        success=True,
                        message=signal_result.get("message", "Trading operation successful"),
                        request_id=request_id,
                        data={
                            "orderId": signal_result.get("order_id"),
                            "instrumentName": signal_result.get("instrument_name"),
                            "executedQuantity": signal_result.get("executed_quantity"),
                            "executedPrice": signal_result.get("executed_price")
                        }
                    )
                else:
                    # Return error response
                    error_msg = signal_result.get("error") if signal_result else "Trading operation failed"
                    return ApiResponse(
                        success=False,
                        message=error_msg,
                        error="Trading failed",
                        request_id=request_id,
                        data={
                            "orderId": signal_result.get("order_id") if signal_result else None,
                            "instrumentName": signal_result.get("instrument_name") if signal_result else None,
                            "executedQuantity": signal_result.get("executed_quantity") if signal_result else None,
                            "executedPrice": signal_result.get("executed_price") if signal_result else None
                        }
                    )
            except Exception as e:
                logger.error(f"💥 [{request_id}] Signal processing error: {e}")
                return ApiResponse(
                    success=False,
                    message=f"Trading operation failed: {str(e)}",
                    error="Processing error",
                    request_id=request_id
                )

        # If not queued, return validation result
        return ApiResponse(
            success=result["status"] != "validation_failed",
            message=result.get("message", "Signal processed"),
            error="; ".join(result.get("validation_result", {}).get("errors", [])) if result["status"] == "validation_failed" else None,
            request_id=request_id,
            data=result
        )

    except Exception as e:
        logger.error(f"💥 [{request_id}] Webhook processing error: {e}")
        return ApiResponse(
            success=False,
            message=f"Unknown error: {str(e)}",
            error="Internal error",
            request_id=request_id
        )


@webhook_router.post("/signal/{account_name}", response_model=ApiResponse[Dict[str, Any]])
async def receive_trading_signal(
    account_name: str,
    request: Request,
    signal: WebhookSignal = Body(...),
    account_config: AccountConfig = Depends(validate_account_dependency),
    security_validation: Dict = Depends(validate_webhook_security)
):
    """
    Receive trading signal from TradingView webhook
    
    This endpoint receives trading signals from TradingView and processes them
    for the specified account. The signal is validated and queued for execution.
    """
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.info(
        f"Received webhook signal [{request_id}] for account: {account_name}, "
        f"symbol: {signal.symbol}, action: {signal.action}"
    )
    
    try:
        # Process signal using signal processor
        processor = get_signal_processor()
        result = await processor.validate_and_process_signal(
            signal, account_name, request_id
        )

        # Determine response based on processing result
        if result["status"] == "validation_failed":
            return ApiResponse(
                success=False,
                message="Signal validation failed",
                error="; ".join(result["validation_result"]["errors"]),
                request_id=request_id,
                data=result
            )

        # For successful signals, immediately process them (like deribit_webhook)
        if result["status"] == "queued":
            try:
                # Process the queued signal immediately
                process_result = await processor.process_queued_signals()

                # Update result with processing outcome
                if process_result["processed_count"] > 0 or process_result["failed_count"] > 0:
                    # Find our signal in the results
                    signal_result = None
                    for res in process_result.get("results", []):
                        if res.get("signal_id") == result.get("signal_id"):
                            signal_result = res
                            break

                    if signal_result:
                        result.update({
                            "execution_result": signal_result,
                            "final_status": signal_result.get("status", "unknown")
                        })
                    else:
                        # If no specific result found, add general processing info
                        result.update({
                            "processing_info": {
                                "processed_count": process_result["processed_count"],
                                "failed_count": process_result["failed_count"],
                                "total_count": process_result["total_count"]
                            }
                        })
                else:
                    # No signals were processed, might be an issue
                    result.update({
                        "processing_warning": "Signal was queued but not immediately processed"
                    })
            except Exception as e:
                logger.error(f"Failed to process queued signals immediately: {e}")
                result.update({
                    "processing_error": f"Failed to process immediately: {str(e)}"
                })

        # Success response
        return ApiResponse(
            success=True,
            message="Trading signal received and processed successfully",
            request_id=request_id,
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook signal [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process trading signal: {str(e)}"
        )


@webhook_router.post("/test/{account_name}", response_model=ApiResponse[Dict[str, Any]])
async def test_webhook_endpoint(
    account_name: str,
    request: Request,
    test_data: Dict[str, Any] = Body(...),
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Test webhook endpoint for debugging and validation
    
    This endpoint can be used to test webhook connectivity and payload format
    without triggering actual trades.
    """
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.info(f"Test webhook called [{request_id}] for account: {account_name}")
    
    response_data = {
        "test_id": request_id,
        "account_name": account_name,
        "account_enabled": account_config.enabled,
        "received_at": datetime.now().isoformat(),
        "payload": test_data,
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    
    return ApiResponse(
        success=True,
        message="Test webhook received successfully",
        request_id=request_id,
        data=response_data
    )


def validate_trading_signal(signal: WebhookSignal, account_config: AccountConfig) -> SignalValidationResult:
    """Validate trading signal against account configuration"""
    
    errors = []
    warnings = []
    
    # Validate required fields
    if not signal.symbol:
        errors.append("Symbol is required")
    
    if not signal.action:
        errors.append("Action is required")
    
    # Validate action
    valid_actions = ["buy", "sell", "close", "close_all"]
    if signal.action and signal.action.lower() not in valid_actions:
        errors.append(f"Invalid action: {signal.action}. Must be one of: {valid_actions}")
    
    # Validate quantity
    if signal.quantity is not None:
        if signal.quantity <= 0:
            errors.append("Quantity must be positive")
        elif signal.quantity > account_config.max_position_size:
            errors.append(f"Quantity {signal.quantity} exceeds max position size {account_config.max_position_size}")
    
    # Validate price
    if signal.price is not None and signal.price <= 0:
        errors.append("Price must be positive")
    
    # Validate symbol format (basic check)
    if signal.symbol:
        if len(signal.symbol) < 1 or len(signal.symbol) > 20:
            errors.append("Symbol length must be between 1 and 20 characters")
        
        # Check for invalid characters
        if not signal.symbol.replace(" ", "").replace(".", "").replace("-", "").isalnum():
            warnings.append("Symbol contains unusual characters")
    
    # Validate order type
    if signal.order_type:
        valid_order_types = ["market", "limit", "stop", "stop_limit"]
        if signal.order_type.lower() not in valid_order_types:
            errors.append(f"Invalid order type: {signal.order_type}")
    
    # Validate time in force
    if signal.time_in_force:
        valid_tif = ["day", "gtc", "ioc", "fok"]
        if signal.time_in_force.lower() not in valid_tif:
            errors.append(f"Invalid time in force: {signal.time_in_force}")
    
    # Account-specific validations
    if not account_config.allow_options_trading and "option" in signal.symbol.lower():
        errors.append("Options trading is not enabled for this account")
    
    return SignalValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        signal_id=signal.signal_id,
        symbol=signal.symbol,
        action=signal.action
    )


def convert_deribit_payload_to_signal(payload: WebhookSignalPayload, request_id: str) -> WebhookSignal:
    """Convert deribit-style payload to internal WebhookSignal format"""

    # Determine action based on side and market position
    action = "buy" if payload.side == "buy" else "sell"

    # Handle special cases for position changes
    if payload.is_closing_position:
        action = "close"
    elif payload.is_reversing_position:
        # For reversals, use the new side
        action = "buy" if payload.market_position == "long" else "sell"

    # Convert size to quantity
    try:
        quantity = payload.size_decimal
    except:
        quantity = None

    # Convert price
    try:
        price = payload.price_decimal
    except:
        price = None

    # Create internal signal
    return WebhookSignal(
        signal_id=request_id,
        symbol=payload.symbol,
        action=action,
        quantity=quantity,
        price=price,
        order_type="market",  # Default to market orders
        time_in_force="day",
        strategy=payload.comment,
        comment=payload.alert_message,
        metadata={
            "original_payload": payload.model_dump(),
            "market_position": payload.market_position,
            "prev_market_position": payload.prev_market_position,
            "exchange": payload.exchange,
            "period": payload.period,
            "qty_type": payload.qty_type,
            "tv_id": getattr(payload, 'tv_id', None),
            "position_size": payload.position_size
        }
    )


def convert_webhook_to_trade_signal(signal: WebhookSignal, account_config: AccountConfig) -> TradeSignal:
    """Convert webhook signal to internal trade signal format"""
    
    # Determine quantity if not specified
    quantity = signal.quantity
    if quantity is None:
        # Use default position size from account config
        quantity = account_config.default_position_size
    
    # Determine order type
    order_type = signal.order_type or "market"
    
    # Determine time in force
    time_in_force = signal.time_in_force or "day"
    
    # Create trade signal
    trade_signal = TradeSignal(
        signal_id=signal.signal_id,
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
    
    return trade_signal


@webhook_router.get("/status/{signal_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_signal_status(signal_id: str):
    """Get processing status of a specific signal"""

    processor = get_signal_processor()
    status = processor.get_signal_status(signal_id)

    if status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal not found: {signal_id}"
        )

    return ApiResponse(
        success=True,
        message="Signal status retrieved successfully",
        data={
            "signal_id": signal_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    )


@webhook_router.get("/queue/status", response_model=ApiResponse[Dict[str, Any]])
async def get_queue_status():
    """Get current processing queue status"""

    processor = get_signal_processor()
    queue_status = processor.get_queue_status()

    return ApiResponse(
        success=True,
        message="Queue status retrieved successfully",
        data=queue_status
    )


@webhook_router.get("/statistics", response_model=ApiResponse[Dict[str, Any]])
async def get_processing_statistics():
    """Get signal processing statistics"""

    processor = get_signal_processor()
    stats = processor.get_processing_statistics()

    return ApiResponse(
        success=True,
        message="Processing statistics retrieved successfully",
        data=stats
    )


@webhook_router.post("/queue/process", response_model=ApiResponse[Dict[str, Any]])
async def process_queued_signals():
    """Manually trigger processing of queued signals"""

    processor = get_signal_processor()
    result = await processor.process_queued_signals()

    return ApiResponse(
        success=True,
        message="Queued signals processed",
        data=result
    )


# Health check for webhook service
@webhook_router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def webhook_health_check():
    """Health check for webhook service"""

    auth_service = get_auth_service()
    processor = get_signal_processor()

    enabled_accounts = auth_service.get_enabled_account_names()
    queue_status = processor.get_queue_status()

    return ApiResponse(
        success=True,
        message="Webhook service is healthy",
        data={
            "service": "webhook",
            "status": "healthy",
            "enabled_accounts": len(enabled_accounts),
            "account_names": enabled_accounts,
            "queue_status": queue_status,
            "timestamp": datetime.now().isoformat()
        }
    )
