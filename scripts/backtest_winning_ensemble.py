#!/usr/bin/env python3
"""
Backtest the Winning Ensemble Strategy
Combines the best-performing strategies from backtest results
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategies.winning_ensemble_strategy import WinningEnsembleStrategy
from strategies.strategy_factory import StrategyFactory
from services.market_data.market_data_provider import get_market_data_manager
from services.database.backtest_results_service import BacktestResultsService
from core.types import TradeSignal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WinningEnsembleBacktest:
    """Backtest the winning ensemble strategy"""
    
    def __init__(self, 
                 initial_capital: float = 100000,
                 start_date: str = "2023-01-01",
                 end_date: str = "2024-12-31",
                 symbols: list = None):
        
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date
        self.symbols = symbols or ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        
        # Portfolio tracking
        self.cash = initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_values = []
        
        # Strategy setup
        self.strategy_factory = StrategyFactory()
        self.ensemble_strategy = WinningEnsembleStrategy(
            min_confidence_threshold=0.6,
            max_risk_per_trade=0.02,
            use_weighted_voting=True
        )
        
        # Market data
        self.market_data_manager = None
        
    async def initialize(self):
        """Initialize the backtest"""
        logger.info("Initializing Winning Ensemble Backtest...")
        
        # Initialize market data manager
        self.market_data_manager = get_market_data_manager()
        
        # Initialize ensemble strategy with individual strategies
        await self.ensemble_strategy.initialize_strategies(self.strategy_factory)
        
        logger.info("Backtest initialized successfully")
    
    async def run_backtest(self):
        """Run the complete backtest"""
        logger.info(f"Starting backtest from {self.start_date} to {self.end_date}")
        
        # Get date range
        start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
        current_date = start_dt
        
        while current_date <= end_dt:
            try:
                # Get market data for current date
                market_data = await self._get_market_data(current_date)
                
                if market_data:
                    # Generate signals for each symbol
                    for symbol in self.symbols:
                        if symbol in market_data:
                            await self._process_symbol_signals(symbol, market_data[symbol], current_date)
                
                # Update portfolio value
                await self._update_portfolio_value(current_date)
                
                # Move to next trading day
                current_date += timedelta(days=1)
                
            except Exception as e:
                logger.error(f"Error processing date {current_date}: {e}")
                current_date += timedelta(days=1)
                continue
        
        # Generate final results
        results = await self._generate_results()
        return results
    
    async def _get_market_data(self, date: datetime) -> dict:
        """Get market data for a specific date"""
        try:
            market_data = {}
            for symbol in self.symbols:
                data = await self.market_data_manager.get_historical_data(
                    symbol=symbol,
                    start_date=date.strftime("%Y-%m-%d"),
                    end_date=date.strftime("%Y-%m-%d"),
                    interval="1d"
                )
                if not data.empty:
                    market_data[symbol] = data
            
            return market_data
        except Exception as e:
            logger.warning(f"Error getting market data for {date}: {e}")
            return {}
    
    async def _process_symbol_signals(self, symbol: str, data: pd.DataFrame, date: datetime):
        """Process signals for a specific symbol"""
        try:
            # Generate ensemble signal
            signal = await self.ensemble_strategy.generate_signal(
                symbol=symbol,
                data=data,
                historical_date=date.strftime("%Y-%m-%d")
            )
            
            if signal:
                await self._execute_trade(signal, date)
                
        except Exception as e:
            logger.error(f"Error processing signals for {symbol}: {e}")
    
    async def _execute_trade(self, signal: TradeSignal, date: datetime):
        """Execute a trade based on the signal"""
        try:
            # Calculate trade details
            trade_value = signal.quantity * signal.price
            commission = trade_value * 0.001  # 0.1% commission
            
            if signal.action == 'BUY':
                # Check if we have enough cash
                total_cost = trade_value + commission
                if self.cash >= total_cost:
                    # Execute buy
                    self.cash -= total_cost
                    if signal.symbol not in self.positions:
                        self.positions[signal.symbol] = 0
                    self.positions[signal.symbol] += signal.quantity
                    
                    # Record trade
                    self.trades.append({
                        'date': date,
                        'symbol': signal.symbol,
                        'action': signal.action,
                        'quantity': signal.quantity,
                        'price': signal.price,
                        'value': trade_value,
                        'commission': commission,
                        'confidence': signal.confidence,
                        'strategy': signal.strategy
                    })
                    
                    logger.info(f"BUY {signal.quantity} {signal.symbol} @ ${signal.price:.2f} (confidence: {signal.confidence:.3f})")
            
            elif signal.action == 'SELL':
                # Check if we have enough shares
                if signal.symbol in self.positions and self.positions[signal.symbol] >= signal.quantity:
                    # Execute sell
                    self.cash += trade_value - commission
                    self.positions[signal.symbol] -= signal.quantity
                    
                    if self.positions[signal.symbol] <= 0:
                        del self.positions[signal.symbol]
                    
                    # Record trade
                    self.trades.append({
                        'date': date,
                        'symbol': signal.symbol,
                        'action': signal.action,
                        'quantity': signal.quantity,
                        'price': signal.price,
                        'value': trade_value,
                        'commission': commission,
                        'confidence': signal.confidence,
                        'strategy': signal.strategy
                    })
                    
                    logger.info(f"SELL {signal.quantity} {signal.symbol} @ ${signal.price:.2f} (confidence: {signal.confidence:.3f})")
                    
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
    
    async def _update_portfolio_value(self, date: datetime):
        """Update portfolio value for tracking"""
        try:
            # Calculate current portfolio value
            portfolio_value = self.cash
            
            # Add value of positions
            for symbol, quantity in self.positions.items():
                # Get current price (simplified - in real implementation, get from market data)
                current_price = 100  # Placeholder price
                portfolio_value += quantity * current_price
            
            self.portfolio_values.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'positions': self.positions.copy()
            })
            
        except Exception as e:
            logger.error(f"Error updating portfolio value: {e}")
    
    async def _generate_results(self) -> dict:
        """Generate backtest results"""
        try:
            if not self.portfolio_values:
                return {"error": "No portfolio data available"}
            
            # Calculate performance metrics
            initial_value = self.portfolio_values[0]['portfolio_value']
            final_value = self.portfolio_values[-1]['portfolio_value']
            total_return = ((final_value - initial_value) / initial_value) * 100
            
            # Calculate daily returns
            daily_returns = []
            for i in range(1, len(self.portfolio_values)):
                prev_value = self.portfolio_values[i-1]['portfolio_value']
                curr_value = self.portfolio_values[i]['portfolio_value']
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)
            
            # Calculate Sharpe ratio
            if daily_returns:
                avg_return = np.mean(daily_returns)
                std_return = np.std(daily_returns)
                sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown()
            
            # Calculate win rate
            win_rate = self._calculate_win_rate()
            
            # Calculate profit factor
            profit_factor = self._calculate_profit_factor()
            
            results = {
                'strategy_name': 'Winning_Ensemble_Strategy',
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_capital': self.initial_capital,
                'final_portfolio_value': final_value,
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': len(self.trades),
                'total_commission': sum(trade['commission'] for trade in self.trades),
                'portfolio_values': self.portfolio_values,
                'trades': self.trades
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating results: {e}")
            return {"error": str(e)}
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        try:
            values = [pv['portfolio_value'] for pv in self.portfolio_values]
            peak = values[0]
            max_dd = 0
            
            for value in values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
            
            return max_dd * 100
        except Exception:
            return 0
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from trades"""
        try:
            if not self.trades:
                return 0
            
            # Group trades by symbol to calculate P&L
            symbol_trades = {}
            for trade in self.trades:
                symbol = trade['symbol']
                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []
                symbol_trades[symbol].append(trade)
            
            # Calculate P&L for each symbol
            wins = 0
            total_trades = 0
            
            for symbol, trades in symbol_trades.items():
                buy_trades = [t for t in trades if t['action'] == 'BUY']
                sell_trades = [t for t in trades if t['action'] == 'SELL']
                
                # Match buy/sell pairs
                for i in range(min(len(buy_trades), len(sell_trades))):
                    buy = buy_trades[i]
                    sell = sell_trades[i]
                    
                    pnl = (sell['price'] - buy['price']) * buy['quantity']
                    pnl -= buy['commission'] + sell['commission']
                    
                    if pnl > 0:
                        wins += 1
                    total_trades += 1
            
            return (wins / total_trades * 100) if total_trades > 0 else 0
            
        except Exception:
            return 0
    
    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        try:
            if not self.trades:
                return 0
            
            # Calculate total profit and loss
            total_profit = 0
            total_loss = 0
            
            # Group trades by symbol
            symbol_trades = {}
            for trade in self.trades:
                symbol = trade['symbol']
                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []
                symbol_trades[symbol].append(trade)
            
            for symbol, trades in symbol_trades.items():
                buy_trades = [t for t in trades if t['action'] == 'BUY']
                sell_trades = [t for t in trades if t['action'] == 'SELL']
                
                for i in range(min(len(buy_trades), len(sell_trades))):
                    buy = buy_trades[i]
                    sell = sell_trades[i]
                    
                    pnl = (sell['price'] - buy['price']) * buy['quantity']
                    pnl -= buy['commission'] + sell['commission']
                    
                    if pnl > 0:
                        total_profit += pnl
                    else:
                        total_loss += abs(pnl)
            
            return total_profit / total_loss if total_loss > 0 else 0
            
        except Exception:
            return 0


async def main():
    """Main function to run the backtest"""
    try:
        # Create backtest instance
        backtest = WinningEnsembleBacktest(
            initial_capital=100000,
            start_date="2023-01-01",
            end_date="2024-12-31",
            symbols=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        )
        
        # Initialize
        await backtest.initialize()
        
        # Run backtest
        logger.info("Running Winning Ensemble Strategy backtest...")
        results = await backtest.run_backtest()
        
        # Print results
        print("\n" + "="*60)
        print("WINNING ENSEMBLE STRATEGY BACKTEST RESULTS")
        print("="*60)
        
        if 'error' in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Strategy: {results['strategy_name']}")
            print(f"Period: {results['start_date']} to {results['end_date']}")
            print(f"Initial Capital: ${results['initial_capital']:,.2f}")
            print(f"Final Portfolio Value: ${results['final_portfolio_value']:,.2f}")
            print(f"Total Return: {results['total_return']:.2f}%")
            print(f"Sharpe Ratio: {results['sharpe_ratio']:.3f}")
            print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
            print(f"Win Rate: {results['win_rate']:.1f}%")
            print(f"Profit Factor: {results['profit_factor']:.2f}")
            print(f"Total Trades: {results['total_trades']}")
            print(f"Total Commission: ${results['total_commission']:,.2f}")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 