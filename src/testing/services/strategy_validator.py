#!/usr/bin/env python3
"""
StrategyValidator service for Strategy Engine Testing Framework
Validates strategy interfaces and basic functionality
"""

import asyncio
import inspect
from typing import Dict, Any, List, Optional, Type
from datetime import datetime

from ..models import (
    TestType, TestStatus, StrategyTestResult, SignalValidation,
    PerformanceMetrics, TestCase
)


class StrategyValidator:
    """
    Validates strategy interfaces and basic functionality
    
    Ensures strategies implement required methods and follow expected patterns
    """
    
    def __init__(self):
        """Initialize strategy validator"""
        self.required_methods = [
            'generate_signal',
            'calculate_position_size'
        ]
        self.required_attributes = [
            'name',
            'config',
            'is_active'
        ]
    
    async def validate_strategy_interface(self, strategy_class: Type, 
                                        strategy_config: Dict[str, Any]) -> StrategyTestResult:
        """
        Validate strategy interface compliance
        
        Args:
            strategy_class: Strategy class to validate
            strategy_config: Configuration for strategy instantiation
            
        Returns:
            StrategyTestResult with validation results
        """
        start_time = datetime.utcnow()
        test_status = TestStatus.PASSED
        error_messages = []
        warnings = []
        
        try:
            # Check if strategy class exists and is importable
            if not strategy_class:
                raise ValueError("Strategy class is None")
            
            # Check required attributes
            interface_valid = await self._check_required_attributes(strategy_class)
            if not interface_valid:
                test_status = TestStatus.FAILED
                error_messages.append("Missing required attributes")
            
            # Check required methods
            methods_valid = await self._check_required_methods(strategy_class)
            if not methods_valid:
                test_status = TestStatus.FAILED
                error_messages.append("Missing required methods")
            
            # Check method signatures
            signatures_valid = await self._check_method_signatures(strategy_class)
            if not signatures_valid:
                test_status = TestStatus.FAILED
                error_messages.append("Invalid method signatures")
            
            # Test strategy instantiation
            instantiation_valid = await self._test_strategy_instantiation(
                strategy_class, strategy_config
            )
            if not instantiation_valid:
                test_status = TestStatus.FAILED
                error_messages.append("Strategy instantiation failed")
            
            # Test basic functionality
            basic_functionality_valid = await self._test_basic_functionality(
                strategy_class, strategy_config
            )
            if not basic_functionality_valid:
                test_status = TestStatus.FAILED
                error_messages.append("Basic functionality test failed")
            
        except Exception as e:
            test_status = TestStatus.ERROR
            error_messages.append(f"Validation error: {str(e)}")
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        return StrategyTestResult(
            strategy_name=getattr(strategy_class, '__name__', 'Unknown'),
            test_type=TestType.INTERFACE,
            test_status=test_status,
            test_duration_seconds=duration,
            start_time=start_time,
            end_time=end_time,
            interface_valid=(test_status == TestStatus.PASSED),
            total_signals_generated=0,
            valid_signals_count=0,
            invalid_signals_count=0,
            average_signal_confidence=0.0,
            average_validation_score=100.0 if test_status == TestStatus.PASSED else 0.0,
            error_messages=error_messages,
            warnings=warnings,
            test_config={"strategy_class": strategy_class.__name__, **strategy_config}
        )
    
    async def _check_required_attributes(self, strategy_class: Type) -> bool:
        """Check if strategy has required attributes"""
        try:
            # Create a temporary instance to check attributes
            temp_instance = strategy_class("test_strategy")
            
            for attr in self.required_attributes:
                if not hasattr(temp_instance, attr):
                    return False
            
            return True
        except Exception:
            return False
    
    async def _check_required_methods(self, strategy_class: Type) -> bool:
        """Check if strategy has required methods"""
        for method_name in self.required_methods:
            if not hasattr(strategy_class, method_name):
                return False
            
            method = getattr(strategy_class, method_name)
            if not callable(method):
                return False
        
        return True
    
    async def _check_method_signatures(self, strategy_class: Type) -> bool:
        """Check if method signatures are correct"""
        try:
            # Check generate_signal signature
            if hasattr(strategy_class, 'generate_signal'):
                method = getattr(strategy_class, 'generate_signal')
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                
                # Should have at least symbol and data parameters
                if 'symbol' not in params or 'data' not in params:
                    return False
            
            # Check calculate_position_size signature
            if hasattr(strategy_class, 'calculate_position_size'):
                method = getattr(strategy_class, 'calculate_position_size')
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                
                # Should have at least capital and price parameters
                if 'capital' not in params or 'price' not in params:
                    return False
            
            return True
        except Exception:
            return False
    
    async def _test_strategy_instantiation(self, strategy_class: Type, 
                                         config: Dict[str, Any]) -> bool:
        """Test if strategy can be instantiated"""
        try:
            strategy_instance = strategy_class("test_strategy", config)
            return strategy_instance is not None
        except Exception:
            return False
    
    async def _test_basic_functionality(self, strategy_class: Type, 
                                      config: Dict[str, Any]) -> bool:
        """Test basic strategy functionality"""
        try:
            # Create strategy instance
            strategy = strategy_class("test_strategy", config)
            
            # Test calculate_position_size with basic inputs
            position_size = strategy.calculate_position_size(
                capital=10000.0,
                price=100.0,
                risk_percentage=0.02
            )
            
            # Position size should be positive and reasonable
            if not isinstance(position_size, (int, float)) or position_size <= 0:
                return False
            
            return True
        except Exception:
            return False
    
    async def validate_strategy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate strategy configuration
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Validation results dictionary
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Check for required configuration keys
            required_keys = ['symbols', 'timeframe']
            for key in required_keys:
                if key not in config:
                    validation_results["errors"].append(f"Missing required config key: {key}")
                    validation_results["valid"] = False
            
            # Validate symbols
            if 'symbols' in config:
                symbols = config['symbols']
                if not isinstance(symbols, list) or len(symbols) == 0:
                    validation_results["errors"].append("Symbols must be a non-empty list")
                    validation_results["valid"] = False
                elif not all(isinstance(s, str) for s in symbols):
                    validation_results["errors"].append("All symbols must be strings")
                    validation_results["valid"] = False
            
            # Validate timeframe
            if 'timeframe' in config:
                timeframe = config['timeframe']
                valid_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
                if timeframe not in valid_timeframes:
                    validation_results["errors"].append(f"Invalid timeframe: {timeframe}")
                    validation_results["valid"] = False
            
            # Check for optional but recommended keys
            recommended_keys = ['lookback_periods', 'confidence_threshold', 'risk_percentage']
            for key in recommended_keys:
                if key not in config:
                    validation_results["recommendations"].append(f"Consider adding {key} to configuration")
            
            # Validate numeric parameters
            numeric_params = ['lookback_periods', 'confidence_threshold', 'risk_percentage']
            for param in numeric_params:
                if param in config:
                    value = config[param]
                    if not isinstance(value, (int, float)) or value <= 0:
                        validation_results["errors"].append(f"{param} must be a positive number")
                        validation_results["valid"] = False
            
            # Validate confidence threshold range
            if 'confidence_threshold' in config:
                threshold = config['confidence_threshold']
                if not (0.0 <= threshold <= 1.0):
                    validation_results["errors"].append("confidence_threshold must be between 0.0 and 1.0")
                    validation_results["valid"] = False
            
            # Validate risk percentage range
            if 'risk_percentage' in config:
                risk = config['risk_percentage']
                if not (0.0 <= risk <= 1.0):
                    validation_results["errors"].append("risk_percentage must be between 0.0 and 1.0")
                    validation_results["valid"] = False
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Configuration validation error: {str(e)}")
        
        return validation_results
    
    async def get_strategy_info(self, strategy_class: Type) -> Dict[str, Any]:
        """
        Get information about a strategy class
        
        Args:
            strategy_class: Strategy class to analyze
            
        Returns:
            Strategy information dictionary
        """
        try:
            info = {
                "class_name": strategy_class.__name__,
                "module": strategy_class.__module__,
                "docstring": strategy_class.__doc__,
                "methods": [],
                "attributes": [],
                "inheritance": [cls.__name__ for cls in strategy_class.__mro__]
            }
            
            # Get methods
            for name, method in inspect.getmembers(strategy_class, predicate=inspect.isfunction):
                if not name.startswith('_'):  # Skip private methods
                    sig = inspect.signature(method)
                    info["methods"].append({
                        "name": name,
                        "signature": str(sig),
                        "docstring": method.__doc__
                    })
            
            # Get attributes (try to instantiate to check)
            try:
                temp_instance = strategy_class("test")
                for attr in dir(temp_instance):
                    if not attr.startswith('_') and not callable(getattr(temp_instance, attr)):
                        info["attributes"].append(attr)
            except Exception:
                pass
            
            return info
            
        except Exception as e:
            return {
                "class_name": "Unknown",
                "error": str(e)
            }













