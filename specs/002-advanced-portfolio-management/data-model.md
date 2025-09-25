# Data Model: Advanced Portfolio Management System

**Branch**: `002-advanced-portfolio-management` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)

## Data Model Overview

This document defines the data structures and relationships for the Advanced Portfolio Management System, including portfolio entities, optimization results, risk metrics, and market views.

## Core Entities

### 1. Portfolio Entity

```python
class Portfolio:
    """Core portfolio entity containing assets and metadata"""
    
    # Primary identifiers
    portfolio_id: str                    # Unique portfolio identifier
    name: str                           # Human-readable portfolio name
    description: str                    # Portfolio description
    owner_id: str                       # Portfolio owner/user ID
    
    # Portfolio metadata
    creation_date: datetime             # Portfolio creation timestamp
    last_updated: datetime              # Last modification timestamp
    status: PortfolioStatus             # ACTIVE, INACTIVE, ARCHIVED
    
    # Portfolio configuration
    base_currency: str                  # Base currency (USD, EUR, etc.)
    rebalancing_frequency: RebalancingFrequency  # DAILY, WEEKLY, MONTHLY
    risk_tolerance: RiskTolerance       # CONSERVATIVE, MODERATE, AGGRESSIVE
    
    # Portfolio constraints
    max_single_asset_weight: float      # Maximum weight per asset (e.g., 0.10 = 10%)
    max_sector_weight: float            # Maximum weight per sector
    min_liquidity_requirement: float    # Minimum market cap requirement
    long_only: bool                     # True for long-only portfolios
    
    # Portfolio state
    total_value: float                  # Current portfolio value
    cash_balance: float                 # Available cash
    total_invested: float               # Total amount invested
    unrealized_pnl: float               # Unrealized profit/loss
    realized_pnl: float                 # Realized profit/loss
    
    # Performance metrics (calculated)
    total_return: float                 # Total return percentage
    annualized_return: float            # Annualized return
    volatility: float                   # Portfolio volatility
    sharpe_ratio: float                 # Risk-adjusted return
    max_drawdown: float                 # Maximum drawdown
    calmar_ratio: float                 # Return/max drawdown ratio
    
    # Relationships
    positions: List[Position]           # Portfolio positions
    optimization_results: List[OptimizationResult]  # Historical optimizations
    rebalancing_history: List[RebalancingEvent]     # Rebalancing events
```

### 2. Position Entity

```python
class Position:
    """Individual position within a portfolio"""
    
    # Primary identifiers
    position_id: str                    # Unique position identifier
    portfolio_id: str                   # Parent portfolio ID
    asset_id: str                       # Asset identifier
    
    # Position details
    quantity: float                     # Number of shares/units
    average_cost: float                 # Average cost per share
    current_price: float                # Current market price
    market_value: float                 # Current market value (quantity * price)
    
    # Position metrics
    cost_basis: float                   # Total cost basis
    unrealized_pnl: float               # Unrealized profit/loss
    unrealized_pnl_pct: float           # Unrealized P&L percentage
    weight: float                       # Position weight in portfolio
    
    # Tax information
    holding_period: int                 # Days held
    is_long_term: bool                  # True if held > 1 year
    tax_lot_id: str                     # Tax lot identifier
    
    # Metadata
    first_purchase_date: datetime       # First purchase date
    last_purchase_date: datetime        # Last purchase date
    last_sale_date: Optional[datetime]  # Last sale date (if any)
```

### 3. Asset Entity

```python
class Asset:
    """Financial asset with market data and metadata"""
    
    # Primary identifiers
    asset_id: str                       # Unique asset identifier
    symbol: str                         # Trading symbol (AAPL, MSFT, etc.)
    name: str                           # Asset name
    asset_type: AssetType               # STOCK, BOND, ETF, COMMODITY, etc.
    
    # Asset classification
    sector: str                         # Sector classification
    industry: str                       # Industry classification
    country: str                        # Country of domicile
    currency: str                       # Trading currency
    
    # Market data
    current_price: float                # Current market price
    market_cap: float                   # Market capitalization
    volume: float                       # Trading volume
    bid_price: float                    # Current bid price
    ask_price: float                    # Current ask price
    spread: float                       # Bid-ask spread
    
    # Risk metrics
    beta: float                         # Market beta
    volatility: float                   # Historical volatility
    correlation_matrix: Dict[str, float]  # Correlations with other assets
    
    # Fundamental data
    pe_ratio: Optional[float]           # Price-to-earnings ratio
    dividend_yield: float               # Dividend yield
    eps: Optional[float]                # Earnings per share
    
    # Metadata
    last_updated: datetime              # Last data update
    data_source: str                    # Data provider
    is_active: bool                     # Asset is actively traded
```

### 4. OptimizationResult Entity

```python
class OptimizationResult:
    """Result of portfolio optimization"""
    
    # Primary identifiers
    optimization_id: str                # Unique optimization identifier
    portfolio_id: str                   # Parent portfolio ID
    
    # Optimization parameters
    optimization_method: OptimizationMethod  # MPT, BLACK_LITTERMAN, RISK_PARITY
    risk_free_rate: float               # Risk-free rate used
    optimization_date: datetime         # When optimization was run
    
    # Optimization results
    expected_return: float              # Expected portfolio return
    expected_volatility: float          # Expected portfolio volatility
    sharpe_ratio: float                 # Expected Sharpe ratio
    
    # Optimal weights
    asset_weights: Dict[str, float]     # Asset ID -> optimal weight
    sector_weights: Dict[str, float]    # Sector -> total weight
    asset_class_weights: Dict[str, float]  # Asset class -> total weight
    
    # Risk metrics
    portfolio_var: float                # Value at Risk (95%)
    portfolio_cvar: float               # Conditional VaR (95%)
    max_drawdown: float                 # Expected maximum drawdown
    beta: float                         # Portfolio beta
    
    # Optimization metadata
    convergence_status: bool            # Optimization converged
    optimization_time: float            # Time taken (seconds)
    iteration_count: int                # Number of iterations
    constraint_violations: List[str]    # Any constraint violations
    
    # Relationships
    efficient_frontier: List[EfficientFrontierPoint]  # Efficient frontier points
    risk_contributions: Dict[str, float]  # Risk contribution by asset
```

### 5. MarketView Entity (Black-Litterman)

```python
class MarketView:
    """User-defined market view for Black-Litterman model"""
    
    # Primary identifiers
    view_id: str                        # Unique view identifier
    portfolio_id: str                   # Parent portfolio ID
    
    # View details
    view_type: ViewType                 # ABSOLUTE, RELATIVE
    view_description: str               # Human-readable view description
    
    # Absolute views (e.g., "AAPL will return 5%")
    target_asset_id: Optional[str]      # Asset for absolute view
    expected_return: Optional[float]    # Expected return
    
    # Relative views (e.g., "AAPL will outperform MSFT by 2%")
    outperforming_asset_id: Optional[str]  # Outperforming asset
    underperforming_asset_id: Optional[str]  # Underperforming asset
    relative_return: Optional[float]    # Expected relative return
    
    # Confidence and metadata
    confidence_level: float             # Confidence (0.0 to 1.0)
    view_date: datetime                 # When view was created
    expiry_date: Optional[datetime]     # When view expires
    is_active: bool                     # View is currently active
    
    # Relationships
    optimization_results: List[OptimizationResult]  # Optimizations using this view
```

### 6. RebalancingRecommendation Entity

```python
class RebalancingRecommendation:
    """Recommendation for portfolio rebalancing"""
    
    # Primary identifiers
    recommendation_id: str              # Unique recommendation identifier
    portfolio_id: str                   # Parent portfolio ID
    optimization_id: str                # Source optimization result
    
    # Recommendation details
    recommendation_date: datetime       # When recommendation was generated
    target_rebalancing_date: datetime   # When to execute rebalancing
    priority: RebalancingPriority       # HIGH, MEDIUM, LOW
    
    # Trade recommendations
    trades: List[TradeRecommendation]   # Individual trade recommendations
    
    # Summary metrics
    total_trades: int                   # Number of recommended trades
    estimated_transaction_cost: float   # Estimated total transaction costs
    estimated_market_impact: float      # Estimated market impact
    tracking_error_reduction: float     # Expected tracking error reduction
    
    # Risk metrics
    expected_risk_reduction: float      # Expected risk reduction
    expected_return_improvement: float  # Expected return improvement
    rebalancing_urgency: float          # Urgency score (0.0 to 1.0)
    
    # Metadata
    is_executed: bool                   # Recommendation has been executed
    execution_date: Optional[datetime]  # When it was executed
    execution_cost: Optional[float]     # Actual execution cost
```

### 7. TradeRecommendation Entity

```python
class TradeRecommendation:
    """Individual trade recommendation within rebalancing"""
    
    # Primary identifiers
    trade_id: str                       # Unique trade identifier
    recommendation_id: str              # Parent recommendation ID
    asset_id: str                       # Asset to trade
    
    # Trade details
    action: TradeAction                 # BUY, SELL, HOLD
    current_quantity: float             # Current position quantity
    target_quantity: float              # Target position quantity
    trade_quantity: float               # Quantity to trade (positive for buy, negative for sell)
    
    # Trade metrics
    current_weight: float               # Current weight in portfolio
    target_weight: float                # Target weight in portfolio
    weight_change: float                # Change in weight
    
    # Price and cost information
    current_price: float                # Current market price
    estimated_execution_price: float    # Estimated execution price
    estimated_cost: float               # Estimated trade cost
    estimated_market_impact: float      # Estimated market impact
    
    # Tax considerations
    is_tax_loss_harvest: bool           # Is this a tax-loss harvesting trade
    tax_lot_id: Optional[str]           # Specific tax lot to sell
    estimated_tax_savings: Optional[float]  # Estimated tax savings
    
    # Metadata
    priority: int                       # Trade priority (1 = highest)
    is_executed: bool                   # Trade has been executed
    execution_date: Optional[datetime]  # When trade was executed
    actual_execution_price: Optional[float]  # Actual execution price
```

### 8. RiskMetrics Entity

```python
class RiskMetrics:
    """Portfolio risk calculations and metrics"""
    
    # Primary identifiers
    risk_metrics_id: str                # Unique risk metrics identifier
    portfolio_id: str                   # Parent portfolio ID
    
    # Calculation metadata
    calculation_date: datetime          # When metrics were calculated
    lookback_period: int                # Days of historical data used
    
    # Value at Risk metrics
    var_95: float                       # 95% Value at Risk
    var_99: float                       # 99% Value at Risk
    cvar_95: float                      # 95% Conditional VaR
    cvar_99: float                      # 99% Conditional VaR
    
    # Risk decomposition
    systematic_risk: float              # Systematic (market) risk
    idiosyncratic_risk: float           # Idiosyncratic (specific) risk
    risk_contributions: Dict[str, float]  # Risk contribution by asset
    
    # Factor exposures
    market_beta: float                  # Market beta
    size_factor_exposure: float         # Size factor exposure
    value_factor_exposure: float        # Value factor exposure
    momentum_factor_exposure: float     # Momentum factor exposure
    quality_factor_exposure: float      # Quality factor exposure
    
    # Correlation metrics
    average_correlation: float          # Average pairwise correlation
    max_correlation: float              # Maximum pairwise correlation
    min_correlation: float              # Minimum pairwise correlation
    
    # Stress test results
    stress_test_results: Dict[str, float]  # Stress scenario -> portfolio return
    
    # Risk-adjusted metrics
    information_ratio: float            # Information ratio
    tracking_error: float               # Tracking error vs benchmark
    max_drawdown: float                 # Maximum drawdown
    calmar_ratio: float                 # Calmar ratio
    sortino_ratio: float                # Sortino ratio
```

## Database Schema

### Portfolio Tables

```sql
-- Core portfolio table
CREATE TABLE portfolios (
    portfolio_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id VARCHAR(50) NOT NULL,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    base_currency VARCHAR(3) DEFAULT 'USD',
    rebalancing_frequency VARCHAR(20) DEFAULT 'MONTHLY',
    risk_tolerance VARCHAR(20) DEFAULT 'MODERATE',
    max_single_asset_weight DECIMAL(5,4) DEFAULT 0.10,
    max_sector_weight DECIMAL(5,4) DEFAULT 0.30,
    min_liquidity_requirement BIGINT DEFAULT 1000000000,
    long_only BOOLEAN DEFAULT TRUE,
    total_value DECIMAL(15,2) DEFAULT 0.00,
    cash_balance DECIMAL(15,2) DEFAULT 0.00,
    total_invested DECIMAL(15,2) DEFAULT 0.00,
    unrealized_pnl DECIMAL(15,2) DEFAULT 0.00,
    realized_pnl DECIMAL(15,2) DEFAULT 0.00,
    total_return DECIMAL(10,6) DEFAULT 0.00,
    annualized_return DECIMAL(10,6) DEFAULT 0.00,
    volatility DECIMAL(10,6) DEFAULT 0.00,
    sharpe_ratio DECIMAL(10,6) DEFAULT 0.00,
    max_drawdown DECIMAL(10,6) DEFAULT 0.00,
    calmar_ratio DECIMAL(10,6) DEFAULT 0.00
);

-- Portfolio positions
CREATE TABLE portfolio_positions (
    position_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) REFERENCES portfolios(portfolio_id),
    asset_id VARCHAR(50) NOT NULL,
    quantity DECIMAL(15,6) NOT NULL,
    average_cost DECIMAL(10,4) NOT NULL,
    current_price DECIMAL(10,4) NOT NULL,
    market_value DECIMAL(15,2) NOT NULL,
    cost_basis DECIMAL(15,2) NOT NULL,
    unrealized_pnl DECIMAL(15,2) DEFAULT 0.00,
    unrealized_pnl_pct DECIMAL(10,6) DEFAULT 0.00,
    weight DECIMAL(8,6) DEFAULT 0.00,
    holding_period INTEGER DEFAULT 0,
    is_long_term BOOLEAN DEFAULT FALSE,
    tax_lot_id VARCHAR(50),
    first_purchase_date TIMESTAMP,
    last_purchase_date TIMESTAMP,
    last_sale_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optimization results
CREATE TABLE optimization_results (
    optimization_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) REFERENCES portfolios(portfolio_id),
    optimization_method VARCHAR(50) NOT NULL,
    risk_free_rate DECIMAL(8,6) DEFAULT 0.02,
    optimization_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_return DECIMAL(10,6) NOT NULL,
    expected_volatility DECIMAL(10,6) NOT NULL,
    sharpe_ratio DECIMAL(10,6) NOT NULL,
    portfolio_var DECIMAL(10,6),
    portfolio_cvar DECIMAL(10,6),
    max_drawdown DECIMAL(10,6),
    beta DECIMAL(10,6),
    convergence_status BOOLEAN DEFAULT FALSE,
    optimization_time DECIMAL(10,3),
    iteration_count INTEGER,
    constraint_violations TEXT[]
);

-- Asset weights from optimization
CREATE TABLE optimization_weights (
    weight_id VARCHAR(50) PRIMARY KEY,
    optimization_id VARCHAR(50) REFERENCES optimization_results(optimization_id),
    asset_id VARCHAR(50) NOT NULL,
    optimal_weight DECIMAL(8,6) NOT NULL,
    risk_contribution DECIMAL(8,6),
    expected_return DECIMAL(10,6),
    expected_volatility DECIMAL(10,6)
);

-- Market views for Black-Litterman
CREATE TABLE market_views (
    view_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) REFERENCES portfolios(portfolio_id),
    view_type VARCHAR(20) NOT NULL,
    view_description TEXT,
    target_asset_id VARCHAR(50),
    expected_return DECIMAL(10,6),
    outperforming_asset_id VARCHAR(50),
    underperforming_asset_id VARCHAR(50),
    relative_return DECIMAL(10,6),
    confidence_level DECIMAL(5,4) NOT NULL,
    view_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Rebalancing recommendations
CREATE TABLE rebalancing_recommendations (
    recommendation_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) REFERENCES portfolios(portfolio_id),
    optimization_id VARCHAR(50) REFERENCES optimization_results(optimization_id),
    recommendation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_rebalancing_date TIMESTAMP NOT NULL,
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    total_trades INTEGER DEFAULT 0,
    estimated_transaction_cost DECIMAL(15,2) DEFAULT 0.00,
    estimated_market_impact DECIMAL(15,2) DEFAULT 0.00,
    tracking_error_reduction DECIMAL(10,6) DEFAULT 0.00,
    expected_risk_reduction DECIMAL(10,6) DEFAULT 0.00,
    expected_return_improvement DECIMAL(10,6) DEFAULT 0.00,
    rebalancing_urgency DECIMAL(5,4) DEFAULT 0.00,
    is_executed BOOLEAN DEFAULT FALSE,
    execution_date TIMESTAMP,
    execution_cost DECIMAL(15,2)
);

-- Trade recommendations
CREATE TABLE trade_recommendations (
    trade_id VARCHAR(50) PRIMARY KEY,
    recommendation_id VARCHAR(50) REFERENCES rebalancing_recommendations(recommendation_id),
    asset_id VARCHAR(50) NOT NULL,
    action VARCHAR(10) NOT NULL,
    current_quantity DECIMAL(15,6) NOT NULL,
    target_quantity DECIMAL(15,6) NOT NULL,
    trade_quantity DECIMAL(15,6) NOT NULL,
    current_weight DECIMAL(8,6) NOT NULL,
    target_weight DECIMAL(8,6) NOT NULL,
    weight_change DECIMAL(8,6) NOT NULL,
    current_price DECIMAL(10,4) NOT NULL,
    estimated_execution_price DECIMAL(10,4),
    estimated_cost DECIMAL(15,2) DEFAULT 0.00,
    estimated_market_impact DECIMAL(15,2) DEFAULT 0.00,
    is_tax_loss_harvest BOOLEAN DEFAULT FALSE,
    tax_lot_id VARCHAR(50),
    estimated_tax_savings DECIMAL(15,2),
    priority INTEGER DEFAULT 1,
    is_executed BOOLEAN DEFAULT FALSE,
    execution_date TIMESTAMP,
    actual_execution_price DECIMAL(10,4)
);

-- Risk metrics
CREATE TABLE risk_metrics (
    risk_metrics_id VARCHAR(50) PRIMARY KEY,
    portfolio_id VARCHAR(50) REFERENCES portfolios(portfolio_id),
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lookback_period INTEGER DEFAULT 252,
    var_95 DECIMAL(10,6),
    var_99 DECIMAL(10,6),
    cvar_95 DECIMAL(10,6),
    cvar_99 DECIMAL(10,6),
    systematic_risk DECIMAL(10,6),
    idiosyncratic_risk DECIMAL(10,6),
    market_beta DECIMAL(10,6),
    size_factor_exposure DECIMAL(10,6),
    value_factor_exposure DECIMAL(10,6),
    momentum_factor_exposure DECIMAL(10,6),
    quality_factor_exposure DECIMAL(10,6),
    average_correlation DECIMAL(8,6),
    max_correlation DECIMAL(8,6),
    min_correlation DECIMAL(8,6),
    information_ratio DECIMAL(10,6),
    tracking_error DECIMAL(10,6),
    max_drawdown DECIMAL(10,6),
    calmar_ratio DECIMAL(10,6),
    sortino_ratio DECIMAL(10,6)
);

-- Risk contributions by asset
CREATE TABLE risk_contributions (
    contribution_id VARCHAR(50) PRIMARY KEY,
    risk_metrics_id VARCHAR(50) REFERENCES risk_metrics(risk_metrics_id),
    asset_id VARCHAR(50) NOT NULL,
    risk_contribution DECIMAL(8,6) NOT NULL,
    marginal_risk DECIMAL(8,6),
    component_risk DECIMAL(8,6)
);
```

## Data Relationships

### Primary Relationships
1. **Portfolio → Positions**: One-to-many (portfolio has many positions)
2. **Portfolio → OptimizationResults**: One-to-many (portfolio has many optimization results)
3. **Portfolio → MarketViews**: One-to-many (portfolio has many market views)
4. **Portfolio → RebalancingRecommendations**: One-to-many (portfolio has many recommendations)
5. **Portfolio → RiskMetrics**: One-to-many (portfolio has many risk calculations)

### Secondary Relationships
1. **OptimizationResult → OptimizationWeights**: One-to-many (optimization has many asset weights)
2. **RebalancingRecommendation → TradeRecommendations**: One-to-many (recommendation has many trades)
3. **RiskMetrics → RiskContributions**: One-to-many (risk metrics has many asset contributions)

## Data Validation Rules

### Portfolio Validation
- Portfolio total_value must equal sum of position market_values plus cash_balance
- Portfolio weights must sum to 1.0 (excluding cash)
- Portfolio status must be one of: ACTIVE, INACTIVE, ARCHIVED
- Rebalancing frequency must be one of: DAILY, WEEKLY, MONTHLY

### Position Validation
- Position quantity must be positive for long positions
- Position market_value must equal quantity × current_price
- Position weight must be between 0 and max_single_asset_weight
- Position unrealized_pnl must equal market_value - cost_basis

### Optimization Validation
- Optimization weights must sum to 1.0
- Optimization expected_return must be within reasonable bounds (-100% to 1000%)
- Optimization expected_volatility must be positive
- Optimization Sharpe ratio must be finite

### Risk Metrics Validation
- VaR values must be negative (representing losses)
- CVaR must be more negative than corresponding VaR
- Beta must be finite and reasonable (-5 to 5)
- Correlation values must be between -1 and 1

---

*Data model completed for Advanced Portfolio Management System*

