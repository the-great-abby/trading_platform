#!/usr/bin/env python3
"""
Quick Test of Paper Trading Fix
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scripts.setup_paper_trading import PaperTradingEngine
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_paper_trading():
    """Test the updated paper trading engine"""
    
    config = {
        'initial_capital': 4000.0,
        'max_position_size': 0.05,
        'max_risk_per_trade': 0.01,
        'trading_interval': 3600,  # 1 hour
        'max_daily_trades': 4,
        'max_weekly_trades': 6,
        'max_monthly_trades': 8,
        'strategies': ['RiskFirst', 'MarketRegimeAdaptive'],
        'symbols': ['AAPL', 'MSFT'],
        'enable_alerts': True,
        'performance_tracking': True
    }
    
    print("\n" + "="*80)
    print("PAPER TRADING FIX VERIFICATION")
    print("="*80)
    print()
    
    # Create engine
    engine = PaperTradingEngine(config)
    
    print()
    print("Testing trade limit enforcement...")
    print()
    
    # Simulate 10 trade attempts
    for i in range(10):
        print(f"\nAttempt #{i+1}:")
        await engine.generate_trade()
    
    print()
    print("="*80)
    print("VERIFICATION RESULTS:")
    print("="*80)
    print()
    print(f"✅ Trading interval: {config['trading_interval']} seconds ({config['trading_interval']/60:.0f} minutes)")
    print(f"✅ Daily limit: {config['max_daily_trades']} trades")
    print(f"✅ Weekly limit: {config['max_weekly_trades']} trades")
    print(f"✅ Monthly limit: {config['max_monthly_trades']} trades")
    print()
    print(f"📊 Actual trades executed: {engine.total_trades}")
    print(f"📊 Daily trades: {engine.daily_trades}/{engine.max_daily_trades}")
    print(f"📊 Weekly trades: {engine.weekly_trades}/{engine.max_weekly_trades}")
    print(f"📊 Monthly trades: {engine.monthly_trades}/{engine.max_monthly_trades}")
    print()
    
    if engine.total_trades <= engine.max_daily_trades:
        print("✅ SUCCESS: Trade limits are being enforced!")
    else:
        print("❌ FAILURE: Trade limits not enforced")
    
    print()
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_paper_trading())







