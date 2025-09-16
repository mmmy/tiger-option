"""
Option Contract Selection Algorithm for Tiger Options Trading Service

This module implements algorithms to select the most appropriate option contracts
based on trading signals and market conditions.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from enum import Enum

from ..models import (
    OptionContract,
    TradeSignal,
    OrderSide,
    OptionType
)
from ..config import AccountConfig


logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """Option selection strategies"""
    ATM = "at_the_money"           # At-the-money options
    OTM = "out_of_the_money"       # Out-of-the-money options
    ITM = "in_the_money"           # In-the-money options
    DELTA_NEUTRAL = "delta_neutral" # Delta-neutral selection
    HIGH_VOLUME = "high_volume"     # High volume options
    TIGHT_SPREAD = "tight_spread"   # Options with tight bid-ask spreads


class OptionSelector:
    """
    Option contract selection service
    
    Selects the most appropriate option contracts based on trading signals,
    market conditions, and configured strategies.
    """
    
    def __init__(self, account_config: AccountConfig):
        """Initialize option selector with account configuration"""
        self.account_config = account_config
        self.logger = logging.getLogger(f"{__name__}.{account_config.name}")
    
    def select_option_contract(
        self,
        signal: TradeSignal,
        option_chain: List[OptionContract],
        current_price: Decimal,
        strategy: SelectionStrategy = SelectionStrategy.ATM
    ) -> Optional[OptionContract]:
        """
        Select the best option contract based on signal and strategy
        
        Args:
            signal: Trading signal with direction and parameters
            option_chain: Available option contracts
            current_price: Current price of underlying asset
            strategy: Selection strategy to use
            
        Returns:
            Selected option contract or None if no suitable contract found
        """
        
        if not option_chain:
            self.logger.warning("No option contracts available for selection")
            return None
        
        try:
            # Filter contracts by option type based on signal action
            option_type = self._determine_option_type(signal)
            filtered_contracts = self._filter_by_option_type(option_chain, option_type)
            
            if not filtered_contracts:
                self.logger.warning(f"No {option_type.value} contracts available")
                return None
            
            # Filter by expiration date
            filtered_contracts = self._filter_by_expiration(filtered_contracts)
            
            if not filtered_contracts:
                self.logger.warning("No contracts with suitable expiration dates")
                return None
            
            # Apply selection strategy
            selected_contract = self._apply_selection_strategy(
                filtered_contracts, current_price, strategy
            )
            
            if selected_contract:
                self.logger.info(
                    f"Selected option contract: {selected_contract.symbol} "
                    f"(strike: {selected_contract.strike}, expiry: {selected_contract.expiry})"
                )
            else:
                self.logger.warning("No suitable contract found after applying strategy")
            
            return selected_contract
            
        except Exception as e:
            self.logger.error(f"Error selecting option contract: {e}")
            return None
    
    def _determine_option_type(self, signal: TradeSignal) -> OptionType:
        """Determine option type (call/put) based on signal action"""
        
        if signal.action == OrderSide.BUY:
            # For buy signals, typically use calls for bullish outlook
            return OptionType.CALL
        elif signal.action == OrderSide.SELL:
            # For sell signals, typically use puts for bearish outlook
            return OptionType.PUT
        else:
            # Default to calls
            return OptionType.CALL
    
    def _filter_by_option_type(
        self, 
        contracts: List[OptionContract], 
        option_type: OptionType
    ) -> List[OptionContract]:
        """Filter contracts by option type (call/put)"""
        
        return [
            contract for contract in contracts 
            if contract.option_type == option_type
        ]
    
    def _filter_by_expiration(
        self, 
        contracts: List[OptionContract],
        min_days: int = 7,
        max_days: int = 60
    ) -> List[OptionContract]:
        """
        Filter contracts by expiration date
        
        Args:
            contracts: List of option contracts
            min_days: Minimum days to expiration
            max_days: Maximum days to expiration
        """
        
        now = datetime.now()
        min_expiry = now + timedelta(days=min_days)
        max_expiry = now + timedelta(days=max_days)
        
        filtered = []
        for contract in contracts:
            if contract.expiry:
                expiry_date = contract.expiry
                if isinstance(expiry_date, str):
                    try:
                        expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                
                if min_expiry <= expiry_date <= max_expiry:
                    filtered.append(contract)
        
        return filtered
    
    def _apply_selection_strategy(
        self,
        contracts: List[OptionContract],
        current_price: Decimal,
        strategy: SelectionStrategy
    ) -> Optional[OptionContract]:
        """Apply the specified selection strategy"""
        
        if strategy == SelectionStrategy.ATM:
            return self._select_atm_contract(contracts, current_price)
        elif strategy == SelectionStrategy.OTM:
            return self._select_otm_contract(contracts, current_price)
        elif strategy == SelectionStrategy.ITM:
            return self._select_itm_contract(contracts, current_price)
        elif strategy == SelectionStrategy.HIGH_VOLUME:
            return self._select_high_volume_contract(contracts)
        elif strategy == SelectionStrategy.TIGHT_SPREAD:
            return self._select_tight_spread_contract(contracts)
        else:
            # Default to ATM
            return self._select_atm_contract(contracts, current_price)
    
    def _select_atm_contract(
        self, 
        contracts: List[OptionContract], 
        current_price: Decimal
    ) -> Optional[OptionContract]:
        """Select at-the-money contract (closest to current price)"""
        
        if not contracts:
            return None
        
        # Find contract with strike closest to current price
        best_contract = None
        min_distance = float('inf')
        
        for contract in contracts:
            if contract.strike:
                distance = abs(float(contract.strike) - float(current_price))
                if distance < min_distance:
                    min_distance = distance
                    best_contract = contract
        
        return best_contract
    
    def _select_otm_contract(
        self, 
        contracts: List[OptionContract], 
        current_price: Decimal
    ) -> Optional[OptionContract]:
        """Select out-of-the-money contract"""
        
        if not contracts:
            return None
        
        # For calls: strike > current_price
        # For puts: strike < current_price
        otm_contracts = []
        
        for contract in contracts:
            if not contract.strike:
                continue
                
            if contract.option_type == OptionType.CALL:
                if contract.strike > current_price:
                    otm_contracts.append(contract)
            elif contract.option_type == OptionType.PUT:
                if contract.strike < current_price:
                    otm_contracts.append(contract)
        
        if not otm_contracts:
            return None
        
        # Select the first OTM contract (closest to ATM)
        otm_contracts.sort(key=lambda x: abs(float(x.strike) - float(current_price)))
        return otm_contracts[0]
    
    def _select_itm_contract(
        self, 
        contracts: List[OptionContract], 
        current_price: Decimal
    ) -> Optional[OptionContract]:
        """Select in-the-money contract"""
        
        if not contracts:
            return None
        
        # For calls: strike < current_price
        # For puts: strike > current_price
        itm_contracts = []
        
        for contract in contracts:
            if not contract.strike:
                continue
                
            if contract.option_type == OptionType.CALL:
                if contract.strike < current_price:
                    itm_contracts.append(contract)
            elif contract.option_type == OptionType.PUT:
                if contract.strike > current_price:
                    itm_contracts.append(contract)
        
        if not itm_contracts:
            return None
        
        # Select the first ITM contract (closest to ATM)
        itm_contracts.sort(key=lambda x: abs(float(x.strike) - float(current_price)))
        return itm_contracts[0]
    
    def _select_high_volume_contract(
        self, 
        contracts: List[OptionContract]
    ) -> Optional[OptionContract]:
        """Select contract with highest volume"""
        
        if not contracts:
            return None
        
        # Sort by volume (descending)
        volume_contracts = [c for c in contracts if c.volume and c.volume > 0]
        
        if not volume_contracts:
            # Fallback to first contract if no volume data
            return contracts[0]
        
        volume_contracts.sort(key=lambda x: x.volume, reverse=True)
        return volume_contracts[0]
    
    def _select_tight_spread_contract(
        self, 
        contracts: List[OptionContract]
    ) -> Optional[OptionContract]:
        """Select contract with tightest bid-ask spread"""
        
        if not contracts:
            return None
        
        # Calculate spreads and select tightest
        spread_contracts = []
        
        for contract in contracts:
            if contract.bid and contract.ask and contract.bid > 0 and contract.ask > 0:
                spread = float(contract.ask) - float(contract.bid)
                spread_pct = spread / float(contract.ask) if contract.ask > 0 else float('inf')
                spread_contracts.append((contract, spread_pct))
        
        if not spread_contracts:
            # Fallback to first contract if no bid/ask data
            return contracts[0]
        
        # Sort by spread percentage (ascending)
        spread_contracts.sort(key=lambda x: x[1])
        return spread_contracts[0][0]
    
    def get_selection_recommendations(
        self,
        signal: TradeSignal,
        option_chain: List[OptionContract],
        current_price: Decimal
    ) -> Dict[str, Optional[OptionContract]]:
        """
        Get recommendations for all selection strategies
        
        Returns a dictionary with strategy names as keys and selected contracts as values
        """
        
        recommendations = {}
        
        for strategy in SelectionStrategy:
            try:
                selected = self.select_option_contract(
                    signal, option_chain, current_price, strategy
                )
                recommendations[strategy.value] = selected
            except Exception as e:
                self.logger.error(f"Error getting recommendation for {strategy.value}: {e}")
                recommendations[strategy.value] = None
        
        return recommendations
