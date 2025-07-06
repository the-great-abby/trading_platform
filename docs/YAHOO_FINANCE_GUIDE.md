# Yahoo Finance Market Data Guide

This guide explains how to get real market data from Yahoo Finance using our enhanced trading system.

## 🚀 Quick Start

### 1. Test Basic Connectivity

```bash
# Test single symbol data retrieval
make yahoo-test-single

# Test batch data retrieval
make yahoo-test-batch
```

### 2. Run Full Demo

```bash
# Run complete Yahoo Finance demo
make yahoo-demo

# Run demo inside Docker
make yahoo-demo-docker
```

### 3. Run Backtests with Real Data

```bash
# Run backtest with real Yahoo Finance data
make yahoo-backtest-real

# Run backtest with real data inside Docker
make yahoo-backtest-real-docker
```

## 📊 Enhanced Yahoo Finance Service

Our enhanced service provides:

### Features
- **Real-time price data** for any stock symbol
- **Historical OHLCV data** with customizable timeframes
- **Symbol information** including company details, sector, market cap
- **Market hours** and trading status
- **Rate limiting** to avoid API restrictions
- **Error handling** with graceful fallbacks
- **Retry logic** for network issues
- **Batch processing** for multiple symbols

### Key Methods

```python
from services.market_data.yahoo_finance_service import YahooFinanceService

# Initialize service
service = YahooFinanceService(rate_limit_delay=0.1)  # 100ms delay between requests

# Get live price
price = service.get_live_price('AAPL')

# Get historical data
data = service.get_historical_data('AAPL', '2024-01-01', '2024-12-31', '1d')

# Get symbol information
info = service.get_symbol_info('AAPL')

# Get multiple symbols
market_data = service.get_multiple_symbols(['AAPL', 'GOOGL', 'MSFT'], '2024-01-01', '2024-12-31')

# Validate symbol
is_valid = service.validate_symbol('AAPL')

# Get market hours
hours = service.get_market_hours()
```

## 🔧 Configuration

### Rate Limiting
The service includes built-in rate limiting to avoid being blocked by Yahoo Finance:

```python
# Conservative rate limiting (recommended for production)
service = YahooFinanceService(rate_limit_delay=0.2)  # 200ms between requests

# Aggressive rate limiting (for testing)
service = YahooFinanceService(rate_limit_delay=0.05)  # 50ms between requests
```

### Error Handling
The service handles various error scenarios:

- **Network timeouts**: Automatic retry with exponential backoff
- **Rate limiting**: Built-in delays between requests
- **Invalid symbols**: Graceful handling with validation
- **Empty responses**: Fallback to mock data for testing

## 📈 Data Formats

### Historical Data Structure
```python
# DataFrame with standardized column names
{
    'OPEN': float,      # Opening price
    'HIGH': float,      # High price
    'LOW': float,       # Low price
    'CLOSE': float,     # Closing price
    'VOLUME': int,      # Trading volume
    'SYMBOL': str       # Stock symbol
}
```

### Symbol Information
```python
{
    'symbol': 'AAPL',
    'name': 'Apple Inc.',
    'sector': 'Technology',
    'industry': 'Consumer Electronics',
    'market_cap': 3000000000000,
    'current_price': 150.25,
    'volume': 50000000,
    'pe_ratio': 25.5,
    'dividend_yield': 0.005,
    'beta': 1.2,
    'currency': 'USD'
}
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Expecting value: line 1 column 1" Error
**Cause**: Yahoo Finance returning empty response
**Solution**: 
- Check internet connectivity
- Verify symbol is valid
- Increase rate limiting delay
- Use fallback mock data for testing

#### 2. No Data Returned
**Cause**: Symbol may be delisted or invalid
**Solution**:
```python
# Validate symbol first
if service.validate_symbol('SYMBOL'):
    data = service.get_historical_data('SYMBOL', start_date, end_date)
```

#### 3. Rate Limiting Issues
**Cause**: Too many requests too quickly
**Solution**:
```python
# Increase delay between requests
service = YahooFinanceService(rate_limit_delay=0.5)  # 500ms delay
```

### Debug Mode
Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

service = YahooFinanceService()
# Now you'll see detailed request/response logs
```

## 🔄 Integration with Backtesting

### Using Real Data in Backtests

```python
from backtesting.backtest_engine import BacktestEngine

# Initialize with real data
engine = BacktestEngine(use_real_data=True)

# Run backtest
results = await engine.run_backtest(
    symbols=['AAPL', 'GOOGL', 'MSFT'],
    start_date='2024-01-01',
    end_date='2024-12-31',
    strategies=['sma_crossover', 'rsi', 'macd']
)
```

### Fallback to Mock Data
If real data is unavailable, the system automatically falls back to mock data:

```python
# Force mock data for testing
engine = BacktestEngine(use_real_data=False)
```

## 📊 Data Quality

### What You Get
- **Real-time prices**: Current market prices
- **Historical data**: OHLCV data with adjustments for splits/dividends
- **Company information**: Sector, industry, financial metrics
- **Market status**: Trading hours, market state

### Limitations
- **Delayed data**: Some data may be delayed by 15-20 minutes
- **Rate limits**: Yahoo Finance has rate limiting
- **Symbol availability**: Not all symbols may be available
- **Data gaps**: Some historical periods may have missing data

## 🚀 Advanced Usage

### Custom Data Intervals
```python
# Daily data
daily_data = service.get_historical_data('AAPL', '2024-01-01', '2024-12-31', '1d')

# Hourly data (limited to recent periods)
hourly_data = service.get_historical_data('AAPL', '2024-12-01', '2024-12-31', '1h')

# 5-minute data (very limited)
minute_data = service.get_historical_data('AAPL', '2024-12-30', '2024-12-31', '5m')
```

### Batch Processing
```python
# Process multiple symbols efficiently
symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX']
market_data = service.get_multiple_symbols(symbols, '2024-01-01', '2024-12-31')

# Check success rate
successful = len(market_data)
total = len(symbols)
print(f"Successfully downloaded {successful}/{total} symbols")
```

### Convenience Functions
```python
from services.market_data.yahoo_finance_service import get_market_data, get_live_prices

# Quick market data download
data = get_market_data(['AAPL', 'GOOGL'], '2024-01-01', '2024-12-31')

# Quick live prices
prices = get_live_prices(['AAPL', 'GOOGL', 'MSFT'])
```

## 🔒 Best Practices

### 1. Rate Limiting
- Use conservative delays in production (200-500ms)
- Implement exponential backoff for retries
- Monitor for rate limit responses

### 2. Error Handling
- Always validate symbols before requesting data
- Implement fallback mechanisms
- Log errors for debugging

### 3. Data Validation
- Check for empty DataFrames
- Verify data quality (no negative prices, reasonable volumes)
- Handle missing data gracefully

### 4. Caching
- Cache frequently requested data
- Implement TTL (Time To Live) for cached data
- Use Redis or similar for distributed caching

## 📝 Example Scripts

### Basic Data Retrieval
```python
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.yahoo_finance_service import YahooFinanceService
from datetime import datetime, timedelta

# Initialize service
service = YahooFinanceService()

# Get current price
price = service.get_live_price('AAPL')
print(f"AAPL Current Price: ${price:.2f}")

# Get historical data
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

data = service.get_historical_data('AAPL', start_date, end_date)
if data is not None:
    print(f"Downloaded {len(data)} records")
    print(f"Latest close: ${data['CLOSE'].iloc[-1]:.2f}")
```

### Portfolio Monitoring
```python
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.market_data.yahoo_finance_service import get_live_prices

# Monitor portfolio
portfolio = {
    'AAPL': 100,
    'GOOGL': 50,
    'MSFT': 75,
    'TSLA': 25
}

# Get current prices
prices = get_live_prices(list(portfolio.keys()))

# Calculate portfolio value
total_value = 0
for symbol, shares in portfolio.items():
    if symbol in prices:
        value = shares * prices[symbol]
        total_value += value
        print(f"{symbol}: {shares} shares @ ${prices[symbol]:.2f} = ${value:,.2f}")

print(f"Total Portfolio Value: ${total_value:,.2f}")
```

## 🎯 Next Steps

1. **Test the service**: Run `make yahoo-demo` to see it in action
2. **Integrate with strategies**: Use real data in your trading strategies
3. **Set up monitoring**: Monitor data quality and API health
4. **Implement caching**: Add Redis caching for frequently accessed data
5. **Add more data sources**: Consider additional providers for redundancy

## 📚 Additional Resources

- [Yahoo Finance API Documentation](https://finance.yahoo.com/)
- [yfinance Library Documentation](https://pypi.org/project/yfinance/)
- [Market Data Best Practices](https://www.investopedia.com/)
- [Trading System Architecture](ARCHITECTURE.md)

---

**Note**: This service uses the Yahoo Finance API through the `yfinance` library. Please respect rate limits and terms of service. For production use, consider using paid data providers for more reliable and comprehensive data. 