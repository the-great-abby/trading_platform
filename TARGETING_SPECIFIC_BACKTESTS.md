# 🎯 Targeting Specific Backtests - Complete Guide

## Overview
This guide shows you **multiple ways** to target and validate specific backtest scripts in your trading system. You have **2,613 backtest scripts** available for validation!

## 🚀 Quick Methods

### 1. **By Script Name (Easiest)**
```bash
# Find scripts containing "Strategy"
make validation-find-script NAME=Strategy

# Validate a specific script by name
make validation-validate-by-name NAME=Strategy_Allocation

# Using the advanced tool
python scripts/validate_specific_script.py --name Strategy_Allocation
```

### 2. **By File Path**
```bash
# Validate by file path
make validation-validate-by-path PATH=strategy_allocation_backtest.py

# Using the advanced tool
python scripts/validate_specific_script.py --path strategy_allocation
```

### 3. **By Script ID (Most Precise)**
```bash
# First, find the ID
make validation-find-script NAME=Strategy_Allocation

# Then validate using the ID
make validation-validate SCRIPT_ID=098c30af-6bd8-482b-a52a-98d8c8ca7574
```

## 🔍 Discovery Methods

### **Find Scripts by Pattern**
```bash
# Find all scripts containing "Strategy"
make validation-find-script NAME=Strategy

# Find all scripts containing "Options"
make validation-find-script NAME=Options

# Find all scripts containing "Backtest"
make validation-find-script NAME=Backtest
```

### **Advanced Search Tool**
```bash
# List all scripts matching a pattern
python scripts/validate_specific_script.py --list Strategy

# Search by partial name
python scripts/validate_specific_script.py --search options

# Search by file path
python scripts/validate_specific_script.py --search backtest.py
```

## 🧪 Validation Methods

### **Method 1: Makefile Targets**
```bash
# By name
make validation-validate-by-name NAME=Strategy_Allocation

# By path
make validation-validate-by-path PATH=strategy_allocation_backtest.py

# By ID
make validation-validate SCRIPT_ID=098c30af-6bd8-482b-a52a-98d8c8ca7574

# Advanced targeting
make validation-validate-specific NAME=Strategy_Allocation
make validation-validate-specific PATH=backtest
make validation-validate-specific SEARCH=options
```

### **Method 2: Python Script (Most Flexible)**
```bash
# Validate by exact name
python scripts/validate_specific_script.py --name Strategy_Allocation

# Validate by partial name
python scripts/validate_specific_script.py --name Strategy

# Validate by file path
python scripts/validate_specific_script.py --path strategy_allocation

# Validate by ID
python scripts/validate_specific_script.py --id 098c30af-6bd8-482b-a52a-98d8c8ca7574

# Search and validate
python scripts/validate_specific_script.py --search Strategy_Allocation
```

## 📋 Step-by-Step Examples

### **Example 1: Find and Validate a Strategy Script**
```bash
# Step 1: Find strategy scripts
make validation-find-script NAME=Strategy

# Step 2: Choose one (e.g., Strategy_Allocation)
# Step 3: Validate it
make validation-validate-by-name NAME=Strategy_Allocation
```

### **Example 2: Validate by File Path**
```bash
# Step 1: Look for backtest files
make validation-find-script NAME=backtest

# Step 2: Choose a file path
# Step 3: Validate by path
make validation-validate-by-path PATH=strategy_allocation_backtest.py
```

### **Example 3: Advanced Search and Validate**
```bash
# Step 1: Search for options scripts
python scripts/validate_specific_script.py --list Options

# Step 2: Choose a script from the list
# Step 3: Validate by ID
python scripts/validate_specific_script.py --id <script-id-from-step-1>
```

## 🎯 Common Use Cases

### **1. Validate a Specific Strategy**
```bash
# Find your strategy
make validation-find-script NAME=YourStrategy

# Validate it
make validation-validate-by-name NAME=YourStrategy
```

### **2. Test All Scripts in a Directory**
```bash
# Find scripts in a specific path
python scripts/validate_specific_script.py --search src/strategies

# Validate a specific one
make validation-validate-specific PATH=src/strategies/your_script.py
```

### **3. Validate Scripts by Type**
```bash
# Find options scripts
python scripts/validate_specific_script.py --list OPTIONS

# Find individual strategy scripts
python scripts/validate_specific_script.py --list INDIVIDUAL_STRATEGY

# Find comprehensive scripts
python scripts/validate_specific_script.py --list COMPREHENSIVE
```

### **4. Batch Validate Similar Scripts**
```bash
# First, find scripts
python scripts/validate_specific_script.py --list Strategy

# Then validate each one individually
make validation-validate-specific NAME=Strategy_Allocation
make validation-validate-specific NAME=Automated_Strategy_Selector
# ... etc
```

## 📊 Example Output

### **Discovery Output**
```
🔍 Searching for scripts containing: 'Strategy'
Found 317 matching scripts:
  1. Automated_Strategy_Selector (OPTIONS)
     ID: 002ac59a-e6c8-41df-8b6f-936659bfec15
     Path: /Users/abby/code/trading/automated_strategy_selector.py

  2. Strategy_Allocation (OPTIONS)
     ID: 098c30af-6bd8-482b-a52a-98d8c8ca7574
     Path: /Users/abby/code/trading/strategy_allocation_backtest.py
```

### **Validation Output**
```
📋 Script Information:
   ID: 098c30af-6bd8-482b-a52a-98d8c8ca7574
   Name: Strategy_Allocation
   Path: /Users/abby/code/trading/strategy_allocation_backtest.py
   Type: OPTIONS
   Function: main
   Class: StrategyAllocationBacktest
   Timeout: 900s
   Status: NEVER_RUN

🧪 Validating script: Strategy_Allocation
   Path: /Users/abby/code/trading/strategy_allocation_backtest.py
   Type: OPTIONS
✅ Validation completed: SUCCESS
   Execution time: 0.38s
   Performance:
     - Total return: 3470809080.30%
     - Sharpe ratio: 0.00
     - Max drawdown: 47.20%
     - Total trades: 630
```

## 🔧 Troubleshooting

### **Script Not Found**
```bash
# If exact name doesn't work, try partial search
python scripts/validate_specific_script.py --search partial_name

# Check available scripts
make validation-list-scripts PATTERN=your_pattern
```

### **Multiple Matches**
```bash
# When multiple scripts match, use exact ID
python scripts/validate_specific_script.py --id exact-script-id

# Or use exact name
python scripts/validate_specific_script.py --name "Exact Script Name"
```

### **Path Issues**
```bash
# Use partial path matching
python scripts/validate_specific_script.py --path partial_path

# Or search by filename
python scripts/validate_specific_script.py --search filename.py
```

## 💡 Pro Tips

### **1. Use Partial Matching**
- `NAME=Strategy` finds all scripts with "Strategy" in the name
- `SEARCH=options` finds scripts with "options" anywhere
- `PATH=backtest` finds scripts with "backtest" in the path

### **2. Get Script Info Without Validation**
```bash
python scripts/validate_specific_script.py --name Strategy_Allocation --info
```

### **3. Refresh Script Discovery**
```bash
# Update the script database
make validation-discover-json

# Then search again
make validation-find-script NAME=YourScript
```

### **4. Combine with Batch Operations**
```bash
# Find scripts
python scripts/validate_specific_script.py --list Strategy

# Validate multiple scripts
make validation-validate-specific NAME=Strategy_Allocation
make validation-validate-specific NAME=Automated_Strategy_Selector
make validation-validate-specific NAME=Enhanced_Multi_Strategy
```

## 🚀 Quick Reference

### **Most Common Commands**
```bash
# Find scripts
make validation-find-script NAME=YourPattern

# Validate by name
make validation-validate-by-name NAME=YourScript

# Advanced search
python scripts/validate_specific_script.py --list YourPattern

# Advanced validation
python scripts/validate_specific_script.py --name YourScript
```

### **All Available Methods**
1. `make validation-find-script NAME=pattern` - Find scripts
2. `make validation-validate-by-name NAME=name` - Validate by name
3. `make validation-validate-by-path PATH=path` - Validate by path
4. `make validation-validate SCRIPT_ID=id` - Validate by ID
5. `make validation-validate-specific NAME=name` - Advanced validation
6. `python scripts/validate_specific_script.py --list pattern` - List scripts
7. `python scripts/validate_specific_script.py --name name` - Validate by name
8. `python scripts/validate_specific_script.py --search query` - Search and validate

---

**🎉 You now have complete control over targeting specific backtests!**

With **2,613 backtest scripts** available, you can easily find and validate any script using multiple targeting methods.











