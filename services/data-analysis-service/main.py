#!/usr/bin/env python3
"""
Data Analysis Service
Comprehensive analysis for stocks, options, trades, and news articles
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
    title="Data Analysis Service",
    description="Comprehensive analysis for stocks, options, trades, and news articles",
    version="1.0.0"
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/trading")
TRANSFORMATION_PIPELINE_URL = os.getenv("TRANSFORMATION_PIPELINE_URL", "http://data-transformation-pipeline:11135")
AI_ANALYSIS_URL = os.getenv("AI_ANALYSIS_URL", "http://ai-analysis-service:11085")

class AnalysisType(str, Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    RISK = "risk"
    PERFORMANCE = "performance"
    CORRELATION = "correlation"
    PATTERN = "pattern"

class AnalysisDepth(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class AnalysisResult:
    """Result of a data analysis operation"""
    success: bool
    analysis_type: str
    data: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    confidence_score: float
    metadata: Dict[str, Any]

class StockAnalysisRequest(BaseModel):
    symbols: List[str]
    analysis_types: List[AnalysisType] = Field(default_factory=list)
    depth: AnalysisDepth = AnalysisDepth.INTERMEDIATE
    include_technical_indicators: bool = True
    include_sentiment: bool = True
    include_risk_assessment: bool = True

class OptionAnalysisRequest(BaseModel):
    symbols: List[str]
    analysis_types: List[AnalysisType] = Field(default_factory=list)
    depth: AnalysisDepth = AnalysisDepth.INTERMEDIATE
    include_greeks: bool = True
    include_volatility_analysis: bool = True

class TradeAnalysisRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    symbols: Optional[List[str]] = None
    analysis_types: List[AnalysisType] = Field(default_factory=list)
    depth: AnalysisDepth = AnalysisDepth.INTERMEDIATE
    include_performance_metrics: bool = True

class NewsAnalysisRequest(BaseModel):
    symbols: List[str]
    analysis_types: List[AnalysisType] = Field(default_factory=list)
    depth: AnalysisDepth = AnalysisDepth.INTERMEDIATE
    hours_back: int = 24
    include_sentiment_analysis: bool = True
    include_impact_assessment: bool = True

class DataAnalysisService:
    """Main data analysis service"""
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_stocks(self, request: StockAnalysisRequest) -> AnalysisResult:
        """Analyze stock data comprehensively"""
        try:
            logger.info(f"Starting stock analysis for {len(request.symbols)} symbols")
            
            # Get transformed stock data
            stock_data = await self._get_transformed_stock_data(request.symbols)
            
            if not stock_data:
                raise HTTPException(status_code=404, detail="No stock data available")
            
            # Perform analysis based on requested types
            analysis_results = {}
            insights = []
            recommendations = []
            risk_factors = []
            
            for analysis_type in request.analysis_types:
                if analysis_type == AnalysisType.TECHNICAL:
                    tech_analysis = await self._perform_technical_analysis(stock_data, request.depth)
                    analysis_results['technical'] = tech_analysis
                    insights.extend(tech_analysis.get('insights', []))
                    recommendations.extend(tech_analysis.get('recommendations', []))
                    risk_factors.extend(tech_analysis.get('risk_factors', []))
                
                elif analysis_type == AnalysisType.FUNDAMENTAL:
                    fund_analysis = await self._perform_fundamental_analysis(stock_data, request.depth)
                    analysis_results['fundamental'] = fund_analysis
                    insights.extend(fund_analysis.get('insights', []))
                    recommendations.extend(fund_analysis.get('recommendations', []))
                    risk_factors.extend(fund_analysis.get('risk_factors', []))
                
                elif analysis_type == AnalysisType.SENTIMENT:
                    sentiment_analysis = await self._perform_sentiment_analysis(stock_data, request.depth)
                    analysis_results['sentiment'] = sentiment_analysis
                    insights.extend(sentiment_analysis.get('insights', []))
                    recommendations.extend(sentiment_analysis.get('recommendations', []))
                    risk_factors.extend(sentiment_analysis.get('risk_factors', []))
                
                elif analysis_type == AnalysisType.RISK:
                    risk_analysis = await self._perform_risk_analysis(stock_data, request.depth)
                    analysis_results['risk'] = risk_analysis
                    insights.extend(risk_analysis.get('insights', []))
                    recommendations.extend(risk_analysis.get('recommendations', []))
                    risk_factors.extend(risk_analysis.get('risk_factors', []))
            
            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(analysis_results)
            
            return AnalysisResult(
                success=True,
                analysis_type="stock_analysis",
                data=analysis_results,
                insights=insights,
                recommendations=recommendations,
                risk_factors=risk_factors,
                confidence_score=confidence_score,
                metadata={
                    "symbols_analyzed": len(request.symbols),
                    "analysis_types": [at.value for at in request.analysis_types],
                    "depth": request.depth.value
                }
            )
            
        except Exception as e:
            logger.error(f"Error in stock analysis: {e}")
            return AnalysisResult(
                success=False,
                analysis_type="stock_analysis",
                data={},
                insights=[],
                recommendations=[],
                risk_factors=[str(e)],
                confidence_score=0.0,
                metadata={}
            )
    
    async def analyze_options(self, request: OptionAnalysisRequest) -> AnalysisResult:
        """Analyze options data comprehensively"""
        try:
            logger.info(f"Starting options analysis for {len(request.symbols)} symbols")
            
            # Get transformed options data
            options_data = await self._get_transformed_options_data(request.symbols)
            
            if not options_data:
                raise HTTPException(status_code=404, detail="No options data available")
            
            # Perform analysis based on requested types
            analysis_results = {}
            insights = []
            recommendations = []
            risk_factors = []
            
            for analysis_type in request.analysis_types:
                if analysis_type == AnalysisType.TECHNICAL:
                    tech_analysis = await self._perform_options_technical_analysis(options_data, request.depth)
                    analysis_results['technical'] = tech_analysis
                    insights.extend(tech_analysis.get('insights', []))
                    recommendations.extend(tech_analysis.get('recommendations', []))
                    risk_factors.extend(tech_analysis.get('risk_factors', []))
                
                elif analysis_type == AnalysisType.RISK:
                    risk_analysis = await self._perform_options_risk_analysis(options_data, request.depth)
                    analysis_results['risk'] = risk_analysis
                    insights.extend(risk_analysis.get('insights', []))
                    recommendations.extend(risk_analysis.get('recommendations', []))
                    risk_factors.extend(risk_analysis.get('risk_factors', []))
            
            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(analysis_results)
            
            return AnalysisResult(
                success=True,
                analysis_type="options_analysis",
                data=analysis_results,
                insights=insights,
                recommendations=recommendations,
                risk_factors=risk_factors,
                confidence_score=confidence_score,
                metadata={
                    "symbols_analyzed": len(request.symbols),
                    "analysis_types": [at.value for at in request.analysis_types],
                    "depth": request.depth.value
                }
            )
            
        except Exception as e:
            logger.error(f"Error in options analysis: {e}")
            return AnalysisResult(
                success=False,
                analysis_type="options_analysis",
                data={},
                insights=[],
                recommendations=[],
                risk_factors=[str(e)],
                confidence_score=0.0,
                metadata={}
            )
    
    async def analyze_trades(self, request: TradeAnalysisRequest) -> AnalysisResult:
        """Analyze trade data comprehensively"""
        try:
            logger.info("Starting trade analysis")
            
            # Get transformed trade data
            trade_data = await self._get_transformed_trade_data(
                request.start_date, request.end_date, request.symbols
            )
            
            if not trade_data:
                raise HTTPException(status_code=404, detail="No trade data available")
            
            # Perform analysis based on requested types
            analysis_results = {}
            insights = []
            recommendations = []
            risk_factors = []
            
            for analysis_type in request.analysis_types:
                if analysis_type == AnalysisType.PERFORMANCE:
                    perf_analysis = await self._perform_trade_performance_analysis(trade_data, request.depth)
                    analysis_results['performance'] = perf_analysis
                    insights.extend(perf_analysis.get('insights', []))
                    recommendations.extend(perf_analysis.get('recommendations', []))
                    risk_factors.extend(perf_analysis.get('risk_factors', []))
                
                elif analysis_type == AnalysisType.RISK:
                    risk_analysis = await self._perform_trade_risk_analysis(trade_data, request.depth)
                    analysis_results['risk'] = risk_analysis
                    insights.extend(risk_analysis.get('insights', []))
                    recommendations.extend(risk_analysis.get('recommendations', []))
                    risk_factors.extend(risk_analysis.get('risk_factors', []))
            
            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(analysis_results)
            
            return AnalysisResult(
                success=True,
                analysis_type="trade_analysis",
                data=analysis_results,
                insights=insights,
                recommendations=recommendations,
                risk_factors=risk_factors,
                confidence_score=confidence_score,
                metadata={
                    "trades_analyzed": len(trade_data),
                    "analysis_types": [at.value for at in request.analysis_types],
                    "depth": request.depth.value
                }
            )
            
        except Exception as e:
            logger.error(f"Error in trade analysis: {e}")
            return AnalysisResult(
                success=False,
                analysis_type="trade_analysis",
                data={},
                insights=[],
                recommendations=[],
                risk_factors=[str(e)],
                confidence_score=0.0,
                metadata={}
            )
    
    async def analyze_news(self, request: NewsAnalysisRequest) -> AnalysisResult:
        """Analyze news data comprehensively"""
        try:
            logger.info(f"Starting news analysis for {len(request.symbols)} symbols")
            
            # Get transformed news data
            news_data = await self._get_transformed_news_data(request.symbols, request.hours_back)
            
            if not news_data:
                raise HTTPException(status_code=404, detail="No news data available")
            
            # Perform analysis based on requested types
            analysis_results = {}
            insights = []
            recommendations = []
            risk_factors = []
            
            for analysis_type in request.analysis_types:
                if analysis_type == AnalysisType.SENTIMENT:
                    sentiment_analysis = await self._perform_news_sentiment_analysis(news_data, request.depth)
                    analysis_results['sentiment'] = sentiment_analysis
                    insights.extend(sentiment_analysis.get('insights', []))
                    recommendations.extend(sentiment_analysis.get('recommendations', []))
                    risk_factors.extend(sentiment_analysis.get('risk_factors', []))
                
                elif analysis_type == AnalysisType.RISK:
                    risk_analysis = await self._perform_news_risk_analysis(news_data, request.depth)
                    analysis_results['risk'] = risk_analysis
                    insights.extend(risk_analysis.get('insights', []))
                    recommendations.extend(risk_analysis.get('recommendations', []))
                    risk_factors.extend(risk_analysis.get('risk_factors', []))
            
            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(analysis_results)
            
            return AnalysisResult(
                success=True,
                analysis_type="news_analysis",
                data=analysis_results,
                insights=insights,
                recommendations=recommendations,
                risk_factors=risk_factors,
                confidence_score=confidence_score,
                metadata={
                    "symbols_analyzed": len(request.symbols),
                    "analysis_types": [at.value for at in request.analysis_types],
                    "depth": request.depth.value
                }
            )
            
        except Exception as e:
            logger.error(f"Error in news analysis: {e}")
            return AnalysisResult(
                success=False,
                analysis_type="news_analysis",
                data={},
                insights=[],
                recommendations=[],
                risk_factors=[str(e)],
                confidence_score=0.0,
                metadata={}
            )
    
    async def _get_transformed_stock_data(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """Get transformed stock data from pipeline"""
        try:
            url = f"{TRANSFORMATION_PIPELINE_URL}/transform/stocks"
            payload = {
                "symbols": symbols,
                "transformations": ["cleaning", "normalization", "enrichment", "feature_engineering"],
                "include_technical_indicators": True,
                "include_sentiment": True
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get transformed stock data: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting transformed stock data: {e}")
            return None
    
    async def _get_transformed_options_data(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """Get transformed options data from pipeline"""
        try:
            url = f"{TRANSFORMATION_PIPELINE_URL}/transform/options"
            payload = {
                "symbols": symbols,
                "transformations": ["cleaning", "normalization", "enrichment", "feature_engineering"]
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get transformed options data: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting transformed options data: {e}")
            return None
    
    async def _get_transformed_trade_data(self, start_date: Optional[str], end_date: Optional[str], 
                                         symbols: Optional[List[str]]) -> Optional[Dict[str, Any]]:
        """Get transformed trade data from pipeline"""
        try:
            url = f"{TRANSFORMATION_PIPELINE_URL}/transform/trades"
            payload = {
                "start_date": start_date,
                "end_date": end_date,
                "symbols": symbols,
                "transformations": ["cleaning", "normalization", "enrichment", "feature_engineering"],
                "include_performance_metrics": True
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get transformed trade data: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting transformed trade data: {e}")
            return None
    
    async def _get_transformed_news_data(self, symbols: List[str], hours_back: int) -> Optional[Dict[str, Any]]:
        """Get transformed news data from pipeline"""
        try:
            url = f"{TRANSFORMATION_PIPELINE_URL}/transform/news"
            payload = {
                "symbols": symbols,
                "hours_back": hours_back,
                "transformations": ["cleaning", "normalization", "enrichment", "feature_engineering"],
                "include_sentiment_analysis": True
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get transformed news data: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting transformed news data: {e}")
            return None
    
    async def _perform_technical_analysis(self, stock_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform technical analysis on stock data"""
        try:
            insights = []
            recommendations = []
            risk_factors = []
            
            # Basic technical analysis
            for stock in stock_data.get("stocks", []):
                symbol = stock["symbol"]
                data = pd.DataFrame(stock["data"])
                
                if data.empty:
                    continue
                
                # RSI analysis
                if 'rsi' in data.columns:
                    latest_rsi = data['rsi'].iloc[-1]
                    if latest_rsi > 70:
                        insights.append(f"{symbol}: RSI indicates overbought conditions ({latest_rsi:.1f})")
                        recommendations.append(f"Consider taking profits on {symbol}")
                        risk_factors.append(f"Overbought RSI for {symbol}")
                    elif latest_rsi < 30:
                        insights.append(f"{symbol}: RSI indicates oversold conditions ({latest_rsi:.1f})")
                        recommendations.append(f"Consider buying {symbol} on weakness")
                
                # Moving average analysis
                if all(col in data.columns for col in ['close', 'sma_20', 'sma_50']):
                    latest_close = data['close'].iloc[-1]
                    sma_20 = data['sma_20'].iloc[-1]
                    sma_50 = data['sma_50'].iloc[-1]
                    
                    if latest_close > sma_20 > sma_50:
                        insights.append(f"{symbol}: Strong uptrend with price above moving averages")
                        recommendations.append(f"Hold {symbol} in uptrend")
                    elif latest_close < sma_20 < sma_50:
                        insights.append(f"{symbol}: Strong downtrend with price below moving averages")
                        recommendations.append(f"Consider shorting {symbol} or wait for reversal")
                        risk_factors.append(f"Downtrend for {symbol}")
                
                # Volume analysis
                if 'volume_ratio' in data.columns:
                    latest_volume_ratio = data['volume_ratio'].iloc[-1]
                    if latest_volume_ratio > 1.5:
                        insights.append(f"{symbol}: High volume activity ({latest_volume_ratio:.2f}x average)")
                    elif latest_volume_ratio < 0.5:
                        insights.append(f"{symbol}: Low volume activity ({latest_volume_ratio:.2f}x average)")
                        risk_factors.append(f"Low volume for {symbol}")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "risk_factors": risk_factors,
                "analysis_depth": depth.value
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return {"insights": [], "recommendations": [], "risk_factors": [str(e)]}
    
    async def _perform_fundamental_analysis(self, stock_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform fundamental analysis on stock data"""
        # Mock fundamental analysis
        return {
            "insights": ["Fundamental analysis requires additional data sources"],
            "recommendations": ["Consider integrating fundamental data providers"],
            "risk_factors": ["Limited fundamental data available"],
            "analysis_depth": depth.value
        }
    
    async def _perform_sentiment_analysis(self, stock_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform sentiment analysis on stock data"""
        # Mock sentiment analysis
        return {
            "insights": ["Sentiment analysis requires news and social media data"],
            "recommendations": ["Integrate news sentiment analysis"],
            "risk_factors": ["Limited sentiment data available"],
            "analysis_depth": depth.value
        }
    
    async def _perform_risk_analysis(self, stock_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform risk analysis on stock data"""
        try:
            insights = []
            recommendations = []
            risk_factors = []
            
            for stock in stock_data.get("stocks", []):
                symbol = stock["symbol"]
                data = pd.DataFrame(stock["data"])
                
                if data.empty:
                    continue
                
                # Volatility analysis
                if 'close' in data.columns:
                    returns = data['close'].pct_change().dropna()
                    volatility = returns.std() * np.sqrt(252)  # Annualized
                    
                    if volatility > 0.4:
                        insights.append(f"{symbol}: High volatility ({volatility:.2%} annualized)")
                        risk_factors.append(f"High volatility for {symbol}")
                        recommendations.append(f"Use smaller position sizes for {symbol}")
                    elif volatility < 0.15:
                        insights.append(f"{symbol}: Low volatility ({volatility:.2%} annualized)")
                        recommendations.append(f"Consider options strategies for {symbol}")
                
                # Price risk analysis
                if 'close' in data.columns:
                    latest_price = data['close'].iloc[-1]
                    price_range = data['close'].max() - data['close'].min()
                    price_risk = price_range / data['close'].mean()
                    
                    if price_risk > 0.5:
                        insights.append(f"{symbol}: High price risk ({price_risk:.2%} range)")
                        risk_factors.append(f"High price risk for {symbol}")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "risk_factors": risk_factors,
                "analysis_depth": depth.value
            }
            
        except Exception as e:
            logger.error(f"Error in risk analysis: {e}")
            return {"insights": [], "recommendations": [], "risk_factors": [str(e)]}
    
    async def _perform_options_technical_analysis(self, options_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform technical analysis on options data"""
        # Mock options technical analysis
        return {
            "insights": ["Options technical analysis requires specialized indicators"],
            "recommendations": ["Implement options-specific technical indicators"],
            "risk_factors": ["Options have unique risk characteristics"],
            "analysis_depth": depth.value
        }
    
    async def _perform_options_risk_analysis(self, options_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform risk analysis on options data"""
        try:
            insights = []
            recommendations = []
            risk_factors = []
            
            for option in options_data.get("options", []):
                symbol = option["symbol"]
                data = pd.DataFrame(option["data"])
                
                if data.empty:
                    continue
                
                # Greeks analysis
                if 'delta' in data.columns:
                    delta = data['delta'].iloc[-1]
                    if abs(delta) > 0.8:
                        insights.append(f"{symbol}: High delta ({delta:.3f}) - option behaves like stock")
                    elif abs(delta) < 0.2:
                        insights.append(f"{symbol}: Low delta ({delta:.3f}) - option is out of the money")
                        risk_factors.append(f"Low delta for {symbol}")
                
                if 'gamma' in data.columns:
                    gamma = data['gamma'].iloc[-1]
                    if gamma > 0.1:
                        insights.append(f"{symbol}: High gamma ({gamma:.3f}) - rapid delta changes")
                        risk_factors.append(f"High gamma for {symbol}")
                
                if 'theta' in data.columns:
                    theta = data['theta'].iloc[-1]
                    if abs(theta) > 0.1:
                        insights.append(f"{symbol}: High theta ({theta:.3f}) - rapid time decay")
                        risk_factors.append(f"High theta for {symbol}")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "risk_factors": risk_factors,
                "analysis_depth": depth.value
            }
            
        except Exception as e:
            logger.error(f"Error in options risk analysis: {e}")
            return {"insights": [], "recommendations": [], "risk_factors": [str(e)]}
    
    async def _perform_trade_performance_analysis(self, trade_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform performance analysis on trade data"""
        try:
            insights = []
            recommendations = []
            risk_factors = []
            
            trades = pd.DataFrame(trade_data.get("trades", []))
            
            if trades.empty:
                return {"insights": [], "recommendations": [], "risk_factors": ["No trade data available"]}
            
            # Win rate analysis
            if 'side' in trades.columns and 'trade_value' in trades.columns:
                buy_trades = trades[trades['side'] == 'buy']
                sell_trades = trades[trades['side'] == 'sell']
                
                total_trades = len(trades)
                if total_trades > 0:
                    insights.append(f"Total trades: {total_trades}")
                    insights.append(f"Buy trades: {len(buy_trades)}")
                    insights.append(f"Sell trades: {len(sell_trades)}")
            
            # Volume analysis
            if 'trade_value' in trades.columns:
                total_volume = trades['trade_value'].sum()
                avg_trade_size = trades['trade_value'].mean()
                insights.append(f"Total volume: ${total_volume:,.2f}")
                insights.append(f"Average trade size: ${avg_trade_size:,.2f}")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "risk_factors": risk_factors,
                "analysis_depth": depth.value
            }
            
        except Exception as e:
            logger.error(f"Error in trade performance analysis: {e}")
            return {"insights": [], "recommendations": [], "risk_factors": [str(e)]}
    
    async def _perform_trade_risk_analysis(self, trade_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform risk analysis on trade data"""
        # Mock trade risk analysis
        return {
            "insights": ["Trade risk analysis requires position sizing and portfolio data"],
            "recommendations": ["Implement position sizing rules"],
            "risk_factors": ["Limited trade risk data available"],
            "analysis_depth": depth.value
        }
    
    async def _perform_news_sentiment_analysis(self, news_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform sentiment analysis on news data"""
        try:
            insights = []
            recommendations = []
            risk_factors = []
            
            for news in news_data.get("news", []):
                symbol = news["symbol"]
                data = pd.DataFrame(news["data"])
                
                if data.empty:
                    continue
                
                # Sentiment analysis
                if 'sentiment_score' in data.columns:
                    avg_sentiment = data['sentiment_score'].mean()
                    if avg_sentiment > 0.5:
                        insights.append(f"{symbol}: Positive news sentiment ({avg_sentiment:.3f})")
                        recommendations.append(f"Monitor {symbol} for positive news impact")
                    elif avg_sentiment < -0.5:
                        insights.append(f"{symbol}: Negative news sentiment ({avg_sentiment:.3f})")
                        risk_factors.append(f"Negative sentiment for {symbol}")
                        recommendations.append(f"Exercise caution with {symbol}")
                    else:
                        insights.append(f"{symbol}: Neutral news sentiment ({avg_sentiment:.3f})")
                
                # News volume analysis
                if 'headline' in data.columns:
                    news_count = len(data)
                    insights.append(f"{symbol}: {news_count} news articles analyzed")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "risk_factors": risk_factors,
                "analysis_depth": depth.value
            }
            
        except Exception as e:
            logger.error(f"Error in news sentiment analysis: {e}")
            return {"insights": [], "recommendations": [], "risk_factors": [str(e)]}
    
    async def _perform_news_risk_analysis(self, news_data: Dict[str, Any], depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform risk analysis on news data"""
        # Mock news risk analysis
        return {
            "insights": ["News risk analysis requires impact assessment models"],
            "recommendations": ["Implement news impact scoring"],
            "risk_factors": ["Limited news risk data available"],
            "analysis_depth": depth.value
        }
    
    def _calculate_confidence_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall confidence score for analysis"""
        if not analysis_results:
            return 0.0
        
        # Simple confidence calculation based on analysis completeness
        total_analyses = len(analysis_results)
        completed_analyses = sum(1 for result in analysis_results.values() 
                               if result.get('insights') or result.get('recommendations'))
        
        if total_analyses == 0:
            return 0.0
        
        base_confidence = completed_analyses / total_analyses
        
        # Adjust based on data quality and analysis depth
        confidence_score = min(base_confidence * 1.2, 1.0)
        
        return confidence_score

# Global analysis service instance
analysis_service = DataAnalysisService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "data-analysis-service",
        "version": "1.0.0"
    }

@app.post("/analyze/stocks")
async def analyze_stocks(request: StockAnalysisRequest):
    """Analyze stock data"""
    async with analysis_service as service:
        result = await service.analyze_stocks(request)
        return result

@app.post("/analyze/options")
async def analyze_options(request: OptionAnalysisRequest):
    """Analyze options data"""
    async with analysis_service as service:
        result = await service.analyze_options(request)
        return result

@app.post("/analyze/trades")
async def analyze_trades(request: TradeAnalysisRequest):
    """Analyze trade data"""
    async with analysis_service as service:
        result = await service.analyze_trades(request)
        return result

@app.post("/analyze/news")
async def analyze_news(request: NewsAnalysisRequest):
    """Analyze news data"""
    async with analysis_service as service:
        result = await service.analyze_news(request)
        return result

@app.get("/status")
async def get_status():
    """Get analysis service status"""
    return {
        "service": "data-analysis-service",
        "version": "1.0.0",
        "status": "operational",
        "supported_analysis_types": [at.value for at in AnalysisType],
        "supported_depths": [ad.value for ad in AnalysisDepth]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11136) 