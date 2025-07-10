# 🚀 Space Trading Station - Launch Sequence

Get your algorithmic trading station up and running in minutes! Welcome to Mission Control.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Installation

1. **Clone the Space Station**
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

4. **Set up Mission Control configuration**
   ```bash
   cp config.env.example .env
   # Edit .env with your API keys and preferences
   ```

## Launch Sequence

### Option 1: Launch the Trading Bot
```bash
python run_trader.py
```

### Option 2: Launch the Web Interface
```bash
python run_api.py
```
Then visit http://localhost:8000 for Mission Control dashboard

### Option 3: Launch Both Systems (in separate terminals)
```bash
# Terminal 1 - Trading Bot
python run_trader.py

# Terminal 2 - Mission Control Interface
python run_api.py
```

## Mission Control Configuration

Edit the `.env` file to configure your trading station:

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

## System Testing

Run the test suite:
```bash
pytest
```

## Next Steps

1. **Explore AI Navigation Systems**: Check out the strategies in `src/strategies/`
2. **Customize Mission Parameters**: Modify parameters in the `.env` file
3. **Monitor from Mission Control**: Use the web interface at http://localhost:8000
4. **Analyze Performance**: Use the Jupyter notebooks in `notebooks/`

## Support

- Check the [README.md](README.md) for detailed documentation
- Create an issue for bugs or feature requests
- Join our community discussions

---

**Happy Trading, Space Cadet! 🚀📈** 