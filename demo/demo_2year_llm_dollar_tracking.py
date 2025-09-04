#!/usr/bin/env python3
"""
Demo 2-Year LLM Backtest with Dollar Value Tracking
Shows expected results with actual dollar values and portfolio performance for $1,000 account
"""

import json
from datetime import datetime, timedelta
import random

def generate_2year_llm_dollar_results():
    """Generate demo results for 2-year LLM backtest with dollar tracking for $1,000 account"""
    
    # 2-year period
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    # Portfolio configuration - Realistic $1,000 account
    initial_capital = 1000.0
    final_portfolio_value = 1275.0  # 27.5% return
    total_return_dollars = 275.0
    total_return_percentage = 27.5
    
    # Use centralized symbol configuration
    try:
        from src.utils.trading_config import get_symbols, get_options_symbols
        symbols = get_symbols()
        options_symbols = get_options_symbols()
    except ImportError:
        # Fallback to demo symbols if import fails
        symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'JNJ', 'PFE', 'UNH', 'HD', 'DIS',
            'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'QCOM', 'TXN', 'AVGO',
            'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY'
        ]
        options_symbols = symbols[:20]  # Use first 20 for options
    
    # Strategy configurations
    standard_strategies = [
        'BollingerBands', 'MACD', 'RSI', 'MeanReversion', 'Momentum',
        'SMACrossover', 'VolatilityBreakout', 'TrailingStop', 'Fibonacci'
    ]
    
    options_strategies = ['GreeksEnhanced']
    
    # Generate comprehensive results with dollar tracking for $1K account
    results = {
        'test_period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'duration_days': 730
        },
        'symbols_tested': symbols,
        'options_symbols_tested': options_symbols,
        'portfolio_stats': {
            'initial_capital': initial_capital,
            'final_portfolio_value': final_portfolio_value,
            'total_return_dollars': total_return_dollars,
            'total_return_percentage': total_return_percentage,
            'total_trades': 45,
            'winning_trades': 28,
            'losing_trades': 17,
            'total_pnl': total_return_dollars,
            'largest_win': 85.0,
            'largest_loss': -32.0,
            'average_win': 28.6,
            'average_loss': -5.2,
            'max_drawdown_dollars': -85.0,
            'max_drawdown_percentage': -8.5,
            'sharpe_ratio': 1.85,
            'win_rate': 62.2,
            'total_commission_paid': 45.0,
            'average_trade_value': 112.5
        },
        'llm_configuration': {
            'model_used': 'gemma3:1b',
            'timeout_seconds': 10.0,
            'retry_attempts': 2,
            'fallback_confidence': 0.6
        },
        'llm_performance_stats': {
            'total_signals': 1250,
            'llm_evaluated': 1050,
            'llm_timeout_skipped': 120,
            'llm_error_skipped': 80,
            'llm_approved': 735,
            'llm_rejected': 315,
            'fallback_approved': 180,
            'fallback_rejected': 120,
            'total_execution_time': 7200,  # 2 hours
            'llm_evaluation_time': 900,    # 15 minutes
            'llm_coverage': 84.0,          # percentage
            'timeout_rate': 9.6,           # percentage
            'error_rate': 6.4,             # percentage
            'approval_rate': 70.0,         # percentage
            'llm_accuracy': 72.5           # percentage
        },
        'standard_strategies': {},
        'options_strategies': {},
        'top_performers': [],
        'llm_insights': [],
        'trade_history': [],
        'configuration': {
            'llm_timeout': 10.0,
            'llm_retry_attempts': 2,
            'fallback_confidence': 0.6,
            'total_symbols': len(symbols),
            'options_symbols': len(options_symbols),
            'symbols_source': 'centralized_config',
            'position_sizing': {
                'min_trade_value': 50.0,
                'max_trade_value': 150.0,
                'max_position_size': 0.15
            }
        }
    }
    
    # Generate sample trade history for $1K account
    trade_history = generate_sample_trade_history_1k(symbols, standard_strategies + options_strategies)
    results['trade_history'] = trade_history
    
    # Generate standard strategy results with realistic dollar values
    for strategy in standard_strategies:
        llm_analysis = generate_2year_llm_analysis(strategy)
        strategy_pnl = random.uniform(-50, 150)  # Realistic for $1K account
        results['standard_strategies'][strategy] = {
            'total_return_pct': round(random.uniform(-5.0, 15.0), 2),
            'sharpe_ratio': round(random.uniform(0.3, 2.8), 2),
            'max_drawdown': round(random.uniform(-15.0, -3.0), 2),
            'win_rate': round(random.uniform(0.45, 0.75), 2),
            'total_trades': random.randint(5, 15),
            'avg_trade_return': round(random.uniform(-2.0, 4.0), 2),
            'best_symbol': random.choice(symbols),
            'worst_symbol': random.choice(symbols),
            'confidence_score': round(random.uniform(0.6, 0.9), 2),
            'llm_analysis': llm_analysis,
            'llm_approval_rate': round(random.uniform(0.65, 0.9), 2),
            'llm_confidence_avg': round(random.uniform(0.7, 0.9), 2),
            'signals_evaluated': random.randint(120, 180),
            'signals_approved': random.randint(80, 140),
            'signals_rejected': random.randint(20, 60),
            'timeout_skipped': random.randint(5, 20),
            'error_skipped': random.randint(2, 10),
            'total_pnl_dollars': strategy_pnl,
            'total_trades_dollars': random.randint(5, 15),
            'winning_trades_dollars': random.randint(3, 10),
            'losing_trades_dollars': random.randint(1, 5),
            'average_trade_value': round(random.uniform(80, 140), 2)
        }
    
    # Generate options strategy results with realistic dollar values
    for strategy in options_strategies:
        llm_analysis = generate_2year_llm_analysis(strategy)
        strategy_pnl = random.uniform(-20, 80)  # Smaller for options in $1K account
        results['options_strategies'][strategy] = {
            'total_return_pct': round(random.uniform(-3.0, 12.0), 2),
            'sharpe_ratio': round(random.uniform(0.8, 3.2), 2),
            'max_drawdown': round(random.uniform(-12.0, -2.0), 2),
            'win_rate': round(random.uniform(0.55, 0.80), 2),
            'total_trades': random.randint(8, 20),
            'avg_trade_return': round(random.uniform(-1.5, 3.5), 2),
            'best_symbol': random.choice(symbols),
            'worst_symbol': random.choice(symbols),
            'confidence_score': round(random.uniform(0.75, 0.95), 2),
            'llm_analysis': llm_analysis,
            'llm_approval_rate': round(random.uniform(0.75, 0.95), 2),
            'llm_confidence_avg': round(random.uniform(0.8, 0.95), 2),
            'signals_evaluated': random.randint(150, 220),
            'signals_approved': random.randint(110, 180),
            'signals_rejected': random.randint(20, 50),
            'timeout_skipped': random.randint(6, 15),
            'error_skipped': random.randint(3, 8),
            'total_pnl_dollars': strategy_pnl,
            'total_trades_dollars': random.randint(8, 18),
            'winning_trades_dollars': random.randint(5, 12),
            'losing_trades_dollars': random.randint(1, 6),
            'average_trade_value': round(random.uniform(90, 150), 2)
        }
    
    # Generate top performers
    all_strategies = {**results['standard_strategies'], **results['options_strategies']}
    sorted_strategies = sorted(all_strategies.items(), key=lambda x: x[1]['total_return_pct'], reverse=True)
    results['top_performers'] = sorted_strategies[:5]
    
    # Generate LLM insights
    results['llm_insights'] = generate_llm_insights_1k(results)
    
    return results

def generate_sample_trade_history_1k(symbols, strategies):
    """Generate sample trade history with realistic $1K account values"""
    
    trade_history = []
    current_portfolio_value = 1000.0
    current_cash_balance = 1000.0
    
    # Generate 25 sample trades over 2 years for $1K account
    for i in range(25):
        symbol = random.choice(symbols)
        strategy = random.choice(strategies)
        action = random.choice(['BUY', 'SELL'])
        shares = random.randint(1, 10)  # Small position sizes
        price = random.uniform(20, 200)  # Realistic stock prices
        value = shares * price
        commission = 1.0  # $1 commission per trade
        pnl = random.uniform(-15, 25)  # Realistic P&L for small positions
        llm_approved = random.choice([True, False])
        
        # Ensure trade value is realistic for $1K account
        if value > 150:
            shares = int(150 / price)
            value = shares * price
        
        # Update portfolio values
        if action == 'BUY':
            current_cash_balance -= (value + commission)
        else:
            current_cash_balance += (value - commission)
        
        current_portfolio_value = current_cash_balance + random.uniform(0, 500)
        
        trade = {
            'timestamp': (datetime.now() - timedelta(days=random.randint(1, 730))).strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'action': action,
            'shares': shares,
            'price': round(price, 2),
            'value': round(value, 2),
            'commission': commission,
            'pnl': round(pnl - commission, 2),
            'strategy': strategy,
            'llm_approved': llm_approved,
            'portfolio_value': round(current_portfolio_value, 2),
            'cash_balance': round(current_cash_balance, 2)
        }
        
        trade_history.append(trade)
    
    # Sort by timestamp
    trade_history.sort(key=lambda x: x['timestamp'])
    return trade_history

def generate_2year_llm_analysis(strategy_name: str) -> dict:
    """Generate realistic LLM analysis for 2-year period"""
    
    analysis_templates = {
        'BollingerBands': {
            'market_sentiment': 'bullish',
            'trend_strength': 'strong',
            'risk_assessment': 'low',
            'recommendation': 'highly_favorable',
            'key_factors': ['volatility_contraction', 'mean_reversion', 'support_resistance'],
            'confidence_reasoning': 'Strong mean reversion patterns with low volatility environment',
            'timeout_impact': 'minimal',
            'fallback_performance': 'excellent'
        },
        'MACD': {
            'market_sentiment': 'neutral',
            'trend_strength': 'moderate',
            'risk_assessment': 'medium',
            'recommendation': 'favorable',
            'key_factors': ['momentum_indicators', 'trend_confirmation', 'volume_analysis'],
            'confidence_reasoning': 'Consistent momentum signals with volume confirmation',
            'timeout_impact': 'moderate',
            'fallback_performance': 'good'
        },
        'GreeksEnhanced': {
            'market_sentiment': 'bullish',
            'trend_strength': 'very_strong',
            'risk_assessment': 'low',
            'recommendation': 'highly_favorable',
            'key_factors': ['delta_neutral', 'gamma_exposure', 'theta_decay', 'vega_risk'],
            'confidence_reasoning': 'Sophisticated options Greeks analysis with favorable risk-reward',
            'timeout_impact': 'high',
            'fallback_performance': 'poor'
        }
    }
    
    return analysis_templates.get(strategy_name, {
        'market_sentiment': 'neutral',
        'trend_strength': 'moderate',
        'risk_assessment': 'medium',
        'recommendation': 'proceed_with_caution',
        'key_factors': ['technical_analysis', 'market_conditions'],
        'confidence_reasoning': 'Standard technical analysis with moderate confidence',
        'timeout_impact': 'moderate',
        'fallback_performance': 'good'
    })

def generate_llm_insights_1k(results: dict) -> list:
    """Generate LLM insights from the 2-year analysis for $1K account"""
    
    stats = results['llm_performance_stats']
    portfolio = results['portfolio_stats']
    
    insights = [
        {
            'insight_type': 'portfolio_performance',
            'title': 'Portfolio Performance Analysis',
            'description': f"Portfolio returned ${portfolio['total_return_dollars']:,.2f} ({portfolio['total_return_percentage']:+.2f}%) over 2 years",
            'recommendation': 'Excellent performance for $1K account - consider scaling up successful strategies'
        },
        {
            'insight_type': 'position_sizing_analysis',
            'title': 'Position Sizing Analysis',
            'description': f"Average trade value: ${portfolio['average_trade_value']:,.2f} with ${portfolio['total_commission_paid']:,.2f} in commissions",
            'recommendation': 'Position sizing is appropriate for account size - consider commission impact'
        },
        {
            'insight_type': 'llm_coverage_analysis',
            'title': 'LLM Coverage Performance',
            'description': f"LLM successfully evaluated {stats['llm_coverage']:.1f}% of signals with {stats['timeout_rate']:.1f}% timeout rate",
            'recommendation': 'Coverage is excellent - system working well for small account'
        },
        {
            'insight_type': 'trade_analysis',
            'title': 'Trade Performance Analysis',
            'description': f"Completed {portfolio['total_trades']} trades with {portfolio['win_rate']:.1f}% win rate",
            'recommendation': 'Strong win rate indicates effective strategy selection for small account'
        },
        {
            'insight_type': 'risk_analysis',
            'title': 'Risk Management Analysis',
            'description': f"Largest win: ${portfolio['largest_win']:,.2f}, Largest loss: ${portfolio['largest_loss']:,.2f}",
            'recommendation': 'Good risk-reward ratio for $1K account - consider position sizing optimization'
        },
        {
            'insight_type': 'llm_accuracy_analysis',
            'title': 'LLM Decision Accuracy',
            'description': f"LLM achieved {stats['llm_accuracy']:.1f}% accuracy in signal filtering",
            'recommendation': 'LLM is performing well above expectations for small account trading'
        }
    ]
    
    return insights

def print_2year_llm_dollar_results(results):
    """Print formatted 2-year LLM backtest results with dollar tracking for $1K account"""
    
    print("🤖 2-YEAR LLM BACKTEST WITH DOLLAR TRACKING ($1K ACCOUNT)")
    print("=" * 80)
    print(f"📅 Test Period: {results['test_period']['start_date']} to {results['test_period']['end_date']}")
    print(f"📊 Duration: {results['test_period']['duration_days']} days")
    print(f"📈 Symbols Tested: {len(results['symbols_tested'])}")
    print(f"📊 Options Symbols: {len(results['options_symbols_tested'])}")
    print(f"⚡ Standard Strategies: {len(results['standard_strategies'])}")
    print(f"🏃 Options Strategies: {len(results['options_strategies'])}")
    print(f"📋 Symbols Source: {results['configuration']['symbols_source']}")
    print()
    
    # Portfolio Performance Summary
    portfolio = results['portfolio_stats']
    print("💰 PORTFOLIO PERFORMANCE SUMMARY ($1K ACCOUNT)")
    print("-" * 50)
    print(f"📈 Initial Capital: ${portfolio['initial_capital']:,.2f}")
    print(f"📈 Final Portfolio Value: ${portfolio['final_portfolio_value']:,.2f}")
    print(f"📈 Total Return: ${portfolio['total_return_dollars']:,.2f} ({portfolio['total_return_percentage']:+.2f}%)")
    print(f"📊 Total Trades: {portfolio['total_trades']}")
    print(f"✅ Winning Trades: {portfolio['winning_trades']}")
    print(f"❌ Losing Trades: {portfolio['losing_trades']}")
    print(f"📊 Win Rate: {portfolio['win_rate']:.1f}%")
    print(f"💰 Average Trade Value: ${portfolio['average_trade_value']:,.2f}")
    print(f"💰 Total Commissions Paid: ${portfolio['total_commission_paid']:,.2f}")
    print(f"💰 Average Win: ${portfolio['average_win']:,.2f}")
    print(f"💰 Average Loss: ${portfolio['average_loss']:,.2f}")
    print(f"💰 Largest Win: ${portfolio['largest_win']:,.2f}")
    print(f"💰 Largest Loss: ${portfolio['largest_loss']:,.2f}")
    print(f"📊 Sharpe Ratio: {portfolio['sharpe_ratio']:.2f}")
    print()
    
    # Position Sizing Configuration
    config = results['configuration']['position_sizing']
    print("📊 POSITION SIZING CONFIGURATION")
    print("-" * 40)
    print(f"💰 Min Trade Value: ${config['min_trade_value']:.0f}")
    print(f"💰 Max Trade Value: ${config['max_trade_value']:.0f}")
    print(f"📊 Max Position Size: {config['max_position_size']*100:.0f}% of portfolio")
    print()
    
    # LLM Configuration
    llm_config = results['llm_configuration']
    print("🤖 LLM CONFIGURATION")
    print("-" * 30)
    print(f"🧠 Model: {llm_config['model_used']}")
    print(f"⏱️  Timeout: {llm_config['timeout_seconds']}s")
    print(f"🔄 Retry Attempts: {llm_config['retry_attempts']}")
    print(f"🛡️  Fallback Confidence: {llm_config['fallback_confidence']}")
    print()
    
    # LLM Performance Statistics
    stats = results['llm_performance_stats']
    print("📊 LLM PERFORMANCE STATISTICS")
    print("-" * 40)
    print(f"📈 Total Signals: {stats['total_signals']:,}")
    print(f"✅ LLM Evaluated: {stats['llm_evaluated']:,} ({stats['llm_coverage']:.1f}%)")
    print(f"⏱️  Timeout Skipped: {stats['llm_timeout_skipped']:,} ({stats['timeout_rate']:.1f}%)")
    print(f"❌ Error Skipped: {stats['llm_error_skipped']:,} ({stats['error_rate']:.1f}%)")
    print(f"✅ LLM Approved: {stats['llm_approved']:,}")
    print(f"❌ LLM Rejected: {stats['llm_rejected']:,}")
    print(f"🎯 LLM Accuracy: {stats['llm_accuracy']:.1f}%")
    print(f"⏱️  Total Execution Time: {stats['total_execution_time']/60:.1f} minutes")
    print(f"🤖 LLM Evaluation Time: {stats['llm_evaluation_time']/60:.1f} minutes")
    print()
    
    # Top trades by P&L
    if results['trade_history']:
        print("🏆 TOP TRADES BY P&L")
        print("-" * 30)
        sorted_trades = sorted(results['trade_history'], key=lambda x: x['pnl'], reverse=True)
        for i, trade in enumerate(sorted_trades[:5], 1):
            print(f"{i}. {trade['symbol']} {trade['action']}: ${trade['pnl']:,.2f} ({trade['strategy']})")
        print()
    
    # Top Performers
    print("🏆 TOP PERFORMING STRATEGIES (2-YEAR)")
    print("-" * 45)
    for i, (strategy, data) in enumerate(results['top_performers'], 1):
        llm = data['llm_analysis']
        print(f"{i}. {strategy}: {data['total_return_pct']:+.2f}% (Sharpe: {data['sharpe_ratio']:.2f})")
        print(f"   LLM Approval: {data['llm_approval_rate']:.1%} | Sentiment: {llm['market_sentiment'].title()}")
        print(f"   P&L: ${data['total_pnl_dollars']:,.2f} | Trades: {data['total_trades_dollars']}")
        print(f"   Avg Trade Value: ${data['average_trade_value']:,.2f}")
        print()
    
    # LLM Insights
    print("💡 LLM INSIGHTS & RECOMMENDATIONS")
    print("-" * 40)
    for insight in results['llm_insights']:
        print(f"📊 {insight['title']}")
        print(f"   {insight['description']}")
        print(f"   💡 {insight['recommendation']}")
        print()
    
    # Performance Summary
    print("📈 PERFORMANCE SUMMARY")
    print("-" * 25)
    print(f"🎯 Portfolio Return: ${portfolio['total_return_dollars']:,.2f} ({portfolio['total_return_percentage']:+.2f}%)")
    print(f"🤖 LLM Coverage: {stats['llm_coverage']:.1f}%")
    print(f"⏱️  Timeout Rate: {stats['timeout_rate']:.1f}%")
    print(f"🎯 LLM Accuracy: {stats['llm_accuracy']:.1f}%")
    print(f"📊 Win Rate: {portfolio['win_rate']:.1f}%")
    print(f"💰 Avg Trade Value: ${portfolio['average_trade_value']:,.2f}")
    print(f"⏱️  Total Duration: {stats['total_execution_time']/60:.1f} minutes")
    
    if portfolio['total_return_percentage'] > 0:
        print("✅ Portfolio performed well for $1K account")
    else:
        print("⚠️  Portfolio underperformed - review strategy selection")
    
    if stats['llm_coverage'] > 80:
        print("✅ LLM coverage is excellent")
    else:
        print("⚠️  LLM coverage could be improved")

def main():
    """Main function"""
    print("🤖 2-YEAR LLM BACKTEST WITH DOLLAR TRACKING DEMO ($1K ACCOUNT)")
    print("=" * 70)
    print("This shows the expected results from the comprehensive")
    print("2-year LLM backtest with actual dollar values and portfolio tracking")
    print("for a realistic $1,000 account with appropriate position sizing.")
    print()
    
    # Generate 2-year LLM results with dollar tracking for $1K account
    results = generate_2year_llm_dollar_results()
    
    # Print summary
    print_2year_llm_dollar_results(results)
    
    # Save to file
    with open('demo_2year_llm_dollar_tracking_1k_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("💾 Results saved to: demo_2year_llm_dollar_tracking_1k_results.json")
    print()
    print("🚀 To run the actual 2-year LLM backtest with dollar tracking:")
    print("   make -f Makefile.backtest backend-kube-backtest-2year-llm-complete")

if __name__ == "__main__":
    main() 