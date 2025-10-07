# Authentication Troubleshooting Guide

This guide helps you resolve authentication issues with the live trading service.

## 🔍 Common Authentication Errors

### 1. "No accounts found" or Empty accounts list
**Symptoms:**
- `curl -s http://localhost:11120/api/v1/accounts` returns `{"accounts":[],"total_count":0}`
- Strategy setup fails with "Account not found"

**Solution:**
You need to connect to Public.com first:
```bash
python scripts/connect_public_com.py
```

### 2. "Invalid access token" or 401 Unauthorized
**Symptoms:**
- Error: "Invalid access token"
- HTTP 401 responses from Public.com API

**Solution:**
1. Get a new access token from Public.com:
   - Go to https://public.com/settings/api
   - Generate a new personal access token
   - Copy the token (it starts with something like `pk_` or `sk_`)

2. Connect with the new token:
```bash
python scripts/connect_public_com.py
```

### 3. "Account not authenticated" or "Account must be connected"
**Symptoms:**
- Error: "Account not found or not authenticated"
- Trading orders fail with authentication errors

**Solution:**
1. Check if account is connected:
```bash
curl -s http://localhost:11120/api/v1/accounts | jq
```

2. If no accounts, connect to Public.com:
```bash
python scripts/connect_public_com.py
```

3. If accounts exist but still getting errors, try reconnecting:
```bash
# Delete existing connection (if needed)
# Then reconnect
python scripts/connect_public_com.py
```

### 4. "Token expired" or "Refresh token failed"
**Symptoms:**
- Error: "Token expired"
- Error: "Failed to refresh access token"

**Solution:**
1. Get a new access token from Public.com
2. Reconnect with the new token:
```bash
python scripts/connect_public_com.py
```

## 🔧 Step-by-Step Authentication Setup

### Step 1: Get Public.com Access Token

1. **Log into Public.com**: Go to https://public.com
2. **Navigate to API Settings**: Go to Settings → API
3. **Generate Token**: Click "Generate New Token"
4. **Copy Token**: Save the token (starts with `pk_` or `sk_`)
5. **Set Permissions**: Ensure the token has trading permissions

### Step 2: Connect to Live Trading Service

```bash
# Run the connection script
python scripts/connect_public_com.py

# Or set environment variable and use setup script
export PUBLIC_API_KEY='your-token-here'
python scripts/setup_live_trading_strategies.py
```

### Step 3: Verify Connection

```bash
# Check if account is connected
curl -s http://localhost:11120/api/v1/accounts | jq

# Check account balance
curl -s http://localhost:11120/api/v1/accounts/{account_id}/balance | jq
```

## 🚨 Troubleshooting Commands

### Check Service Health
```bash
curl -s http://localhost:11120/health | jq
```

### Check Account Status
```bash
curl -s http://localhost:11120/api/v1/accounts | jq
```

### Test Authentication
```bash
# Test with a simple API call
curl -s http://localhost:11120/api/v1/status | jq
```

### Check Service Logs
```bash
kubectl logs -f deployment/live-trading-service
```

## 🔐 Token Management

### Environment Variable Method
```bash
# Set token in current session
export PUBLIC_API_KEY='your-token-here'

# Set token permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export PUBLIC_API_KEY="your-token-here"' >> ~/.bashrc
source ~/.bashrc
```

### Interactive Method
```bash
# Use the connection script (recommended)
python scripts/connect_public_com.py
```

## 📋 Common Token Issues

### 1. Token Format
- ✅ Correct: `pk_1234567890abcdef`
- ❌ Wrong: `1234567890abcdef` (missing prefix)
- ❌ Wrong: `"pk_1234567890abcdef"` (with quotes)

### 2. Token Permissions
Ensure your token has:
- ✅ Trading permissions
- ✅ Account read permissions
- ✅ Order management permissions

### 3. Token Expiration
- Personal access tokens don't expire
- If you get "expired" errors, the token might be invalid
- Generate a new token if needed

## 🆘 Still Having Issues?

### 1. Check Service Status
```bash
# Verify service is running
kubectl get pods -l app=live-trading-service

# Check service logs
kubectl logs deployment/live-trading-service --tail=50
```

### 2. Verify Port Forwarding
```bash
# Check if port forward is active
ps aux | grep "kubectl port-forward.*11120"

# Restart port forward if needed
kubectl port-forward service/live-trading-service 11120:8080 &
```

### 3. Test API Connectivity
```bash
# Test basic connectivity
curl -v http://localhost:11120/health

# Test with timeout
curl --connect-timeout 10 http://localhost:11120/health
```

### 4. Check Database Connection
```bash
# Check if database is accessible
curl -s http://localhost:11120/api/v1/status | jq '.components.database'
```

## 📞 Getting Help

If you're still having issues:

1. **Check the logs**: `kubectl logs deployment/live-trading-service`
2. **Verify service health**: `curl -s http://localhost:11120/health`
3. **Test connectivity**: `python scripts/test_live_trading_setup.py`
4. **Review this guide**: Check all steps above

## 🔄 Reset Authentication

If you need to start fresh:

```bash
# 1. Check current accounts
curl -s http://localhost:11120/api/v1/accounts

# 2. Connect with new token
python scripts/connect_public_com.py

# 3. Verify connection
curl -s http://localhost:11120/api/v1/accounts | jq
```

---

**💡 Tip**: Always test your connection with `python scripts/connect_public_com.py` before trying to set up strategies. This will catch authentication issues early.





















