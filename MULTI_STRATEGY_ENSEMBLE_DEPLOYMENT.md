
# Multi-Strategy Ensemble Deployment Instructions
# ===============================================

## 🚀 Paper Trading Deployment

1. **Start Paper Trading with Multi-Strategy Ensemble:**
   ```bash
   cd /Users/abby/code/trading
   python scripts/setup_paper_trading.py config/multi_strategy_ensemble_paper_trading.yaml
   ```

2. **Monitor Paper Trading Performance:**
   ```bash
   # Check paper trading status
   kubectl logs -f deployment/paper-trading-engine -n trading-system
   
   # View dashboard
   kubectl port-forward svc/unified-trading-dashboard 11115:80 -n trading-system
   # Open: http://localhost:11115
   ```

## 🎯 Live Trading Deployment

1. **Deploy Live Trading Configuration:**
   ```bash
   # Apply live trading configuration
   kubectl apply -f config/multi_strategy_ensemble_live_trading.yaml -n trading-system
   
   # Restart live trading services
   kubectl rollout restart deployment/trading-engine -n trading-system
   kubectl rollout restart deployment/strategy-service -n trading-system
   ```

2. **Monitor Live Trading:**
   ```bash
   # Check live trading status
   kubectl logs -f deployment/trading-engine -n trading-system
   
   # Monitor performance
   kubectl logs -f deployment/strategy-service -n trading-system
   ```

## 📊 Expected Performance Targets

### Paper Trading (Aggressive):
- **Target Return**: 300%+ annually
- **Max Drawdown**: <10%
- **Win Rate**: >80%
- **Sharpe Ratio**: >2.0

### Live Trading (Conservative):
- **Target Return**: 100%+ annually
- **Max Drawdown**: <5%
- **Win Rate**: >70%
- **Sharpe Ratio**: >1.5

## 🔧 Configuration Adjustments

### For More Aggressive Trading:
- Increase `max_position_size` to 0.30
- Decrease `min_cash_reserve` to 0.05
- Increase `max_daily_trades` to 10

### For More Conservative Trading:
- Decrease `max_position_size` to 0.15
- Increase `min_cash_reserve` to 0.30
- Decrease `max_daily_trades` to 3

## 🚨 Risk Management

- Monitor daily P&L closely
- Set up alerts for drawdowns >5%
- Review performance weekly
- Adjust position sizes based on performance

## 📈 Performance Monitoring

- Check dashboard daily: http://localhost:11115
- Review trade logs weekly
- Analyze strategy performance monthly
- Adjust configuration quarterly
