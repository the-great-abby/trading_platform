#!/usr/bin/env python3
"""
Live Trading Exit Strategy Service
Provides sophisticated exit strategy management for live trading
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ExitStrategyType(Enum):
    """Types of exit strategies"""
    TIME_BASED = "TIME_BASED"
    PROFIT_TARGET = "PROFIT_TARGET"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    VOLATILITY_BASED = "VOLATILITY_BASED"
    MOMENTUM_BASED = "MOMENTUM_BASED"
    CORRELATION_BASED = "CORRELATION_BASED"

@dataclass
class ExitStrategy:
    """Exit strategy configuration"""
    strategy_type: ExitStrategyType
    parameters: Dict[str, Any]
    is_active: bool = True
    priority: int = 1  # Higher number = higher priority
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class LiveTradingExitStrategyService:
    """Service for managing exit strategies in live trading"""
    
    def __init__(self):
        self.exit_strategies = {}
        self.strategy_performance = {}
        
        # Default exit strategies
        self.default_strategies = {
            'conservative': [
                ExitStrategy(
                    strategy_type=ExitStrategyType.TIME_BASED,
                    parameters={'max_days': 7, 'min_hours': 4},
                    priority=3
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.PROFIT_TARGET,
                    parameters={'target_pct': 0.10, 'min_target': 0.05},
                    priority=2
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.STOP_LOSS,
                    parameters={'loss_pct': 0.05, 'max_loss': 0.08},
                    priority=1
                )
            ],
            'aggressive': [
                ExitStrategy(
                    strategy_type=ExitStrategyType.TIME_BASED,
                    parameters={'max_days': 14, 'min_hours': 2},
                    priority=3
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.PROFIT_TARGET,
                    parameters={'target_pct': 0.20, 'min_target': 0.10},
                    priority=2
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.STOP_LOSS,
                    parameters={'loss_pct': 0.08, 'max_loss': 0.12},
                    priority=1
                )
            ],
            'swing_trading': [
                ExitStrategy(
                    strategy_type=ExitStrategyType.TIME_BASED,
                    parameters={'max_days': 30, 'min_hours': 24},
                    priority=3
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.PROFIT_TARGET,
                    parameters={'target_pct': 0.15, 'min_target': 0.08},
                    priority=2
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.STOP_LOSS,
                    parameters={'loss_pct': 0.06, 'max_loss': 0.10},
                    priority=1
                )
            ]
        }
        
        logger.info("Live Trading Exit Strategy Service initialized")
    
    def get_exit_strategies(self, strategy_name: str) -> List[ExitStrategy]:
        """Get exit strategies for a trading strategy"""
        if strategy_name in self.exit_strategies:
            return self.exit_strategies[strategy_name]
        
        # Return default strategies based on strategy type
        if 'day' in strategy_name.lower():
            return self.default_strategies['aggressive']
        elif 'swing' in strategy_name.lower():
            return self.default_strategies['swing_trading']
        else:
            return self.default_strategies['conservative']
    
    def set_exit_strategies(self, strategy_name: str, strategies: List[ExitStrategy]):
        """Set exit strategies for a trading strategy"""
        self.exit_strategies[strategy_name] = strategies
        logger.info(f"✅ Set {len(strategies)} exit strategies for {strategy_name}")
    
    async def evaluate_exit_conditions(self, position_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all exit conditions for a position"""
        strategy_name = position_data.get('strategy', 'UNKNOWN')
        strategies = self.get_exit_strategies(strategy_name)
        
        triggered_conditions = []
        
        for strategy in strategies:
            if not strategy.is_active:
                continue
                
            condition_result = await self.evaluate_strategy(strategy, position_data)
            if condition_result['is_triggered']:
                triggered_conditions.append(condition_result)
        
        # Sort by priority (highest first)
        triggered_conditions.sort(key=lambda x: x['priority'], reverse=True)
        
        return triggered_conditions
    
    async def evaluate_strategy(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a specific exit strategy"""
        
        if strategy.strategy_type == ExitStrategyType.TIME_BASED:
            return await self.evaluate_time_based_exit(strategy, position_data)
        elif strategy.strategy_type == ExitStrategyType.PROFIT_TARGET:
            return await self.evaluate_profit_target_exit(strategy, position_data)
        elif strategy.strategy_type == ExitStrategyType.STOP_LOSS:
            return await self.evaluate_stop_loss_exit(strategy, position_data)
        elif strategy.strategy_type == ExitStrategyType.TRAILING_STOP:
            return await self.evaluate_trailing_stop_exit(strategy, position_data)
        elif strategy.strategy_type == ExitStrategyType.VOLATILITY_BASED:
            return await self.evaluate_volatility_exit(strategy, position_data)
        else:
            return {
                'strategy_type': strategy.strategy_type.value,
                'is_triggered': False,
                'priority': strategy.priority,
                'reason': 'Strategy not implemented'
            }
    
    async def evaluate_time_based_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate time-based exit strategy"""
        params = strategy.parameters
        entry_time = position_data['entry_time']
        current_time = datetime.now()
        
        holding_days = (current_time - entry_time).days
        max_days = params.get('max_days', 30)
        
        is_triggered = holding_days >= max_days
        
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': is_triggered,
            'priority': strategy.priority,
            'reason': f"Time-based exit: {holding_days} days >= {max_days} days" if is_triggered else None,
            'current_value': holding_days,
            'threshold': max_days
        }
    
    async def evaluate_profit_target_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate profit target exit strategy"""
        params = strategy.parameters
        pnl_pct = position_data.get('unrealized_pnl_pct', 0.0)
        target_pct = params.get('target_pct', 0.10)
        
        is_triggered = pnl_pct >= target_pct
        
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': is_triggered,
            'priority': strategy.priority,
            'reason': f"Profit target reached: {pnl_pct:.1%} >= {target_pct:.1%}" if is_triggered else None,
            'current_value': pnl_pct,
            'threshold': target_pct
        }
    
    async def evaluate_stop_loss_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate stop loss exit strategy"""
        params = strategy.parameters
        pnl_pct = position_data.get('unrealized_pnl_pct', 0.0)
        loss_pct = params.get('loss_pct', 0.05)
        
        is_triggered = pnl_pct <= -loss_pct
        
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': is_triggered,
            'priority': strategy.priority,
            'reason': f"Stop loss triggered: {pnl_pct:.1%} <= -{loss_pct:.1%}" if is_triggered else None,
            'current_value': pnl_pct,
            'threshold': -loss_pct
        }
    
    async def evaluate_trailing_stop_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate trailing stop exit strategy"""
        # Placeholder implementation
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': False,
            'priority': strategy.priority,
            'reason': 'Trailing stop not implemented'
        }
    
    async def evaluate_volatility_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate volatility-based exit strategy"""
        # Placeholder implementation
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': False,
            'priority': strategy.priority,
            'reason': 'Volatility exit not implemented'
        }
    
    def get_strategy_performance(self, strategy_name: str) -> Dict[str, Any]:
        """Get performance metrics for exit strategies"""
        return self.strategy_performance.get(strategy_name, {
            'total_exits': 0,
            'successful_exits': 0,
            'average_holding_time': 0,
            'average_pnl': 0.0
        })

# Global instance
exit_strategy_service = LiveTradingExitStrategyService()
