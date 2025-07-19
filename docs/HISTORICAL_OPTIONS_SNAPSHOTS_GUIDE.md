# Historical Options Snapshots Guide

## Overview

The Historical Options Snapshots feature enables you to store and retrieve historical options data with Greeks for more effective backtesting. This system captures daily snapshots of options chains and stores them in a dedicated database table, allowing you to access real historical options data during backtesting instead of relying on mock data.

## Key Features

### 🗄️ Historical Data Storage
- **Daily Snapshots**: Automatically captures options data daily
- **Greeks Preservation**: Stores delta, gamma, theta, vega, and implied volatility
- **Underlying Prices**: Records stock prices when snapshots were taken
- **Data Source Tracking**: Tracks the source of options data (e.g., Polygon)

### 📊 Enhanced Backtesting
- **Real Historical Data**: Use actual historical options data instead of mock data
- **Greeks Analysis**: Analyze how Greeks changed over time
- **Date Range Queries**: Retrieve options data for specific date ranges
- **Expiration Filtering**: Filter by specific option expiration dates

### 🔧 Management Tools
- **Automatic Cleanup**: Configurable retention periods (default: 2 years)
- **Batch Operations**: Process multiple symbols efficiently
- **Cache Statistics**: Monitor cache performance and hit rates

## Database Schema

### Historical Options Snapshots Table

```sql
CREATE TABLE historical_options_snapshots (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR,
    snapshot_date DATE,
    expiration VARCHAR,
    strike FLOAT,
    option_type VARCHAR,
    price FLOAT,
    volume INTEGER,
    open_interest INTEGER,
    delta FLOAT,
    gamma FLOAT,
    theta FLOAT,
    vega FLOAT,
    implied_volatility FLOAT,
    underlying_price FLOAT,
    data_source VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Indexes for Performance

```sql
-- Composite indexes for efficient queries
CREATE INDEX idx_historical_options_symbol_date ON historical_options_snapshots (symbol, snapshot_date);
CREATE INDEX idx_historical_options_symbol_expiration ON historical_options_snapshots (symbol, expiration);
CREATE INDEX idx_historical_options_date_range ON historical_options_snapshots (snapshot_date);
CREATE INDEX idx_historical_options_symbol_date_expiration ON historical_options_snapshots (symbol, snapshot_date, expiration);
```

## Usage Examples

### 1. Basic Historical Data Retrieval

```python
from src.services.market_data.enhanced_options_data_service import get_enhanced_options_service
from datetime import date

# Get enhanced options service
enhanced_service = get_enhanced_options_service()

# Get historical options data for a specific date
historical_data = enhanced_service.get_historical_options_data(
    symbol="AAPL",
    snapshot_date=date(2024, 1, 15)
)

if historical_data:
    print(f"Found {len(historical_data.contracts)} contracts for AAPL on 2024-01-15")
    print(f"Underlying price: ${historical_data.underlying_price}")
```

### 2. Historical Greeks for Backtesting

```python
from src.strategies.options.greeks_enhanced_strategy import GreeksEnhancedStrategy

# Create strategy instance
strategy = GreeksEnhancedStrategy()

# Get historical Greeks data
greeks_data = strategy.get_greeks_data(
    symbol="AAPL",
    current_price=150.0,
    historical_date="2024-01-15"
)

if greeks_data:
    print(f"Delta: {greeks_data.delta:.3f}")
    print(f"Gamma: {greeks_data.gamma:.3f}")
    print(f"Theta: {greeks_data.theta:.3f}")
    print(f"Vega: {greeks_data.vega:.3f}")
```

### 3. Date Range Queries

```python
from datetime import date

# Get historical options data for a date range
historical_data_list = enhanced_service.get_historical_options_date_range(
    symbol="AAPL",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31)
)

print(f"Found {len(historical_data_list)} historical snapshots")
```

### 4. Available Dates Query

```python
# Get list of available historical dates
available_dates = enhanced_service.get_available_historical_dates("AAPL")
print(f"Available dates for AAPL: {len(available_dates)} snapshots")
```

## Configuration

### Service Configuration

```python
# Enhanced Options Data Service configuration
enhanced_service = EnhancedOptionsDataService()

# Configuration options
enhanced_service.auto_snapshot_enabled = True  # Enable automatic snapshots
enhanced_service.snapshot_retention_days = 730  # Keep 2 years of data
enhanced_service.snapshot_cleanup_interval = timedelta(days=30)  # Cleanup every 30 days
```

### Database Configuration

The service uses the same database connection as other market data services. Ensure your `DATABASE_URL` environment variable is set:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/trading_bot"
```

## Migration

To set up the historical options snapshots table, run the Alembic migration:

```bash
# Run the migration
alembic upgrade head

# Verify the table was created
psql -d trading_bot -c "\d historical_options_snapshots"
```

## Performance Considerations

### Storage Requirements

- **Daily Snapshots**: ~100-500 contracts per symbol per day
- **Storage per Contract**: ~200 bytes per contract
- **Estimated Daily Storage**: 20-100 KB per symbol per day
- **Annual Storage**: 7-37 MB per symbol per year

### Query Optimization

- Use date range filters to limit query scope
- Leverage composite indexes for symbol + date queries
- Consider partitioning for large datasets

### Cleanup Strategy

```python
# Manual cleanup
deleted_count = enhanced_service.cleanup_old_historical_data(days_to_keep=730)

# Automatic cleanup (runs every 30 days by default)
enhanced_service.cleanup_old_historical_data()
```

## Integration with Backtesting

### Enhanced Greeks Strategy

The `GreeksEnhancedStrategy` has been updated to use historical options data:

```python
# The strategy now automatically tries historical data first
greeks_data = strategy.get_greeks_data(
    symbol="AAPL",
    current_price=150.0,
    historical_date="2024-01-15"  # This triggers historical lookup
)
```

### Backtesting Workflow

1. **Setup Historical Data**: Store daily snapshots for your symbols
2. **Run Backtests**: Use historical Greeks data for accurate backtesting
3. **Analyze Results**: Compare performance with real vs mock data
4. **Cleanup**: Periodically remove old data to manage storage

## Monitoring and Maintenance

### Cache Statistics

```python
# Get cache performance statistics
stats = enhanced_service.get_cache_stats()
print(f"Cache hits: {stats['hits']}")
print(f"Cache misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

### Data Quality Checks

```python
# Check data availability
available_dates = enhanced_service.get_available_historical_dates("AAPL")
print(f"Data coverage: {len(available_dates)} days")

# Check data completeness
for date in available_dates[:5]:  # Check first 5 dates
    data = enhanced_service.get_historical_options_data("AAPL", date)
    if data:
        print(f"{date}: {len(data.contracts)} contracts")
```

## Troubleshooting

### Common Issues

1. **No Historical Data Available**
   - Ensure snapshots are being stored daily
   - Check if the migration was run successfully
   - Verify database connectivity

2. **Poor Performance**
   - Check if indexes are created properly
   - Consider partitioning for large datasets
   - Monitor query execution plans

3. **Storage Issues**
   - Adjust retention period if needed
   - Run cleanup more frequently
   - Monitor database size

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger('src.services.market_data.enhanced_options_data_service').setLevel(logging.DEBUG)

# Check specific date
data = enhanced_service.get_historical_options_data("AAPL", date(2024, 1, 15))
if not data:
    print("No data found - check if snapshots were stored")
```

## Best Practices

### Data Collection

1. **Daily Snapshots**: Store options data daily during market hours
2. **Quality Checks**: Validate data before storing
3. **Backup Strategy**: Regular backups of historical data
4. **Monitoring**: Track storage usage and performance

### Backtesting

1. **Use Historical Data**: Prefer real historical data over mock data
2. **Date Validation**: Ensure requested dates have data available
3. **Fallback Strategy**: Have mock data as fallback
4. **Performance Tracking**: Monitor backtest performance with real data

### Maintenance

1. **Regular Cleanup**: Automate cleanup of old data
2. **Index Maintenance**: Monitor and optimize indexes
3. **Storage Monitoring**: Track database growth
4. **Performance Monitoring**: Monitor query performance

## Future Enhancements

### Planned Features

1. **Real-time Snapshots**: Capture options data in real-time
2. **Advanced Analytics**: Greeks analysis and visualization
3. **Data Compression**: Optimize storage requirements
4. **Distributed Storage**: Scale to handle more symbols
5. **API Integration**: REST API for historical data access

### Contributing

To contribute to the historical options snapshots feature:

1. Follow the existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Consider performance implications
5. Test with real data

## Conclusion

The Historical Options Snapshots feature provides a robust foundation for accurate options backtesting by preserving real historical options data with Greeks. This enables more realistic backtesting scenarios and better strategy validation.

For questions or issues, please refer to the troubleshooting section or create an issue in the project repository. 