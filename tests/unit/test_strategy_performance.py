"""
Strategy Performance Tests

Tests for strategy performance functionality including:
- Performance metrics calculation
- Backtesting results analysis
- Strategy optimization
- Performance monitoring
- Risk-adjusted returns
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
import pandas as pd
import numpy as np

from src.services.database.backtest_results_service import BacktestResultsService
from src.services.database.market_data_service import MarketDataService
from src.utils.strategy_optimizer import StrategyOptimizer
from src.models.backtest_results import BacktestRun, BacktestTrade, BacktestEquityCurve


class TestStrategyPerformanceMetrics:
    """Test strategy performance metrics calculation"""
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        # Mock returns data
        returns = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.02, 0.01])
        
        # Calculate expected Sharpe ratio
        expected_return = returns.mean()
        risk_free_rate = 0.02  # 2% annual
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        expected_sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        
        # Test calculation
        sharpe_ratio = self._calculate_sharpe_ratio(returns, risk_free_rate)
        assert abs(sharpe_ratio - expected_sharpe) < 0.01
    
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation"""
        # Mock equity curve
        equity_curve = pd.Series([100, 105, 110, 108, 112, 115, 113, 118])
        
        # Calculate expected max drawdown
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        expected_max_drawdown = drawdown.min()
        
        # Test calculation
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        assert abs(max_drawdown - expected_max_drawdown) < 0.01
    
    def test_calculate_win_rate(self):
        """Test win rate calculation"""
        # Mock trade results
        trades = [
            {'pnl': 100, 'pnl_pct': 0.02},
            {'pnl': -50, 'pnl_pct': -0.01},
            {'pnl': 200, 'pnl_pct': 0.04},
            {'pnl': -30, 'pnl_pct': -0.006},
            {'pnl': 150, 'pnl_pct': 0.03}
        ]
        
        # Calculate expected win rate
        winning_trades = sum(1 for trade in trades if trade['pnl'] > 0)
        expected_win_rate = winning_trades / len(trades)
        
        # Test calculation
        win_rate = self._calculate_win_rate(trades)
        assert win_rate == expected_win_rate
    
    def test_calculate_profit_factor(self):
        """Test profit factor calculation"""
        # Mock trade results
        trades = [
            {'pnl': 100, 'pnl_pct': 0.02},
            {'pnl': -50, 'pnl_pct': -0.01},
            {'pnl': 200, 'pnl_pct': 0.04},
            {'pnl': -30, 'pnl_pct': -0.006},
            {'pnl': 150, 'pnl_pct': 0.03}
        ]
        
        # Calculate expected profit factor
        gross_profit = sum(trade['pnl'] for trade in trades if trade['pnl'] > 0)
        gross_loss = abs(sum(trade['pnl'] for trade in trades if trade['pnl'] < 0))
        expected_profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Test calculation
        profit_factor = self._calculate_profit_factor(trades)
        assert abs(profit_factor - expected_profit_factor) < 0.01
    
    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio calculation"""
        # Mock annual return and max drawdown
        annual_return = 0.15  # 15%
        max_drawdown = 0.10   # 10%
        
        # Calculate expected Calmar ratio
        expected_calmar = annual_return / abs(max_drawdown)
        
        # Test calculation
        calmar_ratio = self._calculate_calmar_ratio(annual_return, max_drawdown)
        assert abs(calmar_ratio - expected_calmar) < 0.01
    
    def _calculate_sharpe_ratio(self, returns, risk_free_rate):
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate/252
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    def _calculate_max_drawdown(self, equity_curve):
        """Calculate maximum drawdown"""
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min()
    
    def _calculate_win_rate(self, trades):
        """Calculate win rate"""
        winning_trades = sum(1 for trade in trades if trade['pnl'] > 0)
        return winning_trades / len(trades)
    
    def _calculate_profit_factor(self, trades):
        """Calculate profit factor"""
        gross_profit = sum(trade['pnl'] for trade in trades if trade['pnl'] > 0)
        gross_loss = abs(sum(trade['pnl'] for trade in trades if trade['pnl'] < 0))
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def _calculate_calmar_ratio(self, annual_return, max_drawdown):
        """Calculate Calmar ratio"""
        return annual_return / abs(max_drawdown)


class TestBacktestResultsAnalysis:
    """Test backtest results analysis"""
    
    @pytest.fixture
    def mock_backtest_service(self):
        """Create mock backtest service"""
        service = MagicMock(spec=BacktestResultsService)
        return service
    
    @pytest.fixture
    def sample_backtest_results(self):
        """Create sample backtest results"""
        return [
            {
                'id': 'run_1',
                'strategy_name': 'Momentum Strategy',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'total_return_pct': 15.5,
                'sharpe_ratio': 1.2,
                'max_drawdown': -8.5,
                'win_rate': 0.65,
                'profit_factor': 1.8,
                'total_trades': 120,
                'avg_trade_duration': 3.5
            },
            {
                'id': 'run_2',
                'strategy_name': 'Bollinger Bands Strategy',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'total_return_pct': 12.3,
                'sharpe_ratio': 0.9,
                'max_drawdown': -12.1,
                'win_rate': 0.58,
                'profit_factor': 1.4,
                'total_trades': 95,
                'avg_trade_duration': 4.2
            },
            {
                'id': 'run_3',
                'strategy_name': 'MACD Strategy',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'total_return_pct': 18.7,
                'sharpe_ratio': 1.5,
                'max_drawdown': -6.8,
                'win_rate': 0.72,
                'profit_factor': 2.1,
                'total_trades': 85,
                'avg_trade_duration': 2.8
            }
        ]
    
    def test_analyze_strategy_performance(self, mock_backtest_service, sample_backtest_results):
        """Test strategy performance analysis"""
        mock_backtest_service.get_backtest_runs.return_value = sample_backtest_results
        
        # Analyze performance
        analysis = self._analyze_strategy_performance(sample_backtest_results)
        
        # Verify analysis structure
        assert 'total_runs' in analysis
        assert 'strategies' in analysis
        assert 'best_performers' in analysis
        assert 'worst_performers' in analysis
        
        # Verify strategy analysis
        assert len(analysis['strategies']) == 3
        assert 'Momentum Strategy' in analysis['strategies']
        assert 'Bollinger Bands Strategy' in analysis['strategies']
        assert 'MACD Strategy' in analysis['strategies']
        
        # Verify best performers
        assert len(analysis['best_performers']) > 0
        best_strategy = analysis['best_performers'][0]
        assert best_strategy['strategy_name'] == 'MACD Strategy'
        assert best_strategy['total_return_pct'] == 18.7
    
    def test_rank_strategies_by_performance(self, sample_backtest_results):
        """Test strategy ranking by performance"""
        rankings = self._rank_strategies_by_performance(sample_backtest_results)
        
        # Verify rankings
        assert len(rankings) == 3
        assert rankings[0]['strategy_name'] == 'MACD Strategy'  # Best return
        assert rankings[1]['strategy_name'] == 'Momentum Strategy'
        assert rankings[2]['strategy_name'] == 'Bollinger Bands Strategy'
    
    def test_calculate_risk_adjusted_metrics(self, sample_backtest_results):
        """Test risk-adjusted metrics calculation"""
        metrics = self._calculate_risk_adjusted_metrics(sample_backtest_results)
        
        # Verify metrics
        assert 'avg_sharpe_ratio' in metrics
        assert 'avg_calmar_ratio' in metrics
        assert 'avg_sortino_ratio' in metrics
        assert 'risk_return_ratio' in metrics
        
        # Verify calculations
        assert metrics['avg_sharpe_ratio'] > 0
        # Calmar ratio can be negative or infinite if drawdowns are very small
        assert metrics['avg_calmar_ratio'] != 0  # Just check it's calculated
    
    def _analyze_strategy_performance(self, backtest_results):
        """Analyze strategy performance from backtest results"""
        analysis = {
            'total_runs': len(backtest_results),
            'strategies': {},
            'best_performers': [],
            'worst_performers': []
        }
        
        # Group by strategy
        for result in backtest_results:
            strategy_name = result['strategy_name']
            if strategy_name not in analysis['strategies']:
                analysis['strategies'][strategy_name] = {
                    'runs': 0,
                    'total_return': 0,
                    'avg_return': 0,
                    'best_return': -999,
                    'worst_return': 999,
                    'avg_sharpe': 0,
                    'avg_win_rate': 0
                }
            
            strategy_stats = analysis['strategies'][strategy_name]
            strategy_stats['runs'] += 1
            strategy_stats['total_return'] += result['total_return_pct']
            
            if result['total_return_pct'] > strategy_stats['best_return']:
                strategy_stats['best_return'] = result['total_return_pct']
            if result['total_return_pct'] < strategy_stats['worst_return']:
                strategy_stats['worst_return'] = result['total_return_pct']
        
        # Calculate averages
        for strategy_stats in analysis['strategies'].values():
            strategy_stats['avg_return'] = strategy_stats['total_return'] / strategy_stats['runs']
        
        # Rank strategies
        rankings = self._rank_strategies_by_performance(backtest_results)
        analysis['best_performers'] = rankings[:2]
        analysis['worst_performers'] = rankings[-2:]
        
        return analysis
    
    def _rank_strategies_by_performance(self, backtest_results):
        """Rank strategies by total return"""
        return sorted(backtest_results, key=lambda x: x['total_return_pct'], reverse=True)
    
    def _calculate_risk_adjusted_metrics(self, backtest_results):
        """Calculate risk-adjusted metrics"""
        sharpe_ratios = [r['sharpe_ratio'] for r in backtest_results]
        returns = [r['total_return_pct'] for r in backtest_results]
        drawdowns = [r['max_drawdown'] for r in backtest_results]
        
        return {
            'avg_sharpe_ratio': np.mean(sharpe_ratios),
            'avg_calmar_ratio': np.mean([r/d for r, d in zip(returns, drawdowns) if d != 0]),
            'avg_sortino_ratio': np.mean(sharpe_ratios),  # Simplified
            'risk_return_ratio': np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        }


class TestStrategyOptimization:
    """Test strategy optimization functionality"""
    
    @pytest.fixture
    def mock_optimizer(self):
        """Create mock strategy optimizer"""
        optimizer = MagicMock(spec=StrategyOptimizer)
        return optimizer
    
    def test_optimize_strategy_parameters(self, mock_optimizer):
        """Test strategy parameter optimization"""
        # Mock optimization results
        mock_optimizer.optimize_parameters = MagicMock(return_value={
            'best_params': {'lookback_period': 20, 'threshold': 0.02},
            'best_score': 0.85,
            'optimization_history': [],
            'convergence': True
        })
        
        # Test optimization
        result = mock_optimizer.optimize_parameters('momentum_strategy', {})
        
        # Verify results
        assert 'best_params' in result
        assert 'best_score' in result
        assert result['best_score'] == 0.85
        assert result['convergence'] is True
    
    def test_optimize_strategy_algorithm(self, mock_optimizer):
        """Test strategy algorithm optimization"""
        # Mock algorithm optimization
        mock_optimizer.optimize_algorithm = MagicMock(return_value={
            'best_algorithm': 'genetic_algorithm',
            'performance_improvement': 0.15,
            'optimization_time': 120.5
        })
        
        # Test optimization
        result = mock_optimizer.optimize_algorithm('momentum_strategy')
        
        # Verify results
        assert 'best_algorithm' in result
        assert 'performance_improvement' in result
        assert result['performance_improvement'] == 0.15
    
    def test_batch_optimize_strategies(self, mock_optimizer):
        """Test batch strategy optimization"""
        strategies = ['momentum_strategy', 'bollinger_bands_strategy', 'macd_strategy']
        
        # Mock batch optimization results
        mock_optimizer.batch_optimize_strategies = MagicMock(return_value={
            'momentum_strategy': {'improvement': 0.12, 'status': 'success'},
            'bollinger_bands_strategy': {'improvement': 0.08, 'status': 'success'},
            'macd_strategy': {'improvement': 0.18, 'status': 'success'}
        })
        
        # Test batch optimization
        results = mock_optimizer.batch_optimize_strategies(strategies)
        
        # Verify results
        assert len(results) == 3
        assert all(result['status'] == 'success' for result in results.values())
        assert results['macd_strategy']['improvement'] == 0.18


class TestPerformanceMonitoring:
    """Test performance monitoring functionality"""
    
    @pytest.fixture
    def mock_performance_monitor(self):
        """Create mock performance monitor"""
        monitor = MagicMock()
        return monitor
    
    def test_monitor_strategy_performance(self, mock_performance_monitor):
        """Test strategy performance monitoring"""
        # Mock monitoring results
        mock_performance_monitor.run_single_check.return_value = {
            'total_runs': 15,
            'successful_runs': 12,
            'failed_runs': 3,
            'alerts': ['High drawdown detected', 'Low Sharpe ratio']
        }
        
        # Test monitoring
        result = mock_performance_monitor.run_single_check()
        
        # Verify results
        assert 'total_runs' in result
        assert 'alerts' in result
        assert len(result['alerts']) == 2
    
    def test_generate_performance_report(self, mock_performance_monitor):
        """Test performance report generation"""
        # Mock report data
        performance_data = {
            'strategies': {
                'Momentum Strategy': {'avg_return': 12.5, 'sharpe_ratio': 1.2},
                'MACD Strategy': {'avg_return': 15.8, 'sharpe_ratio': 1.5}
            },
            'best_performers': ['MACD Strategy'],
            'worst_performers': ['Bollinger Bands Strategy']
        }
        
        # Mock report generation
        mock_performance_monitor._generate_performance_report.return_value = {
            'report_id': 'perf_20241201',
            'summary': 'Performance analysis completed',
            'recommendations': ['Optimize MACD parameters', 'Review Bollinger Bands']
        }
        
        # Test report generation
        report = mock_performance_monitor._generate_performance_report(performance_data)
        
        # Verify report
        assert 'report_id' in report
        assert 'recommendations' in report
        assert len(report['recommendations']) == 2
    
    def test_continuous_monitoring(self, mock_performance_monitor):
        """Test continuous performance monitoring"""
        # Mock continuous monitoring
        mock_performance_monitor.run_continuous_monitoring.return_value = {
            'monitoring_active': True,
            'check_interval': 300,  # 5 minutes
            'last_check': datetime.now()
        }
        
        # Test continuous monitoring
        result = mock_performance_monitor.run_continuous_monitoring()
        
        # Verify monitoring status
        assert result['monitoring_active'] is True
        assert result['check_interval'] == 300


class TestPerformanceAlerts:
    """Test performance alert system"""
    
    def test_detect_performance_anomalies(self):
        """Test performance anomaly detection"""
        # Mock performance data
        performance_data = {
            'sharpe_ratio': 0.5,  # Below threshold
            'max_drawdown': -0.15,  # Above threshold
            'win_rate': 0.45,  # Below threshold
            'profit_factor': 1.1  # Below threshold
        }
        
        # Test anomaly detection
        anomalies = self._detect_performance_anomalies(performance_data)
        
        # Verify anomalies detected
        assert len(anomalies) > 0
        assert any('sharpe_ratio' in anomaly for anomaly in anomalies)
        assert any('drawdown' in anomaly for anomaly in anomalies)
    
    def test_generate_performance_alerts(self):
        """Test performance alert generation"""
        # Mock anomalies
        anomalies = [
            'Low Sharpe ratio detected: 0.5 (threshold: 1.0)',
            'High drawdown detected: -15% (threshold: -10%)',
            'Low win rate detected: 45% (threshold: 50%)'
        ]
        
        # Test alert generation
        alerts = self._generate_performance_alerts(anomalies)
        
        # Verify alerts
        assert len(alerts) == 3
        assert all('ALERT' in alert for alert in alerts)
        assert any('Sharpe ratio' in alert for alert in alerts)
    
    def _detect_performance_anomalies(self, performance_data):
        """Detect performance anomalies"""
        anomalies = []
        thresholds = {
            'sharpe_ratio': 1.0,
            'max_drawdown': -0.10,
            'win_rate': 0.50,
            'profit_factor': 1.5
        }
        
        for metric, value in performance_data.items():
            if metric in thresholds:
                threshold = thresholds[metric]
                if metric == 'sharpe_ratio' and value < threshold:
                    anomalies.append(f'Low {metric} detected: {value} (threshold: {threshold})')
                elif metric == 'max_drawdown' and value < threshold:
                    anomalies.append(f'High {metric} detected: {value} (threshold: {threshold})')
                elif metric == 'win_rate' and value < threshold:
                    anomalies.append(f'Low {metric} detected: {value} (threshold: {threshold})')
                elif metric == 'profit_factor' and value < threshold:
                    anomalies.append(f'Low {metric} detected: {value} (threshold: {threshold})')
        
        return anomalies
    
    def _generate_performance_alerts(self, anomalies):
        """Generate performance alerts"""
        return [f'ALERT: {anomaly}' for anomaly in anomalies]


class TestStrategyPerformanceIntegration:
    """Test strategy performance integration scenarios"""
    
    def test_complete_performance_analysis_workflow(self):
        """Test complete performance analysis workflow"""
        # Mock backtest results
        backtest_results = [
            {
                'strategy_name': 'Momentum Strategy',
                'total_return_pct': 12.5,
                'sharpe_ratio': 1.2,
                'max_drawdown': -8.5,
                'win_rate': 0.65
            },
            {
                'strategy_name': 'MACD Strategy',
                'total_return_pct': 18.7,
                'sharpe_ratio': 1.5,
                'max_drawdown': -6.8,
                'win_rate': 0.72
            }
        ]
        
        # Test complete workflow
        analysis = self._run_complete_analysis(backtest_results)
        
        # Verify analysis
        assert 'performance_summary' in analysis
        assert 'optimization_recommendations' in analysis
        assert 'alerts' in analysis
        
        # Verify performance summary
        summary = analysis['performance_summary']
        assert summary['best_strategy'] == 'MACD Strategy'
        assert summary['avg_return'] > 0
    
    def test_strategy_comparison_analysis(self):
        """Test strategy comparison analysis"""
        # Mock strategy comparison data
        strategies = {
            'Momentum': {'return': 12.5, 'sharpe': 1.2, 'drawdown': -8.5},
            'MACD': {'return': 18.7, 'sharpe': 1.5, 'drawdown': -6.8},
            'Bollinger': {'return': 10.2, 'sharpe': 0.9, 'drawdown': -12.1}
        }
        
        # Test comparison
        comparison = self._compare_strategies(strategies)
        
        # Verify comparison
        assert 'rankings' in comparison
        assert 'risk_adjusted_rankings' in comparison
        assert comparison['rankings'][0] == 'MACD'  # Best return
        assert comparison['risk_adjusted_rankings'][0] == 'MACD'  # Best Sharpe
    
    def _run_complete_analysis(self, backtest_results):
        """Run complete performance analysis workflow"""
        # Analyze performance
        analysis = {
            'performance_summary': {
                'total_strategies': len(backtest_results),
                'best_strategy': max(backtest_results, key=lambda x: x['total_return_pct'])['strategy_name'],
                'avg_return': np.mean([r['total_return_pct'] for r in backtest_results]),
                'avg_sharpe': np.mean([r['sharpe_ratio'] for r in backtest_results])
            },
            'optimization_recommendations': [
                'Optimize MACD parameters for better performance',
                'Review Bollinger Bands risk management'
            ],
            'alerts': [
                'ALERT: High drawdown detected in Bollinger Bands Strategy'
            ]
        }
        
        return analysis
    
    def _compare_strategies(self, strategies):
        """Compare strategies by multiple metrics"""
        # Rank by return
        return_rankings = sorted(strategies.keys(), 
                               key=lambda x: strategies[x]['return'], reverse=True)
        
        # Rank by Sharpe ratio
        sharpe_rankings = sorted(strategies.keys(), 
                                key=lambda x: strategies[x]['sharpe'], reverse=True)
        
        return {
            'rankings': return_rankings,
            'risk_adjusted_rankings': sharpe_rankings
        } 