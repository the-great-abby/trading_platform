# Makefile Live Trading Guide

## Quick Reference

All automated trading management commands use the **`Makefile.live-trading`** file.

```bash
# View all available commands
make -f makefiles/Makefile.live-trading help
```

---

## 🚀 Quick Start

### Deploy Automated Trading (Paper Mode)
```bash
make -f makefiles/Makefile.live-trading deploy-auto-trading
```

### Check Status
```bash
make -f makefiles/Makefile.live-trading status-auto-trading
```

### Watch Logs in Real-Time
```bash
make -f makefiles/Makefile.live-trading logs-auto-trading-live
```

---

## 🚨 Emergency Controls

### Stop Trading IMMEDIATELY
```bash
make -f makefiles/Makefile.live-trading emergency-stop
```
**What it does:**
- Sets emergency stop flag in ConfigMap
- Disables trading via environment variable
- Next execution will be skipped
- All future executions blocked until resumed

### Resume Trading
```bash
make -f makefiles/Makefile.live-trading emergency-resume
```
**What it does:**
- Clears emergency stop flag
- Re-enables trading
- Next scheduled execution will proceed

### Nuclear Option (Complete Removal)
```bash
make -f makefiles/Makefile.live-trading kill-auto-trading
```
**What it does:**
- Asks for confirmation ("yes")
- Deletes CronJob completely
- Removes ConfigMaps
- Stops all future executions

---

## ⚙️ Configuration Commands

### Trading Mode

**Switch to Paper Trading (Safe)**
```bash
make -f makefiles/Makefile.live-trading set-paper-mode
```

**Switch to Live Trading (⚠️ REAL MONEY)**
```bash
make -f makefiles/Makefile.live-trading set-live-mode
# Asks for confirmation: Type "LIVE"
```

### Execution Intervals

**Every 15 Minutes (Default)**
```bash
make -f makefiles/Makefile.live-trading set-interval-15
```

**Every 30 Minutes**
```bash
make -f makefiles/Makefile.live-trading set-interval-30
```

**Every Hour**
```bash
make -f makefiles/Makefile.live-trading set-interval-60
```

### Risk Limits

**Conservative (Safest)**
```bash
make -f makefiles/Makefile.live-trading set-risk-conservative
```
- Max Daily Loss: $250
- Max Position Size: 10%
- Max Positions: 3
- Max Portfolio Heat: 20%

**Moderate (Balanced)**
```bash
make -f makefiles/Makefile.live-trading set-risk-moderate
```
- Max Daily Loss: $500
- Max Position Size: 20%
- Max Positions: 5
- Max Portfolio Heat: 30%

**Aggressive (Riskier)**
```bash
make -f makefiles/Makefile.live-trading set-risk-aggressive
```
- Max Daily Loss: $1000
- Max Position Size: 30%
- Max Positions: 8
- Max Portfolio Heat: 50%

**Show Current Limits**
```bash
make -f makefiles/Makefile.live-trading show-risk-limits
```

---

## 📊 Monitoring Commands

### Status Check
```bash
make -f makefiles/Makefile.live-trading status-auto-trading
```
Shows:
- CronJob status
- Recent job executions
- Active pods
- Emergency stop status

### View Recent Logs
```bash
make -f makefiles/Makefile.live-trading logs-auto-trading
```
Shows last 100 lines from most recent execution

### Follow Logs in Real-Time
```bash
make -f makefiles/Makefile.live-trading logs-auto-trading-live
```
Continuously streams logs (Ctrl+C to stop)

### Execution History
```bash
make -f makefiles/Makefile.live-trading jobs-auto-trading
```
Shows:
- All execution jobs
- Total jobs
- Completed count
- Failed count

---

## 🧪 Testing Commands

### Manual Execution (Test)
```bash
make -f makefiles/Makefile.live-trading test-execution
```
Manually triggers one trading cycle immediately (doesn't wait for schedule)

### Check Market Hours
```bash
make -f makefiles/Makefile.live-trading test-market-hours
```
Shows:
- Current ET time
- Day of week
- Whether market is open/closed

---

## 🔧 Maintenance Commands

### Clean Old Jobs
```bash
make -f makefiles/Makefile.live-trading clean-old-jobs
```
Removes old completed jobs (keeps last 10)

### Backup Configuration
```bash
make -f makefiles/Makefile.live-trading backup-config
```
Saves current configuration to `backups/` directory

### Restore Configuration
```bash
make -f makefiles/Makefile.live-trading restore-config
```
Restores configuration from backup (asks which backup to use)

### Redeploy
```bash
make -f makefiles/Makefile.live-trading redeploy-auto-trading
```
Removes and re-deploys CronJob (useful after YAML changes)

---

## 📋 Common Workflows

### Initial Setup
```bash
# 1. Deploy in paper mode
make -f makefiles/Makefile.live-trading deploy-auto-trading

# 2. Set conservative risk limits
make -f makefiles/Makefile.live-trading set-risk-conservative

# 3. Check status
make -f makefiles/Makefile.live-trading status-auto-trading

# 4. Watch logs
make -f makefiles/Makefile.live-trading logs-auto-trading-live
```

### Daily Monitoring
```bash
# Quick status check
make -f makefiles/Makefile.live-trading quick-status

# View recent activity
make -f makefiles/Makefile.live-trading logs-auto-trading

# Check execution history
make -f makefiles/Makefile.live-trading jobs-auto-trading
```

### Emergency Response
```bash
# Something wrong? Stop immediately
make -f makefiles/Makefile.live-trading emergency-stop

# Check what happened
make -f makefiles/Makefile.live-trading logs-auto-trading

# When ready to resume
make -f makefiles/Makefile.live-trading emergency-resume
```

### Before Going Live (from Paper)
```bash
# 1. Backup current config
make -f makefiles/Makefile.live-trading backup-config

# 2. Review risk limits
make -f makefiles/Makefile.live-trading show-risk-limits

# 3. Switch to live mode (requires confirmation)
make -f makefiles/Makefile.live-trading set-live-mode

# 4. Monitor VERY closely
make -f makefiles/Makefile.live-trading logs-auto-trading-live
```

### Configuration Changes
```bash
# Backup before changes
make -f makefiles/Makefile.live-trading backup-config

# Make changes (example: increase interval)
make -f makefiles/Makefile.live-trading set-interval-30

# Verify changes
make -f makefiles/Makefile.live-trading status-auto-trading

# If something wrong, restore backup
make -f makefiles/Makefile.live-trading restore-config
```

---

## 🎯 Quick Actions (Aliases)

For faster typing, these aliases are available:

```bash
# Status
make -f makefiles/Makefile.live-trading quick-status

# Emergency stop
make -f makefiles/Makefile.live-trading quick-stop

# Resume
make -f makefiles/Makefile.live-trading quick-resume

# Logs
make -f makefiles/Makefile.live-trading quick-logs
```

---

## 💡 Tips

1. **Always backup before changes**
   ```bash
   make -f makefiles/Makefile.live-trading backup-config
   ```

2. **Monitor after every change**
   ```bash
   make -f makefiles/Makefile.live-trading logs-auto-trading-live
   ```

3. **Start conservative, scale up slowly**
   ```bash
   make -f makefiles/Makefile.live-trading set-risk-conservative
   ```

4. **Test manually before waiting for schedule**
   ```bash
   make -f makefiles/Makefile.live-trading test-execution
   ```

5. **Check market hours to understand timing**
   ```bash
   make -f makefiles/Makefile.live-trading test-market-hours
   ```

---

## ⚠️ Safety Reminders

- ✅ Always deploy in **paper mode** first
- ✅ Test for at least **1 week** before going live
- ✅ Set **conservative risk limits** initially
- ✅ **Monitor logs** daily
- ✅ **Backup config** before changes
- ✅ Know how to **emergency stop**
- ✅ Review **execution history** regularly

---

## 📞 Support

If something goes wrong:

1. **Emergency stop first**
   ```bash
   make -f makefiles/Makefile.live-trading emergency-stop
   ```

2. **Check logs**
   ```bash
   make -f makefiles/Makefile.live-trading logs-auto-trading
   ```

3. **Check status**
   ```bash
   make -f makefiles/Makefile.live-trading status-auto-trading
   ```

4. **Review execution history**
   ```bash
   make -f makefiles/Makefile.live-trading jobs-auto-trading
   ```

5. **Restore from backup if needed**
   ```bash
   make -f makefiles/Makefile.live-trading restore-config
   ```

