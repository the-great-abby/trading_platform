#!/usr/bin/env python3
"""
Demo: Centralized Backtest Configuration

This script demonstrates how to use the new centralized backtesting
configuration system to easily manage all backtest parameters.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.backtest_config import (
    BacktestConfig, BacktestMode, RiskProfile,
    get_backtest_config, get_preset_config, load_config_from_env
)
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.strategies.momentum.macd_strategy import MACDStrategy
from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demonstrate_preset_configs():
    """Demonstrate different preset configurations"""
    print("\n" + "="*80)
    print("PRESET CONFIGURATIONS DEMO")
    print("="*80)
    
    presets = [
        ('quick_test', 'Quick 30-day test with conservative settings'),
        ('comprehensive_test', 'Comprehensive 2-year test with LLM'),
        ('aggressive_test', 'Aggressive 6-month test'),
        ('conservative_test', 'Conservative 1-year test')
    ]
    
    for preset_name, description in presets:
        print(f"\n📋 {preset_name.upper()}:")
        print(f"   Description: {description}")
        
        try:
            config = get_preset_config(preset_name)
            print(f"   Mode: {config.backtest_mode.value}")
            print(f"   Risk Profile: {config.risk_profile.value}")
            print(f"   Period: {config.test_period_days} days")
            print(f"   Symbols: {config.max_symbols} max")
            print(f"   Capital: ${config.initial_capital:,.0f}")
            print(f"   Position Size: {config.position_size:.1%}")
            print(f"   Stop Loss: {config.stop_loss_pct:.1%}")
            print(f"   Take Profit: {config.take_profit_pct:.1%}")
            print(f"   Daily Trades: {config.max_daily_trades}")
            print(f"   LLM Enabled: {config.use_llm}")
            
        except Exception as e:
            print(f"   Error: {e}")


def demonstrate_custom_configs():
    """Demonstrate custom configuration creation"""
    print("\n" + "="*80)
    print("CUSTOM CONFIGURATIONS DEMO")
    print("="*80)
    
    # Example 1: Conservative small account
    print(f"\n💰 CONSERVATIVE SMALL ACCOUNT:")
    conservative_config = get_backtest_config(
        mode=BacktestMode.CONSERVATIVE,
        risk_profile=RiskProfile.ULTRA_CONSERVATIVE,
        initial_capital=1000.0,
        max_symbols=10,
        test_period_days=90,
        backtest_name="conservative_small_account"
    )
    
    print(f"   Capital: ${conservative_config.initial_capital:,.0f}")
    print(f"   Position Size: {conservative_config.position_size:.1%}")
    print(f"   Max Position: {conservative_config.max_position_size:.1%}")
    print(f"   Stop Loss: {conservative_config.stop_loss_pct:.1%}")
    print(f"   Take Profit: {conservative_config.take_profit_pct:.1%}")
    print(f"   Max Daily Trades: {conservative_config.max_daily_trades}")
    print(f"   Confidence Threshold: {conservative_config.confidence_threshold:.1%}")
    
    # Example 2: Aggressive large account
    print(f"\n🚀 AGGRESSIVE LARGE ACCOUNT:")
    aggressive_config = get_backtest_config(
        mode=BacktestMode.AGGRESSIVE,
        risk_profile=RiskProfile.ULTRA_AGGRESSIVE,
        initial_capital=100000.0,
        max_symbols=50,
        test_period_days=365,
        use_llm=True,
        backtest_name="aggressive_large_account"
    )
    
    print(f"   Capital: ${aggressive_config.initial_capital:,.0f}")
    print(f"   Position Size: {aggressive_config.position_size:.1%}")
    print(f"   Max Position: {aggressive_config.max_position_size:.1%}")
    print(f"   Stop Loss: {aggressive_config.stop_loss_pct:.1%}")
    print(f"   Take Profit: {aggressive_config.take_profit_pct:.1%}")
    print(f"   Max Daily Trades: {aggressive_config.max_daily_trades}")
    print(f"   Confidence Threshold: {aggressive_config.confidence_threshold:.1%}")
    print(f"   LLM Enabled: {aggressive_config.use_llm}")


def demonstrate_environment_config():
    """Demonstrate loading configuration from environment variables"""
    print("\n" + "="*80)
    print("ENVIRONMENT CONFIGURATION DEMO")
    print("="*80)
    
    # Set some environment variables
    os.environ['BACKTEST_MODE'] = 'fast'
    os.environ['RISK_PROFILE'] = 'conservative'
    os.environ['INITIAL_CAPITAL'] = '5000'
    os.environ['MAX_SYMBOLS'] = '15'
    os.environ['TEST_PERIOD_DAYS'] = '60'
    
    try:
        config = load_config_from_env()
        print(f"✅ Loaded configuration from environment:")
        print(f"   Mode: {config.backtest_mode.value}")
        print(f"   Risk Profile: {config.risk_profile.value}")
        print(f"   Capital: ${config.initial_capital:,.0f}")
        print(f"   Symbols: {config.max_symbols}")
        print(f"   Period: {config.test_period_days} days")
        
    except Exception as e:
        print(f"❌ Error loading from environment: {e}")
    
    # Clean up environment variables
    for key in ['BACKTEST_MODE', 'RISK_PROFILE', 'INITIAL_CAPITAL', 'MAX_SYMBOLS', 'TEST_PERIOD_DAYS']:
        if key in os.environ:
            del os.environ[key]


def demonstrate_config_validation():
    """Demonstrate configuration validation"""
    print("\n" + "="*80)
    print("CONFIGURATION VALIDATION DEMO")
    print("="*80)
    
    # Test valid configuration
    print(f"\n✅ Valid Configuration:")
    try:
        valid_config = get_backtest_config(
            mode=BacktestMode.STANDARD,
            risk_profile=RiskProfile.MODERATE,
            initial_capital=10000.0,
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        print(f"   Configuration created successfully")
        print(f"   Validation errors: {len(valid_config.validate())}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test invalid configuration
    print(f"\n❌ Invalid Configuration:")
    try:
        invalid_config = BacktestConfig(
            initial_capital=-1000,  # Negative capital
            position_size=1.5,      # Position size > 1
            start_date="2024-12-31",
            end_date="2024-01-01"   # End before start
        )
        errors = invalid_config.validate()
        print(f"   Validation errors: {len(errors)}")
        for error in errors:
            print(f"     - {error}")
            
    except Exception as e:
        print(f"   Error: {e}")


def demonstrate_config_export():
    """Demonstrate exporting configuration to different formats"""
    print("\n" + "="*80)
    print("CONFIGURATION EXPORT DEMO")
    print("="*80)
    
    config = get_backtest_config(
        mode=BacktestMode.STANDARD,
        risk_profile=RiskProfile.MODERATE,
        backtest_name="demo_config"
    )
    
    # Export to dictionary
    config_dict = config.to_dict()
    print(f"\n📋 Configuration as Dictionary:")
    print(f"   Keys: {len(config_dict)}")
    print(f"   Sample keys: {list(config_dict.keys())[:5]}")
    
    # Export to environment variables
    env_vars = config.to_env_vars()
    print(f"\n🔧 Configuration as Environment Variables:")
    print(f"   Variables: {len(env_vars)}")
    print(f"   Sample variables:")
    for key, value in list(env_vars.items())[:5]:
        print(f"     {key}={value}")


def run_backtest_with_config(config: BacktestConfig):
    """Run a backtest using the provided configuration"""
    print(f"\n🚀 Running backtest with configuration:")
    print(f"   Name: {config.backtest_name}")
    print(f"   Mode: {config.backtest_mode.value}")
    print(f"   Risk Profile: {config.risk_profile.value}")
    print(f"   Capital: ${config.initial_capital:,.0f}")
    print(f"   Symbols: {len(config.symbols)}")
    print(f"   Strategies: {len(config.strategies)}")
    print(f"   Period: {config.start_date} to {config.end_date}")
    
    try:
        # Create strategies based on config
        strategies = {}
        if 'MACD' in config.strategies:
            strategies['MACD Strategy'] = MACDStrategy()
        if 'BollingerBands' in config.strategies:
            strategies['Bollinger Bands Strategy'] = BollingerBandsStrategy()
        
        if not strategies:
            print("   ⚠️ No strategies available, skipping backtest")
            return None
        
        # Create backtest engine
        engine = BacktestEngine(
            use_cache=config.use_cache,
            use_real_data=config.use_real_data
        )
        
        # Run backtest
        results = engine.run_backtest(
            strategies=strategies,
            symbols=config.symbols[:5],  # Limit for demo
            start_date=config.start_date,
            end_date=config.end_date
        )
        
        # Store results with backtest name
        engine.store_results(
            results=results,
            symbols=config.symbols[:5],
            start_date=config.start_date,
            end_date=config.end_date,
            backtest_name=config.backtest_name
        )
        
        print(f"   ✅ Backtest completed successfully!")
        return results
        
    except Exception as e:
        print(f"   ❌ Backtest failed: {e}")
        return None


def main():
    """Main demo function"""
    logger.info("🚀 Starting Centralized Backtest Configuration Demo")
    
    print("\n" + "="*80)
    print("CENTRALIZED BACKTEST CONFIGURATION DEMO")
    print("="*80)
    
    # Step 1: Demonstrate preset configurations
    demonstrate_preset_configs()
    
    # Step 2: Demonstrate custom configurations
    demonstrate_custom_configs()
    
    # Step 3: Demonstrate environment configuration
    demonstrate_environment_config()
    
    # Step 4: Demonstrate configuration validation
    demonstrate_config_validation()
    
    # Step 5: Demonstrate configuration export
    demonstrate_config_export()
    
    # Step 6: Run a backtest with configuration
    print(f"\n📈 Step 6: Running backtest with configuration")
    config = get_preset_config('quick_test', backtest_name='demo_centralized_config')
    results = run_backtest_with_config(config)
    
    print(f"\n✅ Centralized Backtest Configuration Demo completed!")
    print(f"\n💡 Key Benefits:")
    print(f"  • Centralized parameter management")
    print(f"  • Preset configurations for common scenarios")
    print(f"  • Environment variable support")
    print(f"  • Configuration validation")
    print(f"  • Easy export to different formats")
    print(f"  • Risk profile and mode-based defaults")


if __name__ == "__main__":
    main() 