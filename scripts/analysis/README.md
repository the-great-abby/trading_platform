# Analysis Scripts

This directory contains scripts for analyzing backtest results, trading performance, and strategy optimization.

## Analysis Categories

### Backtest Analysis
Scripts for analyzing backtest results:
- `analyze_detailed_backtest_results.py` - Detailed backtest analysis
- `analyze_optimization_results.py` - Strategy optimization analysis
- `analyze_top_performers_results.py` - Identify best performing strategies

### Strategy Analysis
Scripts for comparing and analyzing strategies:
- `compare_strategies.py` - Compare multiple strategy performances
- `analyze_complementary_strategies.py` - Find complementary strategy combinations
- `analyze_hybrid_ichimoku_performance.py` - Analyze hybrid strategy performance

### Allocation Analysis
Scripts for analyzing capital allocation:
- `analyze_optimized_allocation.py` - Analyze allocation optimization
- `analyze_ichimoku_heavy_allocation.py` - Analyze Ichimoku-heavy allocations
- `analyze_maximum_return_combo.py` - Find maximum return combinations

### Performance Analysis
- `verify_trading_frequency.py` - Verify trading frequency is realistic
- `positive_return_optimization.py` - Optimize for positive returns

### Technical Analysis
- `analyze_elliott_wave_fix.py` - Analyze Elliott Wave improvements

## Usage

```bash
# Run an analysis script
python scripts/analysis/analyze_detailed_backtest_results.py

# Analyze specific backtest results
python scripts/analysis/compare_strategies.py results/backtest1.json results/backtest2.json
```

## Output

Most analysis scripts:
- Print results to stdout
- Generate visualizations (if matplotlib is available)
- Save detailed reports to `docs/` or `results/`

## Dependencies

Analysis scripts may require additional packages:
```bash
pip install pandas numpy matplotlib seaborn
```

