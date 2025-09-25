"""
Options Strategy Fallback System
Provides fallback mechanisms when options data is unavailable
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import numpy as np

try:
    from ...services.options.mock_options_data_service import get_mock_options_service, MockOptionsContract
except ImportError:
    # Fallback for standalone imports
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/options'))
    from mock_options_data_service import get_mock_options_service, MockOptionsContract

logger = logging.getLogger(__name__)


class OptionsStrategyFallback:
    """Fallback system for options strategies when real data is unavailable"""
    
    def __init__(self):
        self.logger = logger
        self.mock_service = get_mock_options_service()
        self.fallback_mode = True  # Always use mock data for now
        
    def get_options_data(self, symbol: str, strategy_type: str, **kwargs) -> Dict[str, Any]:
        """
        Get options data with fallback to mock data
        
        Args:
            symbol: Stock symbol
            strategy_type: Type of options strategy (iron_condor, butterfly, calendar)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with options data or fallback information
        """
        try:
            if self.fallback_mode:
                return self._get_mock_options_data(symbol, strategy_type, **kwargs)
            else:
                # Try real options data service first
                return self._get_real_options_data(symbol, strategy_type, **kwargs)
                
        except Exception as e:
            self.logger.warning(f"Options data service failed for {symbol}, using fallback: {e}")
            return self._get_mock_options_data(symbol, strategy_type, **kwargs)
    
    def _get_mock_options_data(self, symbol: str, strategy_type: str, **kwargs) -> Dict[str, Any]:
        """Get mock options data for strategy"""
        
        # Get liquid options
        contracts = self.mock_service.get_liquid_options(symbol)
        
        if not contracts:
            return self._create_empty_options_data(symbol, strategy_type)
        
        # Strategy-specific data selection
        if strategy_type == 'iron_condor':
            return self._prepare_iron_condor_data(contracts, symbol)
        elif strategy_type == 'butterfly_spread':
            return self._prepare_butterfly_data(contracts, symbol)
        elif strategy_type == 'calendar_spread':
            return self._prepare_calendar_data(contracts, symbol)
        else:
            return self._prepare_generic_options_data(contracts, symbol)
    
    def _prepare_iron_condor_data(self, contracts: List[MockOptionsContract], symbol: str) -> Dict[str, Any]:
        """Prepare options data for Iron Condor strategy"""
        
        # Get current stock price
        current_price = self.mock_service._get_mock_stock_price(symbol)
        
        # Find appropriate strikes for iron condor
        # Iron Condor: Sell call spread + Sell put spread
        
        # Find strikes around current price
        strikes = sorted([c.strike for c in contracts if c.expiration == min(c.expiration for c in contracts)])
        
        if len(strikes) < 4:
            return self._create_empty_options_data(symbol, 'iron_condor')
        
        # Select strikes for iron condor
        center_idx = len(strikes) // 2
        put_strikes = strikes[center_idx-2:center_idx]
        call_strikes = strikes[center_idx:center_idx+2]
        
        # Get specific contracts
        expiration = min(c.expiration for c in contracts)
        
        data = {
            'symbol': symbol,
            'current_price': current_price,
            'expiration': expiration,
            'strategy_type': 'iron_condor',
            'put_spread': {
                'short_strike': put_strikes[1] if len(put_strikes) > 1 else put_strikes[0],
                'long_strike': put_strikes[0],
                'short_put': self._find_contract(contracts, put_strikes[1], 'put', expiration),
                'long_put': self._find_contract(contracts, put_strikes[0], 'put', expiration)
            },
            'call_spread': {
                'short_strike': call_strikes[0] if len(call_strikes) > 1 else call_strikes[0],
                'long_strike': call_strikes[1] if len(call_strikes) > 1 else call_strikes[0],
                'short_call': self._find_contract(contracts, call_strikes[0], 'call', expiration),
                'long_call': self._find_contract(contracts, call_strikes[1], 'call', expiration)
            },
            'net_credit': 0.0,
            'max_profit': 0.0,
            'max_loss': 0.0,
            'break_even_points': [],
            'data_source': 'mock'
        }
        
        # Calculate strategy metrics
        self._calculate_iron_condor_metrics(data)
        
        return data
    
    def _prepare_butterfly_data(self, contracts: List[MockOptionsContract], symbol: str) -> Dict[str, Any]:
        """Prepare options data for Butterfly Spread strategy"""
        
        current_price = self.mock_service._get_mock_stock_price(symbol)
        strikes = sorted([c.strike for c in contracts if c.expiration == min(c.expiration for c in contracts)])
        
        if len(strikes) < 3:
            return self._create_empty_options_data(symbol, 'butterfly_spread')
        
        # Select strikes for butterfly (center strike + wings)
        center_idx = len(strikes) // 2
        center_strike = strikes[center_idx]
        
        # Find wing strikes
        wing_strikes = [strikes[center_idx-1], strikes[center_idx+1]] if center_idx > 0 and center_idx < len(strikes)-1 else strikes[:3]
        
        expiration = min(c.expiration for c in contracts)
        
        data = {
            'symbol': symbol,
            'current_price': current_price,
            'expiration': expiration,
            'strategy_type': 'butterfly_spread',
            'center_strike': center_strike,
            'wing_strikes': wing_strikes,
            'long_wing': self._find_contract(contracts, wing_strikes[0], 'call', expiration),
            'short_center': self._find_contract(contracts, center_strike, 'call', expiration),
            'long_wing_2': self._find_contract(contracts, wing_strikes[1], 'call', expiration),
            'net_debit': 0.0,
            'max_profit': 0.0,
            'max_loss': 0.0,
            'break_even_points': [],
            'data_source': 'mock'
        }
        
        self._calculate_butterfly_metrics(data)
        
        return data
    
    def _prepare_calendar_data(self, contracts: List[MockOptionsContract], symbol: str) -> Dict[str, Any]:
        """Prepare options data for Calendar Spread strategy"""
        
        current_price = self.mock_service._get_mock_stock_price(symbol)
        
        # Group contracts by expiration
        expirations = sorted(set(c.expiration for c in contracts))
        
        if len(expirations) < 2:
            return self._create_empty_options_data(symbol, 'calendar_spread')
        
        # Select strikes around current price
        near_expiration = expirations[0]
        far_expiration = expirations[1]
        
        near_contracts = [c for c in contracts if c.expiration == near_expiration]
        far_contracts = [c for c in contracts if c.expiration == far_expiration]
        
        # Find strike closest to current price
        target_strike = self._find_closest_strike(near_contracts, current_price)
        
        data = {
            'symbol': symbol,
            'current_price': current_price,
            'near_expiration': near_expiration,
            'far_expiration': far_expiration,
            'strike': target_strike,
            'strategy_type': 'calendar_spread',
            'short_near': self._find_contract(near_contracts, target_strike, 'call', near_expiration),
            'long_far': self._find_contract(far_contracts, target_strike, 'call', far_expiration),
            'net_debit': 0.0,
            'max_profit': 0.0,
            'max_loss': 0.0,
            'break_even_points': [],
            'data_source': 'mock'
        }
        
        self._calculate_calendar_metrics(data)
        
        return data
    
    def _prepare_generic_options_data(self, contracts: List[MockOptionsContract], symbol: str) -> Dict[str, Any]:
        """Prepare generic options data"""
        return {
            'symbol': symbol,
            'current_price': self.mock_service._get_mock_stock_price(symbol),
            'contracts': contracts[:10],  # Limit to first 10 contracts
            'strategy_type': 'generic',
            'data_source': 'mock'
        }
    
    def _find_contract(self, contracts: List[MockOptionsContract], strike: float, 
                      option_type: str, expiration: datetime) -> Optional[MockOptionsContract]:
        """Find specific options contract"""
        for contract in contracts:
            if (contract.strike == strike and 
                contract.option_type == option_type and
                contract.expiration == expiration):
                return contract
        return None
    
    def _find_closest_strike(self, contracts: List[MockOptionsContract], target_price: float) -> float:
        """Find strike closest to target price"""
        if not contracts:
            return target_price
        
        strikes = [c.strike for c in contracts]
        return min(strikes, key=lambda x: abs(x - target_price))
    
    def _calculate_iron_condor_metrics(self, data: Dict[str, Any]) -> None:
        """Calculate Iron Condor strategy metrics"""
        try:
            # Calculate net credit (simplified)
            put_spread = data['put_spread']
            call_spread = data['call_spread']
            
            # Net credit = (short put bid + short call bid) - (long put ask + long call ask)
            net_credit = 0.0
            if put_spread['short_put'] and put_spread['long_put']:
                net_credit += put_spread['short_put'].bid - put_spread['long_put'].ask
            
            if call_spread['short_call'] and call_spread['long_call']:
                net_credit += call_spread['short_call'].bid - call_spread['long_call'].ask
            
            data['net_credit'] = max(0.0, net_credit)
            data['max_profit'] = data['net_credit']
            
            # Max loss = strike width - net credit
            put_width = put_spread['short_strike'] - put_spread['long_strike']
            call_width = call_spread['long_strike'] - call_spread['short_strike']
            max_loss = max(put_width, call_width) - data['net_credit']
            data['max_loss'] = max(0.0, max_loss)
            
        except Exception as e:
            self.logger.warning(f"Error calculating iron condor metrics: {e}")
    
    def _calculate_butterfly_metrics(self, data: Dict[str, Any]) -> None:
        """Calculate Butterfly Spread strategy metrics"""
        try:
            # Calculate net debit
            net_debit = 0.0
            if data['long_wing'] and data['short_center'] and data['long_wing_2']:
                net_debit = (data['long_wing'].ask + data['long_wing_2'].ask) - (data['short_center'].bid * 2)
            
            data['net_debit'] = max(0.0, net_debit)
            data['max_profit'] = data['center_strike'] - data['wing_strikes'][0] - data['net_debit']
            data['max_loss'] = data['net_debit']
            
        except Exception as e:
            self.logger.warning(f"Error calculating butterfly metrics: {e}")
    
    def _calculate_calendar_metrics(self, data: Dict[str, Any]) -> None:
        """Calculate Calendar Spread strategy metrics"""
        try:
            # Calculate net debit
            net_debit = 0.0
            if data['long_far'] and data['short_near']:
                net_debit = data['long_far'].ask - data['short_near'].bid
            
            data['net_debit'] = max(0.0, net_debit)
            data['max_profit'] = data['short_near'].last_price - data['net_debit']  # Simplified
            data['max_loss'] = data['net_debit']
            
        except Exception as e:
            self.logger.warning(f"Error calculating calendar metrics: {e}")
    
    def _create_empty_options_data(self, symbol: str, strategy_type: str) -> Dict[str, Any]:
        """Create empty options data structure"""
        return {
            'symbol': symbol,
            'strategy_type': strategy_type,
            'current_price': 0.0,
            'contracts': [],
            'error': 'No options data available',
            'data_source': 'empty',
            'fallback_available': True,
            'suggested_alternative': 'Consider stock-based strategies or wait for options data'
        }
    
    def _get_real_options_data(self, symbol: str, strategy_type: str, **kwargs) -> Dict[str, Any]:
        """Try to get real options data (placeholder for future implementation)"""
        # This would integrate with real options data services
        self.logger.info(f"Attempting to get real options data for {symbol}")
        raise NotImplementedError("Real options data service not yet implemented")


# Global instance for easy access
_options_fallback = None

def get_options_fallback() -> OptionsStrategyFallback:
    """Get global options strategy fallback instance"""
    global _options_fallback
    if _options_fallback is None:
        _options_fallback = OptionsStrategyFallback()
    return _options_fallback
