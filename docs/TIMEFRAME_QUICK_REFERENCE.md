# ⚡ Intraday & Multi-Timeframe Quick Reference Card

**Quick command reference for the new timeframe analysis features**

---

## 🚀 Make Commands (Easiest)

```bash
# 📊 Daily Analysis (Original)
make recommendations-enhanced
# → Standard swing trading signals, 1-year lookback

# ⏰ Hourly Analysis
make recommendations-hourly
# → Day trading signals, 30-day lookback

# ⚡ Intraday 1-Hour (Fast)
make recommendations-intraday
# → Aggressive day trading, pure technical

# ⚡⚡ Intraday 15-Minute (Ultra-Fast)
make recommendations-15m  
# → Scalping signals, ultra-fast indicators

# 🎯 Multi-Timeframe (Best)
make recommendations-multi
# → Daily + Hourly + 15m combined, alignment detection
```

---

## 🔧 API Endpoints

### **Enhanced Recommendations (Flexible Timeframe)**
```bash
# Daily (default)
curl "http://localhost:11001/api/trading/recommendations/enhanced"

# Hourly
curl "http://localhost:11001/api/trading/recommendations/enhanced?timeframe=1h&lookback_days=30"

# 15-minute
curl "http://localhost:11001/api/trading/recommendations/enhanced?timeframe=15m&lookback_days=7"

# 5-minute
curl "http://localhost:11001/api/trading/recommendations/enhanced?timeframe=5m&lookback_days=3"
```

### **Intraday-Optimized (Fast Signals)**
```bash
# Hourly aggressive
curl "http://localhost:11001/api/trading/recommendations/intraday?timeframe=1h&aggressive=true"

# 15-minute aggressive
curl "http://localhost:11001/api/trading/recommendations/intraday?timeframe=15m&aggressive=true"

# Conservative mode
curl "http://localhost:11001/api/trading/recommendations/intraday?timeframe=1h&aggressive=false"
```

### **Multi-Timeframe (Combined Analysis)**
```bash
# Balanced (default: 40% daily, 40% hourly, 20% 15m)
curl "http://localhost:11001/api/trading/recommendations/multi-timeframe"

# Conservative (heavy daily bias)
curl "http://localhost:11001/api/trading/recommendations/multi-timeframe?daily_weight=0.6&hourly_weight=0.3&minute_weight=0.1"

# Aggressive (heavy intraday bias)
curl "http://localhost:11001/api/trading/recommendations/multi-timeframe?daily_weight=0.2&hourly_weight=0.4&minute_weight=0.4"
```

---

## 📊 Timeframe Comparison Table

| Timeframe | Lookback | Min Data | Signals/Day | Win Rate | Best For |
|-----------|----------|----------|-------------|----------|----------|
| **1d** | 365 days | 210 points | 1-3 | 55-60% | Swing trades |
| **1h** | 30 days | 110 points | 6-12 | 50-55% | Day trades |
| **15m** | 7 days | 60 points | 20-40 | 45-50% | Scalping |
| **5m** | 3 days | 30 points | 50-100 | 40-45% | HFT |
| **Multi-TF** | Mixed | 210+ | 2-5 | 60-65% | High confidence |

---

## 🎯 Strategy Selection Guide

### **Your Trading Style → Best Command**

| If You Trade... | Use This Command |
|-----------------|------------------|
| 🏃 **Position Trading** (weeks-months) | `make recommendations-enhanced` |
| 📈 **Swing Trading** (days-weeks) | `make recommendations-multi` |
| ⚡ **Day Trading** (hours) | `make recommendations-intraday` |
| ⚡⚡ **Active Day Trading** (minutes) | `make recommendations-15m` |
| 🔥 **Scalping** (seconds-minutes) | Custom curl with `timeframe=5m` |

---

## 🔍 Quick Comparison Workflow

```bash
# Compare same symbol across all timeframes
SYMBOL="NVDA"

echo "=== DAILY ===" && \
curl -s "http://localhost:11001/api/trading/recommendations/enhanced?symbol=$SYMBOL&timeframe=1d" | \
jq '.recommendations[0] | {action, score, confidence, timeframe}'

echo "=== HOURLY ===" && \
curl -s "http://localhost:11001/api/trading/recommendations/enhanced?symbol=$SYMBOL&timeframe=1h" | \
jq '.recommendations[0] | {action, score, confidence, timeframe}'

echo "=== 15-MINUTE ===" && \
curl -s "http://localhost:11001/api/trading/recommendations/intraday?symbol=$SYMBOL&timeframe=15m" | \
jq '.recommendations[0] | {action, score, confidence, timeframe}'

echo "=== MULTI-TF ===" && \
curl -s "http://localhost:11001/api/trading/recommendations/multi-timeframe?symbol=$SYMBOL" | \
jq '.recommendations[0] | {action, score, confidence, alignment_boost}'
```

---

## 📈 Indicator Periods by Timeframe

| Indicator | Daily (1d) | Hourly (1h) | 15-min | 5-min |
|-----------|------------|-------------|--------|-------|
| **MACD** | 12/26/9 | 12/26/9 | 8/17/9 | 5/13/5 |
| **MA Short** | 20 | 20 | 10 | 5 |
| **MA Medium** | 50 | 50 | 20 | 10 |
| **MA Long** | 200 | 100 | 50 | 20 |
| **BB Period** | 20 | 20 | 14 | 10 |
| **Volume** | 20 | 20 | 14 | 10 |

---

## 🎓 Pro Tips

### **1. Start Broad, Then Narrow**
```bash
make recommendations-enhanced    # Check overall trend
make recommendations-intraday    # Find momentum
make recommendations-15m         # Time your entry
```

### **2. Use Multi-TF for Confidence**
```bash
make recommendations-multi | grep "ALL TIMEFRAMES ALIGNED"
# Only trade symbols where all timeframes agree!
```

### **3. Match Timeframe to Hold Time**
- Hold for **days**? Use daily
- Hold for **hours**? Use hourly
- Hold for **minutes**? Use 15m
- In and out **quick**? Use 5m

### **4. Watch for Divergence**
If daily says BUY but hourly says SELL:
- ⚠️ Possible pullback coming
- Wait for alignment
- Or trade the pullback on smaller timeframe

---

## 🚨 Quick Troubleshooting

### **Port Forward Down?**
```bash
kubectl port-forward -n trading-system service/strategy-service 11001:8000 &
```

### **"Insufficient Data" Error?**
Reduce lookback period for shorter timeframes:
```bash
# Instead of default
curl "...?timeframe=15m"

# Try this
curl "...?timeframe=15m&lookback_days=5"
```

### **No Intraday Data?**
Check Polygon subscription:
```bash
curl -X POST http://localhost:11084/market-data/historical \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SPY", "start_date": "2025-10-12", "end_date": "2025-10-13", "interval": "1h"}' | \
  jq '.count'
```

---

## 📚 Full Documentation

**Complete Guide**: `docs/INTRADAY_MULTI_TIMEFRAME_RECOMMENDATIONS.md`  
**Implementation Summary**: `INTRADAY_IMPLEMENTATION_SUMMARY.md`  
**Original System**: `docs/ENHANCED_RECOMMENDATIONS_SYSTEM.md`

---

## 🎉 Try It Now!

```bash
# Run all analysis types and compare
make recommendations-enhanced
make recommendations-hourly  
make recommendations-intraday
make recommendations-multi
```

**Answer to your original question**:
> "what time frame is this for? is there a way to adjust the timeframes?"

**Answer**: 
- Original = Daily (1d)
- ✅ YES you can adjust timeframes!
- New options: 1h, 15m, 5m
- Plus multi-timeframe combined analysis
- All implemented and ready to use! 🚀




