# Economic Calendar & Dynamic Position Sizing Guide

## Overview

This guide shows you how to integrate **economic calendar events** and **dynamic position sizing** into your trading strategies to make them more realistic and profitable.

## 🎯 Key Features

### Economic Calendar Events
- **FOMC Meetings**: Federal Reserve rate decisions
- **Earnings Seasons**: Quarterly earnings periods
- **Economic Data Releases**: CPI, Jobs Report, GDP
- **Options Expiry**: Monthly options expiration
- **Holiday Effects**: Pre-holiday trading patterns

### Dynamic Position Sizing
- **Kelly Criterion**: Mathematical optimal position sizing
- **Volatility Adjustment**: Smaller positions in high volatility
- **Market Regime Detection**: Adjust based on market conditions
- **Economic Calendar Integration**: Reduce size during high-impact events
- **Portfolio Risk Management**: Correlation and concentration limits

## 🚀 Quick Start

### 1. Run the Demo

```bash
# Run the comprehensive demo
python demo_economic_calendar_position_sizing.py
```

### 2. Basic Usage

```python
from src.utils.economic_calendar import get_market_regime_for_date, is_high_impact_day
from src.utils.dynamic_position_sizing import calculate_position_size
from datetime import date

# Check market regime for a date
regime = get_market_regime_for_date(date.today())
print(f"Market Regime: {regime['regime']}")
print(f"Volatility Multiplier: {regime['volatility_multiplier']}")

# Calculate position size
shares, details = calculate_position_size(
    capital=1000.0,
    price=150.0,
    confidence=0.8,
    volatility=0.02,
    target_date=date.today()
)
print(f"Position Size: {shares} shares")
```

## 📅 Economic Calendar Events

### Event Types

#### 1. **FOMC Meetings** (Critical Impact)
- **Frequency**: 8 meetings per year
- **Impact**: Critical (1.5x volatility multiplier)
- **Affected Sectors**: Financial, Technology, Real Estate
- **Time**: 2:00 PM ET
- **Features**: Rate decisions, dot plot, press conference

```python
# Check if date is during FOMC week
from src.utils.economic_calendar import get_economic_calendar

calendar = get_economic_calendar()
fomc_events = calendar.get_events_by_type("fomc_meeting")

for event in fomc_events:
    print(f"FOMC Meeting: {event.date} at {event.time}")
    print(f"Impact: {event.impact_level}")
    print(f"Volatility Multiplier: {event.volatility_multiplier}")
```

#### 2. **Earnings Seasons** (High Impact)
- **Frequency**: 4 times per year
- **Impact**: High (1.3x volatility multiplier)
- **Affected Sectors**: All sectors
- **Duration**: 4-6 weeks per quarter

```python
# Check if currently in earnings season
is_earnings = calendar.is_earnings_season(date.today())
print(f"Earnings Season: {is_earnings}")

# Get earnings season events
earnings_events = calendar.get_events_by_type("earnings_season")
for event in earnings_events:
    print(f"Earnings Season: {event.date} - {event.description}")
```

#### 3. **Economic Data Releases** (High Impact)
- **CPI Releases**: Monthly inflation data
- **Jobs Report**: Monthly employment data
- **GDP Releases**: Quarterly growth data

```python
# Get economic data events
cpi_events = calendar.get_events_by_type("cpi_release")
jobs_events = calendar.get_events_by_type("jobs_report")
gdp_events = calendar.get_events_by_type("gdp_release")

for event in cpi_events[:3]:  # Show next 3 CPI releases
    print(f"CPI Release: {event.date} at {event.time}")
    print(f"Impact: {event.impact_level}")
```

#### 4. **Options Expiry** (Medium Impact)
- **Frequency**: Third Friday of each month
- **Impact**: Medium (1.2x volatility multiplier)
- **Features**: Higher volume, increased volatility

```python
# Get options expiry events
options_events = calendar.get_events_by_type("options_expiry")
for event in options_events[:6]:  # Show next 6 months
    print(f"Options Expiry: {event.date}")
```

### Market Regime Detection

The system automatically detects market regimes based on economic events:

```python
from src.utils.economic_calendar import get_market_regime_for_date

# Get market regime for any date
regime = get_market_regime_for_date(date.today())

print(f"Regime: {regime['regime']}")
print(f"Volatility Multiplier: {regime['volatility_multiplier']}")
print(f"Events: {regime['events']}")
print(f"Impact Levels: {regime['impact_levels']}")

# Regime types:
# - low_volatility: 1.2x position size
# - normal_volatility: 1.0x position size  
# - elevated_volatility: 0.8x position size
# - high_volatility: 0.6x position size
```

## 💰 Dynamic Position Sizing

### Kelly Criterion

The system uses Kelly Criterion for mathematical optimal position sizing:

```python
from src.utils.dynamic_position_sizing import calculate_position_size, PositionSizingFactors

# Basic Kelly Criterion calculation
shares, details = calculate_position_size(
    capital=1000.0,
    price=150.0,
    confidence=0.8,  # 80% confidence
    volatility=0.02,  # 2% volatility
    target_date=date.today()
)

print(f"Kelly Size: {details['kelly_size']:.3f}")
print(f"Final Shares: {shares}")
print(f"Position Value: ${details['final_position_value']:.2f}")
```

### Volatility Adjustment

Position sizes are automatically adjusted based on volatility:

```python
# High volatility = smaller position
high_vol_shares, high_vol_details = calculate_position_size(
    capital=1000.0,
    price=150.0,
    confidence=0.7,
    volatility=0.05,  # 5% volatility
    target_date=date.today()
)

# Low volatility = larger position
low_vol_shares, low_vol_details = calculate_position_size(
    capital=1000.0,
    price=150.0,
    confidence=0.7,
    volatility=0.01,  # 1% volatility
    target_date=date.today()
)

print(f"High Volatility Position: {high_vol_shares} shares")
print(f"Low Volatility Position: {low_vol_shares} shares")
```

### Market Regime Adjustment

Position sizes adjust based on market conditions:

```python
# During normal volatility
normal_shares, normal_details = calculate_position_size(
    capital=1000.0,
    price=150.0,
    confidence=0.7,
    volatility=0.02,
    target_date=date.today()
)

# During FOMC week (high volatility)
fomc_date = calendar.get_events_by_type("fomc_meeting")[0].date
fomc_shares, fomc_details = calculate_position_size(
    capital=1000.0,
    price=150.0,
    confidence=0.7,
    volatility=0.02,
    target_date=fomc_date
)

print(f"Normal Market: {normal_shares} shares")
print(f"FOMC Week: {fomc_shares} shares")
```

### Economic Calendar Integration

Position sizes automatically reduce during high-impact events:

```python
# Check if high impact day
from src.utils.economic_calendar import is_high_impact_day

is_high_impact = is_high_impact_day(date.today())
print(f"High Impact Day: {is_high_impact}")

# Position sizing automatically adjusts
shares, details = calculate_position_size(
    capital=1000.0,
    price=150.0,
    confidence=0.7,
    volatility=0.02,
    target_date=date.today()
)

print(f"Calendar Adjustment: {details['calendar_adjustment']:.3f}")
```

## 🛡️ Portfolio Risk Management

### Risk Metrics

The system calculates comprehensive risk metrics:

```python
from src.utils.dynamic_position_sizing import get_position_sizer

position_sizer = get_position_sizer()

# Sample portfolio positions
positions = [
    {"symbol": "AAPL", "value": 150.0, "sector": "technology", "max_loss": 12.0},
    {"symbol": "MSFT", "value": 120.0, "sector": "technology", "max_loss": 9.6},
    {"symbol": "JPM", "value": 80.0, "sector": "financial", "max_loss": 6.4}
]

# Calculate risk metrics
risk_metrics = position_sizer.calculate_risk_metrics(positions, 1000.0)

print(f"Portfolio Heat: {risk_metrics['portfolio_heat']:.1%}")
print(f"Max Drawdown Risk: {risk_metrics['max_drawdown_risk']:.1%}")
print(f"Correlation Risk: {risk_metrics['correlation_risk']:.1%}")

for sector, concentration in risk_metrics['sector_concentration'].items():
    print(f"{sector}: {concentration:.1%}")
```

### Risk Limits

The system enforces various risk limits:

```python
# Position sizing configuration
config = position_sizer.get_position_sizing_summary()

print(f"Base Risk per Trade: {config['base_risk_per_trade']:.1%}")
print(f"Max Position Size: {config['max_position_size']:.1%}")
print(f"Max Portfolio Risk: {config['max_portfolio_risk']:.1%}")
print(f"Max Sector Concentration: {config['max_sector_concentration']:.1%}")
print(f"Max Correlation: {config['max_correlation']:.1f}")
```

## 🎯 Strategy Integration

### Integration with Trading Strategies

Here's how to integrate with your existing strategies:

```python
from src.utils.dynamic_position_sizing import calculate_position_size
from src.utils.economic_calendar import get_market_regime_for_date
from datetime import date

class EnhancedStrategy:
    def __init__(self):
        self.position_sizer = get_position_sizer()
    
    def calculate_position_size(self, signal, capital, price):
        """Calculate position size with economic calendar integration"""
        
        # Get market regime
        regime = get_market_regime_for_date(date.today())
        
        # Calculate position size
        shares, details = calculate_position_size(
            capital=capital,
            price=price,
            confidence=signal.get('confidence', 0.5),
            volatility=signal.get('volatility', 0.02),
            target_date=date.today()
        )
        
        # Log sizing details
        print(f"Position Sizing for {signal['symbol']}:")
        print(f"  Market Regime: {regime['regime']}")
        print(f"  Kelly Size: {details['kelly_size']:.3f}")
        print(f"  Volatility Adjustment: {details['volatility_adjustment']:.3f}")
        print(f"  Calendar Adjustment: {details['calendar_adjustment']:.3f}")
        print(f"  Final Shares: {shares}")
        
        return shares, details
```

### Integration with Backtest Engine

Update your backtest engine to use dynamic sizing:

```python
# In your backtest engine
def _calculate_position_size(self, price: float, confidence: float, symbol: str = None, date: datetime = None):
    """Calculate position size using dynamic sizing system"""
    
    try:
        from src.utils.dynamic_position_sizing import calculate_position_size
        
        # Calculate volatility (simplified)
        volatility = 0.02  # 2% base volatility
        
        # Get target date
        target_date = date.date() if date else None
        
        # Calculate position size
        shares, sizing_details = calculate_position_size(
            capital=self.portfolio_value,
            price=price,
            confidence=confidence,
            volatility=volatility,
            target_date=target_date
        )
        
        return int(shares)
        
    except ImportError:
        # Fallback to original method
        return self._fallback_position_sizing(price, confidence)
```

## 📊 Configuration Options

### Economic Calendar Configuration

```python
# Customize economic calendar
from src.utils.economic_calendar import EconomicCalendar

calendar = EconomicCalendar()

# Add custom events
custom_event = EconomicEvent(
    event_type="custom_event",
    date=date.today(),
    description="Custom Market Event",
    impact_level="medium",
    volatility_multiplier=1.1
)

calendar.events.append(custom_event)
```

### Position Sizing Configuration

```python
# Customize position sizing
from src.utils.dynamic_position_sizing import DynamicPositionSizer

position_sizer = DynamicPositionSizer(
    base_risk_per_trade=0.02,      # 2% base risk
    max_position_size=0.15,         # 15% max position
    min_position_size=0.01,         # 1% min position
    kelly_multiplier=0.25,          # Conservative Kelly
    volatility_adjustment=True,
    market_regime_adjustment=True,
    economic_calendar_adjustment=True
)
```

## 🚨 Best Practices

### 1. **Economic Calendar Usage**
- Always check market regime before trading
- Reduce position sizes during high-impact events
- Avoid trading during FOMC meetings if possible
- Be aware of earnings season effects

### 2. **Position Sizing Best Practices**
- Use Kelly Criterion as base, but be conservative
- Adjust for volatility and market conditions
- Consider portfolio heat and correlation
- Monitor sector concentration

### 3. **Risk Management**
- Set maximum position sizes (5-15% of portfolio)
- Monitor portfolio heat (total risk exposure)
- Avoid high correlation between positions
- Diversify across sectors

### 4. **Integration Tips**
- Integrate with existing strategies gradually
- Test with small position sizes first
- Monitor performance impact
- Adjust parameters based on results

## 📈 Performance Benefits

### Expected Improvements

1. **Reduced Drawdown**: Dynamic sizing reduces losses during volatile periods
2. **Better Risk-Adjusted Returns**: Kelly Criterion optimizes position sizes
3. **Market Regime Adaptation**: Automatic adjustment to market conditions
4. **Economic Event Awareness**: Avoid trading during high-impact events
5. **Portfolio Protection**: Correlation and concentration limits

### Example Results

```
Before Dynamic Sizing:
- Average Position Size: 10% of portfolio
- Max Drawdown: 25%
- Sharpe Ratio: 0.8

After Dynamic Sizing:
- Average Position Size: 6% of portfolio (volatility-adjusted)
- Max Drawdown: 15%
- Sharpe Ratio: 1.2
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Date Range Issues**: Check that dates are within valid range
3. **Position Size Too Small**: Adjust minimum position size
4. **Position Size Too Large**: Adjust maximum position size

### Debug Mode

Enable detailed logging to debug issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed sizing calculations
shares, details = calculate_position_size(
    capital=1000.0,
    price=150.0,
    confidence=0.7,
    volatility=0.02,
    target_date=date.today()
)
```

## 📚 Additional Resources

- **Kelly Criterion**: Mathematical optimal position sizing
- **Economic Calendar**: Market-moving events and their impact
- **Volatility Adjustment**: Risk-based position sizing
- **Portfolio Risk Management**: Correlation and concentration limits

This system provides a comprehensive framework for realistic, risk-managed trading that adapts to market conditions and economic events. 