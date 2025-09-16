"""
Account management routes for Tiger Options Trading Service
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from decimal import Decimal

from ..models.common import ApiResponse
from ..services.auth_service import get_auth_service, AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=ApiResponse)
async def get_accounts(auth_service: AuthService = Depends(get_auth_service)):
    """Get list of available accounts"""
    try:
        accounts = auth_service.get_available_accounts()
        account_list = [{"name": account} for account in accounts]
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(account_list)} accounts",
            data=account_list
        )
    except Exception as e:
        logger.error(f"Failed to get accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_name}/summary", response_model=ApiResponse)
async def get_account_summary(
    account_name: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get account summary including balance and delta information"""
    try:
        client = auth_service.get_client(account_name)
        if not client:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_name}")

        # Get account summary
        account_summary = client.get_account_summary()
        
        # Calculate total delta from positions
        positions = client.get_positions()
        total_delta = sum(pos.get('delta', 0) for pos in positions if pos.get('delta'))
        position_delta = total_delta  # For options, position delta = total delta
        
        summary_data = {
            "account_name": account_name,
            "net_liquidation": account_summary.get('net_liquidation', 0),
            "total_cash": account_summary.get('total_cash', 0),
            "available_funds": account_summary.get('available_funds', 0),
            "buying_power": account_summary.get('buying_power', 0),
            "total_delta": float(total_delta),
            "position_delta": float(position_delta),
            "position_count": len(positions)
        }
        
        return ApiResponse(
            success=True,
            message="Account summary retrieved successfully",
            data=summary_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account summary for {account_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_name}/positions", response_model=ApiResponse)
async def get_positions(
    account_name: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get account positions"""
    try:
        client = auth_service.get_client(account_name)
        if not client:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_name}")

        positions = client.get_positions()
        
        # Filter for options positions only
        option_positions = []
        for pos in positions:
            symbol = pos.get('symbol', '')
            # Check if it's an option (contains expiry date pattern or option keywords)
            if any(keyword in symbol.upper() for keyword in ['C', 'P']) or 'OPT' in symbol.upper():
                option_positions.append({
                    "symbol": symbol,
                    "underlying": pos.get('underlying', ''),
                    "option_type": pos.get('option_type', ''),
                    "strike": pos.get('strike', 0),
                    "expiry": pos.get('expiry', ''),
                    "quantity": pos.get('quantity', 0),
                    "average_price": pos.get('average_price', 0),
                    "market_price": pos.get('market_price', 0),
                    "delta": pos.get('delta', 0),
                    "unrealized_pnl": pos.get('unrealized_pnl', 0)
                })
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(option_positions)} option positions",
            data=option_positions
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get positions for {account_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_name}/orders", response_model=ApiResponse)
async def get_orders(
    account_name: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get account orders"""
    try:
        client = auth_service.get_client(account_name)
        if not client:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_name}")

        orders = client.get_orders()
        
        # Filter for options orders only
        option_orders = []
        for order in orders:
            symbol = order.get('symbol', '')
            # Check if it's an option
            if any(keyword in symbol.upper() for keyword in ['C', 'P']) or 'OPT' in symbol.upper():
                option_orders.append({
                    "order_id": order.get('order_id', ''),
                    "symbol": symbol,
                    "underlying": order.get('underlying', ''),
                    "option_type": order.get('option_type', ''),
                    "side": order.get('side', ''),
                    "quantity": order.get('quantity', 0),
                    "limit_price": order.get('limit_price', 0),
                    "order_type": order.get('order_type', ''),
                    "status": order.get('status', ''),
                    "create_time": order.get('create_time', '')
                })
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(option_orders)} option orders",
            data=option_orders
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get orders for {account_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_name}/trades", response_model=ApiResponse)
async def get_trades(
    account_name: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get account trade history"""
    try:
        client = auth_service.get_client(account_name)
        if not client:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_name}")

        # Get recent trades (last 50)
        trades = client.get_trades(limit=50)
        
        # Filter for options trades only
        option_trades = []
        for trade in trades:
            symbol = trade.get('symbol', '')
            # Check if it's an option
            if any(keyword in symbol.upper() for keyword in ['C', 'P']) or 'OPT' in symbol.upper():
                option_trades.append({
                    "trade_time": trade.get('trade_time', ''),
                    "symbol": symbol,
                    "underlying": trade.get('underlying', ''),
                    "side": trade.get('side', ''),
                    "quantity": trade.get('quantity', 0),
                    "price": trade.get('price', 0),
                    "commission": trade.get('commission', 0),
                    "realized_pnl": trade.get('realized_pnl', 0)
                })
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(option_trades)} option trades",
            data=option_trades
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trades for {account_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_name}/orders/{order_id}/cancel", response_model=ApiResponse)
async def cancel_order(
    account_name: str,
    order_id: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Cancel an order"""
    try:
        client = auth_service.get_client(account_name)
        if not client:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_name}")

        result = client.cancel_order(order_id)
        
        return ApiResponse(
            success=True,
            message=f"Order {order_id} cancelled successfully",
            data={"order_id": order_id, "result": result}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id} for {account_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_name}/positions/{symbol}/close", response_model=ApiResponse)
async def close_position(
    account_name: str,
    symbol: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Close a position"""
    try:
        client = auth_service.get_client(account_name)
        if not client:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_name}")

        result = client.close_position(symbol)
        
        return ApiResponse(
            success=True,
            message=f"Position {symbol} closed successfully",
            data={"symbol": symbol, "result": result}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close position {symbol} for {account_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
