#!/usr/bin/env python3
"""
Ichimoku Strategy Demo
======================

This demo shows how the Ichimoku Cloud strategy provides comprehensive
entry and exit signals with specific price levels.

The Ichimoku strategy is excellent for:
- Trend direction identification
- Entry/exit price levels
- Support/resistance zones
- Multiple confirmation signals
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List
from datetime import datetime

class IchimokuStrategyDemo:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_ichimoku_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Get stock recommendation using Ichimoku strategy"""
        
        payload = {
            "symbol": symbol,
            "include_ai_analysis": True,
            "include_news_sentiment": True,
            "include_risk_assessment": True,
            "strategies": ["ichimoku_strategy"]
        }
        
        try:
            response = await self.client.post(
                f"{self.api_base_url}/recommendations/stock",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def print_ichimoku_analysis(self, recommendation: Dict[str, Any]):
        """Print detailed Ichimoku analysis"""
        if not recommendation:
            print("❌ No recommendation available")
            return
        
        print("\n" + "="*80)
        print(f"🌤️  ICHIMOKU CLOUD ANALYSIS: {recommendation['symbol']}")
        print("="*80)
        
        # Overall recommendation
        action = recommendation['overall_recommendation']
        confidence = recommendation['confidence']
        current_price = recommendation['current_price']
        
        print(f"\n🎯 OVERALL RECOMMENDATION:")
        print(f"   Action: {action}")
        print(f"   Confidence: {confidence:.1%}")
        print(f"   Current Price: ${current_price:.2f}")
        
        # Price targets
        if recommendation.get('target_price'):
            print(f"   Target Price: ${recommendation['target_price']:.2f}")
        if recommendation.get('stop_loss'):
            print(f"   Stop Loss: ${recommendation['stop_loss']:.2f}")
        if recommendation.get('take_profit'):
            print(f"   Take Profit: ${recommendation['take_profit']:.2f}")
        
        # Ichimoku-specific analysis
        if recommendation.get('strategies_analysis'):
            ichimoku_analysis = None
            for strategy in recommendation['strategies_analysis']:
                if strategy['strategy_name'] == 'ichimoku_strategy':
                    ichimoku_analysis = strategy
                    break
            
            if ichimoku_analysis and ichimoku_analysis.get('metadata'):
                metadata = ichimoku_analysis['metadata']
                
                print(f"\n🌤️  ICHIMOKU CLOUD LEVELS:")
                if metadata.get('tenkan'):
                    print(f"   Tenkan-sen: ${metadata['tenkan']:.2f}")
                if metadata.get('kijun'):
                    print(f"   Kijun-sen: ${metadata['kijun']:.2f}")
                if metadata.get('senkou_a'):
                    print(f"   Senkou Span A: ${metadata['senkou_a']:.2f}")
                if metadata.get('senkou_b'):
                    print(f"   Senkou Span B: ${metadata['senkou_b']:.2f}")
                if metadata.get('chikou'):
                    print(f"   Chikou Span: ${metadata['chikou']:.2f}")
                
                # Cloud analysis
                cloud_analysis = metadata.get('cloud_analysis', {})
                if cloud_analysis:
                    print(f"\n☁️  CLOUD ANALYSIS:")
                    print(f"   Above Cloud: {cloud_analysis.get('above_cloud', False)}")
                    print(f"   Below Cloud: {cloud_analysis.get('below_cloud', False)}")
                    print(f"   Inside Cloud: {cloud_analysis.get('inside_cloud', False)}")
                    print(f"   Cloud Bullish: {cloud_analysis.get('cloud_bullish', False)}")
                    print(f"   Cloud Thickness: {cloud_analysis.get('cloud_thickness', 0):.2%}")
                    if cloud_analysis.get('cloud_top'):
                        print(f"   Cloud Top: ${cloud_analysis['cloud_top']:.2f}")
                    if cloud_analysis.get('cloud_bottom'):
                        print(f"   Cloud Bottom: ${cloud_analysis['cloud_bottom']:.2f}")
                
                # Crossover analysis
                crossover_analysis = metadata.get('crossover_analysis', {})
                if crossover_analysis:
                    print(f"\n🔄 CROSSOVER ANALYSIS:")
                    print(f"   Bullish Crossover: {crossover_analysis.get('bullish_crossover', False)}")
                    print(f"   Bearish Crossover: {crossover_analysis.get('bearish_crossover', False)}")
                    print(f"   Tenkan Above Kijun: {crossover_analysis.get('tenkan_above_kijun', False)}")
                    print(f"   Crossover Distance: {crossover_analysis.get('crossover_distance', 0):.2%}")
                
                # Chikou analysis
                chikou_analysis = metadata.get('chikou_analysis', {})
                if chikou_analysis:
                    print(f"\n📈 CHIKOU SPAN ANALYSIS:")
                    print(f"   Chikou Bullish: {chikou_analysis.get('chikou_bullish', False)}")
                    print(f"   Chikou Bearish: {chikou_analysis.get('chikou_bearish', False)}")
                    print(f"   Chikou Strength: {chikou_analysis.get('chikou_strength', 0):.2%}")
                
                # Support/Resistance
                support_resistance = metadata.get('support_resistance', {})
                if support_resistance:
                    print(f"\n🎯 SUPPORT & RESISTANCE:")
                    if support_resistance.get('nearest_support'):
                        print(f"   Nearest Support: ${support_resistance['nearest_support']:.2f}")
                    if support_resistance.get('nearest_resistance'):
                        print(f"   Nearest Resistance: ${support_resistance['nearest_resistance']:.2f}")
        
        # Risk assessment
        print(f"\n⚠️  RISK ASSESSMENT:")
        print(f"   Risk Level: {recommendation['risk_level']}")
        print(f"   Position Size: {recommendation['position_size_recommendation']}")
        
        # Reasoning
        print(f"\n💡 REASONING:")
        print(f"   {recommendation['reasoning']}")
        
        print(f"\n⏰ Generated: {recommendation['timestamp']}")
        print("="*80)
    
    async def demo_single_stock(self, symbol: str):
        """Demo for a single stock"""
        print(f"\n🚀 Getting Ichimoku analysis for {symbol}...")
        
        recommendation = await self.get_ichimoku_recommendation(symbol)
        self.print_ichimoku_analysis(recommendation)
    
    async def demo_multiple_stocks(self, symbols: List[str]):
        """Demo for multiple stocks"""
        print(f"\n🚀 Getting Ichimoku analysis for multiple stocks...")
        
        for symbol in symbols:
            print(f"\n📊 Analyzing {symbol} with Ichimoku...")
            recommendation = await self.get_ichimoku_recommendation(symbol)
            self.print_ichimoku_analysis(recommendation)
            await asyncio.sleep(1)  # Small delay between requests
    
    async def demo_entry_exit_levels(self, symbol: str):
        """Demo focusing on entry/exit levels"""
        print(f"\n🎯 Analyzing entry/exit levels for {symbol}...")
        
        recommendation = await self.get_ichimoku_recommendation(symbol)
        if recommendation and recommendation.get('strategies_analysis'):
            ichimoku_analysis = None
            for strategy in recommendation['strategies_analysis']:
                if strategy['strategy_name'] == 'ichimoku_strategy':
                    ichimoku_analysis = strategy
                    break
            
            if ichimoku_analysis and ichimoku_analysis.get('metadata'):
                metadata = ichimoku_analysis['metadata']
                current_price = recommendation['current_price']
                
                print(f"\n💰 ENTRY/EXIT PRICE ANALYSIS:")
                print(f"   Current Price: ${current_price:.2f}")
                
                # Entry levels
                if metadata.get('tenkan'):
                    print(f"   Entry Level (Tenkan): ${metadata['tenkan']:.2f}")
                if metadata.get('kijun'):
                    print(f"   Entry Level (Kijun): ${metadata['kijun']:.2f}")
                
                # Support/Resistance levels
                support_resistance = metadata.get('support_resistance', {})
                if support_resistance.get('nearest_support'):
                    print(f"   Stop Loss Level: ${support_resistance['nearest_support']:.2f}")
                if support_resistance.get('nearest_resistance'):
                    print(f"   Take Profit Level: ${support_resistance['nearest_resistance']:.2f}")
                
                # Cloud levels
                cloud_analysis = metadata.get('cloud_analysis', {})
                if cloud_analysis.get('cloud_top'):
                    print(f"   Cloud Top: ${cloud_analysis['cloud_top']:.2f}")
                if cloud_analysis.get('cloud_bottom'):
                    print(f"   Cloud Bottom: ${cloud_analysis['cloud_bottom']:.2f}")
    
    async def demo_trend_analysis(self, symbol: str):
        """Demo focusing on trend analysis"""
        print(f"\n📈 Analyzing trend for {symbol}...")
        
        recommendation = await self.get_ichimoku_recommendation(symbol)
        if recommendation and recommendation.get('strategies_analysis'):
            ichimoku_analysis = None
            for strategy in recommendation['strategies_analysis']:
                if strategy['strategy_name'] == 'ichimoku_strategy':
                    ichimoku_analysis = strategy
                    break
            
            if ichimoku_analysis and ichimoku_analysis.get('metadata'):
                metadata = ichimoku_analysis['metadata']
                
                print(f"\n🌤️  TREND ANALYSIS:")
                
                # Cloud trend
                cloud_analysis = metadata.get('cloud_analysis', {})
                if cloud_analysis.get('above_cloud'):
                    print(f"   Trend: BULLISH (Price above cloud)")
                elif cloud_analysis.get('below_cloud'):
                    print(f"   Trend: BEARISH (Price below cloud)")
                elif cloud_analysis.get('inside_cloud'):
                    print(f"   Trend: NEUTRAL (Price inside cloud)")
                
                if cloud_analysis.get('cloud_bullish'):
                    print(f"   Cloud Color: BULLISH (Senkou A > Senkou B)")
                else:
                    print(f"   Cloud Color: BEARISH (Senkou A < Senkou B)")
                
                # Crossover trend
                crossover_analysis = metadata.get('crossover_analysis', {})
                if crossover_analysis.get('bullish_crossover'):
                    print(f"   Crossover: BULLISH (Tenkan crossed above Kijun)")
                elif crossover_analysis.get('bearish_crossover'):
                    print(f"   Crossover: BEARISH (Tenkan crossed below Kijun)")
                elif crossover_analysis.get('tenkan_above_kijun'):
                    print(f"   Crossover: BULLISH (Tenkan above Kijun)")
                else:
                    print(f"   Crossover: BEARISH (Tenkan below Kijun)")
                
                # Chikou trend
                chikou_analysis = metadata.get('chikou_analysis', {})
                if chikou_analysis.get('chikou_bullish'):
                    print(f"   Chikou: BULLISH (Chikou above price)")
                elif chikou_analysis.get('chikou_bearish'):
                    print(f"   Chikou: BEARISH (Chikou below price)")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Main demo function"""
    print("🌤️  Ichimoku Strategy Demo")
    print("="*50)
    
    # Initialize demo
    demo = IchimokuStrategyDemo()
    
    try:
        # Demo 1: Single stock analysis
        await demo.demo_single_stock("AAPL")
        
        # Demo 2: Multiple stocks
        await demo.demo_multiple_stocks(["GOOGL", "MSFT", "TSLA"])
        
        # Demo 3: Entry/exit levels
        await demo.demo_entry_exit_levels("AAPL")
        
        # Demo 4: Trend analysis
        await demo.demo_trend_analysis("GOOGL")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        await demo.close()

if __name__ == "__main__":
    asyncio.run(main()) 