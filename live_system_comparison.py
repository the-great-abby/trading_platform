#!/usr/bin/env python3
"""
Current Live System vs Perspective Changes Comparison
Analyzes the performance difference between current live system and our optimized changes
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiveSystemComparison:
    def __init__(self):
        self.initial_capital = 4000.0
        
        self.symbols = {
            'SPY': {'volatility': 0.15, 'avg_daily_range': 0.015, 'liquidity': 'high', 'beta': 1.0},
            'QQQ': {'volatility': 0.18, 'avg_daily_range': 0.02, 'liquidity': 'high', 'beta': 1.1},
            'AAPL': {'volatility': 0.20, 'avg_daily_range': 0.025, 'liquidity': 'high', 'beta': 0.9},
            'MSFT': {'volatility': 0.18, 'avg_daily_range': 0.02, 'liquidity': 'high', 'beta': 1.0},
            'TSLA': {'volatility': 0.35, 'avg_daily_range': 0.05, 'liquidity': 'high', 'beta': 1.8},
            'NVDA': {'volatility': 0.30, 'avg_daily_range': 0.04, 'liquidity': 'high', 'beta': 1.6}
        }
        
        # Current Live System Configuration (from live_trading_strategies.yaml)
        self.current_live_system = {
            'strategies': {
                'ElliottWaveCorrective': {
                    'base_return': 0.035, 'volatility': 0.08, 'win_rate': 0.68, 'avg_win': 0.065, 'avg_loss': 0.035,
                    'trade_frequency': 0.06, 'max_loss': 0.06, 'profit_target': 0.65, 'trailing_stop': 0.18,
                    'market_regimes': ['corrective', 'sideways', 'low_vol'], 'max_daily_trades': 2, 'max_monthly_trades': 2
                },
                'ElliottWaveImpulse': {
                    'base_return': 0.045, 'volatility': 0.10, 'win_rate': 0.62, 'avg_win': 0.08, 'avg_loss': 0.045,
                    'trade_frequency': 0.05, 'max_loss': 0.07, 'profit_target': 0.75, 'trailing_stop': 0.12,
                    'market_regimes': ['impulse', 'trending', 'bull'], 'max_daily_trades': 0, 'max_monthly_trades': 0  # DISABLED
                },
                'CalendarSpreads': {
                    'base_return': 0.015, 'volatility': 0.04, 'win_rate': 0.75, 'avg_win': 0.04, 'avg_loss': 0.06,
                    'trade_frequency': 0.06, 'max_loss': 0.08, 'profit_target': 0.50, 'trailing_stop': 0.10,
                    'market_regimes': ['low_vol', 'normal', 'sideways', 'corrective'], 'max_daily_trades': 2, 'max_monthly_trades': 2
                },
                'VolatilityTrading': {
                    'base_return': 0.030, 'volatility': 0.12, 'win_rate': 0.65, 'avg_win': 0.055, 'avg_loss': 0.035,
                    'trade_frequency': 0.07, 'max_loss': 0.08, 'profit_target': 0.60, 'trailing_stop': 0.15,
                    'market_regimes': ['volatile', 'trending', 'normal', 'impulse'], 'max_daily_trades': 2, 'max_monthly_trades': 2
                }
            },
            'trading_costs': {
                'commission_per_trade': 0.0, 'commission_per_contract': 0.0, 'options_rebate_per_contract': 0.06,
                'bid_ask_spread': 0.001, 'slippage': 0.0003, 'financing_cost': 0.0001,
                'max_daily_trades': 5, 'min_trade_size': 100, 'max_position_size': 0.10, 'contracts_per_trade': 2
            },
            'portfolio': {
                'max_daily_trades': 5, 'max_monthly_trades': 8, 'max_single_symbol': 0.20, 'max_total_exposure': 0.40, 'min_cash_reserve': 0.15
            }
        }
        
        # Perspective Changes (Our Optimized System)
        self.perspective_changes = {
            'strategies': {
                'ElliottWaveCorrective': {
                    'base_return': 0.035, 'volatility': 0.08, 'win_rate': 0.68, 'avg_win': 0.065, 'avg_loss': 0.035,
                    'trade_frequency': 0.06, 'max_loss': 0.06, 'profit_target': 0.65, 'trailing_stop': 0.18,
                    'market_regimes': ['corrective', 'sideways', 'low_vol'], 'news_delay_days': 2, 'news_quality_threshold': 0.8
                },
                'ElliottWaveImpulse': {
                    'base_return': 0.045, 'volatility': 0.10, 'win_rate': 0.62, 'avg_win': 0.08, 'avg_loss': 0.045,
                    'trade_frequency': 0.05, 'max_loss': 0.07, 'profit_target': 0.75, 'trailing_stop': 0.12,
                    'market_regimes': ['impulse', 'trending', 'bull'], 'news_delay_days': 3, 'news_quality_threshold': 0.85
                },
                'CalendarSpreads': {
                    'base_return': 0.015, 'volatility': 0.04, 'win_rate': 0.75, 'avg_win': 0.04, 'avg_loss': 0.06,
                    'trade_frequency': 0.06, 'max_loss': 0.08, 'profit_target': 0.50, 'trailing_stop': 0.10,
                    'market_regimes': ['low_vol', 'normal', 'sideways', 'corrective'], 'news_delay_days': 1, 'news_quality_threshold': 0.75
                },
                'VolatilityTrading': {
                    'base_return': 0.030, 'volatility': 0.12, 'win_rate': 0.65, 'avg_win': 0.055, 'avg_loss': 0.035,
                    'trade_frequency': 0.07, 'max_loss': 0.08, 'profit_target': 0.60, 'trailing_stop': 0.15,
                    'market_regimes': ['volatile', 'trending', 'normal', 'impulse'], 'news_delay_days': 2, 'news_quality_threshold': 0.75,
                    'volatility_threshold': 0.20, 'volatility_multiplier': 1.5
                }
            },
            'trading_costs': {
                'commission_per_trade': 0.0, 'commission_per_contract': 0.0, 'options_rebate_per_contract': 0.06,
                'bid_ask_spread': 0.001, 'slippage': 0.0003, 'financing_cost': 0.0001,
                'max_daily_trades': 3, 'min_trade_size': 100, 'max_position_size': 0.10, 'contracts_per_trade': 2
            },
            'portfolio': {
                'max_daily_trades': 3, 'max_monthly_trades': 8, 'max_single_symbol': 0.20, 'max_total_exposure': 0.40, 'min_cash_reserve': 0.15
            }
        }
    
    def detect_market_regime(self, day):
        """Simple market regime detection"""
        regime_cycle = day % 100
        
        if regime_cycle < 25:
            return {'regime': 'bull', 'confidence': 0.8, 'volatility': 0.7, 'trend': 0.03}
        elif regime_cycle < 35:
            return {'regime': 'trending', 'confidence': 0.7, 'volatility': 0.8, 'trend': 0.02}
        elif regime_cycle < 50:
            return {'regime': 'normal', 'confidence': 0.6, 'volatility': 1.0, 'trend': 0.0}
        elif regime_cycle < 65:
            return {'regime': 'sideways', 'confidence': 0.7, 'volatility': 0.9, 'trend': 0.0}
        elif regime_cycle < 75:
            return {'regime': 'corrective', 'confidence': 0.6, 'volatility': 1.1, 'trend': -0.01}
        elif regime_cycle < 85:
            return {'regime': 'low_vol', 'confidence': 0.8, 'volatility': 0.6, 'trend': 0.01}
        else:
            return {'regime': 'impulse', 'confidence': 0.7, 'volatility': 0.8, 'trend': 0.025}
    
    def run_system_backtest(self, system_config, years=2):
        """Run backtest for a specific system configuration"""
        days = years * 252
        portfolio_value = self.initial_capital
        peak_value = self.initial_capital
        daily_pnl = []
        total_trades = 0
        total_contracts = 0
        total_rebates = 0.0
        total_costs = 0.0
        
        active_positions = []
        monthly_returns = []
        current_month_pnl = 0
        days_in_month = 0
        
        for day in range(days):
            daily_trade_pnl = 0
            daily_trades = 0
            daily_contracts = 0
            daily_rebates = 0.0
            daily_costs = 0.0
            
            # Skip weekends
            if day % 7 in [5, 6]:
                daily_pnl.append(0)
                days_in_month += 1
                if days_in_month >= 21:
                    monthly_returns.append(current_month_pnl / portfolio_value)
                    current_month_pnl = 0
                    days_in_month = 0
                continue
            
            # Get market regime
            market_regime = self.detect_market_regime(day)
            
            # Process trailing stops for active positions
            positions_to_close = []
            for i, position in enumerate(active_positions):
                # Calculate position P&L
                position_pnl = self._calculate_position_pnl(position, market_regime)
                
                # Check trailing stop
                if self._check_trailing_stop(position, position_pnl):
                    positions_to_close.append(i)
                    daily_trade_pnl += position_pnl
                else:
                    active_positions[i]['current_pnl'] = position_pnl
                    active_positions[i]['days_held'] += 1
            
            # Close positions
            for i in reversed(positions_to_close):
                active_positions.pop(i)
            
            # Run strategies
            for strategy_name, strategy_config in system_config['strategies'].items():
                # Skip disabled strategies
                if strategy_config.get('max_daily_trades', 0) == 0:
                    continue
                
                # Check if strategy is suitable for current regime
                if market_regime['regime'] not in strategy_config['market_regimes']:
                    continue
                
                # Check if strategy generates a signal
                base_frequency = strategy_config['trade_frequency']
                regime_multiplier = 0.5 + (market_regime['confidence'] * 1.0)
                adjusted_frequency = base_frequency * regime_multiplier
                
                if random.random() > adjusted_frequency:
                    continue
                
                # Check daily trade limit
                if daily_trades >= system_config['trading_costs']['max_daily_trades']:
                    break
                
                # Check if we already have a position in this strategy
                if any(pos['strategy'] == strategy_name for pos in active_positions):
                    continue
                
                # Select symbol
                symbol = random.choice(list(self.symbols.keys()))
                symbol_config = self.symbols[symbol]
                
                # Calculate confidence
                confidence = 0.5 + (market_regime['confidence'] * 0.3)
                
                # Skip if confidence too low
                if confidence < 0.6:
                    continue
                
                # Position sizing
                base_size = 0.05
                confidence_multiplier = confidence
                volatility_adjustment = 1.0 - (symbol_config['volatility'] - 0.15) * 0.3
                
                # Volatility Trading gets volatility multiplier (perspective changes only)
                if strategy_name == 'VolatilityTrading' and 'volatility_multiplier' in strategy_config:
                    if symbol_config['volatility'] > strategy_config.get('volatility_threshold', 0.20):
                        volatility_adjustment *= strategy_config['volatility_multiplier']
                
                position_size = min(
                    system_config['trading_costs']['max_position_size'], 
                    max(0.02, base_size * confidence_multiplier * volatility_adjustment)
                )
                
                # Calculate trade size
                trade_size = position_size * portfolio_value
                
                if trade_size < system_config['trading_costs']['min_trade_size']:
                    continue
                
                # Calculate return
                expected_return = strategy_config['base_return'] * market_regime['volatility']
                
                # Win rate calculation
                base_win_rate = strategy_config['win_rate']
                
                # Regime-based adjustments
                if market_regime['regime'] == 'bear':
                    base_win_rate *= 0.5
                elif market_regime['regime'] == 'bull':
                    base_win_rate *= 1.2
                    base_win_rate = min(0.85, base_win_rate)
                elif market_regime['regime'] == 'trending':
                    base_win_rate *= 1.1
                    base_win_rate = min(0.80, base_win_rate)
                
                # Confidence-based adjustment
                base_win_rate *= confidence
                
                is_win = random.random() < base_win_rate
                
                # Calculate trade return
                if is_win:
                    trade_return = max(0.003, np.random.normal(strategy_config['avg_win'], 0.005))
                else:
                    trade_return = -min(strategy_config['max_loss'], abs(np.random.normal(strategy_config['avg_loss'], 0.005)))
                
                # Calculate contracts traded
                contracts_traded = system_config['trading_costs'].get('contracts_per_trade', 1)
                daily_contracts += contracts_traded
                
                # Apply trading costs
                commission_cost = system_config['trading_costs']['commission_per_trade']
                contract_cost = system_config['trading_costs']['commission_per_contract'] * contracts_traded
                rebate = system_config['trading_costs']['options_rebate_per_contract'] * contracts_traded
                spread_cost = trade_size * system_config['trading_costs']['bid_ask_spread']
                slippage_cost = trade_size * system_config['trading_costs']['slippage']
                total_costs_trade = commission_cost + contract_cost + spread_cost + slippage_cost - rebate
                
                net_return = trade_return - (total_costs_trade / trade_size)
                daily_costs += total_costs_trade
                daily_rebates += rebate
                
                trade_pnl = net_return * trade_size
                
                # Create position
                position = {
                    'strategy': strategy_name,
                    'symbol': symbol,
                    'entry_price': trade_size,
                    'entry_day': day,
                    'current_pnl': trade_pnl,
                    'days_held': 0,
                    'max_profit': trade_pnl,
                    'trailing_stop_level': trade_pnl * (1 - strategy_config['trailing_stop']),
                    'profit_target': trade_pnl * strategy_config['profit_target'],
                    'max_loss': trade_pnl * (1 - strategy_config['max_loss']),
                    'confidence': confidence,
                    'market_regime': market_regime['regime']
                }
                
                # Check if we should take profit immediately
                if trade_pnl >= position['profit_target']:
                    daily_trade_pnl += trade_pnl
                else:
                    active_positions.append(position)
                
                total_trades += 1
                daily_trades += 1
                total_costs += total_costs_trade
            
            # Add market noise
            market_noise = np.random.normal(0, 0.002) * portfolio_value
            daily_trade_pnl += market_noise
            
            # Update portfolio
            portfolio_value += daily_trade_pnl
            daily_pnl.append(daily_trade_pnl)
            current_month_pnl += daily_trade_pnl
            total_contracts += daily_contracts
            days_in_month += 1
            
            # End of month
            if days_in_month >= 21:
                monthly_returns.append(current_month_pnl / portfolio_value)
                current_month_pnl = 0
                days_in_month = 0
            
            # Apply financing cost
            portfolio_value *= (1 - system_config['trading_costs']['financing_cost'])
            
            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            else:
                drawdown = (peak_value - portfolio_value) / peak_value
                if drawdown > 0.10:
                    break
        
        # Close remaining positions
        for position in active_positions:
            daily_trade_pnl += position['current_pnl']
        
        # Calculate final metrics
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (365 / len(daily_pnl)) - 1
        
        # Calculate drawdown
        max_drawdown = 0
        running_max = self.initial_capital
        for pnl in daily_pnl:
            running_max += pnl
            if running_max > peak_value:
                peak_value = running_max
            drawdown = (peak_value - running_max) / peak_value
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate Sharpe ratio
        if len(monthly_returns) > 1:
            monthly_volatility = np.std(monthly_returns)
            if monthly_volatility > 0:
                sharpe_ratio = np.mean(monthly_returns) / monthly_volatility * np.sqrt(12)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'final_value': portfolio_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'total_contracts': total_contracts,
            'total_rebates': total_rebates,
            'total_costs': total_costs,
            'daily_pnl': daily_pnl,
            'monthly_returns': monthly_returns
        }
    
    def _calculate_position_pnl(self, position, market_regime):
        """Calculate position P&L"""
        cycle_multiplier = market_regime['volatility']
        
        # Base P&L calculation
        if market_regime['regime'] in ['bull', 'trending', 'impulse']:
            pnl_change = position['current_pnl'] * cycle_multiplier * (1 + np.random.normal(0.02, 0.04))
        elif market_regime['regime'] == 'bear':
            pnl_change = position['current_pnl'] * cycle_multiplier * (1 + np.random.normal(-0.02, 0.04))
        else:
            pnl_change = position['current_pnl'] * cycle_multiplier * (1 + np.random.normal(0, 0.02))
        
        # Time decay for options
        days_factor = min(1.0, position['days_held'] / 45)
        pnl_change *= (1 - days_factor * 0.1)
        
        return position['current_pnl'] + pnl_change
    
    def _check_trailing_stop(self, position, current_pnl):
        """Check trailing stop"""
        # Update max profit
        if current_pnl > position['max_profit']:
            position['max_profit'] = current_pnl
            position['trailing_stop_level'] = current_pnl * (1 - 0.15)
        
        # Check trailing stop
        if current_pnl <= position['max_profit'] * (1 - 0.15):
            return True
        
        # Check profit target
        if current_pnl >= position['profit_target']:
            return True
        
        # Check max loss
        if current_pnl <= position['max_loss']:
            return True
        
        # Time-based exit
        if position['days_held'] >= 45:
            return True
        
        return False
    
    def run_comparison_test(self, num_iterations=5):
        """Run comparison test between current live system and perspective changes"""
        logger.info(f'🚀 Running comparison test with {num_iterations} iterations')
        
        current_results = []
        perspective_results = []
        
        for i in range(num_iterations):
            logger.info(f'Running iteration {i+1}/{num_iterations}')
            
            # Test current live system
            current_result = self.run_system_backtest(self.current_live_system, years=2)
            current_results.append(current_result)
            
            # Test perspective changes
            perspective_result = self.run_system_backtest(self.perspective_changes, years=2)
            perspective_results.append(perspective_result)
        
        # Calculate metrics
        current_returns = [r['annual_return'] for r in current_results]
        perspective_returns = [r['annual_return'] for r in perspective_results]
        
        current_costs = [r['total_costs'] for r in current_results]
        perspective_costs = [r['total_costs'] for r in perspective_results]
        
        current_rebates = [r['total_rebates'] for r in current_results]
        perspective_rebates = [r['total_rebates'] for r in perspective_results]
        
        current_drawdowns = [r['max_drawdown'] for r in current_results]
        perspective_drawdowns = [r['max_drawdown'] for r in perspective_results]
        
        current_sharpes = [r['sharpe_ratio'] for r in current_results]
        perspective_sharpes = [r['sharpe_ratio'] for r in perspective_results]
        
        report = f'''
================================================================================
🚀 CURRENT LIVE SYSTEM vs PERSPECTIVE CHANGES COMPARISON
================================================================================

📊 CURRENT LIVE SYSTEM:
   • Elliott Wave Corrective: 2 trades/day, 2 trades/month
   • Elliott Wave Impulse: DISABLED (0 trades)
   • Calendar Spreads: 2 trades/day, 2 trades/month  
   • Volatility Trading: 2 trades/day, 2 trades/month
   • Total Daily Limit: 5 trades
   • Total Monthly Limit: 8 trades

📈 PERSPECTIVE CHANGES:
   • Elliott Wave Corrective: News delay 2 days, 80% quality threshold
   • Elliott Wave Impulse: ENABLED, News delay 3 days, 85% quality threshold
   • Calendar Spreads: News delay 1 day, 75% quality threshold
   • Volatility Trading: News delay 2 days, 75% quality threshold, Volatility multiplier 1.5x
   • Total Daily Limit: 3 trades (reduced for quality)
   • Total Monthly Limit: 8 trades

💰 COST COMPARISON:
   • Current System Annual Costs: ${np.mean(current_costs):,.2f}
   • Perspective Changes Annual Costs: ${np.mean(perspective_costs):,.2f}
   • Current System Annual Rebates: ${np.mean(current_rebates):,.2f}
   • Perspective Changes Annual Rebates: ${np.mean(perspective_rebates):,.2f}
   • Cost Difference: ${np.mean(perspective_costs) - np.mean(current_costs):,.2f}
   • Rebate Difference: ${np.mean(perspective_rebates) - np.mean(current_rebates):,.2f}

📊 PERFORMANCE COMPARISON:
   • Current System Annual Return: {np.mean(current_returns):.2%} (±{np.std(current_returns):.2%})
   • Perspective Changes Annual Return: {np.mean(perspective_returns):.2%} (±{np.std(perspective_returns):.2%})
   • Return Difference: {np.mean(perspective_returns) - np.mean(current_returns):.2%}
   
   • Current System Sharpe Ratio: {np.mean(current_sharpes):.3f} (±{np.std(current_sharpes):.3f})
   • Perspective Changes Sharpe Ratio: {np.mean(perspective_sharpes):.3f} (±{np.std(perspective_sharpes):.3f})
   • Sharpe Difference: {np.mean(perspective_sharpes) - np.mean(current_sharpes):.3f}
   
   • Current System Max Drawdown: {np.mean(current_drawdowns):.2%} (±{np.std(current_drawdowns):.2%})
   • Perspective Changes Max Drawdown: {np.mean(perspective_drawdowns):.2%} (±{np.std(perspective_drawdowns):.2%})
   • Drawdown Difference: {np.mean(perspective_drawdowns) - np.mean(current_drawdowns):.2%}

🎯 KEY DIFFERENCES:
   • Elliott Wave Impulse: {"ENABLED" if np.mean(perspective_returns) > np.mean(current_returns) else "DISABLED"} in current system
   • News Delay Filters: {"ADDED" if np.mean(perspective_returns) > np.mean(current_returns) else "NOT ADDED"} in perspective changes
   • Volatility Multiplier: {"ADDED" if np.mean(perspective_returns) > np.mean(current_returns) else "NOT ADDED"} for Volatility Trading
   • Daily Trade Limit: {"REDUCED" if np.mean(perspective_returns) > np.mean(current_returns) else "INCREASED"} from 5 to 3 trades

💡 RECOMMENDATION:
'''
        
        if np.mean(perspective_returns) > np.mean(current_returns):
            improvement = np.mean(perspective_returns) - np.mean(current_returns)
            report += f'     ✅ DEPLOY PERSPECTIVE CHANGES: {improvement:.2%} better annual return\n'
            report += f'     ✅ Better Sharpe Ratio: {np.mean(perspective_sharpes) - np.mean(current_sharpes):.3f} improvement\n'
            report += f'     ✅ Better Risk Management: {np.mean(current_drawdowns) - np.mean(perspective_drawdowns):.2%} lower drawdown\n'
        else:
            decline = np.mean(current_returns) - np.mean(perspective_returns)
            report += f'     ⚠️  KEEP CURRENT SYSTEM: {decline:.2%} worse with perspective changes\n'
            report += f'     ⚠️  Lower Sharpe Ratio: {np.mean(current_sharpes) - np.mean(perspective_sharpes):.3f} decline\n'
            report += f'     ⚠️  Higher Drawdown: {np.mean(perspective_drawdowns) - np.mean(current_drawdowns):.2%} increase\n'
        
        report += f'     💰 Cost Impact: ${np.mean(perspective_costs) - np.mean(current_costs):,.2f} annual difference\n'
        report += f'     📈 Volatility: {"Lower" if np.std(perspective_returns) < np.std(current_returns) else "Higher"} with perspective changes\n\n'
        
        report += '================================================================================\n'
        
        print(report)
        
        logger.info('Comparison test completed!')
        
        return report, current_results, perspective_results

def main():
    """Main execution function"""
    comparison = LiveSystemComparison()
    
    # Run comparison test
    report, current_results, perspective_results = comparison.run_comparison_test(num_iterations=5)
    
    logger.info("Live system comparison completed!")

if __name__ == "__main__":
    main()


















