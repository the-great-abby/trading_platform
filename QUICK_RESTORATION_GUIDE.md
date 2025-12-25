# ⚡ Quick Restoration Guide

**TL;DR**: Your system has 2 broken services. Here's how to fix them in 2 minutes.

---

## 🚨 Current Issues

| Service | Status | Problem |
|---------|--------|---------|
| market-data-service | ❌ CrashLoopBackOff | Hardcoded IP address |
| rss-feed-service | ❌ Pending | Wrong RabbitMQ address |

---

## ✅ Quick Fix (2 minutes)

```bash
cd /Users/abby/code/trading
./scripts/fix_service_connections.sh
```

**What it does**:
1. ✅ Fixes market-data-service database URL
2. ✅ Fixes rss-feed-service RabbitMQ URL
3. ✅ Restarts pods automatically
4. ✅ Verifies they're running

**Time**: 2-3 minutes

---

## 🧙 New Wizard Features

Your wizard can now manage **8 repositories**!

```bash
make wizard
```

**New category**: Infrastructure Restoration
- ollama_controller (13 commands)
- database (7 commands)
- rabbitmq (5 commands)
- redis (5 commands)
- grafana, registry, system_mcp

**Total**: 36 cross-repository commands!

---

## 📖 Full Documentation

| Guide | When to Use |
|-------|-------------|
| QUICK_RESTORATION_GUIDE.md | Right now! (this file) |
| SERVICE_RESTORATION_GUIDE.md | Detailed wizard walkthrough |
| MULTI_REPO_WIZARD_GUIDE.md | Learn multi-repo wizard |
| SYSTEM_RESTORATION_COMPLETE.md | Complete summary |

---

## 🎯 Quick Commands

```bash
# Fix services NOW
./scripts/fix_service_connections.sh

# Launch wizard
make wizard

# Check status
kubectl get pods -n trading-system

# View external repos
python3 scripts/wizard_config.py
```

---

## 🚀 What's New

✨ **Multi-Repo Wizard** - Manage 8 repos from one interface  
✨ **Automated Fixes** - One script restores everything  
✨ **Infrastructure Restoration** - New wizard category with 36 commands  
✨ **1,700+ lines** of documentation  

---

**Just run**: `./scripts/fix_service_connections.sh` 🎉








