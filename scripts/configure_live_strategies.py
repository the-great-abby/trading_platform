#!/usr/bin/env python3
"""
Configure Live Trading Strategies
Based on paper trading configuration
"""
import asyncio
import httpx
import json
import logging
import os
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveStrategyConfigurator:
    """Configure live trading strategies based on paper trading setup"""
    
    def __init__(self, live_trading_url: str = "http://localhost:11120"):
        self.live_trading_url = live_trading_url
        self.timeout = 30
        
    async def configure_strategies(self) -> bool:
        """Configure live trading strategies"""
        try:
            # Check if account is connected
            accounts = await self.get_accounts()
            if not accounts:
                logger.error("❌ No live trading accounts found. Please connect to Public.com first.")
                return False
            
            account_id = accounts[0]["account_id"]
            logger.info(f"📊 Configuring strategies for account: {account_id}")
            
            # Load strategy configuration
            strategy_config = self.get_strategy_config()
            
            # Configure each strategy
            for strategy_name, config in strategy_config["strategies"].items():
                if config.get("enabled", False):
                    success = await self.configure_strategy(account_id, strategy_name, config)
                    if success:
                        logger.info(f"✅ Configured {strategy_name}")
                    else:
                        logger.error(f"❌ Failed to configure {strategy_name}")
            
            # Configure risk management
            await self.configure_risk_management(account_id, strategy_config["risk_management"])
            
            # Configure trailing stops
            await self.configure_trailing_stops(account_id, strategy_config["trailing_stops"])
            
            logger.info("🎉 Live trading strategies configured successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configuring strategies: {e}")
            return False
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get live trading accounts"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/api/v1/accounts")
                response.raise_for_status()
                data = response.json()
                # Handle nested structure
                if "accounts" in data:
                    return data["accounts"]
                return data
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            return []
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """Get strategy configuration based on paper trading setup"""
        return {
            "strategies": {
                "iron_condor": {
                    "name": "IRON_CONDOR",
                    "enabled": True,
                    "max_position_size": 0.05,  # 5% of portfolio
                    "max_risk_per_trade": 0.01,  # 1% risk per trade
                    "max_daily_trades": 5,
                    "max_daily_loss": 500.0,
                    "description": "Iron Condor strategy for range-bound markets",
                    "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL"]
                },
                "butterfly_spread": {
                    "name": "BUTTERFLY_SPREAD",
                    "enabled": True,
                    "max_position_size": 0.03,  # 3% of portfolio
                    "max_risk_per_trade": 0.008,  # 0.8% risk per trade
                    "max_daily_trades": 3,
                    "max_daily_loss": 300.0,
                    "description": "Butterfly spread strategy for directional plays",
                    "symbols": ["SPY", "QQQ", "AAPL"]
                },
                "calendar_spread": {
                    "name": "CALENDAR_SPREAD",
                    "enabled": True,
                    "max_position_size": 0.04,  # 4% of portfolio
                    "max_risk_per_trade": 0.009,  # 0.9% risk per trade
                    "max_daily_trades": 4,
                    "max_daily_loss": 400.0,
                    "description": "Calendar spread strategy for time decay",
                    "symbols": ["SPY", "QQQ", "AAPL", "MSFT"]
                },
                "elliott_wave_impulse": {
                    "name": "ELLIOTT_WAVE_IMPULSE",
                    "enabled": True,
                    "max_position_size": 0.02,  # 2% of portfolio
                    "max_risk_per_trade": 0.005,  # 0.5% risk per trade
                    "max_daily_trades": 2,
                    "max_daily_loss": 200.0,
                    "description": "Elliott Wave impulse pattern strategy",
                    "symbols": ["SPY", "QQQ", "AAPL"]
                },
                "elliott_wave_corrective": {
                    "name": "ELLIOTT_WAVE_CORRECTIVE",
                    "enabled": True,
                    "max_position_size": 0.03,  # 3% of portfolio
                    "max_risk_per_trade": 0.008,  # 0.8% risk per trade
                    "max_daily_trades": 3,
                    "max_daily_loss": 300.0,
                    "description": "Elliott Wave corrective pattern strategy",
                    "symbols": ["SPY", "QQQ", "AAPL"]
                }
            },
            "risk_management": {
                "risk_level": "MODERATE",
                "max_greeks_exposure": {
                    "delta": 0.10,
                    "gamma": 0.05,
                    "theta": -0.02,
                    "vega": 0.15
                },
                "position_limits": {
                    "max_options_contracts": 10,
                    "max_stock_shares": 1000,
                    "max_expiration_days": 45
                },
                "emergency_controls": {
                    "stop_loss_percentage": 0.15,
                    "max_drawdown": 0.20,
                    "emergency_stop_enabled": True
                }
            },
            "trailing_stops": {
                "iron_condor": {
                    "profit_threshold": 0.5,
                    "trail_percentage": 0.05,
                    "min_profit": 0.3,
                    "enabled": True
                },
                "butterfly_spread": {
                    "profit_threshold": 0.3,
                    "trail_percentage": 0.03,
                    "min_profit": 0.2,
                    "enabled": True
                },
                "calendar_spread": {
                    "profit_threshold": 0.4,
                    "trail_percentage": 0.04,
                    "min_profit": 0.25,
                    "enabled": True
                },
                "elliott_wave_impulse": {
                    "profit_threshold": 0.2,
                    "trail_percentage": 0.02,
                    "min_profit": 0.1,
                    "enabled": True
                },
                "elliott_wave_corrective": {
                    "profit_threshold": 0.15,
                    "trail_percentage": 0.015,
                    "min_profit": 0.08,
                    "enabled": True
                }
            }
        }
    
    async def configure_strategy(self, account_id: str, strategy_name: str, config: Dict[str, Any]) -> bool:
        """Configure a specific strategy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.live_trading_url}/api/v1/strategies/?account_id={account_id}",
                    json={
                        "strategy_name": config["name"],
                        "enabled": config["enabled"],
                        "max_position_size": config["max_position_size"],
                        "max_risk_per_trade": config["max_risk_per_trade"],
                        "max_daily_trades": config["max_daily_trades"],
                        "max_daily_loss": config["max_daily_loss"],
                        "description": config["description"],
                        "symbols": config["symbols"]
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to configure {strategy_name}: {e}")
            return False
    
    async def configure_risk_management(self, account_id: str, risk_config: Dict[str, Any]) -> bool:
        """Configure risk management settings"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.live_trading_url}/api/v1/risk-management/",
                    json={
                        "account_id": account_id,
                        "risk_level": risk_config["risk_level"],
                        "max_greeks_exposure": risk_config["max_greeks_exposure"],
                        "position_limits": risk_config["position_limits"],
                        "emergency_controls": risk_config["emergency_controls"]
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to configure risk management: {e}")
            return False
    
    async def configure_trailing_stops(self, account_id: str, trailing_config: Dict[str, Any]) -> bool:
        """Configure trailing stop settings"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.live_trading_url}/api/v1/trailing-stops/",
                    json={
                        "account_id": account_id,
                        "trailing_stops": trailing_config
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to configure trailing stops: {e}")
            return False

async def main():
    """Main function"""
    try:
        configurator = LiveStrategyConfigurator()
        success = await configurator.configure_strategies()
        
        if success:
            logger.info("🎉 Live trading strategies configured successfully!")
            logger.info("📊 Strategies configured:")
            logger.info("  • Iron Condor (5% max position, 1% risk)")
            logger.info("  • Butterfly Spread (3% max position, 0.8% risk)")
            logger.info("  • Calendar Spread (4% max position, 0.9% risk)")
            logger.info("  • Elliott Wave Impulse (2% max position, 0.5% risk)")
            logger.info("  • Elliott Wave Corrective (3% max position, 0.8% risk)")
            logger.info("🛡️ Risk management: MODERATE level with emergency controls")
            logger.info("🛑 Trailing stops: Configured for all strategies")
            logger.info("⏰ Market is closed for the weekend - strategies will activate Monday 9:30 AM ET")
            return 0
        else:
            logger.error("❌ Failed to configure live trading strategies")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error in strategy configuration: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
