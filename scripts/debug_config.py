#!/usr/bin/env python3
"""
Debug script to test config loading
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.utils.config import get_config
    from src.utils.trading_config import get_symbols, get_options_symbols
    
    print("Testing config loading...")
    
    # Test direct import
    print(f"Direct get_symbols(): {get_symbols()}")
    print(f"Direct get_options_symbols(): {get_options_symbols()}")
    
    # Test config object
    config = get_config()
    print(f"Config.symbols: {config.symbols}")
    print(f"Config.options_symbols: {config.options_symbols}")
    
    if config.symbols is None:
        print("❌ Config.symbols is None!")
    else:
        print(f"✅ Config.symbols has {len(config.symbols)} symbols")
    
    if config.options_symbols is None:
        print("❌ Config.options_symbols is None!")
    else:
        print(f"✅ Config.options_symbols has {len(config.options_symbols)} symbols")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 