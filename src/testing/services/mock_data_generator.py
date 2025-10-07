#!/usr/bin/env python3
"""
MockDataGenerator service for Strategy Engine Testing Framework
Generates realistic mock market data for testing strategies
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..models import (
    MockMarketData, MockDataGenerationConfig, PriceBar,
    MarketRegime, TimeFrame, validate_market_regime, validate_timeframe
)


class MockDataGenerator:
    """
    Generates realistic mock market data for testing strategies
    
    Creates data with various market regimes, patterns, and conditions
    """
    
    def __init__(self):
        """Initialize mock data generator"""
        self.default_config = {
            'volatility': 0.2,
            'trend_strength': 0.0,
            'volume_pattern': 'normal',
            'noise_level': 0.1,
            'gaps_probability': 0.05
        }
    
    async def generate_mock_data(self, config: MockDataGenerationConfig) -> MockMarketData:
        """
        Generate mock market data based on configuration
        
        Args:
            config: Data generation configuration
            
        Returns:
            MockMarketData with generated price bars
        """
        try:
            # Validate configuration
            self._validate_config(config)
            
            # Generate price data based on market regime
            price_data = await self._generate_price_data(config)
            
            # Create price bars
            price_bars = []
            for i, row in price_data.iterrows():
                bar = PriceBar(
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    symbol=config.symbol
                )
                price_bars.append(bar)
            
            # Calculate data quality score
            quality_score = self._calculate_data_quality(price_bars, config)
            
            # Create generation metadata
            generation_metadata = {
                'volatility': config.volatility,
                'trend_strength': config.trend_strength,
                'volume_pattern': config.volume_pattern,
                'noise_level': config.noise_level,
                'gaps_probability': config.gaps_probability,
                'generated_at': datetime.utcnow().isoformat(),
                'data_points': len(price_bars)
            }
            
            return MockMarketData(
                symbol=config.symbol,
                timeframe=config.timeframe,
                start_date=config.start_date,
                end_date=config.end_date,
                market_regime=config.market_regime,
                price_data=price_bars,
                generation_metadata=generation_metadata,
                data_quality_score=quality_score
            )
            
        except Exception as e:
            # Return empty data on error
            return MockMarketData(
                symbol=config.symbol,
                timeframe=config.timeframe,
                start_date=config.start_date,
                end_date=config.end_date,
                market_regime=config.market_regime,
                price_data=[],
                generation_metadata={'error': str(e)},
                data_quality_score=0.0
            )
    
    def _validate_config(self, config: MockDataGenerationConfig) -> None:
        """Validate generation configuration"""
        if not validate_timeframe(config.timeframe):
            raise ValueError(f"Invalid timeframe: {config.timeframe}")
        
        if not validate_market_regime(config.market_regime):
            raise ValueError(f"Invalid market regime: {config.market_regime}")
        
        if config.start_date >= config.end_date:
            raise ValueError("Start date must be before end date")
        
        if config.initial_price <= 0:
            raise ValueError("Initial price must be positive")
        
        if not (0.0 <= config.volatility <= 1.0):
            raise ValueError("Volatility must be between 0.0 and 1.0")
        
        if not (-1.0 <= config.trend_strength <= 1.0):
            raise ValueError("Trend strength must be between -1.0 and 1.0")
    
    async def _generate_price_data(self, config: MockDataGenerationConfig) -> pd.DataFrame:
        """Generate price data based on configuration"""
        # Calculate number of periods
        timeframe_minutes = self._get_timeframe_minutes(config.timeframe)
        total_minutes = (config.end_date - config.start_date).total_seconds() / 60
        num_periods = int(total_minutes / timeframe_minutes)
        
        # Generate timestamps
        timestamps = pd.date_range(
            start=config.start_date,
            periods=num_periods,
            freq=f'{timeframe_minutes}min'
        )
        
        # Generate base price series based on market regime
        if config.market_regime == MarketRegime.BULL:
            price_series = self._generate_bull_market_prices(
                config.initial_price, num_periods, config.volatility, config.trend_strength
            )
        elif config.market_regime == MarketRegime.BEAR:
            price_series = self._generate_bear_market_prices(
                config.initial_price, num_periods, config.volatility, config.trend_strength
            )
        elif config.market_regime == MarketRegime.SIDEWAYS:
            price_series = self._generate_sideways_market_prices(
                config.initial_price, num_periods, config.volatility
            )
        elif config.market_regime == MarketRegime.VOLATILE:
            price_series = self._generate_volatile_market_prices(
                config.initial_price, num_periods, config.volatility
            )
        else:
            # Default to random walk
            price_series = self._generate_random_walk_prices(
                config.initial_price, num_periods, config.volatility
            )
        
        # Generate OHLC data from price series
        ohlc_data = self._generate_ohlc_from_prices(price_series, config)
        
        # Generate volume data
        volume_data = self._generate_volume_data(num_periods, config.volume_pattern)
        
        # Create DataFrame
        data = pd.DataFrame({
            'timestamp': timestamps,
            'open': ohlc_data['open'],
            'high': ohlc_data['high'],
            'low': ohlc_data['low'],
            'close': ohlc_data['close'],
            'volume': volume_data
        })
        
        # Add gaps if specified
        if config.gaps_probability > 0:
            data = self._add_gaps_to_data(data, config.gaps_probability)
        
        return data
    
    def _get_timeframe_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes"""
        timeframe_map = {
            TimeFrame.ONE_MINUTE: 1,
            TimeFrame.FIVE_MINUTE: 5,
            TimeFrame.FIFTEEN_MINUTE: 15,
            TimeFrame.ONE_HOUR: 60,
            TimeFrame.FOUR_HOUR: 240,
            TimeFrame.ONE_DAY: 1440
        }
        return timeframe_map.get(timeframe, 60)  # Default to 1 hour
    
    def _generate_bull_market_prices(self, initial_price: float, num_periods: int,
                                   volatility: float, trend_strength: float) -> np.ndarray:
        """Generate bullish market price series"""
        # Strong upward trend
        trend = np.linspace(0, trend_strength * 0.5, num_periods)
        
        # Add volatility with upward bias
        returns = np.random.normal(0.001, volatility * 0.01, num_periods)
        returns += trend / num_periods  # Add trend component
        
        # Generate prices
        prices = [initial_price]
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))  # Ensure positive prices
        
        return np.array(prices)
    
    def _generate_bear_market_prices(self, initial_price: float, num_periods: int,
                                   volatility: float, trend_strength: float) -> np.ndarray:
        """Generate bearish market price series"""
        # Strong downward trend
        trend = np.linspace(0, -abs(trend_strength) * 0.5, num_periods)
        
        # Add volatility with downward bias
        returns = np.random.normal(-0.001, volatility * 0.01, num_periods)
        returns += trend / num_periods  # Add trend component
        
        # Generate prices
        prices = [initial_price]
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))  # Ensure positive prices
        
        return np.array(prices)
    
    def _generate_sideways_market_prices(self, initial_price: float, num_periods: int,
                                       volatility: float) -> np.ndarray:
        """Generate sideways market price series"""
        # No trend, just volatility around initial price
        returns = np.random.normal(0, volatility * 0.01, num_periods)
        
        # Generate prices
        prices = [initial_price]
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))  # Ensure positive prices
        
        return np.array(prices)
    
    def _generate_volatile_market_prices(self, initial_price: float, num_periods: int,
                                       volatility: float) -> np.ndarray:
        """Generate volatile market price series"""
        # High volatility with occasional spikes
        base_volatility = volatility * 0.02
        spike_probability = 0.1
        
        returns = []
        for i in range(num_periods):
            if np.random.random() < spike_probability:
                # Volatility spike
                spike_magnitude = np.random.choice([-1, 1]) * volatility * 0.05
                returns.append(spike_magnitude)
            else:
                # Normal volatility
                returns.append(np.random.normal(0, base_volatility))
        
        returns = np.array(returns)
        
        # Generate prices
        prices = [initial_price]
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))  # Ensure positive prices
        
        return np.array(prices)
    
    def _generate_random_walk_prices(self, initial_price: float, num_periods: int,
                                   volatility: float) -> np.ndarray:
        """Generate random walk price series"""
        returns = np.random.normal(0, volatility * 0.01, num_periods)
        
        # Generate prices
        prices = [initial_price]
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))  # Ensure positive prices
        
        return np.array(prices)
    
    def _generate_ohlc_from_prices(self, prices: np.ndarray, config: MockDataGenerationConfig) -> Dict[str, np.ndarray]:
        """Generate OHLC data from price series"""
        num_periods = len(prices)
        opens = np.zeros(num_periods)
        highs = np.zeros(num_periods)
        lows = np.zeros(num_periods)
        closes = prices.copy()
        
        for i in range(num_periods):
            if i == 0:
                opens[i] = prices[i]
            else:
                # Open is close of previous period with small gap
                gap = np.random.normal(0, config.volatility * 0.005)
                opens[i] = closes[i-1] * (1 + gap)
            
            # High and low around open and close
            price_range = config.volatility * 0.02 * prices[i]
            high_low_range = np.random.uniform(0.3, 1.0) * price_range
            
            highs[i] = max(opens[i], closes[i]) + high_low_range
            lows[i] = min(opens[i], closes[i]) - high_low_range
            
            # Ensure OHLC relationships are valid
            highs[i] = max(highs[i], opens[i], closes[i])
            lows[i] = min(lows[i], opens[i], closes[i])
            lows[i] = max(lows[i], 0.01)  # Ensure positive prices
        
        return {
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes
        }
    
    def _generate_volume_data(self, num_periods: int, volume_pattern: str) -> np.ndarray:
        """Generate volume data based on pattern"""
        base_volume = 1000000  # Base volume
        
        if volume_pattern == 'normal':
            # Normal volume with some randomness
            volumes = np.random.normal(base_volume, base_volume * 0.3, num_periods)
        elif volume_pattern == 'increasing':
            # Increasing volume trend
            trend = np.linspace(0.5, 2.0, num_periods)
            volumes = base_volume * trend * np.random.uniform(0.8, 1.2, num_periods)
        elif volume_pattern == 'decreasing':
            # Decreasing volume trend
            trend = np.linspace(2.0, 0.5, num_periods)
            volumes = base_volume * trend * np.random.uniform(0.8, 1.2, num_periods)
        elif volume_pattern == 'spike':
            # Occasional volume spikes
            volumes = np.random.normal(base_volume, base_volume * 0.2, num_periods)
            # Add spikes randomly
            spike_indices = np.random.choice(num_periods, size=num_periods//10, replace=False)
            volumes[spike_indices] *= np.random.uniform(3, 10, len(spike_indices))
        else:
            # Default to normal
            volumes = np.random.normal(base_volume, base_volume * 0.3, num_periods)
        
        # Ensure positive volumes
        volumes = np.maximum(volumes, 1000)
        return volumes.astype(int)
    
    def _add_gaps_to_data(self, data: pd.DataFrame, gap_probability: float) -> pd.DataFrame:
        """Add price gaps to data"""
        gap_mask = np.random.random(len(data)) < gap_probability
        gap_indices = np.where(gap_mask)[0]
        
        for idx in gap_indices:
            if idx > 0:  # Don't gap the first row
                # Create gap by adjusting open price
                gap_magnitude = np.random.uniform(0.01, 0.05)  # 1-5% gap
                gap_direction = np.random.choice([-1, 1])
                
                new_open = data.iloc[idx-1]['close'] * (1 + gap_direction * gap_magnitude)
                data.iloc[idx, data.columns.get_loc('open')] = new_open
                
                # Adjust high/low if necessary
                if new_open > data.iloc[idx]['high']:
                    data.iloc[idx, data.columns.get_loc('high')] = new_open
                elif new_open < data.iloc[idx]['low']:
                    data.iloc[idx, data.columns.get_loc('low')] = new_open
        
        return data
    
    def _calculate_data_quality(self, price_bars: List[PriceBar], config: MockDataGenerationConfig) -> float:
        """Calculate data quality score"""
        if not price_bars:
            return 0.0
        
        quality_score = 100.0
        
        # Check for data completeness
        expected_points = int((config.end_date - config.start_date).total_seconds() / 
                            (self._get_timeframe_minutes(config.timeframe) * 60))
        actual_points = len(price_bars)
        
        if actual_points < expected_points * 0.9:
            quality_score -= 20  # Penalty for missing data
        
        # Check for price validity
        invalid_prices = 0
        for bar in price_bars:
            if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
                invalid_prices += 1
            if bar.high < bar.low or bar.high < bar.open or bar.high < bar.close:
                invalid_prices += 1
            if bar.low > bar.high or bar.low > bar.open or bar.low > bar.close:
                invalid_prices += 1
        
        if invalid_prices > 0:
            quality_score -= (invalid_prices / len(price_bars)) * 50
        
        # Check for reasonable price movements
        extreme_moves = 0
        for i, bar in enumerate(price_bars[1:], 1):
            prev_close = price_bars[i-1].close
            price_change = abs(bar.close - prev_close) / prev_close
            if price_change > 0.2:  # 20% move
                extreme_moves += 1
        
        if extreme_moves > len(price_bars) * 0.05:  # More than 5% extreme moves
            quality_score -= 15
        
        return max(0.0, quality_score)
    
    async def generate_multiple_regimes(self, config: MockDataGenerationConfig,
                                      regimes: List[str]) -> Dict[str, MockMarketData]:
        """Generate data for multiple market regimes"""
        results = {}
        
        for regime in regimes:
            regime_config = MockDataGenerationConfig(
                symbol=config.symbol,
                timeframe=config.timeframe,
                start_date=config.start_date,
                end_date=config.end_date,
                market_regime=regime,
                initial_price=config.initial_price,
                volatility=config.volatility,
                trend_strength=config.trend_strength,
                volume_pattern=config.volume_pattern,
                noise_level=config.noise_level,
                gaps_probability=config.gaps_probability
            )
            
            regime_data = await self.generate_mock_data(regime_config)
            results[regime] = regime_data
        
        return results











