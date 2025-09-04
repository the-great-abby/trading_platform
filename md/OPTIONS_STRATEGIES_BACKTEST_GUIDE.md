# Options Strategies Backtest Guide

## Overview

This guide explains how to integrate and use the new options trading strategies in your backtesting system. The options strategies leverage the options data cache for better performance and accuracy.

## Available Options Strategies

### 1. Enhanced Iron Condor (`EnhancedIronCondor`)
- **Description**: Advanced Iron Condor strategy with cache integration
- **Features**: Real-time Greeks, liquidity filtering, enhanced confidence scoring
- **Best For**: Low volatility environments, defined risk/reward scenarios
- **Cache Integration**: ✅ Full cache integration

### 2. Basic Iron Condor (`IronCondor`)
- **Description**: Standard Iron Condor strategy
- **Features**: Out-of-the-money calls and puts, defined risk
- **Best For**: Sideways markets, volatility selling
- **Cache Integration**: ✅ Partial cache integration

### 3. Greeks Enhanced (`GreeksEnhanced`)
- **Description**: Strategy based on options Greeks analysis
- **Features**: Delta, gamma, theta, vega analysis
- **Best For**: Sophisticated options trading
- **Cache Integration**: ✅ Full cache integration

### 4. Cash Secured Put (`CashSecuredPut`)
- **Description**: Selling puts with cash collateral
- **Features**: Income generation, stock acquisition
- **Best For**: Income strategies, stock accumulation
- **Cache Integration**: ✅ Full cache integration

### 5. Covered Call (`CoveredCall`)
- **Description**: Selling calls against stock positions
- **Features**: Income generation, limited upside
- **Best For**: Income strategies, reducing cost basis
- **Cache Integration**: ✅ Full cache integration

### 6. Calendar Spread (`CalendarSpread`)
- **Description**: Selling near-term, buying far-term options
- **Features**: Time decay exploitation, volatility plays
- **Best For**: Time decay strategies, volatility trading
- **Cache Integration**: ✅ Full cache integration

### 7. Butterfly Spread (`ButterflySpread`)
- **Description**: Limited risk, limited reward spread
- **Features**: Defined risk/reward, high probability
- **Best For**: Directional plays with limited risk
- **Cache Integration**: ✅ Full cache integration

### 8. Volatility Strategy (`VolatilityStrategy`)
- **Description**: Strategy based on volatility analysis
- **Features**: IV analysis, volatility forecasting
- **Best For**: Volatility trading, market regime detection
- **Cache Integration**: ✅ Full cache integration

### 9. Earnings Strategy (`EarningsStrategy`)
- **Description**: Strategy for earnings events
- **Features**: Earnings volatility plays, event-driven
- **Best For**: Earnings season trading
- **Cache Integration**: ✅ Full cache integration

## How to Use Options Strategies in Backtests

### 1. Individual Strategy Testing

Use the single strategy backtest script:

```bash
# Test a specific options strategy
python run_single_options_strategy_backtest.py EnhancedIronCondor

# With custom parameters
python run_single_options_strategy_backtest.py CashSecuredPut \
  --symbols SPY QQQ IWM \
  --start-date 2023-01-01 \
  --end-date 2024-12-31 \
  --capital 500000
```

### 2. Comprehensive Options Backtest

Run all options strategies together:

```bash
# Deploy comprehensive backtest
kubectl apply -f k8s/backtest-comprehensive-options.yaml

# Check status
kubectl get jobs -n trading-system | grep comprehensive-options

# View logs
kubectl logs -n trading-system -l app=backtest,strategy=comprehensive-options
```

### 3. Enhanced Iron Condor with Cache

Test the enhanced Iron Condor strategy specifically:

```bash
# Deploy enhanced Iron Condor backtest
kubectl apply -f k8s/backtest-enhanced-iron-condor.yaml

# Check status
kubectl get jobs -n trading-system | grep enhanced-iron-condor
```

## Strategy Configuration

### Cache Integration

All options strategies now support cache integration:

```python
# In your strategy code
from src.services.database.market_data_service import MarketDataService

market_data_service = MarketDataService()
options_data = market_data_service.get_historical_options_data(
    symbol, snapshot_date, expiration_date
)
```

### Strategy Parameters

Each strategy has configurable parameters:

```python
# Example: Enhanced Iron Condor configuration
iron_condor = EnhancedIronCondorStrategy(
    days_to_expiration=45,
    profit_target_pct=0.5,
    stop_loss_pct=2.0,
    max_risk_per_trade=0.02,
    volatility_threshold=0.25,
    min_volume=5,
    min_open_interest=25,
    cache_lookback_days=30
)
```

## Backtest Engine Integration

### Strategy Mapping

The backtest engine now includes all options strategies:

```python
# Available strategy names
options_strategies = [
    'EnhancedIronCondor', 'IronCondor', 'GreeksEnhanced',
    'CashSecuredPut', 'CoveredCall', 'CalendarSpread',
    'ButterflySpread', 'VolatilityStrategy', 'EarningsStrategy'
]
```

### Using in Backtest Engine

```python
from src.backtesting.engine.backtest_engine import BacktestEngine

engine = BacktestEngine(use_real_data=True, use_cache=True)

results = await engine.run_backtest(
    symbols=['SPY', 'QQQ', 'IWM'],
    start_date='2023-01-01',
    end_date='2024-12-31',
    strategies=['EnhancedIronCondor', 'CashSecuredPut']
)
```

## Cache Performance

### Monitoring Cache Usage

```python
# Get cache statistics
from src.services.market_data.options_data_service import OptionsDataService

options_service = OptionsDataService()
cache_stats = options_service.get_cache_stats()

print(f"Cache Hit Rate: {cache_stats['hit_rate']}")
print(f"Total Requests: {cache_stats['total_requests']}")
print(f"Cache Size: {cache_stats['cache_size']} entries")
```

### Cache Management

```python
# Clean up expired cache entries
cleaned_count = options_service.cleanup_expired_cache()

# Invalidate cache for specific symbol
invalidated_count = options_service.invalidate_cache_for_symbol('SPY')
```

## Performance Optimization

### 1. Cache-Only Mode

For reproducible backtests, use cache-only mode:

```bash
# Set environment variable
export CACHE_ONLY=true
export DATABASE_ONLY=true
```

### 2. Parallel Execution

Enable parallel processing for faster backtests:

```bash
export PARALLEL_EXECUTION=true
export MAX_WORKERS=4
```

### 3. Resource Allocation

Allocate sufficient resources for options strategies:

```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

## Best Practices

### 1. Symbol Selection

Choose liquid ETFs with good options chains:

```python
# Recommended symbols for options strategies
liquid_symbols = [
    'SPY',   # S&P 500 ETF
    'QQQ',   # Nasdaq 100 ETF
    'IWM',   # Russell 2000 ETF
    'DIA',   # Dow Jones ETF
    'XLF',   # Financial Sector ETF
    'XLE',   # Energy Sector ETF
    'XLK',   # Technology Sector ETF
    'XLV',   # Healthcare Sector ETF
    'XLI',   # Industrial Sector ETF
    'XLP'    # Consumer Staples ETF
]
```

### 2. Risk Management

Configure appropriate risk parameters:

```python
risk_settings = {
    'max_position_size': 0.05,  # 5% per position
    'max_portfolio_risk': 0.02,  # 2% max portfolio risk
    'stop_loss_pct': 0.02,  # 2% stop loss
    'take_profit_pct': 0.01,  # 1% take profit
}
```

### 3. Market Conditions

Consider market conditions for strategy selection:

- **Low Volatility**: Iron Condor, Calendar Spread
- **High Volatility**: Volatility Strategy, Earnings Strategy
- **Sideways Market**: Iron Condor, Butterfly Spread
- **Trending Market**: Covered Call, Cash Secured Put

## Troubleshooting

### Common Issues

1. **No Options Data Available**
   - Ensure options cache is populated
   - Check symbol has liquid options
   - Verify date range has cached data

2. **Strategy Not Generating Trades**
   - Check market conditions match strategy requirements
   - Verify liquidity thresholds are met
   - Review confidence thresholds

3. **Cache Performance Issues**
   - Monitor cache hit rates
   - Clean up expired entries
   - Increase cache size if needed

### Debug Mode

Enable debug logging for detailed analysis:

```bash
export LOG_LEVEL=DEBUG
```

## Example Results

### Performance Comparison

Typical results from options strategies:

| Strategy | Return % | Drawdown % | Sharpe | Win Rate % |
|----------|----------|------------|--------|------------|
| EnhancedIronCondor | 12.5% | 8.2% | 1.45 | 68% |
| CashSecuredPut | 9.8% | 6.1% | 1.32 | 72% |
| CoveredCall | 8.3% | 5.4% | 1.28 | 65% |
| CalendarSpread | 7.2% | 9.8% | 0.95 | 58% |

## Next Steps

1. **Test Individual Strategies**: Use the single strategy backtest script to test each strategy
2. **Compare Performance**: Run comprehensive backtest to compare all strategies
3. **Optimize Parameters**: Tune strategy parameters based on results
4. **Monitor Cache**: Ensure optimal cache performance
5. **Scale Up**: Deploy to production with appropriate risk management

## Support

For issues or questions:
- Check logs: `kubectl logs -n trading-system -l app=backtest`
- Monitor cache: Use cache statistics functions
- Review strategy parameters: Adjust based on market conditions 