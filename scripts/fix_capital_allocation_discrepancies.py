#!/usr/bin/env python3
"""
Fix Capital Allocation Discrepancies
Updates all strategies to use the same capital allocation as the backtest
"""

import logging
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CapitalAllocationFixer:
    """Fix capital allocation discrepancies across all strategies"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.strategies_dir = self.base_dir / "src" / "strategies"
        
    def fix_all_strategies(self):
        """Fix capital allocation in all strategy files"""
        logger.info("🔧 Fixing capital allocation discrepancies...")
        
        # Files to fix
        strategy_files = [
            "enhanced_elliott_wave_strategies.py",
            "simplified_calendar_spread_strategy.py", 
            "service_based_elliott_wave_strategy.py",
            "simplified_volatility_strategy.py",
            "simplified_enhanced_multi_strategy.py",
            "enhanced_options_multi_strategy.py"
        ]
        
        for file_name in strategy_files:
            file_path = self.strategies_dir / file_name
            if file_path.exists():
                self.fix_strategy_file(file_path)
            else:
                logger.warning(f"⚠️ File not found: {file_path}")
                
        logger.info("✅ Capital allocation fixes completed")
    
    def fix_strategy_file(self, file_path: Path):
        """Fix capital allocation in a specific strategy file"""
        logger.info(f"🔧 Fixing {file_path.name}...")
        
        content = file_path.read_text()
        
        # Fix hardcoded capital allocation
        old_patterns = [
            (r'capital_allocation = 1000\.0.*?# \$1000 per strategy.*?', 
             'capital_allocation = 4000.0 * 0.95  # $3800 available (5% cash reserve)'),
            (r'risk_percentage = min\(0\.003, confidence \* 0\.006\).*?# 0\.3% max risk.*?',
             'risk_percentage = min(0.20, confidence * 0.20)  # 20% max position size'),
            (r'risk_percentage = min\(0\.005, confidence \* 0\.01\).*?# 0\.5% max risk.*?',
             'risk_percentage = min(0.20, confidence * 0.20)  # 20% max position size'),
            (r'max_shares = int\(capital_allocation \* 0\.03 / current_price\).*?# 3% of capital max',
             'max_shares = int(capital_allocation * 0.20 / current_price)  # 20% of capital max'),
            (r'max_shares = int\(capital_allocation \* 0\.05 / current_price\).*?# 5% of capital max',
             'max_shares = int(capital_allocation * 0.20 / current_price)  # 20% of capital max')
        ]
        
        for old_pattern, new_text in old_patterns:
            content = re.sub(old_pattern, new_text, content, flags=re.MULTILINE | re.DOTALL)
        
        # Update comments
        content = content.replace(
            "# Use paper trading capital allocation: 3% max position size, 0.3% risk per trade",
            "# Use dynamic capital allocation from backtest (5% cash reserve, 20% max position)"
        )
        content = content.replace(
            "# Use paper trading capital allocation: 5% max position size, 0.5% risk per trade", 
            "# Use dynamic capital allocation from backtest (5% cash reserve, 20% max position)"
        )
        
        file_path.write_text(content)
        logger.info(f"✅ Fixed {file_path.name}")

async def main():
    fixer = CapitalAllocationFixer()
    fixer.fix_all_strategies()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())




