#!/usr/bin/env python3
"""
Economic Calendar & Dynamic Position Sizing Demo
===============================================
Demonstrates how to use economic calendar events and dynamic position sizing
in your trading strategies.
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.economic_calendar import (
    get_economic_calendar, 
    get_market_regime_for_date, 
    is_high_impact_day,
    EconomicEvent
)
from src.utils.dynamic_position_sizing import (
    get_position_sizer,
    calculate_position_size,
    PositionSizingFactors
)
from src.utils.trading_config import get_symbols
from loguru import logger


class EconomicCalendarDemo:
    """Demo for economic calendar and position sizing features"""
    
    def __init__(self):
        self.calendar = get_economic_calendar()
        self.position_sizer = get_position_sizer()
        self.symbols = get_symbols()
        
    def demo_economic_calendar(self):
        """Demonstrate economic calendar features"""
        logger.info("📅 ECONOMIC CALENDAR DEMO")
        logger.info("=" * 50)
        
        # Get current date and some sample dates
        current_date = date.today()
        sample_dates = [
            current_date,
            current_date + timedelta(days=7),
            current_date + timedelta(days=30),
            current_date + timedelta(days=60)
        ]
        
        for target_date in sample_dates:
            logger.info(f"\n📊 Market Analysis for {target_date}")
            logger.info("-" * 40)
            
            # Get market regime
            regime = get_market_regime_for_date(target_date)
            logger.info(f"Market Regime: {regime['regime']}")
            logger.info(f"Volatility Multiplier: {regime['volatility_multiplier']:.2f}")
            logger.info(f"Economic Events: {regime['events']}")
            logger.info(f"Impact Levels: {regime['impact_levels']}")
            
            # Check if high impact day
            is_high_impact = is_high_impact_day(target_date)
            logger.info(f"High Impact Day: {'Yes' if is_high_impact else 'No'}")
            
            # Get specific events for this date
            events = self.calendar.get_events_for_date(target_date)
            if events:
                logger.info(f"Events on {target_date}:")
                for event in events:
                    logger.info(f"  • {event.event_type}: {event.description}")
                    logger.info(f"    Impact: {event.impact_level} | Volatility: {event.volatility_multiplier:.2f}")
            else:
                logger.info(f"No economic events on {target_date}")
        
        # Show earnings season analysis
        logger.info(f"\n📈 EARNINGS SEASON ANALYSIS")
        logger.info("-" * 40)
        
        earnings_events = self.calendar.get_events_by_type("earnings_season")
        logger.info(f"Total earnings season events: {len(earnings_events)}")
        
        for event in earnings_events[:4]:  # Show first 4
            logger.info(f"  • {event.date}: {event.description}")
            logger.info(f"    Volatility Multiplier: {event.volatility_multiplier:.2f}")
        
        # Show FOMC meetings
        logger.info(f"\n🏦 FOMC MEETING ANALYSIS")
        logger.info("-" * 40)
        
        fomc_events = self.calendar.get_events_by_type("fomc_meeting")
        logger.info(f"Total FOMC meetings: {len(fomc_events)}")
        
        for event in fomc_events[:4]:  # Show first 4
            logger.info(f"  • {event.date}: {event.description}")
            logger.info(f"    Time: {event.time} | Impact: {event.impact_level}")
            logger.info(f"    Volatility Multiplier: {event.volatility_multiplier:.2f}")
    
    def demo_dynamic_position_sizing(self):
        """Demonstrate dynamic position sizing features"""
        logger.info("\n💰 DYNAMIC POSITION SIZING DEMO")
        logger.info("=" * 50)
        
        # Sample scenarios
        scenarios = [
            {
                "name": "Conservative Trade",
                "capital": 1000.0,
                "price": 150.0,
                "confidence": 0.6,
                "volatility": 0.02,
                "date": date.today()
            },
            {
                "name": "High Confidence Trade",
                "capital": 1000.0,
                "price": 150.0,
                "confidence": 0.9,
                "volatility": 0.02,
                "date": date.today()
            },
            {
                "name": "High Volatility Trade",
                "capital": 1000.0,
                "price": 150.0,
                "confidence": 0.7,
                "volatility": 0.05,
                "date": date.today()
            },
            {
                "name": "FOMC Week Trade",
                "capital": 1000.0,
                "price": 150.0,
                "confidence": 0.7,
                "volatility": 0.03,
                "date": self._find_fomc_week_date()
            },
            {
                "name": "Earnings Season Trade",
                "capital": 1000.0,
                "price": 150.0,
                "confidence": 0.7,
                "volatility": 0.03,
                "date": self._find_earnings_season_date()
            }
        ]
        
        for scenario in scenarios:
            logger.info(f"\n📊 {scenario['name']}")
            logger.info("-" * 30)
            
            # Calculate position size
            shares, sizing_details = calculate_position_size(
                capital=scenario['capital'],
                price=scenario['price'],
                confidence=scenario['confidence'],
                volatility=scenario['volatility'],
                target_date=scenario['date']
            )
            
            # Display results
            logger.info(f"Capital: ${scenario['capital']:,.2f}")
            logger.info(f"Stock Price: ${scenario['price']:.2f}")
            logger.info(f"Confidence: {scenario['confidence']:.1%}")
            logger.info(f"Volatility: {scenario['volatility']:.1%}")
            logger.info(f"Target Date: {scenario['date']}")
            
            logger.info(f"\nPosition Sizing Results:")
            logger.info(f"  Shares: {shares}")
            logger.info(f"  Position Value: ${sizing_details['final_position_value']:.2f}")
            logger.info(f"  Position %: {sizing_details['position_percentage']:.1f}%")
            
            logger.info(f"\nSizing Adjustments:")
            logger.info(f"  Kelly Size: {sizing_details['kelly_size']:.3f}")
            logger.info(f"  Volatility Adjustment: {sizing_details['volatility_adjustment']:.3f}")
            logger.info(f"  Regime Adjustment: {sizing_details['regime_adjustment']:.3f}")
            logger.info(f"  Calendar Adjustment: {sizing_details['calendar_adjustment']:.3f}")
            logger.info(f"  Portfolio Adjustment: {sizing_details['portfolio_adjustment']:.3f}")
            logger.info(f"  Confidence Adjustment: {sizing_details['confidence_adjustment']:.3f}")
    
    def _find_fomc_week_date(self) -> date:
        """Find a date during FOMC week"""
        fomc_events = self.calendar.get_events_by_type("fomc_meeting")
        if fomc_events:
            # Return 2 days before FOMC meeting
            return fomc_events[0].date - timedelta(days=2)
        return date.today()
    
    def _find_earnings_season_date(self) -> date:
        """Find a date during earnings season"""
        earnings_events = self.calendar.get_events_by_type("earnings_season")
        if earnings_events:
            # Return 5 days after earnings season starts
            return earnings_events[0].date + timedelta(days=5)
        return date.today()
    
    def demo_portfolio_risk_analysis(self):
        """Demonstrate portfolio risk analysis"""
        logger.info("\n🛡️ PORTFOLIO RISK ANALYSIS DEMO")
        logger.info("=" * 50)
        
        # Sample portfolio positions
        positions = [
            {"symbol": "AAPL", "value": 150.0, "sector": "technology", "max_loss": 12.0},
            {"symbol": "MSFT", "value": 120.0, "sector": "technology", "max_loss": 9.6},
            {"symbol": "JPM", "value": 80.0, "sector": "financial", "max_loss": 6.4},
            {"symbol": "JNJ", "value": 60.0, "sector": "healthcare", "max_loss": 4.8}
        ]
        
        capital = 1000.0
        
        # Calculate risk metrics
        risk_metrics = self.position_sizer.calculate_risk_metrics(positions, capital)
        
        logger.info(f"Portfolio Capital: ${capital:,.2f}")
        logger.info(f"Total Position Value: ${sum(pos['value'] for pos in positions):,.2f}")
        logger.info(f"\nRisk Metrics:")
        logger.info(f"  Portfolio Heat: {risk_metrics['portfolio_heat']:.1%}")
        logger.info(f"  Max Drawdown Risk: {risk_metrics['max_drawdown_risk']:.1%}")
        logger.info(f"  Correlation Risk: {risk_metrics['correlation_risk']:.1%}")
        
        logger.info(f"\nSector Concentration:")
        for sector, concentration in risk_metrics['sector_concentration'].items():
            logger.info(f"  {sector}: {concentration:.1%}")
        
        # Show position sizing configuration
        config = self.position_sizer.get_position_sizing_summary()
        logger.info(f"\nPosition Sizing Configuration:")
        logger.info(f"  Base Risk per Trade: {config['base_risk_per_trade']:.1%}")
        logger.info(f"  Max Position Size: {config['max_position_size']:.1%}")
        logger.info(f"  Min Position Size: {config['min_position_size']:.1%}")
        logger.info(f"  Kelly Multiplier: {config['kelly_multiplier']:.2f}")
        logger.info(f"  Max Portfolio Risk: {config['max_portfolio_risk']:.1%}")
        logger.info(f"  Max Sector Concentration: {config['max_sector_concentration']:.1%}")
    
    def demo_integration_with_strategies(self):
        """Demonstrate integration with trading strategies"""
        logger.info("\n🎯 STRATEGY INTEGRATION DEMO")
        logger.info("=" * 50)
        
        # Sample strategy signals
        signals = [
            {
                "symbol": "AAPL",
                "action": "BUY",
                "confidence": 0.8,
                "strategy": "BollingerBands",
                "price": 150.0,
                "volatility": 0.025
            },
            {
                "symbol": "TSLA",
                "action": "SELL",
                "confidence": 0.6,
                "strategy": "RSI",
                "price": 200.0,
                "volatility": 0.04
            },
            {
                "symbol": "JPM",
                "action": "BUY",
                "confidence": 0.9,
                "strategy": "MACD",
                "price": 140.0,
                "volatility": 0.02
            }
        ]
        
        capital = 1000.0
        current_date = date.today()
        
        logger.info(f"Portfolio Capital: ${capital:,.2f}")
        logger.info(f"Current Date: {current_date}")
        logger.info(f"Market Regime: {get_market_regime_for_date(current_date)['regime']}")
        
        for i, signal in enumerate(signals, 1):
            logger.info(f"\n📊 Signal {i}: {signal['symbol']} {signal['action']}")
            logger.info("-" * 30)
            
            # Calculate position size
            shares, sizing_details = calculate_position_size(
                capital=capital,
                price=signal['price'],
                confidence=signal['confidence'],
                volatility=signal['volatility'],
                target_date=current_date
            )
            
            logger.info(f"Strategy: {signal['strategy']}")
            logger.info(f"Confidence: {signal['confidence']:.1%}")
            logger.info(f"Volatility: {signal['volatility']:.1%}")
            logger.info(f"Position Size: {shares} shares")
            logger.info(f"Position Value: ${sizing_details['final_position_value']:.2f}")
            logger.info(f"Position %: {sizing_details['position_percentage']:.1f}%")
            
            # Show key adjustments
            logger.info(f"Key Adjustments:")
            logger.info(f"  Kelly: {sizing_details['kelly_size']:.3f}")
            logger.info(f"  Volatility: {sizing_details['volatility_adjustment']:.3f}")
            logger.info(f"  Confidence: {sizing_details['confidence_adjustment']:.3f}")
    
    def run_full_demo(self):
        """Run the complete demo"""
        logger.info("🚀 ECONOMIC CALENDAR & DYNAMIC POSITION SIZING DEMO")
        logger.info("=" * 80)
        
        try:
            # Demo economic calendar
            self.demo_economic_calendar()
            
            # Demo dynamic position sizing
            self.demo_dynamic_position_sizing()
            
            # Demo portfolio risk analysis
            self.demo_portfolio_risk_analysis()
            
            # Demo strategy integration
            self.demo_integration_with_strategies()
            
            logger.info("\n✅ Demo completed successfully!")
            logger.info("📚 Key Features Demonstrated:")
            logger.info("  • Economic calendar events (FOMC, earnings, CPI, etc.)")
            logger.info("  • Market regime detection")
            logger.info("  • Kelly Criterion position sizing")
            logger.info("  • Volatility-adjusted sizing")
            logger.info("  • Economic calendar adjustments")
            logger.info("  • Portfolio risk management")
            logger.info("  • Strategy integration")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise


async def main():
    """Main demo function"""
    demo = EconomicCalendarDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main()) 