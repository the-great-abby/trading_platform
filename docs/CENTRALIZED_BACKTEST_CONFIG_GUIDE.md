# Centralized Backtest Configuration Guide

This guide explains how to use the new centralized backtesting configuration system that consolidates all parameters in one place for easy management.

## Overview

The centralized configuration system provides:
- **Single source of truth** for all backtest parameters
- **Preset configurations** for common scenarios
- **Risk profile management** with predefined settings
- **Environment variable support** for easy deployment
- **Configuration validation** to prevent errors
- **Easy export** to different formats

## Quick Start

### Basic Usage

```python
from src.utils.backtest_config import get_backtest_config, BacktestMode, RiskProfile

# Get a standard configuration
config = get_backtest_config(
    mode=BacktestMode.STANDARD,
    risk_profile=RiskProfile.MODERATE,
    initial_capital=10000.0,
    backtest_name="my_backtest"
)

# Use the configuration
print(f"Capital: ${config.initial_capital:,.0f}")
print(f"Position Size: {config.position_size:.1%}")
print(f"Stop Loss: {config.stop_loss_pct:.1%}")
```

### Preset Configurations

```python
from src.utils.backtest_config import get_preset_config

# Quick test (30 days, conservative)
config = get_preset_config('quick_test')

# Comprehensive test (2 years, LLM enabled)
config = get_preset_config('comprehensive_test')

# Aggressive test (6 months, high risk)
config = get_preset_config('aggressive_test')

# Conservative test (1 year, low risk)
config = get_preset_config('conservative_test')
```

## Configuration Modes

### BacktestMode Enum

| Mode | Description | Default Settings |
|------|-------------|------------------|
| `FAST` | Quick execution | 90 days, 20 symbols, no LLM |
| `STANDARD` | Balanced approach | 365 days, 50 symbols, moderate settings |
| `COMPREHENSIVE` | Full analysis | 730 days, 100 symbols, LLM enabled |
| `AGGRESSIVE` | High activity | 180 days, 30 symbols, aggressive settings |
| `CONSERVATIVE` | Low risk | 365 days, 20 symbols, conservative settings |

### RiskProfile Enum

| Profile | Position Size | Stop Loss | Take Profit | Daily Trades | Confidence |
|---------|---------------|-----------|-------------|--------------|------------|
| `ULTRA_CONSERVATIVE` | 2% | 3% | 8% | 3 | 80% |
| `CONSERVATIVE` | 3% | 5% | 10% | 5 | 70% |
| `MODERATE` | 5% | 8% | 15% | 10 | 60% |
| `AGGRESSIVE` | 8% | 12% | 20% | 15 | 50% |
| `ULTRA_AGGRESSIVE` | 12% | 15% | 25% | 20 | 40% |

## Configuration Parameters

### Basic Configuration

```python
config = BacktestConfig(
    # Identification
    backtest_name="my_strategy",
    backtest_mode=BacktestMode.STANDARD,
    risk_profile=RiskProfile.MODERATE,
    
    # Date range
    start_date="2024-01-01",
    end_date="2024-12-31",
    test_period_days=365,
    
    # Symbols and strategies
    symbols=["AAPL", "MSFT", "GOOGL"],
    strategies=["MACD", "BollingerBands", "RSI"],
    max_symbols=50
)
```

### Capital and Position Sizing

```python
config = BacktestConfig(
    # Initial capital
    initial_capital=100000.0,
    
    # Position sizing
    position_size=0.05,        # 5% of portfolio per trade
    max_position_size=0.15,    # Max 15% per position
    min_trade_value=50.0,      # Minimum $50 per trade
    max_trade_value=15000.0,   # Maximum trade value
    
    # Position limits
    max_positions=5,
    max_daily_trades=10,
    min_trade_interval=1       # Minimum days between trades
)
```

### Risk Management

```python
config = BacktestConfig(
    # Stop loss and take profit
    stop_loss_pct=0.08,        # 8% stop loss
    take_profit_pct=0.15,      # 15% take profit
    trailing_stop_pct=0.05,    # 5% trailing stop
    
    # Risk limits
    max_daily_loss=100.0,      # Max daily loss in dollars
    max_drawdown_pct=0.25,     # 25% max drawdown
    max_portfolio_risk=0.10    # 10% max portfolio risk per trade
)
```

### Trading Costs

```python
config = BacktestConfig(
    # Commission and fees
    commission_per_trade=1.0,   # $1 per trade
    commission_rate=0.001,      # 0.1% commission rate
    slippage_percentage=0.0005, # 0.05% slippage
    
    # Fill settings
    partial_fill_probability=0.15,  # 15% chance of partial fill
    market_hours_only=True
)
```

### Performance Settings

```python
config = BacktestConfig(
    # Parallel processing
    use_parallel=True,
    max_workers=8,
    parallel_strategies=True,
    parallel_symbols=True,
    
    # Caching and data
    use_cache=True,
    use_real_data=True,
    database_only=False,
    
    # Memory and timeout
    memory_limit="2Gi",
    timeout_hours=24,
    batch_size=10
)
```

### Strategy Settings

```python
config = BacktestConfig(
    # Confidence and thresholds
    confidence_threshold=0.6,
    min_volume_ratio=1.2,
    min_price_change=0.005,
    
    # Trend and momentum
    trend_confirmation=True,
    trend_confirmation_weight=0.7,
    require_positive_momentum=True,
    
    # Market regime
    market_regime_filter=True,
    volatility_filter=True,
    volatility_threshold=0.02,
    trend_strength_threshold=0.6,
    correlation_threshold=0.3,
    market_regime_lookback=20
)
```

### LLM Settings

```python
config = BacktestConfig(
    # LLM evaluation
    use_llm=False,
    llm_timeout=10.0,
    llm_retry_attempts=2,
    fallback_confidence=0.6
)
```

## Environment Variables

You can configure backtests using environment variables:

```bash
# Basic settings
export BACKTEST_MODE=fast
export RISK_PROFILE=moderate
export INITIAL_CAPITAL=10000
export MAX_SYMBOLS=20

# Risk management
export STOP_LOSS_PCT=0.08
export TAKE_PROFIT_PCT=0.15
export MAX_DAILY_TRADES=10

# Performance
export USE_CACHE=true
export USE_LLM=false
export MAX_WORKERS=8
```

Then load the configuration:

```python
from src.utils.backtest_config import load_config_from_env

config = load_config_from_env()
```

## Preset Configurations

### Quick Test
```python
config = get_preset_config('quick_test')
# 30 days, conservative settings, fast execution
```

### Comprehensive Test
```python
config = get_preset_config('comprehensive_test')
# 2 years, LLM enabled, full analysis
```

### Aggressive Test
```python
config = get_preset_config('aggressive_test')
# 6 months, high risk, maximum activity
```

### Conservative Test
```python
config = get_preset_config('conservative_test')
# 1 year, low risk, careful approach
```

## Using Configuration with Backtest Engine

```python
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.utils.backtest_config import get_preset_config

# Get configuration
config = get_preset_config('quick_test', backtest_name="my_backtest")

# Create strategies based on config
strategies = {}
if 'MACD' in config.strategies:
    strategies['MACD Strategy'] = MACDStrategy()
if 'BollingerBands' in config.strategies:
    strategies['Bollinger Bands Strategy'] = BollingerBandsStrategy()

# Create backtest engine
engine = BacktestEngine(
    use_cache=config.use_cache,
    use_real_data=config.use_real_data
)

# Run backtest
results = engine.run_backtest(
    strategies=strategies,
    symbols=config.symbols,
    start_date=config.start_date,
    end_date=config.end_date
)

# Store results with backtest name
engine.store_results(
    results=results,
    symbols=config.symbols,
    start_date=config.start_date,
    end_date=config.end_date,
    backtest_name=config.backtest_name
)
```

## Configuration Validation

The system automatically validates configurations:

```python
config = BacktestConfig(
    initial_capital=-1000,  # Invalid: negative capital
    position_size=1.5,      # Invalid: > 100%
    start_date="2024-12-31",
    end_date="2024-01-01"   # Invalid: end before start
)

errors = config.validate()
for error in errors:
    print(f"Error: {error}")
```

## Exporting Configuration

### To Dictionary
```python
config_dict = config.to_dict()
print(f"Configuration has {len(config_dict)} parameters")
```

### To Environment Variables
```python
env_vars = config.to_env_vars()
for key, value in env_vars.items():
    print(f"{key}={value}")
```

## Kubernetes Integration

### Environment Variables in Kubernetes Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: backtest-with-config
spec:
  template:
    spec:
      containers:
      - name: backtest
        image: localhost:5000/trading-bot:latest
        command: ["python", "my_backtest_script.py"]
        env:
        - name: BACKTEST_MODE
          value: "fast"
        - name: RISK_PROFILE
          value: "moderate"
        - name: INITIAL_CAPITAL
          value: "10000"
        - name: MAX_SYMBOLS
          value: "20"
        - name: STOP_LOSS_PCT
          value: "0.08"
        - name: TAKE_PROFIT_PCT
          value: "0.15"
```

### Loading in Script

```python
from src.utils.backtest_config import load_config_from_env

# Load configuration from environment variables
config = load_config_from_env()

# Use the configuration
print(f"Running {config.backtest_mode.value} backtest")
print(f"Risk profile: {config.risk_profile.value}")
print(f"Capital: ${config.initial_capital:,.0f}")
```

## Best Practices

### 1. Use Presets for Common Scenarios

```python
# Instead of manually setting all parameters
config = get_preset_config('quick_test')

# Instead of
config = BacktestConfig(
    test_period_days=30,
    max_symbols=10,
    risk_profile=RiskProfile.CONSERVATIVE,
    # ... many more parameters
)
```

### 2. Override Only What You Need

```python
# Start with a preset and override specific values
config = get_preset_config('comprehensive_test',
    initial_capital=50000,  # Override capital
    max_symbols=30,         # Override symbol count
    backtest_name="my_custom_test"  # Add custom name
)
```

### 3. Use Environment Variables for Deployment

```bash
# Set configuration via environment
export BACKTEST_MODE=fast
export RISK_PROFILE=conservative
export INITIAL_CAPITAL=5000

# Run backtest
python my_backtest_script.py
```

### 4. Validate Configurations

```python
# Always validate before using
config = get_backtest_config(mode=BacktestMode.STANDARD)
errors = config.validate()
if errors:
    raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
```

### 5. Export for Documentation

```python
# Export configuration for documentation
config_dict = config.to_dict()
with open('backtest_config.json', 'w') as f:
    json.dump(config_dict, f, indent=2)
```

## Migration from Old Configuration

### Before (Scattered Parameters)

```python
# Old way - parameters scattered across files
initial_capital = 100000
position_size = 0.05
stop_loss_pct = 0.08
take_profit_pct = 0.15
max_daily_trades = 10
confidence_threshold = 0.6
# ... many more parameters in different places
```

### After (Centralized Configuration)

```python
# New way - all parameters in one place
from src.utils.backtest_config import get_backtest_config

config = get_backtest_config(
    mode=BacktestMode.STANDARD,
    risk_profile=RiskProfile.MODERATE,
    initial_capital=100000,
    backtest_name="my_strategy"
)

# All parameters accessible from config object
print(f"Capital: ${config.initial_capital:,.0f}")
print(f"Position Size: {config.position_size:.1%}")
print(f"Stop Loss: {config.stop_loss_pct:.1%}")
```

## Troubleshooting

### Common Issues

1. **Invalid Configuration**
   ```python
   # Check validation errors
   errors = config.validate()
   for error in errors:
       print(f"Error: {error}")
   ```

2. **Environment Variables Not Loading**
   ```python
   # Check if environment variables are set
   import os
   print(f"BACKTEST_MODE: {os.getenv('BACKTEST_MODE')}")
   print(f"RISK_PROFILE: {os.getenv('RISK_PROFILE')}")
   ```

3. **Preset Not Found**
   ```python
   # Available presets
   from src.utils.backtest_config import get_preset_config
   try:
       config = get_preset_config('unknown_preset')
   except ValueError as e:
       print(f"Error: {e}")
   ```

### Debug Configuration

```python
# Print full configuration
config = get_backtest_config()
config_dict = config.to_dict()
for key, value in config_dict.items():
    print(f"{key}: {value}")
```

## Future Enhancements

### Planned Features

1. **Configuration Templates**
   - Save and load custom configurations
   - Share configurations between team members

2. **Dynamic Configuration**
   - Runtime configuration updates
   - A/B testing different configurations

3. **Configuration Validation Rules**
   - Custom validation rules
   - Industry-standard compliance checks

4. **Configuration Analytics**
   - Track which configurations perform best
   - Automated configuration optimization

## Conclusion

The centralized backtest configuration system provides:
- **Simplified management** of all backtest parameters
- **Consistent defaults** across different scenarios
- **Easy deployment** via environment variables
- **Validation** to prevent configuration errors
- **Flexibility** to override any parameter

By using this system, you can focus on strategy development rather than parameter management, while ensuring consistency and reducing errors across your backtesting workflow. 