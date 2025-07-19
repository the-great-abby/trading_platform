#!/usr/bin/env python3
"""
Demo script for the Centralized Trading API Gateway
Shows how external systems can interact with all trading functionality
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.trading_api_client import (
    TradingAPIClient, 
    TradingOrder, 
    OrderSide, 
    OrderType,
    MarketDataRequest,
    TimeInterval,
    BacktestRequest
)

class TradingAPIDemo:
    """Demo class showing various API usage patterns"""
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = "demo-key"):
        self.api_url = api_url
        self.api_key = api_key
        self.client = None
    
    async def __aenter__(self):
        self.client = TradingAPIClient(
            base_url=self.api_url,
            api_key=self.api_key
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def demo_health_check(self):
        """Demo: Check system health"""
        print("\n🔍 Checking System Health...")
        try:
            health = await self.client.health_check()
            print(f"✅ System Status: {health['status']}")
            print(f"📊 Version: {health['version']}")
            print(f"🕐 Timestamp: {health['timestamp']}")
            
            print("\n📋 Service Status:")
            for service, status in health['services'].items():
                status_emoji = "✅" if status == "healthy" else "❌" if status == "error" else "⚠️"
                print(f"  {status_emoji} {service}: {status}")
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    async def demo_system_info(self):
        """Demo: Get system information"""
        print("\n📋 Getting System Information...")
        try:
            info = await self.client.get_system_status()
            print(f"🚀 Service: {info['data']['service']}")
            print(f"📊 Version: {info['data']['version']}")
            print(f"🟢 Status: {info['data']['status']}")
            
            print("\n🔗 Available Endpoints:")
            for name, endpoint in info['data']['endpoints'].items():
                print(f"  📍 {name}: {endpoint}")
                
        except Exception as e:
            print(f"❌ Failed to get system info: {e}")
    
    async def demo_market_data(self):
        """Demo: Get market data"""
        print("\n📈 Getting Market Data...")
        try:
            # Get quotes for popular stocks
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
            
            request = MarketDataRequest(
                symbols=symbols,
                interval=TimeInterval.DAY_1,
                period="1m"
            )
            
            quotes = await self.client.get_market_quotes(request)
            
            if quotes['success']:
                print("✅ Market data retrieved successfully")
                data = quotes['data']
                
                if 'quotes' in data:
                    print("\n📊 Current Quotes:")
                    for symbol, quote in data['quotes'].items():
                        if isinstance(quote, dict) and 'price' in quote:
                            price = quote['price']
                            change = quote.get('change', 0)
                            change_pct = quote.get('change_percent', 0)
                            
                            change_emoji = "📈" if change >= 0 else "📉"
                            print(f"  {change_emoji} {symbol}: ${price:.2f} ({change:+.2f}, {change_pct:+.2f}%)")
                else:
                    print(f"📊 Raw data: {json.dumps(data, indent=2)}")
            else:
                print(f"❌ Failed to get market data: {quotes.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Market data demo failed: {e}")
    
    async def demo_strategy_recommendations(self):
        """Demo: Get strategy recommendations"""
        print("\n🎯 Getting Strategy Recommendations...")
        try:
            # Get recommendations for Apple
            recommendations = await self.client.get_strategy_recommendations(
                symbol="AAPL",
                include_ai_analysis=True,
                include_news_sentiment=True
            )
            
            if recommendations['success']:
                print("✅ Recommendations retrieved successfully")
                data = recommendations['data']
                
                print(f"\n📊 Symbol: {data.get('symbol', 'N/A')}")
                print(f"🎯 Overall Recommendation: {data.get('overall_recommendation', 'N/A')}")
                print(f"📈 Confidence: {data.get('confidence', 'N/A')}")
                
                if 'strategies' in data:
                    print("\n🔍 Strategy Analysis:")
                    for strategy in data['strategies']:
                        name = strategy.get('name', 'Unknown')
                        signal = strategy.get('signal', 'N/A')
                        confidence = strategy.get('confidence', 'N/A')
                        print(f"  📊 {name}: {signal} (confidence: {confidence})")
                
                if 'ai_analysis' in data:
                    ai = data['ai_analysis']
                    print(f"\n🤖 AI Analysis: {ai.get('summary', 'N/A')}")
                    print(f"🧠 Reasoning: {ai.get('reasoning', 'N/A')}")
                
                if 'risk_assessment' in data:
                    risk = data['risk_assessment']
                    print(f"\n⚠️ Risk Level: {risk.get('risk_level', 'N/A')}")
                    print(f"💰 Position Size: {risk.get('recommended_position_size', 'N/A')}")
                    
            else:
                print(f"❌ Failed to get recommendations: {recommendations.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Strategy recommendations demo failed: {e}")
    
    async def demo_portfolio(self):
        """Demo: Get portfolio information"""
        print("\n💼 Getting Portfolio Information...")
        try:
            portfolio = await self.client.get_portfolio(
                include_positions=True,
                include_history=False
            )
            
            if portfolio['success']:
                print("✅ Portfolio retrieved successfully")
                data = portfolio['data']
                
                print(f"\n💰 Account Balance: ${data.get('balance', {}).get('cash', 0):,.2f}")
                print(f"📈 Total Value: ${data.get('total_value', 0):,.2f}")
                print(f"📊 P&L: ${data.get('unrealized_pnl', 0):,.2f}")
                
                if 'positions' in data:
                    positions = data['positions']
                    if positions:
                        print("\n📋 Current Positions:")
                        for position in positions:
                            symbol = position.get('symbol', 'N/A')
                            quantity = position.get('quantity', 0)
                            avg_price = position.get('avg_price', 0)
                            current_price = position.get('current_price', 0)
                            pnl = position.get('unrealized_pnl', 0)
                            
                            pnl_emoji = "📈" if pnl >= 0 else "📉"
                            print(f"  {pnl_emoji} {symbol}: {quantity} shares @ ${avg_price:.2f} (P&L: ${pnl:,.2f})")
                    else:
                        print("📋 No current positions")
                        
            else:
                print(f"❌ Failed to get portfolio: {portfolio.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Portfolio demo failed: {e}")
    
    async def demo_backtest(self):
        """Demo: Run a backtest"""
        print("\n🧪 Running Backtest...")
        try:
            # Run a simple RSI strategy backtest
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            request = BacktestRequest(
                strategy="rsi_strategy",
                symbols=["AAPL"],
                start_date=start_date,
                end_date=end_date,
                initial_capital=100000,
                commission=0.001
            )
            
            backtest = await self.client.run_backtest(request)
            
            if backtest['success']:
                print("✅ Backtest started successfully")
                data = backtest['data']
                
                print(f"\n📊 Backtest ID: {data.get('backtest_id', 'N/A')}")
                print(f"📈 Strategy: {data.get('strategy', 'N/A')}")
                print(f"📅 Period: {data.get('start_date', 'N/A')} to {data.get('end_date', 'N/A')}")
                print(f"💰 Initial Capital: ${data.get('initial_capital', 0):,.2f}")
                
                # Get results after a short delay
                print("\n⏳ Waiting for backtest to complete...")
                await asyncio.sleep(2)
                
                results = await self.client.get_backtest_results()
                if results['success'] and results['data']:
                    latest_run = results['data'][-1] if isinstance(results['data'], list) else results['data']
                    
                    print(f"\n📊 Final Results:")
                    print(f"💰 Final Value: ${latest_run.get('final_value', 0):,.2f}")
                    print(f"📈 Total Return: {latest_run.get('total_return', 0):.2%}")
                    print(f"📊 Sharpe Ratio: {latest_run.get('sharpe_ratio', 0):.3f}")
                    print(f"📉 Max Drawdown: {latest_run.get('max_drawdown', 0):.2%}")
                    print(f"🔄 Total Trades: {latest_run.get('total_trades', 0)}")
                    
            else:
                print(f"❌ Failed to run backtest: {backtest.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Backtest demo failed: {e}")
    
    async def demo_create_order(self):
        """Demo: Create a trading order (paper trading)"""
        print("\n📝 Creating Trading Order...")
        try:
            # Create a paper trading order
            order = TradingOrder(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=10,
                order_type=OrderType.MARKET,
                strategy="demo_strategy"
            )
            
            result = await self.client.create_order(order)
            
            if result['success']:
                print("✅ Order created successfully")
                data = result['data']
                
                print(f"\n📋 Order Details:")
                print(f"🆔 Order ID: {data.get('order_id', 'N/A')}")
                print(f"📊 Symbol: {data.get('symbol', 'N/A')}")
                print(f"📈 Side: {data.get('side', 'N/A')}")
                print(f"📊 Quantity: {data.get('quantity', 'N/A')}")
                print(f"💰 Price: ${data.get('price', 'N/A')}")
                print(f"📊 Status: {data.get('status', 'N/A')}")
                
            else:
                print(f"❌ Failed to create order: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Order creation demo failed: {e}")
    
    async def demo_analytics(self):
        """Demo: Get performance analytics"""
        print("\n📊 Getting Performance Analytics...")
        try:
            analytics = await self.client.get_performance_analytics()
            
            if analytics['success']:
                print("✅ Analytics retrieved successfully")
                data = analytics['data']
                
                print(f"\n📈 Performance Metrics:")
                print(f"💰 Total P&L: ${data.get('total_pnl', 0):,.2f}")
                print(f"📊 Win Rate: {data.get('win_rate', 0):.2%}")
                print(f"📈 Average Win: ${data.get('avg_win', 0):,.2f}")
                print(f"📉 Average Loss: ${data.get('avg_loss', 0):,.2f}")
                print(f"📊 Profit Factor: {data.get('profit_factor', 0):.2f}")
                print(f"📈 Sharpe Ratio: {data.get('sharpe_ratio', 0):.3f}")
                
            else:
                print(f"❌ Failed to get analytics: {analytics.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Analytics demo failed: {e}")
    
    async def demo_websocket(self):
        """Demo: WebSocket real-time data"""
        print("\n🔌 WebSocket Real-time Data Demo...")
        print("⚠️ Note: This is a simulated demo. Real WebSocket would connect to /ws/market-data")
        
        # Simulate real-time data
        symbols = ["AAPL", "MSFT", "GOOGL"]
        for i in range(5):
            data = {
                "type": "market_data",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    symbol: {
                        "price": 150.0 + i * 0.5,
                        "change": 0.5,
                        "volume": 1000000 + i * 10000
                    } for symbol in symbols
                }
            }
            print(f"📡 Real-time data {i+1}: {json.dumps(data, indent=2)}")
            await asyncio.sleep(1)
    
    async def run_full_demo(self):
        """Run the complete API demo"""
        print("🚀 Space Trading Station - Centralized API Demo")
        print("=" * 60)
        
        try:
            # Run all demos
            await self.demo_health_check()
            await self.demo_system_info()
            await self.demo_market_data()
            await self.demo_strategy_recommendations()
            await self.demo_portfolio()
            await self.demo_backtest()
            await self.demo_create_order()
            await self.demo_analytics()
            await self.demo_websocket()
            
            print("\n✅ Demo completed successfully!")
            print("\n🎯 Key Benefits of Centralized API:")
            print("  📍 Single entry point for all trading operations")
            print("  🔒 Unified authentication and security")
            print("  📊 Comprehensive monitoring and metrics")
            print("  🔄 Real-time data via WebSocket")
            print("  📚 Auto-generated documentation")
            print("  🚀 Scalable and maintainable architecture")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")

async def main():
    """Main demo function"""
    # Configuration
    api_url = os.getenv("API_URL", "http://localhost:8000")
    api_key = os.getenv("API_KEY", "demo-key")
    
    print(f"🔗 Connecting to API at: {api_url}")
    print(f"🔑 Using API key: {api_key}")
    
    async with TradingAPIDemo(api_url, api_key) as demo:
        await demo.run_full_demo()

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main()) 