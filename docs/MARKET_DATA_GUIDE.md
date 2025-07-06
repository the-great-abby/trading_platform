# Market Data Providers Guide

## Overview

This trading system supports multiple market data providers with automatic fallback mechanisms. When one provider fails, the system automatically tries the next available provider.

## Available Providers

### 1. Yahoo Finance (Default - Free)
- **Cost**: Free
- **API Key**: Not required
- **Rate Limits**: 2000 requests per hour
- **Data**: Historical OHLCV, live prices, company info
- **Coverage**: Global stocks, ETFs, indices

**Pros:**
- No API key required
- Good coverage
- Real-time and historical data
- Free to use

**Cons:**
- Rate limited
- Can be unreliable at times
- Limited to 1-minute intervals for intraday

### 2. Alpha Vantage (Free Tier Available)
- **Cost**: Free tier (500 requests/day), Paid plans available
- **API Key**: Required (free at https://www.alphavantage.co/)
- **Rate Limits**: 5 requests/minute (free), 1200/minute (paid)
- **Data**: Real-time, historical, technical indicators
- **Coverage**: Global stocks, forex, crypto

**Pros:**
- Reliable API
- Technical indicators included
- Good documentation
- Free tier available

**Cons:**
- Rate limited on free tier
- Requires API key

### 3. IEX Cloud (Free Tier Available)
- **Cost**: Free tier (50,000 messages/month), Paid plans available
- **API Key**: Required (free at https://iexcloud.io/)
- **Rate Limits**: Varies by plan
- **Data**: Real-time, historical, fundamentals
- **Coverage**: US stocks, ETFs

**Pros:**
- High-quality data
- Good for US markets
- Real-time data
- Free tier available

**Cons:**
- Limited to US markets
- Requires API key

### 4. Polygon.io (Free Tier Available)
- **Cost**: Free tier (5 requests/minute), Paid plans available
- **API Key**: Required (free at https://polygon.io/)
- **Rate Limits**: 5 requests/minute (free)
- **Data**: Real-time, historical, options, forex
- **Coverage**: US stocks, options, forex

**Pros:**
- High-quality data
- Options data available
- Real-time data
- Free tier available

**Cons:**
- Rate limited on free tier
- Requires API key

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in your project root:

```bash
# Alpha Vantage (optional)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# IEX Cloud (optional)
IEX_CLOUD_API_KEY=your_iex_cloud_key_here

# Polygon (optional)
POLYGON_API_KEY=your_polygon_key_here
```

### 2. Get Free API Keys

#### Alpha Vantage
1. Go to https://www.alphavantage.co/
2. Sign up for free account
3. Get your API key
4. Add to `.env` file

#### IEX Cloud
1. Go to https://iexcloud.io/
2. Sign up for free account
3. Get your API key
4. Add to `.env` file

#### Polygon
1. Go to https://polygon.io/
2. Sign up for free account
3. Get your API key
4. Add to `.env` file

### 3. Test the Setup

```bash
# Test market data providers
make test-market-data

# Test specific provider
make test-yahoo-finance
make test-alpha-vantage
make test-iex-cloud
make test-polygon
```

## Usage Examples

### Basic Usage

```python
from src.services.market_data.market_data_provider import get_market_data_manager

# Get market data manager with all providers
manager = get_market_data_manager()

# Get historical data (automatically tries all providers)
data = manager.get_historical_data("AAPL", "2024-01-01", "2024-12-31")

# Get live price
price = manager.get_live_price("AAPL")

# Get multiple symbols
symbols = ["AAPL", "GOOGL", "MSFT"]
data = manager.get_multiple_symbols(symbols, "2024-01-01", "2024-12-31")
```

### Provider-Specific Usage

```python
from src.services.market_data.market_data_provider import (
    YahooFinanceService,
    AlphaVantageProvider,
    IEXCloudProvider,
    PolygonProvider
)

# Use specific provider
yahoo = YahooFinanceService()
alpha = AlphaVantageProvider()
iex = IEXCloudProvider()
polygon = PolygonProvider()

# Get data from specific provider
data = yahoo.get_historical_data("AAPL", "2024-01-01", "2024-12-31")
```

### Check Provider Status

```python
manager = get_market_data_manager()
status = manager.get_provider_status()

for provider, is_working in status.items():
    print(f"{provider}: {'✅ Working' if is_working else '❌ Failed'}")
```

## Integration with Backtesting

The backtesting system automatically uses the market data manager:

```python
# In backtest_engine.py
from src.services.market_data.market_data_provider import get_market_data_manager

class BacktestEngine:
    def __init__(self, use_real_data: bool = True):
        self.use_real_data = use_real_data
        self.market_data_manager = get_market_data_manager() if use_real_data else None
    
    async def _get_market_data(self, symbols, start_date, end_date):
        if self.use_real_data and self.market_data_manager:
            return self.market_data_manager.get_multiple_symbols(symbols, start_date, end_date)
        else:
            return self._generate_mock_data(symbols, start_date, end_date)
```

## Makefile Commands

```bash
# Test all market data providers
make test-market-data

# Test specific providers
make test-yahoo-finance
make test-alpha-vantage
make test-iex-cloud
make test-polygon

# Run backtest with real data
make run-backtest-real-data

# Get live prices
make get-live-prices SYMBOLS="AAPL,GOOGL,MSFT"

# Check provider status
make check-providers
```

## Troubleshooting

### Common Issues

1. **No data returned**
   - Check if API keys are set correctly
   - Verify symbols are valid
   - Check rate limits

2. **Rate limiting**
   - Wait and retry
   - Upgrade to paid plan
   - Use multiple providers

3. **API errors**
   - Check API documentation
   - Verify request format
   - Check network connectivity

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed logs of provider attempts
manager = get_market_data_manager()
data = manager.get_historical_data("AAPL", "2024-01-01", "2024-12-31")
```

## Performance Tips

1. **Use multiple providers**: The system automatically falls back if one fails
2. **Cache data**: Store frequently used data locally
3. **Batch requests**: Get multiple symbols at once
4. **Monitor rate limits**: Stay within provider limits

## Cost Comparison

| Provider | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| Yahoo Finance | Unlimited | N/A | Getting started, testing |
| Alpha Vantage | 500/day | $49.99/month | Technical analysis |
| IEX Cloud | 50K/month | $9/month | US markets |
| Polygon | 5/min | $29/month | Real-time trading |

## Recommendations

### For Development/Testing
- Use **Yahoo Finance** (no setup required)
- Add **Alpha Vantage** for better reliability

### For Production Trading
- Use **IEX Cloud** or **Polygon** for US markets
- Use **Alpha Vantage** for global markets
- Consider paid plans for higher rate limits

### For Backtesting
- Use **Yahoo Finance** for historical data
- Use **Alpha Vantage** for technical indicators
- Combine multiple providers for reliability

## Next Steps

1. **Get free API keys** for the providers you want to use
2. **Test the setup** with the provided commands
3. **Run backtests** with real market data
4. **Monitor performance** and adjust as needed
5. **Consider paid plans** for production use 