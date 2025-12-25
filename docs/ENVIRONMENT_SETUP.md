# Environment Variable Setup Guide

This guide explains how to automatically load environment variables for local development.

## Problem

Running demo scripts and backtests requires environment variables like `POLYGON_API_KEY`. Manually setting them every time is tedious:

```bash
# Tedious manual approach ❌
POLYGON_API_KEY=xyz python3 demo/demo_comprehensive_options_backtest.py
```

## Solutions

We provide **three automated solutions**:

---

## ✅ Solution 1: Makefile Targets (Recommended)

**Best for:** Running specific demos and backtests

The `Makefile.demo` automatically loads environment variables from Kubernetes secrets.

### Usage

```bash
# Run options demo (auto-loads all env vars)
make -f makefiles/Makefile.demo options-demo

# Run stock comparison
make -f makefiles/Makefile.demo comparison-demo

# Run comprehensive comparison (stocks + options)
make -f makefiles/Makefile.demo comprehensive-demo

# Check loaded environment
make -f makefiles/Makefile.demo env-info

# Test Polygon API
make -f makefiles/Makefile.demo test-api

# See all available demos
make -f makefiles/Makefile.demo list-demos
```

### How It Works

The Makefile:
1. Fetches `POLYGON_API_KEY` from Kubernetes secret `trading-secrets`
2. Exports all necessary environment variables
3. Validates API key before running scripts
4. Runs the Python script with pre-configured environment

### Benefits

- ✅ No manual environment setup
- ✅ Automatically pulls from Kubernetes secrets
- ✅ Validates configuration before running
- ✅ Works on any machine with kubectl access
- ✅ Consistent with your existing Makefile workflow

---

## ✅ Solution 2: direnv (Automatic Loading)

**Best for:** Always having environment variables available when working in the directory

[direnv](https://direnv.net/) automatically loads environment variables when you `cd` into the directory.

### Installation

```bash
# Install direnv
brew install direnv

# Add to shell (zsh)
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

# Reload shell
source ~/.zshrc

# Copy example config
cp .envrc.example .envrc

# Allow direnv to load
direnv allow
```

### Usage

Once installed, environment variables load automatically:

```bash
cd /Users/abby/code/trading
# direnv: loading .envrc
# ✅ Trading environment loaded:
#   🔑 POLYGON_API_KEY: PwSQb2yBh2aYq...
#   💾 DATABASE_URL: postgresql://...
#   💰 BACKTEST_INITIAL_CAPITAL: $4000

# Now run any script - env vars are already loaded!
python3 demo/demo_comprehensive_options_backtest.py

# Leave directory - env vars unload automatically
cd ..
# direnv: unloading
```

### How It Works

- `.envrc` file defines environment variables
- `direnv` hook in shell detects when you enter/leave directory
- Automatically exports/unexports variables
- Pulls from Kubernetes secrets just like the Makefile

### Benefits

- ✅ Completely automatic - no commands to remember
- ✅ Environment changes when you `cd` into/out of directory
- ✅ Works with all commands, not just Makefile targets
- ✅ Great for interactive development

### Security Note

The `.envrc` file is gitignored (contains secrets). Each developer creates their own from `.envrc.example`.

---

## ✅ Solution 3: python-dotenv in Scripts

**Best for:** Script-level environment loading

Already implemented in most scripts:

```python
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Now use environment variables
api_key = os.getenv('POLYGON_API_KEY')
```

### Create .env File

**Note:** The `.env` file is blocked by `.gitignore` for security.

You can create it manually:

```bash
# Create .env file
cat > .env << 'EOF'
POLYGON_API_KEY=$(kubectl get secret trading-secrets -n trading-system -o jsonpath='{.data.POLYGON_API_KEY}' 2>/dev/null | base64 -d)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trading_bot
ENABLE_LLM_EVALUATION=false
BACKTEST_INITIAL_CAPITAL=4000
EOF
```

Or use the Makefile to create it:

```bash
# Create .env from Kubernetes secrets
kubectl get secret trading-secrets -n trading-system -o json | \
  jq -r '.data | to_entries | map("\(.key)=\(.value | @base64d)") | .[]' > .env
```

### Benefits

- ✅ Works without external tools
- ✅ Standard Python approach
- ✅ Portable across environments

### Drawbacks

- ❌ Requires manual .env file creation
- ❌ .env file can get out of sync with K8s secrets
- ❌ Each script must call `load_dotenv()`

---

## Comparison

| Solution | Auto-Load | K8s Integration | Interactive Dev | Script Execution |
|----------|-----------|-----------------|-----------------|------------------|
| **Makefile** | ✅ (for targets) | ✅ Real-time | ❌ | ✅ Best |
| **direnv** | ✅ Always | ✅ Real-time | ✅ Best | ✅ |
| **python-dotenv** | ⚠️ Manual .env | ❌ Static file | ⚠️ | ✅ |

## Recommended Workflow

### For Quick Tasks (Recommended)
```bash
make -f makefiles/Makefile.demo options-demo
```

### For Development Sessions (Best Experience)
1. Install direnv (one-time setup)
2. Copy `.envrc.example` to `.envrc`
3. Run `direnv allow`
4. Enjoy automatic environment loading!

### For Production/CI
Use Kubernetes secrets directly (already configured in K8s manifests)

---

## Troubleshooting

### "POLYGON_API_KEY not found"

```bash
# Check if secret exists in Kubernetes
kubectl get secret trading-secrets -n trading-system

# View secret contents
kubectl get secret trading-secrets -n trading-system -o jsonpath='{.data.POLYGON_API_KEY}' | base64 -d

# If secret doesn't exist, you need to create it
kubectl create secret generic trading-secrets \
  --from-literal=POLYGON_API_KEY=your_key_here \
  -n trading-system
```

### "direnv: command not found"

```bash
# Install direnv
brew install direnv

# Add to shell configuration
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc
```

### "direnv: error .envrc is blocked"

```bash
# Allow direnv to load .envrc
direnv allow
```

### Python script can't find environment variables

Make sure script has:
```python
from dotenv import load_dotenv
load_dotenv()  # Must be called before accessing env vars
```

---

## Files

- `Makefile.demo` - Makefile with auto-loaded environment
- `.envrc.example` - direnv configuration template
- `.env` - Local environment file (gitignored, create manually)
- `demo/demo_comprehensive_options_backtest.py` - Updated to use load_dotenv()

## Next Steps

1. **Try the Makefile approach** (easiest):
   ```bash
   make -f makefiles/Makefile.demo env-info
   make -f makefiles/Makefile.demo options-demo
   ```

2. **Install direnv** for the best development experience:
   ```bash
   brew install direnv
   echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
   source ~/.zshrc
   cp .envrc.example .envrc
   direnv allow
   ```

3. **Run demos** without thinking about environment variables!

