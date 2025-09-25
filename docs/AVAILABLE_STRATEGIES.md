# Available Trading Strategies

This document lists all the trading strategies available in the backtesting system, organized by category.

## 📊 Basic Strategies

### Technical Analysis
- **BollingerBands** - Mean reversion strategy using Bollinger Bands
- **RSI** - Relative Strength Index strategy
- **MACD** - Moving Average Convergence Divergence strategy
- **SMACrossover** - Simple Moving Average Crossover strategy
- **Ichimoku** - Ichimoku Cloud strategy
- **IchimokuEnhanced** - Enhanced Ichimoku with AI confirmation
- **VWAP** - Volume Weighted Average Price strategy

### Momentum & Trend
- **Momentum** - Momentum-based strategy
- **AdaptiveMomentum** - Dynamically adjusts parameters based on market conditions
- **CrossSectionalMomentum** - Cross-sectional momentum strategy
- **MeanReversion** - Mean reversion strategy
- **VolatilityBreakout** - Volatility breakout strategy

### Advanced Analytics
- **RegimeSwitching** - Identifies market regimes and switches approaches
- **PairsTrading** - Statistical arbitrage using pairs
- **KalmanFilter** - Kalman filter-based strategy
- **MLEnsemble** - Machine learning ensemble strategy
- **EnhancedDayTrading** - Enhanced day trading strategy

### News & Sentiment
- **NewsEnhanced** - News-enhanced strategy with LLM analysis
- **SocialMediaSentiment** - Social media sentiment analysis

## 🎯 Options Strategies

### Income Strategies
- **CashSecuredPut** - Cash secured put strategy
- **CoveredCall** - Covered call strategy
- **IronCondor** - Iron condor strategy
- **EnhancedIronCondor** - Enhanced iron condor with cache integration

### Spread Strategies
- **CalendarSpread** - Calendar spread strategy
- **ButterflySpread** - Butterfly spread strategy
- **BullishDiagonal** - Bullish diagonal spread
- **BearishDiagonal** - Bearish diagonal spread

### Volatility Strategies
- **GreeksEnhanced** - Greeks-based options strategy
- **VolatilityStrategy** - Volatility-based strategy
- **Straddle** - Straddle strategy
- **LongStrangle** - Long strangle strategy

### Income Strategies
- **OptionsWheel** - Comprehensive options wheel strategy combining cash-secured puts and covered calls
- **ShortStrangle** - Short strangle strategy

### Event-Driven
- **EarningsStrategy** - Earnings-based options strategy

## 🚀 Advanced Strategies

### Risk Management
- **TrailingStop** - Trailing stop strategy
- **EnhancedExit** - Enhanced exit strategy
- **AdvancedExit** - Advanced exit strategy

### AI & ML
- **NeuralNetwork** - Neural network-based strategy
- **QuantumMomentum** - Quantum-inspired momentum strategy

### Portfolio Management
- **PortfolioStrategy** - Multi-strategy portfolio approach
- **Fibonacci** - Fibonacci retracement strategy

## Strategy Selection Guide

### Quick Test (Conservative)
- BollingerBands, RSI, MACD
- Good for: Basic testing, conservative approach

### Comprehensive (Moderate)
- BollingerBands, RSI, MACD, Momentum, MeanReversion, SMACrossover, VolatilityBreakout, Ichimoku, AdaptiveMomentum, VWAP, PairsTrading
- Good for: Thorough analysis, balanced approach

### Options Strategies (Aggressive)
- GreeksEnhanced, IronCondor, EnhancedIronCondor, CashSecuredPut, CoveredCall, CalendarSpread, ButterflySpread, VolatilityStrategy, EarningsStrategy
- Good for: Options trading, income generation

### Advanced AI (Extreme)
- BollingerBands, RSI, MACD, Momentum, MeanReversion, VolatilityBreakout, TrailingStop, Fibonacci, NeuralNetwork, QuantumMomentum, RegimeSwitching, KalmanFilter, MLEnsemble, EnhancedDayTrading
- Good for: Advanced analysis, AI-enhanced strategies

## Strategy Categories in Web Form

The backtest request form (http://localhost:11031/) now includes:

### 📊 Basic Strategies (18 strategies)
- Technical analysis, momentum, trend following, and news-enhanced strategies

### 🎯 Options Strategies (14 strategies)
- Income generation, spreads, volatility, and event-driven options strategies

### 🚀 Advanced Strategies (8 strategies)
- AI/ML, risk management, and portfolio strategies

## Total Available Strategies: 40

The system now supports **40 different trading strategies** across all categories, making it one of the most comprehensive backtesting platforms available.

## Usage

1. **Web Interface**: Visit http://localhost:11031/ to use the interactive form
2. **Quick Selection**: Use the category buttons (Basic, Options, Advanced) to select all strategies in a category
3. **Individual Selection**: Check/uncheck individual strategies as needed
4. **Presets**: Use the preset buttons for common configurations

## Notes

- All strategies are fully integrated with the backtesting engine
- Options strategies require options data and may need specific symbols (ETFs recommended)
- Advanced strategies may require additional computational resources
- LLM-enhanced strategies require the LLM proxy to be running 