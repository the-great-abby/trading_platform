# Backtest Name Tracking Guide

This guide explains how to use the new backtest name tracking feature to identify and combine winning strategies.

## Overview

The backtest name tracking feature allows you to:
- Track which backtest file was used for each backtest run
- Identify winning strategies across different backtest files
- Combine successful strategies into more effective trading approaches
- Analyze patterns in strategy performance

## Database Schema

### New Field Added

The `backtest_runs` table now includes a `backtest_name` field:

```sql
ALTER TABLE backtest_runs ADD COLUMN backtest_name VARCHAR(200);
CREATE INDEX idx_backtest_name ON backtest_runs(backtest_name);
```

### Model Updates

The `BacktestRun` model has been updated to include:

```python
backtest_name = Column(String(200), nullable=True)  # Name of the backtest file/strategy used
```

## Usage

### Automatic Backtest Name Detection

The system automatically detects the backtest name from the calling script:

```python
from src.utils.backtest_utils import get_backtest_name_from_script

# Get the current backtest name
backtest_name = get_backtest_name_from_script()
print(f"Running backtest: {backtest_name}")
```

### Manual Backtest Name Specification

You can also manually specify the backtest name:

```python
from src.backtesting.engine.backtest_engine import BacktestEngine

engine = BacktestEngine()
results = await engine.run_backtest(
    strategies=strategies,
    symbols=symbols,
    start_date=start_date,
    end_date=end_date,
    backtest_name="my_custom_strategy"
)
```

### Utility Functions

Several utility functions are available for working with backtest names:

```python
from src.utils.backtest_utils import (
    get_backtest_name,
    get_backtest_name_from_path,
    format_backtest_name,
    get_backtest_summary
)

# Extract name from calling script
name = get_backtest_name_from_script()

# Extract name from file path
name = get_backtest_name_from_path("/path/to/demo_strategy.py")

# Format name for display
formatted = format_backtest_name("demo_strategy")  # Returns "Demo Strategy"

# Generate summary
summary = get_backtest_summary("demo_strategy", "MACD", ["AAPL"], "2024-01-01", "2024-12-31")
```

## Analyzing Winning Strategies

### Running the Analysis

Use the winning strategies analysis script:

```bash
# Via Kubernetes
kubectl apply -f k8s/analyze-winning-strategies.yaml

# Or locally
python scripts/analyze_winning_strategies.py
```

### Analysis Criteria

The analysis looks for strategies that meet these criteria:
- Minimum return: 10.0%
- Minimum win rate: 60%
- Minimum profit factor: 1.5

You can adjust these criteria in the script.

### Analysis Output

The analysis provides:

1. **Summary Statistics**
   - Total winning strategies found
   - Unique backtests and strategies
   - Top performers

2. **Backtest Performance**
   - Performance metrics by backtest file
   - Strategies that work well together

3. **Strategy Performance**
   - Performance metrics by strategy type
   - Which backtests each strategy works in

4. **Combination Suggestions**
   - Suggested strategy combinations
   - Expected performance metrics
   - Rationale for combinations

## Example Analysis Report

```
================================================================================
WINNING STRATEGIES ANALYSIS REPORT
================================================================================

📊 SUMMARY:
  Total Winning Strategies: 15
  Unique Backtests: 8
  Unique Strategies: 12

🏆 TOP PERFORMERS:
  1. MACD Strategy (Demo Strategy)
     Return: 25.3% | Win Rate: 68% | Profit Factor: 2.1
  2. Bollinger Bands (Advanced Strategy)
     Return: 22.1% | Win Rate: 65% | Profit Factor: 1.9

📈 BACKTEST PERFORMANCE:
  Demo Strategy:
    Winning Strategies: 3
    Avg Return: 18.2%
    Avg Win Rate: 64%
    Strategies: MACD Strategy, RSI Strategy, Moving Average

🎯 STRATEGY PERFORMANCE:
  MACD Strategy:
    Runs: 4
    Avg Return: 20.1%
    Avg Win Rate: 67%
    Backtests: Demo Strategy, Advanced Strategy

💡 STRATEGY COMBINATION SUGGESTIONS:
  1. MACD_Strategy_plus_Bollinger_Bands
     Expected Return: 23.7%
     Expected Win Rate: 66.5%
     Rationale: Combining MACD Strategy (avg 20.1% return) with Bollinger Bands (avg 22.1% return)
     Strategies: MACD Strategy, Bollinger Bands
```

## Combining Strategies

### Manual Combination

Create a new backtest that combines multiple strategies:

```python
from src.strategies.momentum.macd_strategy import MACDStrategy
from src.strategies.mean_reversion.bollinger_bands_strategy import BollingerBandsStrategy

# Create combined strategy
class CombinedStrategy:
    def __init__(self):
        self.macd = MACDStrategy()
        self.bollinger = BollingerBandsStrategy()
    
    def generate_signals(self, data):
        # Combine signals from both strategies
        macd_signals = self.macd.generate_signals(data)
        bollinger_signals = self.bollinger.generate_signals(data)
        
        # Logic to combine signals
        combined_signals = self._combine_signals(macd_signals, bollinger_signals)
        return combined_signals
```

### Automated Combination

Use the analysis results to create automated combinations:

```python
from scripts.analyze_winning_strategies import get_winning_strategies

# Get winning strategies
winning_strategies = get_winning_strategies()

# Find strategies that work well together
for strategy in winning_strategies:
    if strategy['backtest_name'] == 'demo_strategy':
        # This strategy works well in the demo backtest
        print(f"Strategy {strategy['strategy_name']} is effective")
```

## Migration

### Running the Migration

```bash
# Via Kubernetes
kubectl apply -f k8s/alembic-migration-job.yaml

# Or locally
alembic upgrade head
```

### Verifying the Migration

Check that the new field was added:

```sql
-- Connect to database
psql -h localhost -U trading_user -d trading_bot

-- Check the table structure
\d backtest_runs

-- Should show the new backtest_name column
```

## Best Practices

### 1. Consistent Naming

Use consistent naming for your backtest files:
- `demo_strategy.py`
- `advanced_strategy.py`
- `momentum_strategy.py`

### 2. Descriptive Names

Make backtest names descriptive:
- `demo_macd_strategy.py` instead of `demo1.py`
- `advanced_bollinger_strategy.py` instead of `test2.py`

### 3. Version Control

Include version information in backtest names:
- `demo_strategy_v1.py`
- `demo_strategy_v2.py`

### 4. Regular Analysis

Run the winning strategies analysis regularly:
```bash
# Schedule weekly analysis
kubectl create cronjob analyze-strategies --image=localhost:5000/trading-bot:latest \
  --schedule="0 9 * * 1" \
  -- python scripts/analyze_winning_strategies.py
```

## Troubleshooting

### No Backtest Name Detected

If the system can't detect the backtest name:

1. Check that you're running the script directly:
   ```bash
   python demo_strategy.py  # ✅ Works
   python -c "import demo_strategy"  # ❌ Won't work
   ```

2. Manually specify the backtest name:
   ```python
   backtest_name = "my_strategy"
   ```

### Migration Issues

If the migration fails:

1. Check the database connection:
   ```bash
   kubectl logs -f job/alembic-migration
   ```

2. Run the migration manually:
   ```bash
   kubectl exec -it deployment/strategy-service -- alembic upgrade head
   ```

### Analysis Not Finding Results

If the analysis doesn't find winning strategies:

1. Lower the criteria:
   ```python
   winning_strategies = get_winning_strategies(
       min_return_pct=5.0,  # Lower from 10.0
       min_win_rate=0.5,    # Lower from 0.6
       min_profit_factor=1.2  # Lower from 1.5
   )
   ```

2. Check that you have backtest results in the database:
   ```sql
   SELECT COUNT(*) FROM backtest_runs;
   ```

## Future Enhancements

### Planned Features

1. **Strategy Combination Engine**
   - Automated strategy combination
   - Performance prediction
   - Risk assessment

2. **Backtest Versioning**
   - Track changes in backtest files
   - Compare performance across versions

3. **Strategy Ranking**
   - Machine learning-based strategy ranking
   - Performance prediction models

4. **Automated Optimization**
   - Parameter optimization across strategies
   - Portfolio optimization

### Contributing

To contribute to the backtest name tracking feature:

1. Update the database schema if needed
2. Add new utility functions to `src/utils/backtest_utils.py`
3. Update the analysis script in `scripts/analyze_winning_strategies.py`
4. Add tests in `tests/unit/test_backtest_utils.py`

## Conclusion

The backtest name tracking feature provides a powerful way to:
- Track which strategies work best
- Identify patterns in successful strategies
- Combine strategies for better performance
- Optimize your trading approach

By using this feature effectively, you can build more robust and profitable trading strategies. 