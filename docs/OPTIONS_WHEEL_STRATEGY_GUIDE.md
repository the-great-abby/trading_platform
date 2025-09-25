# 🎯 Options Wheel Strategy Guide

## Overview

The Options Wheel Strategy is a comprehensive income-generating options strategy that systematically combines cash-secured put selling and covered call selling in a cyclical approach. This strategy is designed to generate consistent income while potentially acquiring stocks at discounted prices.

## 🔄 How the Options Wheel Works

### Two-Phase Operation

**Phase 1: Put Phase (Cash-Secured Puts)**
- Sell cash-secured puts on stocks you want to own
- Collect premium income upfront
- If stock stays above strike: keep premium, repeat
- If stock falls below strike: get assigned the stock at strike price

**Phase 2: Call Phase (Covered Calls)**
- Once you own stock (from assignment), sell covered calls against it
- Collect premium income while holding the stock
- If stock stays below call strike: keep premium and stock
- If stock rises above call strike: sell stock at call strike price

### The Complete Cycle

```
Put Phase → Assignment → Call Phase → Assignment → Put Phase → ...
   ↓           ↓           ↓           ↓           ↓
Sell Put   Get Stock   Sell Call   Sell Stock   Sell Put
Collect    at Strike   Collect     at Strike    Collect
Premium    Price       Premium     Price        Premium
```

## 🎯 Key Features

### Income Generation
- **Dual Income Streams**: Premium collection from both puts and calls
- **Consistent Cash Flow**: Systematic approach to income generation
- **Premium Optimization**: Dynamic strike selection for maximum premium

### Stock Acquisition
- **Discounted Entry**: Acquire stocks at strike price (often below market)
- **Cost Basis Reduction**: Premium received reduces effective cost basis
- **Quality Stock Selection**: Only trade stocks you're willing to own long-term

### Risk Management
- **Defined Risk**: Maximum loss is strike price minus premium received
- **Cash Management**: Controlled cash utilization limits
- **Position Sizing**: Risk-based position sizing per trade
- **Cycle Limits**: Maximum cycles per symbol to prevent over-concentration

## ⚙️ Configuration Parameters

### Put Phase Configuration
```python
put_days_to_expiration: int = 30        # Days to expiration for puts
put_profit_target_pct: float = 0.7      # 70% of max profit target
put_stop_loss_pct: float = 1.5          # 1.5x max profit stop loss
put_min_delta: float = -0.7             # Maximum delta (negative for puts)
put_max_delta: float = -0.3             # Minimum delta (negative for puts)
put_min_premium_pct: float = 0.015      # 1.5% minimum premium relative to stock price
```

### Call Phase Configuration
```python
call_days_to_expiration: int = 30       # Days to expiration for calls
call_profit_target_pct: float = 0.7     # 70% of max profit target
call_stop_loss_pct: float = 1.5         # 1.5x max profit stop loss
call_min_delta: float = 0.3             # Minimum delta for calls
call_max_delta: float = 0.7             # Maximum delta for calls
call_min_premium_pct: float = 0.02      # 2% minimum premium relative to stock price
```

### Wheel-Specific Configuration
```python
max_wheel_cycles: int = 5               # Maximum cycles per symbol
min_cycle_interval_days: int = 7        # Minimum days between cycles
assignment_buffer_days: int = 3         # Days to wait after assignment
max_cash_utilization: float = 0.8       # 80% max cash utilization
max_risk_per_trade: float = 0.02        # 2% of portfolio per trade
```

### Stock Selection Criteria
```python
min_stock_price: float = 50.0           # Minimum stock price
max_stock_price: float = 500.0          # Maximum stock price
min_volume: int = 1000000               # Minimum daily volume
min_options_volume: int = 100           # Minimum options volume
```

## 📊 Technical Analysis Integration

### Scoring System
The strategy uses a weighted scoring system to evaluate stocks:

```python
combined_score = (
    technical_score * 0.4 +      # Technical analysis weight
    volatility_score * 0.3 +     # Volatility analysis weight
    momentum_score * 0.3         # Momentum analysis weight
)
```

### Technical Indicators
- **RSI Analysis**: Prefers stocks in neutral zone (30-70)
- **Moving Averages**: Uptrend preference with price above SMAs
- **Bollinger Bands**: Middle band position for stability
- **Volume Analysis**: Above-average volume confirmation

### Volatility Analysis
- **Historical Volatility**: Higher volatility preferred for options selling
- **Volatility Scoring**: 30%+ annual volatility gets highest score
- **Options Pricing**: Volatility directly impacts premium collection

## 🎯 Market Conditions

### Ideal Market Conditions
- **Sideways Markets**: Perfect for income generation
- **Low to Moderate Volatility**: 15-30% annual volatility
- **Stable Trends**: Not too bullish or bearish
- **Good Liquidity**: High volume and options activity

### Strategy Selection
The options wheel strategy is automatically selected for:
- **Sideways Range Markets**: Primary strategy
- **Low Volatility Markets**: Secondary strategy
- **Bull Trending Markets**: Secondary strategy (for covered calls)

## 📈 Performance Tracking

### Key Metrics
- **Total Income**: Cumulative premium collected
- **Cycles Completed**: Number of complete wheel cycles
- **Win Rate**: Percentage of profitable cycles
- **Average Premium**: Average premium per trade
- **Cost Basis Reduction**: Effective cost reduction from premiums

### Wheel State Management
```python
wheel_position = {
    'phase': WheelPhase.PUT_PHASE,      # Current phase
    'cycles_completed': 0,              # Cycles completed
    'total_income': 0.0,                # Total income generated
    'shares_owned': 0,                  # Shares currently owned
    'average_cost': 0.0,                # Average cost basis
    'last_cycle_date': None,            # Last cycle date
    'assignment_date': None             # Last assignment date
}
```

## 🚀 Usage Examples

### Basic Implementation
```python
from src.strategies.options.options_wheel_strategy import OptionsWheelStrategy

# Initialize strategy
strategy = OptionsWheelStrategy(
    put_days_to_expiration=30,
    call_days_to_expiration=30,
    max_wheel_cycles=5,
    max_risk_per_trade=0.02
)

# Generate signal
signal = await strategy.generate_signal(symbol, market_data)
```

### Advanced Configuration
```python
strategy = OptionsWheelStrategy(
    # Put Phase
    put_days_to_expiration=45,
    put_min_delta=-0.6,
    put_max_delta=-0.4,
    put_min_premium_pct=0.02,
    
    # Call Phase
    call_days_to_expiration=30,
    call_min_delta=0.3,
    call_max_delta=0.6,
    call_min_premium_pct=0.025,
    
    # Wheel Management
    max_wheel_cycles=3,
    min_cycle_interval_days=10,
    max_cash_utilization=0.7,
    
    # Stock Selection
    min_stock_price=75.0,
    max_stock_price=300.0,
    min_volume=2000000
)
```

## 🔧 Integration with Trading System

### Strategy Registration
```python
from src.strategies.options import OptionsWheelStrategy

# Register with trading engine
trading_engine.register_strategy("OptionsWheel", OptionsWheelStrategy())
```

### Configuration File
```yaml
# strategy_automation_config.yaml
strategy_selection:
  market_condition_strategies:
    sideways_range:
      secondary: ["OptionsWheel", "IronCondor", "CoveredCall"]
    low_volatility:
      secondary: ["OptionsWheel", "CalendarSpread", "IronCondor"]
```

### Portfolio Integration
- **Cash Management**: Integrates with portfolio cash allocation
- **Position Tracking**: Tracks stock ownership and options positions
- **Risk Management**: Respects portfolio risk limits
- **Performance Reporting**: Provides detailed performance metrics

## 📊 Demo and Testing

### Running the Demo
```bash
python demo/demo_options_wheel_strategy.py
```

### Demo Features
- **Strategy Configuration Display**: Shows all configuration parameters
- **Market Data Simulation**: Generates realistic market data
- **Signal Generation**: Tests signal generation for multiple symbols
- **State Management**: Demonstrates wheel state transitions
- **Performance Metrics**: Shows scoring and selection criteria

### Backtesting Integration
The strategy integrates with the existing backtesting system:
- **Historical Data**: Uses historical market data
- **Options Data**: Integrates with options data service
- **Performance Analysis**: Provides detailed performance metrics
- **Risk Analysis**: Calculates risk-adjusted returns

## 🎯 Best Practices

### Stock Selection
- **Quality First**: Only trade stocks you're willing to own long-term
- **Liquidity**: Ensure high volume and options activity
- **Price Range**: Stay within configured price range
- **Fundamentals**: Consider company fundamentals and outlook

### Risk Management
- **Position Sizing**: Never risk more than configured percentage
- **Diversification**: Don't over-concentrate in single stocks
- **Cycle Limits**: Respect maximum cycle limits
- **Cash Management**: Maintain adequate cash reserves

### Market Timing
- **Volatility**: Higher volatility generally means higher premiums
- **Trend Analysis**: Avoid strongly trending markets
- **Economic Events**: Be aware of earnings and other events
- **Market Conditions**: Adjust strategy based on market regime

## 🔍 Troubleshooting

### Common Issues
- **No Signals Generated**: Check eligibility criteria and market conditions
- **Low Premiums**: Consider adjusting delta ranges or expiration dates
- **Assignment Risk**: Monitor positions closely near expiration
- **Cash Constraints**: Ensure adequate cash for cash-secured puts

### Debug Information
```python
# Get strategy information
strategy_info = strategy.get_strategy_info()
print(f"Active Wheels: {strategy_info['active_wheels']}")
print(f"Total Income: ${strategy_info['total_income']:.2f}")
print(f"Phase Distribution: {strategy_info['phase_distribution']}")
```

## 📚 Related Documentation

- [Available Strategies](AVAILABLE_STRATEGIES.md) - Complete list of trading strategies
- [Options Strategies Guide](OPTIONS_STRATEGIES_GUIDE.md) - Comprehensive options strategies
- [Strategy Automation Config](strategy_automation_config.yaml) - Configuration file
- [Backtesting Guide](AUTOMATED_BACKTEST_GUIDE.md) - Backtesting system usage

## 🎯 Conclusion

The Options Wheel Strategy provides a systematic approach to options income generation that combines the benefits of cash-secured put selling and covered call writing. With proper configuration and risk management, it can be an effective tool for generating consistent income while potentially acquiring quality stocks at discounted prices.

The strategy integrates seamlessly with your existing trading system and provides comprehensive tracking and management capabilities for successful implementation.


