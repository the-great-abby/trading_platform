# Backtests

This directory contains backtest scripts that use real historical market data from Polygon API to validate trading strategies.

## What are Backtests?

Backtests test trading strategies against actual historical market data to see how they would have performed in the past. Unlike simulations (which use statistical distributions), backtests use:
- Real stock prices
- Real market conditions
- Actual trading volumes
- Historical news events
- Real market regimes

## Running Backtests

Most backtests can be run directly:

```bash
# Run a specific backtest
python backtests/clean_backtest.py

# Or use Makefile targets
make -f Makefile.backtesting run-backtest
```

## Backtest Categories

### Strategy-Specific Backtests
Backtests focused on specific trading strategies:
- Elliott Wave strategies
- Sector rotation
- Ichimoku strategies
- Volatility trading
- Options strategies (Iron Condor, Butterfly Spread, etc.)

### Allocation Backtests
Tests for capital allocation across multiple strategies:
- `aggressive_allocation_backtest.py`
- `hybrid_capital_allocation_backtest.py`
- `strategy_allocation_backtest.py`

### Comprehensive Backtests
Full system tests with multiple strategies:
- `clean_backtest.py`
- `comprehensive_two_year_backtest.py`
- `simple_comprehensive_backtest.py`

### Platform-Specific Backtests
Backtests for specific trading platforms:
- `public_com_two_year_backtest.py` - Public.com specific tests
- `optimized_public_com_backtest.py`

## Configuration

Backtest parameters are centralized in `src/utils/trading_config.py`:
- Symbol lists
- Account size ($1,000 default)
- Time periods
- Risk management rules

## Results

Backtest results are saved to the `results/` directory as JSON files with timestamps.

## Kubernetes Backtests

For larger backtests, use Kubernetes:

```bash
# See KUBERNETES_VS_LOCAL_BACKTESTS.md in docs/
kubectl apply -f k8s/jobs/backtest-job.yaml
```

## See Also

- `docs/BACKTESTING_GUIDE.md` - Comprehensive backtesting documentation
- `simulations/` - Monte Carlo simulations for quick testing
- `results/` - Backtest output files

