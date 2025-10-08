# Results

This directory contains output files from backtests and simulations.

## File Naming Convention

Results files follow this pattern:
```
{test_name}_{timestamp}.json
```

Example:
```
comprehensive_two_year_backtest_20250929_065505.json
improved_capital_allocation_backtest_20250929_170456.json
```

## File Contents

Result files typically include:
- **Performance metrics**: returns, Sharpe ratio, max drawdown
- **Trade details**: entry/exit points, P&L per trade
- **Strategy breakdown**: performance by individual strategy
- **Risk metrics**: drawdowns, volatility, exposure
- **Timestamps**: when the test was run

## Viewing Results

```bash
# Pretty print a result file
cat results/your_backtest_20250929_065505.json | jq .

# Search for specific metrics
cat results/*.json | jq '.annualized_return'

# Find best performing backtest
cat results/*.json | jq -r '.final_capital' | sort -n | tail -1
```

## Cleanup

Results can accumulate over time. To clean up old results:

```bash
# Remove results older than 30 days
find results/ -name "*.json" -mtime +30 -delete

# Keep only the 10 most recent results
ls -t results/*.json | tail -n +11 | xargs rm
```

## Analysis

For detailed analysis of results, see:
- `scripts/analysis/` - Analysis scripts
- `notebooks/` - Jupyter notebooks for visualization

