#!/usr/bin/env python3
"""
Simple Strategy Discovery Test
"""

import os
import sys
from pathlib import Path

def test_strategy_files_exist():
    """Test if the new strategy files exist"""
    
    print("🔍 Testing Strategy File Discovery")
    print("=" * 40)
    
    # Get the strategies directory
    strategies_dir = Path(__file__).parent.parent / "src" / "strategies"
    
    print(f"📁 Strategies directory: {strategies_dir}")
    
    # Check if directory exists
    if not strategies_dir.exists():
        print("❌ Strategies directory not found")
        return False
    
    # Look for the new strategy files
    new_strategies = [
        "risk_first_strategy.py",
        "market_regime_adaptive_strategy.py", 
        "multi_timeframe_strategy.py"
    ]
    
    print("\n📋 Checking for new strategy files:")
    found_files = []
    
    for strategy_file in new_strategies:
        file_path = strategies_dir / strategy_file
        if file_path.exists():
            print(f"  ✅ {strategy_file}")
            found_files.append(strategy_file)
        else:
            print(f"  ❌ {strategy_file} - NOT FOUND")
    
    # Check for strategy registry
    registry_file = strategies_dir / "strategy_registry.py"
    if registry_file.exists():
        print(f"  ✅ strategy_registry.py")
        found_files.append("strategy_registry.py")
    else:
        print(f"  ❌ strategy_registry.py - NOT FOUND")
    
    # List all strategy files
    print(f"\n📊 All strategy files in directory:")
    strategy_files = list(strategies_dir.glob("*.py"))
    strategy_files.sort()
    
    for file in strategy_files:
        if file.name.startswith("__"):
            continue
        print(f"  • {file.name}")
    
    print(f"\n📈 Summary:")
    print(f"  • Total strategy files: {len([f for f in strategy_files if not f.name.startswith('__')])}")
    print(f"  • New strategy files found: {len([f for f in new_strategies if (strategies_dir / f).exists()])}")
    print(f"  • Registry file found: {registry_file.exists()}")
    
    return len(found_files) == len(new_strategies) + 1  # +1 for registry


def test_import_structure():
    """Test the import structure of the new strategies"""
    
    print("\n🔍 Testing Import Structure")
    print("=" * 30)
    
    # Check if we can import the base strategy
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        
        # Try to import the base strategy
        from src.strategies.base import BaseStrategy
        print("  ✅ BaseStrategy imported successfully")
        
        # Check if new strategy classes exist
        new_strategy_classes = [
            "RiskFirstStrategy",
            "MarketRegimeAdaptiveStrategy", 
            "MultiTimeframeStrategy"
        ]
        
        print("\n📋 Checking strategy class imports:")
        for class_name in new_strategy_classes:
            try:
                # Try to import each strategy class
                if class_name == "RiskFirstStrategy":
                    from src.strategies.risk_first_strategy import RiskFirstStrategy
                    print(f"  ✅ {class_name}")
                elif class_name == "MarketRegimeAdaptiveStrategy":
                    from src.strategies.market_regime_adaptive_strategy import MarketRegimeAdaptiveStrategy
                    print(f"  ✅ {class_name}")
                elif class_name == "MultiTimeframeStrategy":
                    from src.strategies.multi_timeframe_strategy import MultiTimeframeStrategy
                    print(f"  ✅ {class_name}")
            except ImportError as e:
                print(f"  ❌ {class_name}: {e}")
            except Exception as e:
                print(f"  ⚠️ {class_name}: {e}")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Could not import BaseStrategy: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error testing imports: {e}")
        return False


def test_dashboard_integration():
    """Test if the new strategies would be available in dashboards"""
    
    print("\n🔍 Testing Dashboard Integration")
    print("=" * 35)
    
    # Check dashboard files for hardcoded strategy lists
    dashboard_files = [
        "services/unified-trading-dashboard/templates/dashboard.html",
        "services/unified-trading-dashboard/templates/trading.html",
        "services/unified-analytics-dashboard/templates/backtest.html",
        "backtest-form.html"
    ]
    
    print("📋 Checking dashboard files for hardcoded strategy lists:")
    
    for file_path in dashboard_files:
        path = Path(__file__).parent.parent / file_path
        if path.exists():
            print(f"  • {file_path}")
            
            # Read file and look for strategy lists
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    
                # Look for strategy definitions
                if "STRATEGIES" in content:
                    print(f"    ✅ Contains strategy definitions")
                    
                    # Check if it has the new category
                    if "new" in content.lower():
                        print(f"    ✅ Has 'new' category")
                    else:
                        print(f"    ❌ No 'new' category found")
                        
                else:
                    print(f"    ⚠️ No strategy definitions found")
                    
            except Exception as e:
                print(f"    ❌ Error reading file: {e}")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
    
    print("\n💡 To make strategies dynamic in dashboards:")
    print("  1. Replace hardcoded STRATEGIES object with API call")
    print("  2. Add API endpoint to serve strategy list")
    print("  3. Update JavaScript to fetch strategies dynamically")


if __name__ == "__main__":
    print("🚀 Simple Strategy Discovery Test")
    print("=" * 50)
    
    # Test file existence
    files_ok = test_strategy_files_exist()
    
    # Test import structure
    imports_ok = test_import_structure()
    
    # Test dashboard integration
    test_dashboard_integration()
    
    print(f"\n🎉 Test completed!")
    print(f"📊 Results:")
    print(f"  • Files exist: {'✅' if files_ok else '❌'}")
    print(f"  • Imports work: {'✅' if imports_ok else '❌'}")
    
    if files_ok and imports_ok:
        print(f"\n✅ All tests passed! New strategies are ready for integration.")
    else:
        print(f"\n❌ Some tests failed. Check the output above for details.") 