"""
Strategy Factory - Creates and manages strategy instances for the ensemble
"""

import logging
from typing import Dict, Type, Optional
from .base import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyFactory:
    """Factory for creating and managing strategy instances"""
    
    def __init__(self):
        self.strategies = {}
        self._registered_strategies = {}
    
    def register_strategy(self, name: str, strategy_class: Type[BaseStrategy]):
        """Register a strategy class"""
        self._registered_strategies[name] = strategy_class
        logger.info(f"Registered strategy: {name}")
    
    def create_strategy(self, name: str, **kwargs) -> Optional[BaseStrategy]:
        """Create a strategy instance"""
        if name not in self._registered_strategies:
            logger.warning(f"Strategy {name} not registered")
            return None
        
        try:
            strategy_class = self._registered_strategies[name]
            strategy = strategy_class(**kwargs)
            self.strategies[name] = strategy
            logger.info(f"Created strategy instance: {name}")
            return strategy
        except Exception as e:
            logger.error(f"Error creating strategy {name}: {e}")
            return None
    
    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """Get an existing strategy instance"""
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> Dict[str, BaseStrategy]:
        """Get all strategy instances"""
        return self.strategies.copy()
    
    def create_ensemble_strategies(self) -> Dict[str, BaseStrategy]:
        """Create all strategies needed for the winning ensemble"""
        ensemble_strategies = {
            'WinningEnsemble': 'WinningEnsembleStrategy',  # Our new ensemble strategy
            'Ichimoku': 'IchimokuStrategy',
            'CashSecuredPut': 'CashSecuredPutStrategy',
            'SMACrossover': 'SMACrossoverStrategy', 
            'Momentum': 'MomentumStrategy',
            'MeanReversion': 'MeanReversionStrategy',
            'EnhancedDayTrading': 'EnhancedDayTradingStrategy',
            'RegimeSwitching': 'RegimeSwitchingStrategy',
            'GreeksEnhanced': 'GreeksEnhancedStrategy',
            'IronCondor': 'IronCondorStrategy',
            'Volatility': 'VolatilityStrategy'
        }
        
        created_strategies = {}
        
        for strategy_name, class_name in ensemble_strategies.items():
            try:
                # Try to import and create the strategy
                strategy = self._create_strategy_by_name(class_name)
                if strategy:
                    created_strategies[strategy_name] = strategy
                    logger.info(f"Created ensemble strategy: {strategy_name}")
            except Exception as e:
                logger.warning(f"Could not create {strategy_name}: {e}")
                continue
        
        return created_strategies
    
    def _create_strategy_by_name(self, class_name: str) -> Optional[BaseStrategy]:
        """Create strategy by class name using dynamic import"""
        try:
            # Import strategy modules dynamically
            if class_name == 'IchimokuStrategy':
                from .ichimoku_strategy import IchimokuStrategy
                return IchimokuStrategy()
            elif class_name == 'CashSecuredPutStrategy':
                from .options.cash_secured_put_strategy import CashSecuredPutStrategy
                return CashSecuredPutStrategy()
            elif class_name == 'SMACrossoverStrategy':
                from .momentum.sma_crossover_strategy import SMACrossoverStrategy
                return SMACrossoverStrategy()
            elif class_name == 'MomentumStrategy':
                from .momentum.momentum_strategy import MomentumStrategy
                return MomentumStrategy()
            elif class_name == 'MeanReversionStrategy':
                from .mean_reversion.mean_reversion_strategy import MeanReversionStrategy
                return MeanReversionStrategy()
            elif class_name == 'EnhancedDayTradingStrategy':
                from .enhanced_day_trading_strategy import EnhancedDayTradingStrategy
                return EnhancedDayTradingStrategy()
            elif class_name == 'RegimeSwitchingStrategy':
                from .advanced.regime_switching_strategy import RegimeSwitchingStrategy
                return RegimeSwitchingStrategy()
            elif class_name == 'GreeksEnhancedStrategy':
                from .options.greeks_enhanced_strategy import GreeksEnhancedStrategy
                return GreeksEnhancedStrategy()
            elif class_name == 'IronCondorStrategy':
                from .options.iron_condor_strategy import IronCondorStrategy
                return IronCondorStrategy()
            elif class_name == 'VolatilityStrategy':
                from .volatility_strategy import VolatilityStrategy
                return VolatilityStrategy()
            elif class_name == 'WinningEnsembleStrategy':
                from .winning_ensemble_strategy import WinningEnsembleStrategy
                return WinningEnsembleStrategy()
            else:
                logger.warning(f"Unknown strategy class: {class_name}")
                return None
                
        except ImportError as e:
            logger.warning(f"Could not import {class_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating {class_name}: {e}")
            return None
    
    def cleanup(self):
        """Clean up strategy instances"""
        self.strategies.clear()
        logger.info("Cleaned up strategy instances") 