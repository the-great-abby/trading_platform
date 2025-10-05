# Data Model: Comprehensive Risk Management Framework

## Core Entities

### RiskMetrics
Portfolio-level risk measurements and calculations

**Fields**:
- `risk_metrics_id`: UUID, Primary Key
- `portfolio_id`: UUID, Foreign Key to Portfolio
- `calculation_timestamp`: DateTime, When risk metrics were calculated
- `var_95`: Float, Value at Risk at 95% confidence level
- `var_99`: Float, Value at Risk at 99% confidence level
- `expected_shortfall_95`: Float, Conditional VaR at 95% confidence
- `expected_shortfall_99`: Float, Conditional VaR at 99% confidence
- `portfolio_volatility`: Float, Annualized portfolio volatility
- `portfolio_beta`: Float, Portfolio beta to market
- `maximum_drawdown`: Float, Maximum drawdown percentage
- `sharpe_ratio`: Float, Risk-adjusted return metric
- `sortino_ratio`: Float, Downside risk-adjusted return
- `calmar_ratio`: Float, Return to max drawdown ratio
- `concentration_risk`: Float, Portfolio concentration risk score
- `correlation_risk`: Float, Portfolio correlation risk score
- `leverage_ratio`: Float, Portfolio leverage ratio
- `cash_ratio`: Float, Cash as percentage of portfolio
- `calculation_method`: String, VaR calculation method used
- `data_period_days`: Integer, Historical data period used
- `confidence_intervals`: JSON, VaR confidence intervals
- `created_at`: DateTime, Record creation timestamp
- `updated_at`: DateTime, Last update timestamp

**Validation Rules**:
- `var_95` and `var_99` must be non-negative
- `portfolio_volatility` must be between 0 and 10 (1000% max)
- `maximum_drawdown` must be between 0 and 1 (100% max)
- `sharpe_ratio` should be reasonable (-5 to +5 range)
- `calculation_timestamp` must be recent (within last hour)

**Relationships**:
- Belongs to Portfolio (many-to-one)
- Has many RiskContributions (one-to-many)
- Has many StressTestResults (one-to-many)

### StressTestResult
Results from stress testing scenarios

**Fields**:
- `stress_test_id`: UUID, Primary Key
- `portfolio_id`: UUID, Foreign Key to Portfolio
- `scenario_name`: String, Name of stress test scenario
- `scenario_type`: Enum, Type of scenario (market_crash, rate_shock, volatility_spike, sector_rotation, options_decay)
- `test_timestamp`: DateTime, When stress test was performed
- `initial_portfolio_value`: Float, Portfolio value before stress
- `stressed_portfolio_value`: Float, Portfolio value after stress
- `portfolio_value_change`: Float, Absolute change in portfolio value
- `portfolio_value_change_pct`: Float, Percentage change in portfolio value
- `var_impact`: Float, Change in VaR due to stress
- `volatility_impact`: Float, Change in volatility due to stress
- `max_drawdown_impact`: Float, Change in max drawdown due to stress
- `position_impacts`: JSON, Individual position impacts
- `sector_impacts`: JSON, Sector-level impacts
- `scenario_parameters`: JSON, Scenario-specific parameters
- `test_duration_ms`: Integer, Time taken for stress test
- `status`: Enum, Test status (pending, completed, failed)
- `error_message`: String, Error details if test failed
- `created_at`: DateTime, Record creation timestamp

**Validation Rules**:
- `portfolio_value_change_pct` must be reasonable (-100% to +100%)
- `scenario_name` must be one of predefined scenarios
- `test_duration_ms` must be positive
- `status` must be valid enum value

**Relationships**:
- Belongs to Portfolio (many-to-one)
- Belongs to RiskMetrics (many-to-one)

### CorrelationAnalysis
Asset correlation matrices and concentration risk analysis

**Fields**:
- `correlation_analysis_id`: UUID, Primary Key
- `portfolio_id`: UUID, Foreign Key to Portfolio
- `analysis_timestamp`: DateTime, When analysis was performed
- `correlation_matrix`: JSON, Asset correlation matrix
- `sector_correlations`: JSON, Sector correlation matrix
- `concentration_risk_score`: Float, Overall concentration risk score
- `sector_concentration`: JSON, Sector concentration breakdown
- `top_correlations`: JSON, Highest correlation pairs
- `diversification_ratio`: Float, Portfolio diversification ratio
- `effective_number_of_assets`: Float, Diversification metric
- `correlation_stability_score`: Float, How stable correlations are
- `rolling_correlation_period`: Integer, Days for rolling correlation
- `correlation_regime`: String, Current correlation regime
- `recommendations`: JSON, Diversification recommendations
- `risk_attribution`: JSON, Risk contribution by asset/sector
- `analysis_method`: String, Correlation analysis method used
- `created_at`: DateTime, Record creation timestamp

**Validation Rules**:
- `concentration_risk_score` must be between 0 and 1
- `diversification_ratio` must be positive
- `effective_number_of_assets` must be between 1 and number of assets
- `correlation_matrix` must be symmetric and valid correlation matrix

**Relationships**:
- Belongs to Portfolio (many-to-one)

### ComplianceReport
Regulatory compliance status and audit trail

**Fields**:
- `compliance_report_id`: UUID, Primary Key
- `portfolio_id`: UUID, Foreign Key to Portfolio
- `report_timestamp`: DateTime, When report was generated
- `report_type`: Enum, Type of report (daily, weekly, monthly, ad_hoc)
- `report_period_start`: Date, Start of reporting period
- `report_period_end`: Date, End of reporting period
- `compliance_status`: Enum, Overall compliance status (compliant, warning, violation)
- `audit_trail`: JSON, Complete audit trail of activities
- `trade_documentation`: JSON, All trades during period
- `position_reporting`: JSON, All positions at period end
- `risk_metrics_summary`: JSON, Risk metrics summary
- `regulatory_checks`: JSON, Regulatory compliance checks performed
- `violations_detected`: JSON, Any compliance violations
- `recommendations`: JSON, Compliance recommendations
- `report_format`: String, Report format (PDF, CSV, JSON)
- `report_file_path`: String, Path to generated report file
- `generated_by`: String, System or user who generated report
- `reviewed_by`: String, User who reviewed report
- `review_timestamp`: DateTime, When report was reviewed
- `created_at`: DateTime, Record creation timestamp

**Validation Rules**:
- `report_period_end` must be after `report_period_start`
- `compliance_status` must be valid enum value
- `report_format` must be supported format

**Relationships**:
- Belongs to Portfolio (many-to-one)

### RiskLimits
Configurable risk thresholds and limits

**Fields**:
- `risk_limits_id`: UUID, Primary Key
- `portfolio_id`: UUID, Foreign Key to Portfolio
- `limit_type`: Enum, Type of limit (position_size, daily_loss, sector_concentration, var_limit, volatility_limit)
- `limit_value`: Float, Limit threshold value
- `limit_unit`: String, Unit of limit (percentage, dollars, ratio)
- `current_value`: Float, Current value of metric
- `breach_threshold`: Float, Threshold for breach alert
- `warning_threshold`: Float, Threshold for warning alert
- `is_active`: Boolean, Whether limit is currently active
- `enforcement_action`: Enum, Action when limit breached (alert, reduce_position, halt_trading)
- `last_breach_timestamp`: DateTime, When limit was last breached
- `breach_count`: Integer, Number of times limit has been breached
- `limit_description`: String, Human-readable description of limit
- `created_by`: String, User who created limit
- `created_at`: DateTime, Limit creation timestamp
- `updated_at`: DateTime, Last update timestamp

**Validation Rules**:
- `limit_value` must be positive
- `current_value` must be non-negative
- `breach_count` must be non-negative
- `is_active` must be boolean

**Relationships**:
- Belongs to Portfolio (many-to-one)
- Has many RiskAlerts (one-to-many)

### RiskAlert
Risk limit breach notifications and alerts

**Fields**:
- `risk_alert_id`: UUID, Primary Key
- `portfolio_id`: UUID, Foreign Key to Portfolio
- `risk_limits_id`: UUID, Foreign Key to RiskLimits
- `alert_timestamp`: DateTime, When alert was triggered
- `alert_type`: Enum, Type of alert (warning, breach, critical)
- `alert_severity`: Enum, Alert severity (low, medium, high, critical)
- `limit_name`: String, Name of limit that was breached
- `limit_value`: Float, Limit threshold value
- `current_value`: Float, Current value that triggered alert
- `breach_percentage`: Float, How much limit was exceeded
- `alert_message`: String, Human-readable alert message
- `recommended_action`: String, Recommended action to take
- `alert_status`: Enum, Alert status (active, acknowledged, resolved)
- `acknowledged_by`: String, User who acknowledged alert
- `acknowledged_at`: DateTime, When alert was acknowledged
- `resolved_at`: DateTime, When alert was resolved
- `escalation_level`: Integer, Current escalation level
- `notification_sent`: Boolean, Whether notification was sent
- `created_at`: DateTime, Alert creation timestamp

**Validation Rules**:
- `alert_severity` must be valid enum value
- `breach_percentage` must be non-negative
- `escalation_level` must be between 0 and 5
- `acknowledged_at` must be after `alert_timestamp` if set

**Relationships**:
- Belongs to Portfolio (many-to-one)
- Belongs to RiskLimits (many-to-one)

### RiskContributions
Individual asset and sector risk contributions

**Fields**:
- `risk_contribution_id`: UUID, Primary Key
- `risk_metrics_id`: UUID, Foreign Key to RiskMetrics
- `asset_id`: String, Asset identifier
- `asset_type`: Enum, Type of asset (stock, option, bond, cash)
- `sector`: String, Asset sector classification
- `position_value`: Float, Current position value
- `position_weight`: Float, Weight in portfolio
- `var_contribution`: Float, Contribution to portfolio VaR
- `var_contribution_pct`: Float, Percentage contribution to VaR
- `volatility_contribution`: Float, Contribution to portfolio volatility
- `beta_contribution`: Float, Contribution to portfolio beta
- `correlation_contribution`: Float, Contribution to correlation risk
- `concentration_risk`: Float, Concentration risk from this asset
- `marginal_var`: Float, Marginal VaR for this asset
- `component_var`: Float, Component VaR for this asset
- `risk_budget`: Float, Allocated risk budget
- `risk_budget_utilization`: Float, How much of risk budget is used
- `created_at`: DateTime, Record creation timestamp

**Validation Rules**:
- `position_weight` must be between 0 and 1
- `var_contribution_pct` must be between 0 and 1
- `risk_budget_utilization` must be non-negative

**Relationships**:
- Belongs to RiskMetrics (many-to-one)

## Database Schema

### Tables
```sql
-- Risk Metrics Table
CREATE TABLE risk_metrics (
    risk_metrics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id),
    calculation_timestamp TIMESTAMPTZ NOT NULL,
    var_95 DECIMAL(10,4) NOT NULL CHECK (var_95 >= 0),
    var_99 DECIMAL(10,4) NOT NULL CHECK (var_99 >= 0),
    expected_shortfall_95 DECIMAL(10,4) NOT NULL CHECK (expected_shortfall_95 >= 0),
    expected_shortfall_99 DECIMAL(10,4) NOT NULL CHECK (expected_shortfall_99 >= 0),
    portfolio_volatility DECIMAL(8,4) NOT NULL CHECK (portfolio_volatility >= 0 AND portfolio_volatility <= 10),
    portfolio_beta DECIMAL(6,4) NOT NULL,
    maximum_drawdown DECIMAL(6,4) NOT NULL CHECK (maximum_drawdown >= 0 AND maximum_drawdown <= 1),
    sharpe_ratio DECIMAL(6,4) NOT NULL,
    sortino_ratio DECIMAL(6,4) NOT NULL,
    calmar_ratio DECIMAL(6,4) NOT NULL,
    concentration_risk DECIMAL(6,4) NOT NULL CHECK (concentration_risk >= 0 AND concentration_risk <= 1),
    correlation_risk DECIMAL(6,4) NOT NULL CHECK (correlation_risk >= 0 AND correlation_risk <= 1),
    leverage_ratio DECIMAL(6,4) NOT NULL CHECK (leverage_ratio >= 0),
    cash_ratio DECIMAL(6,4) NOT NULL CHECK (cash_ratio >= 0 AND cash_ratio <= 1),
    calculation_method VARCHAR(50) NOT NULL,
    data_period_days INTEGER NOT NULL CHECK (data_period_days > 0),
    confidence_intervals JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stress Test Results Table
CREATE TABLE stress_test_results (
    stress_test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id),
    scenario_name VARCHAR(100) NOT NULL,
    scenario_type VARCHAR(50) NOT NULL CHECK (scenario_type IN ('market_crash', 'rate_shock', 'volatility_spike', 'sector_rotation', 'options_decay')),
    test_timestamp TIMESTAMPTZ NOT NULL,
    initial_portfolio_value DECIMAL(15,2) NOT NULL CHECK (initial_portfolio_value > 0),
    stressed_portfolio_value DECIMAL(15,2) NOT NULL CHECK (stressed_portfolio_value >= 0),
    portfolio_value_change DECIMAL(15,2) NOT NULL,
    portfolio_value_change_pct DECIMAL(8,4) NOT NULL CHECK (portfolio_value_change_pct >= -1 AND portfolio_value_change_pct <= 1),
    var_impact DECIMAL(10,4) NOT NULL,
    volatility_impact DECIMAL(8,4) NOT NULL,
    max_drawdown_impact DECIMAL(6,4) NOT NULL,
    position_impacts JSONB NOT NULL,
    sector_impacts JSONB NOT NULL,
    scenario_parameters JSONB NOT NULL,
    test_duration_ms INTEGER NOT NULL CHECK (test_duration_ms > 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Correlation Analysis Table
CREATE TABLE correlation_analyses (
    correlation_analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id),
    analysis_timestamp TIMESTAMPTZ NOT NULL,
    correlation_matrix JSONB NOT NULL,
    sector_correlations JSONB NOT NULL,
    concentration_risk_score DECIMAL(6,4) NOT NULL CHECK (concentration_risk_score >= 0 AND concentration_risk_score <= 1),
    sector_concentration JSONB NOT NULL,
    top_correlations JSONB NOT NULL,
    diversification_ratio DECIMAL(8,4) NOT NULL CHECK (diversification_ratio > 0),
    effective_number_of_assets DECIMAL(6,2) NOT NULL CHECK (effective_number_of_assets >= 1),
    correlation_stability_score DECIMAL(6,4) NOT NULL,
    rolling_correlation_period INTEGER NOT NULL CHECK (rolling_correlation_period > 0),
    correlation_regime VARCHAR(50) NOT NULL,
    recommendations JSONB NOT NULL,
    risk_attribution JSONB NOT NULL,
    analysis_method VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Compliance Reports Table
CREATE TABLE compliance_reports (
    compliance_report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id),
    report_timestamp TIMESTAMPTZ NOT NULL,
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('daily', 'weekly', 'monthly', 'ad_hoc')),
    report_period_start DATE NOT NULL,
    report_period_end DATE NOT NULL,
    compliance_status VARCHAR(20) NOT NULL CHECK (compliance_status IN ('compliant', 'warning', 'violation')),
    audit_trail JSONB NOT NULL,
    trade_documentation JSONB NOT NULL,
    position_reporting JSONB NOT NULL,
    risk_metrics_summary JSONB NOT NULL,
    regulatory_checks JSONB NOT NULL,
    violations_detected JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    report_format VARCHAR(10) NOT NULL CHECK (report_format IN ('PDF', 'CSV', 'JSON')),
    report_file_path VARCHAR(500),
    generated_by VARCHAR(100) NOT NULL,
    reviewed_by VARCHAR(100),
    review_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (report_period_end > report_period_start)
);

-- Risk Limits Table
CREATE TABLE risk_limits (
    risk_limits_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id),
    limit_type VARCHAR(50) NOT NULL CHECK (limit_type IN ('position_size', 'daily_loss', 'sector_concentration', 'var_limit', 'volatility_limit')),
    limit_value DECIMAL(15,4) NOT NULL CHECK (limit_value > 0),
    limit_unit VARCHAR(20) NOT NULL,
    current_value DECIMAL(15,4) NOT NULL CHECK (current_value >= 0),
    breach_threshold DECIMAL(15,4) NOT NULL CHECK (breach_threshold > 0),
    warning_threshold DECIMAL(15,4) NOT NULL CHECK (warning_threshold > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    enforcement_action VARCHAR(20) NOT NULL CHECK (enforcement_action IN ('alert', 'reduce_position', 'halt_trading')),
    last_breach_timestamp TIMESTAMPTZ,
    breach_count INTEGER NOT NULL DEFAULT 0 CHECK (breach_count >= 0),
    limit_description TEXT NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Risk Alerts Table
CREATE TABLE risk_alerts (
    risk_alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id),
    risk_limits_id UUID NOT NULL REFERENCES risk_limits(risk_limits_id),
    alert_timestamp TIMESTAMPTZ NOT NULL,
    alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('warning', 'breach', 'critical')),
    alert_severity VARCHAR(20) NOT NULL CHECK (alert_severity IN ('low', 'medium', 'high', 'critical')),
    limit_name VARCHAR(100) NOT NULL,
    limit_value DECIMAL(15,4) NOT NULL,
    current_value DECIMAL(15,4) NOT NULL,
    breach_percentage DECIMAL(8,4) NOT NULL CHECK (breach_percentage >= 0),
    alert_message TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    alert_status VARCHAR(20) NOT NULL CHECK (alert_status IN ('active', 'acknowledged', 'resolved')),
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    escalation_level INTEGER NOT NULL DEFAULT 0 CHECK (escalation_level >= 0 AND escalation_level <= 5),
    notification_sent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (acknowledged_at IS NULL OR acknowledged_at >= alert_timestamp)
);

-- Risk Contributions Table
CREATE TABLE risk_contributions (
    risk_contribution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_metrics_id UUID NOT NULL REFERENCES risk_metrics(risk_metrics_id),
    asset_id VARCHAR(20) NOT NULL,
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('stock', 'option', 'bond', 'cash')),
    sector VARCHAR(50) NOT NULL,
    position_value DECIMAL(15,2) NOT NULL,
    position_weight DECIMAL(8,6) NOT NULL CHECK (position_weight >= 0 AND position_weight <= 1),
    var_contribution DECIMAL(10,4) NOT NULL,
    var_contribution_pct DECIMAL(8,6) NOT NULL CHECK (var_contribution_pct >= 0 AND var_contribution_pct <= 1),
    volatility_contribution DECIMAL(8,6) NOT NULL,
    beta_contribution DECIMAL(6,4) NOT NULL,
    correlation_contribution DECIMAL(8,6) NOT NULL,
    concentration_risk DECIMAL(8,6) NOT NULL,
    marginal_var DECIMAL(10,4) NOT NULL,
    component_var DECIMAL(10,4) NOT NULL,
    risk_budget DECIMAL(10,4) NOT NULL,
    risk_budget_utilization DECIMAL(8,6) NOT NULL CHECK (risk_budget_utilization >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX idx_risk_metrics_portfolio_timestamp ON risk_metrics(portfolio_id, calculation_timestamp DESC);
CREATE INDEX idx_stress_test_results_portfolio_timestamp ON stress_test_results(portfolio_id, test_timestamp DESC);
CREATE INDEX idx_correlation_analyses_portfolio_timestamp ON correlation_analyses(portfolio_id, analysis_timestamp DESC);
CREATE INDEX idx_compliance_reports_portfolio_timestamp ON compliance_reports(portfolio_id, report_timestamp DESC);
CREATE INDEX idx_risk_limits_portfolio_active ON risk_limits(portfolio_id, is_active);
CREATE INDEX idx_risk_alerts_portfolio_status ON risk_alerts(portfolio_id, alert_status);
CREATE INDEX idx_risk_alerts_timestamp ON risk_alerts(alert_timestamp DESC);
CREATE INDEX idx_risk_contributions_metrics_asset ON risk_contributions(risk_metrics_id, asset_id);
```

## Performance Considerations

### Indexing Strategy
- Primary indexes on portfolio_id + timestamp for time-series queries
- Composite indexes for common query patterns
- Partial indexes for active records only

### Data Retention
- Risk metrics: 2 years of daily data
- Stress test results: 1 year retention
- Correlation analyses: 6 months retention
- Compliance reports: 7 years retention (regulatory requirement)
- Risk alerts: 1 year retention

### Partitioning Strategy
- Time-based partitioning for risk_metrics table
- Monthly partitions for optimal query performance
- Automatic partition management for data retention












