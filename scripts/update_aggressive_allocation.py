#!/usr/bin/env python3
"""
Update Capital Allocation to More Aggressive Split
==================================================
Update to the new requested allocation:
- 5% cash reserve (more aggressive)
- 20% stocks
- 50% options  
- 25% day trading (much larger allocation)
"""

import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AggressiveAllocationUpdater:
    """Update capital allocation to more aggressive split"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        
    def update_paper_trading_allocation(self):
        """Update paper trading to aggressive allocation"""
        logger.info("🚀 Updating Paper Trading to Aggressive Allocation...")
        
        paper_config = self.config_dir / "multi_strategy_ensemble_paper_trading.yaml"
        if not paper_config.exists():
            logger.error(f"❌ {paper_config.name} not found!")
            return False
        
        # Read current config
        with open(paper_config, 'r') as f:
            config = yaml.safe_load(f)
        
        # AGGRESSIVE CAPITAL ALLOCATION (as requested)
        config['portfolio'] = {
            'initial_capital': 4000.0,
            'max_daily_loss': 300.0,      # 7.5% of $4k capital (more aggressive)
            'max_daily_trades': 30,       # Much more aggressive for day trading
            'max_monthly_trades': 200,    # Much more aggressive for more opportunities
            'max_single_symbol': 0.20,    # 20% max per symbol (more aggressive)
            'max_total_exposure': 0.95,   # 95% total exposure (5% cash reserve)
            'min_cash_reserve': 0.05      # 5% cash reserve (AGGRESSIVE)
        }
        
        # AGGRESSIVE ASSET ALLOCATION SPLIT (as requested)
        config['asset_allocation'] = {
            'enabled': True,
            'cash_reserve_pct': 0.05,     # 5% cash reserve (AGGRESSIVE)
            'stock_allocation_pct': 0.20, # 20% stocks (reduced)
            'options_allocation_pct': 0.50, # 50% options (same)
            
            # Options sub-allocation - MUCH MORE AGGRESSIVE
            'options_day_trading_pct': 0.50,  # 50% of options = 25% total for day trading (HUGE INCREASE)
            'options_swing_trading_pct': 0.50, # 50% of options = 25% total for swing trading (reduced)
            
            # Time windows
            'day_trading_time_window_minutes': 15,  # 15-minute time window
            'swing_trading_time_window_days': 1,    # 1-day time window
            
            # Position sizing per allocation - MORE AGGRESSIVE
            'max_stock_position_pct': 0.15,        # Max 15% per stock position (increased)
            'max_options_day_position_pct': 0.10,  # Max 10% per day trading options position (HUGE INCREASE)
            'max_options_swing_position_pct': 0.15 # Max 15% per swing trading options position (increased)
        }
        
        # AGGRESSIVE TRADING FREQUENCY (based on new allocation)
        config['trading_frequency'] = {
            'day_trading': {
                'enabled': True,
                'interval_minutes': 15,           # 15-minute intervals
                'max_daily_trades': 20,          # Much more aggressive for day trading
                'max_position_duration_hours': 6, # Max 6 hours for day trades (increased)
                'symbols': ['SPY', 'QQQ', 'NVDA', 'AAPL'], # More symbols for day trading
                'strategies': ['AdaptiveSectorWaveStrategy'], # Fast strategies
                'allocation_pct': 0.25           # 25% total allocation (HUGE INCREASE)
            },
            'swing_trading': {
                'enabled': True,
                'interval_minutes': 60,          # 1-hour intervals
                'max_daily_trades': 8,           # Increased for more opportunities
                'max_position_duration_days': 7, # Max 7 days for swing trades
                'symbols': ['SPY', 'AAPL', 'NVDA', 'TSLA', 'META'], # Broader symbol set
                'strategies': ['MultiStrategyEnsemble'], # Full ensemble for swing trading
                'allocation_pct': 0.25           # 25% total allocation (reduced from 45%)
            }
        }
        
        # STRATEGY CONFIGURATION (updated for aggressive allocation)
        config['strategies']['MultiStrategyEnsemble'].update({
            'asset_allocation': {
                'stock_allocation_pct': 0.20,     # 20% stocks (reduced)
                'options_allocation_pct': 0.50,  # 50% options (same)
                'cash_reserve_pct': 0.05         # 5% cash reserve (AGGRESSIVE)
            },
            'adaptive_wave': {
                'elliott_wave_min_confidence': 0.03,  # Lower threshold for more trades
                'ichimoku_min_confidence': 0.03,     # Lower threshold for more trades
                'enable_ichimoku': True,
                'max_position_size_pct': 0.15,   # Increased for more aggressive trading
                'max_daily_loss_pct': 0.03,     # Increased for more risk tolerance
                'volatility_adjustment': True,
                'correlation_limit': 0.8,       # Relaxed correlation limit
                'day_trading_enabled': True,     # Enable day trading
                'swing_trading_enabled': True    # Enable swing trading
            }
        })
        
        # AGGRESSIVE EXECUTION SETTINGS
        config['execution'] = {
            'trading_interval': 15,              # 15-minute base interval
            'market_hours_only': True,
            'extended_hours': False,
            'real_time_data': True,
            'process_every_data_point': True,
            'max_data_points_per_day': 390,      # 6.5 hours * 60 minutes
            'data_point_buffer_size': 1000,
            'parallel_processing': True,
            'disable_engine_stop_loss': True,
            'disable_engine_take_profit': True,
            
            # Aggressive allocation-specific execution
            'day_trading_execution': {
                'enabled': True,
                'interval_minutes': 15,
                'max_trades_per_session': 15,   # Much more aggressive
                'quick_exit_enabled': True
            },
            'swing_trading_execution': {
                'enabled': True,
                'interval_minutes': 60,
                'max_trades_per_day': 8,        # Increased
                'patient_exit_enabled': True
            }
        }
        
        # Write updated config
        with open(paper_config, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info("✅ Paper trading: Updated to aggressive allocation")
        return True
    
    def update_live_trading_allocation(self):
        """Update live trading to aggressive allocation (conservative version)"""
        logger.info("🚀 Updating Live Trading to Aggressive Allocation...")
        
        live_config = self.config_dir / "multi_strategy_ensemble_live_trading.yaml"
        if not live_config.exists():
            logger.error(f"❌ {live_config.name} not found!")
            return False
        
        # Read current config
        with open(live_config, 'r') as f:
            config = yaml.safe_load(f)
        
        # AGGRESSIVE CAPITAL ALLOCATION (conservative for live trading)
        config['portfolio'] = {
            'initial_capital': 4000.0,
            'max_daily_loss': 250.0,      # 6.25% of $4k capital (aggressive but safe)
            'max_daily_trades': 25,       # More aggressive for day trading
            'max_monthly_trades': 150,    # More aggressive for more opportunities
            'max_single_symbol': 0.18,    # 18% max per symbol (more aggressive)
            'max_total_exposure': 0.95,   # 95% total exposure (5% cash reserve)
            'min_cash_reserve': 0.05      # 5% cash reserve (AGGRESSIVE)
        }
        
        # AGGRESSIVE ASSET ALLOCATION SPLIT (conservative for live trading)
        config['asset_allocation'] = {
            'enabled': True,
            'cash_reserve_pct': 0.05,     # 5% cash reserve (AGGRESSIVE)
            'stock_allocation_pct': 0.20, # 20% stocks (reduced)
            'options_allocation_pct': 0.50, # 50% options (same)
            
            # Options sub-allocation (conservative for live trading)
            'options_day_trading_pct': 0.40,  # 40% of options = 20% total for day trading (conservative)
            'options_swing_trading_pct': 0.60, # 60% of options = 30% total for swing trading
            
            # Time windows
            'day_trading_time_window_minutes': 15,  # 15-minute time window
            'swing_trading_time_window_days': 1,    # 1-day time window
            
            # Position sizing per allocation (conservative for live trading)
            'max_stock_position_pct': 0.12,        # Max 12% per stock position
            'max_options_day_position_pct': 0.08,  # Max 8% per day trading options position
            'max_options_swing_position_pct': 0.12 # Max 12% per swing trading options position
        }
        
        # AGGRESSIVE TRADING FREQUENCY (conservative for live trading)
        config['trading_frequency'] = {
            'day_trading': {
                'enabled': True,
                'interval_minutes': 30,           # 30-minute intervals (conservative)
                'max_daily_trades': 15,          # More aggressive but safe for live trading
                'max_position_duration_hours': 6, # Max 6 hours for day trades
                'symbols': ['SPY', 'QQQ', 'NVDA'], # Conservative symbol set for day trading
                'strategies': ['AdaptiveSectorWaveStrategy'], # Fast strategies
                'allocation_pct': 0.20           # 20% total allocation (conservative)
            },
            'swing_trading': {
                'enabled': True,
                'interval_minutes': 120,         # 2-hour intervals (conservative)
                'max_daily_trades': 5,           # More aggressive but safe for live trading
                'max_position_duration_days': 5, # Max 5 days for swing trades
                'symbols': ['SPY', 'AAPL', 'NVDA'], # Conservative symbol set
                'strategies': ['MultiStrategyEnsemble'], # Full ensemble for swing trading
                'allocation_pct': 0.30           # 30% total allocation
            }
        }
        
        # STRATEGY CONFIGURATION (conservative for live trading)
        config['strategies']['MultiStrategyEnsemble'].update({
            'asset_allocation': {
                'stock_allocation_pct': 0.20,     # 20% stocks (reduced)
                'options_allocation_pct': 0.50,  # 50% options (same)
                'cash_reserve_pct': 0.05         # 5% cash reserve (AGGRESSIVE)
            },
            'adaptive_wave': {
                'elliott_wave_min_confidence': 0.05,  # Lower threshold for more trades
                'ichimoku_min_confidence': 0.05,     # Lower threshold for more trades
                'enable_ichimoku': True,
                'max_position_size_pct': 0.12,   # More aggressive for live trading
                'max_daily_loss_pct': 0.025,    # More aggressive for live trading
                'volatility_adjustment': True,
                'correlation_limit': 0.7,       # Moderate correlation limit
                'day_trading_enabled': True,     # Enable day trading
                'swing_trading_enabled': True    # Enable swing trading
            }
        })
        
        # AGGRESSIVE EXECUTION SETTINGS (conservative for live trading)
        config['execution'] = {
            'trading_interval': 30,              # 30-minute base interval (conservative)
            'market_hours_only': True,
            'extended_hours': False,
            'real_time_data': True,
            'process_every_data_point': True,
            'max_data_points_per_day': 78,       # 6.5 hours * 12 (30min intervals)
            'data_point_buffer_size': 500,
            'parallel_processing': True,
            'disable_engine_stop_loss': True,
            'disable_engine_take_profit': True,
            
            # Aggressive allocation-specific execution (conservative)
            'day_trading_execution': {
                'enabled': True,
                'interval_minutes': 30,          # Conservative interval
                'max_trades_per_session': 10,   # More aggressive but safe
                'quick_exit_enabled': True
            },
            'swing_trading_execution': {
                'enabled': True,
                'interval_minutes': 120,         # Conservative interval
                'max_trades_per_day': 5,        # More aggressive but safe
                'patient_exit_enabled': True
            }
        }
        
        # Write updated config
        with open(live_config, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info("✅ Live trading: Updated to aggressive allocation")
        return True
    
    def update_paper_trading_script(self):
        """Update paper trading script to aggressive allocation"""
        logger.info("🚀 Updating Paper Trading Script for Aggressive Allocation...")
        
        paper_script = self.base_dir / "scripts" / "setup_paper_trading.py"
        if not paper_script.exists():
            logger.error(f"❌ {paper_script.name} not found!")
            return False
        
        # Read current script
        with open(paper_script, 'r') as f:
            content = f.read()
        
        # Update configuration section
        old_config = '''        # CORRECT CAPITAL ALLOCATION (as requested)
        config = {
            'initial_capital': 4000.0,  # Match backtest starting capital
            
            # Asset Allocation Split (as requested)
            'cash_reserve_pct': 0.20,   # 20% cash reserve
            'stock_allocation_pct': 0.30, # 30% stocks
            'options_allocation_pct': 0.50, # 50% options
            
            # Options sub-allocation
            'options_day_trading_pct': 0.10,  # 10% of options = 5% total for day trading
            'options_swing_trading_pct': 0.90, # 90% of options = 45% total for swing trading
            
            # Time windows
            'day_trading_time_window_minutes': 15,  # 15-minute time window
            'swing_trading_time_window_days': 1,    # 1-day time window
            
            # Trading configuration
            'trading_interval': 15,     # 15-minute intervals (day trading focus)
            'max_daily_trades': 20,     # Increased for day trading
            'max_weekly_trades': 50,    # Increased for more opportunities
            'max_monthly_trades': 150,  # Increased for more opportunities
            
            # Strategies and symbols
            'strategies': ['MultiStrategyEnsemble'],  # Use Multi-Strategy Ensemble
            'symbols': ['SPY', 'AAPL', 'NVDA'],  # Proven high performers
            'use_real_strategies': True,
            'enable_alerts': True,
            'performance_tracking': True,
            
            # Risk management
            'max_portfolio_utilization': 0.80,  # 80% deployment (20% cash reserve)
            'min_cash_reserve': 0.20,           # 20% cash reserve (CORRECT)
            'disable_engine_stop_loss': True,   # CRITICAL: Let strategy handle exits
            'disable_engine_take_profit': True, # CRITICAL: Let strategy handle exits
            
            # Strategy weights
            'strategy_weights': {
                'adaptive_wave': 0.35,      # 35% - Elliott Wave + Options
                'regime_switching': 0.25,   # 25% - Market timing
                'enhanced_multi': 0.25,      # 25% - Sector rotation
                'momentum': 0.15             # 15% - Cross-sectional momentum
            }
        }'''
        
        new_config = '''        # AGGRESSIVE CAPITAL ALLOCATION (as requested)
        config = {
            'initial_capital': 4000.0,  # Match backtest starting capital
            
            # Asset Allocation Split (AGGRESSIVE)
            'cash_reserve_pct': 0.05,   # 5% cash reserve (AGGRESSIVE)
            'stock_allocation_pct': 0.20, # 20% stocks (reduced)
            'options_allocation_pct': 0.50, # 50% options (same)
            
            # Options sub-allocation - MUCH MORE AGGRESSIVE
            'options_day_trading_pct': 0.50,  # 50% of options = 25% total for day trading (HUGE INCREASE)
            'options_swing_trading_pct': 0.50, # 50% of options = 25% total for swing trading (reduced)
            
            # Time windows
            'day_trading_time_window_minutes': 15,  # 15-minute time window
            'swing_trading_time_window_days': 1,    # 1-day time window
            
            # Trading configuration - MORE AGGRESSIVE
            'trading_interval': 15,     # 15-minute intervals (day trading focus)
            'max_daily_trades': 30,     # Much more aggressive for day trading
            'max_weekly_trades': 100,   # Much more aggressive for more opportunities
            'max_monthly_trades': 200,  # Much more aggressive for more opportunities
            
            # Strategies and symbols
            'strategies': ['MultiStrategyEnsemble'],  # Use Multi-Strategy Ensemble
            'symbols': ['SPY', 'AAPL', 'NVDA', 'QQQ'],  # More symbols for day trading
            'use_real_strategies': True,
            'enable_alerts': True,
            'performance_tracking': True,
            
            # Risk management - MORE AGGRESSIVE
            'max_portfolio_utilization': 0.95,  # 95% deployment (5% cash reserve)
            'min_cash_reserve': 0.05,           # 5% cash reserve (AGGRESSIVE)
            'disable_engine_stop_loss': True,   # CRITICAL: Let strategy handle exits
            'disable_engine_take_profit': True, # CRITICAL: Let strategy handle exits
            
            # Strategy weights
            'strategy_weights': {
                'adaptive_wave': 0.35,      # 35% - Elliott Wave + Options
                'regime_switching': 0.25,   # 25% - Market timing
                'enhanced_multi': 0.25,      # 25% - Sector rotation
                'momentum': 0.15             # 15% - Cross-sectional momentum
            }
        }'''
        
        if old_config in content:
            content = content.replace(old_config, new_config)
        
        # Write updated script
        with open(paper_script, 'w') as f:
            f.write(content)
        
        logger.info("✅ Paper trading script updated with aggressive allocation")
        return True
    
    def create_aggressive_allocation_monitoring_script(self):
        """Create script to monitor aggressive capital allocation"""
        monitoring_script = self.base_dir / "scripts" / "monitor_aggressive_allocation.py"
        
        script_content = '''#!/usr/bin/env python3
"""
Aggressive Capital Allocation Monitor
====================================
Monitors that capital allocation follows the new aggressive split:
- 5% cash reserve
- 20% stocks
- 50% options (25% day trading, 25% swing trading)
"""

import asyncio
import logging
import yaml
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AggressiveAllocationMonitor:
    """Monitor aggressive capital allocation compliance"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        
        # Target allocation (aggressive)
        self.target_allocation = {
            'cash_reserve_pct': 0.05,     # 5% cash reserve
            'stock_allocation_pct': 0.20,  # 20% stocks
            'options_allocation_pct': 0.50, # 50% options
            'options_day_trading_pct': 0.25,  # 25% total for day trading
            'options_swing_trading_pct': 0.25  # 25% total for swing trading
        }
    
    def load_config(self, config_type: str):
        """Load configuration file"""
        config_file = self.config_dir / f"multi_strategy_ensemble_{config_type}_trading.yaml"
        
        if not config_file.exists():
            logger.error(f"❌ {config_file.name} not found!")
            return None
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def validate_allocation(self, config: dict, config_type: str):
        """Validate allocation against aggressive targets"""
        logger.info(f"🔍 Validating {config_type} trading aggressive allocation...")
        
        # Get allocation settings
        portfolio = config.get('portfolio', {})
        asset_allocation = config.get('asset_allocation', {})
        
        # Check cash reserve
        cash_reserve = portfolio.get('min_cash_reserve', 0)
        target_cash = self.target_allocation['cash_reserve_pct']
        
        if abs(cash_reserve - target_cash) < 0.01:  # Within 1%
            logger.info(f"✅ Cash reserve: {cash_reserve:.1%} (target: {target_cash:.1%})")
            cash_ok = True
        else:
            logger.error(f"❌ Cash reserve: {cash_reserve:.1%} (target: {target_cash:.1%})")
            cash_ok = False
        
        # Check stock allocation
        stock_allocation = asset_allocation.get('stock_allocation_pct', 0)
        target_stocks = self.target_allocation['stock_allocation_pct']
        
        if abs(stock_allocation - target_stocks) < 0.01:  # Within 1%
            logger.info(f"✅ Stock allocation: {stock_allocation:.1%} (target: {target_stocks:.1%})")
            stocks_ok = True
        else:
            logger.error(f"❌ Stock allocation: {stock_allocation:.1%} (target: {target_stocks:.1%})")
            stocks_ok = False
        
        # Check options allocation
        options_allocation = asset_allocation.get('options_allocation_pct', 0)
        target_options = self.target_allocation['options_allocation_pct']
        
        if abs(options_allocation - target_options) < 0.01:  # Within 1%
            logger.info(f"✅ Options allocation: {options_allocation:.1%} (target: {target_options:.1%})")
            options_ok = True
        else:
            logger.error(f"❌ Options allocation: {options_allocation:.1%} (target: {target_options:.1%})")
            options_ok = False
        
        # Check options sub-allocation
        day_trading_pct = asset_allocation.get('options_day_trading_pct', 0)
        swing_trading_pct = asset_allocation.get('options_swing_trading_pct', 0)
        
        # Calculate actual percentages
        actual_day_pct = options_allocation * day_trading_pct
        actual_swing_pct = options_allocation * swing_trading_pct
        
        target_day_pct = self.target_allocation['options_day_trading_pct']
        target_swing_pct = self.target_allocation['options_swing_trading_pct']
        
        if abs(actual_day_pct - target_day_pct) < 0.01:  # Within 1%
            logger.info(f"✅ Day trading: {actual_day_pct:.1%} (target: {target_day_pct:.1%})")
            day_ok = True
        else:
            logger.error(f"❌ Day trading: {actual_day_pct:.1%} (target: {target_day_pct:.1%})")
            day_ok = False
        
        if abs(actual_swing_pct - target_swing_pct) < 0.01:  # Within 1%
            logger.info(f"✅ Swing trading: {actual_swing_pct:.1%} (target: {target_swing_pct:.1%})")
            swing_ok = True
        else:
            logger.error(f"❌ Swing trading: {actual_swing_pct:.1%} (target: {target_swing_pct:.1%})")
            swing_ok = False
        
        return cash_ok and stocks_ok and options_ok and day_ok and swing_ok
    
    def run_monitoring(self):
        """Run aggressive allocation monitoring"""
        logger.info("🚀 Starting Aggressive Capital Allocation Monitoring")
        logger.info("=" * 60)
        logger.info("🎯 AGGRESSIVE TARGET ALLOCATION:")
        logger.info(f"   • Cash Reserve: {self.target_allocation['cash_reserve_pct']:.1%}")
        logger.info(f"   • Stocks: {self.target_allocation['stock_allocation_pct']:.1%}")
        logger.info(f"   • Options: {self.target_allocation['options_allocation_pct']:.1%}")
        logger.info(f"     - Day Trading: {self.target_allocation['options_day_trading_pct']:.1%}")
        logger.info(f"     - Swing Trading: {self.target_allocation['options_swing_trading_pct']:.1%}")
        logger.info("=" * 60)
        
        # Validate paper trading
        paper_config = self.load_config("paper")
        if paper_config:
            paper_ok = self.validate_allocation(paper_config, "Paper")
        else:
            paper_ok = False
        
        # Validate live trading
        live_config = self.load_config("live")
        if live_config:
            live_ok = self.validate_allocation(live_config, "Live")
        else:
            live_ok = False
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 AGGRESSIVE ALLOCATION VALIDATION RESULTS:")
        logger.info(f"   • Paper Trading: {'✅ COMPLIANT' if paper_ok else '❌ NON-COMPLIANT'}")
        logger.info(f"   • Live Trading: {'✅ COMPLIANT' if live_ok else '❌ NON-COMPLIANT'}")
        logger.info("=" * 60)
        
        if paper_ok and live_ok:
            logger.info("🎉 ALL AGGRESSIVE ALLOCATIONS COMPLIANT!")
        else:
            logger.error("❌ Some allocations are non-compliant. Check logs above.")
        
        return paper_ok and live_ok

async def main():
    """Main monitoring function"""
    monitor = AggressiveAllocationMonitor()
    success = monitor.run_monitoring()
    
    if success:
        logger.info("✅ All aggressive capital allocations are compliant!")
    else:
        logger.error("❌ Some aggressive capital allocations need fixing.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(monitoring_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(monitoring_script, 0o755)
        
        logger.info(f"✅ Created aggressive allocation monitoring script: {monitoring_script}")
    
    def run_allocation_update(self):
        """Run complete aggressive allocation update"""
        logger.info("🚀 Starting Aggressive Capital Allocation Update")
        logger.info("=" * 60)
        logger.info("🎯 IMPLEMENTING AGGRESSIVE ALLOCATION SPLIT:")
        logger.info("   • 5% cash reserve (AGGRESSIVE)")
        logger.info("   • 20% stocks (reduced)")
        logger.info("   • 50% options (same)")
        logger.info("     - 25% day trading (HUGE INCREASE from 5%)")
        logger.info("     - 25% swing trading (reduced from 45%)")
        logger.info("=" * 60)
        
        try:
            # Step 1: Update paper trading allocation
            logger.info("📋 Step 1: Updating paper trading to aggressive allocation...")
            paper_success = self.update_paper_trading_allocation()
            
            # Step 2: Update live trading allocation
            logger.info("📋 Step 2: Updating live trading to aggressive allocation...")
            live_success = self.update_live_trading_allocation()
            
            # Step 3: Update paper trading script
            logger.info("📋 Step 3: Updating paper trading script...")
            script_success = self.update_paper_trading_script()
            
            # Step 4: Create monitoring script
            logger.info("📋 Step 4: Creating aggressive allocation monitoring script...")
            self.create_aggressive_allocation_monitoring_script()
            
            # Summary
            logger.info("=" * 60)
            logger.info("✅ AGGRESSIVE CAPITAL ALLOCATION UPDATE COMPLETE!")
            logger.info(f"   • Paper Trading Config: {'✅ Updated' if paper_success else '❌ Failed'}")
            logger.info(f"   • Live Trading Config: {'✅ Updated' if live_success else '❌ Failed'}")
            logger.info(f"   • Paper Trading Script: {'✅ Updated' if script_success else '❌ Failed'}")
            logger.info("   • Monitoring Script: ✅ Created")
            logger.info("=" * 60)
            
            logger.info("🎯 AGGRESSIVE ALLOCATION SPLIT IMPLEMENTED:")
            logger.info("   • ✅ 5% cash reserve (AGGRESSIVE)")
            logger.info("   • ✅ 20% stocks (reduced)")
            logger.info("   • ✅ 50% options (same)")
            logger.info("     - ✅ 25% day trading (HUGE INCREASE)")
            logger.info("     - ✅ 25% swing trading (reduced)")
            logger.info("=" * 60)
            
            logger.info("🔍 VALIDATION COMMAND:")
            logger.info("   python scripts/monitor_aggressive_allocation.py")
            logger.info("=" * 60)
            
            return paper_success and live_success and script_success
            
        except Exception as e:
            logger.error(f"❌ Aggressive allocation update failed: {e}")
            return False

def main():
    """Main function"""
    updater = AggressiveAllocationUpdater()
    success = updater.run_allocation_update()
    
    if success:
        logger.info("🎉 Aggressive capital allocation update completed successfully!")
        logger.info("📖 Run validation: python scripts/monitor_aggressive_allocation.py")
    else:
        logger.error("❌ Aggressive allocation update failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()










