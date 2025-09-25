# Backtesting Guide - Trading System

## Overview

This guide covers the backtesting engine for the trading system, including options strategies, mock data generation, and error handling mechanisms.

## Quick Start

### Running a Simple Backtest

```python
from src.backtesting.engine.backtest_engine import BacktestEngine

# Initialize engine with mock data for testing
engine = BacktestEngine(use_real_data=False, use_cache=False)

# Run backtest
results = await engine.run_backtest(
    symbols=["AAPL", "MSFT"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategies=["IronCondor", "RSI", "MACD"]
)

# Access results
for strategy_name, result in results.items():
    print(f"{strategy_name}: {result.total_return:.2%} return")
```

### Using the API Endpoint

```bash
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategies": ["IronCondor", "RSI", "MACD"]
  }'
```

## Backtest Engine Configuration

### Environment Variables

- `DATABASE_ONLY`: Set to "true" to use only database data (no external APIs)
- `USE_MOCK_DATA`: Set to "true" to use mock data for testing
- `ENABLE_OPTIONS_STRATEGIES`: Set to "true" to enable options strategies

### Engine Initialization Options

```python
# Real data with caching
engine = BacktestEngine(use_real_data=True, use_cache=True)

# Mock data for testing
engine = BacktestEngine(use_real_data=False, use_cache=False)

# Real data without caching
engine = BacktestEngine(use_real_data=True, use_cache=False)
```

## Options Strategies

### Supported Options Strategies

- **Iron Condor**: Range-bound strategy with defined risk/reward
- **Butterfly Spread**: Limited risk/reward with specific price targets
- **Calendar Spread**: Time decay strategy with multiple expirations

### Options Data Requirements

Options strategies require options chain data including:
- Strike prices
- Expiration dates
- Option types (call/put)
- Greeks (delta, gamma, theta, vega)
- Volume and liquidity data

### Mock Options Data

When real options data is unavailable, the system uses mock data:

```python
from src.services.mock_options_data_service import MockOptionsDataService

# Initialize mock service
mock_service = MockOptionsDataService()

# Get mock options
options = mock_service.get_liquid_options("AAPL", min_volume=10)
print(f"Generated {len(options)} mock options")
```

## Error Handling and Fallbacks

### Strategy Fallback Mechanism

Options strategies automatically fall back to stock-based strategies when options data is unavailable:

```python
# Strategy checks if options data is available
can_execute = strategy.can_execute_with_options_data()

if not can_execute:
    # Automatically falls back to RSI strategy
    fallback_strategy = strategy.fallback_to_stock_strategy()
```

### Graceful Degradation Levels

1. **Level 1**: Try real options service
2. **Level 2**: Fall back to mock options service
3. **Level 3**: Use minimal service (strategies handle fallback)

### Error Recovery

```python
from src.utils.error_handler import ErrorHandler

error_handler = ErrorHandler()

try:
    result = await engine.run_backtest(...)
except Exception as e:
    error_context = error_handler.handle_error(e, {"context": "backtest"})
    # System provides recovery suggestions
```

## Backtest Results

### BacktestResult Object

```python
@dataclass
class BacktestResult:
    strategy: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    max_drawdown_pct: float  # Primary attribute
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    trades: List[BacktestTrade]
    equity_curve: pd.DataFrame
    start_date: datetime
    end_date: datetime
    
    @property
    def max_drawdown(self) -> float:
        """Backward compatibility alias for max_drawdown_pct"""
        return self.max_drawdown_pct
```

### Accessing Results

```python
# Primary attribute (recommended)
max_dd = result.max_drawdown_pct

# Backward compatibility (still supported)
max_dd = result.max_drawdown  # Same value as max_drawdown_pct
```

## Performance Optimization

### Batch Backtesting

For multiple symbols and strategies:

```python
# Efficient batch processing
results = await engine.run_backtest(
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategies=["IronCondor", "ButterflySpread", "CalendarSpread"]
)
```

### Performance Targets

- **Single Strategy**: < 10 seconds for 2-year backtest
- **Batch Processing**: < 30 seconds for 5 symbols × 3 strategies
- **Memory Usage**: < 1GB for typical backtests

## Testing

### Running Tests

```bash
# Run all backtest tests
pytest tests/backtesting/

# Run specific test categories
pytest tests/unit/test_backtest_result.py
pytest tests/integration/test_mock_options_data.py
pytest tests/contract/test_backtest_result.py
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Contract Tests**: API contract validation
- **Backtest Validation**: End-to-end backtest testing

## Troubleshooting

### Common Issues

1. **"No options data available"**
   - Check if options service is initialized
   - Verify mock data generation is working
   - Review error logs for service failures

2. **"Strategy execution failed"**
   - Check strategy fallback mechanism
   - Verify market data availability
   - Review strategy-specific error logs

3. **"BacktestResult attribute error"**
   - Use `max_drawdown_pct` instead of `max_drawdown`
   - Check backward compatibility property
   - Verify result object structure

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run backtest with detailed logs
results = await engine.run_backtest(...)
```

### Health Checks

```python
# Check engine health
engine_status = engine.get_health_status()

# Check options service
options_available = engine.options_service.can_execute_with_options_data()

# Check service status
service_status = engine.options_service.get_service_status()
```

## Best Practices

### Strategy Development

1. **Always implement fallback mechanisms**
2. **Use structured error handling**
3. **Test with mock data first**
4. **Validate results with multiple data sources**

### Performance Optimization

1. **Use batch processing for multiple tests**
2. **Enable caching for repeated tests**
3. **Monitor memory usage during backtests**
4. **Use appropriate data granularity**

### Error Handling

1. **Implement graceful degradation**
2. **Provide meaningful error messages**
3. **Log errors with sufficient context**
4. **Test error scenarios**

## API Reference

### BacktestEngine

#### Methods

- `run_backtest(symbols, start_date, end_date, strategies)`: Run comprehensive backtest
- `_initialize_options_service()`: Initialize options data service
- `_get_strategy_class(strategy_name)`: Get strategy class by name

#### Properties

- `options_service`: Options data service instance
- `market_data_manager`: Market data manager instance
- `use_real_data`: Whether to use real market data
- `use_cache`: Whether to use cached data

### MockOptionsDataService

#### Methods

- `get_liquid_options(symbol, min_volume)`: Get liquid options for symbol
- `get_liquid_options_with_historical_support(symbol, min_volume, historical_date)`: Get historical options
- `generate_mock_options_chain(symbol, current_price)`: Generate complete options chain
- `can_execute_with_options_data()`: Check if service can provide data

### ErrorHandler

#### Methods

- `handle_error(error, context)`: Handle errors with recovery suggestions
- `log_backtest_progress(stage, details)`: Log backtest progress
- `log_strategy_execution(strategy, symbol, action, details)`: Log strategy execution

## Changelog

### Version 1.1.0 (Current)

- Added mock options data generation
- Implemented strategy fallback mechanisms
- Enhanced error handling and logging
- Added backward compatibility for BacktestResult attributes
- Improved containerized environment support

### Version 1.0.0

- Initial backtest engine implementation
- Basic options strategy support
- Real market data integration
- Performance optimization features

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review error logs with debug mode
3. Test with mock data to isolate issues
4. Verify environment configuration

---

*Last updated: 2025-09-20*


