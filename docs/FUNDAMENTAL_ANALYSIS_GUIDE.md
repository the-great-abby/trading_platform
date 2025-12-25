# 📊 Fundamental Analysis with Polygon Financials API

## Overview

This guide covers the comprehensive fundamental analysis capabilities integrated into the trading system using [Polygon.io's new Financials API](https://polygon.io/blog/announcing-polygon-io-financials-balance-sheets-cash-flow-income-statements-and-ratios).

## Features

### ✅ What's Included

1. **Polygon Financials API Client**
   - Balance Sheets (quarterly & annual)
   - Cash Flow Statements (quarterly, annual, TTM)
   - Income Statements (quarterly, annual, TTM)
   - Daily Financial Ratios (P/E, ROE, D/E, etc.)

2. **Fundamental Stock Screener**
   - 9 pre-defined screening presets
   - Custom screening criteria builder
   - Financial health scoring system
   - Stock comparison tools

3. **AI-Enhanced Analysis**
   - LLM prompt builder with fundamental context
   - Comprehensive fundamental analysis for stocks
   - Integration with existing AI analysis services

4. **REST API Service**
   - FastAPI-based microservice
   - Full CRUD operations for all financial data
   - Screening and comparison endpoints
   - Kubernetes-ready deployment

## Quick Start

### 1. Deploy the Service

```bash
# Build and deploy to Kubernetes
make -f makefiles/Makefile.fundamental-analysis deploy

# Port forward to access locally
make -f makefiles/Makefile.fundamental-analysis port-forward
```

### 2. Run Demo Scripts

```bash
# Comprehensive demo of all features
python demo/demo_fundamental_analysis.py

# Focused screening demo
python demo/demo_fundamental_screener.py
```

### 3. Use the API

Access the service at `http://localhost:11090` (or via Kubernetes service).

#### Get Financial Ratios

```bash
curl http://localhost:11090/api/v1/ratios/AAPL
```

#### Screen Stocks

```bash
curl -X POST http://localhost:11090/api/v1/screening/screen \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "preset": "quality_stocks",
    "min_score": 80
  }'
```

#### Get Health Score

```bash
curl http://localhost:11090/api/v1/screening/health-score/AAPL
```

## Python Usage

### Basic Ratios Retrieval

```python
from src.services.market_data.polygon_financials import PolygonFinancialsClient

client = PolygonFinancialsClient()

# Get latest ratios
ratios = client.get_ratios("AAPL", limit=1)
if ratios:
    r = ratios[0]
    print(f"P/E: {r.price_to_earnings}")
    print(f"ROE: {r.return_on_equity * 100:.2f}%")
    print(f"Debt/Equity: {r.debt_to_equity}")
```

### Screening Stocks

```python
from src.services.analysis.fundamental_screener import FundamentalScreener

screener = FundamentalScreener()

# Use a preset
results = screener.screen_with_preset(
    tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],
    preset_name="quality_stocks",
    min_score=80.0
)

for result in results:
    print(f"{result.ticker}: Score {result.score:.0f}%")
```

### Custom Screening

```python
from src.services.analysis.fundamental_screener import (
    FundamentalScreener,
    ScreenerCriteria,
    ScreenerCondition
)

screener = FundamentalScreener()

# Define custom criteria
criteria = [
    ScreenerCriteria("price_to_earnings", ScreenerCondition.LESS_THAN, 20),
    ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.15),
    ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 1.0),
]

results = screener.screen_stocks(tickers, criteria, min_score=80.0)
```

### AI-Enhanced Analysis

```python
from src.services.analysis.fundamental_ai_analyzer import FundamentalAIAnalyzer

analyzer = FundamentalAIAnalyzer()

# Get fundamental context for LLM
context = analyzer.get_fundamental_context("AAPL")

# Build enhanced LLM prompt
prompt = analyzer.build_llm_prompt_with_fundamentals(
    ticker="AAPL",
    current_price=175.0,
    technical_data=None,  # Add if available
    sentiment_data=None    # Add if available
)

# Compare stocks
comparison_df = analyzer.compare_stocks(["AAPL", "MSFT", "GOOGL"])
print(comparison_df)
```

## Available Screening Presets

| Preset | Description | Key Criteria |
|--------|-------------|--------------|
| `value_stocks` | Low P/E, P/B with strong profitability | P/E: 5-15, P/B < 3, ROE > 15% |
| `growth_stocks` | High profitability, low debt | ROE > 20%, ROA > 10%, D/E < 1.0 |
| `dividend_stocks` | High dividend yield with stability | Div Yield > 3%, D/E < 2.0, Current > 1.0 |
| `quality_stocks` | Strong balance sheet and profitability | ROE > 15%, ROA > 8%, D/E < 1.0 |
| `undervalued_high_quality` | Low EV/EBITDA with strong metrics | EV/EBITDA < 12, ROE > 15% |
| `buffett_style` | Warren Buffett inspired criteria | ROE > 20%, D/E < 0.5, P/E: 10-25 |
| `deep_value` | Extremely low valuation multiples | P/E < 10, P/B < 1.5, P/S < 1.0 |
| `financially_strong` | Focus on liquidity and low leverage | Current > 2.0, Quick > 1.5, D/E < 0.5 |
| `fcf_focused` | Strong free cash flow generation | P/FCF < 20, ROA > 8% |

## Financial Health Scoring

The system calculates a comprehensive financial health score (0-100) based on:

- **Valuation** (20 points): P/E, P/B ratios
- **Profitability** (20 points): ROE, ROA
- **Liquidity** (20 points): Current, Quick ratios
- **Leverage** (20 points): Debt/Equity ratio
- **Efficiency** (20 points): EV/EBITDA, P/FCF

Ratings:
- **Excellent**: 80-100 points
- **Good**: 65-79 points
- **Fair**: 50-64 points
- **Poor**: 35-49 points
- **Very Poor**: 0-34 points

## API Endpoints

### Ratios
- `GET /api/v1/ratios/{ticker}` - Get latest financial ratios

### Financial Statements
- `GET /api/v1/income-statement/{ticker}` - Income statement
- `GET /api/v1/cash-flow/{ticker}` - Cash flow statement
- `GET /api/v1/balance-sheet/{ticker}` - Balance sheet
- `GET /api/v1/comprehensive/{ticker}` - All data in one call

### Screening
- `GET /api/v1/screening/presets` - List available presets
- `POST /api/v1/screening/screen` - Screen stocks
- `GET /api/v1/screening/health-score/{ticker}` - Health score

### AI Integration
- `GET /api/v1/ai/context/{ticker}` - Fundamental context for LLM
- `GET /api/v1/ai/prompt/{ticker}` - Enhanced LLM prompt
- `POST /api/v1/ai/compare` - Compare multiple stocks

## Integration with Existing Services

### AI Analysis Service

The fundamental data automatically enhances LLM prompts in the AI analysis service:

```python
# In your AI analysis service
from src.services.analysis.fundamental_ai_analyzer import FundamentalAIAnalyzer

analyzer = FundamentalAIAnalyzer()

# Get enhanced context
context = analyzer.get_fundamental_context(ticker)

# Use in your LLM prompt
if context.get("has_data"):
    health_score = context["health_score"]
    prompt += f"\nFinancial Health: {health_score['rating']} ({health_score['percentage']:.0f}/100)"
```

### Strategy Selection

Use fundamental screening to filter stocks before strategy execution:

```python
from src.services.analysis.fundamental_screener import FundamentalScreener

screener = FundamentalScreener()

# Only trade high-quality stocks
quality_stocks = screener.screen_with_preset(
    tickers=SYMBOLS,
    preset_name="quality_stocks",
    min_score=75.0
)

quality_tickers = [r.ticker for r in quality_stocks]
# Use quality_tickers in your strategies
```

## Configuration

Update `src/utils/trading_config.py`:

```python
FUNDAMENTAL_ANALYSIS_CONFIG = {
    'enabled': True,
    'polygon_financials_enabled': True,
    'screening_presets': {
        'default': 'quality_stocks',
    },
    'screening_criteria': {
        'pe_ratio_max': 25,
        'roe_min': 0.15,
        'debt_to_equity_max': 1.5,
    },
    'ai_integration': {
        'include_in_llm_analysis': True,
        'include_ratios': True,
        'include_statements': True,
    }
}
```

## Makefile Commands

```bash
# Deploy service
make -f makefiles/Makefile.fundamental-analysis deploy

# Restart service
make -f makefiles/Makefile.fundamental-analysis restart

# View logs
make -f makefiles/Makefile.fundamental-analysis logs

# Port forward
make -f makefiles/Makefile.fundamental-analysis port-forward

# Run demos
make -f makefiles/Makefile.fundamental-analysis demo

# Test endpoints
make -f makefiles/Makefile.fundamental-analysis test-all

# Clean up
make -f makefiles/Makefile.fundamental-analysis clean
```

## Example Use Cases

### 1. Pre-Trade Fundamental Check

```python
# Before executing a trade, check fundamentals
screener = FundamentalScreener()
result = screener.screen_stock("AAPL", screener.presets["quality_stocks"].criteria)

if result and result.score >= 75:
    # Stock passes fundamental checks
    execute_trade("AAPL")
else:
    # Skip trade due to weak fundamentals
    logger.warning(f"AAPL failed fundamental screening: {result.score if result else 0}%")
```

### 2. Portfolio Construction

```python
# Build a quality portfolio
analyzer = FundamentalAIAnalyzer()
comparison = analyzer.compare_stocks(SYMBOLS)

# Select top 10 by health score
top_stocks = comparison.nlargest(10, 'Health Score')
portfolio_tickers = top_stocks['Ticker'].tolist()
```

### 3. Opportunity Identification

```python
# Find undervalued stocks with strong fundamentals
screener = FundamentalScreener()
opportunities = screener.screen_with_preset(
    tickers=SYMBOLS,
    preset_name="undervalued_high_quality",
    min_score=80.0
)

for opp in opportunities:
    print(f"{opp.ticker}: P/E={opp.ratios.price_to_earnings:.1f}, "
          f"ROE={opp.ratios.return_on_equity*100:.1f}%")
```

## Data Refresh

- **Ratios**: Updated daily by Polygon
- **Statements**: Updated quarterly/annually after filings
- **Cache**: 24-hour TTL (configurable)

## Requirements

### Polygon API Plan

⚠️ **IMPORTANT**: The Polygon Financials API requires:
- **Stocks Advanced** plan or higher, OR
- **Financials API add-on** to your existing plan

If you see **403 Forbidden** errors, your current plan doesn't include access to these endpoints. Visit [Polygon.io pricing](https://polygon.io/pricing) to upgrade.

### Security

✅ API keys are sent via **Authorization header** (Bearer token) for security
- Keys are NOT exposed in URLs or logs
- Fallback to query parameter auth if header auth fails
- All requests use HTTPS

## Troubleshooting

### 403 Forbidden Error
**Cause**: Your Polygon API plan doesn't include Financials API access

**Solutions**:
1. Upgrade to Stocks Advanced or Business plan
2. Purchase Financials API as an add-on
3. Contact Polygon support for options

### No data for ticker
- Ensure ticker is valid and traded on US exchanges
- Check if Polygon has coverage for the ticker
- Verify POLYGON_API_KEY is set correctly in `.env` file

### Rate limiting
- The client implements automatic rate limiting
- Default: 1 request/second
- Adjusts dynamically based on rate limit responses

### Service not accessible
```bash
# Check pod status
kubectl get pods -n trading-system -l app=fundamental-analysis-service

# Check logs
kubectl logs -n trading-system -l app=fundamental-analysis-service --tail=50

# Verify port forward
lsof -i :11090
```

## Next Steps

1. **Backtest Integration**: Use fundamental filters in backtest strategies
2. **Alerting**: Set up alerts when stocks meet screening criteria
3. **Dashboard**: Build visualization dashboard for fundamental metrics
4. **Historical Analysis**: Track how fundamental scores correlate with returns

## Resources

- [Polygon Financials API Docs](https://polygon.io/docs/stocks/get_vx_reference_financials)
- [API Announcement Blog Post](https://polygon.io/blog/announcing-polygon-io-financials-balance-sheets-cash-flow-income-statements-and-ratios)
- Local API docs: `http://localhost:11090/docs` (when service is running)

## Support

For issues or questions:
1. Check service logs: `make -f makefiles/Makefile.fundamental-analysis logs`
2. Verify API key: `kubectl get secret trading-secrets -n trading-system -o yaml`
3. Test connectivity: `make -f makefiles/Makefile.fundamental-analysis test-health`

---

**Note**: Requires Polygon.io Stocks Advanced plan or higher to access Financials API endpoints.

