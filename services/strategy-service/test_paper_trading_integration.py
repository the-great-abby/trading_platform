"""
Test Backtest Engine with Real Paper Trading Configuration
========================================================
Tests the backtest engine with the same configuration used in paper trading.
"""

import asyncio
import logging
import sys
import os

# Add src to path for imports
sys.path.append('/app/src')
sys.path.append('/app')

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.services.mock_options_data_service import MockOptionsDataService
from src.utils.error_handler import log_backtest_progress

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paper trading configuration (matching the actual paper trading setup)
PAPER_TRADING_CONFIG = {
    "initial_capital": 2000.0,
    "symbols": ["AMD", "PYPL", "INTC"],
    "strategies": ["IronCondor", "RegimeSwitching", "BollingerBands"],
    "trading_interval": 300,  # 5 minutes
    "max_position_size": 0.1,  # 10%
    "max_risk_per_trade": 0.05,  # 5%
    "start_date": "2023-01-01",
    "end_date": "2024-12-31"
}

async def test_paper_trading_backtest():
    """Test backtest engine with paper trading configuration"""
    
    logger.info("🧪 Testing Backtest Engine with Paper Trading Configuration")
    logger.info("=" * 70)
    
    # Log configuration
    log_backtest_progress("paper_trading_test_started", PAPER_TRADING_CONFIG)
    
    logger.info(f"📊 Paper Trading Configuration:")
    logger.info(f"   Initial Capital: ${PAPER_TRADING_CONFIG['initial_capital']}")
    logger.info(f"   Symbols: {PAPER_TRADING_CONFIG['symbols']}")
    logger.info(f"   Strategies: {PAPER_TRADING_CONFIG['strategies']}")
    logger.info(f"   Date Range: {PAPER_TRADING_CONFIG['start_date']} to {PAPER_TRADING_CONFIG['end_date']}")
    logger.info(f"   Max Position Size: {PAPER_TRADING_CONFIG['max_position_size'] * 100}%")
    logger.info(f"   Max Risk Per Trade: {PAPER_TRADING_CONFIG['max_risk_per_trade'] * 100}%")
    
    try:
        # Initialize backtest engine with mock data (same as containerized environment)
        engine = BacktestEngine(use_real_data=False, use_cache=False)
        
        # Test options service integration
        if engine.options_service:
            logger.info(f"✅ Options service initialized: {type(engine.options_service).__name__}")
            
            # Test mock options data
            test_options = engine.options_service.get_liquid_options("AMD", min_volume=10)
            logger.info(f"✅ Mock options data test: {len(test_options)} options generated for AMD")
        else:
            logger.warning("⚠️ No options service available")
        
        # Run backtest with paper trading configuration
        log_backtest_progress("running_paper_trading_backtest", PAPER_TRADING_CONFIG)
        
        results = await engine.run_backtest(
            symbols=PAPER_TRADING_CONFIG["symbols"],
            start_date=PAPER_TRADING_CONFIG["start_date"],
            end_date=PAPER_TRADING_CONFIG["end_date"],
            strategies=PAPER_TRADING_CONFIG["strategies"]
        )
        
        # Analyze results
        if results:
            logger.info(f"\n📊 BACKTEST RESULTS:")
            logger.info("-" * 50)
            
            for strategy_name, result in results.items():
                if result:
                    final_value = PAPER_TRADING_CONFIG["initial_capital"] * (1 + result.total_return)
                    
                    logger.info(f"{strategy_name}:")
                    logger.info(f"  Total Return: {result.total_return:.2%}")
                    logger.info(f"  Final Value: ${final_value:.2f}")
                    logger.info(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
                    logger.info(f"  Max Drawdown: {result.max_drawdown_pct:.2%}")
                    logger.info(f"  Total Trades: {result.total_trades}")
                    logger.info(f"  Win Rate: {result.win_rate:.2%}")
                    logger.info(f"  Profit Factor: {result.profit_factor:.2f}")
                    logger.info("")
                    
                    # Log structured result
                    log_backtest_progress("strategy_result", {
                        "strategy": strategy_name,
                        "total_return": result.total_return,
                        "final_value": final_value,
                        "sharpe_ratio": result.sharpe_ratio,
                        "max_drawdown_pct": result.max_drawdown_pct,
                        "total_trades": result.total_trades,
                        "win_rate": result.win_rate,
                        "profit_factor": result.profit_factor,
                        "initial_capital": PAPER_TRADING_CONFIG["initial_capital"]
                    })
                else:
                    logger.warning(f"❌ {strategy_name}: No results")
                    log_backtest_progress("strategy_failed", {"strategy": strategy_name, "reason": "no_results"})
            
            # Find best performing strategy
            best_strategy = None
            best_return = -float('inf')
            
            for strategy_name, result in results.items():
                if result and result.total_return > best_return:
                    best_return = result.total_return
                    best_strategy = strategy_name
            
            if best_strategy:
                best_result = results[best_strategy]
                best_final_value = PAPER_TRADING_CONFIG["initial_capital"] * (1 + best_result.total_return)
                
                logger.info(f"🏆 BEST PERFORMING STRATEGY: {best_strategy}")
                logger.info(f"   Return: {best_return:.2%}")
                logger.info(f"   Final Value: ${best_final_value:.2f}")
                logger.info(f"   Profit: ${best_final_value - PAPER_TRADING_CONFIG['initial_capital']:.2f}")
                
                log_backtest_progress("best_strategy_identified", {
                    "strategy": best_strategy,
                    "total_return": best_return,
                    "final_value": best_final_value,
                    "profit": best_final_value - PAPER_TRADING_CONFIG["initial_capital"]
                })
        else:
            logger.error("❌ No backtest results returned")
            log_backtest_progress("backtest_failed", {"reason": "no_results_returned"})
        
        logger.info("✅ Paper trading backtest test completed successfully")
        log_backtest_progress("paper_trading_test_completed", {"status": "success"})
        
    except Exception as e:
        logger.error(f"❌ Paper trading backtest test failed: {e}")
        log_backtest_progress("paper_trading_test_failed", {"error": str(e)})
        raise

async def test_strategy_fallback_mechanisms():
    """Test strategy fallback mechanisms"""
    
    logger.info("\n🔄 Testing Strategy Fallback Mechanisms")
    logger.info("-" * 50)
    
    try:
        # Test with a strategy that requires options data
        from src.strategies.options.iron_condor_strategy import IronCondorStrategy
        
        strategy = IronCondorStrategy()
        
        # Test without options service
        can_execute = strategy.can_execute_with_options_data()
        logger.info(f"Iron Condor without options service: can_execute = {can_execute}")
        
        # Test fallback mechanism
        fallback_strategy = strategy.fallback_to_stock_strategy()
        if fallback_strategy:
            logger.info(f"✅ Fallback strategy created: {fallback_strategy.__class__.__name__}")
        else:
            logger.warning("⚠️ No fallback strategy available")
        
        # Test with mock options service
        mock_service = MockOptionsDataService()
        strategy.set_options_service(mock_service)
        
        can_execute_with_mock = strategy.can_execute_with_options_data()
        logger.info(f"Iron Condor with mock options service: can_execute = {can_execute_with_mock}")
        
        logger.info("✅ Strategy fallback mechanisms test completed")
        
    except Exception as e:
        logger.error(f"❌ Strategy fallback test failed: {e}")
        raise

async def main():
    """Run all tests"""
    
    logger.info("🚀 Starting Paper Trading Integration Tests")
    logger.info("=" * 70)
    
    try:
        # Test 1: Paper trading backtest
        await test_paper_trading_backtest()
        
        # Test 2: Strategy fallback mechanisms
        await test_strategy_fallback_mechanisms()
        
        logger.info("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)


