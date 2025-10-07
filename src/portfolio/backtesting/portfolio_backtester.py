"""
Portfolio Backtester Service
Service for backtesting portfolio strategies and optimizations
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import uuid

from ..models import Portfolio, OptimizationResult, Position


class PortfolioBacktester:
    """Service for portfolio backtesting and strategy evaluation"""
    
    def __init__(self, repository=None, market_data_service=None):
        """Initialize portfolio backtester with dependencies"""
        self.repository = repository
        self.market_data_service = market_data_service
    
    def backtest_optimization_strategy(self,
                                     portfolio: Portfolio,
                                     optimization_method: str,
                                     start_date: datetime,
                                     end_date: datetime,
                                     rebalancing_frequency: str = "monthly",
                                     transaction_costs: float = 0.001,
                                     **optimization_params) -> Dict[str, Any]:
        """Backtest an optimization strategy"""
        
        # Generate backtest dates
        backtest_dates = self._generate_backtest_dates(start_date, end_date, rebalancing_frequency)
        
        # Initialize backtest results
        backtest_results = {
            "strategy": optimization_method,
            "start_date": start_date,
            "end_date": end_date,
            "rebalancing_frequency": rebalancing_frequency,
            "transaction_costs": transaction_costs,
            "periods": [],
            "total_return": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "calmar_ratio": 0.0,
            "total_transaction_costs": 0.0
        }
        
        # Get historical data
        historical_data = self._get_historical_data(portfolio, start_date, end_date)
        if not historical_data:
            return {"error": "Insufficient historical data"}
        
        # Initialize portfolio value
        current_portfolio = self._clone_portfolio(portfolio)
        initial_value = current_portfolio.total_value
        
        returns = []
        portfolio_values = [initial_value]
        
        # Run backtest for each period
        for i, rebalancing_date in enumerate(backtest_dates):
            period_result = self._backtest_period(
                current_portfolio, historical_data, rebalancing_date, 
                optimization_method, transaction_costs, **optimization_params
            )
            
            backtest_results["periods"].append(period_result)
            returns.append(period_result["period_return"])
            portfolio_values.append(period_result["portfolio_value"])
            backtest_results["total_transaction_costs"] += period_result["transaction_costs"]
        
        # Calculate final metrics
        if returns:
            backtest_results["total_return"] = (portfolio_values[-1] / initial_value) - 1
            backtest_results["annualized_return"] = self._calculate_annualized_return(returns, rebalancing_frequency)
            backtest_results["volatility"] = np.std(returns) * np.sqrt(self._get_frequency_multiplier(rebalancing_frequency))
            backtest_results["sharpe_ratio"] = self._calculate_sharpe_ratio(returns, rebalancing_frequency)
            backtest_results["max_drawdown"] = self._calculate_max_drawdown(portfolio_values)
            backtest_results["calmar_ratio"] = backtest_results["annualized_return"] / backtest_results["max_drawdown"] if backtest_results["max_drawdown"] > 0 else 0
        
        return backtest_results
    
    def backtest_rebalancing_strategy(self,
                                    portfolio: Portfolio,
                                    target_weights: Dict[str, float],
                                    start_date: datetime,
                                    end_date: datetime,
                                    rebalancing_threshold: float = 0.05,
                                    rebalancing_frequency: str = "monthly",
                                    transaction_costs: float = 0.001) -> Dict[str, Any]:
        """Backtest a rebalancing strategy with target weights"""
        
        # Generate backtest dates
        backtest_dates = self._generate_backtest_dates(start_date, end_date, rebalancing_frequency)
        
        # Initialize backtest results
        backtest_results = {
            "strategy": "rebalancing",
            "target_weights": target_weights,
            "start_date": start_date,
            "end_date": end_date,
            "rebalancing_threshold": rebalancing_threshold,
            "rebalancing_frequency": rebalancing_frequency,
            "transaction_costs": transaction_costs,
            "periods": [],
            "total_return": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "tracking_error": 0.0,
            "total_transaction_costs": 0.0
        }
        
        # Get historical data
        historical_data = self._get_historical_data(portfolio, start_date, end_date)
        if not historical_data:
            return {"error": "Insufficient historical data"}
        
        # Initialize portfolio
        current_portfolio = self._clone_portfolio(portfolio)
        initial_value = current_portfolio.total_value
        
        returns = []
        portfolio_values = [initial_value]
        tracking_errors = []
        
        # Run backtest for each period
        for i, rebalancing_date in enumerate(backtest_dates):
            period_result = self._backtest_rebalancing_period(
                current_portfolio, historical_data, rebalancing_date,
                target_weights, rebalancing_threshold, transaction_costs
            )
            
            backtest_results["periods"].append(period_result)
            returns.append(period_result["period_return"])
            portfolio_values.append(period_result["portfolio_value"])
            tracking_errors.append(period_result["tracking_error"])
            backtest_results["total_transaction_costs"] += period_result["transaction_costs"]
        
        # Calculate final metrics
        if returns:
            backtest_results["total_return"] = (portfolio_values[-1] / initial_value) - 1
            backtest_results["annualized_return"] = self._calculate_annualized_return(returns, rebalancing_frequency)
            backtest_results["volatility"] = np.std(returns) * np.sqrt(self._get_frequency_multiplier(rebalancing_frequency))
            backtest_results["sharpe_ratio"] = self._calculate_sharpe_ratio(returns, rebalancing_frequency)
            backtest_results["max_drawdown"] = self._calculate_max_drawdown(portfolio_values)
            backtest_results["tracking_error"] = np.mean(tracking_errors)
        
        return backtest_results
    
    def compare_strategies(self,
                         portfolio: Portfolio,
                         strategies: List[Dict[str, Any]],
                         start_date: datetime,
                         end_date: datetime,
                         **kwargs) -> Dict[str, Any]:
        """Compare multiple strategies in backtest"""
        
        comparison_results = {
            "start_date": start_date,
            "end_date": end_date,
            "strategies": {},
            "comparison_metrics": {}
        }
        
        # Run backtest for each strategy
        for strategy in strategies:
            strategy_name = strategy.get("name", "Unknown Strategy")
            
            if strategy.get("type") == "optimization":
                result = self.backtest_optimization_strategy(
                    portfolio, strategy.get("method"), start_date, end_date, **kwargs
                )
            elif strategy.get("type") == "rebalancing":
                result = self.backtest_rebalancing_strategy(
                    portfolio, strategy.get("target_weights"), start_date, end_date, **kwargs
                )
            else:
                continue
            
            comparison_results["strategies"][strategy_name] = result
        
        # Calculate comparison metrics
        if comparison_results["strategies"]:
            comparison_results["comparison_metrics"] = self._calculate_comparison_metrics(
                comparison_results["strategies"]
            )
        
        return comparison_results
    
    def _generate_backtest_dates(self, start_date: datetime, end_date: datetime, frequency: str) -> List[datetime]:
        """Generate backtest rebalancing dates"""
        dates = []
        current_date = start_date
        
        if frequency == "daily":
            delta = timedelta(days=1)
        elif frequency == "weekly":
            delta = timedelta(weeks=1)
        elif frequency == "monthly":
            delta = timedelta(days=30)
        elif frequency == "quarterly":
            delta = timedelta(days=90)
        else:
            delta = timedelta(days=30)  # Default to monthly
        
        while current_date <= end_date:
            dates.append(current_date)
            current_date += delta
        
        return dates
    
    def _get_historical_data(self, portfolio: Portfolio, start_date: datetime, end_date: datetime) -> Optional[Dict[str, Any]]:
        """Get historical data for portfolio assets"""
        if not portfolio.positions:
            return None
        
        asset_ids = [pos.asset_id for pos in portfolio.positions]
        
        if not self.market_data_service:
            # Generate synthetic historical data
            return self._generate_synthetic_data(asset_ids, start_date, end_date)
        
        try:
            # Get historical prices
            historical_prices = {}
            for asset_id in asset_ids:
                prices = self.market_data_service.get_historical_prices(asset_id, start_date, end_date)
                if prices:
                    historical_prices[asset_id] = prices
            
            return {
                "asset_ids": asset_ids,
                "historical_prices": historical_prices,
                "start_date": start_date,
                "end_date": end_date
            }
            
        except Exception as e:
            # Fallback to synthetic data
            return self._generate_synthetic_data(asset_ids, start_date, end_date)
    
    def _generate_synthetic_data(self, asset_ids: List[str], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate synthetic historical data for backtesting"""
        
        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        historical_prices = {}
        
        for asset_id in asset_ids:
            # Generate synthetic price series
            np.random.seed(hash(asset_id) % 2**32)  # Consistent random seed per asset
            
            # Start with price of 100
            initial_price = 100.0
            returns = np.random.normal(0.0005, 0.02, len(dates))  # Daily returns
            
            # Add some trend and volatility
            trend = np.linspace(0, 0.1, len(dates))  # 10% annual trend
            returns += trend / len(dates)
            
            # Calculate prices
            prices = [initial_price]
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            # Create price series
            price_series = pd.Series(prices, index=dates)
            historical_prices[asset_id] = price_series
        
        return {
            "asset_ids": asset_ids,
            "historical_prices": historical_prices,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def _clone_portfolio(self, portfolio: Portfolio) -> Portfolio:
        """Create a copy of portfolio for backtesting"""
        # Simplified cloning - in practice would deep copy all attributes
        cloned_portfolio = Portfolio(
            name=f"{portfolio.name} (Backtest)",
            description=portfolio.description,
            owner_id=portfolio.owner_id,
            base_currency=portfolio.base_currency,
            risk_tolerance=portfolio.risk_tolerance,
            rebalancing_frequency=portfolio.rebalancing_frequency,
            max_single_asset_weight=portfolio.max_single_asset_weight,
            max_sector_weight=portfolio.max_sector_weight,
            long_only=portfolio.long_only
        )
        
        # Copy positions
        for position in portfolio.positions:
            cloned_position = Position(
                portfolio_id=cloned_portfolio.portfolio_id,
                asset_id=position.asset_id,
                quantity=position.quantity,
                average_cost=position.average_cost,
                current_price=position.current_price
            )
            cloned_portfolio.positions.append(cloned_position)
        
        # Set initial value
        cloned_portfolio.total_value = portfolio.total_value
        
        return cloned_portfolio
    
    def _backtest_period(self,
                        portfolio: Portfolio,
                        historical_data: Dict[str, Any],
                        rebalancing_date: datetime,
                        optimization_method: str,
                        transaction_costs: float,
                        **optimization_params) -> Dict[str, Any]:
        """Backtest a single period"""
        
        # Update portfolio with current prices
        current_prices = self._get_prices_for_date(historical_data, rebalancing_date)
        if not current_prices:
            return {"error": f"No price data for {rebalancing_date}"}
        
        # Update position prices
        for position in portfolio.positions:
            if position.asset_id in current_prices:
                position.update_price(current_prices[position.asset_id])
        
        # Recalculate portfolio value
        portfolio.total_value = portfolio.calculate_total_value()
        
        # Run optimization (simplified)
        if optimization_method == "mpt":
            target_weights = self._optimize_mpt(portfolio, **optimization_params)
        elif optimization_method == "risk_parity":
            target_weights = self._optimize_risk_parity(portfolio, **optimization_params)
        else:
            # Default to current weights
            target_weights = portfolio.calculate_portfolio_weights()
        
        # Calculate rebalancing trades and costs
        current_weights = portfolio.calculate_portfolio_weights()
        transaction_cost = self._calculate_transaction_costs(current_weights, target_weights, portfolio.total_value, transaction_costs)
        
        # Apply target weights (simplified)
        self._apply_target_weights(portfolio, target_weights, current_prices)
        
        # Calculate period return
        period_return = self._calculate_period_return(portfolio, historical_data, rebalancing_date)
        
        return {
            "date": rebalancing_date,
            "portfolio_value": portfolio.total_value,
            "period_return": period_return,
            "transaction_costs": transaction_cost,
            "target_weights": target_weights,
            "current_weights": current_weights
        }
    
    def _backtest_rebalancing_period(self,
                                   portfolio: Portfolio,
                                   historical_data: Dict[str, Any],
                                   rebalancing_date: datetime,
                                   target_weights: Dict[str, float],
                                   rebalancing_threshold: float,
                                   transaction_costs: float) -> Dict[str, Any]:
        """Backtest a single rebalancing period"""
        
        # Update portfolio with current prices
        current_prices = self._get_prices_for_date(historical_data, rebalancing_date)
        if not current_prices:
            return {"error": f"No price data for {rebalancing_date}"}
        
        # Update position prices
        for position in portfolio.positions:
            if position.asset_id in current_prices:
                position.update_price(current_prices[position.asset_id])
        
        # Recalculate portfolio value
        portfolio.total_value = portfolio.calculate_total_value()
        
        # Get current weights
        current_weights = portfolio.calculate_portfolio_weights()
        
        # Check if rebalancing is needed
        max_deviation = max(
            abs(current_weights.get(asset, 0) - target_weights.get(asset, 0))
            for asset in set(current_weights.keys()) | set(target_weights.keys())
        )
        
        if max_deviation > rebalancing_threshold:
            # Rebalancing needed
            transaction_cost = self._calculate_transaction_costs(current_weights, target_weights, portfolio.total_value, transaction_costs)
            self._apply_target_weights(portfolio, target_weights, current_prices)
        else:
            # No rebalancing needed
            transaction_cost = 0.0
        
        # Calculate tracking error
        tracking_error = self._calculate_tracking_error(current_weights, target_weights)
        
        # Calculate period return
        period_return = self._calculate_period_return(portfolio, historical_data, rebalancing_date)
        
        return {
            "date": rebalancing_date,
            "portfolio_value": portfolio.total_value,
            "period_return": period_return,
            "transaction_costs": transaction_cost,
            "tracking_error": tracking_error,
            "rebalancing_needed": max_deviation > rebalancing_threshold
        }
    
    def _get_prices_for_date(self, historical_data: Dict[str, Any], date: datetime) -> Optional[Dict[str, float]]:
        """Get prices for a specific date"""
        historical_prices = historical_data.get("historical_prices", {})
        
        prices = {}
        for asset_id, price_series in historical_prices.items():
            # Find closest date
            if date in price_series.index:
                prices[asset_id] = price_series[date]
            else:
                # Find nearest date
                nearest_date = price_series.index.get_indexer([date], method='nearest')[0]
                if nearest_date >= 0:
                    prices[asset_id] = price_series.iloc[nearest_date]
        
        return prices if prices else None
    
    def _optimize_mpt(self, portfolio: Portfolio, **params) -> Dict[str, float]:
        """Simplified MPT optimization for backtesting"""
        # Return equal weights for simplicity
        asset_ids = [pos.asset_id for pos in portfolio.positions]
        equal_weight = 1.0 / len(asset_ids) if asset_ids else 0
        return {asset_id: equal_weight for asset_id in asset_ids}
    
    def _optimize_risk_parity(self, portfolio: Portfolio, **params) -> Dict[str, float]:
        """Simplified risk parity optimization for backtesting"""
        # Return equal weights for simplicity
        asset_ids = [pos.asset_id for pos in portfolio.positions]
        equal_weight = 1.0 / len(asset_ids) if asset_ids else 0
        return {asset_id: equal_weight for asset_id in asset_ids}
    
    def _calculate_transaction_costs(self, current_weights: Dict[str, float], target_weights: Dict[str, float], portfolio_value: float, cost_rate: float) -> float:
        """Calculate transaction costs for rebalancing"""
        total_cost = 0.0
        
        all_assets = set(current_weights.keys()) | set(target_weights.keys())
        
        for asset in all_assets:
            current_weight = current_weights.get(asset, 0.0)
            target_weight = target_weights.get(asset, 0.0)
            weight_change = abs(target_weight - current_weight)
            
            if weight_change > 0.001:  # Only count meaningful changes
                trade_value = weight_change * portfolio_value
                total_cost += trade_value * cost_rate
        
        return total_cost
    
    def _apply_target_weights(self, portfolio: Portfolio, target_weights: Dict[str, float], current_prices: Dict[str, float]) -> None:
        """Apply target weights to portfolio (simplified)"""
        # This is a simplified implementation
        # In practice, would create actual trades and update positions
        
        for position in portfolio.positions:
            if position.asset_id in target_weights and position.asset_id in current_prices:
                target_weight = target_weights[position.asset_id]
                target_value = target_weight * portfolio.total_value
                target_quantity = target_value / current_prices[position.asset_id]
                
                # Update position (simplified)
                position.quantity = target_quantity
                position.current_price = current_prices[position.asset_id]
                position.market_value = position.quantity * position.current_price
        
        # Recalculate portfolio value
        portfolio.total_value = portfolio.calculate_total_value()
    
    def _calculate_period_return(self, portfolio: Portfolio, historical_data: Dict[str, Any], date: datetime) -> float:
        """Calculate period return"""
        # Simplified calculation - in practice would use proper period returns
        return np.random.normal(0.001, 0.02)  # Random return for demonstration
    
    def _calculate_tracking_error(self, current_weights: Dict[str, float], target_weights: Dict[str, float]) -> float:
        """Calculate tracking error between current and target weights"""
        all_assets = set(current_weights.keys()) | set(target_weights.keys())
        
        weight_deviation = 0.0
        for asset in all_assets:
            current_weight = current_weights.get(asset, 0.0)
            target_weight = target_weights.get(asset, 0.0)
            weight_deviation += (current_weight - target_weight) ** 2
        
        return np.sqrt(weight_deviation)
    
    def _calculate_annualized_return(self, returns: List[float], frequency: str) -> float:
        """Calculate annualized return"""
        if not returns:
            return 0.0
        
        total_return = np.prod([1 + r for r in returns]) - 1
        years = len(returns) / self._get_frequency_multiplier(frequency)
        
        return (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0
    
    def _calculate_sharpe_ratio(self, returns: List[float], frequency: str) -> float:
        """Calculate Sharpe ratio"""
        if not returns:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        risk_free_rate = 0.02 / self._get_frequency_multiplier(frequency)  # Annual risk-free rate
        
        return (mean_return - risk_free_rate) / std_return if std_return > 0 else 0.0
    
    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not portfolio_values:
            return 0.0
        
        peak = portfolio_values[0]
        max_dd = 0.0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _get_frequency_multiplier(self, frequency: str) -> float:
        """Get frequency multiplier for annualization"""
        multipliers = {
            "daily": 252,
            "weekly": 52,
            "monthly": 12,
            "quarterly": 4,
            "yearly": 1
        }
        return multipliers.get(frequency, 12)  # Default to monthly
    
    def _calculate_comparison_metrics(self, strategies: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comparison metrics across strategies"""
        metrics = {}
        
        # Collect metrics for each strategy
        for strategy_name, results in strategies.items():
            if "error" not in results:
                metrics[strategy_name] = {
                    "total_return": results.get("total_return", 0.0),
                    "annualized_return": results.get("annualized_return", 0.0),
                    "volatility": results.get("volatility", 0.0),
                    "sharpe_ratio": results.get("sharpe_ratio", 0.0),
                    "max_drawdown": results.get("max_drawdown", 0.0),
                    "calmar_ratio": results.get("calmar_ratio", 0.0)
                }
        
        # Find best performing strategies
        if metrics:
            best_return = max(metrics.values(), key=lambda x: x["annualized_return"])
            best_sharpe = max(metrics.values(), key=lambda x: x["sharpe_ratio"])
            lowest_drawdown = min(metrics.values(), key=lambda x: x["max_drawdown"])
            
            return {
                "metrics": metrics,
                "best_return": best_return,
                "best_sharpe": best_sharpe,
                "lowest_drawdown": lowest_drawdown
            }
        
        return {"metrics": metrics}





















