#!/usr/bin/env python3
"""
Comprehensive Comparison Backtest - Stocks + Options
====================================================

Compares three recommendation systems:
1. Original (Elliott Wave only) - Stocks
2. Enhanced (Multi-indicator) - Stocks  
3. Options (Automated Scanner) - Options strategies

⚠️  NOTE: This is an API INTEGRATION TEST, not a historical backtest!

For true historical backtesting, use:
- backtests/comprehensive_two_year_backtest.py
- backtests/enhanced_market_regime_backtest.py
"""

import asyncio
import httpx
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
import sys
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.utils.trading_config import SYMBOLS
except ImportError:
    SYMBOLS = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA']

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/comprehensive_comparison_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PortfolioState:
    """Track portfolio state"""
    cash: float
    positions: Dict[str, Dict[str, Any]]  # Stock positions
    options_positions: Dict[str, Dict[str, Any]]  # Options positions
    portfolio_value: float
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]


class ComprehensiveComparisonBacktest:
    """
    Run parallel backtests comparing stocks vs options recommendations
    """
    
    def __init__(self, initial_capital: float = 4000.0):
        self.initial_capital = initial_capital
        
        # Strategy service URL
        if os.getenv('KUBERNETES_SERVICE_HOST'):
            self.strategy_service_url = "http://strategy-service.trading-system.svc.cluster.local:8001"
            logger.info("🎯 Running in Kubernetes")
        else:
            self.strategy_service_url = "http://localhost:11001"
            logger.info("💻 Running locally")
        
        # Risk management
        self.max_position_size = 0.20  # 20% max per position
        self.max_concurrent_positions = 5
        self.commission = 0.0
        self.slippage = 0.001
        
        # Initialize three separate portfolios
        self.original_portfolio = PortfolioState(
            cash=initial_capital,
            positions={},
            options_positions={},
            portfolio_value=initial_capital,
            trades=[],
            equity_curve=[]
        )
        
        self.enhanced_portfolio = PortfolioState(
            cash=initial_capital,
            positions={},
            options_positions={},
            portfolio_value=initial_capital,
            trades=[],
            equity_curve=[]
        )
        
        self.options_portfolio = PortfolioState(
            cash=initial_capital,
            positions={},
            options_positions={},
            portfolio_value=initial_capital,
            trades=[],
            equity_curve=[]
        )
    
    async def get_stock_recommendations(self, endpoint: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get stock recommendations from specified endpoint"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.strategy_service_url}{endpoint}",
                    params={"limit": limit}
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Failed to get recommendations from {endpoint}: HTTP {response.status_code}")
                    return []
                
                result = response.json()
                recommendations = result.get('recommendations', [])
                
                return recommendations
                
        except Exception as e:
            logger.error(f"❌ Error getting recommendations from {endpoint}: {e}")
            return []
    
    async def get_options_opportunities(self, available_cash: float) -> List[Dict[str, Any]]:
        """Get options opportunities from scanner"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.strategy_service_url}/api/options/scan",
                    params={
                        "available_cash": available_cash,
                        "min_confidence": 0.6
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Failed to get options opportunities: HTTP {response.status_code}")
                    return []
                
                result = response.json()
                opportunities = result.get('opportunities', [])
                
                return opportunities
                
        except Exception as e:
            logger.error(f"❌ Error getting options opportunities: {e}")
            return []
    
    async def get_market_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.strategy_service_url}/api/market-data/price/{symbol}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('price')
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting price for {symbol}: {e}")
            return None
    
    def execute_stock_trade(self, portfolio: PortfolioState, symbol: str, action: str, 
                           price: float, quantity: int, confidence: float, signal_score: float) -> bool:
        """Execute a stock trade in the specified portfolio"""
        
        if action == 'BUY':
            if quantity <= 0:
                return False
            
            # Apply slippage
            execution_price = price * (1 + self.slippage)
            total_cost = execution_price * quantity
            
            # Check cash
            if total_cost > portfolio.cash:
                return False
            
            # Check position limit
            if len(portfolio.positions) + len(portfolio.options_positions) >= self.max_concurrent_positions:
                return False
            
            # Execute
            portfolio.cash -= total_cost
            
            if symbol in portfolio.positions:
                old_qty = portfolio.positions[symbol]['quantity']
                old_avg = portfolio.positions[symbol]['avg_price']
                new_qty = old_qty + quantity
                new_avg = ((old_qty * old_avg) + (quantity * execution_price)) / new_qty
                
                portfolio.positions[symbol]['quantity'] = new_qty
                portfolio.positions[symbol]['avg_price'] = new_avg
            else:
                portfolio.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': execution_price,
                    'entry_date': datetime.now(),
                    'type': 'stock'
                }
            
            portfolio.trades.append({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': 'BUY',
                'asset_type': 'stock',
                'quantity': quantity,
                'price': execution_price,
                'total': total_cost,
                'confidence': confidence,
                'signal_score': signal_score
            })
            
            logger.info(f"      ✅ BUY {quantity} {symbol} @ ${execution_price:.2f} | Cost: ${total_cost:.2f} | Cash: ${portfolio.cash:.2f}")
            
            return True
        
        elif action == 'SELL':
            if symbol not in portfolio.positions:
                return False
            
            available_qty = portfolio.positions[symbol]['quantity']
            if quantity > available_qty:
                quantity = available_qty
            
            # Apply slippage
            execution_price = price * (1 - self.slippage)
            total_proceeds = execution_price * quantity
            
            # Calculate P&L
            avg_entry_price = portfolio.positions[symbol]['avg_price']
            pnl = (execution_price - avg_entry_price) * quantity
            
            # Execute
            portfolio.cash += total_proceeds
            
            portfolio.positions[symbol]['quantity'] -= quantity
            if portfolio.positions[symbol]['quantity'] <= 0:
                del portfolio.positions[symbol]
            
            portfolio.trades.append({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': 'SELL',
                'asset_type': 'stock',
                'quantity': quantity,
                'price': execution_price,
                'total': total_proceeds,
                'pnl': pnl
            })
            
            logger.info(f"      ✅ SELL {quantity} {symbol} @ ${execution_price:.2f} | Proceeds: ${total_proceeds:.2f} | P&L: ${pnl:+.2f}")
            
            return True
        
        return False
    
    def execute_options_trade(self, portfolio: PortfolioState, opportunity: Dict[str, Any]) -> bool:
        """Execute an options trade"""
        symbol = opportunity.get('symbol')
        strategy = opportunity.get('suggested_strategy')
        estimated_cost = opportunity.get('estimated_cost', 0)
        confidence = opportunity.get('confidence', 0)
        entry_price = opportunity.get('entry_price', 0)
        
        # Check if we have enough cash
        if estimated_cost > portfolio.cash:
            return False
        
        # Check position limit
        if len(portfolio.positions) + len(portfolio.options_positions) >= self.max_concurrent_positions:
            return False
        
        # Execute trade
        portfolio.cash -= estimated_cost
        
        position_id = f"{symbol}_{strategy}_{datetime.now().timestamp()}"
        portfolio.options_positions[position_id] = {
            'symbol': symbol,
            'strategy': strategy,
            'cost': estimated_cost,
            'entry_price': entry_price,
            'entry_date': datetime.now(),
            'target_price': opportunity.get('target_price', entry_price * 1.1),
            'stop_loss': opportunity.get('stop_loss', entry_price * 0.9),
            'confidence': confidence,
            'type': 'options'
        }
        
        portfolio.trades.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': 'OPEN',
            'asset_type': 'options',
            'strategy': strategy,
            'cost': estimated_cost,
            'confidence': confidence
        })
        
        logger.info(f"      ✅ OPEN {strategy} {symbol} | Cost: ${estimated_cost:.2f} | Cash: ${portfolio.cash:.2f}")
        
        return True
    
    def calculate_position_size(self, portfolio: PortfolioState, price: float, confidence: float) -> int:
        """Calculate position size for stocks"""
        base_pct = min(self.max_position_size, confidence * 0.25)
        position_value = portfolio.cash * base_pct
        quantity = int(position_value / price)
        return quantity
    
    async def process_stock_recommendations(self, portfolio: PortfolioState, recommendations: List[Dict[str, Any]]):
        """Process stock recommendations for a portfolio"""
        for rec in recommendations:
            symbol = rec.get('symbol')
            action = rec.get('action', '').upper()
            confidence = rec.get('confidence', 0.0)
            signal_score = rec.get('signal_score', 0.0)
            current_price = rec.get('current_price')
            
            if not symbol or not action or not current_price:
                continue
            
            # Require minimum confidence
            if confidence < 0.60:
                continue
            
            if action == 'BUY':
                quantity = self.calculate_position_size(portfolio, current_price, confidence)
                if quantity > 0:
                    self.execute_stock_trade(portfolio, symbol, 'BUY', current_price, quantity, confidence, signal_score)
            
            elif action == 'SELL' and symbol in portfolio.positions:
                quantity = portfolio.positions[symbol]['quantity']
                self.execute_stock_trade(portfolio, symbol, 'SELL', current_price, quantity, confidence, signal_score)
    
    async def process_options_opportunities(self, portfolio: PortfolioState, opportunities: List[Dict[str, Any]]):
        """Process options opportunities for a portfolio"""
        # Sort by confidence
        sorted_opps = sorted(opportunities, key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Execute top opportunities
        for opp in sorted_opps[:3]:  # Max 3 options trades per check
            if opp.get('affordable', False) and opp.get('confidence', 0) >= 0.6:
                self.execute_options_trade(portfolio, opp)
    
    async def update_portfolio_value(self, portfolio: PortfolioState):
        """Update portfolio value"""
        # Stock positions value
        stocks_value = 0.0
        for symbol, position in portfolio.positions.items():
            current_price = await self.get_market_price(symbol)
            if current_price:
                stocks_value += current_price * position['quantity']
            else:
                stocks_value += position['avg_price'] * position['quantity']
        
        # Options positions value (simplified - use entry price as estimate)
        options_value = 0.0
        for pos_id, position in list(portfolio.options_positions.items()):
            # Simple profit/loss model for options
            # In reality, would need Greeks calculation
            options_value += position['cost'] * 1.05  # Assume 5% return on open positions
        
        portfolio.portfolio_value = portfolio.cash + stocks_value + options_value
        
        portfolio.equity_curve.append({
            'timestamp': datetime.now(),
            'cash': portfolio.cash,
            'stocks_value': stocks_value,
            'options_value': options_value,
            'total_value': portfolio.portfolio_value
        })
    
    async def run_comparison(self, days: int = 30, check_interval_hours: int = 1):
        """Run comparison backtest"""
        logger.info("=" * 80)
        logger.info("🔬 COMPREHENSIVE COMPARISON BACKTEST - STOCKS + OPTIONS")
        logger.info("=" * 80)
        logger.info(f"📅 Duration: {days} days")
        logger.info(f"⏰ Check interval: Every {check_interval_hours} hour(s)")
        logger.info(f"💰 Initial Capital (each): ${self.initial_capital:,.2f}")
        logger.info("=" * 80)
        logger.info("")
        
        start_time = datetime.now()
        checks_per_day = 24 // check_interval_hours
        total_checks = days * checks_per_day
        
        for check in range(total_checks):
            day = check // checks_per_day + 1
            check_of_day = check % checks_per_day + 1
            
            logger.info(f"\n{'='*80}")
            logger.info(f"📅 Day {day}/{days} - Check {check_of_day}/{checks_per_day}")
            logger.info(f"{'='*80}")
            
            # Get stock recommendations
            logger.info("\n🔵 ORIGINAL RECOMMENDATIONS (Elliott Wave Only)")
            original_recs = await self.get_stock_recommendations("/api/trading/recommendations", limit=10)
            logger.info(f"   📊 Got {len(original_recs)} recommendations")
            
            logger.info("\n🟢 ENHANCED RECOMMENDATIONS (Multi-Indicator)")
            enhanced_recs = await self.get_stock_recommendations("/api/trading/recommendations/enhanced", limit=10)
            logger.info(f"   📊 Got {len(enhanced_recs)} recommendations")
            
            # Get options opportunities
            logger.info("\n🟡 OPTIONS OPPORTUNITIES (Automated Scanner)")
            options_opps = await self.get_options_opportunities(self.options_portfolio.cash)
            logger.info(f"   📊 Got {len(options_opps)} opportunities")
            
            # Process original stock recommendations
            if original_recs:
                await self.process_stock_recommendations(self.original_portfolio, original_recs)
            
            # Process enhanced stock recommendations
            if enhanced_recs:
                await self.process_stock_recommendations(self.enhanced_portfolio, enhanced_recs)
            
            # Process options opportunities
            if options_opps:
                await self.process_options_opportunities(self.options_portfolio, options_opps)
            
            # Update portfolio values
            await self.update_portfolio_value(self.original_portfolio)
            await self.update_portfolio_value(self.enhanced_portfolio)
            await self.update_portfolio_value(self.options_portfolio)
            
            # Show comparison
            logger.info(f"\n📊 PORTFOLIO COMPARISON:")
            
            # Original
            orig_stocks = self.original_portfolio.portfolio_value - self.original_portfolio.cash
            logger.info(f"   🔵 Original (Elliott Wave):")
            logger.info(f"      Total:     ${self.original_portfolio.portfolio_value:>12,.2f}")
            logger.info(f"      Cash:      ${self.original_portfolio.cash:>12,.2f}")
            logger.info(f"      Positions: ${orig_stocks:>12,.2f} ({len(self.original_portfolio.positions)} stocks)")
            logger.info(f"      Trades:    {len(self.original_portfolio.trades)}")
            
            # Enhanced
            enh_stocks = self.enhanced_portfolio.portfolio_value - self.enhanced_portfolio.cash
            logger.info(f"   🟢 Enhanced (Multi-Indicator):")
            logger.info(f"      Total:     ${self.enhanced_portfolio.portfolio_value:>12,.2f}")
            logger.info(f"      Cash:      ${self.enhanced_portfolio.cash:>12,.2f}")
            logger.info(f"      Positions: ${enh_stocks:>12,.2f} ({len(self.enhanced_portfolio.positions)} stocks)")
            logger.info(f"      Trades:    {len(self.enhanced_portfolio.trades)}")
            
            # Options
            opt_positions = self.options_portfolio.portfolio_value - self.options_portfolio.cash
            logger.info(f"   🟡 Options (Automated Scanner):")
            logger.info(f"      Total:     ${self.options_portfolio.portfolio_value:>12,.2f}")
            logger.info(f"      Cash:      ${self.options_portfolio.cash:>12,.2f}")
            logger.info(f"      Positions: ${opt_positions:>12,.2f} ({len(self.options_portfolio.options_positions)} options)")
            logger.info(f"      Trades:    {len(self.options_portfolio.trades)}")
            
            await asyncio.sleep(0.5)
        
        # Calculate final results
        return self.calculate_comparison_results(start_time)
    
    def calculate_portfolio_stats(self, portfolio: PortfolioState, name: str) -> Dict[str, Any]:
        """Calculate statistics for a portfolio"""
        # Total return
        total_return = portfolio.portfolio_value - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # Separate stock and options trades
        stock_trades = [t for t in portfolio.trades if t.get('asset_type') == 'stock']
        options_trades = [t for t in portfolio.trades if t.get('asset_type') == 'options']
        
        buy_trades = [t for t in stock_trades if t['action'] == 'BUY']
        sell_trades = [t for t in stock_trades if t['action'] == 'SELL']
        
        # Realized P&L
        realized_pnl = sum(t.get('pnl', 0) for t in sell_trades)
        
        # Positions value
        stocks_value = sum(
            pos['quantity'] * pos['avg_price']
            for pos in portfolio.positions.values()
        )
        options_value = sum(
            pos['cost']
            for pos in portfolio.options_positions.values()
        )
        unrealized_pnl = (portfolio.portfolio_value - portfolio.cash) - (stocks_value + options_value)
        
        winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) < 0]
        
        win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Max drawdown
        max_value = self.initial_capital
        max_drawdown = 0
        
        for point in portfolio.equity_curve:
            value = point['total_value']
            if value > max_value:
                max_value = value
            drawdown = ((max_value - value) / max_value) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'name': name,
            'initial_capital': self.initial_capital,
            'final_capital': portfolio.portfolio_value,
            'cash': portfolio.cash,
            'stocks_value': stocks_value,
            'options_value': options_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_trades': len(portfolio.trades),
            'stock_trades': len(stock_trades),
            'options_trades': len(options_trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown_pct': max_drawdown,
            'open_stock_positions': len(portfolio.positions),
            'open_options_positions': len(portfolio.options_positions)
        }
    
    def calculate_comparison_results(self, start_time: datetime) -> Dict[str, Any]:
        """Calculate comparison results"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        original_stats = self.calculate_portfolio_stats(self.original_portfolio, "Original (Elliott Wave)")
        enhanced_stats = self.calculate_portfolio_stats(self.enhanced_portfolio, "Enhanced (Multi-Indicator)")
        options_stats = self.calculate_portfolio_stats(self.options_portfolio, "Options (Automated Scanner)")
        
        # Calculate winner
        all_returns = [
            ('Original', original_stats['total_return']),
            ('Enhanced', enhanced_stats['total_return']),
            ('Options', options_stats['total_return'])
        ]
        all_returns.sort(key=lambda x: x[1], reverse=True)
        winner = all_returns[0][0]
        
        results = {
            'original': original_stats,
            'enhanced': enhanced_stats,
            'options': options_stats,
            'winner': winner,
            'duration_seconds': duration
        }
        
        # Print comparison
        logger.info("\n" + "=" * 80)
        logger.info("🏆 FINAL COMPARISON RESULTS")
        logger.info("=" * 80)
        
        for stats in [original_stats, enhanced_stats, options_stats]:
            icon = "🔵" if stats['name'].startswith("Original") else "🟢" if stats['name'].startswith("Enhanced") else "🟡"
            logger.info(f"\n{icon} {stats['name'].upper()}")
            logger.info(f"   💰 Final Portfolio:    ${stats['final_capital']:,.2f}")
            logger.info(f"      💵 Cash:            ${stats['cash']:,.2f}")
            logger.info(f"      📈 Stocks:          ${stats['stocks_value']:,.2f}")
            logger.info(f"      📊 Options:         ${stats['options_value']:,.2f}")
            logger.info(f"   📈 Total Return:       ${stats['total_return']:,.2f} ({stats['total_return_pct']:.2f}%)")
            logger.info(f"      ✅ Realized:        ${stats['realized_pnl']:,.2f}")
            logger.info(f"      📊 Unrealized:      ${stats['unrealized_pnl']:,.2f}")
            logger.info(f"   📊 Total Trades:       {stats['total_trades']} ({stats['stock_trades']} stocks, {stats['options_trades']} options)")
            logger.info(f"   🎯 Win Rate:           {stats['win_rate']:.1%}")
            logger.info(f"   📊 Profit Factor:      {stats['profit_factor']:.2f}")
            logger.info(f"   ⚠️  Max Drawdown:       {stats['max_drawdown_pct']:.2f}%")
            logger.info(f"   📦 Open Positions:     {stats['open_stock_positions']} stocks, {stats['open_options_positions']} options")
        
        logger.info(f"\n🏆 WINNER: {winner}")
        logger.info(f"\n⏱️  Total Duration: {duration:.1f}s")
        logger.info("=" * 80)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/comprehensive_comparison_{timestamp}.json"
        
        # Convert for JSON
        results_copy = {
            'original': {**original_stats},
            'enhanced': {**enhanced_stats},
            'options': {**options_stats},
            'winner': winner,
            'duration_seconds': duration,
            'original_trades': [
                {**t, 'timestamp': t['timestamp'].isoformat()} 
                for t in self.original_portfolio.trades
            ],
            'enhanced_trades': [
                {**t, 'timestamp': t['timestamp'].isoformat()} 
                for t in self.enhanced_portfolio.trades
            ],
            'options_trades': [
                {**t, 'timestamp': t['timestamp'].isoformat()} 
                for t in self.options_portfolio.trades
            ]
        }
        
        os.makedirs('results', exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(results_copy, f, indent=2)
        
        logger.info(f"\n💾 Results saved to: {filename}")
        
        return results


async def main():
    """Main entry point"""
    backtest = ComprehensiveComparisonBacktest(initial_capital=4000.0)
    results = await backtest.run_comparison(days=30, check_interval_hours=1)
    return results


if __name__ == "__main__":
    asyncio.run(main())






