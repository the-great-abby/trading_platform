"""
Main Trading Engine - Orchestrates all trading activities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import pandas as pd
from loguru import logger

from ..data.market_data import MarketDataProvider
from ..strategies.base import BaseStrategy
from ..risk.risk_manager import RiskManager
from ..models.portfolio import Portfolio
from ..utils.config import Config
from ..core.types import TradeSignal


class TradingMode(Enum):
    """Trading modes"""
    PAPER = "paper"
    LIVE = "live"
    BACKTEST = "backtest"


class TradingEngine:
    """
    Main trading engine that orchestrates all trading activities
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.mode = TradingMode.PAPER
        self.is_running = False
        
        # Initialize components
        self.market_data = MarketDataProvider(config)
        self.risk_manager = RiskManager(config)
        self.portfolio = Portfolio(config)
        
        # Strategy registry
        self.strategies: Dict[str, BaseStrategy] = {}
        
        # Trading state
        self.active_positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        
        # Performance metrics
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        
        logger.info("Trading engine initialized")
    
    def register_strategy(self, name: str, strategy: BaseStrategy):
        """Register a trading strategy"""
        self.strategies[name] = strategy
        logger.info(f"Registered strategy: {name}")
    
    def set_mode(self, mode: TradingMode):
        """Set trading mode"""
        self.mode = mode
        logger.info(f"Trading mode set to: {mode.value}")
    
    async def start(self):
        """Start the trading engine"""
        if self.is_running:
            logger.warning("Trading engine is already running")
            return
        
        self.is_running = True
        logger.info("Starting trading engine...")
        
        try:
            # Initialize market data
            await self.market_data.connect()
            
            # Start main trading loop
            await self._trading_loop()
            
        except Exception as e:
            logger.error(f"Error in trading engine: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the trading engine"""
        self.is_running = False
        await self.market_data.disconnect()
        logger.info("Trading engine stopped")
    
    async def _trading_loop(self):
        """Main trading loop"""
        while self.is_running:
            try:
                # Get current market data
                symbols = list(self.strategies.keys())
                market_data = await self.market_data.get_latest_data(symbols)
                
                # Generate signals from all strategies
                signals = await self._generate_signals(market_data)
                
                # Process signals through risk manager
                approved_signals = await self._process_signals(signals)
                
                # Execute approved trades
                await self._execute_trades(approved_signals)
                
                # Update portfolio and performance
                await self._update_portfolio()
                
                # Log performance metrics
                self._log_performance()
                
                # Wait for next iteration
                await asyncio.sleep(self.config.trading_interval)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _generate_signals(self, market_data: Dict) -> List[TradeSignal]:
        """Generate trading signals from all strategies"""
        signals = []
        
        for strategy_name, strategy in self.strategies.items():
            try:
                if strategy_name in market_data:
                    signal = await strategy.generate_signal(
                        symbol=strategy_name,
                        data=market_data[strategy_name]
                    )
                    if signal:
                        signals.append(signal)
                        
            except Exception as e:
                logger.error(f"Error generating signal for {strategy_name}: {e}")
        
        return signals
    
    async def _process_signals(self, signals: List[TradeSignal]) -> List[TradeSignal]:
        """Process signals through risk manager"""
        approved_signals = []
        
        for signal in signals:
            try:
                # Check risk limits
                if await self.risk_manager.validate_signal(signal, self.portfolio):
                    approved_signals.append(signal)
                else:
                    logger.info(f"Signal rejected by risk manager: {signal.symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing signal: {e}")
        
        return approved_signals
    
    async def _execute_trades(self, signals: List[TradeSignal]):
        """Execute approved trades"""
        for signal in signals:
            try:
                if self.mode == TradingMode.PAPER:
                    await self._execute_paper_trade(signal)
                elif self.mode == TradingMode.LIVE:
                    await self._execute_live_trade(signal)
                    
            except Exception as e:
                logger.error(f"Error executing trade: {e}")
    
    async def _execute_paper_trade(self, signal: TradeSignal):
        """Execute paper trade (simulated)"""
        trade = {
            "symbol": signal.symbol,
            "action": signal.action,
            "quantity": signal.quantity,
            "price": signal.price,
            "timestamp": signal.timestamp,
            "strategy": signal.strategy,
            "status": "FILLED"
        }
        
        # Update portfolio
        await self.portfolio.update_position(trade)
        
        # Record trade
        self.trade_history.append(trade)
        
        logger.info(f"Paper trade executed: {signal.action} {signal.quantity} {signal.symbol} @ {signal.price}")
    
    async def _execute_live_trade(self, signal: TradeSignal):
        """Execute live trade (real money)"""
        try:
            if hasattr(self.market_data, 'place_order'):
                # Use Public API for live trading
                order_result = await self.market_data.place_order(
                    symbol=signal.symbol,
                    side=signal.action.lower(),
                    quantity=int(signal.quantity),
                    order_type="market"
                )
                
                # Update portfolio with the executed trade
                trade = {
                    "symbol": signal.symbol,
                    "action": signal.action,
                    "quantity": signal.quantity,
                    "price": signal.price,
                    "timestamp": signal.timestamp,
                    "strategy": signal.strategy,
                    "status": "FILLED",
                    "order_id": order_result.get("id", "unknown")
                }
                
                await self.portfolio.update_position(trade)
                self.trade_history.append(trade)
                
                logger.info(f"Live trade executed: {signal.action} {signal.quantity} {signal.symbol} @ {signal.price}")
                return order_result
            else:
                logger.warning("Live trading not available with current data provider")
                
        except Exception as e:
            logger.error(f"Error executing live trade: {e}")
            raise
    
    async def _update_portfolio(self):
        """Update portfolio with current market prices"""
        try:
            await self.portfolio.update_valuations()
            self.total_pnl = self.portfolio.total_pnl
            self.daily_pnl = self.portfolio.daily_pnl
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
    
    def _log_performance(self):
        """Log current performance metrics"""
        logger.info(f"Portfolio P&L: ${self.total_pnl:.2f} (Daily: ${self.daily_pnl:.2f})")
        logger.info(f"Win/Loss: {self.win_count}/{self.loss_count}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            "total_pnl": self.total_pnl,
            "daily_pnl": self.daily_pnl,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "win_rate": self.win_count / (self.win_count + self.loss_count) if (self.win_count + self.loss_count) > 0 else 0,
            "active_positions": len(self.active_positions),
            "total_trades": len(self.trade_history)
        } 