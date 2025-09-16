"""
Market data API routes for Tiger Options Trading Service
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..models import (
    ApiResponse,
    OptionContract,
)
from ..middleware import (
    validate_account_dependency,
)
from ..config import AccountConfig
from ..services import get_auth_service


logger = logging.getLogger(__name__)

# Create market data router
market_router = APIRouter(prefix="/api/market", tags=["market"])


@market_router.get("/option-expirations/{symbol}", response_model=ApiResponse[List[str]])
async def get_option_expirations(
    symbol: str,
    account_name: str = Query(..., description="Account name"),
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Get option expiration dates for a symbol
    
    Returns a list of expiration dates for options on the given symbol.
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
        
        # Get option expirations
        expirations = client.get_option_expirations(symbol)
        
        # Convert datetime objects to ISO strings
        expiration_strings = [exp.isoformat() for exp in expirations]
        
        logger.info(f"Retrieved {len(expirations)} expiration dates for {symbol}")
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(expirations)} expiration dates for {symbol}",
            data=expiration_strings
        )
        
    except Exception as e:
        logger.error(f"Failed to get option expirations for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get option expirations: {str(e)}"
        )


@market_router.get("/option-chain/{symbol}", response_model=ApiResponse[List[OptionContract]])
async def get_option_chain(
    symbol: str,
    expiry: str,
    account_name: str = Query(..., description="Account name"),
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Get option chain for a symbol and expiry date
    
    Returns all option contracts (calls and puts) for the given symbol and expiry.
    """
    
    try:
        # Parse expiry date
        try:
            expiry_date = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid expiry date format: {expiry}. Use ISO format (YYYY-MM-DD)"
            )
        
        # Get Tiger client
        auth_service = get_auth_service()
        client = auth_service.get_client(account_name)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get client for account: {account_name}"
            )
        
        # Get option chain
        option_chain = client.get_option_chain(symbol, expiry_date)
        
        logger.info(f"Retrieved {len(option_chain)} option contracts for {symbol} expiry {expiry}")
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(option_chain)} option contracts for {symbol}",
            data=option_chain
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get option chain for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get option chain: {str(e)}"
        )


@market_router.get("/option-quotes", response_model=ApiResponse[Dict[str, OptionContract]])
async def get_option_quotes(
    symbols: str = Query(..., description="Comma-separated list of option symbols"),
    account_name: str = Query(..., description="Account name"),
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Get option quotes for multiple symbols
    
    Returns current quotes (bid, ask, last, volume, etc.) for the specified option symbols.
    """
    
    try:
        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        
        if not symbol_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one symbol is required"
            )
        
        if len(symbol_list) > 50:  # Limit to prevent abuse
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 symbols allowed per request"
            )
        
        # Get Tiger client
        auth_service = get_auth_service()
        client = auth_service.get_client(account_name)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get client for account: {account_name}"
            )
        
        # Get option quotes
        quotes = client.get_option_quotes(symbol_list)
        
        logger.info(f"Retrieved quotes for {len(quotes)} option symbols")
        
        return ApiResponse(
            success=True,
            message=f"Retrieved quotes for {len(quotes)} option symbols",
            data=quotes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get option quotes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get option quotes: {str(e)}"
        )


@market_router.get("/search/{query}", response_model=ApiResponse[List[Dict[str, Any]]])
async def search_symbols(
    query: str,
    account_name: str = Query(..., description="Account name"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    account_config: AccountConfig = Depends(validate_account_dependency)
):
    """
    Search for symbols (stocks, options, etc.)
    
    Returns a list of symbols matching the search query.
    """
    
    try:
        if len(query) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query must be at least 1 character long"
            )
        
        # For now, return mock search results
        # In a real implementation, this would call Tiger API search endpoint
        mock_results = []
        
        # Mock stock results
        if query.upper() in ['AAPL', 'APPLE']:
            mock_results.append({
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "type": "stock",
                "exchange": "NASDAQ",
                "currency": "USD"
            })
        
        if query.upper() in ['TSLA', 'TESLA']:
            mock_results.append({
                "symbol": "TSLA", 
                "name": "Tesla, Inc.",
                "type": "stock",
                "exchange": "NASDAQ",
                "currency": "USD"
            })
        
        # Mock option results
        if 'AAPL' in query.upper():
            mock_results.extend([
                {
                    "symbol": "AAPL  250117C00150000",
                    "name": "AAPL Jan 17 2025 $150 Call",
                    "type": "option",
                    "underlying": "AAPL",
                    "strike": 150.0,
                    "expiry": "2025-01-17",
                    "option_type": "call"
                },
                {
                    "symbol": "AAPL  250117P00150000",
                    "name": "AAPL Jan 17 2025 $150 Put", 
                    "type": "option",
                    "underlying": "AAPL",
                    "strike": 150.0,
                    "expiry": "2025-01-17",
                    "option_type": "put"
                }
            ])
        
        # Limit results
        results = mock_results[:limit]
        
        logger.info(f"Symbol search for '{query}' returned {len(results)} results")
        
        return ApiResponse(
            success=True,
            message=f"Found {len(results)} symbols matching '{query}'",
            data=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search symbols for '{query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search symbols: {str(e)}"
        )


@market_router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def market_health_check():
    """Health check for market data service"""
    
    auth_service = get_auth_service()
    enabled_accounts = auth_service.get_enabled_account_names()
    
    return ApiResponse(
        success=True,
        message="Market data service is healthy",
        data={
            "service": "market_data",
            "status": "healthy",
            "enabled_accounts": len(enabled_accounts),
            "account_names": enabled_accounts,
            "timestamp": datetime.now().isoformat()
        }
    )
