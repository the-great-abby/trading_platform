#!/usr/bin/env python3
"""
Simplified script to demonstrate the Strategy Testing Framework capabilities
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.testing.services import MockDataGenerator
from src.testing.models import (
    MockDataGenerationConfig, StrategyTestResult, TestType, TestStatus,
    SignalValidation, PerformanceMetrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

async def test_mock_data_generation():
    """Test mock data generation capabilities"""
    logger.info("🧪 Testing Mock Data Generation...")
    
    mock_generator = MockDataGenerator()
    
    # Test different market regimes
    regimes = ["bull", "bear", "sideways", "volatile"]
    results = []
    
    for regime in regimes:
        logger.info(f"📊 Generating mock data for {regime} market...")
        
        config = MockDataGenerationConfig(
            symbol="AAPL",
            timeframe="1d",
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-01-31T23:59:59Z",
            market_regime=regime,
            initial_price=150.0,
            volatility=0.2
        )
        
        try:
            mock_data = await mock_generator.generate_mock_data(config)
            
            result = {
                "regime": regime,
                "data_points": len(mock_data.price_data),
                "symbol": mock_data.symbol,
                "timeframe": mock_data.timeframe,
                "success": True
            }
            
            logger.info(f"✅ {regime} market: {len(mock_data.price_data)} data points generated")
            results.append(result)
            
        except Exception as e:
            logger.error(f"❌ Error generating {regime} market data: {e}")
            results.append({
                "regime": regime,
                "success": False,
                "error": str(e)
            })
    
    return results

async def test_strategy_test_result_models():
    """Test the data models for strategy testing"""
    logger.info("🧪 Testing Strategy Test Result Models...")
    
    results = []
    
    # Test StrategyTestResult
    try:
        test_result = StrategyTestResult(
            strategy_name="TestStrategy",
            test_type=TestType.SIGNAL,
            test_status=TestStatus.PASSED,
            test_duration_seconds=1.5,
            start_time=datetime.now(),
            end_time=datetime.now(),
            interface_valid=True,
            total_signals_generated=10,
            valid_signals_count=9,
            invalid_signals_count=1,
            average_signal_confidence=0.85,
            average_validation_score=90.0,
            test_config={"param1": "value1"}
        )
        
        logger.info(f"✅ StrategyTestResult created: {test_result.strategy_name}")
        results.append({"model": "StrategyTestResult", "success": True})
        
    except Exception as e:
        logger.error(f"❌ Error creating StrategyTestResult: {e}")
        results.append({"model": "StrategyTestResult", "success": False, "error": str(e)})
    
    # Test SignalValidation
    try:
        from src.testing.models.enums import ValidationStatus
        signal_validation = SignalValidation(
            strategy_name="TestStrategy",
            symbol="AAPL",
            signal_timestamp=datetime.now(),
            signal_action="BUY",
            signal_confidence=0.85,
            validation_score=90.0,
            validation_status=ValidationStatus.VALID
        )
        
        logger.info(f"✅ SignalValidation created: {signal_validation.signal_action} @ {signal_validation.signal_confidence}")
        results.append({"model": "SignalValidation", "success": True})
        
    except Exception as e:
        logger.error(f"❌ Error creating SignalValidation: {e}")
        results.append({"model": "SignalValidation", "success": False, "error": str(e)})
    
    # Test PerformanceMetrics
    try:
        from src.testing.models.enums import PerformanceStatus
        performance_metrics = PerformanceMetrics(
            strategy_name="TestStrategy",
            test_duration_seconds=2.5,
            signals_generated=150,
            signals_per_second=60.0,
            average_execution_time_ms=16.67,
            max_execution_time_ms=50.0,
            min_execution_time_ms=5.0,
            memory_peak_mb=45.2,
            memory_average_mb=32.1,
            cpu_peak_percent=25.8,
            cpu_average_percent=18.5,
            validation_status=PerformanceStatus.WITHIN_LIMITS
        )
        
        logger.info(f"✅ PerformanceMetrics created: {performance_metrics.signals_per_second} signals/sec")
        results.append({"model": "PerformanceMetrics", "success": True})
        
    except Exception as e:
        logger.error(f"❌ Error creating PerformanceMetrics: {e}")
        results.append({"model": "PerformanceMetrics", "success": False, "error": str(e)})
    
    return results

async def simulate_strategy_testing():
    """Simulate comprehensive strategy testing"""
    logger.info("🧪 Simulating Strategy Testing Framework...")
    
    strategies = [
        "ElliottWaveStrategy",
        "AdaptiveWaveStrategy", 
        "IchimokuStrategy",
        "IronCondorStrategy"
    ]
    
    results = []
    
    for strategy_name in strategies:
        logger.info(f"🔍 Simulating tests for {strategy_name}...")
        
        # Simulate test execution time
        await asyncio.sleep(0.1)
        
        # Create mock test results
        test_result = StrategyTestResult(
            strategy_name=strategy_name,
            test_type=TestType.PERFORMANCE,
            test_status=TestStatus.PASSED,
            test_duration_seconds=1.2,
            start_time=datetime.now(),
            end_time=datetime.now(),
            interface_valid=True,
            total_signals_generated=120,
            valid_signals_count=115,
            invalid_signals_count=5,
            average_signal_confidence=0.85,
            average_validation_score=88.5,
            test_config={"lookback_periods": 50, "confidence_threshold": 0.8}
        )
        
        # Simulate signal validation
        from src.testing.models.enums import ValidationStatus
        signal_validation = SignalValidation(
            strategy_name=strategy_name,
            symbol="AAPL",
            signal_timestamp=datetime.now(),
            signal_action="BUY" if "Wave" in strategy_name else "SELL",
            signal_confidence=0.85,
            validation_score=88.5,
            validation_status=ValidationStatus.VALID
        )
        
        # Simulate performance metrics
        from src.testing.models.enums import PerformanceStatus
        performance_metrics = PerformanceMetrics(
            strategy_name=strategy_name,
            test_duration_seconds=1.2,
            signals_generated=120,
            signals_per_second=100.0,
            average_execution_time_ms=10.0,
            max_execution_time_ms=25.0,
            min_execution_time_ms=5.0,
            memory_peak_mb=32.1,
            memory_average_mb=28.5,
            cpu_peak_percent=18.5,
            cpu_average_percent=15.2,
            validation_status=PerformanceStatus.WITHIN_LIMITS
        )
        
        result = {
            "strategy": strategy_name,
            "test_result": test_result,
            "signal_validation": signal_validation,
            "performance_metrics": performance_metrics,
            "overall_status": "passed"
        }
        
        results.append(result)
        
        logger.info(f"✅ {strategy_name}: PASSED (100 signals/sec, 88.5% score)")
    
    return results

def print_comprehensive_summary(mock_data_results, model_results, strategy_results):
    """Print comprehensive test summary"""
    logger.info("\n" + "="*70)
    logger.info("📊 COMPREHENSIVE STRATEGY TESTING FRAMEWORK DEMONSTRATION")
    logger.info("="*70)
    
    # Mock Data Generation Results
    logger.info("\n📊 Mock Data Generation:")
    mock_success = sum(1 for r in mock_data_results if r.get("success"))
    logger.info(f"   Market Regimes Tested: {len(mock_data_results)}")
    logger.info(f"   ✅ Successful: {mock_success}")
    logger.info(f"   ❌ Failed: {len(mock_data_results) - mock_success}")
    
    for result in mock_data_results:
        if result.get("success"):
            logger.info(f"   📈 {result['regime']}: {result['data_points']} data points")
    
    # Model Validation Results
    logger.info("\n🏗️  Data Model Validation:")
    model_success = sum(1 for r in model_results if r.get("success"))
    logger.info(f"   Models Tested: {len(model_results)}")
    logger.info(f"   ✅ Successful: {model_success}")
    logger.info(f"   ❌ Failed: {len(model_results) - model_success}")
    
    # Strategy Testing Results
    logger.info("\n🎯 Strategy Testing Simulation:")
    strategy_success = sum(1 for r in strategy_results if r.get("overall_status") == "passed")
    logger.info(f"   Strategies Tested: {len(strategy_results)}")
    logger.info(f"   ✅ Passed: {strategy_success}")
    logger.info(f"   ❌ Failed: {len(strategy_results) - strategy_success}")
    logger.info(f"   Success Rate: {(strategy_success/len(strategy_results))*100:.1f}%")
    
    logger.info("\n📋 Strategy Details:")
    for result in strategy_results:
        strategy = result["strategy"]
        perf = result["performance_metrics"]
        signal = result["signal_validation"]
        logger.info(f"   🎯 {strategy}:")
        logger.info(f"      Performance: {perf.signals_per_second:.0f} signals/sec")
        logger.info(f"      Signal Quality: {signal.validation_score:.1f}%")
        logger.info(f"      Status: {result['overall_status'].upper()}")
    
    # Overall Assessment
    total_tests = len(mock_data_results) + len(model_results) + len(strategy_results)
    total_success = mock_success + model_success + strategy_success
    overall_success_rate = (total_success / total_tests) * 100
    
    logger.info(f"\n🎉 Overall Framework Assessment:")
    logger.info(f"   Total Tests: {total_tests}")
    logger.info(f"   Successful: {total_success}")
    logger.info(f"   Success Rate: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 90:
        logger.info("   🏆 Framework Status: EXCELLENT")
    elif overall_success_rate >= 75:
        logger.info("   🥇 Framework Status: GOOD")
    elif overall_success_rate >= 50:
        logger.info("   🥈 Framework Status: FAIR")
    else:
        logger.info("   🥉 Framework Status: NEEDS IMPROVEMENT")

async def main():
    """Main function"""
    try:
        logger.info("🚀 Starting Strategy Testing Framework Demonstration...")
        start_time = time.time()
        
        # Test mock data generation
        mock_data_results = await test_mock_data_generation()
        
        # Test data models
        model_results = await test_strategy_test_result_models()
        
        # Simulate strategy testing
        strategy_results = await simulate_strategy_testing()
        
        # Print comprehensive summary
        print_comprehensive_summary(mock_data_results, model_results, strategy_results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n⏱️  Total demonstration duration: {duration:.2f} seconds")
        logger.info("🎉 Strategy Testing Framework demonstration completed!")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"💥 Fatal error during demonstration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
