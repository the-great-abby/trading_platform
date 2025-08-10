#!/usr/bin/env python3
"""
Usage Example: Winning Ensemble Strategy Integration
Shows how to integrate the winning ensemble strategy into your trading system
"""

import asyncio
import pandas as pd
from datetime import datetime
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategies.winning_ensemble_strategy import WinningEnsembleStrategy
from strategies.strategy_factory import StrategyFactory
from core.types import TradeSignal
from services.market_data.market_data_provider import get_market_data_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingSystem:
    """Example trading system using the winning ensemble strategy"""
    
    def __init__(self):
        self.ensemble_strategy = WinningEnsembleStrategy(
            min_confidence_threshold=0.6,
            max_risk_per_trade=0.02,
            use_weighted_voting=True
        )
        self.strategy_factory = StrategyFactory()
        self.market_data_manager = None
        self.portfolio = {
            'cash': 100000,
            'positions': {},
            'total_value': 100000
        }
        
    async def initialize(self):
        """Initialize the trading system"""
        logger.info("Initializing trading system...")
        
        # Initialize market data manager
        self.market_data_manager = get_market_data_manager()
        
        # Initialize ensemble strategy
        await self.ensemble_strategy.initialize_strategies(self.strategy_factory)
        
        logger.info("Trading system initialized successfully")
    
    async def generate_trading_signals(self, symbols: list) -> list:
        """Generate trading signals for multiple symbols"""
        signals = []
        
        for symbol in symbols:
            try:
                # Get market data
                data = await self.market_data_manager.get_historical_data(
                    symbol=symbol,
                    start_date=(datetime.now() - pd.Timedelta(days=100)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    interval="1d"
                )
                
                if not data.empty:
                    # Generate ensemble signal
                    signal = await self.ensemble_strategy.generate_signal(
                        symbol=symbol,
                        data=data
                    )
                    
                    if signal:
                        signals.append(signal)
                        logger.info(f"Generated signal for {symbol}: {signal.action} "
                                  f"(confidence: {signal.confidence:.3f})")
                
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        return signals
    
    async def execute_trades(self, signals: list):
        """Execute trades based on signals"""
        for signal in signals:
            try:
                if signal.action == 'BUY':
                    await self._execute_buy(signal)
                elif signal.action == 'SELL':
                    await self._execute_sell(signal)
                    
            except Exception as e:
                logger.error(f"Error executing trade: {e}")
    
    async def _execute_buy(self, signal: TradeSignal):
        """Execute a buy order"""
        trade_value = signal.quantity * signal.price
        commission = trade_value * 0.001  # 0.1% commission
        total_cost = trade_value + commission
        
        if self.portfolio['cash'] >= total_cost:
            # Execute buy
            self.portfolio['cash'] -= total_cost
            
            if signal.symbol not in self.portfolio['positions']:
                self.portfolio['positions'][signal.symbol] = 0
            self.portfolio['positions'][signal.symbol] += signal.quantity
            
            logger.info(f"BUY executed: {signal.quantity} {signal.symbol} @ ${signal.price:.2f}")
        else:
            logger.warning(f"Insufficient cash for BUY: {signal.symbol}")
    
    async def _execute_sell(self, signal: TradeSignal):
        """Execute a sell order"""
        if signal.symbol in self.portfolio['positions'] and \
           self.portfolio['positions'][signal.symbol] >= signal.quantity:
            
            trade_value = signal.quantity * signal.price
            commission = trade_value * 0.001
            net_proceeds = trade_value - commission
            
            # Execute sell
            self.portfolio['cash'] += net_proceeds
            self.portfolio['positions'][signal.symbol] -= signal.quantity
            
            if self.portfolio['positions'][signal.symbol] <= 0:
                del self.portfolio['positions'][signal.symbol]
            
            logger.info(f"SELL executed: {signal.quantity} {signal.symbol} @ ${signal.price:.2f}")
        else:
            logger.warning(f"Insufficient shares for SELL: {signal.symbol}")
    
    def get_portfolio_summary(self) -> dict:
        """Get portfolio summary"""
        total_value = self.portfolio['cash']
        
        # Add position values (simplified - in real system, get current prices)
        for symbol, quantity in self.portfolio['positions'].items():
            # Placeholder price - in real system, get from market data
            current_price = 100  # This should be actual current price
            total_value += quantity * current_price
        
        return {
            'cash': self.portfolio['cash'],
            'positions': self.portfolio['positions'],
            'total_value': total_value,
            'return_pct': ((total_value - 100000) / 100000) * 100
        }


async def main():
    """Main function demonstrating the trading system"""
    try:
        # Create trading system
        trading_system = TradingSystem()
        
        # Initialize
        await trading_system.initialize()
        
        # Example symbols to trade
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        
        print("\n" + "="*60)
        print("WINNING ENSEMBLE STRATEGY TRADING SYSTEM")
        print("="*60)
        
        # Generate signals
        print("\nGenerating trading signals...")
        signals = await trading_system.generate_trading_signals(symbols)
        
        if signals:
            print(f"\nGenerated {len(signals)} signals:")
            for signal in signals:
                print(f"  {signal.symbol}: {signal.action} "
                      f"(confidence: {signal.confidence:.3f}, "
                      f"quantity: {signal.quantity:.2f})")
            
            # Execute trades
            print("\nExecuting trades...")
            await trading_system.execute_trades(signals)
            
            # Show portfolio summary
            summary = trading_system.get_portfolio_summary()
            print(f"\nPortfolio Summary:")
            print(f"  Cash: ${summary['cash']:,.2f}")
            print(f"  Positions: {summary['positions']}")
            print(f"  Total Value: ${summary['total_value']:,.2f}")
            print(f"  Return: {summary['return_pct']:.2f}%")
        else:
            print("No signals generated")
        
        print("\n" + "="*60)
        print("INTEGRATION NOTES:")
        print("="*60)
        print("1. This example shows basic integration")
        print("2. In production, add proper error handling")
        print("3. Implement real-time market data feeds")
        print("4. Add proper order management system")
        print("5. Include comprehensive risk management")
        print("6. Add performance monitoring and reporting")
        print("7. Implement proper logging and alerts")
        
    except Exception as e:
        logger.error(f"Error in trading system: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 