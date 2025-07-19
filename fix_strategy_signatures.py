#!/usr/bin/env python3
"""
Fix Strategy Signatures Script

This script fixes all strategy generate_signal method signatures to match
the base class signature: generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None)
"""

import os
import re
from pathlib import Path

def fix_strategy_signature(file_path: str):
    """Fix the generate_signal signature in a strategy file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match the old signature
    old_pattern = r'async def generate_signal\(self, symbol: str, data: pd\.DataFrame\) -> Optional\[TradeSignal\]:'
    new_signature = 'async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:'
    
    # Replace the signature
    new_content = re.sub(old_pattern, new_signature, content)
    
    # Also fix any calls to generate_signal that don't pass historical_date
    # This is a more complex pattern, so we'll handle it case by case
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed signature in {file_path}")
        return True
    return False

def fix_options_strategies():
    """Fix options strategies that have wrong parameter names"""
    options_files = [
        'src/strategies/options/volatility_strategy.py',
        'src/strategies/options/earnings_strategy.py',
        'src/strategies/options/cash_secured_put_strategy.py',
        'src/strategies/options/covered_call_strategy.py',
        'src/strategies/options/calendar_spread_strategy.py',
        'src/strategies/options/butterfly_spread_strategy.py',
    ]
    
    for file_path in options_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Fix the signature for options strategies
            old_pattern = r'async def generate_signal\(self, symbol: str, data: pd\.DataFrame, options_data: Optional\[Dict\[str, Any\]\] = None\) -> Optional\[TradeSignal\]:'
            new_signature = 'async def generate_signal(self, symbol: str, data: pd.DataFrame, historical_date: Optional[str] = None) -> Optional[TradeSignal]:'
            
            new_content = re.sub(old_pattern, new_signature, content)
            
            if new_content != content:
                with open(file_path, 'w') as f:
                    f.write(new_content)
                print(f"Fixed options strategy signature in {file_path}")

def main():
    """Main function to fix all strategy signatures"""
    print("🔧 Fixing strategy signatures...")
    
    # Fix options strategies first
    fix_options_strategies()
    
    # Find all strategy files
    strategy_dir = Path('src/strategies')
    strategy_files = []
    
    for pattern in ['**/*.py']:
        strategy_files.extend(strategy_dir.glob(pattern))
    
    fixed_count = 0
    for file_path in strategy_files:
        if file_path.name != '__init__.py' and file_path.name != 'base.py':
            if fix_strategy_signature(str(file_path)):
                fixed_count += 1
    
    print(f"✅ Fixed {fixed_count} strategy signatures")

if __name__ == "__main__":
    main() 