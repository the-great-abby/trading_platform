"""
Optimized Backtest Engine - High-performance backtesting with parallel processing
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import partial
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import hashlib
import json

from src.core.types import TradeSignal
from src.services.market_data.cached_market_data_manager import get_cached_market_data_manager
from src.services.database.market_data_service import MarketDataDatabaseService
from src.services.ai.ollama_service import OllamaService
from src.strategies.base import BaseStrategy
from src.strategies.momentum.macd_strategy import MACDStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.breakout.sma_crossover import SMACrossoverStrategy
from src.strategies.momentum.momentum_strategy import MomentumStrategy
from src.strategies.mean_reversion.mean_reversion_strategy import MeanReversionStrategy
from src.strategies.breakout.volatility_breakout_strategy import VolatilityBreakoutStrategy
from src.strategies.options.greeks_enhanced_strategy import GreeksEnhancedStrategy
# from src.strategies.sentiment.social_media_sentiment_strategy import SocialMediaSentimentStrategy
# Import BacktestResult from the existing backtest engine
from .backtest_engine import BacktestResult, BacktestTrade

logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """Configuration for optimized backtesting"""
    symbols: List[str]
    start_date: str
    end_date: str
    strategies: List[str]
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    max_workers: int = None
    use_cache: bool = True
    use_llm: bool = False
    batch_size: int = 10
    memory_limit: str = "2Gi"
    timeout_hours: int = 24
    save_intermediate: bool = True
    parallel_strategies: bool = True
    parallel_symbols: bool = True

class OptimizedBacktestEngine:
    """High-performance backtest engine with parallel processing"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.cache_dir = Path("backtest_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize services
        self.market_data_service = MarketDataDatabaseService()
        self.cached_manager = get_cached_market_data_manager()
        
        if config.use_llm:
            self.ollama_service = OllamaService()
        
        # Strategy mapping
        self.strategy_classes = {
            'MACD': MACDStrategy,
            'RSI': RSIStrategy,
            'BollingerBands': BollingerBandsStrategy,
            'SMACrossover': SMACrossoverStrategy,
            'Momentum': MomentumStrategy,
            'MeanReversion': MeanReversionStrategy,
            'VolatilityBreakout': VolatilityBreakoutStrategy,
            'GreeksEnhanced': GreeksEnhancedStrategy
            # 'SocialMediaSentiment': SocialMediaSentimentStrategy  # Temporarily disabled
        }
        
        # Performance tracking
        self.performance_metrics = {
            'total_time': 0,
            'data_fetch_time': 0,
            'strategy_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'parallel_jobs': 0
        }
    
    async def run_optimized_backtest(self) -> Dict[str, BacktestResult]:
        """Run optimized backtest with parallel processing"""
        
        start_time = time.time()
        logger.info("🚀 Starting Optimized Backtest Engine")
        logger.info(f"📊 Configuration:")
        logger.info(f"   Symbols: {len(self.config.symbols)}")
        logger.info(f"   Strategies: {len(self.config.strategies)}")
        logger.info(f"   Period: {self.config.start_date} to {self.config.end_date}")
        logger.info(f"   Parallel processing: {'Enabled' if self.config.parallel_strategies else 'Disabled'}")
        logger.info(f"   Cache: {'Enabled' if self.config.use_cache else 'Disabled'}")
        
        # Phase 1: Fetch and cache market data
        market_data = await self._fetch_market_data_parallel()
        
        # Phase 2: Run strategies in parallel
        if self.config.parallel_strategies:
            results = await self._run_strategies_parallel(market_data)
        else:
            results = await self._run_strategies_sequential(market_data)
        
        # Phase 3: Generate performance report
        self._generate_performance_report(start_time)
        
        return results
    
    async def _fetch_market_data_parallel(self) -> Dict[str, pd.DataFrame]:
        """Fetch market data with parallel processing"""
        
        logger.info("📊 Fetching market data with parallel processing...")
        fetch_start = time.time()
        
        # Check cache first
        cache_key = self._generate_cache_key("market_data")
        if self.config.use_cache and self._load_from_cache(cache_key):
            cached_data = self._load_from_cache(cache_key)
            if cached_data:
                logger.info(f"✅ Loaded market data from cache")
                self.performance_metrics['cache_hits'] += 1
                self.performance_metrics['data_fetch_time'] = time.time() - fetch_start
                return cached_data
        
        # Fetch data in parallel
        with ThreadPoolExecutor(max_workers=min(10, len(self.config.symbols))) as executor:
            loop = asyncio.get_event_loop()
            tasks = []
            
            for symbol in self.config.symbols:
                task = loop.run_in_executor(
                    executor,
                    self._fetch_single_symbol_data,
                    symbol
                )
                tasks.append(task)
            
            # Process results in batches
            market_data = {}
            for i in range(0, len(tasks), self.config.batch_size):
                batch = tasks[i:i + self.config.batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to fetch data for {self.config.symbols[i + j]}: {result}")
                    else:
                        symbol = self.config.symbols[i + j]
                        market_data[symbol] = result
                        logger.info(f"✅ Fetched data for {symbol}")
            
            # Cache the results
            if self.config.use_cache:
                self._save_to_cache(cache_key, market_data)
                self.performance_metrics['cache_misses'] += 1
            
            self.performance_metrics['data_fetch_time'] = time.time() - fetch_start
            logger.info(f"📊 Market data fetch completed in {self.performance_metrics['data_fetch_time']:.2f}s")
            
            return market_data
    
    def _fetch_single_symbol_data(self, symbol: str) -> pd.DataFrame:
        """Fetch data for a single symbol"""
        try:
            # Use the correct method from CachedMarketDataManager
            data = self.cached_manager.get_historical_data(
                symbol, self.config.start_date, self.config.end_date, interval="1d"
            )
            
            if data is not None and not data.empty:
                return data
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _run_strategies_parallel(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, BacktestResult]:
        """Run strategies in parallel"""
        
        logger.info("🏃 Running strategies in parallel...")
        strategy_start = time.time()
        
        # Group strategies by complexity
        simple_strategies = ['MACD', 'RSI', 'BollingerBands', 'SMACrossover', 'Momentum', 'MeanReversion']
        complex_strategies = ['VolatilityBreakout', 'GreeksEnhanced', 'SocialMediaSentiment', 'Ichimoku']
        advanced_strategies = ['AdaptiveMomentum', 'RegimeSwitching', 'QuantumMomentum', 'NeuralNetwork']
        
        # Run simple strategies first (fastest)
        simple_results = await self._run_strategy_group_parallel(
            [s for s in self.config.strategies if s in simple_strategies],
            market_data,
            max_workers=min(8, len(self.config.symbols))
        )
        
        # Run complex strategies
        complex_results = await self._run_strategy_group_parallel(
            [s for s in self.config.strategies if s in complex_strategies],
            market_data,
            max_workers=min(4, len(self.config.symbols))
        )
        
        # Run advanced strategies (most resource-intensive)
        advanced_results = await self._run_strategy_group_parallel(
            [s for s in self.config.strategies if s in advanced_strategies],
            market_data,
            max_workers=min(2, len(self.config.symbols))
        )
        
        # Combine results
        all_results = {**simple_results, **complex_results, **advanced_results}
        
        self.performance_metrics['strategy_time'] = time.time() - strategy_start
        logger.info(f"🏃 Strategy execution completed in {self.performance_metrics['strategy_time']:.2f}s")
        
        return all_results
    
    async def _run_strategy_group_parallel(self, strategies: List[str], 
                                         market_data: Dict[str, pd.DataFrame],
                                         max_workers: int) -> Dict[str, BacktestResult]:
        """Run a group of strategies in parallel"""
        
        if not strategies:
            return {}
        
        logger.info(f"🏃 Running {len(strategies)} strategies with {max_workers} workers")
        
        # Create strategy instances
        strategy_instances = {}
        for strategy_name in strategies:
            if strategy_name in self.strategy_classes:
                strategy_class = self.strategy_classes[strategy_name]
                strategy_instances[strategy_name] = strategy_class()
        
        # Run strategies in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = []
            
            for strategy_name, strategy_instance in strategy_instances.items():
                for symbol in self.config.symbols:
                    if symbol in market_data and not market_data[symbol].empty:
                        task = loop.run_in_executor(
                            executor,
                            self._run_single_strategy_backtest,
                            strategy_instance,
                            symbol,
                            market_data[symbol]
                        )
                        tasks.append((strategy_name, symbol, task))
            
            # Process results
            results = {}
            for strategy_name, symbol, task in tasks:
                try:
                    result = await task
                    if result:
                        key = f"{strategy_name}_{symbol}"
                        results[key] = result
                        logger.info(f"✅ {strategy_name} completed for {symbol}")
                except Exception as e:
                    logger.error(f"❌ {strategy_name} failed for {symbol}: {e}")
            
            return results
    
    def _run_single_strategy_backtest(self, strategy: BaseStrategy, 
                                    symbol: str, data: pd.DataFrame) -> Optional[BacktestResult]:
        """Run backtest for a single strategy and symbol"""
        
        try:
            # Initialize strategy
            strategy.initialize(data)
            
            # Run backtest
            result = strategy.backtest(
                data=data,
                initial_capital=self.config.initial_capital,
                commission=self.config.commission,
                slippage=self.config.slippage
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error running {strategy.__class__.__name__} for {symbol}: {e}")
            return None
    
    async def _run_strategies_sequential(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, BacktestResult]:
        """Run strategies sequentially (fallback)"""
        
        logger.info("🏃 Running strategies sequentially...")
        strategy_start = time.time()
        
        results = {}
        
        for strategy_name in self.config.strategies:
            if strategy_name in self.strategy_classes:
                strategy_class = self.strategy_classes[strategy_name]
                strategy_instance = strategy_class()
                
                logger.info(f"🏃 Running {strategy_name}...")
                
                for symbol in self.config.symbols:
                    if symbol in market_data and not market_data[symbol].empty:
                        result = self._run_single_strategy_backtest(
                            strategy_instance, symbol, market_data[symbol]
                        )
                        
                        if result:
                            key = f"{strategy_name}_{symbol}"
                            results[key] = result
        
        self.performance_metrics['strategy_time'] = time.time() - strategy_start
        return results
    
    def _generate_cache_key(self, prefix: str) -> str:
        """Generate cache key for data"""
        config_hash = hashlib.md5(
            json.dumps({
                'symbols': sorted(self.config.symbols),
                'start_date': self.config.start_date,
                'end_date': self.config.end_date,
                'strategies': sorted(self.config.strategies)
            }, sort_keys=True).encode()
        ).hexdigest()
        
        return f"{prefix}_{config_hash}"
    
    def _save_to_cache(self, key: str, data: Any):
        """Save data to cache"""
        try:
            cache_file = self.cache_dir / f"{key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _load_from_cache(self, key: str) -> Optional[Any]:
        """Load data from cache"""
        try:
            cache_file = self.cache_dir / f"{key}.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
        
        return None
    
    def _generate_performance_report(self, start_time: float):
        """Generate performance report"""
        
        total_time = time.time() - start_time
        self.performance_metrics['total_time'] = total_time
        
        logger.info("📊 PERFORMANCE REPORT")
        logger.info("=" * 50)
        logger.info(f"⏱️  Total time: {total_time:.2f}s")
        logger.info(f"📊 Data fetch: {self.performance_metrics['data_fetch_time']:.2f}s")
        logger.info(f"🏃 Strategy execution: {self.performance_metrics['strategy_time']:.2f}s")
        logger.info(f"💾 Cache hits: {self.performance_metrics['cache_hits']}")
        logger.info(f"❌ Cache misses: {self.performance_metrics['cache_misses']}")
        logger.info(f"⚡ Parallel jobs: {self.performance_metrics['parallel_jobs']}")
        
        if self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses'] > 0:
            cache_rate = (self.performance_metrics['cache_hits'] / 
                         (self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses'])) * 100
            logger.info(f"📈 Cache hit rate: {cache_rate:.1f}%")
        
        # Performance recommendations
        if total_time > 3600:  # More than 1 hour
            logger.warning("⚠️  Performance recommendations:")
            logger.warning("   • Consider reducing the number of symbols")
            logger.warning("   • Use more aggressive caching")
            logger.warning("   • Run complex strategies separately")
            logger.warning("   • Consider using GPU acceleration for ML strategies") 