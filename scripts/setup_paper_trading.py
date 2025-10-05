#!/usr/bin/env python3
"""
Paper Trading Setup Script
This script runs the actual paper trading logic in the background
"""
import asyncio
import logging
import time
import random
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import real strategy classes
try:
    from src.strategies.base import BaseStrategy
    from src.strategies.advanced.adaptive_sector_wave_strategy import AdaptiveSectorWaveStrategy
    from src.strategies.hybrid_ichimoku_strategy import HybridIchimokuStrategy
    from src.strategies.advanced.elliott_wave_corrective_strategy import ElliottWaveCorrectiveStrategy
    from src.strategies.advanced.elliott_wave_impulse_strategy import ElliottWaveImpulseStrategy
    from src.strategies.momentum.rsi_strategy import RSIStrategy
    from src.strategies.momentum.macd_strategy import MACDStrategy
    from src.strategies.momentum.momentum_strategy import MomentumStrategy
    from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy
    from src.strategies.options.cash_secured_put_strategy import CashSecuredPutStrategy
    from src.core.types import TradeSignal
    REAL_STRATEGIES_AVAILABLE = True
    print("✅ Real strategy classes imported successfully")
except ImportError as e:
    print(f"⚠️ Real strategies not available: {e}")
    import traceback
    traceback.print_exc()
    REAL_STRATEGIES_AVAILABLE = False
    BaseStrategy = None
    TradeSignal = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PaperTradingEngine:
    """Enhanced paper trading engine that can use real strategies"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.portfolio_value = config.get('initial_capital', 100000.0)
        self.total_trades = 0
        self.total_pnl = 0.0
        self.trades = []
        self.strategy_names = config.get('strategies', ['AdaptiveSectorWaveStrategy', 'RSIStrategy', 'MACDStrategy'])
        self.symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'])
        self.trading_interval = config.get('trading_interval', 3600)
        self.is_running = True
        
        # Real strategy instances
        self.strategy_instances = {}
        self.use_real_strategies = config.get('use_real_strategies', True) and REAL_STRATEGIES_AVAILABLE
        
        # Advanced capital allocation parameters
        self.allocated_capital = 0.0  # Capital tied up in positions
        self.available_capital = self.portfolio_value
        self.max_portfolio_utilization = config.get('max_portfolio_utilization', 0.80)  # Use max 80% of portfolio
        self.min_cash_reserve = config.get('min_cash_reserve', 0.20)  # Keep 20% in cash
        self.max_position_size = config.get('max_position_size', 0.15)  # Max 15% per position
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.05)  # Max 5% risk per trade
        
        # Hybrid allocation parameters
        self.hybrid_allocation = config.get('hybrid_allocation', {})
        self.use_hybrid_allocation = self.hybrid_allocation.get('enabled', False)
        
        if self.use_hybrid_allocation:
            self.cash_reserve_pct = self.hybrid_allocation.get('cash_reserve_pct', 0.20)
            self.stock_allocation_pct = self.hybrid_allocation.get('stock_allocation_pct', 0.20)
            self.options_allocation_pct = self.hybrid_allocation.get('options_allocation_pct', 0.60)
            
            # Calculate allocation amounts
            self.cash_reserve = self.portfolio_value * self.cash_reserve_pct
            self.stock_capital = self.portfolio_value * self.stock_allocation_pct
            self.options_capital = self.portfolio_value * self.options_allocation_pct
            
            # Track allocations
            self.allocated_stock_capital = 0.0
            self.allocated_options_capital = 0.0
            self.available_stock_capital = self.stock_capital
            self.available_options_capital = self.options_capital
            
            logger.info(f"🎯 Hybrid Capital Allocation Enabled:")
            logger.info(f"   💵 Cash Reserve ({self.cash_reserve_pct:.0%}): ${self.cash_reserve:,.2f}")
            logger.info(f"   📈 Stock Allocation ({self.stock_allocation_pct:.0%}): ${self.stock_capital:,.2f}")
            logger.info(f"   🎯 Options Allocation ({self.options_allocation_pct:.0%}): ${self.options_capital:,.2f}")
        
        # Dynamic sizing parameters
        self.capital_efficiency_threshold = config.get('capital_efficiency_threshold', 0.70)  # Increase sizing when utilization > 70%
        self.capital_scarcity_threshold = config.get('capital_scarcity_threshold', 0.30)  # Decrease sizing when utilization < 30%
        
        if self.use_real_strategies:
            self._initialize_real_strategies()
        else:
            logger.warning("⚠️ Using fallback simulation strategies")
        
        # Trade limits
        self.max_daily_trades = config.get('max_daily_trades', 4)
        self.max_weekly_trades = config.get('max_weekly_trades', 6)
        self.max_monthly_trades = config.get('max_monthly_trades', 8)
        
        # Trade counters
        self.daily_trades = 0
        self.weekly_trades = 0
        self.monthly_trades = 0
        self.last_reset_day = datetime.now().day
        self.last_reset_week = datetime.now().isocalendar()[1]
        self.last_reset_month = datetime.now().month
        
        # Strategy performance tracking
        self.strategy_performance = {strategy: {
            'trades': 0,
            'pnl': 0.0,
            'win_rate': 0.0,
            'wins': 0,
            'losses': 0
        } for strategy in self.strategy_names}
        
        logger.info(f"🚀 Paper Trading Engine initialized with {len(self.strategy_names)} strategies")
        logger.info(f"📊 Portfolio: ${self.portfolio_value:,.2f}")
        logger.info(f"🎯 Symbols: {', '.join(self.symbols)}")
        logger.info(f"⏱️ Trading interval: {self.trading_interval} seconds ({self.trading_interval/60:.0f} minutes)")
        logger.info(f"🧠 Using real strategies: {self.use_real_strategies}")
        logger.info(f"📈 Trade limits: {self.max_daily_trades}/day, {self.max_weekly_trades}/week, {self.max_monthly_trades}/month")
    
    def _initialize_real_strategies(self):
        """Initialize real strategy instances"""
        strategy_classes = {
            'AdaptiveSectorWaveStrategy': AdaptiveSectorWaveStrategy,
            'HybridIchimokuStrategy': HybridIchimokuStrategy,
            'ElliottWaveCorrectiveStrategy': ElliottWaveCorrectiveStrategy,
            'ElliottWaveImpulseStrategy': ElliottWaveImpulseStrategy,
            'RSIStrategy': RSIStrategy,
            'MACDStrategy': MACDStrategy,
            'BollingerBandsStrategy': BollingerBandsStrategy,
            'MomentumStrategy': MomentumStrategy,
            'CashSecuredPutStrategy': CashSecuredPutStrategy,
        }
        
        # Get strategy options from config
        strategy_options = self.config.get('strategy_options', {})
        
        for strategy_name in self.strategy_names:
            if strategy_name in strategy_classes:
                # Check if strategy is enabled
                strategy_config = strategy_options.get(strategy_name, {})
                if not strategy_config.get('enabled', True):
                    logger.info(f"⏭️ Skipping disabled strategy: {strategy_name}")
                    continue
                    
                try:
                    strategy_class = strategy_classes[strategy_name]
                    self.strategy_instances[strategy_name] = strategy_class()
                    logger.info(f"✅ Initialized {strategy_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize {strategy_name}: {e}")
            else:
                logger.warning(f"⚠️ Unknown strategy: {strategy_name}")
        
        logger.info(f"🎯 Active strategies: {list(self.strategy_instances.keys())}")
    
    def calculate_available_capital(self) -> float:
        """Calculate available capital for new positions"""
        return max(0, self.portfolio_value - self.allocated_capital - (self.portfolio_value * self.min_cash_reserve))
    
    def can_open_new_position(self) -> bool:
        """Check if we can open a new position based on capital allocation"""
        available_capital = self.calculate_available_capital()
        utilization = self.allocated_capital / self.portfolio_value if self.portfolio_value > 0 else 1.0
        
        return (
            available_capital > 0 and 
            utilization < self.max_portfolio_utilization and
            len(self.trades) < self.max_daily_trades  # Also check daily trade limits
        )
    
    def calculate_advanced_position_size(self, symbol: str, price: float, strategy: str) -> int:
        """Calculate position size using advanced capital allocation techniques"""
        if price <= 0:
            return 0
        
        available_capital = self.calculate_available_capital()
        
        if available_capital <= 0:
            logger.warning(f"⚠️ No available capital for {symbol} {strategy}")
            return 0
        
        # Base position sizing
        max_position_value = min(
            self.portfolio_value * self.max_position_size,
            available_capital * 0.5  # Use max 50% of available capital
        )
        
        max_risk_value = self.portfolio_value * self.max_risk_per_trade
        
        # Calculate max shares
        max_shares_position = int(max_position_value / price)
        max_shares_risk = int(max_risk_value / price)
        
        max_shares = min(max_shares_position, max_shares_risk)
        
        # More aggressive minimum - allow smaller positions
        if max_shares < 1 and price < available_capital * 0.1:
            max_shares = 1
        
        if max_shares < 1:
            logger.warning(f"⚠️ Position too small for {symbol} {strategy}")
            return 0
        
        # Dynamic sizing based on capital utilization
        utilization = self.allocated_capital / self.portfolio_value
        
        if utilization > self.capital_efficiency_threshold:
            shares = random.randint(1, min(max_shares, 2))
        elif utilization < self.capital_scarcity_threshold:
            shares = random.randint(1, min(max_shares, 4))
        else:
            shares = random.randint(1, min(max_shares, 3))
        
        return shares
    
    def calculate_public_com_costs(self, trade_type: str, contracts: int = 0, trade_value: float = 0.0) -> Dict[str, float]:
        """
        Calculate Public.com specific costs and rebates
        
        Args:
            trade_type: 'STOCK' or 'OPTIONS'
            contracts: Number of options contracts (for options trades)
            trade_value: Total trade value (for stock trades)
        
        Returns:
            Dict with cost breakdown
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
            # Commission-free stock trading
            costs['commission'] = 0.0
            costs['slippage'] = trade_value * 0.0003  # 0.03% slippage
            costs['spread_cost'] = trade_value * 0.001  # 0.1% spread cost
            
        elif trade_type == 'OPTIONS':
            # Options trading with rebates
            costs['commission'] = 0.0  # Commission-free
            costs['options_rebate'] = contracts * 0.06  # $0.06 per contract rebate
            costs['slippage'] = trade_value * 0.0003  # 0.03% slippage
            costs['spread_cost'] = trade_value * 0.001  # 0.1% spread cost
        
        # Calculate totals
        costs['total_cost'] = costs['commission'] + costs['slippage'] + costs['spread_cost']
        costs['net_cost'] = costs['total_cost'] - costs['options_rebate']
        
        return costs
    
    def track_public_com_metrics(self, trade: Dict):
        """Track Public.com specific metrics for quality analysis"""
        if not hasattr(self, 'public_com_metrics'):
            self.public_com_metrics = {
                'total_contracts': 0,
                'total_rebates': 0.0,
                'monthly_contracts': 0,
                'quality_trades': 0,
                'total_trades': 0,
                'rebate_tier': 'Bronze'  # Bronze, Silver, Gold, Tier 4
            }
        
        # Update contract count for options trades
        if trade.get('strategy') == 'CashSecuredPutStrategy':
            contracts = trade.get('quantity', 0)  # Assuming quantity = contracts for options
            self.public_com_metrics['total_contracts'] += contracts
            self.public_com_metrics['monthly_contracts'] += contracts
            
            # Calculate rebate
            rebate = contracts * 0.06
            self.public_com_metrics['total_rebates'] += rebate
        
        # Update trade quality metrics
        self.public_com_metrics['total_trades'] += 1
        if trade.get('pnl', 0) > 0:
            self.public_com_metrics['quality_trades'] += 1
        
        # Update rebate tier
        monthly_contracts = self.public_com_metrics['monthly_contracts']
        if monthly_contracts >= 1000:
            self.public_com_metrics['rebate_tier'] = 'Tier 4'
        elif monthly_contracts >= 500:
            self.public_com_metrics['rebate_tier'] = 'Gold'
        elif monthly_contracts >= 100:
            self.public_com_metrics['rebate_tier'] = 'Silver'
        else:
            self.public_com_metrics['rebate_tier'] = 'Bronze'
    
    def get_public_com_summary(self) -> Dict:
        """Get Public.com metrics summary"""
        if not hasattr(self, 'public_com_metrics'):
            return {'message': 'No Public.com metrics available yet'}
        
        metrics = self.public_com_metrics
        quality_rate = (metrics['quality_trades'] / max(1, metrics['total_trades'])) * 100
        
        return {
            'rebate_tier': metrics['rebate_tier'],
            'monthly_contracts': metrics['monthly_contracts'],
            'total_rebates': f"${metrics['total_rebates']:.2f}",
            'quality_rate': f"{quality_rate:.1f}%",
            'total_trades': metrics['total_trades'],
            'quality_trades': metrics['quality_trades'],
            'next_tier_threshold': self._get_next_tier_threshold(metrics['monthly_contracts'])
        }
    
    def _get_next_tier_threshold(self, current_contracts: int) -> str:
        """Get next tier threshold information"""
        if current_contracts < 100:
            return f"Silver: {100 - current_contracts} contracts to go"
        elif current_contracts < 500:
            return f"Gold: {500 - current_contracts} contracts to go"
        elif current_contracts < 1000:
            return f"Tier 4: {1000 - current_contracts} contracts to go"
        else:
            return "Tier 4 achieved! 🎉"
    
    async def run(self):
        """Main paper trading loop"""
        logger.info("🚀 Starting paper trading engine...")
        
        while self.is_running:
            try:
                # Generate a trade
                trade_generated = await self.generate_trade()
                
                # Only update portfolio if a trade was actually generated
                if trade_generated:
                self.update_portfolio()
                
                # Log status
                logger.info(f"📊 Portfolio: ${self.portfolio_value:,.2f} | Trades: {self.total_trades} | P&L: ${self.total_pnl:,.2f}")
                
                # Wait for next trading cycle
                await asyncio.sleep(self.trading_interval)
                
            except Exception as e:
                logger.error(f"Error in paper trading loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def _check_and_reset_trade_limits(self):
        """Check and reset trade limits based on time periods"""
        now = datetime.now()
        current_day = now.day
        current_week = now.isocalendar()[1]
        current_month = now.month
        
        # Reset daily counter
        if current_day != self.last_reset_day:
            self.daily_trades = 0
            self.last_reset_day = current_day
            logger.info(f"🔄 Daily trade counter reset")
        
        # Reset weekly counter
        if current_week != self.last_reset_week:
            self.weekly_trades = 0
            self.last_reset_week = current_week
            logger.info(f"🔄 Weekly trade counter reset")
        
        # Reset monthly counter
        if current_month != self.last_reset_month:
            self.monthly_trades = 0
            self.last_reset_month = current_month
            logger.info(f"🔄 Monthly trade counter reset")
    
    def _can_trade(self) -> bool:
        """Check if we can execute a trade based on limits"""
        self._check_and_reset_trade_limits()
        
        if self.daily_trades >= self.max_daily_trades:
            logger.info(f"⏸️ Daily trade limit reached ({self.daily_trades}/{self.max_daily_trades})")
            return False
        
        if self.weekly_trades >= self.max_weekly_trades:
            logger.info(f"⏸️ Weekly trade limit reached ({self.weekly_trades}/{self.max_weekly_trades})")
            return False
        
        if self.monthly_trades >= self.max_monthly_trades:
            logger.info(f"⏸️ Monthly trade limit reached ({self.monthly_trades}/{self.max_monthly_trades})")
            return False
        
        return True
    
    async def generate_trade(self):
        """Generate a trade using real strategies or fallback simulation"""
        if not self.is_running:
            return False
        
        # Check trade limits
        if not self._can_trade():
            return False
        
        if self.use_real_strategies:
            return await self._generate_real_strategy_trade()
        else:
            return await self._generate_simulated_trade()
    
    async def _generate_real_strategy_trade(self):
        """Generate trade using real strategy instances with advanced capital allocation"""
        try:
            # Check if we can open a new position
            if not self.can_open_new_position():
                logger.info(f"📊 Cannot open new position - Available capital: ${self.calculate_available_capital():.2f}, Utilization: {(self.allocated_capital/self.portfolio_value)*100:.1f}%")
                return False
            
            # Randomly select a strategy and symbol
            strategy_name = random.choice(self.strategy_names)
            symbol = random.choice(self.symbols)
            
            if strategy_name not in self.strategy_instances:
                logger.warning(f"⚠️ Strategy {strategy_name} not initialized, skipping")
                return False
            
            strategy = self.strategy_instances[strategy_name]
            
            # Generate realistic market data for the strategy
            market_data = self._generate_market_data(symbol)
            
            # Get signal from real strategy
            signal = await strategy.generate_signal(symbol, market_data)
            
            if signal and signal.action in ['BUY', 'SELL']:
                # Use advanced capital allocation for position sizing
                if signal.action == 'BUY':
                    # Override quantity with advanced position sizing
                    advanced_quantity = self.calculate_advanced_position_size(symbol, signal.price, strategy_name)
                    if advanced_quantity <= 0:
                        logger.info(f"⏭️ Position too small for {symbol} {strategy_name}")
                        return False
                    signal.quantity = advanced_quantity
                
                # Execute the trade
                trade = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': signal.action,
                    'quantity': signal.quantity,
                    'price': signal.price,
                    'strategy': strategy_name,
                    'confidence': signal.confidence,
                    'pnl': self._calculate_real_pnl(signal),
                    'portfolio_value': self.portfolio_value,
                    'trade_id': f"PT_{int(time.time())}_{random.randint(1000, 9999)}",
                    'metadata': signal.metadata,
                    'capital_utilization': (self.allocated_capital / self.portfolio_value) * 100
                }
                
                # Calculate Public.com costs and rebates
                trade_value = signal.quantity * signal.price
                trade_type = 'OPTIONS' if strategy_name == 'CashSecuredPutStrategy' else 'STOCK'
                contracts = signal.quantity if trade_type == 'OPTIONS' else 0
                
                public_com_costs = self.calculate_public_com_costs(trade_type, contracts, trade_value)
                trade['public_com_costs'] = public_com_costs
                trade['net_cost'] = public_com_costs['net_cost']
                
                # Track Public.com metrics
                self.track_public_com_metrics(trade)
                
                # Update capital allocation
                if signal.action == 'BUY':
                    self.allocated_capital += signal.quantity * signal.price
                elif signal.action == 'SELL':
                    self.allocated_capital = max(0, self.allocated_capital - signal.quantity * signal.price)
                
                # Add to trades list
                self.trades.append(trade)
                self.total_trades += 1
                self.total_pnl += trade['pnl']
                
                # Increment trade counters
                self.daily_trades += 1
                self.weekly_trades += 1
                self.monthly_trades += 1
                
                # Update strategy performance
                self.update_strategy_performance(strategy_name, trade['pnl'])
                
                logger.info(f"🧠 Real Strategy Trade: {signal.action} {signal.quantity} {symbol} @ ${signal.price:.2f} | P&L: ${trade['pnl']:.2f} | Strategy: {strategy_name} | Confidence: {signal.confidence:.2f}")
                logger.info(f"💰 Capital: Allocated ${self.allocated_capital:.2f} ({trade['capital_utilization']:.1f}%) | Available: ${self.calculate_available_capital():.2f}")
                logger.info(f"📊 Trade counts: Daily {self.daily_trades}/{self.max_daily_trades}, Weekly {self.weekly_trades}/{self.max_weekly_trades}, Monthly {self.monthly_trades}/{self.max_monthly_trades}")
                
                # Log Public.com specific information
                if trade_type == 'OPTIONS' and public_com_costs['options_rebate'] > 0:
                    logger.info(f"🏦 Public.com: Options rebate ${public_com_costs['options_rebate']:.2f} | Net cost: ${public_com_costs['net_cost']:.4f}")
                elif trade_type == 'STOCK':
                    logger.info(f"🏦 Public.com: Commission-free stock trade | Net cost: ${public_com_costs['net_cost']:.4f}")
                
                # Log Public.com metrics summary every 5 trades
                if self.total_trades % 5 == 0:
                    summary = self.get_public_com_summary()
                    logger.info(f"📈 Public.com Summary: {summary['rebate_tier']} tier | {summary['monthly_contracts']} contracts | {summary['total_rebates']} rebates | {summary['quality_rate']} quality")
                return True
            else:
                logger.info(f"🔍 {strategy_name} generated no signal for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error generating real strategy trade: {e}")
            return False
    
    async def _generate_simulated_trade(self):
        """Generate a simulated trade with proper position sizing (fallback)"""
        # Randomly select a strategy and symbol
        strategy = random.choice(self.strategy_names)
        symbol = random.choice(self.symbols)
        
        # Generate trade parameters with proper position sizing
        action = random.choice(['BUY', 'SELL'])
        price = self.get_simulated_price(symbol)
        
        # Calculate proper position size based on portfolio value
        quantity = self.calculate_position_size(symbol, price, strategy)
        
        # Skip trade if position size is too small
        if quantity < 1:
            logger.info(f"⏭️ Skipping trade: position size too small for {symbol}")
            return False
        
        # Calculate P&L (simplified)
        pnl = self.calculate_pnl(action, quantity, price)
        
        # Create trade record
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'strategy': strategy,
            'pnl': pnl,
            'portfolio_value': self.portfolio_value,
            'trade_id': f"PT_{int(time.time())}_{random.randint(1000, 9999)}"
        }
        
        # Add to trades list
        self.trades.append(trade)
        self.total_trades += 1
        self.total_pnl += pnl
        
        # Increment trade counters
        self.daily_trades += 1
        self.weekly_trades += 1
        self.monthly_trades += 1
        
        # Update strategy performance
        self.update_strategy_performance(strategy, pnl)
        
        logger.info(f"📈 Simulated Trade: {action} {quantity} {symbol} @ ${price:.2f} | P&L: ${pnl:.2f} | Strategy: {strategy}")
        logger.info(f"📊 Trade counts: Daily {self.daily_trades}/{self.max_daily_trades}, Weekly {self.weekly_trades}/{self.max_weekly_trades}, Monthly {self.monthly_trades}/{self.max_monthly_trades}")
        return True
    
    def _generate_market_data(self, symbol: str) -> pd.DataFrame:
        """Generate realistic market data for strategy analysis"""
        import pandas as pd
        import numpy as np
        
        # Generate 100 days of realistic price data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        
        # Base price for different symbols
        base_prices = {
            'AAPL': 150.0, 'MSFT': 300.0, 'GOOGL': 2500.0, 
            'TSLA': 200.0, 'NVDA': 400.0, 'SPY': 400.0, 'QQQ': 350.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        prices = [base_price]
        
        # Generate realistic price movements
        for i in range(1, 100):
            daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% std
            prices.append(prices[-1] * (1 + daily_return))
        
        # Create DataFrame with required columns
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
        return data
    
    def _calculate_real_pnl(self, signal: TradeSignal) -> float:
        """Calculate P&L for real strategy trades"""
        # Simplified P&L calculation - in real implementation this would be more complex
        if signal.action == 'BUY':
            # Simulate profit/loss based on confidence
            base_return = (signal.confidence - 0.5) * 0.1  # -5% to +5% based on confidence
            return signal.quantity * signal.price * base_return
        else:  # SELL
            # Simulate profit/loss for exit
            base_return = np.random.normal(0.02, 0.05)  # Random exit return
            return signal.quantity * signal.price * base_return
    
    def calculate_position_size(self, symbol: str, price: float, strategy: str) -> int:
        """Calculate proper position size based on portfolio value and risk management"""
        
        # Get max position size from config (default 12%)
        max_position_size = self.config.get('max_position_size', 0.12)
        max_risk_per_trade = self.config.get('max_risk_per_trade', 0.05)  # Increased to 5% for small portfolios
        
        # Calculate maximum position value (12% of portfolio)
        max_position_value = self.portfolio_value * max_position_size
        
        # Calculate maximum shares based on position size
        max_shares_by_position = int(max_position_value / price) if price > 0 else 0
        
        # Calculate maximum shares based on risk per trade (1.5% risk)
        max_risk_value = self.portfolio_value * max_risk_per_trade
        max_shares_by_risk = int(max_risk_value / price) if price > 0 else 0
        
        # Use the smaller of the two limits
        max_shares = min(max_shares_by_position, max_shares_by_risk)
        
        # Ensure minimum viable position (at least $50 for small portfolios)
        min_position_value = 50.0
        min_shares = int(min_position_value / price) if price > 0 else 0
        
        # Randomly select quantity between min and max (with some variation)
        if max_shares < min_shares:
            return 0  # Position too small
        
        # Add some randomness but keep it reasonable
        quantity = random.randint(min_shares, max_shares)
        
        # Ensure we don't exceed available cash
        trade_value = quantity * price
        if trade_value > self.portfolio_value * 0.95:  # Leave 5% cash buffer
            quantity = int((self.portfolio_value * 0.95) / price)
        
        return max(0, quantity)
    
    def get_simulated_price(self, symbol: str) -> float:
        """Get simulated price for a symbol with realistic current prices"""
        # Current realistic prices (as of 2025)
        base_prices = {
            'AAPL': 150.0,
            'MSFT': 308.0,  # Updated to match your example
            'GOOGL': 140.0,  # Updated for realistic price
            'TSLA': 200.0,
            'NVDA': 400.0,
            'SPY': 450.0,
            'QQQ': 380.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add small random variation (±1% for more realistic simulation)
        variation = random.uniform(-0.01, 0.01)  # ±1%
        price = base_price * (1 + variation)
        
        return round(price, 2)
    
    def calculate_pnl(self, action: str, quantity: int, price: float) -> float:
        """Calculate P&L for a trade"""
        # Simplified P&L calculation
        if action == 'BUY':
            # Simulate buying at a good price
            pnl = random.uniform(-50, 100)
        else:
            # Simulate selling at a good price
            pnl = random.uniform(-30, 80)
        
        return round(pnl, 2)
    
    def update_portfolio(self):
        """Update portfolio value based on P&L"""
        # Add some portfolio growth/decline
        portfolio_change = random.uniform(-0.001, 0.002)  # ±0.1% to +0.2%
        self.portfolio_value *= (1 + portfolio_change)
    
    def update_strategy_performance(self, strategy: str, pnl: float):
        """Update strategy performance metrics"""
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {
                'trades': 0,
                'pnl': 0.0,
                'win_rate': 0.0,
                'wins': 0,
                'losses': 0
            }
        
        perf = self.strategy_performance[strategy]
        perf['trades'] += 1
        perf['pnl'] += pnl
        
        if pnl > 0:
            perf['wins'] += 1
        else:
            perf['losses'] += 1
        
        # Calculate win rate
        if perf['trades'] > 0:
            perf['win_rate'] = perf['wins'] / perf['trades']
    
    def stop(self):
        """Stop the paper trading engine"""
        logger.info("⏹️ Stopping paper trading engine...")
        self.is_running = False
    
    def get_status(self) -> Dict:
        """Get current paper trading status"""
        status = {
            'is_running': self.is_running,
            'portfolio_value': self.portfolio_value,
            'total_trades': self.total_trades,
            'total_pnl': self.total_pnl,
            'active_strategies': list(self.strategy_instances.keys()),
            'strategy_performance': self.strategy_performance,
            'recent_trades': self.trades[-10:] if self.trades else []
        }
        
        # Add Public.com metrics if available
        if hasattr(self, 'public_com_metrics'):
            status['public_com_summary'] = self.get_public_com_summary()
        
        return status

async def main():
    """Main function to run paper trading"""
    try:
        # Load configuration from command line argument or use defaults
        config = {
            'initial_capital': 4000.0,  # Updated to match live trading
            'max_position_size': 0.05,
            'max_risk_per_trade': 0.01,
            'trading_interval': 1800,  # 30 minutes (1800 seconds) - MODERATE FREQUENCY INCREASE
            'max_daily_trades': 8,  # 2x more daily trades (was 4)
            'max_weekly_trades': 12,  # 2x more weekly trades (was 6)
            'max_monthly_trades': 20,  # 2.5x more monthly trades (was 8)
            'strategies': ['AdaptiveSectorWaveStrategy'],  # Only use the adaptive strategy
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
            'use_real_strategies': True,  # Enable real strategy integration
            'enable_alerts': True,
            'performance_tracking': True
        }
        
        # Load config from file if provided
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                logger.info(f"📋 Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Could not load config from {config_file}: {e}")
        
        # Create and run paper trading engine
        engine = PaperTradingEngine(config)
        
        # Run the engine
        await engine.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Paper trading stopped by user")
    except Exception as e:
        logger.error(f"❌ Error in paper trading: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 