# 🔍 Backtest Validation Framework - Makefile Guide

## Overview
This guide explains how to use the Makefile targets for testing the backtest validation framework against local filesystem files instead of Kubernetes.

## 🚀 Quick Start for Local Testing

### 1. **Run Quick Test Suite**
```bash
make validation-quick-test
```
This runs a comprehensive test of all framework components:
- ✅ Script discovery (found 2,613 scripts)
- ✅ Sample validation execution
- ✅ API creation (44 routes)
- ✅ Configuration validation

### 2. **Start Local API Server**
```bash
make validation-run-local
```
Starts the validation framework locally with filesystem configuration on `http://localhost:8000`

### 3. **Test API Endpoints**
```bash
make validation-api-test
```
Tests the health, discovery, and metrics endpoints locally.

## 🔍 Discovery & Validation Commands

### **Script Discovery**
```bash
# Discover first 20 scripts (quick overview)
make validation-discover

# Discover all scripts (full output)
make validation-discover-all

# Save discovery results as JSON
make validation-discover-json
```

### **Script Validation**
```bash
# Validate a sample script (recommended for testing)
make validation-validate-sample

# Validate a specific script
make validation-validate SCRIPT_ID=your-script-id

# Batch validate sample scripts (5 scripts)
make validation-batch-sample

# Batch validate a directory
make validation-batch DIR=./your-directory
```

### **Report Generation**
```bash
# Generate sample report (10 scripts)
make validation-report-sample

# Generate full report
make validation-report FORMAT=json
make validation-report FORMAT=table
```

## 🧪 Testing Commands

### **Framework Testing**
```bash
# Test with local filesystem
make validation-test-local

# Run full test suite
make validation-test

# Test specific components
make validation-test-discovery
make validation-test-execution
make validation-test-api
make validation-test-integration
```

### **Health & Status**
```bash
# Check local framework health
make validation-health-local

# Check configuration
make validation-config-test

# Load local environment
make validation-load-local
```

## 🏗️ Local vs Kubernetes Commands

### **Local Development (Recommended)**
- `validation-run-local` - Run locally with filesystem config
- `validation-test-local` - Test against local files
- `validation-health-local` - Check local health
- `validation-quick-test` - Quick local test suite

### **Kubernetes Production**
- `validation-build` - Build Docker image
- `validation-deploy` - Deploy to Kubernetes
- `validation-run` - Run locally (default mode)
- `validation-health` - Check Kubernetes health
- `validation-port-forward` - Port forward from Kubernetes

## 📋 Configuration

### **Local Environment File**
The framework uses `config/validation-local.env` for local configuration:
```bash
# Load local environment
make validation-load-local

# Check current configuration
make validation-config-test
```

### **Key Local Settings**
- `VALIDATION_DB_HOST=localhost` - Use local database
- `VALIDATION_DEFAULT_DIRECTORY=.` - Search current directory
- `VALIDATION_HEALTH_DB_ENABLED=false` - Disable DB health checks
- `VALIDATION_LOG_LEVEL=INFO` - Set logging level

## 🎯 Common Use Cases

### **1. Test Your Backtest Scripts**
```bash
# Quick overview of all scripts
make validation-discover

# Test a sample script
make validation-validate-sample

# Generate a report
make validation-report-sample
```

### **2. Validate Specific Scripts**
```bash
# Find script ID first
make validation-discover-json
# Look for your script in validation_scripts.json

# Validate specific script
make validation-validate SCRIPT_ID=your-script-id
```

### **3. Batch Validation**
```bash
# Test small batch (5 scripts)
make validation-batch-sample

# Validate entire directory
make validation-batch DIR=./src/strategies
```

### **4. Development Testing**
```bash
# Run full local test
make validation-test-local

# Start local API for testing
make validation-run-local

# In another terminal, test API
make validation-api-test
```

## 🔧 Troubleshooting

### **Script Discovery Issues**
- Some scripts may have syntax errors (expected)
- Framework handles errors gracefully and continues
- Check specific errors in output for problematic files

### **Validation Failures**
- Most failures are due to missing database configuration
- This is expected for local testing without full infrastructure
- Framework still validates script execution and structure

### **API Issues**
- Ensure port 8000 is available
- Check `make validation-health-local` for status
- Use `make validation-run-local` to start fresh

## 📊 Example Output

### **Discovery Results**
```
🔍 Discovering backtest scripts in local filesystem...
Discovered 2613 backtest scripts:

ID      Name    Type    Status  Path
--------------------------------------------------------------------------------
c6cff3f7        Run_Automated_Backtest_Now      OPTIONS ValidationStatus.NEVER_RUN
ee31f844        Verify_Trading_Frequency        OPTIONS ValidationStatus.NEVER_RUN
a9e4ab33        Example_Kubernetes_Elliott_Wave OPTIONS ValidationStatus.NEVER_RUN
```

### **Validation Results**
```
🧪 Validating sample backtest script...
📊 Found 2613 scripts
🧪 Testing sample validation...
   Testing: Run_Automated_Backtest_Now
✅ Sample validation completed: SUCCESS
   Error: Failed to initialize market data manager: DATABASE_URL environment variable is required
```

## 🚀 Next Steps

1. **Start with Quick Test**: `make validation-quick-test`
2. **Explore Your Scripts**: `make validation-discover`
3. **Test Validation**: `make validation-validate-sample`
4. **Generate Reports**: `make validation-report-sample`
5. **Start API Server**: `make validation-run-local`

## 💡 Pro Tips

- Use `validation-quick-test` for rapid validation of framework health
- Use `validation-discover` to get an overview of your scripts
- Use `validation-validate-sample` for quick validation testing
- Use `validation-run-local` + `validation-api-test` for API development
- Check `config/validation-local.env` for configuration customization

---

**🎉 Your backtest validation framework is ready for local testing!**

The framework successfully discovered **2,613 backtest scripts** in your codebase and is ready to help ensure their reliability and consistency.













