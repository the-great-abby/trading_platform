# 📊 Advanced Portfolio Management System - Demo Scripts

This directory contains comprehensive demo scripts showcasing the Advanced Portfolio Management System capabilities.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the portfolio services (in separate terminals)
kubectl port-forward -n trading-system service/enhanced-portfolio-service 11180:80 &
kubectl port-forward -n trading-system service/enhanced-risk-management-service 11181:80 &

# Run a demo
python portfolio_optimization_demo.py
```

## 📋 Available Demos

### **Core Optimization Demos**
- **`portfolio_optimization_demo.py`** - Modern Portfolio Theory (MPT) optimization with efficient frontier
- **`black_litterman_demo.py`** - Black-Litterman model with market views and confidence levels
- **`risk_parity_demo.py`** - Risk Parity optimization with equal risk contribution

### **Advanced Features Demos**
- **`tax_optimization_demo.py`** - Tax-loss harvesting and tax-aware rebalancing
- **`rebalancing_strategies_demo.py`** - Intelligent rebalancing with drift and volatility triggers

### **Risk Management Demos**
- **`risk_assessment_demo.py`** - VaR, CVaR, stress testing, and factor analysis
- **`stress_testing_demo.py`** - Comprehensive stress testing scenarios

### **Backtesting Demos**
- **`portfolio_backtesting_demo.py`** - Complete portfolio backtesting with performance metrics
- **`strategy_comparison_demo.py`** - Compare different optimization strategies

### **Integration Demos**
- **`complete_system_demo.py`** - End-to-end workflow demonstration
- **`real_time_monitoring_demo.py`** - Real-time portfolio monitoring and alerts

## 🎯 Demo Features

### **Portfolio Optimization**
- Modern Portfolio Theory (MPT)
- Black-Litterman Model
- Risk Parity Optimization
- Efficient Frontier Generation
- Constraint Handling

### **Risk Management**
- Value at Risk (VaR) Calculation
- Conditional Value at Risk (CVaR)
- Stress Testing Scenarios
- Factor Analysis
- Correlation Analysis

### **Tax Optimization**
- Tax-Loss Harvesting
- Wash Sale Compliance
- Tax-Aware Rebalancing
- Tax Lot Management

### **Backtesting**
- Historical Performance Analysis
- Strategy Comparison
- Risk-Adjusted Metrics
- Walk-Forward Analysis

### **Real-Time Features**
- Live Portfolio Monitoring
- Risk Alerts
- Performance Tracking
- Rebalancing Recommendations

## 📊 Sample Data

The demos use realistic sample data including:
- **Asset Universe**: 50+ major stocks and ETFs
- **Historical Data**: 5+ years of daily price data
- **Market Views**: Expert opinions and analyst forecasts
- **Risk Scenarios**: Market crashes, interest rate shocks, sector rotations

## 🔧 Configuration

Each demo can be configured via:
- **Command Line Arguments**: Customize parameters
- **Configuration Files**: Persistent settings
- **Environment Variables**: System-wide defaults

## 📈 Output

Demos generate:
- **Console Output**: Real-time progress and results
- **JSON Reports**: Detailed analysis results
- **CSV Files**: Data exports for further analysis
- **Visualizations**: Charts and graphs (when matplotlib is available)

## 🚨 Prerequisites

1. **Portfolio Services Running**: Enhanced Portfolio Service (port 11180) and Risk Management Service (port 11181)
2. **Python Dependencies**: See `requirements.txt`
3. **Market Data**: Yahoo Finance API access (free)
4. **Database**: PostgreSQL/TimescaleDB with portfolio schema

## 📚 Learning Path

1. **Start with**: `portfolio_optimization_demo.py` - Basic MPT optimization
2. **Explore**: `black_litterman_demo.py` - Advanced optimization with views
3. **Understand Risk**: `risk_assessment_demo.py` - Comprehensive risk analysis
4. **See Tax Benefits**: `tax_optimization_demo.py` - Tax optimization strategies
5. **Full Workflow**: `complete_system_demo.py` - End-to-end demonstration

## 🎓 Educational Value

These demos are designed to:
- **Learn Portfolio Theory**: Understand MPT, Black-Litterman, Risk Parity
- **Practice Risk Management**: VaR, stress testing, factor analysis
- **Explore Tax Optimization**: Tax-loss harvesting, wash sale rules
- **Understand Backtesting**: Historical performance analysis
- **See Real Applications**: Practical portfolio management workflows

## 🔍 Troubleshooting

### **Common Issues**
- **Service Not Running**: Ensure portfolio services are deployed and port-forwarded
- **Market Data Errors**: Check internet connection and Yahoo Finance access
- **Database Errors**: Verify database connection and schema
- **Memory Issues**: Reduce asset universe size for large-scale demos

### **Debug Mode**
```bash
# Run with debug logging
python portfolio_optimization_demo.py --debug --verbose

# Run with specific configuration
python portfolio_optimization_demo.py --config custom_config.json
```

## 📞 Support

For questions or issues:
- **Documentation**: See `specs/002-advanced-portfolio-management/`
- **Integration Tests**: See `scripts/test-portfolio-system-integration.py`
- **Health Checks**: See `scripts/check-portfolio-services-health.sh`

---

**Happy Portfolio Optimizing!** 🚀📊



