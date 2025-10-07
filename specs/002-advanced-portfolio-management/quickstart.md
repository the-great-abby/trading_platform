# Quickstart Guide: Advanced Portfolio Management System

**Branch**: `002-advanced-portfolio-management` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)

## Quickstart Overview

This guide provides step-by-step instructions for setting up and using the Advanced Portfolio Management System. You'll learn how to create portfolios, run optimizations, implement Black-Litterman views, and perform risk parity optimization.

## Prerequisites

### System Requirements
- Python 3.11+
- PostgreSQL/TimescaleDB database
- Redis cache
- Market data service (15-minute delayed data)
- Kubernetes cluster (for production deployment)

### Required Python Packages
```bash
pip install numpy scipy pandas scikit-learn cvxpy PyPortfolioOpt
pip install sqlalchemy alembic psycopg2-binary redis
pip install fastapi uvicorn pytest pytest-asyncio
```

### Database Setup
```bash
# Create database tables
alembic upgrade head

# Verify database connection
python -c "from src.database import engine; print('Database connected successfully')"
```

## 1. Basic Portfolio Creation

### Create Your First Portfolio

```python
from src.portfolio.portfolio_manager import PortfolioManager
from src.portfolio.models import Portfolio, RiskTolerance, RebalancingFrequency

# Initialize portfolio manager
portfolio_manager = PortfolioManager()

# Create a new portfolio
portfolio = portfolio_manager.create_portfolio(
    name="My First Portfolio",
    description="A diversified portfolio using Modern Portfolio Theory",
    base_currency="USD",
    risk_tolerance=RiskTolerance.MODERATE,
    rebalancing_frequency=RebalancingFrequency.MONTHLY,
    max_single_asset_weight=0.10,  # 10% max per asset
    max_sector_weight=0.30,        # 30% max per sector
    long_only=True
)

print(f"Created portfolio: {portfolio.portfolio_id}")
print(f"Portfolio value: ${portfolio.total_value:,.2f}")
```

### Add Assets to Portfolio

```python
# Add positions to your portfolio
positions = [
    {"asset_id": "AAPL", "quantity": 100, "average_cost": 150.00},
    {"asset_id": "MSFT", "quantity": 50, "average_cost": 300.00},
    {"asset_id": "GOOGL", "quantity": 20, "average_cost": 2500.00},
    {"asset_id": "TSLA", "quantity": 30, "average_cost": 200.00},
    {"asset_id": "SPY", "quantity": 200, "average_cost": 400.00},
]

for position in positions:
    portfolio_manager.add_position(
        portfolio_id=portfolio.portfolio_id,
        asset_id=position["asset_id"],
        quantity=position["quantity"],
        average_cost=position["average_cost"]
    )

print("Added positions to portfolio")
```

## 2. Modern Portfolio Theory Optimization

### Basic MPT Optimization

```python
from src.portfolio.optimization.mpt_optimizer import MPTOptimizer

# Initialize MPT optimizer
mpt_optimizer = MPTOptimizer()

# Run optimization
optimization_result = mpt_optimizer.optimize_portfolio(
    portfolio_id=portfolio.portfolio_id,
    risk_free_rate=0.02,  # 2% risk-free rate
    optimization_method="max_sharpe"  # Maximize Sharpe ratio
)

print(f"Expected Return: {optimization_result.expected_return:.2%}")
print(f"Expected Volatility: {optimization_result.expected_volatility:.2%}")
print(f"Sharpe Ratio: {optimization_result.sharpe_ratio:.3f}")

# View optimal weights
print("\nOptimal Asset Weights:")
for asset_id, weight in optimization_result.asset_weights.items():
    print(f"  {asset_id}: {weight:.2%}")
```

### Efficient Frontier Analysis

```python
# Generate efficient frontier
efficient_frontier = mpt_optimizer.generate_efficient_frontier(
    portfolio_id=portfolio.portfolio_id,
    num_points=20,
    risk_free_rate=0.02
)

print("Efficient Frontier Points:")
for point in efficient_frontier:
    print(f"  Risk: {point.volatility:.2%}, Return: {point.expected_return:.2%}, Sharpe: {point.sharpe_ratio:.3f}")

# Find optimal portfolio for specific risk level
target_volatility = 0.15  # 15% target volatility
optimal_portfolio = mpt_optimizer.optimize_for_target_volatility(
    portfolio_id=portfolio.portfolio_id,
    target_volatility=target_volatility
)
print(f"\nOptimal portfolio for {target_volatility:.1%} volatility:")
print(f"  Expected Return: {optimal_portfolio.expected_return:.2%}")
print(f"  Sharpe Ratio: {optimal_portfolio.sharpe_ratio:.3f}")
```

## 3. Black-Litterman Model Implementation

### Create Market Views

```python
from src.portfolio.optimization.black_litterman import BlackLittermanOptimizer
from src.portfolio.models import MarketView, ViewType

# Initialize Black-Litterman optimizer
bl_optimizer = BlackLittermanOptimizer()

# Create absolute view: "AAPL will return 8% annually"
absolute_view = MarketView(
    portfolio_id=portfolio.portfolio_id,
    view_type=ViewType.ABSOLUTE,
    view_description="AAPL will return 8% annually",
    target_asset_id="AAPL",
    expected_return=0.08,
    confidence_level=0.7  # 70% confidence
)

# Create relative view: "Technology will outperform Healthcare by 3%"
relative_view = MarketView(
    portfolio_id=portfolio.portfolio_id,
    view_type=ViewType.RELATIVE,
    view_description="Technology will outperform Healthcare by 3%",
    outperforming_asset_id="XLK",  # Technology ETF
    underperforming_asset_id="XLV",  # Healthcare ETF
    relative_return=0.03,
    confidence_level=0.6  # 60% confidence
)

# Add views to portfolio
portfolio_manager.add_market_view(absolute_view)
portfolio_manager.add_market_view(relative_view)

print("Added market views to portfolio")
```

### Run Black-Litterman Optimization

```python
# Run Black-Litterman optimization with views
bl_result = bl_optimizer.optimize_with_views(
    portfolio_id=portfolio.portfolio_id,
    market_views=[absolute_view, relative_view],
    risk_free_rate=0.02,
    tau=0.025  # Scaling factor for market equilibrium
)

print("Black-Litterman Optimization Results:")
print(f"Expected Return: {bl_result.expected_return:.2%}")
print(f"Expected Volatility: {bl_result.expected_volatility:.2%}")
print(f"Sharpe Ratio: {bl_result.sharpe_ratio:.3f}")

print("\nUpdated Asset Weights:")
for asset_id, weight in bl_result.asset_weights.items():
    print(f"  {asset_id}: {weight:.2%}")

# Compare with market equilibrium weights
equilibrium_weights = bl_optimizer.get_market_equilibrium_weights(
    portfolio_id=portfolio.portfolio_id
)

print("\nWeight Changes vs Market Equilibrium:")
for asset_id in bl_result.asset_weights:
    bl_weight = bl_result.asset_weights[asset_id]
    eq_weight = equilibrium_weights.get(asset_id, 0.0)
    change = bl_weight - eq_weight
    print(f"  {asset_id}: {change:+.2%}")
```

## 4. Risk Parity Optimization

### Basic Risk Parity Implementation

```python
from src.portfolio.optimization.risk_parity import RiskParityOptimizer

# Initialize risk parity optimizer
rp_optimizer = RiskParityOptimizer()

# Run equal risk contribution optimization
rp_result = rp_optimizer.optimize_equal_risk_contribution(
    portfolio_id=portfolio.portfolio_id,
    rebalance_threshold=0.05  # 5% drift threshold
)

print("Risk Parity Optimization Results:")
print(f"Expected Return: {rp_result.expected_return:.2%}")
print(f"Expected Volatility: {rp_result.expected_volatility:.2%}")
print(f"Sharpe Ratio: {rp_result.sharpe_ratio:.3f}")

print("\nRisk Parity Weights:")
for asset_id, weight in rp_result.asset_weights.items():
    risk_contrib = rp_result.risk_contributions.get(asset_id, 0.0)
    print(f"  {asset_id}: {weight:.2%} (Risk Contribution: {risk_contrib:.2%})")

# Verify equal risk contribution
total_risk_contrib = sum(rp_result.risk_contributions.values())
expected_contrib = 1.0 / len(rp_result.risk_contributions)
print(f"\nRisk Contribution Verification:")
print(f"Expected per asset: {expected_contrib:.2%}")
print(f"Actual range: {min(rp_result.risk_contributions.values()):.2%} - {max(rp_result.risk_contributions.values()):.2%}")
```

### Risk Parity with Constraints

```python
# Risk parity with sector constraints
constrained_rp_result = rp_optimizer.optimize_with_constraints(
    portfolio_id=portfolio.portfolio_id,
    max_sector_weight=0.40,  # 40% max per sector
    min_weight=0.01,         # 1% minimum weight
    max_weight=0.20          # 20% maximum weight
)

print("Constrained Risk Parity Results:")
print(f"Expected Return: {constrained_rp_result.expected_return:.2%}")
print(f"Expected Volatility: {constrained_rp_result.expected_volatility:.2%}")

print("\nConstrained Weights:")
for asset_id, weight in constrained_rp_result.asset_weights.items():
    print(f"  {asset_id}: {weight:.2%}")
```

## 5. Portfolio Rebalancing

### Generate Rebalancing Recommendations

```python
from src.portfolio.rebalancing.rebalancing_manager import RebalancingManager

# Initialize rebalancing manager
rebalancing_manager = RebalancingManager()

# Generate rebalancing recommendations
recommendations = rebalancing_manager.generate_rebalancing_recommendations(
    portfolio_id=portfolio.portfolio_id,
    target_optimization_id=bl_result.optimization_id,  # Use Black-Litterman result
    rebalancing_threshold=0.05,  # 5% drift threshold
    transaction_cost_rate=0.001,  # 0.1% transaction cost
    market_impact_rate=0.0005     # 0.05% market impact
)

print(f"Generated {recommendations.total_trades} rebalancing trades")
print(f"Estimated transaction cost: ${recommendations.estimated_transaction_cost:,.2f}")
print(f"Estimated market impact: ${recommendations.estimated_market_impact:,.2f}")
print(f"Rebalancing urgency: {recommendations.rebalancing_urgency:.1%}")

print("\nRecommended Trades:")
for trade in recommendations.trades:
    action = "BUY" if trade.trade_quantity > 0 else "SELL"
    print(f"  {action} {abs(trade.trade_quantity):,.0f} shares of {trade.asset_id}")
    print(f"    Current weight: {trade.current_weight:.2%}")
    print(f"    Target weight: {trade.target_weight:.2%}")
    print(f"    Estimated cost: ${trade.estimated_cost:,.2f}")
    if trade.is_tax_loss_harvest:
        print(f"    Tax savings: ${trade.estimated_tax_savings:,.2f}")
```

### Execute Rebalancing

```python
# Execute rebalancing recommendations
execution_result = rebalancing_manager.execute_rebalancing(
    recommendation_id=recommendations.recommendation_id,
    dry_run=False  # Set to True for simulation only
)

if execution_result.success:
    print("Rebalancing executed successfully!")
    print(f"Actual transaction cost: ${execution_result.actual_cost:,.2f}")
    print(f"Trades executed: {execution_result.trades_executed}")
    print(f"Execution time: {execution_result.execution_time:.2f} seconds")
else:
    print(f"Rebalancing failed: {execution_result.error_message}")
```

## 6. Tax-Loss Harvesting

### Identify Tax-Loss Harvesting Opportunities

```python
from src.portfolio.tax.tax_optimizer import TaxOptimizer

# Initialize tax optimizer
tax_optimizer = TaxOptimizer()

# Identify tax-loss harvesting opportunities
tax_opportunities = tax_optimizer.identify_tax_loss_harvesting(
    portfolio_id=portfolio.portfolio_id,
    min_loss_threshold=0.05,  # 5% minimum loss
    wash_sale_period=30       # 30-day wash sale rule
)

print(f"Found {len(tax_opportunities)} tax-loss harvesting opportunities")

for opportunity in tax_opportunities:
    print(f"\nTax-Loss Harvesting Opportunity:")
    print(f"  Asset: {opportunity.asset_id}")
    print(f"  Current loss: {opportunity.unrealized_loss:.2%}")
    print(f"  Estimated tax savings: ${opportunity.estimated_tax_savings:,.2f}")
    print(f"  Replacement asset: {opportunity.replacement_asset_id}")
    print(f"  Tracking error risk: {opportunity.tracking_error_risk:.2%}")

# Execute tax-loss harvesting
if tax_opportunities:
    best_opportunity = max(tax_opportunities, key=lambda x: x.estimated_tax_savings)
    
    harvest_result = tax_optimizer.execute_tax_loss_harvesting(
        portfolio_id=portfolio.portfolio_id,
        opportunity=best_opportunity
    )
    
    print(f"\nTax-loss harvesting executed:")
    print(f"  Tax savings realized: ${harvest_result.tax_savings:,.2f}")
    print(f"  Tracking error: {harvest_result.tracking_error:.2%}")
```

## 7. Portfolio Backtesting

### Historical Performance Validation

```python
from src.portfolio.backtesting.portfolio_backtester import PortfolioBacktester

# Initialize portfolio backtester
backtester = PortfolioBacktester()

# Run historical backtest
backtest_result = backtester.run_historical_backtest(
    portfolio_id=portfolio.portfolio_id,
    start_date="2023-01-01",
    end_date="2024-12-31",
    rebalancing_frequency="monthly",
    transaction_cost_rate=0.001,
    benchmark_symbol="SPY"
)

print("Portfolio Backtest Results:")
print(f"Total Return: {backtest_result.total_return:.2%}")
print(f"Annualized Return: {backtest_result.annualized_return:.2%}")
print(f"Volatility: {backtest_result.volatility:.2%}")
print(f"Sharpe Ratio: {backtest_result.sharpe_ratio:.3f}")
print(f"Maximum Drawdown: {backtest_result.max_drawdown:.2%}")
print(f"Calmar Ratio: {backtest_result.calmar_ratio:.3f}")

print(f"\nBenchmark Comparison (SPY):")
print(f"Benchmark Return: {backtest_result.benchmark_return:.2%}")
print(f"Alpha: {backtest_result.alpha:.2%}")
print(f"Beta: {backtest_result.beta:.3f}")
print(f"Information Ratio: {backtest_result.information_ratio:.3f}")
print(f"Tracking Error: {backtest_result.tracking_error:.2%}")

# Performance attribution
print(f"\nPerformance Attribution:")
print(f"Asset Selection: {backtest_result.asset_selection_contribution:.2%}")
print(f"Asset Allocation: {backtest_result.asset_allocation_contribution:.2%}")
print(f"Interaction: {backtest_result.interaction_contribution:.2%}")
```

### Walk-Forward Analysis

```python
# Run walk-forward analysis
wf_result = backtester.run_walk_forward_analysis(
    portfolio_id=portfolio.portfolio_id,
    start_date="2023-01-01",
    end_date="2024-12-31",
    optimization_window=180,  # 6 months optimization window
    out_of_sample_window=30,  # 1 month out-of-sample
    rebalancing_frequency="monthly"
)

print("Walk-Forward Analysis Results:")
print(f"Average In-Sample Sharpe: {wf_result.avg_in_sample_sharpe:.3f}")
print(f"Average Out-of-Sample Sharpe: {wf_result.avg_out_of_sample_sharpe:.3f}")
print(f"Sharpe Ratio Stability: {wf_result.sharpe_stability:.3f}")
print(f"Number of Optimizations: {wf_result.num_optimizations}")

print(f"\nOut-of-Sample Performance by Period:")
for i, period in enumerate(wf_result.out_of_sample_periods):
    print(f"  Period {i+1}: Return {period.return:.2%}, Sharpe {period.sharpe:.3f}")
```

## 8. Risk Monitoring and Analysis

### Portfolio Risk Metrics

```python
from src.portfolio.risk.risk_manager import RiskManager

# Initialize risk manager
risk_manager = RiskManager()

# Calculate comprehensive risk metrics
risk_metrics = risk_manager.calculate_portfolio_risk(
    portfolio_id=portfolio.portfolio_id,
    lookback_period=252,  # 1 year of daily data
    confidence_levels=[0.95, 0.99]
)

print("Portfolio Risk Metrics:")
print(f"Value at Risk (95%): {risk_metrics.var_95:.2%}")
print(f"Value at Risk (99%): {risk_metrics.var_99:.2%}")
print(f"Conditional VaR (95%): {risk_metrics.cvar_95:.2%}")
print(f"Conditional VaR (99%): {risk_metrics.cvar_99:.2%}")

print(f"\nRisk Decomposition:")
print(f"Systematic Risk: {risk_metrics.systematic_risk:.2%}")
print(f"Idiosyncratic Risk: {risk_metrics.idiosyncratic_risk:.2%}")

print(f"\nFactor Exposures:")
print(f"Market Beta: {risk_metrics.market_beta:.3f}")
print(f"Size Factor: {risk_metrics.size_factor_exposure:.3f}")
print(f"Value Factor: {risk_metrics.value_factor_exposure:.3f}")
print(f"Momentum Factor: {risk_metrics.momentum_factor_exposure:.3f}")

print(f"\nRisk Contributions by Asset:")
for asset_id, contribution in risk_metrics.risk_contributions.items():
    print(f"  {asset_id}: {contribution:.2%}")
```

### Stress Testing

```python
# Run stress tests
stress_scenarios = {
    "Market Crash": -0.20,      # 20% market decline
    "Tech Selloff": -0.15,      # 15% tech sector decline
    "Interest Rate Shock": 0.02,  # 2% interest rate increase
    "Volatility Spike": 0.50     # 50% volatility increase
}

stress_results = risk_manager.run_stress_tests(
    portfolio_id=portfolio.portfolio_id,
    scenarios=stress_scenarios
)

print("Stress Test Results:")
for scenario, result in stress_results.items():
    print(f"  {scenario}: {result:.2%} portfolio return")
```

## 9. API Usage Examples

### REST API Calls

```python
import requests

# Portfolio API base URL
API_BASE = "http://localhost:11101"  # Adjust port as needed

# Create portfolio via API
portfolio_data = {
    "name": "API Portfolio",
    "description": "Portfolio created via API",
    "risk_tolerance": "MODERATE",
    "rebalancing_frequency": "MONTHLY"
}

response = requests.post(f"{API_BASE}/portfolios", json=portfolio_data)
portfolio = response.json()
print(f"Created portfolio: {portfolio['portfolio_id']}")

# Run optimization via API
optimization_data = {
    "portfolio_id": portfolio["portfolio_id"],
    "optimization_method": "MPT",
    "risk_free_rate": 0.02
}

response = requests.post(f"{API_BASE}/optimize", json=optimization_data)
optimization_result = response.json()
print(f"Optimization completed: {optimization_result['optimization_id']}")

# Get portfolio performance
response = requests.get(f"{API_BASE}/portfolios/{portfolio['portfolio_id']}/performance")
performance = response.json()
print(f"Portfolio return: {performance['total_return']:.2%}")
```

## 10. Configuration and Customization

### Portfolio Configuration

```python
# Load configuration
from src.utils.trading_config import TradingConfig

config = TradingConfig()

# Customize optimization parameters
config.portfolio_optimization.max_optimization_time = 60  # 60 seconds
config.portfolio_optimization.default_risk_free_rate = 0.02
config.portfolio_optimization.transaction_cost_rate = 0.001

# Customize risk management
config.risk_management.max_single_asset_weight = 0.15  # 15% max
config.risk_management.max_sector_weight = 0.40        # 40% max
config.risk_management.var_confidence_level = 0.95     # 95% VaR

# Customize rebalancing
config.rebalancing.default_threshold = 0.05            # 5% drift
config.rebalancing.min_trade_size = 100.0              # $100 minimum
config.rebalancing.tax_loss_harvesting_enabled = True

print("Configuration loaded and customized")
```

### Custom Optimization Strategies

```python
# Create custom optimization strategy
from src.portfolio.optimization.base import BaseOptimizer

class CustomOptimizer(BaseOptimizer):
    def optimize(self, portfolio_id: str, **kwargs):
        # Custom optimization logic
        # This is a template - implement your custom strategy
        pass

# Use custom optimizer
custom_optimizer = CustomOptimizer()
result = custom_optimizer.optimize(portfolio_id=portfolio.portfolio_id)
```

## Troubleshooting

### Common Issues

1. **Optimization Fails to Converge**
   ```python
   # Increase optimization time limit
   config.portfolio_optimization.max_optimization_time = 120
   
   # Check for constraint violations
   if not optimization_result.convergence_status:
       print("Optimization failed to converge")
       print(f"Violations: {optimization_result.constraint_violations}")
   ```

2. **Missing Market Data**
   ```python
   # Check data availability
   from src.market_data.data_service import DataService
   
   data_service = DataService()
   available_data = data_service.check_data_availability(
       symbols=["AAPL", "MSFT", "GOOGL"],
       start_date="2023-01-01",
       end_date="2024-12-31"
   )
   
   for symbol, available in available_data.items():
       if not available:
           print(f"Missing data for {symbol}")
   ```

3. **Portfolio Weights Don't Sum to 1.0**
   ```python
   # Validate portfolio weights
   total_weight = sum(optimization_result.asset_weights.values())
   if abs(total_weight - 1.0) > 0.001:
       print(f"Weight sum error: {total_weight:.6f}")
       # Normalize weights
       normalized_weights = {
           asset: weight / total_weight 
           for asset, weight in optimization_result.asset_weights.items()
       }
   ```

### Performance Optimization

```python
# Enable caching for repeated optimizations
config.portfolio_optimization.enable_caching = True
config.portfolio_optimization.cache_ttl = 3600  # 1 hour

# Use parallel processing for multiple portfolios
config.portfolio_optimization.parallel_optimization = True
config.portfolio_optimization.max_workers = 4

# Optimize database queries
config.database.connection_pool_size = 20
config.database.query_timeout = 30
```

## Next Steps

1. **Explore Advanced Features**: Implement custom optimization strategies, alternative risk models
2. **Integration**: Connect with your existing trading system and market data feeds
3. **Monitoring**: Set up alerts for portfolio drift, risk limit breaches, and rebalancing opportunities
4. **Automation**: Schedule regular optimizations and rebalancing based on your investment strategy
5. **Scaling**: Deploy to production Kubernetes cluster for high availability and performance

---

*Quickstart guide completed for Advanced Portfolio Management System*






















