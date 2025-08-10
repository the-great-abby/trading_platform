#!/usr/bin/env python3
"""
Test Dynamic Strategy Discovery
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.strategies.strategy_registry import get_strategy_registry, discover_strategies


def test_dynamic_strategy_discovery():
    """Test the dynamic strategy discovery system"""
    
    print("🔍 Testing Dynamic Strategy Discovery")
    print("=" * 50)
    
    # Get the registry
    registry = get_strategy_registry()
    
    # Discover strategies
    print("📊 Discovering strategies...")
    strategies = discover_strategies()
    
    print(f"\n✅ Total strategies discovered: {len(strategies)}")
    
    # Get categories
    categories = registry.get_all_categories()
    
    print("\n📊 Strategy Categories:")
    for category, strategy_list in categories.items():
        if strategy_list:
            print(f"  • {category.upper()}: {len(strategy_list)} strategies")
            for strategy in sorted(strategy_list):
                print(f"    - {strategy}")
    
    # Test strategy validation
    print("\n🔍 Validating strategies...")
    validation_results = registry.validate_strategies()
    
    print(f"\n✅ Valid strategies: {len(validation_results['valid'])}")
    print(f"❌ Invalid strategies: {len(validation_results['invalid'])}")
    
    if validation_results['valid']:
        print("\n✅ Valid Strategies:")
        for strategy in sorted(validation_results['valid']):
            print(f"  • {strategy}")
    
    if validation_results['invalid']:
        print("\n❌ Invalid Strategies:")
        for strategy in sorted(validation_results['invalid']):
            print(f"  • {strategy}")
    
    if validation_results['errors']:
        print("\n⚠️ Validation Errors:")
        for error in validation_results['errors']:
            print(f"  • {error}")
    
    # Test strategy info
    print("\n📋 Strategy Information:")
    for strategy_name in sorted(strategies.keys()):
        info = registry.get_strategy_info(strategy_name)
        if info:
            print(f"  • {strategy_name}: {info['category']} category")
    
    # Test strategy creation
    print("\n🧪 Testing strategy instantiation...")
    successful_creations = 0
    failed_creations = 0
    
    for strategy_name in strategies.keys():
        try:
            instance = registry.create_strategy_instance(strategy_name)
            if instance:
                successful_creations += 1
                print(f"  ✅ {strategy_name}: Created successfully")
            else:
                failed_creations += 1
                print(f"  ❌ {strategy_name}: Failed to create")
        except Exception as e:
            failed_creations += 1
            print(f"  ❌ {strategy_name}: Error - {e}")
    
    print(f"\n📊 Creation Results:")
    print(f"  ✅ Successful: {successful_creations}")
    print(f"  ❌ Failed: {failed_creations}")
    
    # Print formatted list
    print("\n" + registry.list_strategies())
    
    return {
        'total_strategies': len(strategies),
        'categories': categories,
        'valid_strategies': len(validation_results['valid']),
        'invalid_strategies': len(validation_results['invalid']),
        'successful_creations': successful_creations,
        'failed_creations': failed_creations
    }


def test_new_strategies():
    """Test the new strategies specifically"""
    
    print("\n🎯 Testing New Strategies")
    print("=" * 30)
    
    registry = get_strategy_registry()
    
    new_strategies = [
        'RiskFirstStrategy',
        'MarketRegimeAdaptiveStrategy', 
        'MultiTimeframeStrategy'
    ]
    
    for strategy_name in new_strategies:
        print(f"\n🔍 Testing {strategy_name}:")
        
        # Check if strategy exists
        strategy_class = registry.get_strategy(strategy_name)
        if strategy_class:
            print(f"  ✅ Strategy class found")
            
            # Try to create instance
            try:
                instance = registry.create_strategy_instance(strategy_name)
                if instance:
                    print(f"  ✅ Instance created successfully")
                    print(f"  📋 Name: {instance.name}")
                    print(f"  📋 Category: {registry._get_strategy_category(strategy_name)}")
                else:
                    print(f"  ❌ Failed to create instance")
            except Exception as e:
                print(f"  ❌ Error creating instance: {e}")
        else:
            print(f"  ❌ Strategy class not found")


if __name__ == "__main__":
    print("🚀 Dynamic Strategy Discovery Test")
    print("=" * 50)
    
    # Test general discovery
    results = test_dynamic_strategy_discovery()
    
    # Test new strategies
    test_new_strategies()
    
    print(f"\n🎉 Test completed!")
    print(f"📊 Summary:")
    print(f"  • Total strategies: {results['total_strategies']}")
    print(f"  • Valid strategies: {results['valid_strategies']}")
    print(f"  • Successful creations: {results['successful_creations']}")
    
    # Check if new strategies are available
    registry = get_strategy_registry()
    new_strategies = registry.get_strategies_by_category('new')
    
    if new_strategies:
        print(f"  • New strategies available: {len(new_strategies)}")
        for strategy in new_strategies:
            print(f"    - {strategy}")
    else:
        print("  ⚠️ No new strategies found in 'new' category") 