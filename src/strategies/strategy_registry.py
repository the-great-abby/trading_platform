"""
Dynamic Strategy Registry - Automatically discovers and registers all available strategies
"""

import os
import importlib
import inspect
import logging
from typing import Dict, List, Type, Optional, Set
from pathlib import Path

from .base import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Dynamic strategy registry that automatically discovers all available strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, Type[BaseStrategy]] = {}
        self.strategy_categories: Dict[str, List[str]] = {
            'basic': [],
            'options': [],
            'advanced': [],
            'new': []  # New category for our improved strategies
        }
        self.discovered = False
    
    def discover_strategies(self) -> Dict[str, Type[BaseStrategy]]:
        """Automatically discover all strategy classes in the strategies directory"""
        if self.discovered:
            return self.strategies
        
        logger.info("🔍 Discovering available strategies...")
        
        # Get the strategies directory path
        strategies_dir = Path(__file__).parent
        discovered_count = 0
        
        # Walk through all Python files in the strategies directory
        for strategy_file in strategies_dir.rglob("*.py"):
            if strategy_file.name.startswith("__"):
                continue
            
            # Convert file path to module path
            relative_path = strategy_file.relative_to(strategies_dir)
            module_path = f"src.strategies.{str(relative_path).replace('/', '.').replace('.py', '')}"
            
            try:
                # Import the module
                module = importlib.import_module(module_path)
                
                # Find all classes that inherit from BaseStrategy
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseStrategy) and 
                        obj != BaseStrategy):
                        
                        strategy_name = name
                        self.strategies[strategy_name] = obj
                        
                        # Categorize the strategy
                        category = self._categorize_strategy(strategy_name, obj)
                        self.strategy_categories[category].append(strategy_name)
                        
                        discovered_count += 1
                        logger.info(f"✅ Discovered strategy: {strategy_name} (category: {category})")
                
            except ImportError as e:
                logger.warning(f"⚠️ Could not import {module_path}: {e}")
            except Exception as e:
                logger.error(f"❌ Error discovering strategies in {strategy_file}: {e}")
        
        self.discovered = True
        logger.info(f"🎯 Total strategies discovered: {discovered_count}")
        logger.info(f"📊 Categories: {dict((k, len(v)) for k, v in self.strategy_categories.items())}")
        
        return self.strategies
    
    def _categorize_strategy(self, strategy_name: str, strategy_class: Type[BaseStrategy]) -> str:
        """Categorize a strategy based on its name and characteristics"""
        
        # New improved strategies
        if any(keyword in strategy_name.lower() for keyword in ['risk', 'regime', 'timeframe', 'adaptive']):
            return 'new'
        
        # Options strategies
        if any(keyword in strategy_name.lower() for keyword in ['option', 'put', 'call', 'condor', 'spread', 'greeks']):
            return 'options'
        
        # Advanced strategies
        if any(keyword in strategy_name.lower() for keyword in ['neural', 'quantum', 'ensemble', 'enhanced', 'advanced', 'ml', 'ai']):
            return 'advanced'
        
        # Basic strategies (default)
        return 'basic'
    
    def get_strategy(self, name: str) -> Optional[Type[BaseStrategy]]:
        """Get a strategy class by name"""
        if not self.discovered:
            self.discover_strategies()
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> Dict[str, Type[BaseStrategy]]:
        """Get all discovered strategies"""
        if not self.discovered:
            self.discover_strategies()
        return self.strategies.copy()
    
    def get_strategies_by_category(self, category: str) -> List[str]:
        """Get strategy names by category"""
        if not self.discovered:
            self.discover_strategies()
        return self.strategy_categories.get(category, [])
    
    def get_all_categories(self) -> Dict[str, List[str]]:
        """Get all categories with their strategies"""
        if not self.discovered:
            self.discover_strategies()
        return self.strategy_categories.copy()
    
    def create_strategy_instance(self, name: str, **kwargs) -> Optional[BaseStrategy]:
        """Create a strategy instance by name"""
        strategy_class = self.get_strategy(name)
        if strategy_class:
            try:
                return strategy_class(**kwargs)
            except Exception as e:
                logger.error(f"Error creating strategy instance {name}: {e}")
                return None
        return None
    
    def get_strategy_info(self, name: str) -> Optional[Dict]:
        """Get information about a strategy"""
        strategy_class = self.get_strategy(name)
        if strategy_class:
            return {
                'name': name,
                'class': strategy_class,
                'docstring': strategy_class.__doc__ or '',
                'category': self._get_strategy_category(name),
                'module': strategy_class.__module__
            }
        return None
    
    def _get_strategy_category(self, strategy_name: str) -> str:
        """Get the category of a specific strategy"""
        for category, strategies in self.strategy_categories.items():
            if strategy_name in strategies:
                return category
        return 'unknown'
    
    def list_strategies(self) -> str:
        """Return a formatted list of all strategies"""
        if not self.discovered:
            self.discover_strategies()
        
        output = "🎯 Available Strategies:\n"
        output += "=" * 50 + "\n"
        
        for category, strategies in self.strategy_categories.items():
            if strategies:
                output += f"\n📊 {category.upper()} ({len(strategies)} strategies):\n"
                for strategy in sorted(strategies):
                    output += f"  • {strategy}\n"
        
        return output
    
    def validate_strategies(self) -> Dict[str, List[str]]:
        """Validate that all discovered strategies can be instantiated"""
        validation_results = {
            'valid': [],
            'invalid': [],
            'errors': []
        }
        
        for name, strategy_class in self.strategies.items():
            try:
                # Try to create an instance
                instance = strategy_class()
                validation_results['valid'].append(name)
                logger.info(f"✅ Strategy {name} is valid")
            except Exception as e:
                validation_results['invalid'].append(name)
                validation_results['errors'].append(f"{name}: {str(e)}")
                logger.warning(f"⚠️ Strategy {name} failed validation: {e}")
        
        return validation_results


# Global registry instance
strategy_registry = StrategyRegistry()


def get_strategy_registry() -> StrategyRegistry:
    """Get the global strategy registry instance"""
    return strategy_registry


def discover_strategies() -> Dict[str, Type[BaseStrategy]]:
    """Discover all available strategies"""
    return strategy_registry.discover_strategies()


def get_strategies_by_category(category: str) -> List[str]:
    """Get strategies by category"""
    return strategy_registry.get_strategies_by_category(category)


def create_strategy_instance(name: str, **kwargs) -> Optional[BaseStrategy]:
    """Create a strategy instance by name"""
    return strategy_registry.create_strategy_instance(name, **kwargs) 