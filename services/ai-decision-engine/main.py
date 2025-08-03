#!/usr/bin/env python3
"""
AI Decision Engine - Real-time investment recommendations with timing analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import numpy as np
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Decision Engine", version="1.0.0")

# Configuration
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://llm-proxy:12001")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-service:8002")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot")

@dataclass
class MarketContext:
    """Market context for decision making"""
    volatility_regime: str  # "low", "medium", "high"
    market_trend: str  # "bullish", "bearish", "sideways"
    sector_performance: Dict[str, float]
    economic_calendar: List[Dict[str, Any]]
    correlation_matrix: pd.DataFrame
    market_breadth: Dict[str, float]

@dataclass
class InvestmentRecommendation:
    """Complete investment recommendation"""
    symbol: str
    action: str  # "BUY_NOW", "BUY_LATER", "SELL_NOW", "SELL_LATER", "HOLD"
    confidence: float  # 0-100
    reasoning: str
    target_price: Optional[float]
    stop_loss: Optional[float]
    position_size: str  # "SMALL", "MEDIUM", "LARGE"
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    timing: Dict[str, Any]  # When to execute
    market_context: MarketContext
    technical_signals: Dict[str, Any]
    sentiment_score: Optional[float]
    ai_analysis: Dict[str, Any]
    created_at: datetime

class DecisionEngine:
    """AI-powered decision engine for investment recommendations"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.market_data_service = MarketDataService()
        self.news_service = NewsService()
        self.technical_service = TechnicalAnalysisService()
        
    async def get_investment_recommendation(self, symbol: str, 
                                          include_timing: bool = True,
                                          risk_profile: str = "moderate") -> InvestmentRecommendation:
        """Get comprehensive investment recommendation with timing analysis"""
        
        # Gather all data
        market_data = await self.market_data_service.get_current_data(symbol)
        news_data = await self.news_service.get_recent_news(symbol)
        technical_data = await self.technical_service.get_indicators(symbol)
        market_context = await self._get_market_context()
        
        # Generate AI analysis
        ai_analysis = await self._analyze_with_ai(symbol, market_data, news_data, technical_data, market_context)
        
        # Determine action and timing
        action, confidence, reasoning = await self._determine_action(
            symbol, market_data, technical_data, ai_analysis, market_context, risk_profile
        )
        
        # Calculate position sizing
        position_size = self._calculate_position_size(confidence, risk_profile, market_context)
        
        # Generate timing analysis
        timing = await self._analyze_timing(symbol, action, market_data, market_context) if include_timing else {}
        
        # Calculate target and stop loss
        target_price, stop_loss = self._calculate_price_targets(symbol, action, market_data, technical_data)
        
        return InvestmentRecommendation(
            symbol=symbol,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            target_price=target_price,
            stop_loss=stop_loss,
            position_size=position_size,
            risk_level=self._assess_risk_level(confidence, market_context),
            timing=timing,
            market_context=market_context,
            technical_signals=technical_data,
            sentiment_score=ai_analysis.get("sentiment_score"),
            ai_analysis=ai_analysis,
            created_at=datetime.now()
        )
    
    async def _analyze_with_ai(self, symbol: str, market_data: Dict, news_data: List[Dict], 
                               technical_data: Dict, market_context: MarketContext) -> Dict[str, Any]:
        """Analyze with AI for comprehensive decision making"""
        
        prompt = f"""
You are an expert investment analyst. Analyze {symbol} for investment decision making.

CURRENT MARKET DATA:
- Price: ${market_data.get('price', 0):.2f}
- Volume: {market_data.get('volume', 0):,}
- Change: {market_data.get('change_percent', 0):.2f}%

TECHNICAL INDICATORS:
{json.dumps(technical_data, indent=2)}

RECENT NEWS ({len(news_data)} articles):
{json.dumps(news_data[:5], indent=2)}

MARKET CONTEXT:
- Volatility Regime: {market_context.volatility_regime}
- Market Trend: {market_context.market_trend}
- Sector Performance: {market_context.sector_performance}

Provide analysis in JSON format:
{{
    "recommendation": "BUY_NOW|BUY_LATER|SELL_NOW|SELL_LATER|HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation",
    "timing_factors": ["factor1", "factor2"],
    "risk_assessment": "LOW|MEDIUM|HIGH",
    "sentiment_score": -1.0 to 1.0,
    "key_drivers": ["driver1", "driver2"],
    "market_impact": "bullish|bearish|neutral",
    "optimal_timing": "immediate|wait_1d|wait_1w|avoid"
}}
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                llm_request = {
                    "prompt": prompt,
                    "max_tokens": 800,
                    "temperature": 0.3,
                    "task_type": "investment_analysis"
                }
                
                url = f"{LLM_PROXY_URL}/api/chat"
                async with session.post(url, json=llm_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_ai_response(result.get("response", ""))
                    else:
                        logger.error(f"LLM service error: {response.status}")
                        return self._get_fallback_analysis(symbol)
                        
        except Exception as e:
            logger.error(f"Error calling LLM for {symbol}: {e}")
            return self._get_fallback_analysis(symbol)
    
    async def _determine_action(self, symbol: str, market_data: Dict, technical_data: Dict,
                               ai_analysis: Dict, market_context: MarketContext, 
                               risk_profile: str) -> Tuple[str, float, str]:
        """Determine investment action with confidence and reasoning"""
        
        # Get AI recommendation
        ai_recommendation = ai_analysis.get("recommendation", "HOLD")
        ai_confidence = ai_analysis.get("confidence", 0.5)
        
        # Calculate technical confidence
        technical_confidence = self._calculate_technical_confidence(technical_data)
        
        # Calculate market context confidence
        market_confidence = self._calculate_market_confidence(market_context)
        
        # Combine confidences with weights
        combined_confidence = (
            ai_confidence * 0.4 +
            technical_confidence * 0.3 +
            market_confidence * 0.3
        )
        
        # Apply risk profile adjustments
        confidence_thresholds = {
            "conservative": 0.7,
            "moderate": 0.6,
            "aggressive": 0.5
        }
        
        threshold = confidence_thresholds.get(risk_profile, 0.6)
        
        # Determine final action
        if combined_confidence >= threshold:
            if ai_recommendation.startswith("BUY"):
                action = ai_recommendation
            elif ai_recommendation.startswith("SELL"):
                action = ai_recommendation
            else:
                action = "HOLD"
        else:
            action = "HOLD"
        
        reasoning = ai_analysis.get("reasoning", "Analysis completed")
        
        return action, combined_confidence, reasoning
    
    async def _analyze_timing(self, symbol: str, action: str, market_data: Dict, 
                             market_context: MarketContext) -> Dict[str, Any]:
        """Analyze optimal timing for investment decision"""
        
        timing_analysis = {
            "optimal_execution": "immediate",
            "confidence": 0.5,
            "factors": [],
            "risks": [],
            "alternatives": []
        }
        
        # Analyze market conditions for timing
        if market_context.volatility_regime == "high":
            timing_analysis["optimal_execution"] = "wait_1d"
            timing_analysis["factors"].append("High volatility - wait for stability")
            timing_analysis["confidence"] *= 0.8
        
        if market_context.market_trend == "bearish" and action.startswith("BUY"):
            timing_analysis["optimal_execution"] = "wait_1w"
            timing_analysis["factors"].append("Bearish market - wait for reversal")
            timing_analysis["confidence"] *= 0.7
        
        # Check for upcoming events
        upcoming_events = [event for event in market_context.economic_calendar 
                          if event.get("impact") == "high"]
        if upcoming_events:
            timing_analysis["factors"].append(f"High-impact events: {len(upcoming_events)}")
            timing_analysis["optimal_execution"] = "wait_1d"
        
        return timing_analysis
    
    def _calculate_position_size(self, confidence: float, risk_profile: str, 
                                market_context: MarketContext) -> str:
        """Calculate position size based on confidence and risk profile"""
        
        base_sizes = {
            "conservative": {"low": "SMALL", "medium": "SMALL", "high": "MEDIUM"},
            "moderate": {"low": "SMALL", "medium": "MEDIUM", "high": "LARGE"},
            "aggressive": {"low": "MEDIUM", "medium": "LARGE", "high": "LARGE"}
        }
        
        # Adjust for market conditions
        if market_context.volatility_regime == "high":
            confidence *= 0.8
        elif market_context.volatility_regime == "low":
            confidence *= 1.1
        
        # Determine confidence level
        if confidence < 0.5:
            level = "low"
        elif confidence < 0.8:
            level = "medium"
        else:
            level = "high"
        
        return base_sizes.get(risk_profile, base_sizes["moderate"]).get(level, "MEDIUM")
    
    def _calculate_price_targets(self, symbol: str, action: str, market_data: Dict, 
                                technical_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Calculate target price and stop loss"""
        
        current_price = market_data.get("price", 0)
        if not current_price:
            return None, None
        
        # Calculate target based on action
        if action.startswith("BUY"):
            # Use technical indicators for target
            sma_20 = technical_data.get("sma_20", current_price)
            sma_50 = technical_data.get("sma_50", current_price)
            
            # Target 5-10% above current price
            target_price = current_price * 1.07
            
            # Stop loss 3-5% below current price
            stop_loss = current_price * 0.96
            
        elif action.startswith("SELL"):
            # Target 5-10% below current price
            target_price = current_price * 0.93
            
            # Stop loss 3-5% above current price
            stop_loss = current_price * 1.04
            
        else:
            target_price = None
            stop_loss = None
        
        return target_price, stop_loss
    
    def _assess_risk_level(self, confidence: float, market_context: MarketContext) -> str:
        """Assess overall risk level"""
        
        # Base risk on confidence
        if confidence >= 0.8:
            base_risk = "LOW"
        elif confidence >= 0.6:
            base_risk = "MEDIUM"
        else:
            base_risk = "HIGH"
        
        # Adjust for market conditions
        if market_context.volatility_regime == "high":
            if base_risk == "LOW":
                base_risk = "MEDIUM"
            elif base_risk == "MEDIUM":
                base_risk = "HIGH"
        
        return base_risk
    
    def _calculate_technical_confidence(self, technical_data: Dict) -> float:
        """Calculate confidence based on technical indicators"""
        # Simple technical confidence calculation
        signals = []
        
        rsi = technical_data.get("rsi", 50)
        if 30 <= rsi <= 70:
            signals.append(0.7)
        else:
            signals.append(0.3)
        
        macd = technical_data.get("macd", {})
        if macd.get("signal", 0) > 0:
            signals.append(0.8)
        else:
            signals.append(0.4)
        
        return np.mean(signals) if signals else 0.5
    
    def _calculate_market_confidence(self, market_context: MarketContext) -> float:
        """Calculate confidence based on market context"""
        confidence = 0.5
        
        # Adjust for market trend
        if market_context.market_trend == "bullish":
            confidence += 0.2
        elif market_context.market_trend == "bearish":
            confidence -= 0.2
        
        # Adjust for volatility
        if market_context.volatility_regime == "low":
            confidence += 0.1
        elif market_context.volatility_regime == "high":
            confidence -= 0.1
        
        return max(0.1, min(0.9, confidence))
    
    async def _get_market_context(self) -> MarketContext:
        """Get current market context"""
        # Mock market context - in production, fetch from market data services
        return MarketContext(
            volatility_regime="medium",
            market_trend="bullish",
            sector_performance={"technology": 0.05, "finance": 0.02, "healthcare": -0.01},
            economic_calendar=[],
            correlation_matrix=pd.DataFrame(),
            market_breadth={"advancing": 0.6, "declining": 0.4}
        )
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response"""
        try:
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        return self._get_fallback_analysis("unknown")
    
    def _get_fallback_analysis(self, symbol: str) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        return {
            "recommendation": "HOLD",
            "confidence": 0.5,
            "reasoning": "AI analysis unavailable",
            "timing_factors": ["market_conditions"],
            "risk_assessment": "MEDIUM",
            "sentiment_score": 0.0,
            "key_drivers": ["technical_analysis"],
            "market_impact": "neutral",
            "optimal_timing": "wait_1d"
        }

# Initialize decision engine
decision_engine = DecisionEngine()

# Mock services for now
class LLMClient:
    pass

class MarketDataService:
    async def get_current_data(self, symbol: str) -> Dict:
        return {"price": 150.0, "volume": 1000000, "change_percent": 2.5}

class NewsService:
    async def get_recent_news(self, symbol: str) -> List[Dict]:
        return [{"title": "Sample news", "sentiment": "positive"}]

class TechnicalAnalysisService:
    async def get_indicators(self, symbol: str) -> Dict:
        return {"rsi": 65, "macd": {"signal": 0.5}, "sma_20": 148, "sma_50": 145}

@app.get("/api/recommendation/{symbol}")
async def get_recommendation(symbol: str, 
                           include_timing: bool = True,
                           risk_profile: str = "moderate") -> Dict[str, Any]:
    """Get investment recommendation for a symbol"""
    try:
        recommendation = await decision_engine.get_investment_recommendation(
            symbol, include_timing, risk_profile
        )
        
        return {
            "symbol": recommendation.symbol,
            "action": recommendation.action,
            "confidence": recommendation.confidence,
            "reasoning": recommendation.reasoning,
            "target_price": recommendation.target_price,
            "stop_loss": recommendation.stop_loss,
            "position_size": recommendation.position_size,
            "risk_level": recommendation.risk_level,
            "timing": recommendation.timing,
            "sentiment_score": recommendation.sentiment_score,
            "technical_signals": recommendation.technical_signals,
            "ai_analysis": recommendation.ai_analysis,
            "created_at": recommendation.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recommendation for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-analysis")
async def get_market_analysis() -> Dict[str, Any]:
    """Get overall market analysis"""
    try:
        market_context = await decision_engine._get_market_context()
        
        return {
            "volatility_regime": market_context.volatility_regime,
            "market_trend": market_context.market_trend,
            "sector_performance": market_context.sector_performance,
            "market_breadth": market_context.market_breadth,
            "recommendations": {
                "bullish_sectors": ["technology", "finance"],
                "bearish_sectors": ["healthcare"],
                "overall_sentiment": "neutral"
            }
        }
    except Exception as e:
        logger.error(f"Error getting market analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 