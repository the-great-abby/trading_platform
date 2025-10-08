#!/usr/bin/env python3
"""
Update Paper Trading Engine Configuration
This script ensures the paper trading engine uses the correct configuration file
"""

import yaml
import json
import os
import sys
from pathlib import Path

def update_paper_trading_engine_config():
    """Update paper trading engine to use the correct configuration"""
    
    print("🔧 Updating Paper Trading Engine Configuration...")
    print("=" * 50)
    
    # Paths
    config_file = "config/paper_trading_strategies.yaml"
    engine_script = "scripts/setup_paper_trading.py"
    
    # Check if config file exists
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return False
    
    try:
        # Read the configuration
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"📖 Loaded configuration from: {config_file}")
        
        # Extract key settings for the engine
        portfolio_config = config.get('portfolio', {})
        initial_capital = portfolio_config.get('initial_capital', 4000.0)
        max_daily_trades = portfolio_config.get('max_daily_trades', 4)
        max_daily_loss = portfolio_config.get('max_daily_loss', 150.0)
        
        # Get strategy names
        strategies = []
        for strategy_name, strategy_config in config.get('strategies', {}).items():
            if strategy_config.get('enabled', False):
                strategies.append(strategy_name)
        
        # Create engine configuration
        engine_config = {
            'initial_capital': initial_capital,
            'max_position_size': config.get('dynamic_sizing', {}).get('max_position_size', 0.12),
            'max_risk_per_trade': 0.015,  # Default risk per trade
            'trading_interval': 60,  # 1 minute intervals
            'strategies': strategies,
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'SPY', 'QQQ'],
            'enable_alerts': True,
            'performance_tracking': True,
            'max_daily_trades': max_daily_trades,
            'max_daily_loss': max_daily_loss,
            'max_monthly_trades': portfolio_config.get('max_monthly_trades', 8),
            'min_cash_reserve': portfolio_config.get('min_cash_reserve', 0.15)
        }
        
        # Write engine configuration
        engine_config_file = "config/paper_trading_engine.json"
        with open(engine_config_file, 'w') as f:
            json.dump(engine_config, f, indent=2)
        
        print(f"✅ Engine configuration saved to: {engine_config_file}")
        
        # Display configuration summary
        print("\n📊 Paper Trading Engine Configuration:")
        print(f"  💰 Initial Capital: ${initial_capital:,.2f}")
        print(f"  📈 Max Daily Trades: {max_daily_trades}")
        print(f"  📉 Max Daily Loss: ${max_daily_loss:,.2f}")
        print(f"  🎯 Max Position Size: {engine_config['max_position_size']:.1%}")
        print(f"  🎯 Max Monthly Trades: {engine_config['max_monthly_trades']}")
        print(f"  💵 Min Cash Reserve: {engine_config['min_cash_reserve']:.1%}")
        
        print(f"\n🎯 Active Strategies ({len(strategies)}):")
        for strategy in strategies:
            print(f"  ✅ {strategy}")
        
        print(f"\n📊 Symbols ({len(engine_config['symbols'])}):")
        print(f"  {', '.join(engine_config['symbols'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Paper Trading Engine Configuration Update")
    print("=" * 50)
    
    if update_paper_trading_engine_config():
        print("\n✅ Paper trading engine configuration updated successfully!")
        print("\n🔧 Next Steps:")
        print("  1. Run: make paper-trading-restart")
        print("  2. Run: make paper-trading-verify-balance")
        print("  3. Run: make paper-trading-status")
    else:
        print("\n❌ Failed to update configuration")
        sys.exit(1)

if __name__ == "__main__":
    main()




















