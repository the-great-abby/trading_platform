#!/usr/bin/env python3
"""
Simple Symbol Population Script
Uses the existing database connection from unified-analytics-dashboard
"""

import requests
import json
from typing import List, Dict, Any

# Symbol categories and descriptions
SYMBOL_INFO = {
    # Major Tech Stocks
    'AAPL': {'category': 'Technology', 'description': 'Apple Inc.'},
    'MSFT': {'category': 'Technology', 'description': 'Microsoft Corporation'},
    'GOOGL': {'category': 'Technology', 'description': 'Alphabet Inc.'},
    'AMZN': {'category': 'Technology', 'description': 'Amazon.com Inc.'},
    'TSLA': {'category': 'Technology', 'description': 'Tesla Inc.'},
    'NVDA': {'category': 'Technology', 'description': 'NVIDIA Corporation'},
    'META': {'category': 'Technology', 'description': 'Meta Platforms Inc.'},
    'NFLX': {'category': 'Technology', 'description': 'Netflix Inc.'},
    'AMD': {'category': 'Technology', 'description': 'Advanced Micro Devices Inc.'},
    'INTC': {'category': 'Technology', 'description': 'Intel Corporation'},
    
    # Financial Sector
    'JPM': {'category': 'Finance', 'description': 'JPMorgan Chase & Co.'},
    'BAC': {'category': 'Finance', 'description': 'Bank of America Corporation'},
    'WFC': {'category': 'Finance', 'description': 'Wells Fargo & Company'},
    'GS': {'category': 'Finance', 'description': 'Goldman Sachs Group Inc.'},
    'MS': {'category': 'Finance', 'description': 'Morgan Stanley'},
    
    # Healthcare
    'JNJ': {'category': 'Healthcare', 'description': 'Johnson & Johnson'},
    'PFE': {'category': 'Healthcare', 'description': 'Pfizer Inc.'},
    'UNH': {'category': 'Healthcare', 'description': 'UnitedHealth Group Inc.'},
    
    # Consumer Discretionary
    'HD': {'category': 'Consumer Discretionary', 'description': 'Home Depot Inc.'},
    'DIS': {'category': 'Consumer Discretionary', 'description': 'Walt Disney Co.'},
    'V': {'category': 'Finance', 'description': 'Visa Inc.'},
    'MA': {'category': 'Finance', 'description': 'Mastercard Inc.'},
    'PYPL': {'category': 'Technology', 'description': 'PayPal Holdings Inc.'},
    'ADBE': {'category': 'Technology', 'description': 'Adobe Inc.'},
    'CRM': {'category': 'Technology', 'description': 'Salesforce Inc.'},
    'ORCL': {'category': 'Technology', 'description': 'Oracle Corporation'},
    'CSCO': {'category': 'Technology', 'description': 'Cisco Systems Inc.'},
    'QCOM': {'category': 'Technology', 'description': 'Qualcomm Incorporated'},
    'TXN': {'category': 'Technology', 'description': 'Texas Instruments Incorporated'},
    'AVGO': {'category': 'Technology', 'description': 'Broadcom Inc.'},
    
    # ETFs & Indexes
    'SPY': {'category': 'ETF', 'description': 'SPDR S&P 500 ETF Trust'},
    'QQQ': {'category': 'ETF', 'description': 'Invesco QQQ Trust'},
    'VTI': {'category': 'ETF', 'description': 'Vanguard Total Stock Market ETF'},
    'VOO': {'category': 'ETF', 'description': 'Vanguard S&P 500 ETF'},
    'VUG': {'category': 'ETF', 'description': 'Vanguard Growth ETF'},
    'XLK': {'category': 'ETF', 'description': 'Technology Select Sector SPDR Fund'},
    'XLF': {'category': 'ETF', 'description': 'Financial Select Sector SPDR Fund'},
    'XLE': {'category': 'ETF', 'description': 'Energy Select Sector SPDR Fund'},
    'XLV': {'category': 'ETF', 'description': 'Health Care Select Sector SPDR Fund'},
    'XLY': {'category': 'ETF', 'description': 'Consumer Discretionary Select Sector SPDR Fund'},
    'SMCI': {'category': 'Technology', 'description': 'Super Micro Computer Inc.'}
}

# Central symbol list (from trading_config.py)
CENTRAL_SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
    'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
    'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY', 'SMCI'
]

def add_symbol(symbol: str, description: str, category: str, priority: int) -> bool:
    """Add a symbol using the API"""
    try:
        response = requests.post('http://localhost:11114/api/symbols/add', 
                               json={
                                   'name': symbol,
                                   'description': description,
                                   'category': category,
                                   'priority': priority,
                                   'active': True
                               })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Added {symbol} ({category}) - Priority {priority}")
                return True
            else:
                print(f"❌ Failed to add {symbol}: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code} for {symbol}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding {symbol}: {e}")
        return False

def delete_symbol(symbol: str) -> bool:
    """Delete a symbol using the API"""
    try:
        response = requests.delete(f'http://localhost:11114/api/symbols/delete/{symbol}')
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"🗑️  Deleted {symbol}")
                return True
            else:
                print(f"❌ Failed to delete {symbol}: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code} for deleting {symbol}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting {symbol}: {e}")
        return False

def get_current_symbols() -> List[str]:
    """Get current symbols from the database"""
    try:
        response = requests.get('http://localhost:11114/api/symbols/all')
        if response.status_code == 200:
            symbols = response.json()
            if isinstance(symbols, list):
                return [s.get('name', '') for s in symbols if s.get('name')]
        return []
    except Exception as e:
        print(f"❌ Error getting current symbols: {e}")
        return []

def main():
    """Main function"""
    print("🚀 Starting Symbol Database Population...")
    print("=" * 50)
    
    # Check if dashboard is accessible
    try:
        response = requests.get('http://localhost:11114/health', timeout=5)
        if response.status_code != 200:
            print("❌ Dashboard not accessible. Make sure port forwarding is active.")
            return
    except Exception as e:
        print("❌ Cannot connect to dashboard. Make sure port forwarding is active.")
        print(f"   Error: {e}")
        return
    
    print("✅ Dashboard is accessible")
    
    # Get current symbols
    current_symbols = get_current_symbols()
    print(f"📊 Current symbols in database: {len(current_symbols)}")
    
    # Delete all current symbols (except TEST if it exists)
    symbols_to_delete = [s for s in current_symbols if s != 'TEST']
    if symbols_to_delete:
        print(f"🗑️  Deleting {len(symbols_to_delete)} existing symbols...")
        for symbol in symbols_to_delete:
            delete_symbol(symbol)
    
    # Add all symbols from central list
    print(f"\n📝 Adding {len(CENTRAL_SYMBOLS)} symbols from central list...")
    successful_adds = 0
    
    for i, symbol in enumerate(CENTRAL_SYMBOLS):
        symbol_info = SYMBOL_INFO.get(symbol, {
            'category': 'stock',
            'description': f'{symbol} Stock'
        })
        
        priority = i + 1  # Priority 1, 2, 3, etc.
        
        if add_symbol(symbol, symbol_info['description'], symbol_info['category'], priority):
            successful_adds += 1
    
    print(f"\n🎉 Population completed!")
    print(f"   Successfully added: {successful_adds}/{len(CENTRAL_SYMBOLS)} symbols")
    
    if successful_adds == len(CENTRAL_SYMBOLS):
        print("\n💡 The Symbol Management interface now controls the central list!")
        print("   You can now:")
        print("   1. View all symbols in the web interface")
        print("   2. Activate/deactivate symbols")
        print("   3. Change priorities and categories")
        print("   4. Add new custom symbols")
    else:
        print(f"\n⚠️  Some symbols failed to add. Check the errors above.")

if __name__ == "__main__":
    main()

