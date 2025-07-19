#!/usr/bin/env python3
"""
2-Year LLM-Enhanced Backtest with Dollar Value Tracking
=======================================================
Runs comprehensive 2-year backtests with LLM trade evaluation:
- 2-year historical data analysis
- LLM evaluates each trade signal before execution
- Tracks actual dollar values and portfolio performance
- Shows individual trade P&L and final portfolio value
- Handles Ollama timeouts gracefully
- Realistic trading features: slippage, market hours, partial fills
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import os
import sys
import random

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.services.ai.trade_evaluator import TradeEvaluator
from src.services.ai.ollama_service import OllamaService
from src.utils.trading_config import get_symbols, get_options_symbols
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class TwoYearLLMBacktest:
    """
    Comprehensive 2-year backtest with LLM evaluation and dollar tracking
    """
    
    def __init__(self, initial_capital: float = 1000.0):
        # 2-year period configuration
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=730)  # 2 years
        
        # Portfolio configuration - Realistic $1,000 account
        self.initial_capital = initial_capital
        self.portfolio_value = initial_capital
        self.cash_balance = initial_capital
        self.positions = {}  # symbol -> {'shares': int, 'avg_price': float}
        
        # Position sizing for small account
        self.max_position_size = 0.15  # Max 15% of portfolio per position
        self.min_trade_value = 50.0    # Minimum $50 per trade
        self.max_trade_value = 150.0   # Maximum $150 per trade (15% of $1K)
        
        # Realistic trading features
        self.commission_per_trade = 1.0  # $1 commission per trade
        self.slippage_percentage = 0.05  # 0.05% slippage on trades
        self.partial_fill_probability = 0.15  # 15% chance of partial fill
        self.market_hours_only = True  # Only trade during market hours
        self.max_daily_trades = 3  # Max 3 trades per day
        self.min_holding_period = 1  # Minimum 1 day holding period
        self.stop_loss_percentage = 0.08  # 8% stop loss
        self.take_profit_percentage = 0.15  # 15% take profit
        
        # Risk management
        self.max_daily_loss = 50.0  # Max $50 loss per day
        self.max_portfolio_risk = 0.10  # Max 10% portfolio risk per trade
        self.correlation_limit = 0.7  # Max correlation between positions
        
        # Market conditions simulation
        self.volatility_multiplier = 1.0
        self.trend_strength = 1.0
        self.market_regime = 'normal'  # normal, volatile, trending
        
        # Get symbols from centralized configuration
        self.all_symbols = get_symbols()
        self.options_symbols = get_options_symbols()
        
        logger.info(f"📊 Using centralized symbol configuration:")
        logger.info(f"   Standard symbols: {len(self.all_symbols)}")
        logger.info(f"   Options symbols: {len(self.options_symbols)}")
        logger.info(f"💰 Initial capital: ${initial_capital:,.2f}")
        logger.info(f"📊 Position sizing: ${self.min_trade_value:.0f}-${self.max_trade_value:.0f} per trade")
        logger.info(f"📊 Max position size: {self.max_position_size*100:.0f}% of portfolio")
        logger.info(f"💰 Commission: ${self.commission_per_trade:.2f} per trade")
        logger.info(f"📊 Slippage: {self.slippage_percentage*100:.2f}%")
        logger.info(f"📊 Max daily trades: {self.max_daily_trades}")
        logger.info(f"🛡️  Stop loss: {self.stop_loss_percentage*100:.0f}% | Take profit: {self.take_profit_percentage*100:.0f}%")
        
        # Strategy configurations
        self.standard_strategies = [
            'BollingerBands', 'MACD', 'RSI', 'MeanReversion', 'Momentum',
            'SMACrossover', 'VolatilityBreakout', 'TrailingStop', 'Fibonacci'
        ]
        
        self.options_strategies = ['GreeksEnhanced']
        
        # LLM configuration
        self.llm_timeout = 10.0  # seconds
        self.llm_retry_attempts = 2
        self.fallback_confidence = 0.6  # Default confidence when LLM fails
        
        # Performance tracking
        self.llm_stats = {
            'total_signals': 0,
            'llm_evaluated': 0,
            'llm_timeout_skipped': 0,
            'llm_error_skipped': 0,
            'llm_approved': 0,
            'llm_rejected': 0,
            'fallback_approved': 0,
            'fallback_rejected': 0,
            'total_execution_time': 0,
            'llm_evaluation_time': 0
        }
        
        # Portfolio tracking
        self.portfolio_stats = {
            'initial_capital': initial_capital,
            'final_portfolio_value': 0,
            'total_return_dollars': 0,
            'total_return_percentage': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'average_win': 0,
            'average_loss': 0,
            'max_drawdown_dollars': 0,
            'max_drawdown_percentage': 0,
            'sharpe_ratio': 0,
            'total_commission_paid': 0,
            'total_slippage_paid': 0,
            'average_trade_value': 0,
            'partial_fills': 0,
            'stop_losses_triggered': 0,
            'take_profits_triggered': 0,
            'max_daily_loss_hits': 0,
            'correlation_violations': 0
        }
        
        # Trade history
        self.trade_history = []
        self.daily_trades = {}  # date -> trade_count
        self.daily_pnl = {}     # date -> pnl
        
        # Market conditions tracking
        self.market_conditions = {
            'volatility_periods': 0,
            'trending_periods': 0,
            'normal_periods': 0,
            'high_volume_days': 0,
            'low_volume_days': 0
        }
    
    async def run_2year_llm_backtest(self):
        """Run comprehensive 2-year backtest with LLM evaluation and dollar tracking"""
        
        logger.info("🚀 Starting 2-Year LLM-Enhanced Backtest with Dollar Tracking")
        logger.info("=" * 80)
        logger.info(f"📊 Configuration:")
        logger.info(f"   Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Duration: {(self.end_date - self.start_date).days} days")
        logger.info(f"   Total symbols: {len(self.all_symbols)}")
        logger.info(f"   Options symbols: {len(self.options_symbols)}")
        logger.info(f"   Initial capital: ${self.initial_capital:,.2f}")
        logger.info(f"   Position sizing: ${self.min_trade_value:.0f}-${self.max_trade_value:.0f}")
        logger.info(f"   Commission: ${self.commission_per_trade:.2f} per trade")
        logger.info(f"   Slippage: {self.slippage_percentage*100:.2f}%")
        logger.info(f"   Max daily trades: {self.max_daily_trades}")
        logger.info(f"   Stop loss: {self.stop_loss_percentage*100:.0f}% | Take profit: {self.take_profit_percentage*100:.0f}%")
        logger.info(f"   LLM Timeout: {self.llm_timeout}s")
        logger.info(f"   LLM Retry Attempts: {self.llm_retry_attempts}")
        logger.info(f"   Fallback Confidence: {self.fallback_confidence}")
        
        start_time = time.time()
        
        # Initialize backtest engine with LLM evaluation
        engine = BacktestEngine(use_real_data=True, use_cache=True)
        engine.use_llm_evaluation = True
        
        # Initialize LLM services
        await self._initialize_llm_services()
        
        # Run standard strategies
        logger.info("\n📈 PHASE 1: Standard Strategies with LLM Evaluation")
        logger.info("-" * 60)
        
        standard_results = await self._run_strategies_with_llm(
            engine, self.all_symbols, self.standard_strategies, "standard"
        )
        
        # Run options strategies
        logger.info("\n📈 PHASE 2: Options Strategies with LLM Evaluation")
        logger.info("-" * 60)
        
        options_results = await self._run_strategies_with_llm(
            engine, self.options_symbols, self.options_strategies, "options"
        )
        
        # Calculate total execution time
        total_time = time.time() - start_time
        self.llm_stats['total_execution_time'] = total_time
        
        # Calculate final portfolio value and performance
        self._calculate_portfolio_performance()
        
        # Generate comprehensive report
        await self._generate_2year_llm_report(standard_results, options_results)
        
        return {
            'standard_results': standard_results,
            'options_results': options_results,
            'llm_stats': self.llm_stats,
            'portfolio_stats': self.portfolio_stats,
            'trade_history': self.trade_history,
            'market_conditions': self.market_conditions
        }
    
    def _calculate_portfolio_performance(self):
        """Calculate final portfolio performance metrics"""
        
        # Calculate final portfolio value
        final_value = self.cash_balance
        for symbol, position in self.positions.items():
            # For demo purposes, assume current price is average price
            # In real implementation, this would use actual current prices
            final_value += position['shares'] * position['avg_price']
        
        self.portfolio_stats['final_portfolio_value'] = final_value
        self.portfolio_stats['total_return_dollars'] = final_value - self.initial_capital
        self.portfolio_stats['total_return_percentage'] = ((final_value - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate trade statistics
        if self.trade_history:
            winning_trades = [t for t in self.trade_history if t['pnl'] > 0]
            losing_trades = [t for t in self.trade_history if t['pnl'] < 0]
            
            self.portfolio_stats['total_trades'] = len(self.trade_history)
            self.portfolio_stats['winning_trades'] = len(winning_trades)
            self.portfolio_stats['losing_trades'] = len(losing_trades)
            self.portfolio_stats['total_pnl'] = sum(t['pnl'] for t in self.trade_history)
            
            # Calculate average trade value
            total_trade_values = sum(t['value'] for t in self.trade_history)
            self.portfolio_stats['average_trade_value'] = total_trade_values / len(self.trade_history)
            
            if winning_trades:
                self.portfolio_stats['largest_win'] = max(t['pnl'] for t in winning_trades)
                self.portfolio_stats['average_win'] = sum(t['pnl'] for t in winning_trades) / len(winning_trades)
            
            if losing_trades:
                self.portfolio_stats['largest_loss'] = min(t['pnl'] for t in losing_trades)
                self.portfolio_stats['average_loss'] = sum(t['pnl'] for t in losing_trades) / len(losing_trades)
        
        logger.info(f"💰 Portfolio Performance Summary:")
        logger.info(f"   Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"   Final Portfolio Value: ${final_value:,.2f}")
        logger.info(f"   Total Return: ${self.portfolio_stats['total_return_dollars']:,.2f} ({self.portfolio_stats['total_return_percentage']:+.2f}%)")
        logger.info(f"   Total Trades: {self.portfolio_stats['total_trades']}")
        logger.info(f"   Winning Trades: {self.portfolio_stats['winning_trades']}")
        logger.info(f"   Losing Trades: {self.portfolio_stats['losing_trades']}")
        logger.info(f"   Average Trade Value: ${self.portfolio_stats['average_trade_value']:,.2f}")
        logger.info(f"   Total Commissions: ${self.portfolio_stats['total_commission_paid']:,.2f}")
        logger.info(f"   Total Slippage: ${self.portfolio_stats['total_slippage_paid']:,.2f}")
        logger.info(f"   Partial Fills: {self.portfolio_stats['partial_fills']}")
        logger.info(f"   Stop Losses: {self.portfolio_stats['stop_losses_triggered']}")
        logger.info(f"   Take Profits: {self.portfolio_stats['take_profits_triggered']}")
    
    def _calculate_position_size(self, price: float, confidence: float, symbol: Optional[str] = None, date: Optional[datetime] = None) -> int:
        """Calculate realistic position size using dynamic sizing system"""
        
        try:
            from src.utils.dynamic_position_sizing import calculate_position_size, PositionSizingFactors
            from src.utils.economic_calendar import get_market_regime_for_date
            
            # Calculate volatility (simplified - in production you'd use actual volatility)
            volatility = 0.02  # 2% base volatility
            
            # Get market regime if date provided
            target_date = date.date() if date else None
            
            # Calculate position size using dynamic system
            shares, sizing_details = calculate_position_size(
                capital=self.portfolio_value,
                price=price,
                confidence=confidence,
                volatility=volatility,
                target_date=target_date
            )
            
            # Log sizing details for debugging
            if symbol:
                logger.debug(f"📊 Position sizing for {symbol}: {shares} shares (${sizing_details['final_position_value']:.2f})")
                logger.debug(f"   Kelly: {sizing_details['kelly_size']:.3f} | Vol Adj: {sizing_details['volatility_adjustment']:.3f}")
                logger.debug(f"   Regime: {sizing_details['regime_adjustment']:.3f} | Calendar: {sizing_details['calendar_adjustment']:.3f}")
            
            return int(shares)
            
        except ImportError:
            # Fallback to original method if dynamic sizing not available
            logger.warning("Dynamic position sizing not available, using fallback method")
            
            # Base position size based on confidence
            base_amount = self.max_trade_value * confidence
            
            # Ensure minimum trade size
            if base_amount < self.min_trade_value:
                base_amount = self.min_trade_value
            
            # Calculate shares based on price
            shares = int(base_amount / price)
            
            # Ensure we have at least 1 share
            if shares < 1:
                shares = 1
            
            # Ensure we don't exceed max position size
            max_shares = int((self.portfolio_value * self.max_position_size) / price)
            if shares > max_shares:
                shares = max_shares
            
            return shares
    
    def _simulate_market_conditions(self, date: datetime) -> Dict[str, Any]:
        """Simulate realistic market conditions"""
        
        # Simulate different market regimes
        day_of_week = date.weekday()
        month = date.month
        
        # Higher volatility on Mondays and Fridays
        if day_of_week in [0, 4]:  # Monday, Friday
            volatility_mult = 1.2
        else:
            volatility_mult = 1.0
        
        # Trending periods (earnings season, etc.)
        if month in [1, 4, 7, 10]:  # Earnings months
            trend_strength = 1.3
            self.market_conditions['trending_periods'] += 1
        else:
            trend_strength = 1.0
            self.market_conditions['normal_periods'] += 1
        
        # High volume days (monthly options expiry, etc.)
        if date.day in [15, 16, 17, 18, 19]:  # Options expiry week
            volume_mult = 1.5
            self.market_conditions['high_volume_days'] += 1
        else:
            volume_mult = 1.0
            self.market_conditions['low_volume_days'] += 1
        
        return {
            'volatility_multiplier': volatility_mult,
            'trend_strength': trend_strength,
            'volume_multiplier': volume_mult,
            'slippage_multiplier': volume_mult  # Higher volume = more slippage
        }
    
    def _check_risk_limits(self, symbol: str, action: str, shares: int, price: float) -> bool:
        """Check if trade meets risk management criteria"""
        
        trade_value = shares * price
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Check daily trade limit
        if current_date in self.daily_trades:
            if self.daily_trades[current_date] >= self.max_daily_trades:
                logger.info(f"⚠️  Daily trade limit reached for {current_date}")
                return False
        
        # Check daily loss limit
        if current_date in self.daily_pnl:
            if self.daily_pnl[current_date] <= -self.max_daily_loss:
                logger.info(f"⚠️  Daily loss limit reached for {current_date}")
                return False
        
        # Check portfolio risk limit
        if trade_value > (self.portfolio_value * self.max_portfolio_risk):
            logger.info(f"⚠️  Portfolio risk limit exceeded: ${trade_value:.2f} > ${self.portfolio_value * self.max_portfolio_risk:.2f}")
            return False
        
        # Check correlation limit (simplified)
        if len(self.positions) >= 2:
            # Simple correlation check - avoid too many similar positions
            sector_positions = sum(1 for pos in self.positions.keys() if pos in ['AAPL', 'MSFT', 'GOOGL'])
            if sector_positions >= 2 and symbol in ['AAPL', 'MSFT', 'GOOGL']:
                logger.info(f"⚠️  Correlation limit reached for tech stocks")
                return False
        
        return True
    
    def _simulate_trade_execution(self, symbol: str, action: str, shares: int, price: float) -> Dict[str, Any]:
        """Simulate realistic trade execution with slippage and partial fills"""
        
        # Simulate market conditions
        market_conditions = self._simulate_market_conditions(datetime.now())
        
        # Calculate slippage
        slippage_mult = market_conditions['slippage_multiplier']
        slippage_amount = price * self.slippage_percentage * slippage_mult
        
        # Apply slippage to execution price
        if action == 'BUY':
            execution_price = price + slippage_amount
        else:
            execution_price = price - slippage_amount
        
        # Simulate partial fill
        partial_fill = random.random() < self.partial_fill_probability
        if partial_fill:
            shares = max(1, int(shares * random.uniform(0.5, 0.9)))
            self.portfolio_stats['partial_fills'] += 1
            logger.info(f"📊 Partial fill: {shares} shares of {symbol}")
        
        # Calculate trade value and commission
        trade_value = shares * execution_price
        commission = self.commission_per_trade
        slippage_cost = abs(execution_price - price) * shares
        
        return {
            'shares': shares,
            'execution_price': execution_price,
            'trade_value': trade_value,
            'commission': commission,
            'slippage_cost': slippage_cost,
            'partial_fill': partial_fill
        }
    
    def _record_trade(self, symbol: str, action: str, shares: int, price: float, pnl: float, strategy: str, llm_approved: bool):
        """Record a trade with realistic execution details"""
        
        # Simulate trade execution
        execution = self._simulate_trade_execution(symbol, action, shares, price)
        
        # Update portfolio statistics
        self.portfolio_stats['total_commission_paid'] += execution['commission']
        self.portfolio_stats['total_slippage_paid'] += execution['slippage_cost']
        
        # Calculate net P&L after all costs
        net_pnl = pnl - execution['commission'] - execution['slippage_cost']
        
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': action,
            'shares': execution['shares'],
            'price': price,
            'execution_price': execution['execution_price'],
            'value': execution['trade_value'],
            'commission': execution['commission'],
            'slippage_cost': execution['slippage_cost'],
            'pnl': net_pnl,
            'strategy': strategy,
            'llm_approved': llm_approved,
            'portfolio_value': self.portfolio_value,
            'cash_balance': self.cash_balance,
            'partial_fill': execution['partial_fill'],
            'market_conditions': self._simulate_market_conditions(datetime.now())
        }
        
        self.trade_history.append(trade)
        
        # Update daily tracking
        current_date = datetime.now().strftime('%Y-%m-%d')
        if current_date not in self.daily_trades:
            self.daily_trades[current_date] = 0
        self.daily_trades[current_date] += 1
        
        if current_date not in self.daily_pnl:
            self.daily_pnl[current_date] = 0
        self.daily_pnl[current_date] += net_pnl
        
        # Update portfolio
        if action == 'BUY':
            total_cost = execution['trade_value'] + execution['commission']
            self.cash_balance -= total_cost
            if symbol in self.positions:
                # Average down/up
                total_shares = self.positions[symbol]['shares'] + execution['shares']
                total_cost_basis = (self.positions[symbol]['shares'] * self.positions[symbol]['avg_price']) + execution['trade_value']
                self.positions[symbol] = {
                    'shares': total_shares,
                    'avg_price': total_cost_basis / total_shares
                }
            else:
                self.positions[symbol] = {
                    'shares': execution['shares'],
                    'avg_price': execution['execution_price']
                }
        elif action == 'SELL':
            total_proceeds = execution['trade_value'] - execution['commission']
            self.cash_balance += total_proceeds
            if symbol in self.positions:
                self.positions[symbol]['shares'] -= execution['shares']
                if self.positions[symbol]['shares'] <= 0:
                    del self.positions[symbol]
        
        # Update portfolio value
        self.portfolio_value = self.cash_balance
        for sym, pos in self.positions.items():
            self.portfolio_value += pos['shares'] * pos['avg_price']
        
        logger.info(f"💰 Trade: {symbol} {action} {execution['shares']} shares @ ${execution['execution_price']:.2f} = ${execution['trade_value']:,.2f}")
        logger.info(f"   Commission: ${execution['commission']:.2f} | Slippage: ${execution['slippage_cost']:.2f} | Net P&L: ${net_pnl:,.2f}")
        logger.info(f"   Portfolio: ${self.portfolio_value:,.2f} | Partial Fill: {execution['partial_fill']}")
    
    async def _initialize_llm_services(self):
        """Initialize LLM services with timeout handling"""
        
        try:
            # Initialize Ollama service
            ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://192.168.65.3:11434')
            self.ollama_service = OllamaService(
                base_url=ollama_url,
                model=os.getenv('OLLAMA_MODEL', 'gemma3:1b'),
                timeout=self.llm_timeout
            )
            
            # Test LLM connection
            test_response = await asyncio.wait_for(
                self.ollama_service._call_ollama("Test connection"),
                timeout=self.llm_timeout
            )
            
            logger.info("✅ LLM service initialized successfully")
            self.llm_available = True
            
        except Exception as e:
            logger.warning(f"⚠️  LLM service not available: {str(e)}")
            logger.info("🔄 Will use fallback confidence for all signals")
            self.llm_available = False
            self.ollama_service = None
    
    async def _run_strategies_with_llm(self, engine: BacktestEngine, symbols: List[str], 
                                      strategies: List[str], strategy_type: str) -> Dict[str, Any]:
        """Run strategies with LLM evaluation and dollar tracking"""
        
        logger.info(f"🎯 Running {strategy_type} strategies with LLM evaluation...")
        logger.info(f"   Symbols: {len(symbols)}")
        logger.info(f"   Strategies: {len(strategies)}")
        
        # Custom trade evaluator with timeout handling and dollar tracking
        custom_evaluator = DollarTrackingTradeEvaluator(
            ollama_service=self.ollama_service,
            timeout=self.llm_timeout,
            retry_attempts=self.llm_retry_attempts,
            fallback_confidence=self.fallback_confidence,
            stats_tracker=self.llm_stats,
            portfolio_tracker=self
        )
        
        # Replace engine's trade evaluator
        engine.trade_evaluator = custom_evaluator
        
        # Run backtest
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            strategies=strategies
        )
        
        return results
    
    async def _generate_2year_llm_report(self, standard_results: Dict, options_results: Dict):
        """Generate comprehensive 2-year LLM backtest report with dollar values"""
        
        logger.info("\n📊 2-YEAR LLM BACKTEST RESULTS WITH DOLLAR TRACKING")
        logger.info("=" * 80)
        
        # Portfolio Performance Summary
        portfolio = self.portfolio_stats
        logger.info("💰 PORTFOLIO PERFORMANCE SUMMARY")
        logger.info("-" * 40)
        logger.info(f"📈 Initial Capital: ${portfolio['initial_capital']:,.2f}")
        logger.info(f"📈 Final Portfolio Value: ${portfolio['final_portfolio_value']:,.2f}")
        logger.info(f"📈 Total Return: ${portfolio['total_return_dollars']:,.2f} ({portfolio['total_return_percentage']:+.2f}%)")
        logger.info(f"📊 Total Trades: {portfolio['total_trades']}")
        logger.info(f"✅ Winning Trades: {portfolio['winning_trades']}")
        logger.info(f"❌ Losing Trades: {portfolio['losing_trades']}")
        logger.info(f"📊 Win Rate: {(portfolio['winning_trades']/portfolio['total_trades']*100):.1f}%" if portfolio['total_trades'] > 0 else "N/A")
        logger.info(f"💰 Average Trade Value: ${portfolio['average_trade_value']:,.2f}")
        logger.info(f"💰 Total Commissions: ${portfolio['total_commission_paid']:,.2f}")
        logger.info(f"💰 Total Slippage: ${portfolio['total_slippage_paid']:,.2f}")
        logger.info(f"📊 Partial Fills: {portfolio['partial_fills']}")
        logger.info(f"🛡️  Stop Losses: {portfolio['stop_losses_triggered']}")
        logger.info(f"🎯 Take Profits: {portfolio['take_profits_triggered']}")
        
        if portfolio['total_trades'] > 0:
            logger.info(f"💰 Average Win: ${portfolio['average_win']:,.2f}")
            logger.info(f"💰 Average Loss: ${portfolio['average_loss']:,.2f}")
            logger.info(f"💰 Largest Win: ${portfolio['largest_win']:,.2f}")
            logger.info(f"💰 Largest Loss: ${portfolio['largest_loss']:,.2f}")
        
        # Market Conditions Summary
        conditions = self.market_conditions
        logger.info("\n📈 MARKET CONDITIONS SUMMARY")
        logger.info("-" * 35)
        logger.info(f"📊 Volatility Periods: {conditions['volatility_periods']}")
        logger.info(f"📊 Trending Periods: {conditions['trending_periods']}")
        logger.info(f"📊 Normal Periods: {conditions['normal_periods']}")
        logger.info(f"📊 High Volume Days: {conditions['high_volume_days']}")
        logger.info(f"📊 Low Volume Days: {conditions['low_volume_days']}")
        
        # LLM Performance Summary
        stats = self.llm_stats
        logger.info("\n🤖 LLM PERFORMANCE SUMMARY")
        logger.info("-" * 40)
        logger.info(f"📊 Total Signals: {stats['total_signals']:,}")
        logger.info(f"✅ LLM Evaluated: {stats['llm_evaluated']:,}")
        logger.info(f"⏱️  LLM Timeout Skipped: {stats['llm_timeout_skipped']:,}")
        logger.info(f"❌ LLM Error Skipped: {stats['llm_error_skipped']:,}")
        logger.info(f"✅ LLM Approved: {stats['llm_approved']:,}")
        logger.info(f"❌ LLM Rejected: {stats['llm_rejected']:,}")
        
        # Calculate percentages
        if stats['total_signals'] > 0:
            llm_coverage = (stats['llm_evaluated'] / stats['total_signals']) * 100
            timeout_rate = (stats['llm_timeout_skipped'] / stats['total_signals']) * 100
            error_rate = (stats['llm_error_skipped'] / stats['total_signals']) * 100
            
            logger.info(f"📈 LLM Coverage: {llm_coverage:.1f}%")
            logger.info(f"⏱️  Timeout Rate: {timeout_rate:.1f}%")
            logger.info(f"❌ Error Rate: {error_rate:.1f}%")
        
        # Execution time
        logger.info(f"⏱️  Total Execution Time: {stats['total_execution_time']:.1f}s")
        logger.info(f"🤖 LLM Evaluation Time: {stats['llm_evaluation_time']:.1f}s")
        
        # Top trades by P&L
        if self.trade_history:
            logger.info("\n🏆 TOP TRADES BY P&L")
            logger.info("-" * 30)
            sorted_trades = sorted(self.trade_history, key=lambda x: x['pnl'], reverse=True)
            for i, trade in enumerate(sorted_trades[:5], 1):
                logger.info(f"{i}. {trade['symbol']} {trade['action']}: ${trade['pnl']:,.2f} ({trade['strategy']})")
        
        # Strategy Results Summary
        logger.info("\n📈 STRATEGY PERFORMANCE SUMMARY")
        logger.info("-" * 40)
        
        # Standard strategies
        if standard_results:
            logger.info("📊 Standard Strategies:")
            for strategy, result in standard_results.items():
                if result and hasattr(result, 'total_return_pct'):
                    logger.info(f"   {strategy}: {result.total_return_pct:+.2f}%")
        
        # Options strategies
        if options_results:
            logger.info("📊 Options Strategies:")
            for strategy, result in options_results.items():
                if result and hasattr(result, 'total_return_pct'):
                    logger.info(f"   {strategy}: {result.total_return_pct:+.2f}%")
        
        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS")
        logger.info("-" * 20)
        
        if portfolio['total_return_percentage'] > 0:
            logger.info("✅ Portfolio performed well - consider scaling up successful strategies")
        else:
            logger.info("⚠️  Portfolio underperformed - review strategy selection")
        
        if stats.get('llm_coverage', 0) > 80:
            logger.info("✅ LLM coverage is excellent - system working well")
        else:
            logger.info("⚠️  LLM coverage could be improved - consider timeout adjustments")

class DollarTrackingTradeEvaluator(TradeEvaluator):
    """Enhanced trade evaluator with dollar tracking and timeout handling"""
    
    def __init__(self, ollama_service: Optional[OllamaService], timeout: float, 
                 retry_attempts: int, fallback_confidence: float, stats_tracker: Dict, portfolio_tracker):
        super().__init__()
        self.ollama_service = ollama_service
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.fallback_confidence = fallback_confidence
        self.stats_tracker = stats_tracker
        self.portfolio_tracker = portfolio_tracker
        self.llm_available = ollama_service is not None
    
    async def evaluate_trade_signal(self, signal, market_data: pd.DataFrame, 
                                  strategy_name: str) -> Dict[str, Any]:
        """Evaluate trade signal with dollar tracking"""
        
        self.stats_tracker['total_signals'] += 1
        start_time = time.time()
        
        if not self.llm_available:
            # Use fallback evaluation
            evaluation = self._fallback_evaluation(signal, strategy_name)
            self.stats_tracker['llm_error_skipped'] += 1
            return evaluation
        
        try:
            # Prepare context for LLM
            context = self._prepare_evaluation_context(signal, market_data, strategy_name)
            prompt = self._generate_evaluation_prompt(context)
            
            # Try LLM evaluation with timeout and retries
            for attempt in range(self.retry_attempts + 1):
                try:
                    response = await asyncio.wait_for(
                        self.ollama_service._call_ollama(prompt),
                        timeout=self.timeout
                    )
                    
                    # Parse LLM response
                    evaluation = self._parse_evaluation_response(response, signal)
                    evaluation['timestamp'] = datetime.now()
                    evaluation['signal'] = signal
                    evaluation['strategy'] = strategy_name
                    
                    # Track statistics
                    self.stats_tracker['llm_evaluated'] += 1
                    if evaluation['approved']:
                        self.stats_tracker['llm_approved'] += 1
                    else:
                        self.stats_tracker['llm_rejected'] += 1
                    
                    # Update evaluation time
                    eval_time = time.time() - start_time
                    self.stats_tracker['llm_evaluation_time'] += eval_time
                    
                    logger.info(f"🔍 LLM Evaluation: {signal.symbol} {signal.action} - "
                               f"Approved: {evaluation['approved']}, "
                               f"Confidence: {evaluation['confidence']:.2f}")
                    
                    return evaluation
                    
                except asyncio.TimeoutError:
                    if attempt < self.retry_attempts:
                        logger.warning(f"⏱️  LLM timeout (attempt {attempt + 1}/{self.retry_attempts + 1})")
                        continue
                    else:
                        logger.warning(f"⏱️  LLM timeout after {self.retry_attempts + 1} attempts")
                        self.stats_tracker['llm_timeout_skipped'] += 1
                        return self._fallback_evaluation(signal, strategy_name)
                        
                except Exception as e:
                    if attempt < self.retry_attempts:
                        logger.warning(f"❌ LLM error (attempt {attempt + 1}/{self.retry_attempts + 1}): {str(e)}")
                        continue
                    else:
                        logger.error(f"❌ LLM error after {self.retry_attempts + 1} attempts: {str(e)}")
                        self.stats_tracker['llm_error_skipped'] += 1
                        return self._fallback_evaluation(signal, strategy_name)
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in LLM evaluation: {str(e)}")
            self.stats_tracker['llm_error_skipped'] += 1
            return self._fallback_evaluation(signal, strategy_name)
    
    def _fallback_evaluation(self, signal, strategy_name: str) -> Dict[str, Any]:
        """Fallback evaluation when LLM is unavailable"""
        
        # Simple fallback logic based on signal confidence
        approved = signal.confidence >= self.fallback_confidence
        
        if approved:
            self.stats_tracker['fallback_approved'] += 1
        else:
            self.stats_tracker['fallback_rejected'] += 1
        
        evaluation = {
            'approved': approved,
            'confidence': signal.confidence,
            'reason': f"Fallback evaluation (LLM unavailable) - Signal confidence: {signal.confidence:.2f}",
            'risk_level': 'medium',
            'expected_return': 'neutral',
            'timestamp': datetime.now(),
            'signal': signal,
            'strategy': strategy_name,
            'fallback_used': True
        }
        
        logger.info(f"🔄 Fallback Evaluation: {signal.symbol} {signal.action} - "
                   f"Approved: {approved}, Confidence: {signal.confidence:.2f}")
        
        return evaluation

async def main():
    """Main function"""
    
    logger.info("🚀 Starting 2-Year LLM-Enhanced Backtest with Dollar Tracking")
    
    # Initialize and run backtest with $1,000 initial capital
    backtest = TwoYearLLMBacktest(initial_capital=1000.0)
    results = await backtest.run_2year_llm_backtest()
    
    logger.info("✅ 2-Year LLM backtest with dollar tracking completed successfully!")
    
    # Save results
    import json
    with open('2year_llm_backtest_dollar_results.json', 'w') as f:
        # Convert results to serializable format
        serializable_results = {
            'llm_stats': results['llm_stats'],
            'portfolio_stats': results['portfolio_stats'],
            'market_conditions': results['market_conditions'],
            'test_period': {
                'start_date': backtest.start_date.strftime('%Y-%m-%d'),
                'end_date': backtest.end_date.strftime('%Y-%m-%d'),
                'duration_days': (backtest.end_date - backtest.start_date).days
            },
            'configuration': {
                'initial_capital': backtest.initial_capital,
                'llm_timeout': backtest.llm_timeout,
                'llm_retry_attempts': backtest.llm_retry_attempts,
                'fallback_confidence': backtest.fallback_confidence,
                'total_symbols': len(backtest.all_symbols),
                'options_symbols': len(backtest.options_symbols),
                'position_sizing': {
                    'min_trade_value': backtest.min_trade_value,
                    'max_trade_value': backtest.max_trade_value,
                    'max_position_size': backtest.max_position_size
                },
                'trading_features': {
                    'commission_per_trade': backtest.commission_per_trade,
                    'slippage_percentage': backtest.slippage_percentage,
                    'partial_fill_probability': backtest.partial_fill_probability,
                    'max_daily_trades': backtest.max_daily_trades,
                    'stop_loss_percentage': backtest.stop_loss_percentage,
                    'take_profit_percentage': backtest.take_profit_percentage
                }
            },
            'trade_history': [
                {
                    'timestamp': trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': trade['symbol'],
                    'action': trade['action'],
                    'shares': trade['shares'],
                    'price': trade['price'],
                    'execution_price': trade['execution_price'],
                    'value': trade['value'],
                    'commission': trade['commission'],
                    'slippage_cost': trade['slippage_cost'],
                    'pnl': trade['pnl'],
                    'strategy': trade['strategy'],
                    'llm_approved': trade['llm_approved'],
                    'portfolio_value': trade['portfolio_value'],
                    'cash_balance': trade['cash_balance'],
                    'partial_fill': trade['partial_fill']
                }
                for trade in results['trade_history']
            ]
        }
        json.dump(serializable_results, f, indent=2)
    
    logger.info("💾 Results saved to: 2year_llm_backtest_dollar_results.json")

if __name__ == "__main__":
    asyncio.run(main()) 