#!/usr/bin/env python3
"""
MockMarketData model for Strategy Engine Testing Framework
Represents generated mock market data for testing strategies
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta

from .enums import TimeFrame, MarketRegime, validate_timeframe, validate_market_regime
from .price_bar import PriceBar


class MockMarketData(BaseModel):
    """
    Generated mock market data for strategy testing
    
    Provides realistic market data with configurable patterns and regimes
    """
    
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Data timeframe")
    start_date: datetime = Field(..., description="Start date for data generation")
    end_date: datetime = Field(..., description="End date for data generation")
    market_regime: str = Field(..., description="Market regime type")
    price_data: List[PriceBar] = Field(..., description="Generated price bars")
    generation_metadata: Optional[Dict[str, Any]] = Field(None, description="Data generation parameters")
    data_quality_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Data quality assessment")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "timeframe": "1d",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z",
                "market_regime": "bull",
                "price_data": [],
                "generation_metadata": {
                    "volatility": 0.25,
                    "trend_strength": 0.7,
                    "volume_pattern": "normal"
                },
                "data_quality_score": 95.5
            }
        }
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe is valid"""
        if not validate_timeframe(v):
            raise ValueError(f'Invalid timeframe: {v}')
        return v
    
    @validator('market_regime')
    def validate_market_regime(cls, v):
        """Validate market regime is valid"""
        if not validate_market_regime(v):
            raise ValueError(f'Invalid market regime: {v}')
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate end date is after start date"""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('price_data')
    def validate_price_data(cls, v):
        """Validate price data is sorted by timestamp"""
        if len(v) > 1:
            for i in range(1, len(v)):
                if v[i].timestamp <= v[i-1].timestamp:
                    raise ValueError('Price data must be sorted by timestamp')
        return v
    
    def get_data_count(self) -> int:
        """Get number of price bars"""
        return len(self.price_data)
    
    def get_date_range(self) -> Dict[str, datetime]:
        """Get actual date range of data"""
        if not self.price_data:
            return {"start": self.start_date, "end": self.end_date}
        
        return {
            "start": self.price_data[0].timestamp,
            "end": self.price_data[-1].timestamp
        }
    
    def get_price_range(self) -> Dict[str, float]:
        """Get price range across all data"""
        if not self.price_data:
            return {"min": 0.0, "max": 0.0}
        
        all_prices = []
        for bar in self.price_data:
            all_prices.extend([bar.open, bar.high, bar.low, bar.close])
        
        return {
            "min": min(all_prices),
            "max": max(all_prices)
        }
    
    def get_volume_stats(self) -> Dict[str, float]:
        """Get volume statistics"""
        if not self.price_data:
            return {"total": 0.0, "average": 0.0, "max": 0.0, "min": 0.0}
        
        volumes = [bar.volume for bar in self.price_data]
        return {
            "total": sum(volumes),
            "average": sum(volumes) / len(volumes),
            "max": max(volumes),
            "min": min(volumes)
        }
    
    def get_volatility_estimate(self) -> float:
        """Estimate volatility from price data"""
        if len(self.price_data) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(self.price_data)):
            prev_close = self.price_data[i-1].close
            curr_close = self.price_data[i].close
            if prev_close > 0:
                returns.append((curr_close - prev_close) / prev_close)
        
        if not returns:
            return 0.0
        
        # Calculate standard deviation of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return (variance ** 0.5) * (252 ** 0.5)  # Annualized volatility
    
    def get_trend_direction(self) -> str:
        """Determine trend direction from price data"""
        if len(self.price_data) < 2:
            return "unknown"
        
        first_close = self.price_data[0].close
        last_close = self.price_data[-1].close
        
        if last_close > first_close * 1.05:  # 5% threshold
            return "bullish"
        elif last_close < first_close * 0.95:  # 5% threshold
            return "bearish"
        else:
            return "sideways"
    
    def filter_by_date_range(self, start_date: datetime, end_date: datetime) -> 'MockMarketData':
        """Filter data by date range"""
        filtered_data = [
            bar for bar in self.price_data
            if start_date <= bar.timestamp <= end_date
        ]
        
        return MockMarketData(
            symbol=self.symbol,
            timeframe=self.timeframe,
            start_date=start_date,
            end_date=end_date,
            market_regime=self.market_regime,
            price_data=filtered_data,
            generation_metadata=self.generation_metadata,
            data_quality_score=self.data_quality_score
        )
    
    def get_subset(self, count: int, from_end: bool = True) -> 'MockMarketData':
        """Get subset of data"""
        if count >= len(self.price_data):
            return self
        
        if from_end:
            subset_data = self.price_data[-count:]
            start_date = subset_data[0].timestamp
            end_date = subset_data[-1].timestamp
        else:
            subset_data = self.price_data[:count]
            start_date = subset_data[0].timestamp
            end_date = subset_data[-1].timestamp
        
        return MockMarketData(
            symbol=self.symbol,
            timeframe=self.timeframe,
            start_date=start_date,
            end_date=end_date,
            market_regime=self.market_regime,
            price_data=subset_data,
            generation_metadata=self.generation_metadata,
            data_quality_score=self.data_quality_score
        )
    
    def to_dataframe_dict(self) -> Dict[str, List]:
        """Convert to dictionary format suitable for pandas DataFrame"""
        if not self.price_data:
            return {
                "timestamp": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": [],
                "symbol": []
            }
        
        return {
            "timestamp": [bar.timestamp for bar in self.price_data],
            "open": [bar.open for bar in self.price_data],
            "high": [bar.high for bar in self.price_data],
            "low": [bar.low for bar in self.price_data],
            "close": [bar.close for bar in self.price_data],
            "volume": [bar.volume for bar in self.price_data],
            "symbol": [bar.symbol for bar in self.price_data]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "market_regime": self.market_regime,
            "price_data": [bar.to_dict() for bar in self.price_data],
            "generation_metadata": self.generation_metadata,
            "data_quality_score": self.data_quality_score
        }


class MockDataGenerationConfig(BaseModel):
    """Configuration for generating mock market data"""
    
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Data timeframe")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    market_regime: str = Field(..., description="Market regime")
    initial_price: float = Field(100.0, gt=0, description="Initial price")
    volatility: float = Field(0.2, ge=0.0, le=1.0, description="Price volatility")
    trend_strength: float = Field(0.0, ge=-1.0, le=1.0, description="Trend strength (-1 to 1)")
    volume_pattern: str = Field("normal", description="Volume pattern")
    noise_level: float = Field(0.1, ge=0.0, le=1.0, description="Market noise level")
    gaps_probability: float = Field(0.05, ge=0.0, le=1.0, description="Probability of gaps")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        """Validate timeframe is valid"""
        if not validate_timeframe(v):
            raise ValueError(f'Invalid timeframe: {v}')
        return v
    
    @validator('market_regime')
    def validate_market_regime(cls, v):
        """Validate market regime is valid"""
        if not validate_market_regime(v):
            raise ValueError(f'Invalid market regime: {v}')
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate end date is after start date"""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "market_regime": self.market_regime,
            "initial_price": self.initial_price,
            "volatility": self.volatility,
            "trend_strength": self.trend_strength,
            "volume_pattern": self.volume_pattern,
            "noise_level": self.noise_level,
            "gaps_probability": self.gaps_probability
        }
