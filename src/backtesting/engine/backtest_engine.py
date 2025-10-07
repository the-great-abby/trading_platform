"""
Enhanced Backtesting Engine with Real Market Data Support
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.services.market_data.unified_options_pricing_service import unified_options_pricing
import logging
from dataclasses import dataclass
import uuid
import traceback
import os

logger = logging.getLogger(__name__)

# Import with error handling to avoid dependency issues
try:
    from src.strategies.base import BaseStrategy
    from src.core.types import TradeSignal
    from src.services.market_data.market_data_provider import get_market_data_manager
    from src.services.market_data.cached_market_data_manager import get_cached_market_data_manager
    from src.services.database.backtest_results_service import BacktestResultsService
    from src.services.ai.trade_evaluator import TradeEvaluator
    from src.strategies.strategy_registry import get_strategy_registry, discover_strategies
    STRATEGIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some dependencies not available: {e}")
    STRATEGIES_AVAILABLE = False
    # Define minimal fallbacks
    BaseStrategy = None
    TradeSignal = None


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
    
    @property
    def max_drawdown(self) -> float:
        """Backward compatibility property for max_drawdown_pct"""
        return self.max_drawdown_pct
    
    @max_drawdown.setter
    def max_drawdown(self, value: float) -> None:
        """Backward compatibility setter for max_drawdown_pct"""
        self.max_drawdown_pct = value


class BacktestEngine:
    """Enhanced backtesting engine with real market data support and caching"""
    
    def __init__(self, use_real_data: bool = True, use_cache: bool = True):
        self.use_real_data = use_real_data
        self.use_cache = use_cache
        
        # Check environment variable for database_only mode
        self.database_only = os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
        
        # Check if running in Kubernetes (has KUBERNETES_SERVICE_HOST)
        self.in_kubernetes = os.getenv('KUBERNETES_SERVICE_HOST') is not None
        if self.in_kubernetes:
            logger.info("🎯 Running in Kubernetes - will use cluster service addresses")
        
        # Initialize appropriate market data manager
        if use_real_data and STRATEGIES_AVAILABLE:
            try:
                if use_cache:
                    self.market_data_manager = get_cached_market_data_manager()
                    logger.info(f"✅ Using cached market data manager (database_only={self.database_only})")
                else:
                    self.market_data_manager = get_market_data_manager()
                    logger.info("✅ Using direct market data manager")
            except Exception as e:
                logger.warning(f"Failed to initialize market data manager: {e}")
                self.market_data_manager = None
                self.use_real_data = False
        else:
            self.market_data_manager = None
            logger.info("✅ Using mock data for testing")
        
        self.results = {}
        
        # Initialize options data service for real options pricing
        if STRATEGIES_AVAILABLE:
            try:
                from src.services.market_data.enhanced_options_data_service import get_enhanced_options_service
                self.options_data_service = get_enhanced_options_service()
                logger.info("✅ Enhanced options data service initialized")
            except Exception as e:
                logger.warning(f"Enhanced options data service not available: {e}")
                self.options_data_service = None
        else:
            self.options_data_service = None
        
        # Initialize LLM trade evaluator
        self.use_llm_evaluation = os.getenv('ENABLE_LLM_EVALUATION', 'true').lower() in ('true', '1', 'yes')
        if STRATEGIES_AVAILABLE:
            try:
                self.trade_evaluator = TradeEvaluator(enable_llm=self.use_llm_evaluation)
            except Exception as e:
                logger.warning(f"Failed to initialize trade evaluator: {e}")
                self.trade_evaluator = None
        else:
            self.trade_evaluator = None
        
        # Track the last signal for options trade detection
        self._last_signal = None
    
    def _get_real_options_price(self, symbol: str, current_date: datetime, underlying_price: float) -> Optional[float]:
        """
        Get real historical options price for backtesting
        
        Args:
            symbol: Stock symbol
            current_date: Current date in backtest
            underlying_price: Current underlying stock price
            
        Returns:
            Real options price or None if not available
        """
        if not self.options_data_service:
            return None
            
        try:
            # Convert datetime to date
            if isinstance(current_date, datetime):
                snapshot_date = current_date.date()
            else:
                snapshot_date = current_date
            
            # Get historical options data for this date
            historical_data = self.options_data_service.get_historical_options_data(
                symbol=symbol, 
                snapshot_date=snapshot_date
            )
            
            if not historical_data or not historical_data.contracts:
                logger.debug(f"No historical options data for {symbol} on {snapshot_date}")
                return None
            
            # Find the most liquid contract (highest volume)
            liquid_contracts = [
                contract for contract in historical_data.contracts 
                if contract.get('volume', 0) > 0 and contract.get('close', 0) > 0
            ]
            
            if not liquid_contracts:
                logger.debug(f"No liquid options contracts for {symbol} on {snapshot_date}")
                return None
            
            # Get the most liquid contract
            most_liquid = max(liquid_contracts, key=lambda x: x.get('volume', 0))
            
            # Return the real options price
            real_price = most_liquid.get('close', 0)
            
            if real_price > 0:
                logger.debug(f"📊 Found real options price for {symbol}: ${real_price:.2f} on {snapshot_date}")
                return real_price
            else:
                logger.debug(f"Invalid options price for {symbol} on {snapshot_date}: {real_price}")
                return None
                
        except Exception as e:
            logger.debug(f"Error getting real options price for {symbol}: {e}")
            return None
        
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
        logger.info(f"🚀 Starting Comprehensive Backtesting Analysis")
        logger.info("=" * 60)
        logger.info(f"📊 Test Configuration:")
        logger.info(f"   Initial Capital: $100,000.00")
        logger.info(f"   Test Period: {start_date} to {end_date}")
        logger.info(f"   Symbols: {len(symbols)} stocks")
        logger.info(f"   Strategies: {', '.join(strategies)}")
        logger.info(f"   Data Source: {'Cached Real Market Data' if self.use_cache else 'Real Market Data' if self.use_real_data else 'Mock Data'}")
        
        # Get market data
        market_data = await self._get_market_data(symbols, start_date, end_date)
        
        if not market_data:
            logger.error("❌ No market data available for backtesting")
            return {}
        
        # Run backtests for each strategy
        results = {}
        for strategy_name in strategies:
            logger.info(f"🏃 Running backtest for {strategy_name} strategy...")
            strategy_results = await self._run_strategy_backtest(strategy_name, market_data)
            logger.info(f"🔍 DEBUG: {strategy_name} result type: {type(strategy_results)}")
            logger.info(f"🔍 DEBUG: {strategy_name} result value: {strategy_results}")
            results[strategy_name] = strategy_results
        
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
            if 'llm_performance' in llm_report:
                logger.info(f"   Total Signals Evaluated: {llm_report['llm_performance']['total_signals']}")
            else:
                logger.info(f"   LLM Performance: {llm_report}")
                if 'evaluations_summary' in llm_report:
                    logger.info(f"   LLM Approval Rate: {llm_report['evaluations_summary'].get('approval_rate', 'N/A')}")
                    logger.info(f"   LLM Accuracy: {llm_report['evaluations_summary'].get('accuracy', 'N/A')}")
                    logger.info(f"   Average Confidence: {llm_report['evaluations_summary'].get('average_confidence', 'N/A')}")
        
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
            # Include market regimes: bull (40%), bear (20%), sideways (40%)
            regime_length = len(date_range) // 3
            
            for i in range(1, len(date_range)):
                # Determine market regime
                if i < regime_length:
                    # Bull market - positive drift
                    mean_return = 0.0005
                    volatility = 0.015
                elif i < regime_length * 2:
                    # Bear market - negative drift
                    mean_return = -0.0003
                    volatility = 0.025
                else:
                    # Sideways - no drift, lower volatility
                    mean_return = 0.0
                    volatility = 0.012
                
                # Add occasional market shocks (5% chance)
                if np.random.random() < 0.05:
                    shock = np.random.normal(0, 0.05)  # 5% volatility shock
                    daily_return = shock
                else:
                    daily_return = np.random.normal(mean_return, volatility)
                
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
        
        # Calculate RSI
        df['RSI'] = self._calculate_rsi(close_series)
        
        # Calculate Simple Moving Averages
        df['SMA_20'] = close_series.rolling(window=20).mean()
        df['SMA_50'] = close_series.rolling(window=50).mean()
        
        # Calculate MACD
        exp1 = close_series.ewm(span=12).mean()
        exp2 = close_series.ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Calculate Bollinger Bands
        df['BB_Middle'] = close_series.rolling(window=20).mean()
        bb_std = close_series.rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # Remove NaN values from the beginning (where indicators can't be calculated)
        df = df.dropna()
        
        return df
    
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
            
            strategy = strategy_class()
            initial_capital = getattr(self, 'initial_capital', 1000.0)
            final_capital = initial_capital
            total_trades = 0
            winning_trades = 0
            losing_trades = 0
            trades = []
            equity_curve_data = []
            
            # Run backtest for each symbol with shared capital
            for symbol, data in market_data.items():
                logger.info(f"🔍 DEBUG: {strategy_name} - Processing symbol {symbol}")
                symbol_result = await self._backtest_symbol(strategy, symbol, data)
                if symbol_result:
                    logger.info(f"🔍 DEBUG: {strategy_name} - {symbol} result: {symbol_result}")
                    total_trades += symbol_result['trades']
                    trades.extend(symbol_result['trade_list'])
                    
                    # Calculate capital changes from individual symbol trades
                    for trade in symbol_result['trade_list']:
                        if trade['action'] == 'BUY':
                            final_capital -= trade['value']  # Spend money to buy shares
                        elif trade['action'] == 'SELL':
                            final_capital += trade['value']  # Receive money from sale
                            # Count winning/losing trades based on P&L
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
            total_return = final_capital - initial_capital
            total_return_pct = (total_return / initial_capital) * 100 if initial_capital > 0 else 0
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
            
            # Convert trades to BacktestTrade objects
            backtest_trades = []
            for trade in trades:
                backtest_trades.append(BacktestTrade(
                    timestamp=trade['date'],
                    symbol=trade.get('symbol', ''),
                    action=trade['action'],
                    quantity=trade['shares'],
                    price=trade['price'],
                    strategy=strategy_name,
                    pnl=trade.get('pnl', 0),
                    confidence=trade.get('confidence', 0.5),  # Default confidence if not available
                    portfolio_value=trade.get('portfolio_value', 0.0),  # Default portfolio value if not available
                    cash=trade.get('cash', 0.0),  # Default cash if not available
                    position_value=trade.get('position_value', 0.0),  # Default position value if not available
                    total_pnl=trade.get('total_pnl', 0.0),  # Default total P&L if not available
                    trade_pnl=trade.get('trade_pnl', 0.0)  # Default trade P&L if not available
                ))
            
            logger.info(f"🔍 DEBUG: {strategy_name} - Created {len(backtest_trades)} BacktestTrade objects")
            
            result = BacktestResult(
                strategy=strategy_name,
                initial_capital=initial_capital,
                final_capital=final_capital,
                total_return=total_return,
                total_return_pct=total_return_pct,
                max_drawdown_pct=max_drawdown_pct,
                sharpe_ratio=sharpe_ratio,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_win=avg_win,
                avg_loss=avg_loss,
                trades=backtest_trades,
                equity_curve=equity_curve,
                start_date=datetime.now(),  # Placeholder
                end_date=datetime.now()     # Placeholder
            )
            
            logger.info(f"🔍 DEBUG: {strategy_name} - Created BacktestResult object")
            logger.info(f"✅ {strategy_name}: {total_return_pct:.2f}% return, {total_trades} trades")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error running backtest for {strategy_name}: {str(e)}")
            logger.error(f"❌ Exception details: {traceback.format_exc()}")
            return None
    
    async def _backtest_symbol(self, strategy: BaseStrategy, symbol: str, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Run backtest for a single symbol with realistic transaction costs"""
        try:
            # Use the engine's initial capital if set, otherwise default to 10000
            initial_capital = getattr(self, 'initial_capital', 10000)
            current_capital = initial_capital
            
            # Calculate cash reserve (20% of initial capital)
            cash_reserve = initial_capital * 0.20
            max_tradeable_capital = initial_capital - cash_reserve
            
            position = 0
            position_cost_basis = 0.0  # Track average cost basis
            trades = []
            signals_generated = 0
            
            # Risk management parameters
            stop_loss_pct = 0.15  # 15% stop loss
            take_profit_pct = 0.30  # 30% take profit
            max_daily_loss_pct = 0.02  # 2% max daily loss
            daily_pnl = 0.0  # Track daily P&L
            
            logger.info(f"🔍 DEBUG: {symbol} - Initial capital: ${initial_capital:.2f}, Cash reserve: ${cash_reserve:.2f}, Max tradeable: ${max_tradeable_capital:.2f}")
            
            # Realistic trading costs (from paper_trading_strategies.yaml)
            commission_per_trade = 0.0  # Public.com is commission-free
            slippage = 0.0003  # 0.03% slippage
            spread_cost = 0.001  # 0.1% spread
            
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
                if len(current_data) < 20:  # Need minimum data for indicators
                    continue
                
                # Get the current date being simulated
                current_date = data_with_indicators.index[i]
                if hasattr(current_date, 'strftime'):
                    historical_date = current_date.strftime("%Y-%m-%d")
                else:
                    historical_date = str(current_date)
                
                # Check stop loss and take profit before generating new signals
                if position > 0:
                    current_price = data_with_indicators.iloc[i]['Close']
                    
                    # Check if this is an options trade (use last signal metadata)
                    is_options_trade = False
                    if hasattr(self, '_last_signal') and self._last_signal:
                        is_options_trade = (self._last_signal.metadata and 
                                          (self._last_signal.metadata.get('options_strategy') or 
                                           self._last_signal.metadata.get('active_strategy')))
                    
                    if is_options_trade:
                        # For options: use REAL market data instead of simulation
                        underlying_price = current_price
                        entry_price = position_cost_basis
                        
                        # Try to get real historical options data for this date
                        real_options_price = self._get_real_options_price(symbol, current_date, underlying_price)
                        
                        if real_options_price is not None:
                            # Use real market data
                            simulated_premium = real_options_price
                            logger.debug(f"📊 {symbol} - Using REAL options price: ${simulated_premium:.2f} on {current_date}")
                        else:
                            # Fallback to improved simulation if real data unavailable
                            logger.debug(f"📊 {symbol} - Using fallback options pricing for {current_date}")
                            
                            # Calculate price movement from entry
                            price_movement_pct = (underlying_price - entry_price * 100) / (entry_price * 100)
                            
                            # Delta effect: options move with underlying (typically 0.3-0.7 for ATM options)
                            delta = 0.5  # Assume 50% delta for simplicity
                            delta_effect = price_movement_pct * delta
                            
                            # Time decay: options lose value over time (simplified)
                            # Find the last BUY trade to calculate days held
                            days_held = 1  # Default
                            for trade in reversed(trades):
                                if trade['action'] == 'BUY' and trade['symbol'] == symbol:
                                    days_held = (current_date - trade['date']).days
                                    break
                            theta_decay = -0.02 * days_held  # 2% decay per day (simplified)
                            
                            # Volatility effect: assume some volatility changes
                            volatility_effect = np.random.normal(0, 0.05)  # Reduced volatility (more realistic)
                            
                            # Combine all effects
                            total_effect = delta_effect + theta_decay + volatility_effect
                            
                            # Calculate new premium
                            simulated_premium = entry_price * (1 + total_effect)
                            
                            # Ensure realistic premium bounds (not too low, not too high)
                            simulated_premium = max(entry_price * 0.2, min(entry_price * 2.0, simulated_premium))
                        
                        position_pnl_pct = (simulated_premium - position_cost_basis) / position_cost_basis
                        current_price = simulated_premium  # Use premium for trade execution
                    else:
                        # For stocks: normal price-based P&L calculation
                        position_pnl_pct = (current_price - position_cost_basis) / position_cost_basis
                    
                    # Let the strategy handle all exit logic - no engine-level stop loss/take profit
                    # The strategy has sophisticated patient exit logic that should be respected
                    # Skip engine-level exit checks and let strategy generate exit signals
                
                # Generate signal with historical date
                signal = await strategy.generate_signal(symbol, current_data, historical_date)
                
                if signal:
                    signals_generated += 1
                    # Track the last signal for options trade detection
                    self._last_signal = signal
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
                        # Calculate available cash (current capital minus cash reserve)
                        available_cash = current_capital - cash_reserve
                        
                        # Buy signal - use strategy's quantity or calculate based on available cash
                        if hasattr(signal, 'quantity') and signal.quantity > 0:
                            # Use strategy's specified quantity
                            shares_to_buy = signal.quantity
                            
                            trade_value = shares_to_buy * signal.price
                            
                            # Check if we have enough cash (including reserve)
                            if trade_value > available_cash:
                                logger.warning(f"⚠️ {symbol} - Insufficient cash for trade: need ${trade_value:.2f}, available ${available_cash:.2f} (reserve: ${cash_reserve:.2f})")
                                continue
                            
                            # Check minimum trade value (at least $10)
                            if trade_value < 10:
                                logger.warning(f"⚠️ {symbol} - Trade value too small: ${trade_value:.2f} (minimum $10)")
                                continue
                        else:
                            # Fallback: calculate based on available cash
                            shares_to_buy = available_cash // signal.price
                            if shares_to_buy <= 0:
                                logger.warning(f"⚠️ {symbol} - Insufficient cash for trade: need ${signal.price:.2f}, available ${available_cash:.2f} (reserve: ${cash_reserve:.2f})")
                                continue
                            trade_value = shares_to_buy * signal.price
                        
                        # Update position and cost basis
                        if position == 0:
                            # New position
                            position = shares_to_buy
                            position_cost_basis = signal.price
                        else:
                            # Add to existing position (average cost basis)
                            total_shares = position + shares_to_buy
                            total_cost = (position * position_cost_basis) + trade_value
                            position_cost_basis = total_cost / total_shares
                            position = total_shares
                        
                        current_capital -= trade_value
                        
                        logger.info(f"🔍 DEBUG: {symbol} - BUY trade: {shares_to_buy} shares at ${signal.price:.2f}, remaining cash: ${current_capital:.2f} (reserve: ${cash_reserve:.2f})")
                        
                        trades.append({
                            'date': signal.timestamp,
                            'symbol': symbol,  # Add symbol to trade
                            'action': 'BUY',
                            'price': signal.price,
                            'shares': shares_to_buy,
                            'value': trade_value,
                            'pnl': 0,
                            'llm_evaluation': evaluation if self.use_llm_evaluation else None
                        })
                        
                        # Update strategy's capital estimation
                        if hasattr(strategy, 'update_capital_estimation'):
                            strategy.update_capital_estimation(trade_value, 0)
                        logger.info(f"🔍 DEBUG: {symbol} - BUY trade: {shares_to_buy} shares at ${signal.price:.2f}")
                    
                    elif signal.action == 'SELL' and position > 0:
                        # Sell signal
                        trade_value = position * signal.price
                        
                        # Check if this is an options trade
                        is_options_trade = (signal.metadata and 
                                          (signal.metadata.get('options_strategy') or 
                                           signal.metadata.get('active_strategy')))
                        
                        if is_options_trade:
                            # For options: P&L = contracts * (exit_premium - entry_premium)
                            pnl = position * (signal.price - position_cost_basis)
                        else:
                            # For stocks: P&L = shares * (exit_price - entry_price)
                            pnl = trade_value - (position * position_cost_basis)
                        
                        current_capital += trade_value
                        
                        trades.append({
                            'date': signal.timestamp,
                            'symbol': symbol,  # Add symbol to trade
                            'action': 'SELL',
                            'price': signal.price,
                            'shares': position,
                            'value': trade_value,
                            'pnl': pnl,
                            'llm_evaluation': evaluation if self.use_llm_evaluation else None
                        })
                        
                        # Update strategy's capital estimation with actual P&L
                        if hasattr(strategy, 'update_capital_estimation'):
                            strategy.update_capital_estimation(trade_value, pnl)
                        logger.info(f"🔍 DEBUG: {symbol} - SELL trade: {position} shares at ${signal.price:.2f}, P&L: ${pnl:.2f}")
                        
                        # Update LLM performance if evaluation was used
                        if self.use_llm_evaluation and len(trades) >= 2:
                            signal_id = f"{symbol}_{signal.timestamp.strftime('%Y%m%d_%H%M%S')}"
                            self.trade_evaluator.update_performance(signal_id, pnl)
                        
                        position = 0
                        position_cost_basis = 0.0
            
            # Close any remaining position
            if position > 0:
                final_price = data_with_indicators.iloc[-1]['Close']
                final_value = position * final_price
                
                # Check if this is an options trade
                is_options_trade = False
                if hasattr(self, '_last_signal') and self._last_signal:
                    is_options_trade = (self._last_signal.metadata and 
                                      (self._last_signal.metadata.get('options_strategy') or 
                                       self._last_signal.metadata.get('active_strategy')))
                
                if is_options_trade:
                    final_pnl = position * (final_price - position_cost_basis)
                else:
                    final_pnl = final_value - (position * position_cost_basis)
                
                current_capital += final_value
                logger.info(f"🔍 DEBUG: {symbol} - Closing position: {position} shares at ${final_price:.2f}, P&L: ${final_pnl:.2f}")
            
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
        strategy_map = self._get_strategy_mapping()
        
        if strategy_name not in strategy_map:
            return None
        
        try:
            module_path, class_name = strategy_map[strategy_name].rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Error importing strategy {strategy_name}: {str(e)}")
            return None
    
    def _get_strategy_mapping(self) -> Dict[str, str]:
        """Get dynamic strategy mapping from registry"""
        try:
            registry = get_strategy_registry()
            
            # Discover strategies if not already done
            if not registry.discovered:
                discover_strategies()
            
            # Get all strategies
            strategies = registry.get_all_strategies()
            
            # Build mapping (strategy_name -> module_path)
            mapping = {}
            for strategy_name, strategy_class in strategies.items():
                mapping[strategy_name] = f"{strategy_class.__module__}.{strategy_class.__name__}"
            
            logger.info(f"📊 Dynamic strategy mapping created with {len(mapping)} strategies")
            return mapping
            
        except Exception as e:
            logger.error(f"Error creating dynamic strategy mapping: {e}")
            # Fallback to hardcoded mapping
            return {
                'BollingerBands': 'src.strategies.bollinger_bands_strategy.BollingerBandsStrategy',
                'RSI': 'src.strategies.rsi_strategy.RSIStrategy',
                'MACD': 'src.strategies.macd_strategy.MACDStrategy',
                'SMACrossover': 'src.strategies.momentum.sma_crossover_strategy.SMACrossoverStrategy',
                'MeanReversion': 'src.strategies.mean_reversion.mean_reversion_strategy.MeanReversionStrategy',
                'Momentum': 'src.strategies.momentum.momentum_strategy.MomentumStrategy',
                'VolatilityBreakout': 'src.strategies.breakout.volatility_breakout_strategy.VolatilityBreakoutStrategy',
                'TrailingStop': 'src.strategies.advanced.trailing_stop_strategy.TrailingStopStrategy',
                'Fibonacci': 'src.strategies.advanced.fibonacci_strategy.FibonacciStrategy',
                'GreeksEnhanced': 'src.strategies.options.greeks_enhanced_strategy.GreeksEnhancedStrategy',
                'Ichimoku': 'src.strategies.ichimoku_strategy.IchimokuStrategy',
                'IchimokuEnhanced': 'src.strategies.ichimoku_enhanced_strategy.IchimokuEnhancedStrategy',
                'AdaptiveMomentum': 'src.strategies.adaptive_momentum_strategy.AdaptiveMomentumStrategy',
                'NeuralNetwork': 'src.strategies.neural_network_strategy.NeuralNetworkStrategy',
                'QuantumMomentum': 'src.strategies.quantum_momentum_strategy.QuantumMomentumStrategy',
                'RegimeSwitching': 'src.strategies.regime_switching_strategy.RegimeSwitchingStrategy',
                'IronCondor': 'src.strategies.options.iron_condor_strategy.IronCondorStrategy',
                'EnhancedIronCondor': 'src.strategies.options.enhanced_iron_condor_strategy.EnhancedIronCondorStrategy',
                'VWAP': 'src.strategies.vwap_strategy.VWAPStrategy',
                'PairsTrading': 'src.strategies.pairs_trading_strategy.PairsTradingStrategy',
                'KalmanFilter': 'src.strategies.kalman_filter_strategy.KalmanFilterStrategy',
                'MLEnsemble': 'src.strategies.ml_ensemble_strategy.MLEnsembleStrategy',
                'EnhancedDayTrading': 'src.strategies.enhanced_day_trading_strategy.EnhancedDayTradingStrategy',
                'NewsEnhanced': 'src.strategies.news_enhanced_strategy.NewsEnhancedStrategy',
                'SocialMediaSentiment': 'src.strategies.social_media_sentiment_strategy.SocialMediaSentimentStrategy',
                'CashSecuredPut': 'src.strategies.options.cash_secured_put_strategy.CashSecuredPutStrategy',
                'CoveredCall': 'src.strategies.options.covered_call_strategy.CoveredCallStrategy',
                'CalendarSpread': 'src.strategies.options.calendar_spread_strategy.CalendarSpreadStrategy',
                'ButterflySpread': 'src.strategies.options.butterfly_spread_strategy.ButterflySpreadStrategy',
                'BullishDiagonal': 'src.strategies.options.bullish_diagonal_strategy.BullishDiagonalStrategy',
                'BearishDiagonal': 'src.strategies.options.bearish_diagonal_strategy.BearishDiagonalStrategy',
                'VolatilityStrategy': 'src.strategies.volatility_strategy.VolatilityStrategy',
                'Straddle': 'src.strategies.options.straddle_strategy.StraddleStrategy',
                'LongStrangle': 'src.strategies.options.long_strangle_strategy.LongStrangleStrategy',
                'ShortStrangle': 'src.strategies.options.short_strangle_strategy.ShortStrangleStrategy',
                'EarningsStrategy': 'src.strategies.options.earnings_strategy.EarningsStrategy',
                'EnhancedExit': 'src.strategies.advanced_exit_strategies.EnhancedExitStrategy',
                'AdvancedExit': 'src.strategies.advanced_exit_strategies.AdvancedExitStrategy',
                'PortfolioStrategy': 'src.strategies.portfolio_strategy.PortfolioStrategy',
                'CrossSectionalMomentum': 'src.strategies.cross_sectional_momentum_strategy.CrossSectionalMomentumStrategy',
                'WinningEnsemble': 'src.strategies.winning_ensemble_strategy.WinningEnsembleStrategy',
                # Add new strategies
                'RiskFirst': 'src.strategies.risk_first_strategy.RiskFirstStrategy',
                'MarketRegimeAdaptive': 'src.strategies.market_regime_adaptive_strategy.MarketRegimeAdaptiveStrategy',
                'MultiTimeframe': 'src.strategies.multi_timeframe_strategy.MultiTimeframeStrategy'
            }
    
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
        current_value = 100000  # Initial capital
        
        for trade in trades:
            pnl = trade.get('pnl', 0)
            current_value += pnl
            portfolio_values.append(current_value)
        
        if not portfolio_values:
            return 0.0
        
        # Calculate drawdown as percentage
        peak = portfolio_values[0]
        max_drawdown_pct = 0.0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            
            drawdown_pct = ((peak - value) / peak) * 100 if peak > 0 else 0
            if drawdown_pct > max_drawdown_pct:
                max_drawdown_pct = drawdown_pct
        
        return max_drawdown_pct
    
    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
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
                    strategy_name=strategy_name,
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