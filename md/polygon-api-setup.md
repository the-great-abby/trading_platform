# Polygon API Setup Guide

## Quick Setup

### 1. Create/Edit .env File

```bash
# Create .env file if it doesn't exist
cp config.env.example .env

# Or create a new one
nano .env
```

### 2. Add Your Polygon API Key

Add this line to your `.env` file:

```bash
POLYGON_API_KEY=your_actual_api_key_here
```

### 3. Get Your Polygon API Key

If you don't have one yet:

1. Go to [Polygon.io](https://polygon.io/)
2. Sign up for an account
3. For 0-DTE screening, you need the **Options Advanced** plan
4. Copy your API key from the dashboard
5. Paste it into your `.env` file

### 4. Verify Setup

```bash
# Check if .env file exists and has the key
grep POLYGON_API_KEY .env

# Test the screener
make -f makefiles/Makefile.zero-dte spreads
```

## Environment File Locations

The screener will automatically check these locations:

1. `/Users/abby/code/trading/.env` (project root)
2. `/Users/abby/code/trading/config.env`
3. `~/.trading/.env` (home directory)

## Alternative: Environment Variable

If you prefer not to use a `.env` file:

```bash
# Set for current session
export POLYGON_API_KEY=your_api_key_here

# Or add to your shell profile (~/.zshrc or ~/.bashrc)
echo 'export POLYGON_API_KEY=your_api_key_here' >> ~/.zshrc
source ~/.zshrc
```

## Kubernetes/Docker

For Kubernetes deployments, the API key is stored in secrets:

```bash
# Check if secret exists
kubectl get secret trading-secrets

# Create/update secret
kubectl create secret generic trading-secrets \
  --from-literal=POLYGON_API_KEY=your_api_key_here \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Security Notes

⚠️ **NEVER commit your .env file to git!**

The `.env` file is already in `.gitignore`, but double-check:

```bash
# Verify .env is ignored
grep -q "^\.env$" .gitignore && echo "✅ .env is gitignored" || echo "⚠️  Add .env to .gitignore!"
```

## Troubleshooting

### "Polygon API key not provided"

**Solution 1**: Create/edit `.env` file
```bash
echo "POLYGON_API_KEY=your_key_here" >> .env
```

**Solution 2**: Export environment variable
```bash
export POLYGON_API_KEY=your_key_here
```

**Solution 3**: Pass directly to Python
```bash
POLYGON_API_KEY=your_key_here python scripts/zero_dte_screener.py screen
```

### "python-dotenv not installed"

```bash
# Install in your virtual environment
pip install python-dotenv

# Or add to requirements
echo "python-dotenv" >> requirements.txt
pip install -r requirements.txt
```

### Verify API Key is Loaded

Add this to test:

```bash
# Quick test
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'API Key: {os.getenv(\"POLYGON_API_KEY\", \"NOT FOUND\")}')"
```

## Complete Example .env File

```bash
# Polygon API (Required for 0-DTE screener)
POLYGON_API_KEY=your_polygon_api_key_here

# Other API keys (optional)
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
PUBLIC_API_KEY=your_public_api_key_here

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/trading

# Trading config
INITIAL_CAPITAL=10000
MAX_POSITION_SIZE=0.1
```

## After Setup

Once your API key is configured, run:

```bash
# Test basic screening
make -f makefiles/Makefile.zero-dte screen

# Test credit spread screening
make -f makefiles/Makefile.zero-dte spreads

# You should see: "✅ Loaded environment from: /Users/abby/code/trading/.env"
```

---

**Need help?** The screener will show which .env file it's loading from when you run it.

