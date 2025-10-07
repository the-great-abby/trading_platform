#!/usr/bin/env python3
"""
Capital Allocation Monitor
==========================
Monitors that capital allocation follows the requested split:
- 20% cash reserve
- 30% stocks
- 50% options (5% day trading, 45% swing trading)
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

class CapitalAllocationMonitor:
    """Monitor capital allocation compliance"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        
        # Target allocation (as requested)
        self.target_allocation = {
            'cash_reserve_pct': 0.20,     # 20% cash reserve
            'stock_allocation_pct': 0.30,  # 30% stocks
            'options_allocation_pct': 0.50, # 50% options
            'options_day_trading_pct': 0.05,  # 5% total for day trading
            'options_swing_trading_pct': 0.45  # 45% total for swing trading
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
        """Validate allocation against targets"""
        logger.info(f"🔍 Validating {config_type} trading allocation...")
        
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
        """Run allocation monitoring"""
        logger.info("🚀 Starting Capital Allocation Monitoring")
        logger.info("=" * 60)
        logger.info("🎯 TARGET ALLOCATION:")
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
        logger.info("📊 ALLOCATION VALIDATION RESULTS:")
        logger.info(f"   • Paper Trading: {'✅ COMPLIANT' if paper_ok else '❌ NON-COMPLIANT'}")
        logger.info(f"   • Live Trading: {'✅ COMPLIANT' if live_ok else '❌ NON-COMPLIANT'}")
        logger.info("=" * 60)
        
        if paper_ok and live_ok:
            logger.info("🎉 ALL ALLOCATIONS COMPLIANT WITH REQUESTED SPLIT!")
        else:
            logger.error("❌ Some allocations are non-compliant. Check logs above.")
        
        return paper_ok and live_ok

async def main():
    """Main monitoring function"""
    monitor = CapitalAllocationMonitor()
    success = monitor.run_monitoring()
    
    if success:
        logger.info("✅ All capital allocations are compliant!")
    else:
        logger.error("❌ Some capital allocations need fixing.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
