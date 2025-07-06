# 🚀 Quick Start Guide

Get your algorithmic trading bot up and running in minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd algo-trader
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up configuration**
   ```bash
   cp config.env.example .env
   # Edit .env with your API keys and preferences
   ```

## Quick Start

### Option 1: Run the Trading Bot
```bash
python run_trader.py
```

### Option 2: Run the Web Interface
```bash
python run_api.py
```
Then visit http://localhost:8000

### Option 3: Run Both (in separate terminals)
```bash
# Terminal 1
python run_trader.py

# Terminal 2
python run_api.py
```

## Configuration

Edit the `.env` file to configure your bot:

```env
# Required: Get free API keys from Alpaca
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here

# Optional: Adjust trading parameters
INITIAL_CAPITAL=10000
MAX_POSITION_SIZE=0.1
TRADING_INTERVAL=60
```

## Getting API Keys

1. Visit [Alpaca Markets](https://alpaca.markets/)
2. Sign up for a free account
3. Go to API Keys section
4. Copy your API key and secret
5. Add them to your `.env` file

## Testing

Run the test suite:
```bash
pytest
```

## Next Steps

1. **Explore Strategies**: Check out the strategies in `src/strategies/`
2. **Customize**: Modify parameters in the `.env` file
3. **Monitor**: Use the web interface at http://localhost:8000
4. **Analyze**: Use the Jupyter notebooks in `notebooks/`

## Support

- Check the [README.md](README.md) for detailed documentation
- Create an issue for bugs or feature requests
- Join our community discussions

---

**Happy Trading! 📈** 