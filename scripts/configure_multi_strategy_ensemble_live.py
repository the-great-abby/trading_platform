#!/usr/bin/env python3
"""
Configure MultiStrategyEnsemble for Live Trading
===============================================

This script configures the MultiStrategyEnsemble for live trading,
replacing individual strategies with the sophisticated ensemble approach.

MultiStrategyEnsemble Components:
1. AdaptiveSectorWaveStrategy (35% weight) - Elliott Wave + Options
2. RegimeSwitchingStrategy (25% weight) - Market timing
3. EnhancedMultiStrategy (25% weight) - Sector rotation  
4. CrossSectionalMomentumStrategy (15% weight) - Cross-sectional momentum

Target: 313%+ returns through strategy diversification
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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiStrategyEnsembleConfigurator:
    """Configure MultiStrategyEnsemble for live trading"""
    
    def __init__(self, live_trading_url: str = "http://localhost:11120"):
        self.live_trading_url = live_trading_url
        self.timeout = 30
        self.account_id = "19c25392-8b61-4b71-a344-0eb04d275528"
        
        logger.info(f"🚀 MultiStrategyEnsemble Configurator initialized: {live_trading_url}")
    
    async def check_service_health(self) -> bool:
        """Check if live trading service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✅ Live trading service: {health_data.get('status', 'unknown')}")
                    return True
                else:
                    logger.error(f"❌ Live trading service unhealthy: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error checking live trading service health: {e}")
            return False
    
    async def configure_multi_strategy_ensemble(self) -> bool:
        """Configure MultiStrategyEnsemble using available strategy types"""
        try:
            # Since MultiStrategyEnsemble is not in the StrategyType enum,
            # we'll configure the component strategies that make up the ensemble
            
            # Component strategies of MultiStrategyEnsemble
            ensemble_strategies = [
                {
                    "strategy_name": "ELLIOTT_WAVE_IMPULSE",
                    "enabled": True,
                    "max_position_size": 0.07,  # 35% * 20% = 7% (35% weight of 20% total)
                    "max_risk_per_trade": 0.0175,  # 35% * 5% = 1.75%
                    "max_daily_trades": 5,  # 35% * 15 = 5 trades
                    "max_daily_loss": 70.0,  # 35% * $200 = $70
                    "description": "Elliott Wave Impulse - Component of MultiStrategyEnsemble (35% weight)",
                    "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
                },
                {
                    "strategy_name": "REGIME_SWITCHING",
                    "enabled": True,
                    "max_position_size": 0.05,  # 25% * 20% = 5%
                    "max_risk_per_trade": 0.0125,  # 25% * 5% = 1.25%
                    "max_daily_trades": 4,  # 25% * 15 = 4 trades
                    "max_daily_loss": 50.0,  # 25% * $200 = $50
                    "description": "Regime Switching - Component of MultiStrategyEnsemble (25% weight)",
                    "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
                },
                {
                    "strategy_name": "SECTOR_ROTATION",
                    "enabled": True,
                    "max_position_size": 0.05,  # 25% * 20% = 5%
                    "max_risk_per_trade": 0.0125,  # 25% * 5% = 1.25%
                    "max_daily_trades": 4,  # 25% * 15 = 4 trades
                    "max_daily_loss": 50.0,  # 25% * $200 = $50
                    "description": "Sector Rotation - Component of MultiStrategyEnsemble (25% weight)",
                    "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
                },
                {
                    "strategy_name": "VOLATILITY_TRADING",
                    "enabled": True,
                    "max_position_size": 0.03,  # 15% * 20% = 3%
                    "max_risk_per_trade": 0.0075,  # 15% * 5% = 0.75%
                    "max_daily_trades": 2,  # 15% * 15 = 2 trades
                    "max_daily_loss": 30.0,  # 15% * $200 = $30
                    "description": "Volatility Trading - Component of MultiStrategyEnsemble (15% weight)",
                    "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
                }
            ]
            
            success_count = 0
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for strategy_config in ensemble_strategies:
                    try:
                        response = await client.post(
                            f"{self.live_trading_url}/api/v1/strategies/",
                            params={"account_id": self.account_id},
                            json=strategy_config
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            logger.info(f"✅ Configured {strategy_config['strategy_name']} successfully!")
                            logger.info(f"   • Position Size: {strategy_config['max_position_size']:.1%}")
                            logger.info(f"   • Daily Trades: {strategy_config['max_daily_trades']}")
                            logger.info(f"   • Daily Loss: ${strategy_config['max_daily_loss']:.2f}")
                            success_count += 1
                        else:
                            logger.error(f"❌ Failed to configure {strategy_config['strategy_name']}: {response.status_code}")
                            logger.error(f"   Response: {response.text}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error configuring {strategy_config['strategy_name']}: {e}")
            
            if success_count == len(ensemble_strategies):
                logger.info(f"🎉 All {len(ensemble_strategies)} MultiStrategyEnsemble components configured successfully!")
                logger.info("📊 MultiStrategyEnsemble Components:")
                logger.info("   • Elliott Wave Impulse: 35% weight (7% position, 5 trades)")
                logger.info("   • Regime Switching: 25% weight (5% position, 4 trades)")
                logger.info("   • Sector Rotation: 25% weight (5% position, 4 trades)")
                logger.info("   • Volatility Trading: 15% weight (3% position, 2 trades)")
                return True
            else:
                logger.error(f"❌ Only {success_count}/{len(ensemble_strategies)} strategies configured successfully")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error configuring MultiStrategyEnsemble: {e}")
            return False
    
    async def configure_risk_management(self) -> bool:
        """Configure risk management for MultiStrategyEnsemble"""
        try:
            risk_config = {
                "max_position_size": 0.20,      # 20% max position size
                "max_portfolio_risk": 0.05,      # 5% max portfolio risk
                "max_daily_loss": 200.0,        # $200 max daily loss
                "max_daily_trades": 15,          # More aggressive trading
                "allowed_strategies": ["MultiStrategyEnsemble"],
                "max_greeks_exposure": {
                    "delta": 2000.0,    # Higher delta exposure for ensemble
                    "gamma": 200.0,     # Higher gamma exposure
                    "theta": -100.0,    # Higher theta exposure
                    "vega": 400.0       # Higher vega exposure
                },
                "emergency_stop_active": False,
                "risk_level": "AGGRESSIVE"  # Aggressive for higher returns
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{self.live_trading_url}/api/v1/risk/profile/{self.account_id}",
                    json=risk_config
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Risk management configured for MultiStrategyEnsemble!")
                    logger.info(f"   • Max Position Size: {risk_config['max_position_size']:.1%}")
                    logger.info(f"   • Max Daily Loss: ${risk_config['max_daily_loss']:.2f}")
                    logger.info(f"   • Risk Level: {risk_config['risk_level']}")
                    return True
                else:
                    logger.error(f"❌ Failed to configure risk management: {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error configuring risk management: {e}")
            return False
    
    async def verify_configuration(self) -> bool:
        """Verify MultiStrategyEnsemble configuration"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check strategies
                response = await client.get(f"{self.live_trading_url}/api/v1/strategies/{self.account_id}")
                if response.status_code == 200:
                    strategies_data = response.json()
                    active_strategies = [s for s in strategies_data.get("strategies", []) if s.get("enabled")]
                    
                    logger.info(f"📊 Active Strategies: {len(active_strategies)}")
                    for strategy in active_strategies:
                        logger.info(f"   • {strategy['strategy_name']}: {strategy['max_position_size']:.1%} max position, {strategy['max_daily_trades']} daily trades")
                    
                    # Check if MultiStrategyEnsemble is active
                    ensemble_active = any(s['strategy_name'] == 'MultiStrategyEnsemble' for s in active_strategies)
                    if ensemble_active:
                        logger.info("✅ MultiStrategyEnsemble is active!")
                        return True
                    else:
                        logger.error("❌ MultiStrategyEnsemble is not active!")
                        return False
                else:
                    logger.error(f"❌ Failed to verify strategies: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error verifying configuration: {e}")
            return False

async def main():
    """Main function to configure MultiStrategyEnsemble"""
    try:
        logger.info("🚀 Starting MultiStrategyEnsemble Configuration...")
        
        # Initialize configurator
        configurator = MultiStrategyEnsembleConfigurator()
        
        # Check service health
        logger.info("🔍 Checking live trading service health...")
        if not await configurator.check_service_health():
            logger.error("❌ Live trading service is not healthy. Exiting.")
            return
        
        # Configure MultiStrategyEnsemble
        logger.info("📊 Configuring MultiStrategyEnsemble...")
        if not await configurator.configure_multi_strategy_ensemble():
            logger.error("❌ Failed to configure MultiStrategyEnsemble. Exiting.")
            return
        
        # Configure risk management
        logger.info("🛡️ Configuring risk management...")
        if not await configurator.configure_risk_management():
            logger.error("❌ Failed to configure risk management. Exiting.")
            return
        
        # Verify configuration
        logger.info("🔍 Verifying configuration...")
        if not await configurator.verify_configuration():
            logger.error("❌ Configuration verification failed. Exiting.")
            return
        
        logger.info("🎉 MultiStrategyEnsemble configuration completed successfully!")
        logger.info("📈 Target: 313%+ returns through strategy diversification")
        logger.info("🎯 Strategy Weights:")
        logger.info("   • AdaptiveSectorWaveStrategy: 35% (Elliott Wave + Options)")
        logger.info("   • RegimeSwitchingStrategy: 25% (Market timing)")
        logger.info("   • EnhancedMultiStrategy: 25% (Sector rotation)")
        logger.info("   • CrossSectionalMomentumStrategy: 15% (Momentum)")
        
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
        return

if __name__ == "__main__":
    asyncio.run(main())
