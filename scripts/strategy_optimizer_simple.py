#!/usr/bin/env python3
"""
Strategy Optimizer (Simplified)
Automatically optimizes strategy selection based on performance
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class StrategyMetrics:
    """Strategy performance metrics"""
    name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float
    volatility: float
    calmar_ratio: float
    sortino_ratio: float


class StrategyOptimizer:
    """Optimize strategy selection based on performance"""
    
    def __init__(self):
        self.strategy_metrics: Dict[str, StrategyMetrics] = {}
        self.optimization_history: List[Dict] = []
        self.current_weights: Dict[str, float] = {}
        self.performance_thresholds = {
            'min_sharpe': 0.5,
            'max_drawdown': 0.15,
            'min_win_rate': 0.45,
            'min_profit_factor': 1.2
        }
    
    def add_strategy_performance(self, strategy_name: str, metrics: StrategyMetrics):
        """Add strategy performance metrics"""
        self.strategy_metrics[strategy_name] = metrics
        logger.info(f"📊 Added performance for {strategy_name}: Sharpe={metrics.sharpe_ratio:.3f}, Win Rate={metrics.win_rate:.1%}")
    
    def calculate_strategy_score(self, metrics: StrategyMetrics) -> float:
        """Calculate overall strategy score"""
        # Weighted scoring system
        weights = {
            'sharpe_ratio': 0.25,
            'win_rate': 0.20,
            'profit_factor': 0.20,
            'calmar_ratio': 0.15,
            'sortino_ratio': 0.10,
            'volatility': 0.10
        }
        
        # Normalize metrics to 0-1 scale
        normalized_metrics = {
            'sharpe_ratio': min(max(metrics.sharpe_ratio / 2.0, 0), 1),  # Cap at 2.0
            'win_rate': metrics.win_rate,
            'profit_factor': min(max(metrics.profit_factor / 3.0, 0), 1),  # Cap at 3.0
            'calmar_ratio': min(max(metrics.calmar_ratio / 2.0, 0), 1),  # Cap at 2.0
            'sortino_ratio': min(max(metrics.sortino_ratio / 2.0, 0), 1),  # Cap at 2.0
            'volatility': max(0, 1 - metrics.volatility)  # Lower volatility is better
        }
        
        # Calculate weighted score
        score = sum(
            weights[metric] * normalized_metrics[metric]
            for metric in weights.keys()
        )
        
        return score
    
    def optimize_strategy_weights(self) -> Dict[str, float]:
        """Optimize strategy weights based on performance"""
        logger.info("🚀 Optimizing strategy weights...")
        
        if not self.strategy_metrics:
            logger.warning("No strategy metrics available for optimization")
            return {}
        
        # Calculate scores for all strategies
        strategy_scores = {}
        for name, metrics in self.strategy_metrics.items():
            score = self.calculate_strategy_score(metrics)
            strategy_scores[name] = score
            
            logger.info(f"   {name}: Score={score:.3f}, Sharpe={metrics.sharpe_ratio:.3f}, Win Rate={metrics.win_rate:.1%}")
        
        # Filter strategies that meet minimum thresholds
        qualified_strategies = {}
        for name, metrics in self.strategy_metrics.items():
            if (metrics.sharpe_ratio >= self.performance_thresholds['min_sharpe'] and
                metrics.max_drawdown <= self.performance_thresholds['max_drawdown'] and
                metrics.win_rate >= self.performance_thresholds['min_win_rate'] and
                metrics.profit_factor >= self.performance_thresholds['min_profit_factor']):
                qualified_strategies[name] = strategy_scores[name]
        
        if not qualified_strategies:
            logger.warning("No strategies meet performance thresholds")
            return {}
        
        # Calculate weights based on scores
        total_score = sum(qualified_strategies.values())
        if total_score == 0:
            # Equal weights if all scores are 0
            weight = 1.0 / len(qualified_strategies)
            optimized_weights = {name: weight for name in qualified_strategies.keys()}
        else:
            optimized_weights = {
                name: score / total_score
                for name, score in qualified_strategies.items()
            }
        
        # Log optimization results
        logger.info("✅ Strategy optimization completed:")
        for name, weight in optimized_weights.items():
            metrics = self.strategy_metrics[name]
            logger.info(f"   {name}: Weight={weight:.1%}, Sharpe={metrics.sharpe_ratio:.3f}")
        
        # Store optimization history
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'weights': optimized_weights.copy(),
            'qualified_strategies': list(qualified_strategies.keys()),
            'total_strategies': len(self.strategy_metrics)
        })
        
        self.current_weights = optimized_weights
        return optimized_weights
    
    def get_strategy_recommendations(self) -> Dict[str, List[str]]:
        """Get strategy recommendations based on performance"""
        recommendations = {
            'high_performance': [],
            'medium_performance': [],
            'low_performance': [],
            'avoid': []
        }
        
        for name, metrics in self.strategy_metrics.items():
            score = self.calculate_strategy_score(metrics)
            
            if score >= 0.7:
                recommendations['high_performance'].append(name)
            elif score >= 0.5:
                recommendations['medium_performance'].append(name)
            elif score >= 0.3:
                recommendations['low_performance'].append(name)
            else:
                recommendations['avoid'].append(name)
        
        return recommendations
    
    def calculate_average_metrics(self) -> Dict[str, float]:
        """Calculate average metrics across all strategies"""
        if not self.strategy_metrics:
            return {}
        
        total_strategies = len(self.strategy_metrics)
        avg_sharpe = sum(m.sharpe_ratio for m in self.strategy_metrics.values()) / total_strategies
        avg_win_rate = sum(m.win_rate for m in self.strategy_metrics.values()) / total_strategies
        avg_drawdown = sum(m.max_drawdown for m in self.strategy_metrics.values()) / total_strategies
        
        return {
            'avg_sharpe_ratio': avg_sharpe,
            'avg_win_rate': avg_win_rate,
            'avg_max_drawdown': avg_drawdown
        }
    
    def generate_optimization_report(self) -> Dict:
        """Generate comprehensive optimization report"""
        if not self.strategy_metrics:
            return {"error": "No strategy metrics available"}
        
        # Calculate overall statistics
        total_strategies = len(self.strategy_metrics)
        avg_metrics = self.calculate_average_metrics()
        
        # Get recommendations
        recommendations = self.get_strategy_recommendations()
        
        # Get top performers
        sorted_strategies = sorted(
            self.strategy_metrics.items(),
            key=lambda x: self.calculate_strategy_score(x[1]),
            reverse=True
        )
        
        top_performers = [name for name, _ in sorted_strategies[:3]]
        
        return {
            "summary": {
                "total_strategies": total_strategies,
                "avg_sharpe_ratio": avg_metrics['avg_sharpe_ratio'],
                "avg_win_rate": avg_metrics['avg_win_rate'],
                "avg_max_drawdown": avg_metrics['avg_max_drawdown'],
                "optimization_timestamp": datetime.now().isoformat()
            },
            "recommendations": recommendations,
            "top_performers": top_performers,
            "current_weights": self.current_weights,
            "optimization_history": len(self.optimization_history)
        }
    
    def display_optimization_report(self):
        """Display optimization report"""
        report = self.generate_optimization_report()
        
        if "error" in report:
            print(f"❌ {report['error']}")
            return
        
        print("\n" + "="*80)
        print("🚀 STRATEGY OPTIMIZATION REPORT")
        print("="*80)
        
        # Summary
        summary = report['summary']
        print(f"📊 Summary:")
        print(f"   Total Strategies: {summary['total_strategies']}")
        print(f"   Average Sharpe Ratio: {summary['avg_sharpe_ratio']:.3f}")
        print(f"   Average Win Rate: {summary['avg_win_rate']:.1%}")
        print(f"   Average Max Drawdown: {summary['avg_max_drawdown']:.1%}")
        
        # Top Performers
        print(f"\n🏆 Top Performers:")
        for i, strategy in enumerate(report['top_performers'], 1):
            metrics = self.strategy_metrics[strategy]
            score = self.calculate_strategy_score(metrics)
            print(f"   {i}. {strategy}: Score={score:.3f}, Sharpe={metrics.sharpe_ratio:.3f}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for category, strategies in report['recommendations'].items():
            if strategies:
                print(f"   {category.replace('_', ' ').title()}: {', '.join(strategies)}")
        
        # Current Weights
        if report['current_weights']:
            print(f"\n⚖️  Optimized Weights:")
            for strategy, weight in report['current_weights'].items():
                print(f"   {strategy}: {weight:.1%}")
        
        print("="*80)


async def main():
    """Main optimization function"""
    optimizer = StrategyOptimizer()
    
    # Example: Add performance metrics for strategies
    # In practice, these would come from backtesting results
    
    # RiskFirst Strategy (new improved strategy)
    optimizer.add_strategy_performance("RiskFirst", StrategyMetrics(
        name="RiskFirst",
        total_return=0.25,
        sharpe_ratio=1.2,
        max_drawdown=0.08,
        win_rate=0.65,
        profit_factor=1.8,
        total_trades=150,
        avg_trade_duration=2.5,
        volatility=0.12,
        calmar_ratio=3.1,
        sortino_ratio=1.5
    ))
    
    # MarketRegimeAdaptive Strategy
    optimizer.add_strategy_performance("MarketRegimeAdaptive", StrategyMetrics(
        name="MarketRegimeAdaptive",
        total_return=0.30,
        sharpe_ratio=1.4,
        max_drawdown=0.10,
        win_rate=0.60,
        profit_factor=2.0,
        total_trades=120,
        avg_trade_duration=3.0,
        volatility=0.15,
        calmar_ratio=3.0,
        sortino_ratio=1.6
    ))
    
    # MultiTimeframe Strategy
    optimizer.add_strategy_performance("MultiTimeframe", StrategyMetrics(
        name="MultiTimeframe",
        total_return=0.28,
        sharpe_ratio=1.3,
        max_drawdown=0.09,
        win_rate=0.62,
        profit_factor=1.9,
        total_trades=180,
        avg_trade_duration=2.8,
        volatility=0.13,
        calmar_ratio=3.1,
        sortino_ratio=1.4
    ))
    
    # Old WinningEnsemble Strategy (for comparison)
    optimizer.add_strategy_performance("WinningEnsemble", StrategyMetrics(
        name="WinningEnsemble",
        total_return=0.15,
        sharpe_ratio=0.3,
        max_drawdown=0.25,
        win_rate=0.45,
        profit_factor=1.1,
        total_trades=200,
        avg_trade_duration=4.0,
        volatility=0.25,
        calmar_ratio=0.6,
        sortino_ratio=0.4
    ))
    
    # Optimize strategy weights
    optimized_weights = optimizer.optimize_strategy_weights()
    
    # Display report
    optimizer.display_optimization_report()
    
    return optimized_weights


if __name__ == "__main__":
    asyncio.run(main()) 