"""
Strategy Service Client Integration
Connects StrategyMatcherService to existing strategy service
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx

from ..services.strategy_matcher_service import StrategyMatcherService, StrategyMatchingError
from ...utils.trading_config import get_trade_recovery_config

logger = logging.getLogger(__name__)


class StrategyServiceClient:
    """Client for strategy service integration"""
    
    def __init__(self):
        """Initialize strategy service client"""
        self.config = get_trade_recovery_config()
        self.strategy_config = self.config['strategy_service']
        
        self.client = httpx.AsyncClient(
            base_url=self.strategy_config['base_url'],
            timeout=self.strategy_config['timeout']
        )
    
    async def get_available_strategies(self, trade_symbol: Optional[str] = None, 
                                     position_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available strategies from strategy service
        
        Args:
            trade_symbol: Filter by symbol
            position_type: Filter by position type
            
        Returns:
            List of available strategies
        """
        try:
            logger.info(f"Fetching available strategies from strategy service")
            
            params = {}
            if trade_symbol:
                params["symbol"] = trade_symbol
            if position_type:
                params["position_type"] = position_type
            
            response = await self.client.get(
                "/api/v1/strategies/available",
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
    
    async def get_strategy_performance(self, strategy_name: str, 
                                     days: int = 30) -> Dict[str, Any]:
        """
        Get strategy performance metrics
        
        Args:
            strategy_name: Name of the strategy
            days: Number of days for performance calculation
            
        Returns:
            Performance metrics
        """
        try:
            logger.info(f"Fetching performance for strategy {strategy_name}")
            
            response = await self.client.get(
                f"/api/v1/strategies/{strategy_name}/performance",
                params={"days": days}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Strategy service error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise StrategyMatchingError("Strategy service timeout")
        except httpx.RequestError as e:
            raise StrategyMatchingError(f"Strategy service request failed: {str(e)}")
    
    async def get_strategy_parameters(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get strategy parameters and configuration
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy parameters
        """
        try:
            logger.info(f"Fetching parameters for strategy {strategy_name}")
            
            response = await self.client.get(f"/api/v1/strategies/{strategy_name}/parameters")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Strategy service error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise StrategyMatchingError("Strategy service timeout")
        except httpx.RequestError as e:
            raise StrategyMatchingError(f"Strategy service request failed: {str(e)}")
    
    async def validate_strategy_for_trade(self, strategy_name: str, 
                                        trade_data: Dict[str, Any]) -> bool:
        """
        Validate if a strategy is suitable for a trade
        
        Args:
            strategy_name: Name of the strategy
            trade_data: Trade data to validate against
            
        Returns:
            True if strategy is suitable, False otherwise
        """
        try:
            logger.info(f"Validating strategy {strategy_name} for trade")
            
            response = await self.client.post(
                f"/api/v1/strategies/{strategy_name}/validate",
                json=trade_data
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("valid", False)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to validate strategy {strategy_name}: {e}")
            return False
    
    async def get_strategy_recommendations(self, trade_data: Dict[str, Any], 
                                         market_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get strategy recommendations for a trade
        
        Args:
            trade_data: Trade data
            market_conditions: Market conditions
            
        Returns:
            List of strategy recommendations
        """
        try:
            logger.info("Getting strategy recommendations from strategy service")
            
            response = await self.client.post(
                "/api/v1/strategies/recommend",
                json={
                    "trade": trade_data,
                    "market_conditions": market_conditions
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("recommendations", [])
            else:
                raise Exception(f"Strategy service error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise StrategyMatchingError("Strategy service timeout")
        except httpx.RequestError as e:
            raise StrategyMatchingError(f"Strategy service request failed: {str(e)}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class IntegratedStrategyMatcherService(StrategyMatcherService):
    """StrategyMatcherService with integrated strategy service client"""
    
    def __init__(self):
        """Initialize integrated strategy matcher service"""
        config = get_trade_recovery_config()
        super().__init__(
            strategy_service_url=config['strategy_service']['base_url'],
            market_data_service_url=config['market_data_service']['base_url'],
            timeout=config['strategy_service']['timeout']
        )
        
        self.strategy_client = StrategyServiceClient()
    
    async def get_available_strategies(self, trade_symbol: Optional[str] = None, 
                                     position_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Override to use integrated strategy service client"""
        try:
            logger.info(f"Getting available strategies using integrated strategy service")
            
            return await self.strategy_client.get_available_strategies(trade_symbol, position_type)
            
        except Exception as e:
            logger.error(f"Failed to get available strategies: {e}")
            raise StrategyMatchingError(f"Failed to get available strategies: {str(e)}")
    
    async def _score_strategy(self, strategy: Dict[str, Any], trade, market_conditions) -> tuple:
        """Override to use integrated strategy service for scoring"""
        try:
            # Convert trade to dict for API call
            trade_data = {
                "symbol": trade.symbol,
                "quantity": float(trade.quantity),
                "side": trade.side.value,
                "entry_price": float(trade.entry_price),
                "current_price": float(trade.current_price),
                "position_type": trade.position_type.value,
                "unrealized_pnl": float(trade.unrealized_pnl) if trade.unrealized_pnl else 0
            }
            
            # Get strategy validation from service
            is_valid = await self.strategy_client.validate_strategy_for_trade(
                strategy["name"], trade_data
            )
            
            if not is_valid:
                return 0.0, "Strategy not suitable for this trade"
            
            # Get strategy performance
            performance = await self.strategy_client.get_strategy_performance(strategy["name"])
            
            # Calculate score based on performance and trade characteristics
            base_score = 0.5  # Base score for valid strategies
            
            # Adjust score based on performance metrics
            if performance.get("sharpe_ratio", 0) > 1.0:
                base_score += 0.2
            if performance.get("win_rate", 0) > 0.6:
                base_score += 0.1
            if performance.get("max_drawdown", 1) < 0.1:
                base_score += 0.1
            
            # Adjust score based on market conditions
            if market_conditions.trend in ["BULLISH", "BEARISH"] and strategy.get("category") == "MOMENTUM":
                base_score += 0.2
            elif market_conditions.volatility > 0.3 and strategy.get("category") == "MEAN_REVERSION":
                base_score += 0.2
            
            # Normalize score to 0-1 range
            score = min(1.0, max(0.0, base_score))
            
            reason = f"Strategy validated with score {score:.2f}"
            return score, reason
            
        except Exception as e:
            logger.error(f"Failed to score strategy {strategy.get('name', 'unknown')}: {e}")
            return 0.0, f"Scoring error: {str(e)}"
    
    async def _calculate_expected_performance(self, strategy: Dict[str, Any], trade, market_conditions) -> float:
        """Override to use integrated strategy service for performance calculation"""
        try:
            performance = await self.strategy_client.get_strategy_performance(strategy["name"])
            return performance.get("annualized_return", 0.05)
            
        except Exception as e:
            logger.error(f"Failed to calculate expected performance: {e}")
            return 0.05  # Default 5% return
    
    async def close(self):
        """Close both clients"""
        await super().close()
        await self.strategy_client.close()








