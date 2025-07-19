"""
Strategy Service - Internal microservice for trading strategy operations
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
from datetime import datetime
import asyncio
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Strategy Service", version="1.0.0")

class StrategyConfig(BaseModel):
    name: str
    symbol: str
    parameters: Dict[str, Any]

class StrategyStatus(BaseModel):
    name: str
    is_active: bool
    symbol: str
    parameters: Dict[str, Any]
    performance: Dict[str, Any]

class SignalRequest(BaseModel):
    strategy_name: str
    symbol: str
    market_data: Dict[str, Any]

class StockRecommendationRequest(BaseModel):
    symbol: str
    include_ai_analysis: bool = True
    include_news_sentiment: bool = True
    include_risk_assessment: bool = True
    strategies: Optional[List[str]] = None  # If None, use all available strategies

class StockRecommendationResponse(BaseModel):
    symbol: str
    overall_recommendation: str  # "BUY", "SELL", "HOLD"
    confidence: float
    current_price: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasoning: str
    risk_level: str
    position_size_recommendation: str
    strategies_analysis: List[Dict[str, Any]]
    ai_analysis: Optional[Dict[str, Any]]
    news_sentiment: Optional[Dict[str, Any]]
    risk_assessment: Optional[Dict[str, Any]]
    timestamp: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "strategy-service"}

@app.get("/status")
async def get_status():
    """Get strategy service status"""
    return {
        "service": "strategy-service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/strategies")
async def get_strategies():
    """Get all available strategies"""
    try:
        strategies = [
            {
                "name": "sma_crossover",
                "display_name": "SMA Crossover",
                "description": "Simple Moving Average Crossover Strategy",
                "parameters": {
                    "short_window": 20,
                    "long_window": 50,
                    "min_volume": 1000000
                },
                "is_active": True
            },
            {
                "name": "rsi_strategy",
                "display_name": "RSI Strategy",
                "description": "Relative Strength Index Strategy",
                "parameters": {
                    "period": 14,
                    "oversold": 30,
                    "overbought": 70
                },
                "is_active": True
            },
            {
                "name": "macd_strategy",
                "display_name": "MACD Strategy",
                "description": "Moving Average Convergence Divergence Strategy",
                "parameters": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "is_active": True
            },
            {
                "name": "bollinger_bands",
                "display_name": "Bollinger Bands Strategy",
                "description": "Bollinger Bands Mean Reversion Strategy",
                "parameters": {
                    "period": 20,
                    "std_dev": 2
                },
                "is_active": True
            },
            {
                "name": "news_enhanced",
                "display_name": "News Enhanced Strategy",
                "description": "Technical indicators enhanced with news sentiment",
                "parameters": {
                    "sentiment_threshold": 0.6,
                    "news_weight": 0.3,
                    "technical_weight": 0.7
                },
                "is_active": True
            },
            {
                "name": "momentum_strategy",
                "display_name": "Momentum Strategy",
                "description": "Price momentum and volume analysis",
                "parameters": {
                    "momentum_period": 20,
                    "volume_threshold": 1.5
                },
                "is_active": True
            },
            {
                "name": "mean_reversion_strategy",
                "display_name": "Mean Reversion Strategy",
                "description": "Mean reversion with moving averages",
                "parameters": {
                    "short_ma": 20,
                    "long_ma": 50,
                    "deviation_threshold": 0.05
                },
                "is_active": True
            },
            {
                "name": "ichimoku_strategy",
                "display_name": "Ichimoku Cloud Strategy",
                "description": "Ichimoku Cloud analysis with entry/exit levels",
                "parameters": {
                    "tenkan_period": 9,
                    "kijun_period": 26,
                    "senkou_b_period": 52,
                    "displacement": 26
                },
                "is_active": True
            },
            {
                "name": "ichimoku_enhanced_strategy",
                "display_name": "Enhanced Ichimoku Strategy",
                "description": "Ichimoku Cloud with AI enhancement and multi-strategy confirmation",
                "parameters": {
                    "ai_weight": 0.3,
                    "technical_weight": 0.7,
                    "min_confidence": 0.6,
                    "use_llm_evaluation": True
                },
                "is_active": True
            },
            {
                "name": "adaptive_momentum_strategy",
                "display_name": "Adaptive Momentum Strategy",
                "description": "Dynamically adjusts parameters based on market conditions and volatility regimes",
                "parameters": {
                    "base_momentum_period": 20,
                    "volatility_lookback": 50,
                    "trend_lookback": 100,
                    "min_confidence": 0.6
                },
                "is_active": True
            },
            {
                "name": "regime_switching_strategy",
                "display_name": "Regime Switching Strategy",
                "description": "Identifies market regimes and switches between different trading approaches",
                "parameters": {
                    "lookback_period": 100,
                    "regime_confidence_threshold": 0.7,
                    "min_regime_duration": 20
                },
                "is_active": True
            },
            {
                "name": "quantum_momentum_strategy",
                "display_name": "Quantum Momentum Strategy",
                "description": "Quantum-inspired strategy using superposition and entanglement of market indicators",
                "parameters": {
                    "qubit_count": 8,
                    "measurement_threshold": 0.6,
                    "entanglement_strength": 0.5,
                    "superposition_decay": 0.1
                },
                "is_active": True
            },
            {
                "name": "neural_network_strategy",
                "display_name": "Neural Network Strategy",
                "description": "Deep learning-based strategy using LSTM networks for pattern recognition",
                "parameters": {
                    "sequence_length": 50,
                    "hidden_size": 64,
                    "num_layers": 2,
                    "learning_rate": 0.001,
                    "min_confidence": 0.6
                },
                "is_active": True
            }
        ]
        
        return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategies: {str(e)}")

@app.get("/strategies/{strategy_name}")
async def get_strategy(strategy_name: str):
    """Get specific strategy details"""
    try:
        # Mock strategy details
        strategy = {
            "name": strategy_name,
            "display_name": strategy_name.replace("_", " ").title(),
            "description": f"Strategy for {strategy_name}",
            "parameters": {
                "period": 20,
                "threshold": 0.5
            },
            "is_active": True,
            "performance": {
                "total_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.08,
                "win_rate": 0.65,
                "total_trades": 45
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return strategy
    except Exception as e:
        logger.error(f"Failed to get strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategy: {str(e)}")

@app.post("/strategies/{strategy_name}/activate")
async def activate_strategy(strategy_name: str):
    """Activate a strategy"""
    try:
        logger.info(f"Activating strategy: {strategy_name}")
        
        return {
            "message": f"Strategy {strategy_name} activated successfully",
            "strategy_name": strategy_name,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to activate strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate strategy: {str(e)}")

@app.post("/strategies/{strategy_name}/deactivate")
async def deactivate_strategy(strategy_name: str):
    """Deactivate a strategy"""
    try:
        logger.info(f"Deactivating strategy: {strategy_name}")
        
        return {
            "message": f"Strategy {strategy_name} deactivated successfully",
            "strategy_name": strategy_name,
            "status": "inactive",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to deactivate strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate strategy: {str(e)}")

@app.put("/strategies/{strategy_name}/config")
async def update_strategy_config(strategy_name: str, config: StrategyConfig):
    """Update strategy configuration"""
    try:
        logger.info(f"Updating strategy config for {strategy_name}")
        
        return {
            "message": f"Strategy {strategy_name} configuration updated successfully",
            "strategy_name": strategy_name,
            "new_config": config.dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to update strategy config for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update strategy config: {str(e)}")

@app.post("/strategies/{strategy_name}/signal", response_model=Dict[str, Any])
async def generate_signal(strategy_name: str, request: SignalRequest):
    """Generate trading signal for a strategy"""
    try:
        # Mock signal generation
        import random
        
        signal_types = ["buy", "sell", "hold"]
        signal = random.choice(signal_types)
        
        if signal == "hold":
            return {
                "strategy_name": strategy_name,
                "symbol": request.symbol,
                "signal": "hold",
                "confidence": 0.0,
                "reason": "No clear signal",
                "timestamp": datetime.now().isoformat()
            }
        
        confidence = random.uniform(0.6, 0.95)
        price = request.market_data.get("close", 100.0)
        
        logger.info(f"Generated {signal} signal for {request.symbol} using {strategy_name}")
        
        return {
            "strategy_name": strategy_name,
            "symbol": request.symbol,
            "signal": signal,
            "confidence": confidence,
            "price": price,
            "quantity": 100 if signal == "buy" else 0,
            "reason": f"{strategy_name} strategy indicates {signal} signal",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to generate signal for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate signal: {str(e)}")

@app.post("/recommendations/stock", response_model=StockRecommendationResponse)
async def get_stock_recommendation(request: StockRecommendationRequest):
    """
    Get comprehensive stock recommendation combining multiple strategies, AI analysis, and risk assessment
    
    This endpoint provides:
    - Multi-strategy analysis
    - AI-powered market analysis
    - News sentiment analysis
    - Risk assessment
    - Entry/exit recommendations
    - Position sizing guidance
    """
    try:
        logger.info(f"Generating stock recommendation for {request.symbol}")
        
        # Get market data for the symbol
        market_data = await _get_market_data(request.symbol)
        if not market_data:
            raise HTTPException(status_code=404, detail=f"Market data not available for {request.symbol}")
        
        # Get strategies to analyze
        available_strategies = await _get_available_strategies()
        strategies_to_analyze = request.strategies or [s["name"] for s in available_strategies if s["is_active"]]
        
        # Analyze with each strategy
        strategies_analysis = []
        for strategy_name in strategies_to_analyze:
            try:
                strategy_signal = await _analyze_with_strategy(strategy_name, request.symbol, market_data)
                if strategy_signal:
                    strategies_analysis.append(strategy_signal)
            except Exception as e:
                logger.warning(f"Strategy {strategy_name} failed for {request.symbol}: {e}")
        
        # Get AI analysis if requested
        ai_analysis = None
        if request.include_ai_analysis:
            try:
                ai_analysis = await _get_ai_analysis(request.symbol, strategies_analysis, market_data)
            except Exception as e:
                logger.warning(f"AI analysis failed for {request.symbol}: {e}")
        
        # Get news sentiment if requested
        news_sentiment = None
        if request.include_news_sentiment:
            try:
                news_sentiment = await _get_news_sentiment(request.symbol)
            except Exception as e:
                logger.warning(f"News sentiment failed for {request.symbol}: {e}")
        
        # Get risk assessment if requested
        risk_assessment = None
        if request.include_risk_assessment:
            try:
                risk_assessment = await _get_risk_assessment(request.symbol, market_data)
            except Exception as e:
                logger.warning(f"Risk assessment failed for {request.symbol}: {e}")
        
        # Combine all analyses into final recommendation
        recommendation = await _combine_analyses(
            request.symbol, 
            strategies_analysis, 
            ai_analysis, 
            news_sentiment, 
            risk_assessment,
            market_data
        )
        
        logger.info(f"Generated recommendation for {request.symbol}: {recommendation['overall_recommendation']}")
        
        return StockRecommendationResponse(**recommendation)
        
    except Exception as e:
        logger.error(f"Failed to generate stock recommendation for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")

async def _get_market_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Get market data for a symbol"""
    try:
        # Mock market data - in production, this would call your market data service
        return {
            "symbol": symbol,
            "current_price": 150.0,
            "open": 148.5,
            "high": 152.0,
            "low": 147.8,
            "volume": 1000000,
            "market_cap": 2500000000,
            "pe_ratio": 25.5,
            "price_change_24h": 0.02,
            "volume_change_24h": 0.15,
            "volatility": 0.025
        }
    except Exception as e:
        logger.error(f"Failed to get market data for {symbol}: {e}")
        return None

async def _get_available_strategies() -> List[Dict[str, Any]]:
    """Get list of available strategies"""
    strategies_response = await get_strategies()
    return strategies_response["strategies"]

async def _analyze_with_strategy(strategy_name: str, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze a symbol with a specific strategy"""
    try:
        # Mock strategy analysis - in production, this would call actual strategy implementations
        import random
        
        signals = ["BUY", "SELL", "HOLD"]
        signal = random.choice(signals)
        confidence = random.uniform(0.3, 0.9)
        
        return {
            "strategy_name": strategy_name,
            "signal": signal,
            "confidence": confidence,
            "reasoning": f"{strategy_name} indicates {signal.lower()} signal",
            "metadata": {
                "technical_indicators": ["RSI", "MACD", "SMA"],
                "signal_strength": confidence,
                "risk_level": "medium"
            }
        }
    except Exception as e:
        logger.error(f"Strategy analysis failed for {strategy_name}: {e}")
        return None

async def _get_ai_analysis(symbol: str, strategies_analysis: List[Dict], market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get AI-powered market analysis"""
    try:
        # Mock AI analysis - in production, this would call your Ollama service
        return {
            "sentiment_score": 0.65,
            "confidence": 0.8,
            "reasoning": "AI analysis indicates positive momentum with strong technical indicators",
            "risk_assessment": "medium",
            "market_impact": "bullish",
            "recommended_action": "BUY",
            "key_factors": ["technical_momentum", "volume_increase", "positive_sentiment"],
            "market_volatility": "medium"
        }
    except Exception as e:
        logger.error(f"AI analysis failed for {symbol}: {e}")
        return None

async def _get_news_sentiment(symbol: str) -> Optional[Dict[str, Any]]:
    """Get news sentiment analysis"""
    try:
        # Mock news sentiment - in production, this would call your news service
        return {
            "sentiment_score": 0.7,
            "sentiment_label": "positive",
            "confidence": 0.75,
            "recent_events_count": 5,
            "impact_score": 0.6,
            "key_events": [
                {"type": "earnings", "sentiment": "positive", "impact": "high"},
                {"type": "product_launch", "sentiment": "positive", "impact": "medium"}
            ]
        }
    except Exception as e:
        logger.error(f"News sentiment failed for {symbol}: {e}")
        return None

async def _get_risk_assessment(symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get risk assessment for the symbol"""
    try:
        # Mock risk assessment - in production, this would call your risk service
        return {
            "risk_level": "medium",
            "volatility_score": 0.4,
            "liquidity_score": 0.8,
            "correlation_risk": 0.3,
            "sector_risk": 0.5,
            "recommended_position_size": "3-5%",
            "max_position_size": "10%",
            "stop_loss_recommendation": "8%",
            "take_profit_recommendation": "15%"
        }
    except Exception as e:
        logger.error(f"Risk assessment failed for {symbol}: {e}")
        return None

async def _combine_analyses(symbol: str, strategies_analysis: List[Dict], ai_analysis: Optional[Dict], 
                           news_sentiment: Optional[Dict], risk_assessment: Optional[Dict], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Combine all analyses into final recommendation"""
    
    # Calculate overall recommendation
    buy_signals = [s for s in strategies_analysis if s["signal"] == "BUY"]
    sell_signals = [s for s in strategies_analysis if s["signal"] == "SELL"]
    hold_signals = [s for s in strategies_analysis if s["signal"] == "HOLD"]
    
    # Weight the signals
    buy_score = sum(s["confidence"] for s in buy_signals)
    sell_score = sum(s["confidence"] for s in sell_signals)
    hold_score = sum(s["confidence"] for s in hold_signals)
    
    # Add AI analysis weight
    if ai_analysis:
        if ai_analysis.get("recommended_action") == "BUY":
            buy_score += ai_analysis.get("confidence", 0) * 1.5
        elif ai_analysis.get("recommended_action") == "SELL":
            sell_score += ai_analysis.get("confidence", 0) * 1.5
    
    # Add news sentiment weight
    if news_sentiment:
        sentiment_score = news_sentiment.get("sentiment_score", 0)
        if sentiment_score > 0.3:
            buy_score += abs(sentiment_score) * 0.5
        elif sentiment_score < -0.3:
            sell_score += abs(sentiment_score) * 0.5
    
    # Determine overall recommendation
    if buy_score > sell_score and buy_score > hold_score and buy_score > 1.0:
        overall_recommendation = "BUY"
        confidence = min(buy_score / (buy_score + sell_score + hold_score), 0.95)
    elif sell_score > buy_score and sell_score > hold_score and sell_score > 1.0:
        overall_recommendation = "SELL"
        confidence = min(sell_score / (buy_score + sell_score + hold_score), 0.95)
    else:
        overall_recommendation = "HOLD"
        confidence = min(hold_score / (buy_score + sell_score + hold_score), 0.8)
    
    # Calculate target prices
    current_price = market_data["current_price"]
    target_price = None
    stop_loss = None
    take_profit = None
    
    if overall_recommendation == "BUY":
        target_price = current_price * 1.15  # 15% upside
        stop_loss = current_price * 0.92  # 8% downside
        take_profit = current_price * 1.20  # 20% upside
    elif overall_recommendation == "SELL":
        target_price = current_price * 0.85  # 15% downside
        stop_loss = current_price * 1.08  # 8% upside
        take_profit = current_price * 0.80  # 20% downside
    
    # Generate reasoning
    reasoning_parts = []
    if buy_signals:
        reasoning_parts.append(f"{len(buy_signals)} strategies indicate BUY")
    if sell_signals:
        reasoning_parts.append(f"{len(sell_signals)} strategies indicate SELL")
    if ai_analysis:
        reasoning_parts.append(f"AI analysis: {ai_analysis.get('reasoning', '')}")
    if news_sentiment:
        reasoning_parts.append(f"News sentiment: {news_sentiment.get('sentiment_label', 'neutral')}")
    
    reasoning = ". ".join(reasoning_parts) if reasoning_parts else "Insufficient data for clear recommendation"
    
    # Determine risk level
    risk_level = "medium"
    if risk_assessment:
        risk_level = risk_assessment.get("risk_level", "medium")
    
    # Position size recommendation
    position_size = "3-5% of portfolio"
    if risk_assessment:
        position_size = risk_assessment.get("recommended_position_size", "3-5% of portfolio")
    
    return {
        "symbol": symbol,
        "overall_recommendation": overall_recommendation,
        "confidence": confidence,
        "current_price": current_price,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "reasoning": reasoning,
        "risk_level": risk_level,
        "position_size_recommendation": position_size,
        "strategies_analysis": strategies_analysis,
        "ai_analysis": ai_analysis,
        "news_sentiment": news_sentiment,
        "risk_assessment": risk_assessment,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/strategies/{strategy_name}/performance")
async def get_strategy_performance(strategy_name: str, period: str = "1m"):
    """Get strategy performance metrics"""
    try:
        # Mock performance data
        performance = {
            "strategy_name": strategy_name,
            "period": period,
            "total_return": 0.15,
            "annualized_return": 0.18,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.08,
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "total_trades": 45,
            "avg_trade_duration": "3.2 days",
            "best_trade": 0.12,
            "worst_trade": -0.05,
            "current_streak": 3,
            "longest_winning_streak": 8,
            "longest_losing_streak": 3
        }
        
        return performance
    except Exception as e:
        logger.error(f"Failed to get performance for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
