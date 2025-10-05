# Research: Advanced Portfolio Management System

**Branch**: `002-advanced-portfolio-management` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)

## Research Overview

This document outlines the research findings and technical approaches for implementing the Advanced Portfolio Management System, focusing on Modern Portfolio Theory, Black-Litterman model, risk parity strategies, and dynamic asset allocation optimized for 15-minute delayed data.

## Key Research Areas

### 1. Modern Portfolio Theory (MPT) Implementation

#### **Convex Optimization with cvxpy**
- **Approach**: Use cvxpy for efficient portfolio optimization
- **Benefits**: Handles constraints, transaction costs, and complex objective functions
- **Implementation**: Quadratic programming for mean-variance optimization
- **Performance**: Can handle 50+ assets in <60 seconds

#### **Efficient Frontier Calculation**
- **Method**: Grid search over risk levels with convex optimization
- **Output**: Risk-return pairs for efficient frontier
- **Integration**: Connect with existing backtesting framework
- **Validation**: Compare against benchmark indices

#### **Transaction Cost Modeling**
- **Fixed Costs**: Per-trade fees (e.g., $5 per trade)
- **Variable Costs**: Bid-ask spreads and market impact
- **Implementation**: Add to optimization objective function
- **Impact**: Reduces turnover and improves net returns

### 2. Black-Litterman Model Implementation

#### **Market Equilibrium Views**
- **CAPM Equilibrium**: Use market capitalization weights as starting point
- **Risk Aversion**: Calibrate based on historical market data
- **Implementation**: Matrix operations for view integration
- **Validation**: Compare against market-cap weighted portfolio

#### **User-Defined Views Integration**
- **Absolute Views**: "Asset X will return 5%"
- **Relative Views**: "Asset X will outperform Asset Y by 2%"
- **Confidence Levels**: User-specified uncertainty for each view
- **Implementation**: Bayesian updating of expected returns

#### **Parameter Calibration**
- **Tau (τ)**: Scaling factor for market equilibrium (typically 0.025-0.05)
- **Omega (Ω)**: Uncertainty matrix for views
- **Implementation**: Empirical calibration using historical data
- **Validation**: Backtest parameter sensitivity

### 3. Risk Parity Strategies

#### **Equal Risk Contribution (ERC)**
- **Objective**: Each asset contributes equally to portfolio risk
- **Implementation**: Iterative optimization with risk budget constraints
- **Benefits**: More stable than market-cap weighting
- **Challenges**: Handling assets with zero/negative correlation

#### **Risk Parity with Constraints**
- **Sector Limits**: Maximum exposure per sector (e.g., 30%)
- **Liquidity Constraints**: Minimum market cap requirements
- **Implementation**: Add constraints to ERC optimization
- **Validation**: Stress test during market stress periods

#### **Dynamic Risk Parity**
- **Volatility Targeting**: Adjust weights based on realized volatility
- **Implementation**: Rolling volatility estimation with 15-minute data
- **Benefits**: Adapts to changing market conditions
- **Parameters**: Volatility lookback period (e.g., 30 days)

### 4. Tax-Loss Harvesting Optimization

#### **Tax Rules Implementation**
- **Wash Sale Rules**: 30-day lookback/forward period
- **Long-term vs Short-term**: Different tax rates for different holding periods
- **Implementation**: Track holding periods and tax lots
- **Jurisdictions**: Start with US tax rules, extensible for others

#### **Tax-Aware Rebalancing**
- **Objective**: Minimize tax impact while maintaining portfolio targets
- **Implementation**: Multi-objective optimization (return vs tax cost)
- **Benefits**: Improves after-tax returns
- **Challenges**: Complex optimization with tax lot tracking

#### **Tax Loss Identification**
- **Algorithm**: Identify positions with unrealized losses
- **Replacement**: Find similar assets to maintain exposure
- **Implementation**: Correlation-based asset substitution
- **Validation**: Backtest tax savings vs tracking error

### 5. Portfolio Backtesting Framework

#### **Historical Validation**
- **Period**: 2+ years of historical data
- **Frequency**: Daily rebalancing with 15-minute data updates
- **Metrics**: Sharpe ratio, max drawdown, volatility, alpha
- **Implementation**: Integration with existing backtesting engine

#### **Walk-Forward Analysis**
- **Method**: Rolling optimization windows (e.g., 6-month optimization, 1-month out-of-sample)
- **Benefits**: Tests strategy robustness over time
- **Implementation**: Automated rolling window backtesting
- **Validation**: Compare in-sample vs out-of-sample performance

#### **Transaction Cost Modeling**
- **Fixed Costs**: Per-trade fees
- **Variable Costs**: Bid-ask spreads
- **Market Impact**: Slippage based on trade size
- **Implementation**: Realistic cost modeling for accurate backtesting

### 6. Multi-Asset Class Optimization

#### **Asset Class Definitions**
- **Equities**: Individual stocks, sector ETFs
- **Fixed Income**: Government bonds, corporate bonds, bond ETFs
- **Commodities**: Gold, oil, agricultural products
- **Alternatives**: REITs, infrastructure, private equity proxies
- **Implementation**: Hierarchical optimization with asset class constraints

#### **Correlation Modeling**
- **Dynamic Correlations**: Rolling correlation estimation
- **Regime Detection**: Different correlation structures for different market regimes
- **Implementation**: Multivariate GARCH or copula models
- **Validation**: Test correlation stability over time

#### **Asset Class Constraints**
- **Minimum/Maximum Weights**: Per asset class limits
- **Liquidity Requirements**: Minimum market cap or volume
- **Implementation**: Add constraints to optimization problem
- **Benefits**: Prevents extreme concentrations

### 7. Performance Attribution and Risk Decomposition

#### **Return Attribution**
- **Asset Selection**: Individual asset performance contribution
- **Asset Allocation**: Asset class allocation contribution
- **Interaction**: Combined effect of selection and allocation
- **Implementation**: Brinson model for attribution analysis

#### **Risk Decomposition**
- **Factor Risk**: Exposure to market factors (beta, size, value, momentum)
- **Specific Risk**: Idiosyncratic risk not explained by factors
- **Implementation**: Factor model regression analysis
- **Benefits**: Understand sources of portfolio risk

#### **Risk Budgeting**
- **Risk Contribution**: Each asset's contribution to portfolio risk
- **Risk Limits**: Maximum risk contribution per asset or sector
- **Implementation**: Risk budget optimization
- **Monitoring**: Real-time risk contribution tracking

## Technical Implementation Considerations

### 1. Data Requirements
- **Market Data**: 15-minute delayed OHLCV data for all assets
- **Corporate Actions**: Dividends, splits, mergers for accurate returns
- **Risk-Free Rate**: Treasury bill rates for Sharpe ratio calculation
- **Benchmark Data**: S&P 500, Russell 2000, bond indices

### 2. Computational Performance
- **Optimization Speed**: <60 seconds for 50+ asset optimization
- **Memory Usage**: Efficient matrix operations for large portfolios
- **Caching**: Cache optimization results for repeated calculations
- **Parallelization**: Multi-threaded optimization for multiple portfolios

### 3. Error Handling and Robustness
- **Missing Data**: Handle missing market data gracefully
- **Optimization Failures**: Fallback to simpler optimization methods
- **Numerical Stability**: Robust optimization algorithms
- **Data Quality**: Validate input data before optimization

### 4. Integration with Existing System
- **Market Data Service**: Use existing market data infrastructure
- **Backtesting Engine**: Integrate with existing backtesting framework
- **Risk Management**: Connect with existing risk monitoring
- **Dashboard**: Display portfolio analytics in unified dashboard

## Validation and Testing Strategy

### 1. Unit Testing
- **Optimization Algorithms**: Test individual optimization methods
- **Risk Calculations**: Validate risk metrics calculations
- **Tax Logic**: Test tax-loss harvesting rules
- **Data Processing**: Test data validation and cleaning

### 2. Integration Testing
- **End-to-End**: Test complete portfolio optimization workflow
- **API Integration**: Test service-to-service communication
- **Database Integration**: Test data persistence and retrieval
- **Performance Testing**: Validate computational performance

### 3. Backtesting Validation
- **Historical Performance**: Test strategies on historical data
- **Regime Testing**: Test performance across different market regimes
- **Stress Testing**: Test during market stress periods
- **Benchmark Comparison**: Compare against relevant benchmarks

## Risk Considerations

### 1. Model Risk
- **Assumption Validation**: Test optimization assumptions
- **Parameter Sensitivity**: Test sensitivity to key parameters
- **Model Stability**: Ensure consistent results across time periods
- **Overfitting**: Avoid overfitting to historical data

### 2. Implementation Risk
- **Data Quality**: Ensure high-quality input data
- **Computational Errors**: Robust error handling and validation
- **System Integration**: Test integration with existing systems
- **Performance Monitoring**: Monitor system performance and accuracy

### 3. Market Risk
- **Correlation Breakdown**: Handle correlation changes during stress
- **Liquidity Risk**: Ensure sufficient liquidity for rebalancing
- **Transaction Costs**: Account for realistic transaction costs
- **Market Impact**: Consider market impact of large trades

## Success Metrics

### 1. Performance Metrics
- **Sharpe Ratio**: Risk-adjusted returns vs benchmark
- **Maximum Drawdown**: Worst peak-to-trough decline
- **Alpha**: Excess returns vs benchmark
- **Information Ratio**: Active return vs tracking error

### 2. Risk Metrics
- **Value at Risk (VaR)**: 95% and 99% VaR
- **Conditional VaR**: Expected loss beyond VaR
- **Portfolio Volatility**: Annualized portfolio volatility
- **Beta**: Market sensitivity

### 3. Operational Metrics
- **Optimization Speed**: Time to complete optimization
- **Rebalancing Frequency**: How often rebalancing occurs
- **Transaction Costs**: Total costs as % of portfolio value
- **Tracking Error**: Volatility of excess returns vs benchmark

---

*Research completed for Advanced Portfolio Management System implementation*












