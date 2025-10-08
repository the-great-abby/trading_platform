# Simulations

This directory contains Monte Carlo-style simulation scripts that use statistical modeling to test trading strategies.

## What are Simulations?

Simulations use probability distributions and random sampling rather than real market data:
- **Win rates** (e.g., 65% success rate)
- **Average win/loss amounts** (e.g., +1.5% win, -1.2% loss)
- **Position sizing rules**
- **Risk management limits**
- **Market regime effects** (bull/bear/volatile/range-bound)

## Simulations vs Backtests

| Feature | Simulations | Backtests |
|---------|------------|-----------|
| Data Source | Statistical distributions | Real historical market data |
| Speed | Fast (seconds) | Slower (API calls) |
| Purpose | Quick concept validation | Real-world validation |
| Accuracy | Based on assumptions | Based on actual market behavior |

## Types of Simulations

### Strategy Testing
- `realistic_trading_simulation.py` - Tests optimized strategies with realistic risk management
- `truly_realistic_simulation.py` - More conservative version with proper constraints
- `strategy_comparison_simulation.py` - Compares traditional vs optimized strategies

### Options Strategies
- `iron_condor_stock_simulation.py` - Tests Iron Condor on specific stocks (INTC, AMD, PYPL)
- `realistic_iron_condor_options_simulation.py` - Iron Condor with realistic parameters
- `iron_condor_mature_stocks_simulation.py` - Iron Condor on mature/stable stocks

## Typical Workflow

1. **Simulation** → Test if strategy concept is mathematically viable
2. **Backtest** (in `backtests/`) → Validate with real historical market data
3. **Paper Trading** → Test in real-time without real money
4. **Live Trading** → Deploy with actual capital

## Running Simulations

```bash
# Run a simulation
python simulations/realistic_trading_simulation.py

# Simulations run quickly and output performance metrics:
# - Total return
# - Annualized return
# - Max drawdown
# - Sharpe ratio
# - Win rate
```

## When to Use

**Use simulations for:**
- ✅ Quick "what if" scenario testing
- ✅ Testing different position sizes, stop losses
- ✅ Strategy viability sanity checks
- ✅ Parameter optimization ideas

**Use backtests for:**
- ✅ Validation with real market data
- ✅ Final strategy confirmation
- ✅ Production deployment decisions

