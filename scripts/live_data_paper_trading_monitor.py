#!/usr/bin/env python3
"""
Live Data Paper Trading Monitor
Real-time monitoring of live data options paper trading
"""

import json
import os
import time
from datetime import datetime
import aiohttp
import asyncio
from typing import Dict, Optional

def get_live_prices() -> Dict[str, float]:
    """Get live prices directly from Polygon API"""
    async def fetch_live_price(symbol):
        try:
            api_key = 'PwSQb2yBh2aYqEs0lZIqnTX_nT2b7CHr'
            url = f'https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}'
            params = {'apiKey': api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if 'ticker' in data and data['ticker']:
                        ticker = data['ticker']
                        if 'day' in ticker and 'c' in ticker['day']:
                            return float(ticker['day']['c'])
                        elif 'min' in ticker and 'c' in ticker['min']:
                            return float(ticker['min']['c'])
                    return None
        except Exception as e:
            print(f"Error fetching live price for {symbol}: {e}")
            return None
    
    # Get live prices for all symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'SPY', 'QQQ', 'AMZN', 'META', 'NFLX']
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [fetch_live_price(symbol) for symbol in symbols]
        prices = loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()
        return dict(zip(symbols, prices))
    except Exception as e:
        print(f"Error fetching live prices: {e}")
        return {}

def load_portfolio_status() -> Optional[Dict]:
    """Load current portfolio status from live engine"""
    try:
        if os.path.exists('config/paper_trading_status.json'):
            with open('config/paper_trading_status.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Error loading portfolio status: {e}")
    return None

def display_portfolio_status():
    """Display current portfolio status"""
    status = load_portfolio_status()
    
    if not status:
        print("❌ No portfolio status available")
        print("💡 Make sure the live data paper trading engine is running")
        return
    
    # Calculate additional metrics
    current_value = status.get('current_capital', 0)
    initial_capital = status.get('initial_capital', 0)
    total_pnl = status.get('total_pnl', 0)
    pnl_pct = status.get('pnl_percentage', 0)
    total_trades = status.get('total_trades', 0)
    active_positions = status.get('active_positions', 0)
    allocated_capital = status.get('allocated_capital', 0.0)
    available_capital = status.get('available_capital', 0.0)
    capital_utilization = status.get('capital_utilization', 0.0)
    live_data_enabled = status.get('live_data_enabled', False)
    recent_trades = status.get('recent_trades', [])
    active_positions_detail = status.get('active_positions_detail', [])
    capital_allocation_settings = status.get('capital_allocation_settings', {})
    
    # Display header
    print(f"\n📊 Live Data Paper Trading Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Portfolio summary
    print(f"💰 Initial Capital: ${initial_capital:,.2f}")
    print(f"📈 Current Value: ${current_value:,.2f}")
    print(f"📊 Total P&L: ${total_pnl:,.2f} ({pnl_pct:+.2f}%)")
    print(f"📈 Total Trades: {total_trades}")
    print(f"🔄 Active Positions: {active_positions}")
    print(f"🌐 Live Data: {'✅ Enabled' if live_data_enabled else '❌ Disabled'}")
    
    # Capital Allocation Summary
    print(f"\n🎯 Advanced Capital Allocation:")
    print(f"💰 Allocated Capital: ${allocated_capital:,.2f}")
    print(f"💵 Available Capital: ${available_capital:,.2f}")
    print(f"📊 Capital Utilization: {capital_utilization:.1f}%")
    
    if capital_allocation_settings:
        print(f"⚙️  Settings: Max Util {capital_allocation_settings.get('max_portfolio_utilization', 0)*100:.0f}% | "
              f"Cash Reserve {capital_allocation_settings.get('min_cash_reserve', 0)*100:.0f}% | "
              f"Early Profit {capital_allocation_settings.get('early_profit_target_pct', 0)*100:.0f}%")
    
        # Active positions
        if active_positions_detail:
            print(f"\n🔄 Active Positions ({len(active_positions_detail)}):")
            print("-" * 70)
            for i, pos in enumerate(active_positions_detail, 1):
                elliott_info = ""
                if pos.get('elliott_wave_analysis'):
                    ew = pos['elliott_wave_analysis']
                    elliott_info = f" | 🌊 {ew.get('pattern_type', 'N/A')} ({ew.get('confidence', 0):.2f})"
                
                print(f"  {i}. {pos.get('strategy', 'N/A')} -> {pos.get('options_strategy', 'N/A')} | "
                      f"{pos.get('contracts', 0)} contracts {pos.get('symbol', 'N/A')} | "
                      f"${pos.get('premium', 0):.2f} | P&L: ${pos.get('pnl', 0):+.2f}{elliott_info}")
                
                # Display Elliott Wave analysis details
                if pos.get('elliott_wave_analysis'):
                    ew = pos['elliott_wave_analysis']
                    pattern = ew.get('pattern_type', 'N/A')
                    confidence = ew.get('confidence', 0)
                    signal = ew.get('signal', 'N/A')
                    target_price = ew.get('target_price', 0)
                    print(f"     🌊 Elliott Wave: {pattern} (confidence: {confidence:.2f})")
                    print(f"     📊 Signal: {signal} | Target: ${target_price:.2f}")
                
                # Display exit strategy information
                if pos.get('exit_strategy'):
                    exit_strategy = pos['exit_strategy']
                    max_holding = exit_strategy.get('max_holding_days', 'N/A')
                    profit_target = exit_strategy.get('profit_target_pct', 'N/A')
                    stop_loss = exit_strategy.get('stop_loss_pct', 'N/A')
                    early_profit = exit_strategy.get('early_profit_target_pct', 'N/A')
                    
                    print(f"     🎯 Exit Strategy:")
                    print(f"        • Max Hold: {max_holding} days")
                    print(f"        • Profit Target: {profit_target:.1%}" if isinstance(profit_target, (int, float)) else f"        • Profit Target: {profit_target}")
                    print(f"        • Stop Loss: {stop_loss:.1%}" if isinstance(stop_loss, (int, float)) else f"        • Stop Loss: {stop_loss}")
                    print(f"        • Early Profit: {early_profit:.1%}" if isinstance(early_profit, (int, float)) else f"        • Early Profit: {early_profit}")
                else:
                    # Show default exit strategy if not in position data
                    print(f"     🎯 Exit Strategy:")
                    print(f"        • Max Hold: 30 days")
                    print(f"        • Profit Target: 10.0%")
                    print(f"        • Stop Loss: 5.0%")
                    print(f"        • Early Profit: 8.0%")
    
    # Recent trades
    if recent_trades:
        print(f"\n📋 Recent Trades (Last {len(recent_trades)}):")
        print("-" * 60)
        for trade in recent_trades[-3:]:  # Show last 3 trades
            timestamp = trade.get('timestamp', 'Unknown')
            symbol = trade.get('symbol', 'Unknown')
            strategy = trade.get('strategy', 'Unknown')
            contracts = trade.get('contracts', 0)
            premium = trade.get('premium', 0)
            pnl = trade.get('pnl', 0)
            data_source = trade.get('data_source', 'Unknown')
            status = trade.get('status', 'unknown')
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
            
            status_icon = "🔄" if status == "open" else "✅" if status == "closed" else "❓"
            print(f"  {status_icon} {time_str} | {strategy} {contracts} contracts {symbol} | Premium: ${premium:.2f} | P&L: ${pnl:+.2f} | Source: {data_source}")
    
    # Current LIVE prices (fetched directly from API)
    print(f"\n💹 Current LIVE Prices (Direct from Polygon API):")
    print("-" * 50)
    live_prices = get_live_prices()
    if live_prices:
        for symbol, price in list(live_prices.items())[:5]:  # Show first 5
            if price:
                print(f"  {symbol}: ${price:.2f}")
            else:
                print(f"  {symbol}: Failed to fetch")
    else:
        print("  ❌ Failed to fetch live prices")
    
    print("=" * 80)

def main():
    """Main monitoring loop"""
    print("📊 Live Data Paper Trading Monitor")
    print("Press Ctrl+C to stop monitoring")
    
    try:
        while True:
            display_portfolio_status()
            print(f"\n⏰ Next update in 30 seconds...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    main()
