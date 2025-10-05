"""
StrategyMatcherService for trade recovery system
Handles intelligent strategy selection for recovered trades
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
import httpx

from ..models.active_trade import ActiveTrade, PositionType, TradeSide
from ..models.recovery_log import RecoveryLog, LogAction, LogSeverity

logger = logging.getLogger(__name__)


class StrategyMatch:
    """Represents a strategy match result"""
    
    def __init__(self, strategy_name: str, confidence_score: float, match_reason: str,
                 expected_performance: Optional[float] = None, risk_level: Optional[str] = None,
                 estimated_duration: Optional[str] = None):
        self.strategy_name = strategy_name
        self.confidence_score = confidence_score
        self.match_reason = match_reason
        self.expected_performance = expected_performance
        self.risk_level = risk_level
        self.estimated_duration = estimated_duration


class MarketConditions:
    """Represents current market conditions"""
    
    def __init__(self, volatility: float, trend: str, volume: int, 
                 historical_performance: Optional[Dict[str, float]] = None):
        self.volatility = volatility
        self.trend = trend
        self.volume = volume
        self.historical_performance = historical_performance or {}


class StrategyMatcherService:
    """Service for matching strategies to recovered trades"""
    
    def __init__(self, strategy_service_url: str, market_data_service_url: str, timeout: int = 30):
        """
        Initialize StrategyMatcherService
        
        Args:
            strategy_service_url: URL for strategy service
            market_data_service_url: URL for market data service
            timeout: Request timeout in seconds
        """
        self.strategy_service_url = strategy_service_url
        self.market_data_service_url = market_data_service_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_available_strategies(self, trade_symbol: Optional[str] = None, 
                                     position_type: Optional[PositionType] = None) -> List[Dict[str, Any]]:
        """
        Get available trading strategies
        
        Args:
            trade_symbol: Filter by specific symbol
            position_type: Filter by position type
            
        Returns:
            List of available strategies
        """
        try:
            logger.info(f"Getting available strategies for symbol={trade_symbol}, type={position_type}")
            
            params = {}
            if trade_symbol:
                params["trade_symbol"] = trade_symbol
            if position_type:
                params["position_type"] = position_type.value
            
            response = await self.client.get(
                f"{self.strategy_service_url}/strategies/available",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("strategies", [])
            else:
                raise Exception(f"Strategy service error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise StrategyMatchingError("Strategy service timeout")
        except httpx.RequestError as e:
            raise StrategyMatchingError(f"Strategy service request failed: {str(e)}")
    
    async def match_strategies_to_trade(self, trade: ActiveTrade, 
                                      market_conditions: Optional[MarketConditions] = None) -> List[StrategyMatch]:
        """
        Match strategies to a specific trade
        
        Args:
            trade: The trade to match strategies for
            market_conditions: Current market conditions
            
        Returns:
            List of strategy matches ordered by confidence score
        """
        try:
            logger.info(f"Matching strategies for trade {trade.symbol} (ID: {trade.id})")
            
            # Get market conditions if not provided
            if market_conditions is None:
                market_conditions = await self._get_market_conditions(trade.symbol)
            
            # Get available strategies
            available_strategies = await self.get_available_strategies(
                trade_symbol=trade.symbol,
                position_type=trade.position_type
            )
            
            # Score strategies
            matches = []
            for strategy in available_strategies:
                if not strategy.get("enabled", False):
                    continue
                
                score, reason = await self._score_strategy(strategy, trade, market_conditions)
                if score > 0.0:  # Only include strategies with positive scores
                    match = StrategyMatch(
                        strategy_name=strategy["name"],
                        confidence_score=score,
                        match_reason=reason,
                        expected_performance=await self._calculate_expected_performance(strategy, trade, market_conditions),
                        risk_level=await self._assess_risk_level(strategy, trade, market_conditions),
                        estimated_duration=await self._estimate_duration(strategy, trade, market_conditions)
                    )
                    matches.append(match)
            
            # Sort by confidence score (highest first)
            matches.sort(key=lambda x: x.confidence_score, reverse=True)
            
            logger.info(f"Found {len(matches)} strategy matches for trade {trade.symbol}")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to match strategies for trade {trade.symbol}: {e}")
            raise StrategyMatchingError(f"Failed to match strategies: {str(e)}")
    
    async def _get_market_conditions(self, symbol: str) -> MarketConditions:
        """Get current market conditions for a symbol"""
        try:
            response = await self.client.get(
                f"{self.market_data_service_url}/market-conditions/{symbol}"
            )
            
            if response.status_code == 200:
                data = response.json()
                return MarketConditions(
                    volatility=data.get("volatility", 0.2),
                    trend=data.get("trend", "SIDEWAYS"),
                    volume=data.get("volume", 1000000),
                    historical_performance=data.get("historical_performance", {})
                )
            else:
                # Return default conditions if API fails
                return MarketConditions(volatility=0.2, trend="SIDEWAYS", volume=1000000)
                
        except Exception as e:
            logger.warning(f"Failed to get market conditions for {symbol}: {e}")
            return MarketConditions(volatility=0.2, trend="SIDEWAYS", volume=1000000)
    
    async def _score_strategy(self, strategy: Dict[str, Any], trade: ActiveTrade, 
                            market_conditions: MarketConditions) -> Tuple[float, str]:
        """Score a strategy for a given trade and market conditions"""
        try:
            score = 0.0
            reasons = []
            
            # Check position type compatibility
            if trade.position_type.value not in strategy.get("supported_position_types", []):
                return 0.0, "Position type not supported"
            
            # Check symbol compatibility
            if strategy.get("supported_symbols") and trade.symbol not in strategy.get("supported_symbols", []):
                return 0.0, "Symbol not supported"
            
            # Check position size compatibility
            position_value = float(trade.current_value or 0)
            min_size = strategy.get("min_position_size", 0)
            max_size = strategy.get("max_position_size", float('inf'))
            
            if position_value < min_size:
                return 0.0, f"Position too small (${position_value} < ${min_size})"
            
            if position_value > max_size:
                return 0.0, f"Position too large (${position_value} > ${max_size})"
            
            # Base score for compatibility
            score += 0.3
            reasons.append("Position compatible")
            
            # Score based on market conditions
            strategy_category = strategy.get("category", "")
            
            if strategy_category == "MOMENTUM":
                if market_conditions.trend in ["BULLISH", "BEARISH"]:
                    score += 0.4
                    reasons.append(f"Strong {market_conditions.trend.lower()} trend")
                else:
                    score += 0.1
                    reasons.append("Weak trend for momentum strategy")
            
            elif strategy_category == "MEAN_REVERSION":
                if market_conditions.volatility > 0.3:
                    score += 0.4
                    reasons.append("High volatility for mean reversion")
                else:
                    score += 0.2
                    reasons.append("Moderate volatility for mean reversion")
            
            elif strategy_category == "OPTIONS":
                if trade.position_type == PositionType.OPTION:
                    score += 0.5
                    reasons.append("Options strategy for options position")
                else:
                    score += 0.1
                    reasons.append("Options strategy for non-options position")
            
            # Score based on trade characteristics
            if trade.unrealized_pnl and float(trade.unrealized_pnl) > 0:
                score += 0.1
                reasons.append("Profitable position")
            elif trade.unrealized_pnl and float(trade.unrealized_pnl) < 0:
                score += 0.2
                reasons.append("Loss position - strategy may help")
            
            # Score based on time held
            if trade.entry_date:
                days_held = (datetime.utcnow() - trade.entry_date).days
                if days_held > 30:
                    score += 0.1
                    reasons.append("Long-term position")
                elif days_held < 7:
                    score += 0.2
                    reasons.append("Short-term position")
            
            # Normalize score to 0-1 range
            score = min(1.0, max(0.0, score))
            
            reason = "; ".join(reasons)
            return score, reason
            
        except Exception as e:
            logger.error(f"Failed to score strategy {strategy.get('name', 'unknown')}: {e}")
            return 0.0, f"Scoring error: {str(e)}"
    
    async def _calculate_expected_performance(self, strategy: Dict[str, Any], trade: ActiveTrade, 
                                            market_conditions: MarketConditions) -> float:
        """Calculate expected performance for a strategy"""
        try:
            # This would typically involve historical backtesting
            # For now, return a mock calculation based on strategy category
            base_performance = 0.05  # 5% base
            
            strategy_category = strategy.get("category", "")
            if strategy_category == "MOMENTUM":
                if market_conditions.trend in ["BULLISH", "BEARISH"]:
                    return base_performance + 0.03  # 8%
                else:
                    return base_performance - 0.02  # 3%
            elif strategy_category == "MEAN_REVERSION":
                if market_conditions.volatility > 0.3:
                    return base_performance + 0.02  # 7%
                else:
                    return base_performance  # 5%
            elif strategy_category == "OPTIONS":
                return base_performance + 0.01  # 6%
            else:
                return base_performance  # 5%
                
        except Exception as e:
            logger.error(f"Failed to calculate expected performance: {e}")
            return 0.05
    
    async def _assess_risk_level(self, strategy: Dict[str, Any], trade: ActiveTrade, 
                               market_conditions: MarketConditions) -> str:
        """Assess risk level for a strategy"""
        try:
            risk_score = 0
            
            # Base risk from volatility
            if market_conditions.volatility > 0.4:
                risk_score += 2
            elif market_conditions.volatility > 0.2:
                risk_score += 1
            
            # Risk from strategy category
            strategy_category = strategy.get("category", "")
            if strategy_category == "OPTIONS":
                risk_score += 2
            elif strategy_category == "MOMENTUM":
                risk_score += 1
            
            # Risk from position size
            position_value = float(trade.current_value or 0)
            if position_value > 50000:
                risk_score += 1
            
            # Determine risk level
            if risk_score >= 4:
                return "HIGH"
            elif risk_score >= 2:
                return "MEDIUM"
            else:
                return "LOW"
                
        except Exception as e:
            logger.error(f"Failed to assess risk level: {e}")
            return "MEDIUM"
    
    async def _estimate_duration(self, strategy: Dict[str, Any], trade: ActiveTrade, 
                               market_conditions: MarketConditions) -> str:
        """Estimate strategy duration"""
        try:
            strategy_category = strategy.get("category", "")
            
            if strategy_category == "MOMENTUM":
                return "MEDIUM_TERM"
            elif strategy_category == "MEAN_REVERSION":
                return "SHORT_TERM"
            elif strategy_category == "OPTIONS":
                return "SHORT_TERM"
            else:
                return "MEDIUM_TERM"
                
        except Exception as e:
            logger.error(f"Failed to estimate duration: {e}")
            return "MEDIUM_TERM"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class StrategyMatchingError(Exception):
    """Exception raised when strategy matching fails"""
    pass








