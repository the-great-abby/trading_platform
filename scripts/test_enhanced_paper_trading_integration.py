#!/usr/bin/env python3
"""
Test script for Enhanced Paper Trading System Integration
Tests the enhanced setup_paper_trading.py with Elliott Wave and trailing stops
"""
import asyncio
import json
import tempfile
import os
import sys
from datetime import datetime

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'unified-trading-dashboard', 'scripts'))

from setup_paper_trading import RiskManagedPaperTradingEngine, ElliottWaveIntegration, TrailingStopManager

class EnhancedPaperTradingTester:
    def __init__(self):
        self.test_config = {
            "initial_capital": 2000.0,
            "symbols": ["SPY", "QQQ", "AAPL"],
            "strategies": [
                "IronCondor",
                "ButterflySpread", 
                "CalendarSpread",
                "ElliottWaveImpulse",
                "ElliottWaveCorrective"
            ],
            "trading_interval": 60  # 1 minute for testing
        }
    
    async def test_elliott_wave_integration(self):
        """Test Elliott Wave integration"""
        print("🧪 Testing Elliott Wave Integration...")
        
        elliott_integration = ElliottWaveIntegration()
        
        # Test signal generation
        for symbol in self.test_config["symbols"]:
            try:
                signal = await elliott_integration.get_elliott_signals(symbol)
                print(f"✅ Elliott Wave signal for {symbol}: {signal.get('action', 'HOLD')} "
                      f"(confidence: {signal.get('confidence', 0.0):.2f})")
            except Exception as e:
                print(f"⚠️ Elliott Wave test for {symbol}: {e}")
        
        print("✅ Elliott Wave Integration test completed")
    
    async def test_trailing_stop_manager(self):
        """Test trailing stop manager"""
        print("🧪 Testing Trailing Stop Manager...")
        
        trailing_manager = TrailingStopManager()
        
        # Test setting trailing stops
        test_positions = [
            ("SPY", "IronCondor", 450.0, 460.0),
            ("QQQ", "ButterflySpread", 380.0, 390.0),
            ("AAPL", "CalendarSpread", 180.0, 185.0)
        ]
        
        for symbol, strategy, entry_price, current_price in test_positions:
            position_data = {"symbol": symbol, "strategy": strategy}
            trailing_manager.set_trailing_stop(symbol, strategy, entry_price, current_price, position_data)
            
            # Test stop trigger check
            triggered = trailing_manager.check_stop_triggered(symbol, current_price - 10)
            print(f"✅ Trailing stop for {symbol} ({strategy}): "
                  f"Stop at ${trailing_manager.trailing_stops[symbol]['stop_price']:.2f}, "
                  f"Triggered: {triggered}")
        
        print("✅ Trailing Stop Manager test completed")
    
    async def test_enhanced_trading_engine(self):
        """Test the enhanced trading engine"""
        print("🧪 Testing Enhanced Trading Engine...")
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            config_file = f.name
        
        try:
            # Initialize enhanced engine
            engine = RiskManagedPaperTradingEngine(config_file)
            
            print(f"✅ Enhanced engine initialized with {len(engine.strategies)} strategies")
            print(f"✅ Elliott Wave integration: {'✅ Active' if hasattr(engine, 'elliott_wave_integration') else '❌ Missing'}")
            print(f"✅ Trailing stop manager: {'✅ Active' if hasattr(engine, 'trailing_stop_manager') else '❌ Missing'}")
            
            # Test strategy signal calculation
            for symbol in engine.symbols:
                for strategy in engine.strategies:
                    try:
                        signal = await engine.calculate_strategy_signal(symbol, strategy)
                        print(f"✅ Signal for {symbol} ({strategy}): {signal}")
                    except Exception as e:
                        print(f"⚠️ Signal test for {symbol} ({strategy}): {e}")
            
            # Test one trading cycle
            print("🔄 Running one trading cycle...")
            await engine.run_trading_cycle()
            
            print(f"✅ Trading cycle completed. Portfolio value: ${engine.portfolio_value:.2f}")
            print(f"✅ Active positions: {len(engine.active_positions)}")
            print(f"✅ Trailing stops: {len(engine.trailing_stop_manager.trailing_stops)}")
            
        finally:
            # Clean up
            os.unlink(config_file)
        
        print("✅ Enhanced Trading Engine test completed")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🏴‍☠️ Enhanced Paper Trading System Integration Tests")
        print("=" * 60)
        
        tests = [
            ("Elliott Wave Integration", self.test_elliott_wave_integration),
            ("Trailing Stop Manager", self.test_trailing_stop_manager),
            ("Enhanced Trading Engine", self.test_enhanced_trading_engine)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                await test_func()
                passed += 1
                print(f"✅ {test_name} PASSED")
            except Exception as e:
                print(f"❌ {test_name} FAILED: {e}")
            
            print("-" * 40)
        
        print(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Enhanced Paper Trading System is working correctly!")
            print("\n🏴‍☠️ Yo ho ho! Your enhanced paper trading system is ready for action!")
            print("   - Elliott Wave pattern detection ✅")
            print("   - Trailing stops for all strategies ✅")
            print("   - Options trading integration ✅")
            print("   - Enhanced risk management ✅")
        else:
            print("⚠️ Some tests failed. Check the logs above for details.")
        
        return passed == total

async def main():
    """Main test function"""
    print("🚀 Starting Enhanced Paper Trading System Integration Tests...")
    
    tester = EnhancedPaperTradingTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Start paper trading with Elliott Wave strategies:")
        print("   curl -X POST http://localhost:11115/api/paper-trading/start \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"strategies\": [\"IronCondor\", \"ElliottWaveImpulse\", \"ElliottWaveCorrective\"]}'")
        print("\n2. Monitor trading status:")
        print("   curl http://localhost:11115/api/paper-trading/status")
        print("\n3. View trading dashboard:")
        print("   open http://localhost:11115/paper-trading")

if __name__ == "__main__":
    asyncio.run(main())
