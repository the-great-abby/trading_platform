#!/usr/bin/env python3
"""
Enhanced Recommendations Backtest - API Integration Test
=========================================================

⚠️  NOTE: This is an API INTEGRATION TEST, not a historical backtest!

This script tests the enhanced recommendations endpoint by calling it repeatedly:
- Endpoint: /api/trading/recommendations/enhanced
- Multi-indicator analysis: RSI, MACD, MA, Volume, Bollinger Bands

WHAT IT DOES:
- ✅ Validates enhanced API endpoint works correctly
- ✅ Tests multi-indicator recommendation retrieval
- ✅ Simulates trade execution based on current recommendations
- ✅ Uses same risk management as live trading

WHAT IT DOES NOT DO:
- ❌ Test historical strategy performance (uses current data repeatedly)
- ❌ Simulate different market conditions (same data every call)
- ❌ Calculate actual historical returns

For true historical backtesting, use:
- backtests/comprehensive_two_year_backtest.py (uses real historical data)
- backtests/enhanced_market_regime_backtest.py (tests market conditions)
"""

import asyncio
import httpx
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.utils.trading_config import SYMBOLS
except ImportError:
    # Fallback if trading_config not available
    SYMBOLS = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA']

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_recommendations_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedRecommendationsBacktest:
    """
    Backtest using the enhanced recommendations endpoint (multi-indicator analysis)
    Mimics the live trading system's approach
    """
    
    def __init__(self, initial_capital: float = 4000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.portfolio_value = initial_capital
        self.positions = {}  # {symbol: {'quantity': int, 'avg_price': float, 'entry_date': datetime}}
        self.trades = []
        self.equity_curve = []
        
        # Strategy service URL (same as live trading)
        # Check if running in Kubernetes
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            self.strategy_service_url = "http://strategy-service.trading-system.svc.cluster.local:8001"
            logger.info("🎯 Running in Kubernetes - using cluster service address")
        else:
            self.strategy_service_url = "http://localhost:11001"
            logger.info("💻 Running locally - using port-forwarded address")
        
        # Risk management (same as live trading)
        self.max_position_size = 0.20  # 20% max per position
        self.max_concurrent_positions = 5
        self.max_daily_loss = 500.0  # $500 max daily loss
        
        # Trading costs (Public.com style)
        self.commission = 0.0  # No commission
        self.slippage = 0.001  # 0.1% slippage
        
        logger.info(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"🔗 Strategy Service: {self.strategy_service_url}")
    
    async def get_enhanced_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get enhanced recommendations from strategy service
        Same endpoint as live trading system
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.strategy_service_url}/api/trading/recommendations/enhanced",
                    params={"limit": limit}
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Failed to get recommendations: HTTP {response.status_code}")
                    return []
                
                result = response.json()
                recommendations = result.get('recommendations', [])
                
                logger.info(f"📊 Got {len(recommendations)} enhanced recommendations")
                return recommendations
                
        except Exception as e:
            logger.error(f"❌ Error getting recommendations: {e}")
            return []
    
    async def get_market_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.strategy_service_url}/api/market-data/price/{symbol}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('price')
                
                # Fallback: get from recommendations
                recommendations = await self.get_enhanced_recommendations(limit=20)
                for rec in recommendations:
                    if rec.get('symbol') == symbol:
                        return rec.get('current_price')
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting price for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, symbol: str, price: float, confidence: float) -> int:
        """
        Calculate position size based on risk management rules
        Same logic as live trading system
        """
        # Base allocation as percentage of portfolio
        base_pct = min(self.max_position_size, confidence * 0.25)  # Max 20%, scaled by confidence
        
        # Calculate dollar amount
        position_value = self.cash * base_pct
        
        # Calculate quantity
        quantity = int(position_value / price)
        
        return quantity
    
    def apply_slippage(self, price: float, action: str) -> float:
        """Apply slippage to price"""
        if action == 'BUY':
            return price * (1 + self.slippage)
        else:  # SELL
            return price * (1 - self.slippage)
    
    async def execute_buy(self, symbol: str, price: float, quantity: int, confidence: float, signal_score: float) -> bool:
        """Execute a buy order"""
        if quantity <= 0:
            return False
        
        # Apply slippage
        execution_price = self.apply_slippage(price, 'BUY')
        total_cost = execution_price * quantity
        
        # Check if we have enough cash
        if total_cost > self.cash:
            logger.warning(f"⚠️  Insufficient cash for {symbol}: need ${total_cost:,.2f}, have ${self.cash:,.2f}")
            return False
        
        # Check position limit
        if len(self.positions) >= self.max_concurrent_positions:
            logger.warning(f"⚠️  Max concurrent positions reached ({self.max_concurrent_positions})")
            return False
        
        # Execute trade
        self.cash -= total_cost
        
        if symbol in self.positions:
            # Add to existing position
            old_qty = self.positions[symbol]['quantity']
            old_avg = self.positions[symbol]['avg_price']
            new_qty = old_qty + quantity
            new_avg = ((old_qty * old_avg) + (quantity * execution_price)) / new_qty
            
            self.positions[symbol]['quantity'] = new_qty
            self.positions[symbol]['avg_price'] = new_avg
        else:
            # New position
            self.positions[symbol] = {
                'quantity': quantity,
                'avg_price': execution_price,
                'entry_date': datetime.now()
            }
        
        # Record trade
        self.trades.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': 'BUY',
            'quantity': quantity,
            'price': execution_price,
            'total': total_cost,
            'confidence': confidence,
            'signal_score': signal_score,
            'cash_after': self.cash
        })
        
        logger.info(f"✅ BUY {quantity} {symbol} @ ${execution_price:.2f} (confidence: {confidence:.1%}, score: {signal_score:.2f})")
        return True
    
    async def execute_sell(self, symbol: str, price: float, quantity: int) -> bool:
        """Execute a sell order"""
        if symbol not in self.positions:
            return False
        
        # Check quantity
        available_qty = self.positions[symbol]['quantity']
        if quantity > available_qty:
            quantity = available_qty
        
        # Apply slippage
        execution_price = self.apply_slippage(price, 'SELL')
        total_proceeds = execution_price * quantity
        
        # Calculate P&L
        avg_entry_price = self.positions[symbol]['avg_price']
        pnl = (execution_price - avg_entry_price) * quantity
        
        # Execute trade
        self.cash += total_proceeds
        
        # Update position
        self.positions[symbol]['quantity'] -= quantity
        if self.positions[symbol]['quantity'] <= 0:
            del self.positions[symbol]
        
        # Record trade
        self.trades.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': execution_price,
            'total': total_proceeds,
            'pnl': pnl,
            'cash_after': self.cash
        })
        
        logger.info(f"✅ SELL {quantity} {symbol} @ ${execution_price:.2f} (P&L: ${pnl:,.2f})")
        return True
    
    async def process_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Process recommendations and execute trades"""
        for rec in recommendations:
            symbol = rec.get('symbol')
            action = rec.get('action', '').upper()
            confidence = rec.get('confidence', 0.0)
            signal_score = rec.get('signal_score', 0.0)
            current_price = rec.get('current_price')
            
            if not symbol or not action or not current_price:
                continue
            
            # Require minimum confidence
            if confidence < 0.60:  # Same threshold as live trading
                logger.info(f"⏭️  Skipping {symbol}: confidence {confidence:.1%} below threshold")
                continue
            
            if action == 'BUY':
                quantity = self.calculate_position_size(symbol, current_price, confidence)
                if quantity > 0:
                    await self.execute_buy(symbol, current_price, quantity, confidence, signal_score)
            
            elif action == 'SELL' and symbol in self.positions:
                # Sell entire position
                quantity = self.positions[symbol]['quantity']
                await self.execute_sell(symbol, current_price, quantity)
    
    async def update_portfolio_value(self):
        """Update portfolio value based on current positions"""
        positions_value = 0.0
        
        for symbol, position in self.positions.items():
            current_price = await self.get_market_price(symbol)
            if current_price:
                positions_value += current_price * position['quantity']
            else:
                # Use entry price as fallback
                positions_value += position['avg_price'] * position['quantity']
        
        self.portfolio_value = self.cash + positions_value
        
        # Record equity curve
        self.equity_curve.append({
            'timestamp': datetime.now(),
            'cash': self.cash,
            'positions_value': positions_value,
            'total_value': self.portfolio_value
        })
    
    async def run_backtest(self, days: int = 30, check_interval_hours: int = 1):
        """
        Run backtest over specified number of days
        Checks recommendations at regular intervals (mimics cronjob)
        """
        logger.info("=" * 80)
        logger.info("🚀 ENHANCED RECOMMENDATIONS BACKTEST")
        logger.info("=" * 80)
        logger.info(f"📅 Duration: {days} days")
        logger.info(f"⏰ Check interval: Every {check_interval_hours} hour(s)")
        logger.info(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        logger.info("=" * 80)
        logger.info("")
        
        start_time = datetime.now()
        checks_per_day = 24 // check_interval_hours
        total_checks = days * checks_per_day
        
        for check in range(total_checks):
            day = check // checks_per_day + 1
            check_of_day = check % checks_per_day + 1
            
            logger.info(f"\n📅 Day {day}/{days} - Check {check_of_day}/{checks_per_day}")
            logger.info(f"💰 Portfolio Value: ${self.portfolio_value:,.2f}")
            logger.info(f"💵 Cash: ${self.cash:,.2f}")
            logger.info(f"📊 Positions: {len(self.positions)}")
            
            # Get enhanced recommendations
            recommendations = await self.get_enhanced_recommendations(limit=10)
            
            if recommendations:
                logger.info(f"\n📊 Processing {len(recommendations)} recommendations:")
                for rec in recommendations[:5]:  # Show top 5
                    logger.info(f"   {rec.get('symbol'):6} | {rec.get('action'):4} | Score: {rec.get('signal_score', 0):6.2f} | Conf: {rec.get('confidence', 0):5.1%}")
                
                # Process recommendations
                await self.process_recommendations(recommendations)
            else:
                logger.info("ℹ️  No recommendations available")
            
            # Update portfolio value
            await self.update_portfolio_value()
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        # Final portfolio update
        await self.update_portfolio_value()
        
        # Calculate results
        return self.calculate_results(start_time)
    
    def calculate_results(self, start_time: datetime) -> Dict[str, Any]:
        """Calculate backtest results"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        total_return = self.portfolio_value - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # Calculate trade statistics
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) < 0]
        
        win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0
        
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Calculate max drawdown
        max_value = self.initial_capital
        max_drawdown = 0
        
        for point in self.equity_curve:
            value = point['total_value']
            if value > max_value:
                max_value = value
            drawdown = ((max_value - value) / max_value) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        results = {
            'initial_capital': self.initial_capital,
            'final_capital': self.portfolio_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown_pct': max_drawdown,
            'open_positions': len(self.positions),
            'duration_seconds': duration,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'positions': self.positions
        }
        
        # Print results
        logger.info("\n" + "=" * 80)
        logger.info("📊 BACKTEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"💰 Initial Capital:     ${results['initial_capital']:,.2f}")
        logger.info(f"💰 Final Capital:       ${results['final_capital']:,.2f}")
        logger.info(f"📈 Total Return:        ${results['total_return']:,.2f} ({results['total_return_pct']:.2f}%)")
        logger.info(f"📊 Total Trades:        {results['total_trades']}")
        logger.info(f"   ├─ Buys:             {results['buy_trades']}")
        logger.info(f"   └─ Sells:            {results['sell_trades']}")
        logger.info(f"🎯 Win Rate:            {results['win_rate']:.1%}")
        logger.info(f"   ├─ Winning Trades:   {results['winning_trades']}")
        logger.info(f"   └─ Losing Trades:    {results['losing_trades']}")
        logger.info(f"💵 Avg Win:             ${results['avg_win']:.2f}")
        logger.info(f"💸 Avg Loss:            ${results['avg_loss']:.2f}")
        logger.info(f"📊 Profit Factor:       {results['profit_factor']:.2f}")
        logger.info(f"⚠️  Max Drawdown:        {results['max_drawdown_pct']:.2f}%")
        logger.info(f"📦 Open Positions:      {results['open_positions']}")
        logger.info(f"⏱️  Duration:            {results['duration_seconds']:.1f}s")
        logger.info("=" * 80)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/enhanced_recommendations_backtest_{timestamp}.json"
        
        # Convert non-serializable objects
        results_copy = results.copy()
        results_copy['trades'] = [
            {**t, 'timestamp': t['timestamp'].isoformat()} for t in results_copy['trades']
        ]
        results_copy['equity_curve'] = [
            {**e, 'timestamp': e['timestamp'].isoformat()} for e in results_copy['equity_curve']
        ]
        results_copy['positions'] = {
            symbol: {**pos, 'entry_date': pos['entry_date'].isoformat()}
            for symbol, pos in results_copy['positions'].items()
        }
        
        os.makedirs('results', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(results_copy, f, indent=2)
        
        logger.info(f"\n💾 Results saved to: {filename}")
        
        return results


async def main():
    """Main entry point"""
    # Create backtest instance
    backtest = EnhancedRecommendationsBacktest(initial_capital=4000.0)
    
    # Run backtest
    # Simulates 30 days of trading, checking recommendations every hour
    results = await backtest.run_backtest(days=30, check_interval_hours=1)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

