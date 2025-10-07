"""
Enhanced Backtesting Engine with Real Market Data Support
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import uuid
import traceback
import os

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.services.market_data.market_data_provider import get_market_data_manager
from src.services.market_data.cached_market_data_manager import get_cached_market_data_manager
from src.services.database.backtest_results_service import BacktestResultsService
# Risk management imports - simplified to avoid loguru dependency
from src.models.portfolio import Portfolio

# Simple risk limits for backtesting
@dataclass
class SimpleRiskLimits:
    """Simple risk limits for backtesting"""
    max_daily_loss: float = 0.02  # 2% max daily loss
    max_position_size: float = 0.05  # 5% max position size
    max_positions: int = 3  # Max 3 positions
    max_sector_concentration: float = 0.40  # 40% max sector concentration
    max_correlation: float = 0.70  # 70% max correlation
    var_limit: float = 0.02  # 2% VaR limit
    volatility_limit: float = 0.30  # 30% volatility limit
    beta_limit: float = 1.5  # 1.5 beta limit
from src.services.ai.trade_evaluator import TradeEvaluator
from src.utils.dynamic_position_sizing import DynamicPositionSizer, PositionSizingFactors
# Import error handler if available, otherwise use basic logging
try:
    from src.utils.error_handler import log_backtest_progress, log_strategy_execution, ErrorHandler
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    
    def log_backtest_progress(event: str, data: dict):
        logger.info(f"BACKTEST_PROGRESS - {event}: {data}")
    
    def log_strategy_execution(strategy_name: str, event: str, data: dict):
        logger.info(f"STRATEGY_EXECUTION - {strategy_name} - {event}: {data}")
    
    class ErrorHandler:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
        
        def handle_error(self, error, context):
            self.logger.error(f"Error in {context}: {error}")

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Represents a single trade in backtesting"""
    timestamp: datetime
    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    strategy: str
    pnl: float = 0.0
    confidence: float = 0.0  # Signal confidence level
    portfolio_value: float = 0.0  # Portfolio value at time of trade
    cash: float = 0.0  # Available cash at time of trade
    position_value: float = 0.0  # Value of position at time of trade
    total_pnl: float = 0.0  # Cumulative P&L at time of trade
    trade_pnl: float = 0.0  # Individual trade P&L
    # Public.com cost tracking
    commission: float = 0.0  # Commission paid
    options_rebate: float = 0.0  # Options rebate earned
    slippage: float = 0.0  # Slippage cost
    spread_cost: float = 0.0  # Spread cost
    total_cost: float = 0.0  # Total transaction cost
    net_cost: float = 0.0  # Net cost after rebates
    trade_type: str = "STOCK"  # STOCK or OPTIONS


@dataclass
class BacktestResult:
    """Represents the results of a backtest"""
    strategy: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    trades: List[BacktestTrade]
    equity_curve: pd.DataFrame
    start_date: datetime
    end_date: datetime
    # Public.com metrics
    public_com_summary: Optional[Dict[str, Any]] = None
    total_transaction_costs: float = 0.0
    total_rebates: float = 0.0
    net_transaction_costs: float = 0.0
    
    @property
    def max_drawdown(self) -> float:
        """Backward compatibility alias for max_drawdown_pct"""
        return self.max_drawdown_pct


class BacktestEngine:
    """Enhanced backtesting engine with real market data support and caching"""
    
    def __init__(self, 
                 use_real_data: bool = True, 
                 use_cache: bool = True, 
                 use_public_com_pricing: bool = True,
                 batch_size: int = 5,
                 progress_callback: Optional[callable] = None,
                 initial_capital: float = 4000.0):
        """
        Initialize the backtest engine with enhanced features
        
        Args:
            use_real_data: Whether to use real market data
            use_cache: Whether to use cached data
            use_public_com_pricing: Whether to use Public.com pricing
            batch_size: Number of symbols to process in each batch
            progress_callback: Function to call with progress updates
            initial_capital: Initial capital for backtesting (default: $4,000)
        """
        self.use_real_data = use_real_data
        self.use_cache = use_cache
        self.use_public_com_pricing = use_public_com_pricing
        self.batch_size = batch_size
        self.progress_callback = progress_callback
        self.initial_capital = initial_capital
        
        logger.info(f"🔧 DEBUG: BacktestEngine initialized with initial_capital: ${self.initial_capital:.2f}")
        
        # Check environment variable for database_only mode
        self.database_only = os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
        
        # Initialize appropriate market data manager
        if use_real_data:
            if use_cache:
                self.market_data_manager = get_cached_market_data_manager()
                logger.info(f"✅ Using cached market data manager (database_only={self.database_only})")
            else:
                self.market_data_manager = get_market_data_manager()
                logger.info("✅ Using direct market data manager")
        else:
            self.market_data_manager = None
            logger.info("✅ Using mock data for testing")
        
        self.results = {}
        
        # Initialize LLM trade evaluator
        self.use_llm_evaluation = os.getenv('ENABLE_LLM_EVALUATION', 'true').lower() in ('true', '1', 'yes')
        self.trade_evaluator = TradeEvaluator(enable_llm=self.use_llm_evaluation)
        
        # Initialize dynamic position sizer
        self.position_sizer = DynamicPositionSizer(
            base_risk_per_trade=0.02,  # 2% base risk
            max_position_size=0.15,    # 15% max position
            min_position_size=0.01,    # 1% min position
            kelly_multiplier=0.25,     # Conservative Kelly
            volatility_adjustment=True,
            market_regime_adjustment=True,
            economic_calendar_adjustment=True
        )
        
        # Initialize risk management for $4,000 account
        self.risk_limits = SimpleRiskLimits(
            max_daily_loss=0.02,  # 2% max daily loss ($80 on $4,000)
            max_position_size=0.05,  # 5% max position size ($200 on $4,000)
            max_positions=3,  # Max 3 positions for small account
            max_sector_concentration=0.40,  # 40% max sector concentration
            max_correlation=0.70,  # 70% max correlation
            var_limit=0.02,  # 2% VaR limit
            volatility_limit=0.30,  # 30% volatility limit
            beta_limit=1.5  # 1.5 beta limit
        )
        
        # Risk tracking
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        # Strategy weight allocation system
        self.strategy_weights = {
            'HybridIchimokuStrategy': 0.50,
            'CashSecuredPutStrategy': 0.50,
            'IronCondorStrategy': 0.20,
            'ButterflyStrategy': 0.15,
            'CalendarSpreadStrategy': 0.15,
            'ElliottWaveImpulseStrategy': 0.30,
            'ElliottWaveCorrectiveStrategy': 0.30,
            'RegimeSwitchingStrategy': 0.40
        }
        
        # Capital allocation system (as requested)
        self.capital_allocation = {
            'cash_reserve_pct': 0.10,          # 10% cash reserve
            'stock_allocation_pct': 0.40,      # 40% stocks swing trading
            'options_day_trading_pct': 0.25,   # 25% day trading options
            'options_swing_trading_pct': 0.25  # 25% swing trading options
        }
        
        # Portfolio heat tracking
        self.portfolio_heat = 0.0
        self.max_portfolio_heat = 0.20  # 20% max portfolio risk
        
        # Strategy performance tracking
        self.strategy_performance = {}
        self.strategy_trade_counts = {}
        
        # Current positions tracking
        self.current_positions = {}
        
        # Portfolio capital (will be set during backtest)
        self.portfolio_capital = self.initial_capital
        
        # Current portfolio value tracking
        self.current_portfolio_value = self.initial_capital
        
        # Public.com metrics tracking
        self.public_com_metrics = {
            'total_contracts': 0,
            'total_rebates': 0.0,
            'quality_trades': 0,
            'tier_level': 'Bronze'
        }
        
        # Initialize options data service
        self.options_service = None
        
        # Progress tracking
        self.progress_data = {
            'total_symbols': 0,
            'processed_symbols': 0,
            'current_strategy': '',
            'current_batch': 0,
            'total_batches': 0,
            'start_time': None,
            'estimated_completion': None
        }
        
        logger.info(f"🚀 BacktestEngine initialized:")
        logger.info(f"  - Real Data: {use_real_data}")
        logger.info(f"  - Cache: {use_cache}")
        logger.info(f"  - Public.com Pricing: {use_public_com_pricing}")
        logger.info(f"  - Batch Size: {batch_size}")
        logger.info(f"  - LLM Evaluation: {self.use_llm_evaluation}")
        self._initialize_options_service()
    
    def _log_progress(self, event: str, data: dict = None):
        """Log progress updates"""
        if data is None:
            data = {}
        
        # Update progress data
        if event == "start":
            self.progress_data['start_time'] = datetime.now()
            self.progress_data['total_symbols'] = data.get('total_symbols', 0)
            self.progress_data['total_batches'] = (self.progress_data['total_symbols'] + self.batch_size - 1) // self.batch_size
            self.progress_data['processed_symbols'] = 0
            self.progress_data['current_batch'] = 0
        
        elif event == "batch_start":
            self.progress_data['current_batch'] = data.get('batch_number', 0)
            self.progress_data['current_strategy'] = data.get('strategy', '')
        
        elif event == "batch_complete":
            self.progress_data['processed_symbols'] += data.get('symbols_processed', 0)
            
            # Calculate estimated completion time
            if self.progress_data['start_time'] and self.progress_data['processed_symbols'] > 0:
                elapsed = (datetime.now() - self.progress_data['start_time']).total_seconds()
                rate = self.progress_data['processed_symbols'] / elapsed
                remaining_symbols = self.progress_data['total_symbols'] - self.progress_data['processed_symbols']
                if rate > 0:
                    remaining_seconds = remaining_symbols / rate
                    self.progress_data['estimated_completion'] = datetime.now() + timedelta(seconds=remaining_seconds)
        
        # Log progress
        progress_pct = (self.progress_data['processed_symbols'] / self.progress_data['total_symbols'] * 100) if self.progress_data['total_symbols'] > 0 else 0
        
        logger.info(f"📊 PROGRESS [{event.upper()}]: {progress_pct:.1f}% complete")
        logger.info(f"  - Batch: {self.progress_data['current_batch']}/{self.progress_data['total_batches']}")
        logger.info(f"  - Symbols: {self.progress_data['processed_symbols']}/{self.progress_data['total_symbols']}")
        logger.info(f"  - Strategy: {self.progress_data['current_strategy']}")
        
        if self.progress_data['estimated_completion']:
            logger.info(f"  - ETA: {self.progress_data['estimated_completion'].strftime('%H:%M:%S')}")
        
        # Call progress callback if provided
        if self.progress_callback:
            self.progress_callback(event, self.progress_data.copy())
    
    def _create_symbol_batches(self, symbols: List[str]) -> List[List[str]]:
        """Create batches of symbols for processing"""
        batches = []
        for i in range(0, len(symbols), self.batch_size):
            batch = symbols[i:i + self.batch_size]
            batches.append(batch)
        
        logger.info(f"📦 Created {len(batches)} batches of symbols (batch_size={self.batch_size})")
        return batches
    
    async def _run_backtest_for_symbol(self, symbol: str, data: pd.DataFrame, start_date: str, end_date: str, strategy_name: str) -> List[BacktestTrade]:
        """
        Run backtest for a single symbol with a specific strategy
        
        Args:
            symbol: Stock symbol
            data: Market data for the symbol
            start_date: Start date
            end_date: End date
            strategy_name: Name of the strategy to run
            
        Returns:
            List of BacktestTrade objects
        """
        try:
            # Get strategy class
            strategy_class = self._get_strategy_class(strategy_name)
            if not strategy_class:
                logger.warning(f"⚠️ Strategy {strategy_name} not found")
                return []
            
            # Initialize strategy
            strategy = strategy_class()
            
            # Add technical indicators to data
            data_with_indicators = self._add_technical_indicators(data.copy())
            
            if data_with_indicators.empty:
                logger.warning(f"⚠️ No data after adding indicators for {symbol}")
                return []
            
            # Generate signals
            trades = []
            for i in range(len(data_with_indicators)):
                current_date = data_with_indicators.index[i]
                current_data = data_with_indicators.iloc[:i+1]
                
                if len(current_data) < 5:  # Reduced from 20 to 5 for testing
                    continue
                
                try:
                    signal = await strategy.generate_signal(symbol, current_data, current_date.strftime('%Y-%m-%d'))
                    logger.info(f"🔍 DEBUG: {symbol} - Signal generated: {signal}")
                    
                    # Risk validation for $4,000 account
                    if signal and signal.action in ['BUY', 'SELL']:
                        # Check daily loss limit
                        if self.daily_loss >= self.risk_limits.max_daily_loss * self.portfolio_capital:
                            logger.warning(f"🚨 RISK LIMIT: Daily loss limit reached for {symbol} (${self.daily_loss:.2f})")
                            continue
                        
                        # Check position size limit
                        position_value = signal.quantity * signal.price
                        max_position_value = self.risk_limits.max_position_size * self.portfolio_capital
                        if position_value > max_position_value:
                            logger.warning(f"🚨 RISK LIMIT: Position size too large for {symbol} (${position_value:.2f} > ${max_position_value:.2f})")
                            # Adjust position size to limit
                            signal.quantity = max_position_value / signal.price
                            logger.info(f"🔧 RISK ADJUSTMENT: Reduced position size to ${signal.quantity * signal.price:.2f}")
                        
                        # Check maximum positions
                        if len(self.current_positions) >= self.risk_limits.max_positions:
                            logger.warning(f"🚨 RISK LIMIT: Maximum positions reached ({len(self.current_positions)}/{self.risk_limits.max_positions})")
                            continue
                        
                        logger.info(f"✅ RISK VALIDATION PASSED: {symbol} - {signal.action} signal approved")
                    
                    if signal and signal.action in ['BUY', 'SELL']:
                        logger.info(f"🔍 DEBUG: {symbol} - Processing {signal.action} signal")
                        # Calculate dynamic position size
                        current_price = data_with_indicators['Close'].iloc[i]
                        logger.info(f"🔍 DEBUG: {symbol} - Current price: {current_price}")
                        
                        # Calculate position sizing factors
                        volatility = current_data['Close'].pct_change().std() * np.sqrt(252) if len(current_data) > 1 else 0.2
                        confidence = signal.confidence
                        logger.info(f"🔍 DEBUG: {symbol} - Volatility: {volatility}, Confidence: {confidence}")
                        
                        # Determine market regime based on volatility
                        if volatility < 0.15:
                            market_regime = "low_volatility"
                        elif volatility > 0.35:
                            market_regime = "high_volatility"
                        else:
                            market_regime = "normal_volatility"
                        
                        # Create position sizing factors
                        logger.info(f"🔍 DEBUG: {symbol} - Creating sizing factors...")
                        try:
                            sizing_factors = PositionSizingFactors(
                                volatility=volatility,
                                confidence=confidence,
                                market_regime=market_regime,
                                volatility_multiplier=1.0,
                                economic_impact=1.0,
                                portfolio_heat=len(self.current_positions) * 0.02,  # Simple portfolio heat
                                correlation_risk=0.0,
                                sector_concentration=0.0,
                                momentum_strength=0.0,
                                trend_strength=0.0,
                                risk_free_rate=0.02
                            )
                            logger.info(f"🔍 DEBUG: {symbol} - Sizing factors created successfully")
                        except Exception as e:
                            logger.error(f"🔍 DEBUG: {symbol} - Sizing factors creation error: {e}")
                            # Create minimal sizing factors
                            sizing_factors = PositionSizingFactors(
                                volatility=volatility,
                                confidence=confidence,
                                market_regime=market_regime,
                                volatility_multiplier=1.0,
                                economic_impact=1.0,
                                portfolio_heat=0.0,
                                correlation_risk=0.0,
                                sector_concentration=0.0,
                                momentum_strength=0.0,
                                trend_strength=0.0,
                                risk_free_rate=0.02
                            )
                        
                        # Get strategy weight for position sizing
                        strategy_weight = self.strategy_weights.get(strategy_name, 0.25)  # Default 25%
                        logger.info(f"🔍 DEBUG: {symbol} - Strategy weight: {strategy_weight}")
                        
                        # Adjust capital based on strategy weight and allocation
                        available_capital = self.portfolio_capital * strategy_weight
                        logger.info(f"🔍 DEBUG: {symbol} - Available capital after strategy weight: ${available_capital:.2f}")
                        
                        # Determine if this is a stock or options strategy
                        if 'Strategy' in strategy_name and any(x in strategy_name for x in ['IronCondor', 'Butterfly', 'Calendar', 'CashSecured']):
                            # Options strategy - use options allocation
                            available_capital *= self.capital_allocation['options_allocation_pct']
                        else:
                            # Stock strategy - use stock allocation
                            available_capital *= self.capital_allocation['stock_allocation_pct']
                        
                        # Calculate simple position size (bypass DynamicPositionSizer for now)
                        shares = int(available_capital * 0.5 / current_price)  # 50% of capital for more realistic trades
                        sizing_details = {"method": "simple", "capital": available_capital, "price": current_price}
                        logger.info(f"🔍 DEBUG: {symbol} - Simple position sizing: shares={shares}, capital=${available_capital:.2f}")
                        
                        # Apply portfolio heat adjustment
                        if self.portfolio_heat > self.max_portfolio_heat:
                            heat_adjustment = 1.0 - (self.portfolio_heat - self.max_portfolio_heat) * 2
                            shares = int(shares * max(0.1, heat_adjustment))
                        
                        # Update strategy performance tracking
                        if strategy_name not in self.strategy_performance:
                            self.strategy_performance[strategy_name] = {
                                'trades': 0,
                                'total_return': 0.0,
                                'win_rate': 0.0,
                                'sharpe_ratio': 0.0,
                                'max_drawdown': 0.0
                            }
                            self.strategy_trade_counts[strategy_name] = 0
                        
                        self.strategy_trade_counts[strategy_name] += 1
                        
                        # Update portfolio heat
                        trade_value = shares * current_price
                        trade_risk = trade_value * 0.02  # Assume 2% risk per trade
                        self.portfolio_heat += trade_risk / self.portfolio_capital
                        
                        # Calculate P&L for the trade
                        trade_pnl = 0.0
                        if signal.action == 'SELL' and symbol in self.current_positions:
                            # Calculate trade P&L for SELL trades
                            entry_price = self.current_positions[symbol]['entry_price']
                            trade_pnl = (current_price - entry_price) * shares
                            logger.info(f"🔍 DEBUG: {symbol} - SELL trade P&L: ${trade_pnl:.2f} (entry: ${entry_price:.2f}, exit: ${current_price:.2f}, shares: {shares})")
                        elif signal.action == 'BUY':
                            # BUY trades have no P&L initially
                            trade_pnl = 0.0
                            logger.info(f"🔍 DEBUG: {symbol} - BUY trade P&L: $0.00 (initial purchase)")
                        
                        # Calculate actual portfolio value
                        current_portfolio_value = self.current_portfolio_value
                        current_cash = current_portfolio_value - sum(pos['shares'] * pos['entry_price'] for pos in self.current_positions.values())
                        
                        trade = BacktestTrade(
                            timestamp=current_date,
                            symbol=symbol,
                            action=signal.action,
                            price=current_price,
                            quantity=shares,
                            strategy=strategy_name,
                            pnl=trade_pnl,  # Store actual P&L
                            confidence=signal.confidence,
                            portfolio_value=current_portfolio_value,
                            cash=current_cash,
                            position_value=trade_value,
                            total_pnl=trade_pnl,  # For now, same as trade P&L
                            trade_pnl=trade_pnl,
                            commission=0.0,
                            options_rebate=0.0,
                            slippage=0.0,
                            spread_cost=0.0,
                            total_cost=0.0,
                            net_cost=0.0
                        )
                        trades.append(trade)
                        logger.info(f"🔍 DEBUG: {symbol} - Trade added to list: {trade}")
                        
                        # Update portfolio value after trade
                        self.current_portfolio_value += trade_pnl
                        logger.info(f"💰 PORTFOLIO UPDATE: Value updated to ${self.current_portfolio_value:.2f} (P&L: ${trade_pnl:.2f})")
                        
                        # Update risk tracking
                        self.daily_trades += 1
                        if signal.action == 'SELL' and symbol in self.current_positions:
                            # Calculate trade P&L for risk tracking
                            entry_price = self.current_positions[symbol]['entry_price']
                            trade_pnl = (current_price - entry_price) * shares
                            if trade_pnl < 0:  # Only track losses
                                self.daily_loss += abs(trade_pnl)
                                logger.info(f"📊 RISK TRACKING: Daily loss updated to ${self.daily_loss:.2f} (trade loss: ${abs(trade_pnl):.2f})")
                        
                        # Update portfolio tracking with holding period management
                        if signal.action == 'BUY':
                            self.current_positions[symbol] = {
                                'shares': shares,
                                'entry_price': current_price,
                                'strategy': strategy_name,
                                'timestamp': current_date,
                                'max_holding_days': 30,  # Maximum holding period
                                'stop_loss_price': current_price * 0.95,  # 5% stop loss
                                'take_profit_price': current_price * 1.10  # 10% take profit
                            }
                            logger.info(f"🛡️ Position opened: {symbol} at ${current_price:.2f} (Stop: ${current_price * 0.95:.2f}, Target: ${current_price * 1.10:.2f})")
                        elif signal.action == 'SELL' and symbol in self.current_positions:
                            # Calculate holding period
                            entry_time = self.current_positions[symbol]['timestamp']
                            holding_days = (current_date - entry_time).days
                            
                            # Check if position exceeded maximum holding period
                            if holding_days > self.current_positions[symbol]['max_holding_days']:
                                logger.info(f"🕒 Position {symbol} closed due to maximum holding period: {holding_days} days")
                            
                            del self.current_positions[symbol]
                        
                        # Check for stop-losses and take-profits on existing positions
                        positions_to_close = []
                        for pos_symbol, position in self.current_positions.items():
                            entry_price = position['entry_price']
                            stop_loss_price = position['stop_loss_price']
                            take_profit_price = position['take_profit_price']
                            
                            # Check stop-loss
                            if current_price <= stop_loss_price:
                                logger.warning(f"🛑 STOP-LOSS TRIGGERED: {pos_symbol} at ${current_price:.2f} (stop: ${stop_loss_price:.2f})")
                                positions_to_close.append(pos_symbol)
                            # Check take-profit
                            elif current_price >= take_profit_price:
                                logger.info(f"🎯 TAKE-PROFIT TRIGGERED: {pos_symbol} at ${current_price:.2f} (target: ${take_profit_price:.2f})")
                                positions_to_close.append(pos_symbol)
                        
                        # Close positions that hit stop-loss or take-profit
                        for pos_symbol in positions_to_close:
                            if pos_symbol in self.current_positions:
                                entry_price = self.current_positions[pos_symbol]['entry_price']
                                position_shares = self.current_positions[pos_symbol]['shares']
                                trade_pnl = (current_price - entry_price) * position_shares
                                
                                # Calculate actual portfolio value for stop-loss trade
                                current_portfolio_value = self.current_portfolio_value
                                current_cash = current_portfolio_value - sum(pos['shares'] * pos['entry_price'] for pos in self.current_positions.values())
                                
                                # Create stop-loss/take-profit trade
                                stop_trade = BacktestTrade(
                                    timestamp=current_date,
                                    symbol=pos_symbol,
                                    action="SELL",
                                    price=current_price,
                                    quantity=position_shares,
                                    strategy="StopLoss/TakeProfit",
                                    pnl=trade_pnl,
                                    confidence=1.0,
                                    portfolio_value=current_portfolio_value,
                                    cash=current_cash,
                                    position_value=position_shares * current_price,
                                    total_pnl=trade_pnl,
                                    trade_pnl=trade_pnl,
                                    commission=0.0,
                                    options_rebate=0.0,
                                    slippage=0.0,
                                    spread_cost=0.0,
                                    total_cost=0.0,
                                    net_cost=0.0
                                )
                                trades.append(stop_trade)
                                logger.info(f"📊 Stop-loss/take-profit trade: {pos_symbol} P&L: ${trade_pnl:.2f}")
                                
                                # Update portfolio value after stop-loss trade
                                self.current_portfolio_value += trade_pnl
                                logger.info(f"💰 PORTFOLIO UPDATE: Stop-loss value updated to ${self.current_portfolio_value:.2f} (P&L: ${trade_pnl:.2f})")
                                
                                del self.current_positions[pos_symbol]
                        
                        logger.info(f"📊 Dynamic position sizing for {symbol}: {shares} shares (confidence: {confidence:.2f}, volatility: {volatility:.3f}, weight: {strategy_weight:.2f})")
                except Exception as e:
                    logger.debug(f"Error generating signal for {symbol} on {current_date}: {e}")
                    continue
            
            logger.info(f"✅ Generated {len(trades)} trades for {symbol} with {strategy_name}")
            return trades
            
        except Exception as e:
            logger.error(f"❌ Error running backtest for {symbol} with {strategy_name}: {e}")
            return []
    
    def _calculate_strategy_results(self, strategy_name: str, trades: List[BacktestTrade], start_date: str, end_date: str) -> 'BacktestResult':
        """Calculate strategy results from trades"""
        logger.info(f"🔍 DEBUG: _calculate_strategy_results called for {strategy_name} with {len(trades)} trades")
        
        if not trades:
            logger.info(f"🔍 DEBUG: No trades provided for {strategy_name}, returning empty result")
            return BacktestResult(
                strategy=strategy_name,
                initial_capital=0.0,
                final_capital=0.0,
                total_return=0.0,
                total_return_pct=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                trades=[],
                equity_curve=pd.DataFrame(),
                start_date=datetime.now(),
                end_date=datetime.now(),
                public_com_summary={},
                total_transaction_costs=0.0,
                total_rebates=0.0,
                net_transaction_costs=0.0
            )
        
        # Calculate returns
        initial_capital = self.initial_capital  # Use the actual initial capital from the engine
        current_capital = initial_capital
        returns = []
        
        for trade in trades:
            if trade.action == 'BUY':
                current_capital -= trade.price * trade.quantity
            elif trade.action == 'SELL':
                current_capital += trade.price * trade.quantity
            
            returns.append((current_capital - initial_capital) / initial_capital)
        
        total_return = returns[-1] if returns else 0.0
        final_capital = current_capital  # Final capital after all trades
        
        logger.info(f"🔍 DEBUG: {strategy_name} - final_capital calculation:")
        logger.info(f"🔍 DEBUG: {strategy_name} - initial_capital: ${initial_capital:.2f}")
        logger.info(f"🔍 DEBUG: {strategy_name} - current_capital: ${current_capital:.2f}")
        logger.info(f"🔍 DEBUG: {strategy_name} - final_capital: ${final_capital:.2f}")
        logger.info(f"🔍 DEBUG: {strategy_name} - total_return: {total_return:.6f}")
        
        # Calculate win rate
        winning_trades = sum(1 for r in returns if r > 0)
        losing_trades = len(trades) - winning_trades  # Calculate losing trades
        win_rate = winning_trades / len(returns) if returns else 0.0
        
        # Calculate Sharpe ratio (simplified)
        if len(returns) > 1:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Calculate max drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns - running_max
        max_drawdown_pct = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
        
        # Calculate profit factor
        profits = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        gross_profit = sum(profits) if profits else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        # Calculate average win and loss
        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0.0
        avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0.0
        
        logger.info(f"🔍 DEBUG: {strategy_name} - Creating BacktestResult with final_capital: ${final_capital:.2f}")
        
        return BacktestResult(
            strategy=strategy_name,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return * 100,  # Convert to percentage
            max_drawdown_pct=max_drawdown_pct * 100,  # Convert to percentage
            sharpe_ratio=sharpe_ratio,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            trades=trades,
            equity_curve=pd.DataFrame({'date': [], 'value': []}),
            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
            public_com_summary=self.public_com_metrics.copy(),
            total_transaction_costs=0.0,
            total_rebates=0.0,
            net_transaction_costs=0.0
        )
        
        # Initialize Public.com cost tracking
        self.public_com_metrics = {
            'total_contracts': 0,
            'total_rebates': 0.0,
            'total_commission_savings': 0.0,
            'tier': 'Bronze',
            'quality_trades': 0,
            'total_trades': 0
        }
        
        logger.info(f"🏴‍☠️ Public.com pricing: {'Enabled' if use_public_com_pricing else 'Disabled'}")
    
    def _initialize_options_service(self):
        """Initialize options data service with graceful degradation"""
        try:
            if not self.use_real_data:
                # Use mock options service for testing
                from src.services.mock_options_data_service import MockOptionsDataService
                self.options_service = MockOptionsDataService()
                logger.info("✅ Initialized MockOptionsDataService for backtesting")
            else:
                # Try to initialize real options service with multiple fallback levels
                service_initialized = False
                
                # Level 1: Try real options service
                try:
                    from src.services.market_data.options_data_service import OptionsDataService
                    self.options_service = OptionsDataService()
                    
                    # Test the service
                    test_options = self.options_service.get_liquid_options("AAPL", min_volume=10)
                    if test_options and len(test_options) > 0:
                        logger.info("✅ Initialized and tested real OptionsDataService")
                        service_initialized = True
                    else:
                        logger.warning("⚠️ Real options service returned no data, falling back")
                        
                except ImportError as e:
                    logger.warning(f"⚠️ Real options service not available: {e}")
                except Exception as e:
                    logger.warning(f"⚠️ Real options service failed: {e}")
                
                # Level 2: Fall back to mock service
                if not service_initialized:
                    try:
                        from src.services.mock_options_data_service import MockOptionsDataService
                        self.options_service = MockOptionsDataService()
                        
                        # Test the mock service
                        test_options = self.options_service.get_liquid_options("AAPL", min_volume=10)
                        if test_options and len(test_options) > 0:
                            logger.info("✅ Initialized and tested MockOptionsDataService fallback")
                            service_initialized = True
                        else:
                            logger.warning("⚠️ Mock options service returned no data")
                            
                    except Exception as e:
                        logger.error(f"❌ Mock options service failed: {e}")
                
                # Level 3: Create minimal service as last resort
                if not service_initialized:
                    logger.warning("⚠️ All options services failed, creating minimal fallback")
                    self.options_service = self._create_minimal_options_service()
                    logger.info("✅ Created minimal options service fallback")
                    
        except Exception as e:
            logger.error(f"❌ Critical failure in options service initialization: {e}")
            # Create a minimal service as absolute last resort
            self.options_service = self._create_minimal_options_service()
            logger.info("✅ Using critical fallback options service")
    
    def _create_minimal_options_service(self):
        """Create a minimal options service as last resort"""
        class MinimalOptionsService:
            def get_liquid_options(self, symbol, min_volume=10):
                logger.warning(f"Using minimal options service for {symbol}")
                return []  # Return empty list - strategies will handle fallback
            
            def get_liquid_options_with_historical_support(self, symbol, min_volume=10, historical_date=None):
                logger.warning(f"Using minimal options service for {symbol} (historical)")
                return []
            
            def can_execute_with_options_data(self):
                return False  # Indicates no options data available
        
        return MinimalOptionsService()
    
    def calculate_public_com_costs(self, trade_type: str, contracts: int = 0, trade_value: float = 0.0) -> Dict[str, float]:
        """
        Calculate Public.com specific costs and rebates for backtesting
        
        Args:
            trade_type: 'STOCK' or 'OPTIONS'
            contracts: Number of contracts (for options)
            trade_value: Total trade value
            
        Returns:
            Dictionary with cost breakdown
        """
        costs = {
            'commission': 0.0,
            'options_rebate': 0.0,
            'slippage': 0.0,
            'spread_cost': 0.0,
            'total_cost': 0.0,
            'net_cost': 0.0  # After rebates
        }
        
        if trade_type == 'STOCK':
            costs['commission'] = 0.0  # Commission-free
            costs['slippage'] = trade_value * 0.0003  # 0.03% slippage
            costs['spread_cost'] = trade_value * 0.001  # 0.1% spread
            
        elif trade_type == 'OPTIONS':
            costs['commission'] = 0.0  # Commission-free
            costs['options_rebate'] = contracts * 0.06  # $0.06 per contract rebate
            costs['slippage'] = trade_value * 0.0003  # 0.03% slippage
            costs['spread_cost'] = trade_value * 0.001  # 0.1% spread
            
            # Update Public.com metrics
            self.public_com_metrics['total_contracts'] += contracts
            self.public_com_metrics['total_rebates'] += costs['options_rebate']
        
        costs['total_cost'] = costs['commission'] + costs['slippage'] + costs['spread_cost']
        costs['net_cost'] = costs['total_cost'] - costs['options_rebate']
        
        return costs
    
    def calculate_traditional_costs(self, trade_type: str, contracts: int = 0, trade_value: float = 0.0) -> Dict[str, float]:
        """
        Calculate traditional broker costs for comparison
        
        Args:
            trade_type: 'STOCK' or 'OPTIONS'
            contracts: Number of contracts (for options)
            trade_value: Total trade value
            
        Returns:
            Dictionary with traditional cost breakdown
        """
        costs = {
            'commission': 0.0,
            'options_rebate': 0.0,
            'slippage': 0.0,
            'spread_cost': 0.0,
            'total_cost': 0.0,
            'net_cost': 0.0
        }
        
        if trade_type == 'STOCK':
            costs['commission'] = 0.65  # Traditional commission
            costs['slippage'] = trade_value * 0.0005  # 0.05% slippage
            costs['spread_cost'] = trade_value * 0.002  # 0.2% spread
            
        elif trade_type == 'OPTIONS':
            costs['commission'] = 0.50 * contracts  # $0.50 per contract
            costs['slippage'] = trade_value * 0.0005  # 0.05% slippage
            costs['spread_cost'] = trade_value * 0.002  # 0.2% spread
        
        costs['total_cost'] = costs['commission'] + costs['slippage'] + costs['spread_cost']
        costs['net_cost'] = costs['total_cost'] - costs['options_rebate']
        
        return costs
    
    def get_public_com_summary(self) -> Dict[str, Any]:
        """Get Public.com metrics summary"""
        # Calculate tier based on monthly contracts
        monthly_contracts = self.public_com_metrics['total_contracts']
        if monthly_contracts >= 100:
            tier = 'Gold'
        elif monthly_contracts >= 50:
            tier = 'Silver'
        else:
            tier = 'Bronze'
        
        return {
            'tier': tier,
            'monthly_contracts': monthly_contracts,
            'total_rebates': round(self.public_com_metrics['total_rebates'], 2),
            'total_trades': self.public_com_metrics['total_trades'],
            'quality_trades': self.public_com_metrics['quality_trades'],
            'quality_rate': round(self.public_com_metrics['quality_trades'] / max(self.public_com_metrics['total_trades'], 1) * 100, 1),
            'next_tier_threshold': 50 if tier == 'Bronze' else 100 if tier == 'Silver' else None,
            'contracts_to_next_tier': max(0, (50 if tier == 'Bronze' else 100 if tier == 'Silver' else 0) - monthly_contracts)
        }
        
    async def run_backtest(self, symbols: List[str], start_date: str, end_date: str, strategies: List[str]) -> Dict[str, BacktestResult]:
        """
        Run comprehensive backtest with real market data and caching
        
        Args:
            symbols: List of stock symbols to test
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            strategies: List of strategy names to test
            
        Returns:
            Dictionary with strategy names as keys and BacktestResult objects as values
        """
        # Log backtest start with structured data
        log_backtest_progress("backtest_started", {
            "initial_capital": 100000.0,
            "start_date": start_date,
            "end_date": end_date,
            "symbols": symbols,
            "strategies": strategies,
            "data_source": "cached_real" if self.use_cache else "real" if self.use_real_data else "mock",
            "options_service_available": self.options_service is not None
        })
        
        # Initialize progress tracking
        self._log_progress("start", {"total_symbols": len(symbols)})
        
        logger.info(f"🚀 Starting Comprehensive Backtesting Analysis")
        logger.info("=" * 60)
        logger.info(f"📊 Test Configuration:")
        logger.info(f"   Initial Capital: $100,000.00")
        logger.info(f"   Test Period: {start_date} to {end_date}")
        logger.info(f"   Symbols: {len(symbols)} stocks")
        logger.info(f"   Strategies: {', '.join(strategies)}")
        logger.info(f"   Data Source: {'Cached Real Market Data' if self.use_cache else 'Real Market Data' if self.use_real_data else 'Mock Data'}")
        logger.info(f"   Batch Size: {self.batch_size}")
        
        # Create symbol batches for smart processing
        symbol_batches = self._create_symbol_batches(symbols)
        
        # Get market data for all symbols
        log_backtest_progress("fetching_market_data", {"symbols": symbols, "date_range": f"{start_date} to {end_date}"})
        market_data = await self._get_market_data(symbols, start_date, end_date)
        
        if not market_data:
            logger.error("❌ No market data available for backtesting")
            return {}
        
        # Initialize error handler for structured error tracking
        error_handler = ErrorHandler()
        
        # Run backtests for each strategy with smart batching
        results = {}
        
        for strategy_name in strategies:
            logger.info(f"\n🔄 Processing Strategy: {strategy_name}")
            logger.info("-" * 40)
            
            # Initialize strategy results
            strategy_trades = []
            strategy_returns = []
            
            # Process symbols in batches
            for batch_idx, symbol_batch in enumerate(symbol_batches):
                self._log_progress("batch_start", {
                    "batch_number": batch_idx + 1,
                    "strategy": strategy_name,
                    "symbols_in_batch": len(symbol_batch)
                })
                
                logger.info(f"📦 Processing batch {batch_idx + 1}/{len(symbol_batches)}: {symbol_batch}")
                
                # Process each symbol in the batch
                batch_trades = []
                for symbol in symbol_batch:
                    if symbol in market_data:
                        try:
                            symbol_result = await self._run_backtest_for_symbol(
                                symbol, market_data[symbol], start_date, end_date, strategy_name
                            )
                            if symbol_result:
                                batch_trades.extend(symbol_result)
                        except Exception as e:
                            logger.error(f"❌ Error processing {symbol}: {e}")
                            error_handler.handle_error(e, f"symbol_{symbol}")
                
                # Add batch trades to strategy results
                strategy_trades.extend(batch_trades)
                
                self._log_progress("batch_complete", {
                    "symbols_processed": len(symbol_batch),
                    "trades_generated": len(batch_trades)
                })
            
            # Calculate strategy results
            if strategy_trades:
                result = self._calculate_strategy_results(strategy_name, strategy_trades, start_date, end_date)
                results[strategy_name] = result
                logger.info(f"✅ Strategy {strategy_name} completed: {len(strategy_trades)} trades")
            else:
                logger.warning(f"⚠️ No trades generated for strategy: {strategy_name}")
        
        # Add strategy performance summary to all results
        for strategy_name, result in results.items():
            result.strategy_performance = self.strategy_performance
            result.strategy_trade_counts = self.strategy_trade_counts
            result.capital_allocation = self.capital_allocation
            result.portfolio_heat = self.portfolio_heat
        
        logger.info(f"\n📊 Strategy Performance Summary:")
        for strategy, perf in self.strategy_performance.items():
            trade_count = self.strategy_trade_counts.get(strategy, 0)
            logger.info(f"  {strategy}: {trade_count} trades, {perf.get('total_return', 0):.2f}% return")
        
        logger.info(f"💰 Capital Allocation: {self.capital_allocation}")
        logger.info(f"🔥 Portfolio Heat: {self.portfolio_heat:.2f}%")
        
        logger.info(f"\n🎯 Backtesting Complete!")
        logger.info(f"   Strategies tested: {len(results)}")
        logger.info(f"   Total trades: {sum(len(r.trades) for r in results.values())}")
        
        return results
        import time
        start_time = time.time()
        
        for strategy_name in strategies:
            strategy_start_time = time.time()
            
            log_backtest_progress("strategy_started", {"strategy": strategy_name, "total_strategies": len(strategies)})
            logger.info(f"🏃 Running backtest for {strategy_name} strategy...")
            
            try:
                strategy_results = await self._run_strategy_backtest(strategy_name, market_data)
                
                strategy_duration = time.time() - strategy_start_time
                logger.info(f"⏱️ {strategy_name} completed in {strategy_duration:.2f} seconds")
                
                if strategy_results:
                    log_backtest_progress("strategy_completed", {
                        "strategy": strategy_name,
                        "total_return": strategy_results.total_return if hasattr(strategy_results, 'total_return') else 0,
                        "sharpe_ratio": strategy_results.sharpe_ratio if hasattr(strategy_results, 'sharpe_ratio') else 0,
                        "total_trades": strategy_results.total_trades if hasattr(strategy_results, 'total_trades') else 0,
                        "duration_seconds": strategy_duration
                    })
                else:
                    log_backtest_progress("strategy_failed", {"strategy": strategy_name, "reason": "no_results"})
                
                results[strategy_name] = strategy_results
                
            except Exception as e:
                error_context = {
                    "strategy": strategy_name,
                    "context": "strategy_backtest_execution",
                    "symbols": symbols,
                    "date_range": f"{start_date} to {end_date}"
                }
                error_handler.handle_error(e, error_context)
                log_backtest_progress("strategy_error", {"strategy": strategy_name, "error": str(e)})
                logger.error(f"❌ {strategy_name}: Error - {e}")
                results[strategy_name] = None
        
        total_duration = time.time() - start_time
        logger.info(f"⏱️ Total backtest duration: {total_duration:.2f} seconds")
        
        # Performance validation
        expected_max_duration = 30.0  # 30 seconds for 5 symbols × 3 strategies
        if total_duration > expected_max_duration:
            logger.warning(f"⚠️ Backtest took {total_duration:.2f}s, exceeding target of {expected_max_duration}s")
        else:
            logger.info(f"✅ Backtest completed within performance target ({total_duration:.2f}s < {expected_max_duration}s)")
        
        logger.info(f"🔍 DEBUG: Final results dictionary: {results}")
        logger.info(f"🔍 DEBUG: Final results keys: {list(results.keys())}")
        logger.info(f"🔍 DEBUG: Final results values: {list(results.values())}")
        
        self.results = results
        
        # Log cache performance if using cached manager
        if self.use_cache and hasattr(self.market_data_manager, 'get_stats'):
            cache_stats = self.market_data_manager.get_stats()
            logger.info("📊 Cache Performance Summary:")
            logger.info(f"   Cache Hit Rate: {cache_stats.get('cache_hit_rate', 0):.1f}%")
            logger.info(f"   API Calls Saved: {cache_stats.get('cache_hits', 0)}")
            logger.info(f"   Total API Calls: {cache_stats.get('api_calls', 0)}")
        
        # Log LLM performance if used
        if self.use_llm_evaluation:
            llm_report = self.trade_evaluator.get_performance_report()
            logger.info("🤖 LLM Trade Evaluation Performance:")
            logger.info(f"   Total Signals Evaluated: {llm_report['llm_performance']['total_signals']}")
            logger.info(f"   LLM Approval Rate: {llm_report['evaluations_summary']['approval_rate']:.1f}%")
            logger.info(f"   LLM Accuracy: {llm_report['evaluations_summary']['accuracy']:.1f}%")
            logger.info(f"   Average Confidence: {llm_report['evaluations_summary']['average_confidence']:.2f}")
        
        return results
    
    async def _get_market_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Get market data for all symbols with caching support"""
        if self.use_real_data and self.market_data_manager:
            logger.info(f"📥 Fetching market data for {len(symbols)} symbols...")
            
            # Use cached manager if available
            if hasattr(self.market_data_manager, 'get_multiple_symbols'):
                # Cached manager
                market_data = self.market_data_manager.get_multiple_symbols(symbols, start_date, end_date)
            else:
                # Direct manager
                market_data = self.market_data_manager.get_multiple_symbols(symbols, start_date, end_date)
            
            successful_symbols = len(market_data)
            logger.info(f"✅ Successfully fetched data for {successful_symbols}/{len(symbols)} symbols")
            
            if successful_symbols == 0:
                logger.warning("⚠️  No real data available, falling back to mock data...")
                return self._generate_mock_data(symbols, start_date, end_date)
            
            # Preprocess the data to add technical indicators
            processed_data = {}
            for symbol, data in market_data.items():
                processed_data[symbol] = self._add_technical_indicators(data)
            
            return processed_data
        else:
            logger.info("📊 Using mock data for testing...")
            return self._generate_mock_data(symbols, start_date, end_date)
    
    def _generate_mock_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Generate mock market data for testing"""
        mock_data = {}
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Generate date range
        date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
        
        for symbol in symbols:
            # Generate realistic mock data
            np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
            
            # Base price with some variation
            base_price = 100 + np.random.uniform(50, 200)
            prices = [base_price]
            
            # Generate price series with realistic movements
            for i in range(1, len(date_range)):
                # Daily return with some trend and volatility
                daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% std
                prices.append(prices[-1] * (1 + daily_return))
            
            # Create OHLCV data (using lowercase column names to match strategy expectations)
            data = pd.DataFrame({
                'Open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
                'High': [p * (1 + abs(np.random.uniform(0, 0.02))) for p in prices],
                'Low': [p * (1 - abs(np.random.uniform(0, 0.02))) for p in prices],
                'Close': prices,
                'Volume': np.random.randint(1000000, 10000000, len(prices)),
                'Symbol': symbol
            }, index=date_range)
            
            # Calculate technical indicators for mock data
            data['RSI'] = self._calculate_rsi(data['Close'])
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            
            # MACD
            exp1 = data['Close'].ewm(span=12).mean()
            exp2 = data['Close'].ewm(span=26).mean()
            data['MACD'] = exp1 - exp2
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
            
            # Bollinger Bands
            data['BB_Middle'] = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
            data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
            
            mock_data[symbol] = data
        
        logger.info(f"📊 Generated mock data for {len(symbols)} symbols")
        return mock_data
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the data"""
        if data.empty:
            return data
        
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # Ensure we have the required columns (Polygon uses different names)
        if 'Close' not in df.columns and 'c' in df.columns:
            df['Close'] = df['c']
        if 'Open' not in df.columns and 'o' in df.columns:
            df['Open'] = df['o']
        if 'High' not in df.columns and 'h' in df.columns:
            df['High'] = df['h']
        if 'Low' not in df.columns and 'l' in df.columns:
            df['Low'] = df['l']
        if 'Volume' not in df.columns and 'v' in df.columns:
            df['Volume'] = df['v']
        
        # Get the close price series for calculations
        close_series = df['Close'] if 'Close' in df.columns else df['c']
        
        # Calculate RSI with very conservative period to preserve data
        rsi_period = min(7, len(df) - 3)  # Use 7 or leave 3 days, whichever is smaller
        df['RSI'] = self._calculate_rsi(close_series, period=rsi_period)
        
        # Calculate Simple Moving Averages with very conservative periods
        sma_short_period = min(5, len(df) - 2)  # Use 5 or leave 2 days, whichever is smaller
        sma_long_period = min(10, len(df) - 1)  # Use 10 or leave 1 day, whichever is smaller
        
        df['SMA_20'] = close_series.rolling(window=sma_short_period).mean()
        df['SMA_50'] = close_series.rolling(window=sma_long_period).mean()
        
        # Calculate MACD with very conservative periods
        macd_fast = min(3, len(df) - 4)   # Use 3 or leave 4 days, whichever is smaller
        macd_slow = min(5, len(df) - 3)   # Use 5 or leave 3 days, whichever is smaller
        macd_signal = min(2, len(df) - 5)  # Use 2 or leave 5 days, whichever is smaller
        
        exp1 = close_series.ewm(span=macd_fast).mean()
        exp2 = close_series.ewm(span=macd_slow).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=macd_signal).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Calculate Bollinger Bands with very conservative period
        bb_period = min(5, len(df) - 2)  # Use 5 or leave 2 days, whichever is smaller
        df['BB_Middle'] = close_series.rolling(window=bb_period).mean()
        bb_std = close_series.rolling(window=bb_period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # Only remove NaN values if we have enough data left - be very conservative
        df_clean = df.dropna()
        if len(df_clean) < 10:  # If we have less than 10 days left, keep some NaN values
            logger.warning(f"⚠️ Limited data available ({len(df)} days), keeping partial indicators")
            # Keep the last few rows even with some NaN values - be more aggressive about keeping data
            df_clean = df.tail(max(10, len(df) - 2))  # Keep at least 10 days or all but 2 days
        
        logger.info(f"📊 Technical indicators added: {len(df_clean)}/{len(df)} days retained")
        return df_clean
    
    async def _run_strategy_backtest(self, strategy_name: str, market_data: Dict[str, pd.DataFrame]) -> Optional[BacktestResult]:
        """Run backtest for a specific strategy"""
        try:
            logger.info(f"🔍 DEBUG: Starting strategy backtest for {strategy_name}")
            logger.info(f"🔍 DEBUG: Market data has {len(market_data)} symbols")
            
            # Import strategy dynamically
            strategy_class = self._get_strategy_class(strategy_name)
            if not strategy_class:
                logger.error(f"❌ Strategy {strategy_name} not found")
                return None
            
            # Special handling for MultiStrategyEnsemble to use backtesting configuration
            if strategy_name == 'MultiStrategyEnsemble':
                from src.utils.multi_strategy_ensemble_config import get_backtesting_config
                backtest_config = get_backtesting_config()
                
                strategy = strategy_class(
                    adaptive_wave_weight=backtest_config['adaptive_wave_weight'],
                    regime_switching_weight=backtest_config['regime_switching_weight'],
                    enhanced_multi_weight=backtest_config['enhanced_multi_weight'],
                    momentum_weight=backtest_config['momentum_weight'],
                    max_total_exposure=backtest_config['max_total_exposure'],
                    correlation_threshold=backtest_config['correlation_threshold'],
                    performance_window=backtest_config['performance_window'],
                    rebalance_frequency=backtest_config['rebalance_frequency']
                )
                logger.info(f"✅ Initialized {strategy_name} with backtesting config:")
                logger.info(f"   Weights: adaptive_wave={backtest_config['adaptive_wave_weight']}, "
                           f"regime_switching={backtest_config['regime_switching_weight']}, "
                           f"enhanced_multi={backtest_config['enhanced_multi_weight']}, "
                           f"momentum={backtest_config['momentum_weight']}")
                logger.info(f"   Risk: max_exposure={backtest_config['max_total_exposure']}, "
                           f"correlation_threshold={backtest_config['correlation_threshold']}")
            else:
                strategy = strategy_class()
            
            # Set options service for strategies that need it
            if hasattr(strategy, 'set_options_service') and self.options_service:
                strategy.set_options_service(self.options_service)
            
            initial_capital = self.initial_capital  # Use the actual initial capital from the engine
            final_capital = initial_capital
            total_trades = 0
            winning_trades = 0
            losing_trades = 0
            trades = []
            equity_curve_data = []
            
            # Run backtest for each symbol
            for symbol, data in market_data.items():
                logger.info(f"🔍 DEBUG: {strategy_name} - Processing symbol {symbol}")
                symbol_result = await self._backtest_symbol(strategy, symbol, data)
                if symbol_result:
                    logger.info(f"🔍 DEBUG: {strategy_name} - {symbol} result: {symbol_result}")
                    total_trades += symbol_result['trades']
                    trades.extend(symbol_result['trade_list'])
                    
                    # Calculate capital changes
                    for trade in symbol_result['trade_list']:
                        if trade['action'] == 'BUY':
                            final_capital -= trade['value']
                        elif trade['action'] == 'SELL':
                            final_capital += trade['value']
                            if trade['pnl'] > 0:
                                winning_trades += 1
                            else:
                                losing_trades += 1
                else:
                    logger.info(f"🔍 DEBUG: {strategy_name} - {symbol} returned None result")
            
            logger.info(f"🔍 DEBUG: {strategy_name} - After processing all symbols:")
            logger.info(f"🔍 DEBUG: {strategy_name} - Total trades: {total_trades}")
            logger.info(f"🔍 DEBUG: {strategy_name} - Winning trades: {winning_trades}")
            logger.info(f"🔍 DEBUG: {strategy_name} - Losing trades: {losing_trades}")
            logger.info(f"🔍 DEBUG: {strategy_name} - All trades list length: {len(trades)}")
            
            # Calculate metrics
            total_return_absolute = final_capital - initial_capital
            total_return = total_return_absolute / initial_capital if initial_capital > 0 else 0  # Decimal return (0.15 = 15%)
            total_return_pct = total_return * 100  # Percentage return (15.0 = 15%)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            sharpe_ratio = self._calculate_sharpe_ratio(trades) if trades else 0
            max_drawdown_pct = self._calculate_max_drawdown(trades) if trades else 0
            
            # Calculate profit factor and average win/loss
            total_wins = sum(t['pnl'] for t in trades if t.get('pnl', 0) > 0)
            total_losses = abs(sum(t['pnl'] for t in trades if t.get('pnl', 0) < 0))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            avg_win = total_wins / winning_trades if winning_trades > 0 else 0
            avg_loss = total_losses / losing_trades if losing_trades > 0 else 0
            
            logger.info(f"🔍 DEBUG: {strategy_name} - Calculated metrics:")
            logger.info(f"🔍 DEBUG: {strategy_name} - Total return: ${total_return:.2f} ({total_return_pct:.2f}%)")
            logger.info(f"🔍 DEBUG: {strategy_name} - Win rate: {win_rate:.2f}")
            logger.info(f"🔍 DEBUG: {strategy_name} - Sharpe ratio: {sharpe_ratio:.2f}")
            logger.info(f"🔍 DEBUG: {strategy_name} - Max drawdown: {max_drawdown_pct:.2f}%")
            
            # Create equity curve
            equity_curve = pd.DataFrame(equity_curve_data) if equity_curve_data else pd.DataFrame()
            
            # Sanitize float values to prevent JSON serialization errors
            def sanitize_float(value):
                if value is None:
                    return 0.0
                if isinstance(value, (int, float)):
                    if np.isnan(value) or np.isinf(value):
                        return 0.0
                    return float(value)
                return 0.0
            
            # Convert trades to BacktestTrade objects
            backtest_trades = []
            for trade in trades:
                backtest_trades.append(BacktestTrade(
                    timestamp=trade['date'],
                    symbol=trade.get('symbol', ''),
                    action=trade['action'],
                    quantity=int(trade['shares']) if trade['shares'] is not None else 0,
                    price=sanitize_float(trade['price']),
                    strategy=strategy_name,
                    pnl=sanitize_float(trade.get('pnl', 0)),
                    confidence=sanitize_float(trade.get('confidence', 0.5)),  # Default confidence if not available
                    portfolio_value=sanitize_float(trade.get('portfolio_value', 0.0)),  # Default portfolio value if not available
                    cash=sanitize_float(trade.get('cash', 0.0)),  # Default cash if not available
                    position_value=sanitize_float(trade.get('position_value', 0.0)),  # Default position value if not available
                    total_pnl=sanitize_float(trade.get('total_pnl', 0.0)),  # Default total P&L if not available
                    trade_pnl=sanitize_float(trade.get('trade_pnl', 0.0))  # Default trade P&L if not available
                ))
            
            logger.info(f"🔍 DEBUG: {strategy_name} - Created {len(backtest_trades)} BacktestTrade objects")
            
            # Calculate Public.com metrics
            total_transaction_costs = sum(trade.get('total_cost', 0.0) for trade in trades)
            total_rebates = sum(trade.get('options_rebate', 0.0) for trade in trades)
            net_transaction_costs = total_transaction_costs - total_rebates
            
            result = BacktestResult(
                strategy=strategy_name,
                initial_capital=sanitize_float(initial_capital),
                final_capital=sanitize_float(final_capital),
                total_return=sanitize_float(total_return),
                total_return_pct=sanitize_float(total_return_pct),
                max_drawdown_pct=sanitize_float(max_drawdown_pct),
                sharpe_ratio=sanitize_float(sharpe_ratio),
                total_trades=int(total_trades) if total_trades is not None else 0,
                winning_trades=int(winning_trades) if winning_trades is not None else 0,
                losing_trades=int(losing_trades) if losing_trades is not None else 0,
                win_rate=sanitize_float(win_rate),
                profit_factor=sanitize_float(profit_factor),
                avg_win=sanitize_float(avg_win),
                avg_loss=sanitize_float(avg_loss),
                trades=backtest_trades,
                equity_curve=equity_curve,
                start_date=datetime.now(),  # Placeholder
                end_date=datetime.now(),     # Placeholder
                public_com_summary=self.get_public_com_summary() if self.use_public_com_pricing else None,
                total_transaction_costs=sanitize_float(total_transaction_costs),
                total_rebates=sanitize_float(total_rebates),
                net_transaction_costs=sanitize_float(net_transaction_costs)
            )
            
            logger.info(f"🔍 DEBUG: {strategy_name} - Created BacktestResult object")
            logger.info(f"✅ {strategy_name}: {total_return_pct:.2f}% return, {total_trades} trades")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error running backtest for {strategy_name}: {str(e)}")
            logger.error(f"❌ Exception details: {traceback.format_exc()}")
            return None
    
    async def _backtest_symbol(self, strategy: BaseStrategy, symbol: str, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Run backtest for a single symbol"""
        try:
            initial_capital = self.initial_capital  # Use the actual initial capital from the engine
            current_capital = initial_capital
            position = 0
            trades = []
            signals_generated = 0
            
            logger.info(f"🔍 DEBUG: Starting backtest for {symbol} with {len(data)} data points")
            
            # Add technical indicators to the data
            data_with_indicators = self._add_technical_indicators(data)
            logger.info(f"🔍 DEBUG: {symbol} - Data columns after adding indicators: {list(data_with_indicators.columns)}")
            
            # Check if data is empty after adding indicators
            if data_with_indicators.empty:
                logger.warning(f"⚠️ WARNING: {symbol} - Data is empty after adding technical indicators!")
                logger.warning(f"⚠️ WARNING: {symbol} - Original data shape: {data.shape}")
                logger.warning(f"⚠️ WARNING: {symbol} - This means insufficient data for rolling indicators (need 50+ days)")
                return None
            
            logger.info(f"🔍 DEBUG: {symbol} - Data with indicators shape: {data_with_indicators.shape}")
            
            # Run strategy on data
            for i in range(len(data_with_indicators)):
                current_data = data_with_indicators.iloc[:i+1]
                if len(current_data) < 5:  # Reduced from 20 to 5 for testing
                    continue
                
                # Get the current date being simulated
                current_date = data_with_indicators.index[i]
                if hasattr(current_date, 'strftime'):
                    historical_date = current_date.strftime("%Y-%m-%d")
                else:
                    historical_date = str(current_date)
                
                # Generate signal with historical date
                signal = await strategy.generate_signal(symbol, current_data, historical_date)
                
                if signal:
                    signals_generated += 1
                    logger.info(f"🔍 DEBUG: {symbol} - Signal {signals_generated}: {signal.action} at {data_with_indicators.index[i]}")
                    
                    # Initialize evaluation variable
                    evaluation = None
                    
                    # LLM Trade Evaluation
                    if self.use_llm_evaluation:
                        try:
                            evaluation = await self.trade_evaluator.evaluate_trade_signal(
                                signal, data_with_indicators, strategy.__class__.__name__
                            )
                            
                            # Only execute if LLM approves
                            if not evaluation['approved']:
                                logger.info(f"🔍 DEBUG: {symbol} - LLM rejected trade: {signal.action} at ${signal.price:.2f}")
                                continue
                            else:
                                logger.info(f"🔍 DEBUG: {symbol} - LLM approved trade: {signal.action} at ${signal.price:.2f} (confidence: {evaluation['confidence']:.2f})")
                        except Exception as e:
                            logger.error(f"❌ LLM evaluation failed for {symbol}: {str(e)}")
                            # Continue with trade if LLM evaluation fails
                    
                    # Execute trade
                    if signal.action == 'BUY' and position == 0:
                        # Buy signal
                        shares_to_buy = current_capital // signal.price
                        if shares_to_buy > 0:
                            position = shares_to_buy
                            trade_value = shares_to_buy * signal.price
                            
                            # Calculate transaction costs based on pricing model
                            if self.use_public_com_pricing:
                                costs = self.calculate_public_com_costs('STOCK', 0, trade_value)
                            else:
                                costs = self.calculate_traditional_costs('STOCK', 0, trade_value)
                            
                            # Apply net cost to capital
                            current_capital -= trade_value + costs['net_cost']
                            
                            # Update Public.com metrics
                            self.public_com_metrics['total_trades'] += 1
                            
                            trades.append({
                                'date': signal.timestamp,
                                'action': 'BUY',
                                'price': signal.price,
                                'shares': shares_to_buy,
                                'value': trade_value,
                                'pnl': 0,
                                'commission': costs['commission'],
                                'options_rebate': costs['options_rebate'],
                                'slippage': costs['slippage'],
                                'spread_cost': costs['spread_cost'],
                                'total_cost': costs['total_cost'],
                                'net_cost': costs['net_cost'],
                                'trade_type': 'STOCK',
                                'llm_evaluation': evaluation if self.use_llm_evaluation else None
                            })
                            logger.info(f"🔍 DEBUG: {symbol} - BUY trade: {shares_to_buy} shares at ${signal.price:.2f}, Net cost: ${costs['net_cost']:.2f}")
                    
                    elif signal.action == 'SELL' and position > 0:
                        # Sell signal
                        trade_value = position * signal.price
                        
                        # Calculate transaction costs based on pricing model
                        if self.use_public_com_pricing:
                            costs = self.calculate_public_com_costs('STOCK', 0, trade_value)
                        else:
                            costs = self.calculate_traditional_costs('STOCK', 0, trade_value)
                        
                        # Calculate P&L before costs
                        gross_pnl = trade_value - (position * trades[-1]['price']) if trades else 0
                        net_pnl = gross_pnl - costs['net_cost']
                        
                        # Apply net cost to capital
                        current_capital += trade_value - costs['net_cost']
                        
                        # Update Public.com metrics
                        self.public_com_metrics['total_trades'] += 1
                        if net_pnl > 0:
                            self.public_com_metrics['quality_trades'] += 1
                        
                        trades.append({
                            'date': signal.timestamp,
                            'action': 'SELL',
                            'price': signal.price,
                            'shares': position,
                            'value': trade_value,
                            'pnl': net_pnl,
                            'commission': costs['commission'],
                            'options_rebate': costs['options_rebate'],
                            'slippage': costs['slippage'],
                            'spread_cost': costs['spread_cost'],
                            'total_cost': costs['total_cost'],
                            'net_cost': costs['net_cost'],
                            'trade_type': 'STOCK',
                            'llm_evaluation': evaluation if self.use_llm_evaluation else None
                        })
                        logger.info(f"🔍 DEBUG: {symbol} - SELL trade: {position} shares at ${signal.price:.2f}, Net P&L: ${net_pnl:.2f}, Net cost: ${costs['net_cost']:.2f}")
                        
                        # Update LLM performance if evaluation was used
                        if self.use_llm_evaluation and len(trades) >= 2:
                            signal_id = f"{symbol}_{signal.timestamp.strftime('%Y%m%d_%H%M%S')}"
                            self.trade_evaluator.update_performance(signal_id, net_pnl)
                        
                        position = 0
            
            # Close any remaining position
            if position > 0:
                final_value = position * data_with_indicators.iloc[-1]['Close']
                current_capital += final_value
                logger.info(f"🔍 DEBUG: {symbol} - Closing position: {position} shares at ${data_with_indicators.iloc[-1]['Close']:.2f}")
            
            # Calculate return
            total_return = ((current_capital - initial_capital) / initial_capital) * 100
            completed_trades = len([t for t in trades if t['action'] == 'SELL'])
            
            logger.info(f"🔍 DEBUG: {symbol} - Summary: {signals_generated} signals, {len(trades)} total trades, {completed_trades} completed trades, {total_return:.2f}% return")
            
            result = {
                'symbol': symbol,
                'return': total_return,
                'trades': completed_trades,
                'trade_list': trades
            }
            
            logger.info(f"🔍 DEBUG: {symbol} - Returning result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error backtesting {symbol}: {str(e)}")
            return None
    
    def _get_strategy_class(self, strategy_name: str):
        """Get strategy class by name"""
        strategy_map = {
            'sma_crossover': 'src.strategies.breakout.sma_crossover.SMACrossoverStrategy',
            'rsi': 'src.strategies.momentum.rsi_strategy.RSIStrategy',
            'macd': 'src.strategies.momentum.macd_strategy.MACDStrategy',
            'bollinger_bands': 'src.strategies.mean_reversion.bollinger_bands_strategy.BollingerBandsStrategy',
            'news_enhanced': 'src.strategies.news_enhanced_strategy.NewsEnhancedStrategy',
            'momentum': 'src.strategies.momentum.momentum_strategy.MomentumStrategy',
            'mean_reversion': 'src.strategies.mean_reversion.mean_reversion_strategy.MeanReversionStrategy',
            'volatility_breakout': 'src.strategies.breakout.volatility_breakout_strategy.VolatilityBreakoutStrategy',
            'portfolio': 'src.strategies.portfolio_strategy.PortfolioStrategy',
            'SMACrossover': 'src.strategies.breakout.sma_crossover.SMACrossoverStrategy',
            'RSI': 'src.strategies.momentum.rsi_strategy.RSIStrategy',
            'RSIStrategy': 'src.strategies.momentum.rsi_strategy.RSIStrategy',
            'MACD': 'src.strategies.momentum.macd_strategy.MACDStrategy',
            'MACDStrategy': 'src.strategies.momentum.macd_strategy.MACDStrategy',
            'BollingerBands': 'src.strategies.mean_reversion.bollinger_bands_strategy.BollingerBandsStrategy',
            'BollingerBandsStrategy': 'src.strategies.mean_reversion.bollinger_bands_strategy.BollingerBandsStrategy',
            'MeanReversion': 'src.strategies.mean_reversion.mean_reversion_strategy.MeanReversionStrategy',
            'Momentum': 'src.strategies.momentum.momentum_strategy.MomentumStrategy',
            'VolatilityBreakout': 'src.strategies.breakout.volatility_breakout_strategy.VolatilityBreakoutStrategy',
            'TrailingStop': 'src.strategies.advanced.trailing_stop_strategy.TrailingStopStrategy',
            'Fibonacci': 'src.strategies.advanced.fibonacci_strategy.FibonacciStrategy',
            'GreeksEnhanced': 'src.strategies.options.greeks_enhanced_strategy.GreeksEnhancedStrategy',
            'Ichimoku': 'src.strategies.ichimoku_strategy.IchimokuStrategy',
            'IchimokuStrategy': 'src.strategies.ichimoku_strategy.IchimokuStrategy',
            'IchimokuEnhanced': 'src.strategies.ichimoku_enhanced_strategy.IchimokuEnhancedStrategy',
            'AdaptiveMomentum': 'src.strategies.adaptive_momentum_strategy.AdaptiveMomentumStrategy',
            'NeuralNetwork': 'src.strategies.neural_network_strategy.NeuralNetworkStrategy',
            'QuantumMomentum': 'src.strategies.quantum_momentum_strategy.QuantumMomentumStrategy',
            'RegimeSwitching': 'src.strategies.regime_switching_strategy.RegimeSwitchingStrategy',
            'RegimeSwitchingStrategy': 'src.strategies.regime_switching_strategy.RegimeSwitchingStrategy',
            'IronCondor': 'src.strategies.options.iron_condor_strategy.IronCondorStrategy',
            'EnhancedIronCondor': 'src.strategies.options.enhanced_iron_condor_strategy.EnhancedIronCondorStrategy',
            # New Advanced Options Strategies
            'IronCondorStrategy': 'src.strategies.advanced_options_strategies.IronCondorStrategy',
            'ButterflyStrategy': 'src.strategies.advanced_options_strategies.ButterflyStrategy',
            'CalendarSpreadStrategy': 'src.strategies.advanced_options_strategies.CalendarSpreadStrategy',
            'VWAP': 'src.strategies.vwap_strategy.VWAPStrategy',
            'PairsTrading': 'src.strategies.pairs_trading_strategy.PairsTradingStrategy',
            'KalmanFilter': 'src.strategies.kalman_filter_strategy.KalmanFilterStrategy',
            'MLEnsemble': 'src.strategies.ml_ensemble_strategy.MLEnsembleStrategy',
            'EnhancedDayTrading': 'src.strategies.enhanced_day_trading_strategy.EnhancedDayTradingStrategy',
            'NewsEnhanced': 'src.strategies.news_enhanced_strategy.NewsEnhancedStrategy',
            'SocialMediaSentiment': 'src.strategies.sentiment.social_media_sentiment_strategy.SocialMediaSentimentStrategy',
            'MultiStrategyEnsemble': 'src.strategies.advanced.multi_strategy_ensemble.MultiStrategyEnsemble',
            # New Options Strategies
            'CashSecuredPut': 'src.strategies.options.cash_secured_put_strategy.CashSecuredPutStrategy',
            'CashSecuredPutStrategy': 'src.strategies.options.cash_secured_put_strategy.CashSecuredPutStrategy',
            'CoveredCall': 'src.strategies.options.covered_call_strategy.CoveredCallStrategy',
            'CalendarSpread': 'src.strategies.options.calendar_spread_strategy.CalendarSpreadStrategy',
            'ButterflySpread': 'src.strategies.options.butterfly_spread_strategy.ButterflySpreadStrategy',
            'VolatilityStrategy': 'src.strategies.options.volatility_strategy.VolatilityStrategy',
            'EarningsStrategy': 'src.strategies.options.earnings_strategy.EarningsStrategy',
            # Alternative names for options strategies
            'CSP': 'src.strategies.options.cash_secured_put_strategy.CashSecuredPutStrategy',
            'CC': 'src.strategies.options.covered_call_strategy.CoveredCallStrategy',
            'Calendar': 'src.strategies.options.calendar_spread_strategy.CalendarSpreadStrategy',
            'Butterfly': 'src.strategies.options.butterfly_spread_strategy.ButterflySpreadStrategy',
            'Volatility': 'src.strategies.options.volatility_strategy.VolatilityStrategy',
            # Our new strategies
            'HybridIchimokuStrategy': 'src.strategies.hybrid_ichimoku_strategy.HybridIchimokuStrategy',
            'MomentumStrategy': 'src.strategies.momentum.momentum_strategy.MomentumStrategy',
            'Earnings': 'src.strategies.options.earnings_strategy.EarningsStrategy',
               'SimpleTestStrategy': 'src.strategies.simple_test_strategy.SimpleTestStrategy',
               'AggressiveTestStrategy': 'src.strategies.aggressive_test_strategy.AggressiveTestStrategy',
               'SimpleCashSecuredPutStrategy': 'src.strategies.simple_cash_secured_put_strategy.SimpleCashSecuredPutStrategy',
            # Elliott Wave strategies (enhanced)
            'ElliottWaveImpulseStrategy': 'src.strategies.enhanced_elliott_wave_strategies.ElliottWaveImpulseStrategy',
            'ElliottWaveCorrectiveStrategy': 'src.strategies.enhanced_elliott_wave_strategies.ElliottWaveCorrectiveStrategy',
            # Service-based Elliott Wave strategies
            'ServiceElliottWaveCorrectiveStrategy': 'src.strategies.elliott_wave_strategies.ElliottWaveCorrectiveStrategy',
            # Simplified Elliott Wave strategies
            'SimplifiedElliottWaveImpulseStrategy': 'src.strategies.simplified_elliott_wave_strategies.SimplifiedElliottWaveImpulseStrategy',
            'SimplifiedElliottWaveCorrectiveStrategy': 'src.strategies.simplified_elliott_wave_strategies.SimplifiedElliottWaveCorrectiveStrategy',
            'EnhancedElliottWaveImpulseStrategy': 'src.strategies.enhanced_elliott_wave_strategies.ElliottWaveImpulseStrategy',
            'EnhancedElliottWaveCorrectiveStrategy': 'src.strategies.enhanced_elliott_wave_strategies.ElliottWaveCorrectiveStrategy'
        }
        
        if strategy_name not in strategy_map:
            return None
        
        try:
            module_path, class_name = strategy_map[strategy_name].rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Error importing strategy {strategy_name}: {str(e)}")
            return None
    
    def _calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """Calculate Sharpe ratio from trades"""
        if not trades:
            return 0.0
        
        returns = [t.get('pnl', 0) for t in trades if t.get('pnl') is not None]
        if not returns:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        return mean_return / std_return
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown percentage from trades"""
        if not trades:
            return 0.0
        
        # Calculate cumulative portfolio value over time
        portfolio_values = []
        current_value = self.portfolio_capital  # Start with initial capital
        
        # Track portfolio value chronologically
        for trade in trades:
            # Get trade P&L (should be the change in portfolio value)
            trade_pnl = trade.get('pnl', 0)
            
            # Update portfolio value
            current_value += trade_pnl
            portfolio_values.append(current_value)
        
        if not portfolio_values:
            return 0.0
        
        # Calculate maximum drawdown properly
        peak = portfolio_values[0]  # Start with first value
        max_drawdown_pct = 0.0
        
        for value in portfolio_values:
            # Update peak if we hit a new high
            if value > peak:
                peak = value
            
            # Calculate drawdown from current peak
            if peak > 0:
                drawdown_pct = ((peak - value) / peak) * 100
            if drawdown_pct > max_drawdown_pct:
                max_drawdown_pct = drawdown_pct
        
        logger.info(f"🔍 DEBUG: Drawdown calculation - Initial: ${self.portfolio_capital:.2f}, Final: ${current_value:.2f}, Max DD: {max_drawdown_pct:.2f}%")
        return max_drawdown_pct
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi 

    async def store_results(self, results: Dict[str, BacktestResult], symbols: List[str], start_date: str, end_date: str, database_only: bool = False, backtest_name: Optional[str] = None):
        """Store backtest results in the database"""
        try:
            service = BacktestResultsService()
            
            for strategy_name, result in results.items():
                # Generate unique run ID
                run_id = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{strategy_name}"
                
                # Convert BacktestResult to dictionary format expected by service
                result_dict = {
                    'initial_capital': result.initial_capital,
                    'final_capital': result.final_capital,
                    'total_return': result.total_return,
                    'total_return_pct': result.total_return_pct,
                    'max_drawdown_pct': result.max_drawdown_pct,
                    'sharpe_ratio': result.sharpe_ratio,
                    'total_trades': result.total_trades,
                    'winning_trades': result.winning_trades,
                    'losing_trades': result.losing_trades,
                    'win_rate': result.win_rate,
                    'profit_factor': result.profit_factor,
                    'avg_win': result.avg_win,
                    'avg_loss': result.avg_loss,
                    'trades': [
                        {
                            'timestamp': trade.timestamp,
                            'symbol': trade.symbol,
                            'action': trade.action,
                            'quantity': trade.quantity,
                            'price': trade.price,
                            'pnl': trade.pnl,
                            'confidence': trade.confidence,
                            'portfolio_value': trade.portfolio_value,
                            'cash': trade.cash,
                            'position_value': trade.position_value,
                            'total_pnl': trade.total_pnl,
                            'trade_pnl': trade.trade_pnl
                        }
                        for trade in result.trades
                    ],
                    'equity_curve': result.equity_curve
                }
                
                # Store the result
                success = service.store_backtest_results(
                    run_id=run_id,
                    strategy=strategy_name,
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    result=result_dict,
                    database_only=database_only,
                    data_provider="cached" if self.use_cache else "direct",
                    backtest_name=backtest_name
                )
                
                if success:
                    logger.info(f"✅ Stored backtest results for {strategy_name} (run_id: {run_id}, backtest: {backtest_name})")
                else:
                    logger.error(f"❌ Failed to store backtest results for {strategy_name}")
            
            logger.info("✅ Backtest results storage completed")
        except Exception as e:
            logger.error(f"❌ Error storing backtest results: {str(e)}")
    
    def get_stored_results(self, strategy_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve stored backtest results from the database"""
        try:
            service = BacktestResultsService()
            return service.get_backtest_runs(strategy_name=strategy_name, limit=limit)
        except Exception as e:
            logger.error(f"❌ Error retrieving backtest results: {str(e)}")
            return [] 