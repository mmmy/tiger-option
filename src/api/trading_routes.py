"""
Trading API routes for Tiger Options Trading Service
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field

from ..models import (
    ApiResponse,
    TigerOrder,
    Position,
    OrderType,
    OrderSide,
)
from ..middleware import (
    validate_account_dependency,
)
from ..config import AccountConfig
from ..services import get_auth_service


logger = logging.getLogger(__name__)

# Create trading router
trading_router = APIRouter(prefix="/api/trading", tags=["trading"])


class PlaceOrderRequest(BaseModel):
    """Request model for placing orders"""
    symbol: str = Field(description="Trading symbol")
    order_type: OrderType = Field(description="Order type")
    side: OrderSide = Field(description="Order side (buy/sell)")
    quantity: Decimal = Field(description="Order quantity")
    price: Optional[Decimal] = Field(default=None, description="Order price (for limit orders)")
    stop_price: Optional[Decimal] = Field(default=None, description="Stop price (for stop orders)")
    time_in_force: str = Field(default="day", description="Time in force")


@trading_router.post("/orders/{account_name}", response_model=ApiResponse[Dict[str, Any]])
async def place_order(
    account_name: str,
    order_request: PlaceOrderRequest,
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Place a trading order
    
    Places a new trading order for the specified account.
    """
    
    try:
        # Get Tiger client
        auth_service = get_auth_service()
        client = auth_service.get_client(account_name)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get client for account: {account_name}"
            )
        
        # Validate order parameters
        if order_request.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and order_request.price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Price is required for {order_request.order_type.value} orders"
            )
        
        if order_request.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and order_request.stop_price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stop price is required for {order_request.order_type.value} orders"
            )
        
        # Place order
        order_id = client.place_order(
            symbol=order_request.symbol,
            order_type=order_request.order_type,
            side=order_request.side,
            quantity=order_request.quantity,
            price=order_request.price,
            stop_price=order_request.stop_price,
            time_in_force=order_request.time_in_force
        )
        
        if not order_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to place order"
            )
        
        logger.info(f"Order placed successfully: {order_id} for account {account_name}")
        
        return ApiResponse(
            success=True,
            message="Order placed successfully",
            data={
                "order_id": order_id,
                "account_name": account_name,
                "symbol": order_request.symbol,
                "order_type": order_request.order_type.value,
                "side": order_request.side.value,
                "quantity": str(order_request.quantity),
                "price": str(order_request.price) if order_request.price else None,
                "stop_price": str(order_request.stop_price) if order_request.stop_price else None,
                "time_in_force": order_request.time_in_force,
                "placed_at": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to place order for account {account_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place order: {str(e)}"
        )


@trading_router.delete("/orders/{account_name}/{order_id}", response_model=ApiResponse[Dict[str, Any]])
async def cancel_order(
    account_name: str,
    order_id: str,
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Cancel a trading order
    
    Cancels an existing order by order ID.
    """
    
    try:
        # Get Tiger client
        auth_service = get_auth_service()
        client = auth_service.get_client(account_name)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get client for account: {account_name}"
            )
        
        # Cancel order
        success = client.cancel_order(order_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel order: {order_id}"
            )
        
        logger.info(f"Order cancelled successfully: {order_id} for account {account_name}")
        
        return ApiResponse(
            success=True,
            message="Order cancelled successfully",
            data={
                "order_id": order_id,
                "account_name": account_name,
                "cancelled_at": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id} for account {account_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )


@trading_router.get("/orders/{account_name}", response_model=ApiResponse[List[TigerOrder]])
async def get_orders(
    account_name: str,
    status_filter: Optional[str] = Query(default=None, description="Filter by order status"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of orders to return"),
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Get trading orders for an account
    
    Returns a list of orders for the specified account, optionally filtered by status.
    """
    
    try:
        # Get Tiger client
        auth_service = get_auth_service()
        client = auth_service.get_client(account_name)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get client for account: {account_name}"
            )
        
        # Get orders
        orders = client.get_orders(status=status_filter)
        
        # Limit results
        if len(orders) > limit:
            orders = orders[:limit]
        
        logger.info(f"Retrieved {len(orders)} orders for account {account_name}")
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(orders)} orders",
            data=orders
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get orders for account {account_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders: {str(e)}"
        )


@trading_router.get("/positions/{account_name}", response_model=ApiResponse[List[Position]])
async def get_positions(
    account_name: str,
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Get current positions for an account
    
    Returns all current positions for the specified account.
    """
    
    try:
        # Get Tiger client
        auth_service = get_auth_service()
        client = auth_service.get_client(account_name)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get client for account: {account_name}"
            )
        
        # Get positions
        positions = client.get_positions()
        
        logger.info(f"Retrieved {len(positions)} positions for account {account_name}")
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(positions)} positions",
            data=positions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get positions for account {account_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get positions: {str(e)}"
        )


@trading_router.get("/account/{account_name}/summary", response_model=ApiResponse[Dict[str, Any]])
async def get_account_summary(
    account_name: str,
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Get account summary including balance, positions, and orders
    
    Returns a comprehensive summary of the account status.
    """
    
    try:
        # Get Tiger client
        auth_service = get_auth_service()
        client = auth_service.get_client(account_name)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get client for account: {account_name}"
            )
        
        # Get account info, positions, and orders
        account_info = client.get_account_info()
        positions = client.get_positions()
        orders = client.get_orders()
        
        # Calculate summary statistics
        total_positions = len(positions)
        total_market_value = sum(pos.market_value or 0 for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl or 0 for pos in positions)
        
        # Count orders by status
        order_counts = {}
        for order in orders:
            status_key = order.status.value if hasattr(order.status, 'value') else str(order.status)
            order_counts[status_key] = order_counts.get(status_key, 0) + 1
        
        summary = {
            "account_name": account_name,
            "account_info": account_info.dict() if account_info else None,
            "positions_summary": {
                "total_positions": total_positions,
                "total_market_value": str(total_market_value),
                "total_unrealized_pnl": str(total_unrealized_pnl)
            },
            "orders_summary": {
                "total_orders": len(orders),
                "by_status": order_counts
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Generated account summary for {account_name}")
        
        return ApiResponse(
            success=True,
            message="Account summary retrieved successfully",
            data=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account summary for {account_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account summary: {str(e)}"
        )


@trading_router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def trading_health_check():
    """Health check for trading service"""
    
    auth_service = get_auth_service()
    enabled_accounts = auth_service.get_enabled_account_names()
    
    # Test connections
    connection_status = {}
    for account_name in enabled_accounts:
        try:
            client = auth_service.get_client(account_name)
            connection_status[account_name] = client is not None
        except Exception:
            connection_status[account_name] = False
    
    return ApiResponse(
        success=True,
        message="Trading service is healthy",
        data={
            "service": "trading",
            "status": "healthy",
            "enabled_accounts": len(enabled_accounts),
            "account_names": enabled_accounts,
            "connection_status": connection_status,
            "timestamp": datetime.now().isoformat()
        }
    )
