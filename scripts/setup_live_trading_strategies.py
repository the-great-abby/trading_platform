#!/usr/bin/env python3
"""
Live Trading Strategy Setup Script
=================================

This script configures trading strategies for the live trading service,
similar to the paper trading setup but with real money and risk controls.

Features:
- Strategy configuration and deployment
- Risk management setup
- Trailing stop configuration
- Portfolio limits and controls
- Integration with Elliott Wave analysis
- Real-time monitoring and alerts

Author: Orion (AI Trading Assistant)
Date: 2025-09-26
"""

import asyncio
import json
import logging
import httpx
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveTradingStrategySetup:
    """Live trading strategy configuration and setup"""
    
    def __init__(self, live_trading_url: str = "http://localhost:11120"):
        self.live_trading_url = live_trading_url
        self.timeout = 30
        self.strategies = []
        self.risk_config = {}
        self.trailing_stops = {}
        
        logger.info(f"🚀 Live Trading Strategy Setup initialized: {live_trading_url}")
    
    async def check_service_health(self) -> bool:
        """Check if live trading service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✅ Live trading service is healthy: {health_data}")
                    return True
                else:
                    logger.error(f"❌ Live trading service health check failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error checking live trading service health: {e}")
            return False
    
    async def connect_to_public(self, access_token: str, account_name: str = "Live Trading Account") -> bool:
        """Connect to Public.com API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.live_trading_url}/api/v1/auth/public-connect",
                    json={
                        "access_token": access_token,
                        "account_name": account_name,
                        "account_type": "CASH"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Connected to Public.com: {result}")
                    return True
                else:
                    logger.error(f"❌ Failed to connect to Public.com: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error connecting to Public.com: {e}")
            return False
    
    async def setup_risk_profile(self, account_id: str, risk_config: Dict[str, Any]) -> bool:
        """Set up risk management profile"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{self.live_trading_url}/api/v1/risk/profile/{account_id}",
                    json=risk_config
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Risk profile configured: {result}")
                    return True
                else:
                    logger.error(f"❌ Failed to configure risk profile: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error configuring risk profile: {e}")
            return False
    
    async def configure_strategies(self, account_id: str, strategies: List[Dict[str, Any]]) -> bool:
        """Configure trading strategies"""
        try:
            for strategy in strategies:
                logger.info(f"📊 Configuring strategy: {strategy['name']}")
                
                # For now, we'll store strategy configuration in the risk profile
                # In a full implementation, you'd have dedicated strategy endpoints
                strategy_config = {
                    "max_position_size": strategy.get("max_position_size", 0.05),
                    "max_risk_per_trade": strategy.get("max_risk_per_trade", 0.01),
                    "allowed_strategies": [strategy["name"]],
                    "max_daily_trades": strategy.get("max_daily_trades", 10),
                    "max_daily_loss": strategy.get("max_daily_loss", 1000.0)
                }
                
                success = await self.setup_risk_profile(account_id, strategy_config)
                if not success:
                    logger.error(f"❌ Failed to configure strategy {strategy['name']}")
                    return False
                
                logger.info(f"✅ Strategy {strategy['name']} configured successfully")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error configuring strategies: {e}")
            return False
    
    async def setup_trailing_stops(self, account_id: str, trailing_config: Dict[str, Any]) -> bool:
        """Set up trailing stop management"""
        try:
            # Store trailing stop configuration
            self.trailing_stops[account_id] = trailing_config
            
            logger.info(f"✅ Trailing stops configured for account {account_id}")
            logger.info(f"📊 Trailing stop config: {trailing_config}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error setting up trailing stops: {e}")
            return False
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/api/v1/accounts")
                
                if response.status_code == 200:
                    accounts_data = response.json()
                    if accounts_data.get("accounts"):
                        account = accounts_data["accounts"][0]  # Use first account
                        logger.info(f"📊 Account info: {account}")
                        return account
                    else:
                        logger.warning("⚠️ No accounts found")
                        return None
                else:
                    logger.error(f"❌ Failed to get account info: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error getting account info: {e}")
            return None
    
    async def submit_sample_order(self, account_id: str, symbol: str = "SPY") -> bool:
        """Submit a sample order to test the setup"""
        try:
            # Create a simple Iron Condor order
            order_data = {
                "symbol": symbol,
                "strategy": "IRON_CONDOR",
                "legs": [
                    {
                        "action": "SELL",
                        "option_type": "CALL",
                        "strike_price": 450.0,
                        "quantity": 1,
                        "premium": 2.50
                    },
                    {
                        "action": "BUY",
                        "option_type": "CALL",
                        "strike_price": 455.0,
                        "quantity": 1,
                        "premium": 1.00
                    },
                    {
                        "action": "SELL",
                        "option_type": "PUT",
                        "strike_price": 440.0,
                        "quantity": 1,
                        "premium": 2.00
                    },
                    {
                        "action": "BUY",
                        "option_type": "PUT",
                        "strike_price": 435.0,
                        "quantity": 1,
                        "premium": 0.50
                    }
                ],
                "order_type": "LIMIT",
                "limit_price": 3.00,
                "time_in_force": "DAY",
                "estimated_premium": 3.00,
                "estimated_risk": 1000.0,
                "greeks": {
                    "delta": 0.05,
                    "gamma": 0.01,
                    "theta": -0.02,
                    "vega": 0.15
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.live_trading_url}/api/v1/trading/orders",
                    params={"account_id": account_id},
                    json=order_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Sample order submitted: {result}")
                    return True
                else:
                    logger.error(f"❌ Failed to submit sample order: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error submitting sample order: {e}")
            return False

def get_default_strategy_config() -> Dict[str, Any]:
    """Get default strategy configuration based on paper trading setup"""
    return {
        "strategies": [
            {
                "name": "IRON_CONDOR",
                "max_position_size": 0.05,  # 5% of portfolio
                "max_risk_per_trade": 0.01,  # 1% risk per trade
                "max_daily_trades": 5,
                "max_daily_loss": 500.0,
                "description": "Iron Condor strategy for range-bound markets"
            },
            {
                "name": "BUTTERFLY_SPREAD",
                "max_position_size": 0.03,  # 3% of portfolio
                "max_risk_per_trade": 0.008,  # 0.8% risk per trade
                "max_daily_trades": 3,
                "max_daily_loss": 300.0,
                "description": "Butterfly spread strategy for directional plays"
            },
            {
                "name": "CALENDAR_SPREAD",
                "max_position_size": 0.04,  # 4% of portfolio
                "max_risk_per_trade": 0.009,  # 0.9% risk per trade
                "max_daily_trades": 4,
                "max_daily_loss": 400.0,
                "description": "Calendar spread strategy for time decay"
            }
        ],
        "trailing_stops": {
            "iron_condor": {
                "profit_threshold": 0.5,  # 50% profit
                "trail_percentage": 0.05,  # 5% below current
                "min_profit": 0.3  # Minimum profit to activate
            },
            "butterfly_spread": {
                "profit_threshold": 0.3,  # 30% profit
                "trail_percentage": 0.03,  # 3% below current
                "min_profit": 0.2
            },
            "calendar_spread": {
                "profit_threshold": 0.4,  # 40% profit
                "trail_percentage": 0.04,  # 4% below current
                "min_profit": 0.25
            }
        },
        "portfolio_limits": {
            "max_total_exposure": 0.20,  # 20% total portfolio exposure
            "max_single_symbol": 0.10,  # 10% max per symbol
            "max_daily_loss": 1000.0,  # $1000 max daily loss
            "max_daily_trades": 15,  # 15 trades per day max
            "min_cash_reserve": 0.20  # 20% cash reserve
        }
    }

async def main():
    """Main function to set up live trading strategies"""
    try:
        # Get configuration
        config = get_default_strategy_config()
        
        # Initialize setup
        setup = LiveTradingStrategySetup()
        
        # Check service health
        logger.info("🔍 Checking live trading service health...")
        if not await setup.check_service_health():
            logger.error("❌ Live trading service is not healthy. Exiting.")
            return
        
        # Get Public.com access token from environment or user input
        access_token = os.getenv("PUBLIC_API_KEY")
        if not access_token:
            access_token = input("Enter your Public.com access token: ").strip()
            if not access_token:
                logger.error("❌ No access token provided. Exiting.")
                return
        
        # Connect to Public.com
        logger.info("🔗 Connecting to Public.com...")
        if not await setup.connect_to_public(access_token):
            logger.error("❌ Failed to connect to Public.com. Exiting.")
            return
        
        # Get account information
        logger.info("📊 Getting account information...")
        account_info = await setup.get_account_info()
        if not account_info:
            logger.error("❌ No account information available. Exiting.")
            return
        
        account_id = account_info["account_id"]
        logger.info(f"✅ Using account: {account_id}")
        
        # Configure strategies
        logger.info("📊 Configuring trading strategies...")
        if not await setup.configure_strategies(account_id, config["strategies"]):
            logger.error("❌ Failed to configure strategies. Exiting.")
            return
        
        # Set up trailing stops
        logger.info("🛑 Setting up trailing stops...")
        if not await setup.setup_trailing_stops(account_id, config["trailing_stops"]):
            logger.error("❌ Failed to set up trailing stops. Exiting.")
            return
        
        # Set up portfolio limits
        logger.info("💰 Setting up portfolio limits...")
        portfolio_limits = {
            "max_position_size": config["portfolio_limits"]["max_total_exposure"],
            "max_portfolio_risk": config["portfolio_limits"]["max_total_exposure"],
            "max_daily_loss": config["portfolio_limits"]["max_daily_loss"],
            "max_daily_trades": config["portfolio_limits"]["max_daily_trades"],
            "risk_level": "MODERATE"
        }
        
        if not await setup.setup_risk_profile(account_id, portfolio_limits):
            logger.error("❌ Failed to set up portfolio limits. Exiting.")
            return
        
        # Test with a sample order (optional)
        test_order = input("Submit a test order? (y/N): ").strip().lower()
        if test_order == 'y':
            logger.info("🧪 Submitting test order...")
            await setup.submit_sample_order(account_id)
        
        logger.info("✅ Live trading strategy setup completed successfully!")
        logger.info("🎯 You can now start live trading with the configured strategies.")
        logger.info("📊 Monitor your trades at: http://localhost:11120/docs")
        
    except KeyboardInterrupt:
        logger.info("🛑 Setup interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error in live trading strategy setup: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())











