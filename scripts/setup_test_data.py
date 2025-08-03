#!/usr/bin/env python3
"""
Test Data Setup Script
Creates test data for the trading system testing environment
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data constants
TEST_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]
TEST_STRATEGIES = ["sma_crossover", "rsi_strategy", "bollinger_bands", "macd_strategy"]
TEST_USERS = ["test_user_1", "test_user_2", "test_user_3"]


async def setup_test_market_data():
    """Setup test market data"""
    logger.info("Setting up test market data...")
    
    # This would connect to your market data service
    # For now, we'll create mock data
    test_data = []
    
    for symbol in TEST_SYMBOLS:
        base_price = random.uniform(50, 500)
        for i in range(30):  # 30 days of data
            date = datetime.now() - timedelta(days=i)
            price = base_price + random.uniform(-10, 10)
            volume = random.randint(1000, 10000)
            
            test_data.append({
                "symbol": symbol,
                "price": Decimal(str(round(price, 2))),
                "volume": volume,
                "timestamp": date,
                "open": Decimal(str(round(price - random.uniform(-5, 5), 2))),
                "high": Decimal(str(round(price + random.uniform(0, 5), 2))),
                "low": Decimal(str(round(price - random.uniform(0, 5), 2))),
                "close": Decimal(str(round(price, 2)))
            })
    
    logger.info(f"Created {len(test_data)} market data records")
    return test_data


async def setup_test_strategies():
    """Setup test trading strategies"""
    logger.info("Setting up test strategies...")
    
    strategies = []
    
    for strategy_name in TEST_STRATEGIES:
        strategy = {
            "name": strategy_name,
            "description": f"Test {strategy_name} strategy",
            "parameters": {
                "lookback_period": random.randint(10, 50),
                "threshold": random.uniform(0.1, 0.3),
                "position_size": random.uniform(0.1, 0.5)
            },
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        strategies.append(strategy)
    
    logger.info(f"Created {len(strategies)} test strategies")
    return strategies


async def setup_test_orders():
    """Setup test orders"""
    logger.info("Setting up test orders...")
    
    orders = []
    
    for i in range(20):  # 20 test orders
        symbol = random.choice(TEST_SYMBOLS)
        side = random.choice(["BUY", "SELL"])
        quantity = random.randint(10, 100)
        price = Decimal(str(round(random.uniform(50, 500), 2)))
        
        order = {
            "order_id": f"test_order_{i:03d}",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "order_type": random.choice(["MARKET", "LIMIT"]),
            "status": random.choice(["PENDING", "FILLED", "CANCELLED"]),
            "user_id": random.choice(TEST_USERS),
            "strategy_id": random.choice(TEST_STRATEGIES),
            "created_at": datetime.now() - timedelta(hours=random.randint(1, 24)),
            "updated_at": datetime.now()
        }
        orders.append(order)
    
    logger.info(f"Created {len(orders)} test orders")
    return orders


async def setup_test_portfolios():
    """Setup test portfolios"""
    logger.info("Setting up test portfolios...")
    
    portfolios = []
    
    for user_id in TEST_USERS:
        portfolio = {
            "user_id": user_id,
            "total_value": Decimal(str(round(random.uniform(10000, 100000), 2))),
            "cash_balance": Decimal(str(round(random.uniform(1000, 10000), 2))),
            "positions": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Add some positions
        for symbol in random.sample(TEST_SYMBOLS, 3):
            position = {
                "symbol": symbol,
                "quantity": random.randint(10, 100),
                "avg_price": Decimal(str(round(random.uniform(50, 500), 2))),
                "current_value": Decimal(str(round(random.uniform(1000, 10000), 2))),
                "unrealized_pnl": Decimal(str(round(random.uniform(-1000, 1000), 2)))
            }
            portfolio["positions"].append(position)
        
        portfolios.append(portfolio)
    
    logger.info(f"Created {len(portfolios)} test portfolios")
    return portfolios


async def setup_test_backtests():
    """Setup test backtest results"""
    logger.info("Setting up test backtest results...")
    
    backtests = []
    
    for i in range(10):  # 10 test backtests
        strategy = random.choice(TEST_STRATEGIES)
        symbol = random.choice(TEST_SYMBOLS)
        
        # Generate realistic performance metrics
        total_return = random.uniform(-0.2, 0.5)  # -20% to +50%
        sharpe_ratio = random.uniform(-1, 3)
        max_drawdown = random.uniform(0, 0.3)  # 0% to 30%
        
        backtest = {
            "backtest_id": f"test_backtest_{i:03d}",
            "strategy_name": strategy,
            "symbol": symbol,
            "start_date": datetime.now() - timedelta(days=random.randint(30, 365)),
            "end_date": datetime.now(),
            "total_return": Decimal(str(round(total_return, 4))),
            "annualized_return": Decimal(str(round(total_return * 12, 4))),
            "sharpe_ratio": Decimal(str(round(sharpe_ratio, 4))),
            "max_drawdown": Decimal(str(round(max_drawdown, 4))),
            "total_trades": random.randint(10, 100),
            "win_rate": random.uniform(0.3, 0.7),
            "profit_factor": random.uniform(0.5, 2.0),
            "parameters": {
                "lookback_period": random.randint(10, 50),
                "threshold": random.uniform(0.1, 0.3)
            },
            "created_at": datetime.now(),
            "status": "COMPLETED"
        }
        backtests.append(backtest)
    
    logger.info(f"Created {len(backtests)} test backtest results")
    return backtests


async def setup_test_signals():
    """Setup test trading signals"""
    logger.info("Setting up test trading signals...")
    
    signals = []
    
    for i in range(15):  # 15 test signals
        symbol = random.choice(TEST_SYMBOLS)
        signal_type = random.choice(["BUY", "SELL", "HOLD"])
        confidence = random.uniform(0.5, 1.0)
        
        signal = {
            "signal_id": f"test_signal_{i:03d}",
            "symbol": symbol,
            "signal_type": signal_type,
            "confidence": Decimal(str(round(confidence, 4))),
            "price": Decimal(str(round(random.uniform(50, 500), 2))),
            "strategy_name": random.choice(TEST_STRATEGIES),
            "reasoning": f"Test signal for {symbol} based on {signal_type} signal",
            "created_at": datetime.now() - timedelta(hours=random.randint(1, 24)),
            "expires_at": datetime.now() + timedelta(hours=random.randint(1, 24)),
            "status": random.choice(["ACTIVE", "EXECUTED", "EXPIRED"])
        }
        signals.append(signal)
    
    logger.info(f"Created {len(signals)} test signals")
    return signals


async def setup_test_risk_metrics():
    """Setup test risk metrics"""
    logger.info("Setting up test risk metrics...")
    
    risk_metrics = []
    
    for user_id in TEST_USERS:
        # Calculate some realistic risk metrics
        var_95 = random.uniform(1000, 5000)
        var_99 = var_95 * 1.5
        max_loss = var_99 * 2
        
        metrics = {
            "user_id": user_id,
            "var_95": Decimal(str(round(var_95, 2))),
            "var_99": Decimal(str(round(var_99, 2))),
            "max_loss": Decimal(str(round(max_loss, 2))),
            "current_exposure": Decimal(str(round(random.uniform(5000, 50000), 2))),
            "position_concentration": random.uniform(0.1, 0.8),
            "correlation_risk": random.uniform(0.1, 0.9),
            "liquidity_risk": random.uniform(0.1, 0.5),
            "calculated_at": datetime.now()
        }
        risk_metrics.append(metrics)
    
    logger.info(f"Created {len(risk_metrics)} test risk metrics")
    return risk_metrics


async def setup_test_llm_data():
    """Setup test LLM/AI data"""
    logger.info("Setting up test LLM data...")
    
    llm_data = []
    
    # Test sentiment analysis results
    for symbol in TEST_SYMBOLS:
        sentiment = random.choice(["POSITIVE", "NEGATIVE", "NEUTRAL"])
        confidence = random.uniform(0.5, 1.0)
        
        sentiment_data = {
            "symbol": symbol,
            "sentiment": sentiment,
            "confidence": Decimal(str(round(confidence, 4))),
            "source": "news_analysis",
            "text_sample": f"Test news article about {symbol} performance",
            "created_at": datetime.now() - timedelta(hours=random.randint(1, 24))
        }
        llm_data.append(sentiment_data)
    
    # Test AI-generated signals
    for i in range(5):
        signal_data = {
            "signal_id": f"ai_signal_{i:03d}",
            "symbol": random.choice(TEST_SYMBOLS),
            "signal_type": random.choice(["BUY", "SELL"]),
            "confidence": Decimal(str(round(random.uniform(0.6, 0.95), 4))),
            "reasoning": f"AI-generated signal based on market analysis and sentiment",
            "model_version": "gpt-4-v1",
            "created_at": datetime.now() - timedelta(hours=random.randint(1, 12))
        }
        llm_data.append(signal_data)
    
    logger.info(f"Created {len(llm_data)} test LLM data records")
    return llm_data


async def main():
    """Main function to setup all test data"""
    logger.info("🚀 Starting test data setup...")
    
    try:
        # Setup all test data
        market_data = await setup_test_market_data()
        strategies = await setup_test_strategies()
        orders = await setup_test_orders()
        portfolios = await setup_test_portfolios()
        backtests = await setup_test_backtests()
        signals = await setup_test_signals()
        risk_metrics = await setup_test_risk_metrics()
        llm_data = await setup_test_llm_data()
        
        # Summary
        total_records = (
            len(market_data) + len(strategies) + len(orders) + 
            len(portfolios) + len(backtests) + len(signals) + 
            len(risk_metrics) + len(llm_data)
        )
        
        logger.info("✅ Test data setup completed successfully!")
        logger.info(f"📊 Total records created: {total_records}")
        logger.info("📋 Summary:")
        logger.info(f"   - Market data: {len(market_data)} records")
        logger.info(f"   - Strategies: {len(strategies)} records")
        logger.info(f"   - Orders: {len(orders)} records")
        logger.info(f"   - Portfolios: {len(portfolios)} records")
        logger.info(f"   - Backtests: {len(backtests)} records")
        logger.info(f"   - Signals: {len(signals)} records")
        logger.info(f"   - Risk metrics: {len(risk_metrics)} records")
        logger.info(f"   - LLM data: {len(llm_data)} records")
        
        # In a real implementation, you would save this data to your database
        # For now, we'll just log that it's ready
        logger.info("💾 Test data is ready for use in tests")
        
    except Exception as e:
        logger.error(f"❌ Error setting up test data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 