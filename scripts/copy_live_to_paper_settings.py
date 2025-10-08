#!/usr/bin/env python3
"""
Copy Live Trading Settings to Paper Trading
This script copies the optimized live trading configuration to paper trading
"""

import yaml
import shutil
import os
import sys
from datetime import datetime
from pathlib import Path

def backup_existing_config(config_path: str) -> str:
    """Backup existing configuration file"""
    if os.path.exists(config_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{config_path}.backup_{timestamp}"
        shutil.copy2(config_path, backup_path)
        print(f"📋 Backed up existing config to: {backup_path}")
        return backup_path
    return None

def copy_live_to_paper_settings():
    """Copy live trading settings to paper trading configuration"""
    
    # File paths
    live_config_path = "config/live_trading_strategies.yaml"
    paper_config_path = "config/paper_trading_strategies.yaml"
    
    print("🔄 Copying Live Trading Settings to Paper Trading...")
    print("=" * 60)
    
    # Check if live trading config exists
    if not os.path.exists(live_config_path):
        print(f"❌ Live trading config not found: {live_config_path}")
        return False
    
    # Backup existing paper trading config
    backup_path = backup_existing_config(paper_config_path)
    
    try:
        # Read live trading configuration
        with open(live_config_path, 'r') as f:
            live_config = yaml.safe_load(f)
        
        print(f"📖 Loaded live trading config from: {live_config_path}")
        
        # Modify configuration for paper trading
        paper_config = live_config.copy()
        
        # Paper trading specific modifications
        paper_config['portfolio']['initial_capital'] = 4000.0  # Same as live
        paper_config['monitoring']['enabled'] = True
        paper_config['cost_controls']['enabled'] = True
        
        # Add paper trading specific settings
        paper_config['paper_trading'] = {
            'enabled': True,
            'simulation_mode': True,
            'real_time_prices': True,
            'commission_free': True,
            'risk_free': True
        }
        
        # Write paper trading configuration
        with open(paper_config_path, 'w') as f:
            yaml.dump(paper_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Paper trading config created: {paper_config_path}")
        
        # Display key settings
        print("\n📊 Key Settings Copied:")
        print(f"  💰 Initial Capital: ${paper_config['portfolio']['initial_capital']:,.2f}")
        print(f"  📈 Max Daily Trades: {paper_config['portfolio']['max_daily_trades']}")
        print(f"  🎯 Max Position Size: {paper_config['dynamic_sizing']['max_position_size']:.1%}")
        print(f"  📉 Max Drawdown Limit: {paper_config['monitoring']['performance_targets']['max_drawdown_limit']:.1%}")
        print(f"  🎯 Annual Return Target: {paper_config['monitoring']['performance_targets']['annual_return_target']:.1%}")
        
        # Display active strategies
        print("\n🎯 Active Strategies:")
        for strategy_name, strategy_config in paper_config['strategies'].items():
            if strategy_config.get('enabled', False):
                print(f"  ✅ {strategy_name}: {strategy_config.get('win_rate', 0):.1%} win rate")
        
        print(f"\n🔄 Configuration copied successfully!")
        if backup_path:
            print(f"📋 Original config backed up to: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying configuration: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Live Trading to Paper Trading Settings Copy")
    print("=" * 50)
    
    if copy_live_to_paper_settings():
        print("\n✅ Success! Paper trading now uses live trading settings")
        print("\n🔧 Next Steps:")
        print("  1. Run: make paper-trading-restart")
        print("  2. Run: make paper-trading-status")
        print("  3. Run: make paper-trading-dashboard")
    else:
        print("\n❌ Failed to copy settings")
        sys.exit(1)

if __name__ == "__main__":
    main()




















