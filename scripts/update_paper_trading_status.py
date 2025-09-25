#!/usr/bin/env python3
"""
Update Paper Trading Status in PORT_MAP.md
Automatically updates the paper trading status section with current data
"""

import requests
import json
import re
from datetime import datetime
import os

def get_paper_trading_status():
    """Get current paper trading status from API"""
    try:
        response = requests.get("http://localhost:11115/api/paper-trading/status", timeout=5)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            return None
    except Exception as e:
        print(f"Error fetching paper trading status: {e}")
        return None

def update_port_map_with_paper_trading_status():
    """Update PORT_MAP.md with current paper trading status"""
    
    # Get current status
    status = get_paper_trading_status()
    if not status:
        print("Could not fetch paper trading status")
        return
    
    # Read current PORT_MAP.md
    port_map_path = "/Users/abby/code/trading/PORT_MAP.md"
    with open(port_map_path, 'r') as f:
        content = f.read()
    
    # Update timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S EEST")
    content = re.sub(
        r'\*\*Last Updated\*\*: .*',
        f'**Last Updated**: {current_time}',
        content
    )
    
    # Update paper trading status section
    status_text = "✅ **RUNNING**" if status["is_running"] else "❌ **STOPPED**"
    
    # Format portfolio value
    portfolio_value = f"${status['portfolio_value']:,.2f}"
    
    # Format start time
    start_time = status.get("start_time", "N/A")
    if start_time and start_time != "N/A":
        try:
            # Parse and format the timestamp
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            start_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    
    # Format last trade
    last_trade = status.get("last_trade")
    if last_trade:
        last_trade_text = f"{last_trade.get('action', 'Unknown')} {last_trade.get('symbol', '')} at ${last_trade.get('price', 0):.2f}"
    else:
        last_trade_text = "None"
    
    # Create new paper trading status section
    paper_trading_section = f"""## 📈 Paper Trading Status

| Metric | Value | Details |
|--------|-------|---------|
| **Status** | {status_text} | {'Active since ' + start_time if status["is_running"] and start_time != "N/A" else 'Not running'} |
| **Portfolio Value** | **{portfolio_value}** | {'Current value' if status["total_trades"] > 0 else 'Initial capital'} |
| **Total Trades** | **{status['total_trades']}** | {'Completed trades' if status['total_trades'] > 0 else 'No completed trades yet'} |
| **Total P&L** | **${status['total_pnl']:,.2f}** | {'Realized gains/losses' if status['total_pnl'] != 0 else 'No realized gains/losses'} |
| **Active Strategies** | **{len(status.get('active_strategies', []))}** | {', '.join(status.get('active_strategies', []))} |
| **Trading Symbols** | **3** | AMD, PYPL, INTC |
| **Trading Interval** | **5 minutes** | 300 seconds between cycles |
| **Max Risk Per Trade** | **5%** | $100 max risk per trade |
| **Max Position Size** | **10%** | $200 max position size |
| **Last Trade** | **{last_trade_text}** | {'Most recent trade' if last_trade else 'No trades yet'} |

### 🎯 Strategy Configuration
- **Primary**: Iron Condor (Options strategy for range-bound markets)
- **Secondary**: Regime Switching (Adaptive strategy based on market conditions)  
- **Backup**: Bollinger Bands (Mean reversion strategy)"""
    
    # Replace the paper trading status section
    pattern = r'## 📈 Paper Trading Status.*?(?=## 📋|$)'
    content = re.sub(pattern, paper_trading_section, content, flags=re.DOTALL)
    
    # Write updated content back to file
    with open(port_map_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated PORT_MAP.md with current paper trading status")
    print(f"📊 Status: {status_text}")
    print(f"💰 Portfolio: {portfolio_value}")
    print(f"📈 Trades: {status['total_trades']}")

if __name__ == "__main__":
    update_port_map_with_paper_trading_status()


