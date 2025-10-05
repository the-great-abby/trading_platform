#!/usr/bin/env python3
"""
PriceBar model for Strategy Engine Testing Framework
Represents individual price bar data for market data
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class PriceBar(BaseModel):
    """
    Individual price bar in market data
    
    Represents OHLCV (Open, High, Low, Close, Volume) data for a single time period
    """
    
    timestamp: datetime = Field(..., description="Bar timestamp")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")
    symbol: str = Field(..., description="Trading symbol")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:00:00Z",
                "open": 150.25,
                "high": 151.80,
                "low": 149.90,
                "close": 151.50,
                "volume": 1250000,
                "symbol": "AAPL"
            }
        }
    
    @validator('high')
    def validate_high(cls, v, values):
        """Validate that high is the highest price"""
        if 'low' in values and v < values['low']:
            raise ValueError('High price must be >= low price')
        if 'open' in values and v < values['open']:
            raise ValueError('High price must be >= open price')
        if 'close' in values and v < values['close']:
            raise ValueError('High price must be >= close price')
        return v
    
    @validator('low')
    def validate_low(cls, v, values):
        """Validate that low is the lowest price"""
        if 'high' in values and v > values['high']:
            raise ValueError('Low price must be <= high price')
        if 'open' in values and v > values['open']:
            raise ValueError('Low price must be <= open price')
        if 'close' in values and v > values['close']:
            raise ValueError('Low price must be <= close price')
        return v
    
    @validator('volume')
    def validate_volume(cls, v):
        """Validate volume is non-negative"""
        if v < 0:
            raise ValueError('Volume must be non-negative')
        return v
    
    def get_price_range(self) -> float:
        """Get the price range (high - low)"""
        return self.high - self.low
    
    def get_body_size(self) -> float:
        """Get the body size (|close - open|)"""
        return abs(self.close - self.open)
    
    def get_upper_shadow(self) -> float:
        """Get the upper shadow (high - max(open, close))"""
        return self.high - max(self.open, self.close)
    
    def get_lower_shadow(self) -> float:
        """Get the lower shadow (min(open, close) - low)"""
        return min(self.open, self.close) - self.low
    
    def is_bullish(self) -> bool:
        """Check if the bar is bullish (close > open)"""
        return self.close > self.open
    
    def is_bearish(self) -> bool:
        """Check if the bar is bearish (close < open)"""
        return self.close < self.open
    
    def is_doji(self, tolerance: float = 0.001) -> bool:
        """Check if the bar is a doji (open ≈ close)"""
        return abs(self.close - self.open) <= tolerance
    
    def get_typical_price(self) -> float:
        """Get the typical price (high + low + close) / 3"""
        return (self.high + self.low + self.close) / 3.0
    
    def get_weighted_close(self) -> float:
        """Get the weighted close (high + low + 2*close) / 4"""
        return (self.high + self.low + 2 * self.close) / 4.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "symbol": self.symbol
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PriceBar':
        """Create PriceBar from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')),
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
            symbol=data["symbol"]
        )
