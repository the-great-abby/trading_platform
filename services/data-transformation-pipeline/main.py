#!/usr/bin/env python3
"""
Data Transformation Pipeline Service
Comprehensive data transformation for stocks, options, trades, and news articles
"""

import os
import logging
import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import aiohttp
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Transformation Pipeline",
    description="Comprehensive data transformation for stocks, options, trades, and news articles",
    version="1.0.0"
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/trading")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-service:80")
AI_ANALYSIS_URL = os.getenv("AI_ANALYSIS_URL", "http://ai-analysis-service:11085")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://trading_user:trading_pass@rabbitmq-service:5672/trading_vhost")

class DataType(str, Enum):
    STOCK = "stock"
    OPTION = "option"
    TRADE = "trade"
    NEWS = "news"

class TransformationType(str, Enum):
    CLEANING = "cleaning"
    NORMALIZATION = "normalization"
    ENRICHMENT = "enrichment"
    AGGREGATION = "aggregation"
    FEATURE_ENGINEERING = "feature_engineering"
    VALIDATION = "validation"

class DataQualityLevel(str, Enum):
    RAW = "raw"
    CLEANED = "cleaned"
    VALIDATED = "validated"
    ENRICHED = "enriched"
    ANALYZED = "analyzed"

@dataclass
class TransformationResult:
    """Result of a data transformation operation"""
    success: bool
    data: Dict[str, Any]
    quality_score: float
    transformations_applied: List[str]
    errors: List[str]
    metadata: Dict[str, Any]

class StockDataRequest(BaseModel):
    symbols: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    transformations: List[TransformationType] = Field(default_factory=list)
    include_technical_indicators: bool = True
    include_sentiment: bool = True

class OptionDataRequest(BaseModel):
    symbols: List[str]
    expiration_date: Optional[str] = None
    strike_price: Optional[float] = None
    option_type: Optional[str] = None  # "call" or "put"
    transformations: List[TransformationType] = Field(default_factory=list)

class TradeDataRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    symbols: Optional[List[str]] = None
    transformations: List[TransformationType] = Field(default_factory=list)
    include_performance_metrics: bool = True

class NewsDataRequest(BaseModel):
    symbols: List[str]
    keywords: Optional[List[str]] = None
    hours_back: int = 24
    transformations: List[TransformationType] = Field(default_factory=list)
    include_sentiment_analysis: bool = True

class DataTransformationPipeline:
    """Main data transformation pipeline"""
    
    def __init__(self):
        self.quality_threshold = 0.8
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def transform_stock_data(self, request: StockDataRequest) -> TransformationResult:
        """Transform stock data with comprehensive processing"""
        try:
            logger.info(f"Starting stock data transformation for {len(request.symbols)} symbols")
            
            results = []
            total_quality_score = 0
            
            for symbol in request.symbols:
                # Fetch raw stock data
                raw_data = await self._fetch_stock_data(symbol, request.start_date, request.end_date)
                
                if raw_data is None or raw_data.empty:
                    logger.warning(f"No data available for {symbol}")
                    continue
                
                # Apply transformations
                transformed_data = await self._apply_stock_transformations(
                    raw_data, symbol, request.transformations, 
                    request.include_technical_indicators, request.include_sentiment
                )
                
                # Calculate quality score
                quality_score = self._calculate_data_quality(transformed_data)
                total_quality_score += quality_score
                
                results.append({
                    "symbol": symbol,
                    "data": transformed_data.to_dict(orient="records"),
                    "quality_score": quality_score,
                    "data_points": len(transformed_data)
                })
            
            avg_quality_score = total_quality_score / len(results) if results else 0
            
            return TransformationResult(
                success=len(results) > 0,
                data={"stocks": results},
                quality_score=avg_quality_score,
                transformations_applied=[t.value for t in request.transformations],
                errors=[],
                metadata={
                    "symbols_processed": len(results),
                    "total_data_points": sum(r["data_points"] for r in results),
                    "transformation_types": [t.value for t in request.transformations]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in stock data transformation: {e}")
            return TransformationResult(
                success=False,
                data={},
                quality_score=0.0,
                transformations_applied=[],
                errors=[str(e)],
                metadata={}
            )
    
    async def transform_option_data(self, request: OptionDataRequest) -> TransformationResult:
        """Transform options data with Greeks and volatility analysis"""
        try:
            logger.info(f"Starting options data transformation for {len(request.symbols)} symbols")
            
            results = []
            total_quality_score = 0
            
            for symbol in request.symbols:
                # Fetch raw options data
                raw_data = await self._fetch_option_data(
                    symbol, request.expiration_date, request.strike_price, request.option_type
                )
                
                if raw_data is None or raw_data.empty:
                    logger.warning(f"No options data available for {symbol}")
                    continue
                
                # Apply options-specific transformations
                transformed_data = await self._apply_option_transformations(
                    raw_data, symbol, request.transformations
                )
                
                # Calculate quality score
                quality_score = self._calculate_data_quality(transformed_data)
                total_quality_score += quality_score
                
                results.append({
                    "symbol": symbol,
                    "data": transformed_data.to_dict(orient="records"),
                    "quality_score": quality_score,
                    "data_points": len(transformed_data)
                })
            
            avg_quality_score = total_quality_score / len(results) if results else 0
            
            return TransformationResult(
                success=len(results) > 0,
                data={"options": results},
                quality_score=avg_quality_score,
                transformations_applied=[t.value for t in request.transformations],
                errors=[],
                metadata={
                    "symbols_processed": len(results),
                    "total_data_points": sum(r["data_points"] for r in results),
                    "transformation_types": [t.value for t in request.transformations]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in options data transformation: {e}")
            return TransformationResult(
                success=False,
                data={},
                quality_score=0.0,
                transformations_applied=[],
                errors=[str(e)],
                metadata={}
            )
    
    async def transform_trade_data(self, request: TradeDataRequest) -> TransformationResult:
        """Transform trade data with performance analysis"""
        try:
            logger.info("Starting trade data transformation")
            
            # Fetch trade data
            raw_data = await self._fetch_trade_data(
                request.start_date, request.end_date, request.symbols
            )
            
            if raw_data is None or raw_data.empty:
                logger.warning("No trade data available")
                return TransformationResult(
                    success=False,
                    data={},
                    quality_score=0.0,
                    transformations_applied=[],
                    errors=["No trade data available"],
                    metadata={}
                )
            
            # Apply trade-specific transformations
            transformed_data = await self._apply_trade_transformations(
                raw_data, request.transformations, request.include_performance_metrics
            )
            
            # Calculate quality score
            quality_score = self._calculate_data_quality(transformed_data)
            
            return TransformationResult(
                success=True,
                data={"trades": transformed_data.to_dict(orient="records")},
                quality_score=quality_score,
                transformations_applied=[t.value for t in request.transformations],
                errors=[],
                metadata={
                    "trades_processed": len(transformed_data),
                    "transformation_types": [t.value for t in request.transformations]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in trade data transformation: {e}")
            return TransformationResult(
                success=False,
                data={},
                quality_score=0.0,
                transformations_applied=[],
                errors=[str(e)],
                metadata={}
            )
    
    async def transform_news_data(self, request: NewsDataRequest) -> TransformationResult:
        """Transform news data with sentiment analysis"""
        try:
            logger.info(f"Starting news data transformation for {len(request.symbols)} symbols")
            
            results = []
            total_quality_score = 0
            
            for symbol in request.symbols:
                # Fetch news data
                raw_data = await self._fetch_news_data(
                    symbol, request.keywords, request.hours_back
                )
                
                if raw_data is None or raw_data.empty:
                    logger.warning(f"No news data available for {symbol}")
                    continue
                
                # Apply news-specific transformations
                transformed_data = await self._apply_news_transformations(
                    raw_data, symbol, request.transformations, request.include_sentiment_analysis
                )
                
                # Calculate quality score
                quality_score = self._calculate_data_quality(transformed_data)
                total_quality_score += quality_score
                
                results.append({
                    "symbol": symbol,
                    "data": transformed_data.to_dict(orient="records"),
                    "quality_score": quality_score,
                    "data_points": len(transformed_data)
                })
            
            avg_quality_score = total_quality_score / len(results) if results else 0
            
            return TransformationResult(
                success=len(results) > 0,
                data={"news": results},
                quality_score=avg_quality_score,
                transformations_applied=[t.value for t in request.transformations],
                errors=[],
                metadata={
                    "symbols_processed": len(results),
                    "total_data_points": sum(r["data_points"] for r in results),
                    "transformation_types": [t.value for t in request.transformations]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in news data transformation: {e}")
            return TransformationResult(
                success=False,
                data={},
                quality_score=0.0,
                transformations_applied=[],
                errors=[str(e)],
                metadata={}
            )
    
    async def _fetch_stock_data(self, symbol: str, start_date: Optional[str], end_date: Optional[str]) -> Optional[pd.DataFrame]:
        """Fetch stock data from market data service"""
        try:
            url = f"{MARKET_DATA_URL}/market-data/historical"
            params = {
                "symbol": symbol,
                "start_date": start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": end_date or datetime.now().strftime("%Y-%m-%d"),
                "interval": "1d"
            }
            
            async with self.session.post(url, json=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return pd.DataFrame(data["data"])
                else:
                    logger.error(f"Failed to fetch stock data for {symbol}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    async def _fetch_option_data(self, symbol: str, expiration_date: Optional[str], 
                                strike_price: Optional[float], option_type: Optional[str]) -> Optional[pd.DataFrame]:
        """Fetch options data from market data service"""
        try:
            # This would integrate with your options data service
            # For now, return mock data
            mock_data = pd.DataFrame({
                "symbol": [symbol],
                "expiration": [expiration_date or "2024-12-20"],
                "strike": [strike_price or 100.0],
                "option_type": [option_type or "call"],
                "bid": [1.50],
                "ask": [1.55],
                "volume": [100],
                "open_interest": [500],
                "delta": [0.6],
                "gamma": [0.02],
                "theta": [-0.05],
                "vega": [0.15]
            })
            return mock_data
            
        except Exception as e:
            logger.error(f"Error fetching options data for {symbol}: {e}")
            return None
    
    async def _fetch_trade_data(self, start_date: Optional[str], end_date: Optional[str], 
                               symbols: Optional[List[str]]) -> Optional[pd.DataFrame]:
        """Fetch trade data from trading service"""
        try:
            # This would integrate with your trading service
            # For now, return mock data
            mock_data = pd.DataFrame({
                "symbol": ["AAPL", "GOOGL", "MSFT"],
                "side": ["buy", "sell", "buy"],
                "quantity": [100, 50, 75],
                "price": [150.0, 2800.0, 300.0],
                "timestamp": [datetime.now().isoformat()] * 3,
                "status": ["filled", "filled", "filled"]
            })
            return mock_data
            
        except Exception as e:
            logger.error(f"Error fetching trade data: {e}")
            return None
    
    async def _fetch_news_data(self, symbol: str, keywords: Optional[List[str]], hours_back: int) -> Optional[pd.DataFrame]:
        """Fetch news data from RSS feed service"""
        try:
            # This would integrate with your RSS feed service
            # For now, return mock data
            mock_data = pd.DataFrame({
                "symbol": [symbol],
                "headline": [f"News about {symbol}"],
                "summary": [f"Latest news and analysis for {symbol}"],
                "source": ["Reuters"],
                "timestamp": [datetime.now().isoformat()],
                "url": [f"https://example.com/news/{symbol}"]
            })
            return mock_data
            
        except Exception as e:
            logger.error(f"Error fetching news data for {symbol}: {e}")
            return None
    
    async def _apply_stock_transformations(self, data: pd.DataFrame, symbol: str, 
                                         transformations: List[TransformationType],
                                         include_technical: bool, include_sentiment: bool) -> pd.DataFrame:
        """Apply stock-specific transformations"""
        transformed_data = data.copy()
        
        for transformation in transformations:
            if transformation == TransformationType.CLEANING:
                transformed_data = self._clean_stock_data(transformed_data)
            elif transformation == TransformationType.NORMALIZATION:
                transformed_data = self._normalize_stock_data(transformed_data)
            elif transformation == TransformationType.ENRICHMENT:
                transformed_data = await self._enrich_stock_data(transformed_data, symbol)
            elif transformation == TransformationType.FEATURE_ENGINEERING:
                transformed_data = self._engineer_stock_features(transformed_data, include_technical)
        
        return transformed_data
    
    async def _apply_option_transformations(self, data: pd.DataFrame, symbol: str,
                                          transformations: List[TransformationType]) -> pd.DataFrame:
        """Apply options-specific transformations"""
        transformed_data = data.copy()
        
        for transformation in transformations:
            if transformation == TransformationType.CLEANING:
                transformed_data = self._clean_option_data(transformed_data)
            elif transformation == TransformationType.NORMALIZATION:
                transformed_data = self._normalize_option_data(transformed_data)
            elif transformation == TransformationType.ENRICHMENT:
                transformed_data = await self._enrich_option_data(transformed_data, symbol)
            elif transformation == TransformationType.FEATURE_ENGINEERING:
                transformed_data = self._engineer_option_features(transformed_data)
        
        return transformed_data
    
    async def _apply_trade_transformations(self, data: pd.DataFrame,
                                         transformations: List[TransformationType],
                                         include_performance: bool) -> pd.DataFrame:
        """Apply trade-specific transformations"""
        transformed_data = data.copy()
        
        for transformation in transformations:
            if transformation == TransformationType.CLEANING:
                transformed_data = self._clean_trade_data(transformed_data)
            elif transformation == TransformationType.NORMALIZATION:
                transformed_data = self._normalize_trade_data(transformed_data)
            elif transformation == TransformationType.ENRICHMENT:
                transformed_data = await self._enrich_trade_data(transformed_data)
            elif transformation == TransformationType.FEATURE_ENGINEERING:
                transformed_data = self._engineer_trade_features(transformed_data, include_performance)
        
        return transformed_data
    
    async def _apply_news_transformations(self, data: pd.DataFrame, symbol: str,
                                        transformations: List[TransformationType],
                                        include_sentiment: bool) -> pd.DataFrame:
        """Apply news-specific transformations"""
        transformed_data = data.copy()
        
        for transformation in transformations:
            if transformation == TransformationType.CLEANING:
                transformed_data = self._clean_news_data(transformed_data)
            elif transformation == TransformationType.NORMALIZATION:
                transformed_data = self._normalize_news_data(transformed_data)
            elif transformation == TransformationType.ENRICHMENT:
                transformed_data = await self._enrich_news_data(transformed_data, symbol, include_sentiment)
            elif transformation == TransformationType.FEATURE_ENGINEERING:
                transformed_data = self._engineer_news_features(transformed_data)
        
        return transformed_data
    
    def _clean_stock_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean stock data"""
        # Remove duplicates
        data = data.drop_duplicates()
        
        # Handle missing values
        data = data.fillna(method='ffill')
        
        # Remove outliers (simple approach)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in data.columns:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                data = data[~((data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR)))]
        
        return data
    
    def _normalize_stock_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize stock data"""
        # Add normalized columns
        if 'close' in data.columns:
            data['price_change'] = data['close'].pct_change()
            data['price_change_pct'] = data['price_change'] * 100
        
        if 'volume' in data.columns:
            data['volume_ma'] = data['volume'].rolling(window=20).mean()
            data['volume_ratio'] = data['volume'] / data['volume_ma']
        
        return data
    
    async def _enrich_stock_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Enrich stock data with additional information"""
        # Add symbol column if not present
        if 'symbol' not in data.columns:
            data['symbol'] = symbol
        
        # Add timestamp if not present
        if 'timestamp' not in data.columns and 'date' in data.columns:
            data['timestamp'] = pd.to_datetime(data['date'])
        
        return data
    
    def _engineer_stock_features(self, data: pd.DataFrame, include_technical: bool) -> pd.DataFrame:
        """Engineer stock features including technical indicators"""
        if not include_technical:
            return data
        
        # Simple moving averages
        if 'close' in data.columns:
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_50'] = data['close'].rolling(window=50).mean()
            data['sma_200'] = data['close'].rolling(window=200).mean()
        
        # RSI
        if 'close' in data.columns:
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        if 'close' in data.columns:
            data['bb_middle'] = data['close'].rolling(window=20).mean()
            bb_std = data['close'].rolling(window=20).std()
            data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
            data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
        
        return data
    
    def _clean_option_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean options data"""
        # Remove invalid options data
        data = data.dropna(subset=['bid', 'ask', 'strike'])
        
        # Remove options with zero volume
        if 'volume' in data.columns:
            data = data[data['volume'] > 0]
        
        return data
    
    def _normalize_option_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize options data"""
        # Calculate implied volatility (simplified)
        if all(col in data.columns for col in ['bid', 'ask', 'strike']):
            data['mid_price'] = (data['bid'] + data['ask']) / 2
            data['bid_ask_spread'] = data['ask'] - data['bid']
            data['spread_pct'] = data['bid_ask_spread'] / data['mid_price'] * 100
        
        return data
    
    async def _enrich_option_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Enrich options data"""
        # Add symbol column if not present
        if 'symbol' not in data.columns:
            data['symbol'] = symbol
        
        return data
    
    def _engineer_option_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer options features"""
        # Add Greeks if not present (mock values)
        if 'delta' not in data.columns:
            data['delta'] = 0.5
        if 'gamma' not in data.columns:
            data['gamma'] = 0.02
        if 'theta' not in data.columns:
            data['theta'] = -0.05
        if 'vega' not in data.columns:
            data['vega'] = 0.15
        
        return data
    
    def _clean_trade_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean trade data"""
        # Remove invalid trades
        data = data.dropna(subset=['symbol', 'quantity', 'price'])
        
        # Remove trades with zero quantity
        data = data[data['quantity'] > 0]
        
        return data
    
    def _normalize_trade_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize trade data"""
        # Calculate trade value
        if all(col in data.columns for col in ['quantity', 'price']):
            data['trade_value'] = data['quantity'] * data['price']
        
        return data
    
    async def _enrich_trade_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Enrich trade data"""
        # Add trade ID if not present
        if 'trade_id' not in data.columns:
            data['trade_id'] = range(len(data))
        
        return data
    
    def _engineer_trade_features(self, data: pd.DataFrame, include_performance: bool) -> pd.DataFrame:
        """Engineer trade features"""
        if not include_performance:
            return data
        
        # Calculate performance metrics
        if 'trade_value' in data.columns:
            data['cumulative_value'] = data['trade_value'].cumsum()
        
        return data
    
    def _clean_news_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean news data"""
        # Remove duplicates
        data = data.drop_duplicates(subset=['headline', 'timestamp'])
        
        # Remove empty headlines
        data = data.dropna(subset=['headline'])
        
        return data
    
    def _normalize_news_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize news data"""
        # Convert timestamp to datetime
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        return data
    
    async def _enrich_news_data(self, data: pd.DataFrame, symbol: str, include_sentiment: bool) -> pd.DataFrame:
        """Enrich news data with sentiment analysis"""
        # Add symbol column if not present
        if 'symbol' not in data.columns:
            data['symbol'] = symbol
        
        # Add sentiment analysis if requested
        if include_sentiment:
            data['sentiment_score'] = 0.0  # Mock sentiment score
            data['sentiment_label'] = 'neutral'
        
        return data
    
    def _engineer_news_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer news features"""
        # Add news features
        if 'headline' in data.columns:
            data['headline_length'] = data['headline'].str.len()
            data['word_count'] = data['headline'].str.split().str.len()
        
        return data
    
    def _calculate_data_quality(self, data: pd.DataFrame) -> float:
        """Calculate data quality score"""
        if data.empty:
            return 0.0
        
        # Calculate completeness
        completeness = 1 - (data.isnull().sum().sum() / (len(data) * len(data.columns)))
        
        # Calculate consistency (no duplicates)
        consistency = 1 - (len(data) - len(data.drop_duplicates())) / len(data)
        
        # Calculate validity (basic checks)
        validity = 1.0
        for col in data.columns:
            if col in ['open', 'high', 'low', 'close', 'price']:
                if (data[col] < 0).any():
                    validity *= 0.8
            elif col in ['volume', 'quantity']:
                if (data[col] < 0).any():
                    validity *= 0.8
        
        # Overall quality score
        quality_score = (completeness + consistency + validity) / 3
        return min(quality_score, 1.0)

# Global pipeline instance
pipeline = DataTransformationPipeline()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "data-transformation-pipeline",
        "version": "1.0.0"
    }

@app.post("/transform/stocks")
async def transform_stocks(request: StockDataRequest):
    """Transform stock data"""
    async with pipeline as p:
        result = await p.transform_stock_data(request)
        return result

@app.post("/transform/options")
async def transform_options(request: OptionDataRequest):
    """Transform options data"""
    async with pipeline as p:
        result = await p.transform_option_data(request)
        return result

@app.post("/transform/trades")
async def transform_trades(request: TradeDataRequest):
    """Transform trade data"""
    async with pipeline as p:
        result = await p.transform_trade_data(request)
        return result

@app.post("/transform/news")
async def transform_news(request: NewsDataRequest):
    """Transform news data"""
    async with pipeline as p:
        result = await p.transform_news_data(request)
        return result

@app.get("/status")
async def get_status():
    """Get transformation pipeline status"""
    return {
        "service": "data-transformation-pipeline",
        "version": "1.0.0",
        "status": "operational",
        "supported_data_types": [dt.value for dt in DataType],
        "supported_transformations": [t.value for dt in TransformationType],
        "quality_threshold": pipeline.quality_threshold
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11135) 