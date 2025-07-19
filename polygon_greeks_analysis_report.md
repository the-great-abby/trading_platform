# Polygon Greeks Data Analysis Report
Generated: 2025-07-17 15:30:47

## Summary Statistics
- Total endpoint tests: 35
- Successful responses (200): 30
- Tests with data found: 15
- Tests with Greeks data: 0

## Endpoint Analysis
### SNAPSHOT Endpoints
- Total tests: 5
- Successful: 0
- With Greeks: 0

### REFERENCE Endpoints
- Total tests: 20
- Successful: 20
- With Greeks: 0

**Sample data from /v3/reference/options/contracts:**
```json
{
  "cfi": "OCASPS",
  "contract_type": "call",
  "exercise_style": "american",
  "expiration_date": "2025-07-18",
  "primary_exchange": "BATO",
  "shares_per_contract": 100,
  "strike_price": 90,
  "ticker": "O:AAPL250718C00090000",
  "underlying_ticker": "AAPL"
}...
```

**Sample data from /v3/reference/options/contracts:**
```json
{
  "cfi": "OCASPS",
  "contract_type": "call",
  "exercise_style": "american",
  "expiration_date": "2025-07-18",
  "primary_exchange": "BATO",
  "shares_per_contract": 100,
  "strike_price": 60,
  "ticker": "O:TSLA250718C00060000",
  "underlying_ticker": "TSLA"
}...
```

**Sample data from /v3/reference/options/contracts:**
```json
{
  "cfi": "OCASPS",
  "contract_type": "call",
  "exercise_style": "american",
  "expiration_date": "2025-07-17",
  "primary_exchange": "BATO",
  "shares_per_contract": 100,
  "strike_price": 400,
  "ticker": "O:SPY250717C00400000",
  "underlying_ticker": "SPY"
}...
```

**Sample data from /v3/reference/options/contracts:**
```json
{
  "cfi": "OCASPS",
  "contract_type": "call",
  "exercise_style": "american",
  "expiration_date": "2025-07-17",
  "primary_exchange": "BATO",
  "shares_per_contract": 100,
  "strike_price": 400,
  "ticker": "O:QQQ250717C00400000",
  "underlying_ticker": "QQQ"
}...
```

**Sample data from /v3/reference/options/contracts:**
```json
{
  "cfi": "OCASPS",
  "contract_type": "call",
  "exercise_style": "american",
  "expiration_date": "2025-07-18",
  "primary_exchange": "BATO",
  "shares_per_contract": 100,
  "strike_price": 5,
  "ticker": "O:NVDA250718C00005000",
  "underlying_ticker": "NVDA"
}...
```

### AGGS Endpoints
- Total tests: 10
- Successful: 10
- With Greeks: 0

**Sample data from /v2/aggs/ticker/AAPL/prev:**
```json
{
  "T": "AAPL",
  "v": 47490532.0,
  "vw": 210.3633,
  "o": 210.295,
  "c": 210.16,
  "h": 212.4,
  "l": 208.64,
  "t": 1752696000000,
  "n": 535850
}...
```

**Sample data from /v2/aggs/ticker/AAPL/range/1/day/2025-06-17/2025-07-17:**
```json
{
  "v": 38856152.0,
  "vw": 196.4948,
  "o": 197.2,
  "c": 195.64,
  "h": 198.39,
  "l": 195.21,
  "t": 1750132800000,
  "n": 522902
}...
```

**Sample data from /v2/aggs/ticker/TSLA/prev:**
```json
{
  "T": "TSLA",
  "v": 97284786.0,
  "vw": 319.0476,
  "o": 312.8,
  "c": 321.67,
  "h": 323.5,
  "l": 312.62,
  "t": 1752696000000,
  "n": 1362478
}...
```

**Sample data from /v2/aggs/ticker/TSLA/range/1/day/2025-06-17/2025-07-17:**
```json
{
  "v": 88282669.0,
  "vw": 319.8117,
  "o": 326.09,
  "c": 316.35,
  "h": 327.26,
  "l": 314.74,
  "t": 1750132800000,
  "n": 1298505
}...
```

**Sample data from /v2/aggs/ticker/SPY/prev:**
```json
{
  "T": "SPY",
  "v": 88987511.0,
  "vw": 622.2168,
  "o": 623.74,
  "c": 624.22,
  "h": 624.73,
  "l": 618.05,
  "t": 1752696000000,
  "n": 961974
}...
```

**Sample data from /v2/aggs/ticker/SPY/range/1/day/2025-06-17/2025-07-17:**
```json
{
  "v": 82209365.0,
  "vw": 599.0958,
  "o": 600.21,
  "c": 597.53,
  "h": 601.75,
  "l": 596.76,
  "t": 1750132800000,
  "n": 827346
}...
```

**Sample data from /v2/aggs/ticker/QQQ/prev:**
```json
{
  "T": "QQQ",
  "v": 52314711.0,
  "vw": 555.7396,
  "o": 557.28,
  "c": 557.29,
  "h": 560.21,
  "l": 551.56,
  "t": 1752696000000,
  "n": 619013
}...
```

**Sample data from /v2/aggs/ticker/QQQ/range/1/day/2025-06-17/2025-07-17:**
```json
{
  "v": 42180866.0,
  "vw": 530.8473,
  "o": 531.71,
  "c": 529.08,
  "h": 533.325,
  "l": 527.91,
  "t": 1750132800000,
  "n": 555573
}...
```

**Sample data from /v2/aggs/ticker/NVDA/prev:**
```json
{
  "T": "NVDA",
  "v": 158831509.0,
  "vw": 170.5912,
  "o": 171.06,
  "c": 171.37,
  "h": 171.75,
  "l": 168.9,
  "t": 1752696000000,
  "n": 1514668
}...
```

**Sample data from /v2/aggs/ticker/NVDA/range/1/day/2025-06-17/2025-07-17:**
```json
{
  "v": 139108000.0,
  "vw": 144.4918,
  "o": 144.49,
  "c": 144.12,
  "h": 145.22,
  "l": 143.78,
  "t": 1750132800000,
  "n": 1141208
}...
```

## Recommendations
❌ **No Greeks data found** in current tests
- Check API subscription tier for options data access
- Verify API key permissions
- Consider alternative data providers

## Next Steps
1. Implement daily Greeks data collection
2. Store historical snapshots in database
3. Integrate with backtesting system
4. Monitor API rate limits and costs