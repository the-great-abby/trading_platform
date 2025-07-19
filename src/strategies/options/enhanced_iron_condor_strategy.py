"""
Enhanced Iron Condor Options Strategy with Cache Integration
==========================================================
A strategy that sells out-of-the-money calls and puts to profit from low volatility environments.
Enhanced with options data cache integration for better performance and accuracy.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, date
import logging

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger
from src.services.market_data.options_data_service import OptionsDataService, OptionContract

logger = get_trading_logger()

class EnhancedIronCondorStrategy(BaseStrategy):
    """
    Enhanced Iron Condor Options Strategy with Cache Integration
    
    Features:
    - Sells out-of-the-money calls and puts
    - Profits from low volatility environments
    - Defined risk and reward
    - High probability of profit in sideways markets
    - Dynamic strike selection based on volatility
    - Integrated options data cache for performance
    - Real-time Greeks calculations
    - Historical volatility analysis
    """
    
    def __init__(self, 
                 name: str = "EnhancedIronCondor",
                 days_to_expiration: int = 45,
                 profit_target_pct: float = 0.5,  # 50% of max profit
                 stop_loss_pct: float = 2.0,  # 2x max profit
                 max_risk_per_trade: float = 0.02,  # 2% of portfolio
                 volatility_threshold: float = 0.3,  # 30% IV threshold
                 min_dte: int = 30,
                 max_dte: int = 60,
                 min_volume: int = 10,  # Minimum volume for liquidity
                 min_open_interest: int = 50,  # Minimum open interest
                 cache_lookback_days: int = 30):  # Days to look back in cache
        
        super().__init__(name)
        self.days_to_expiration = days_to_expiration
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_risk_per_trade = max_risk_per_trade
        self.volatility_threshold = volatility_threshold
        self.min_dte = min_dte
        self.max_dte = max_dte
        self.min_volume = min_volume
        self.min_open_interest = min_open_interest
        self.cache_lookback_days = cache_lookback_days
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # Strategy state
        self.active_positions = {}
        self.position_history = []
        
    def get_cached_options_data(self, symbol: str, target_date: date) -> Optional[List[Dict]]:
        """Get options data from cache for a specific date"""
        try:
            from src.services.database.market_data_service import MarketDataService
            market_data_service = MarketDataService()
            
            # Get historical options data from cache
            cached_data = market_data_service.get_historical_options_data(
                symbol, target_date
            )
            
            if cached_data:
                logger.info(f"📊 Found {len(cached_data)} cached options contracts for {symbol} on {target_date}")
                return cached_data
            else:
                logger.debug(f"📊 No cached options data found for {symbol} on {target_date}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting cached options data for {symbol}: {e}")
            return None
    
    def get_available_expiration_dates(self, symbol: str) -> List[str]:
        """Get available expiration dates from cache"""
        try:
            from src.services.database.market_data_service import MarketDataService
            market_data_service = MarketDataService()
            
            # Get available dates
            available_dates = market_data_service.get_available_historical_dates(symbol)
            
            if not available_dates:
                return []
            
            # Get most recent date
            latest_date = max(available_dates)
            
            # Get options data for latest date
            options_data = market_data_service.get_historical_options_data(symbol, latest_date)
            
            if not options_data:
                return []
            
            # Extract unique expiration dates
            expirations = list(set([contract['expiration'] for contract in options_data]))
            expirations.sort()
            
            logger.info(f"📅 Found {len(expirations)} available expiration dates for {symbol}")
            return expirations
            
        except Exception as e:
            logger.error(f"❌ Error getting expiration dates for {symbol}: {e}")
            return []
    
    def find_optimal_expiration(self, symbol: str, target_dte: int) -> Optional[str]:
        """Find optimal expiration date closest to target DTE"""
        expirations = self.get_available_expiration_dates(symbol)
        
        if not expirations:
            return None
        
        # Calculate target date
        target_date = datetime.now().date() + timedelta(days=target_dte)
        
        # Find closest expiration
        closest_expiration = None
        min_difference = float('inf')
        
        for expiration in expirations:
            try:
                exp_date = datetime.strptime(expiration, '%Y-%m-%d').date()
                difference = abs((exp_date - datetime.now().date()).days - target_dte)
                
                if difference < min_difference:
                    min_difference = difference
                    closest_expiration = expiration
                    
            except ValueError:
                continue
        
        if closest_expiration:
            logger.info(f"🎯 Selected expiration {closest_expiration} for {symbol} (target DTE: {target_dte})")
        
        return closest_expiration
    
    def get_liquid_options_chain(self, symbol: str, expiration: str, current_price: float) -> Optional[List[OptionContract]]:
        """Get liquid options chain from cache for specific expiration"""
        try:
            from src.services.database.market_data_service import MarketDataService
            market_data_service = MarketDataService()
            
            # Get available dates
            available_dates = market_data_service.get_available_historical_dates(symbol)
            
            if not available_dates:
                return None
            
            # Use most recent date
            latest_date = max(available_dates)
            
            # Get options data
            options_data = market_data_service.get_historical_options_data(symbol, latest_date, expiration)
            
            if not options_data:
                return None
            
            # Convert to OptionContract objects and filter for liquidity
            contracts = []
            for contract_data in options_data:
                if (contract_data.get('volume', 0) >= self.min_volume and 
                    contract_data.get('open_interest', 0) >= self.min_open_interest):
                    
                    contract = OptionContract(
                        symbol=contract_data['symbol'],
                        strike=contract_data['strike'],
                        expiration=contract_data['expiration'],
                        option_type=contract_data['option_type'],
                        price=contract_data['price'],
                        volume=contract_data['volume'],
                        open_interest=contract_data['open_interest'],
                        delta=contract_data.get('delta'),
                        gamma=contract_data.get('gamma'),
                        theta=contract_data.get('theta'),
                        vega=contract_data.get('vega'),
                        implied_volatility=contract_data.get('implied_volatility')
                    )
                    contracts.append(contract)
            
            logger.info(f"💧 Found {len(contracts)} liquid options contracts for {symbol} {expiration}")
            return contracts
            
        except Exception as e:
            logger.error(f"❌ Error getting liquid options chain for {symbol}: {e}")
            return None
    
    def calculate_implied_volatility(self, options_data: List[OptionContract]) -> float:
        """Calculate weighted average implied volatility from options data"""
        if not options_data:
            return 0.0
        
        total_weight = 0
        weighted_iv_sum = 0
        
        for contract in options_data:
            if contract.implied_volatility is not None and contract.volume > 0:
                # Weight by volume
                weight = contract.volume
                weighted_iv_sum += contract.implied_volatility * weight
                total_weight += weight
        
        if total_weight > 0:
            return weighted_iv_sum / total_weight
        else:
            # Fallback to simple average
            valid_ivs = [c.implied_volatility for c in options_data if c.implied_volatility is not None]
            return np.mean(valid_ivs) if valid_ivs else 0.0
    
    def select_strikes_from_cache(self, symbol: str, current_price: float, expiration: str) -> Optional[Dict[str, float]]:
        """Select strikes for Iron Condor using cached options data"""
        
        # Get liquid options chain
        options_chain = self.get_liquid_options_chain(symbol, expiration, current_price)
        
        if not options_chain:
            logger.warning(f"⚠️  No liquid options chain found for {symbol} {expiration}")
            return None
        
        # Calculate implied volatility
        iv = self.calculate_implied_volatility(options_chain)
        if iv == 0:
            iv = 0.3  # Default IV if not available
        
        # Calculate expected move
        dte = (datetime.strptime(expiration, '%Y-%m-%d').date() - datetime.now().date()).days
        expected_move = current_price * iv * np.sqrt(dte / 365)
        
        # Find suitable strikes
        put_strikes = []
        call_strikes = []
        
        for contract in options_chain:
            if contract.option_type == 'put' and contract.strike < current_price:
                put_strikes.append(contract.strike)
            elif contract.option_type == 'call' and contract.strike > current_price:
                call_strikes.append(contract.strike)
        
        if not put_strikes or not call_strikes:
            logger.warning(f"⚠️  Insufficient strike options for {symbol}")
            return None
        
        # Select optimal strikes
        put_strikes.sort(reverse=True)  # Closest to current price
        call_strikes.sort()  # Closest to current price
        
        # Select strikes based on expected move
        target_put_distance = expected_move / 3
        target_call_distance = expected_move / 3
        
        # Find closest strikes to target distances
        selected_put = None
        selected_call = None
        
        for strike in put_strikes:
            if strike <= current_price - target_put_distance:
                selected_put = strike
                break
        
        for strike in call_strikes:
            if strike >= current_price + target_call_distance:
                selected_call = strike
                break
        
        if not selected_put or not selected_call:
            logger.warning(f"⚠️  Could not find suitable strikes for {symbol}")
            return None
        
        # Calculate spread width (typically 2-5 points)
        spread_width = max(2, min(5, expected_move / 4))
        
        return {
            'put_strike': selected_put,
            'call_strike': selected_call,
            'put_spread_width': spread_width,
            'call_spread_width': spread_width,
            'expected_move': expected_move,
            'implied_volatility': iv,
            'dte': dte,
            'current_price': current_price
        }
    
    def calculate_position_metrics(self, strikes: Dict[str, float], options_chain: List[OptionContract]) -> Dict[str, float]:
        """Calculate detailed position metrics using cached options data"""
        
        # Find actual option prices from chain
        put_price = None
        call_price = None
        
        for contract in options_chain:
            if (contract.option_type == 'put' and 
                abs(contract.strike - strikes['put_strike']) < 0.01):
                put_price = contract.price
            elif (contract.option_type == 'call' and 
                  abs(contract.strike - strikes['call_strike']) < 0.01):
                call_price = contract.price
        
        if put_price is None or call_price is None:
            logger.warning(f"⚠️  Could not find option prices for strikes")
            return {}
        
        # Calculate position metrics
        max_risk = self.calculate_max_risk(strikes)
        max_profit = self.calculate_max_profit(strikes)
        
        # Calculate Greeks (if available)
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        
        for contract in options_chain:
            if (contract.option_type == 'put' and 
                abs(contract.strike - strikes['put_strike']) < 0.01):
                if contract.delta is not None:
                    total_delta += contract.delta
                if contract.gamma is not None:
                    total_gamma += contract.gamma
                if contract.theta is not None:
                    total_theta += contract.theta
                if contract.vega is not None:
                    total_vega += contract.vega
            elif (contract.option_type == 'call' and 
                  abs(contract.strike - strikes['call_strike']) < 0.01):
                if contract.delta is not None:
                    total_delta += contract.delta
                if contract.gamma is not None:
                    total_gamma += contract.gamma
                if contract.theta is not None:
                    total_theta += contract.theta
                if contract.vega is not None:
                    total_vega += contract.vega
        
        return {
            'max_risk': max_risk,
            'max_profit': max_profit,
            'risk_reward_ratio': max_profit / max_risk if max_risk > 0 else 0,
            'put_price': put_price,
            'call_price': call_price,
            'total_delta': total_delta,
            'total_gamma': total_gamma,
            'total_theta': total_theta,
            'total_vega': total_vega,
            'implied_volatility': strikes['implied_volatility'],
            'dte': strikes['dte']
        }
    
    def check_market_conditions(self, data: pd.DataFrame, options_chain: List[OptionContract]) -> bool:
        """Check if market conditions are suitable for Iron Condor using cached data"""
        
        if len(data) < 20:
            return False
        
        # Check volatility from options data
        iv = self.calculate_implied_volatility(options_chain)
        if iv < self.volatility_threshold:
            logger.debug(f"📊 IV {iv:.3f} below threshold {self.volatility_threshold}")
            return False
        
        # Check for strong trending market (avoid in strong trends)
        price_change_20d = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
        if abs(price_change_20d) > 0.1:  # More than 10% move in 20 days
            logger.debug(f"📊 Strong trend detected: {price_change_20d:.3f}")
            return False
        
        # Check for high volatility period
        volatility_20d = data['Close'].pct_change().rolling(20).std().iloc[-1]
        if volatility_20d > 0.03:  # More than 3% daily volatility
            logger.debug(f"📊 High volatility detected: {volatility_20d:.3f}")
            return False
        
        # Check options liquidity
        liquid_contracts = [c for c in options_chain if c.volume >= self.min_volume and c.open_interest >= self.min_open_interest]
        if len(liquid_contracts) < 10:  # Need sufficient liquidity
            logger.debug(f"📊 Insufficient liquidity: {len(liquid_contracts)} liquid contracts")
            return False
        
        return True
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame, 
                            options_data: Optional[Dict[str, Any]] = None) -> Optional[TradeSignal]:
        """Generate enhanced Iron Condor signal using cached options data"""
        
        if len(data) < 20:
            return None
        
        current_price = data['Close'].iloc[-1]
        
        # Find optimal expiration
        expiration = self.find_optimal_expiration(symbol, self.days_to_expiration)
        if not expiration:
            logger.debug(f"📊 No suitable expiration found for {symbol}")
            return None
        
        # Get liquid options chain
        options_chain = self.get_liquid_options_chain(symbol, expiration, current_price)
        if not options_chain:
            logger.debug(f"📊 No liquid options chain for {symbol}")
            return None
        
        # Check market conditions
        if not self.check_market_conditions(data, options_chain):
            return None
        
        # Select strikes using cached data
        strikes = self.select_strikes_from_cache(symbol, current_price, expiration)
        if not strikes:
            return None
        
        # Calculate position metrics
        metrics = self.calculate_position_metrics(strikes, options_chain)
        if not metrics:
            return None
        
        # Only trade if risk/reward is acceptable
        if metrics['risk_reward_ratio'] < 0.3:  # At least 30% profit potential
            logger.debug(f"📊 Risk/reward ratio {metrics['risk_reward_ratio']:.3f} below threshold")
            return None
        
        # Calculate confidence based on market conditions and options data
        confidence = self._calculate_enhanced_confidence(data, options_chain, strikes, metrics)
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action="ENHANCED_IRON_CONDOR",
            quantity=1,  # One Iron Condor position
            price=current_price,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=confidence,
            metadata={
                'strikes': strikes,
                'metrics': metrics,
                'expiration': expiration,
                'options_chain_size': len(options_chain),
                'liquid_contracts': len([c for c in options_chain if c.volume >= self.min_volume]),
                'signal_type': 'enhanced_iron_condor',
                'position_size': self.max_risk_per_trade / metrics['max_risk'] if metrics['max_risk'] > 0 else 0,
                'profit_target': metrics['max_profit'] * self.profit_target_pct,
                'stop_loss': metrics['max_risk'] * self.stop_loss_pct
            }
        )
        
        logger.info(f"🎯 Enhanced Iron Condor signal: {symbol} (confidence: {confidence:.3f}, "
                   f"risk/reward: {metrics['risk_reward_ratio']:.3f}, IV: {metrics['implied_volatility']:.3f})")
        
        return signal
    
    def _calculate_enhanced_confidence(self, data: pd.DataFrame, options_chain: List[OptionContract], 
                                     strikes: Dict[str, float], metrics: Dict[str, float]) -> float:
        """Calculate enhanced confidence using options data"""
        
        confidence = 0.5  # Base confidence
        
        # Volatility factor
        iv = metrics['implied_volatility']
        if 0.2 <= iv <= 0.4:  # Optimal IV range
            confidence += 0.2
        elif iv > 0.4:
            confidence -= 0.1
        
        # Market trend factor
        price_change_20d = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
        if abs(price_change_20d) < 0.05:  # Low trend
            confidence += 0.2
        elif abs(price_change_20d) > 0.15:  # High trend
            confidence -= 0.3
        
        # Risk/reward factor
        risk_reward_ratio = metrics['risk_reward_ratio']
        if risk_reward_ratio > 0.5:
            confidence += 0.1
        elif risk_reward_ratio < 0.2:
            confidence -= 0.2
        
        # Liquidity factor
        liquid_contracts = len([c for c in options_chain if c.volume >= self.min_volume])
        if liquid_contracts > 20:
            confidence += 0.1
        elif liquid_contracts < 10:
            confidence -= 0.1
        
        # Greeks factor
        if abs(metrics['total_delta']) < 0.1:  # Near delta neutral
            confidence += 0.1
        if metrics['total_theta'] > 0:  # Positive theta (time decay)
            confidence += 0.1
        
        # Time to expiration factor
        dte = metrics['dte']
        if self.min_dte <= dte <= self.max_dte:
            confidence += 0.1
        
        return min(max(confidence, 0.1), 0.9)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "days_to_expiration": self.days_to_expiration,
            "profit_target_pct": self.profit_target_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "max_risk_per_trade": self.max_risk_per_trade,
            "volatility_threshold": self.volatility_threshold,
            "min_dte": self.min_dte,
            "max_dte": self.max_dte,
            "min_volume": self.min_volume,
            "min_open_interest": self.min_open_interest,
            "cache_lookback_days": self.cache_lookback_days,
            "features": [
                "Cache-integrated options data",
                "Real-time Greeks calculations",
                "Liquidity filtering",
                "Enhanced confidence scoring",
                "Historical volatility analysis"
            ]
        }
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get position summary"""
        return {
            "active_positions": len(self.active_positions),
            "total_positions": len(self.position_history),
            "cache_stats": self.options_service.get_cache_stats() if hasattr(self, 'options_service') else {}
        } 