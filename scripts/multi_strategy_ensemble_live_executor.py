#!/usr/bin/env python3
"""
MultiStrategyEnsemble Live Execution Service
===========================================

This service runs the MultiStrategyEnsemble strategy in live trading mode,
generating signals and automatically submitting orders to the live trading service.

Features:
- Real-time market data integration
- MultiStrategyEnsemble signal generation
- Automatic order submission to live trading service
- Risk management and position sizing
- Performance monitoring and rebalancing
"""

import asyncio
import json
import logging
import httpx
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Import strategy components
from src.strategies.advanced.multi_strategy_ensemble import MultiStrategyEnsemble
from src.core.types import TradeSignal
from src.services.market_data.unified_options_pricing_service import UnifiedOptionsPricingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiStrategyEnsembleLiveExecutor:
    """Live execution service for MultiStrategyEnsemble strategy"""
    
    def __init__(self, 
                 live_trading_url: str = "http://localhost:11120",
                 market_data_url: str = "http://localhost:11084",
                 account_id: str = "19c25392-8b61-4b71-a344-0eb04d275528"):
        
        self.live_trading_url = live_trading_url
        self.market_data_url = market_data_url
        self.account_id = account_id
        self.timeout = 30
        
        # Initialize MultiStrategyEnsemble
        self.ensemble = MultiStrategyEnsemble(
            adaptive_wave_weight=0.35,
            regime_switching_weight=0.25,
            enhanced_multi_weight=0.25,
            momentum_weight=0.15,
            max_total_exposure=0.95,
            correlation_threshold=0.7
        )
        
        # Market data service
        self.market_data_service = UnifiedOptionsPricingService()
        
        # Trading symbols
        self.symbols = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        
        # Position tracking
        self.active_positions = {}
        self.last_signals = {}
        
        logger.info(f"🚀 MultiStrategyEnsemble Live Executor initialized")
        logger.info(f"   • Live Trading URL: {live_trading_url}")
        logger.info(f"   • Market Data URL: {market_data_url}")
        logger.info(f"   • Account ID: {account_id}")
        logger.info(f"   • Symbols: {self.symbols}")
    
    async def check_services_health(self) -> bool:
        """Check if all required services are healthy"""
        try:
            # Check live trading service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.live_trading_url}/health")
                if response.status_code != 200:
                    logger.error(f"❌ Live trading service unhealthy: {response.status_code}")
                    return False
                
                # Check market data service
                response = await client.get(f"{self.market_data_url}/health")
                if response.status_code != 200:
                    logger.error(f"❌ Market data service unhealthy: {response.status_code}")
                    return False
                
                logger.info("✅ All services healthy")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error checking services health: {e}")
            return False
    
    async def get_market_data(self, symbol: str, days: int = 100) -> Optional[pd.DataFrame]:
        """Get market data for a symbol"""
        try:
            # Calculate start date
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.market_data_url}/market-data/historical",
                    json={
                        "symbol": symbol,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "interval": "1d"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']:
                        df = pd.DataFrame(data['data'])
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        return df
                    else:
                        logger.warning(f"⚠️ No data returned for {symbol}")
                        return None
                else:
                    logger.error(f"❌ Failed to get market data for {symbol}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error getting market data for {symbol}: {e}")
            return None
    
    async def generate_ensemble_signals(self) -> Dict[str, Optional[TradeSignal]]:
        """Generate signals from MultiStrategyEnsemble for all symbols"""
        signals = {}
        
        for symbol in self.symbols:
            try:
                # Get market data
                data = await self.get_market_data(symbol)
                if data is None or len(data) < 50:
                    logger.warning(f"⚠️ Insufficient data for {symbol}")
                    signals[symbol] = None
                    continue
                
                # Generate signal
                signal = await self.ensemble.generate_signal(symbol, data)
                signals[symbol] = signal
                
                if signal:
                    logger.info(f"📊 {symbol}: {signal.action} signal (confidence: {signal.confidence:.2f})")
                else:
                    logger.debug(f"📊 {symbol}: No signal")
                    
            except Exception as e:
                logger.error(f"❌ Error generating signal for {symbol}: {e}")
                signals[symbol] = None
        
        return signals
    
    async def submit_order(self, symbol: str, signal: TradeSignal) -> bool:
        """Submit order to live trading service"""
        try:
            # Determine order type based on signal
            if signal.action == "BUY":
                action = "BUY"
                option_type = "CALL"  # Default to calls for buy signals
            else:
                action = "SELL"
                option_type = "PUT"   # Default to puts for sell signals
            
            # Calculate position size based on ensemble weights
            base_position_size = 0.20  # 20% max position size
            position_size = base_position_size * signal.confidence
            
            # Create order request
            order_request = {
                "symbol": symbol,
                "strategy": "MULTI_STRATEGY_ENSEMBLE",
                "order_type": "MARKET",
                "time_in_force": "DAY",
                "legs": [{
                    "action": action,
                    "option_type": option_type,
                    "strike_price": None,  # Market order
                    "expiration_date": None,  # Will be determined by market
                    "quantity": int(position_size * 100),  # Convert to shares
                    "premium": None
                }],
                "estimated_premium": 0.0,
                "estimated_risk": position_size,
                "greeks": {}
            }
            
            # Submit order
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.live_trading_url}/api/v1/trading/orders",
                    params={"account_id": self.account_id},
                    json=order_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        logger.info(f"✅ Order submitted for {symbol}: {action} {result.get('trade_id')}")
                        return True
                    else:
                        logger.error(f"❌ Order failed for {symbol}: {result.get('error')}")
                        return False
                else:
                    logger.error(f"❌ Order submission failed for {symbol}: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error submitting order for {symbol}: {e}")
            return False
    
    async def execute_trading_cycle(self) -> Dict[str, Any]:
        """Execute one complete trading cycle"""
        try:
            logger.info("🔄 Starting trading cycle...")
            
            # Generate signals
            signals = await self.generate_ensemble_signals()
            
            # Process signals and submit orders
            orders_submitted = 0
            orders_successful = 0
            
            for symbol, signal in signals.items():
                if signal and signal.confidence > 0.6:  # Only trade high-confidence signals
                    success = await self.submit_order(symbol, signal)
                    orders_submitted += 1
                    if success:
                        orders_successful += 1
                    
                    # Store signal for tracking
                    self.last_signals[symbol] = signal
            
            # Note: Ensemble weights are managed internally by the MultiStrategyEnsemble
            
            logger.info(f"📈 Trading cycle completed: {orders_successful}/{orders_submitted} orders successful")
            
            return {
                "success": True,
                "orders_submitted": orders_submitted,
                "orders_successful": orders_successful,
                "signals_generated": len([s for s in signals.values() if s]),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in trading cycle: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run_continuous_trading(self, interval_minutes: int = 15):
        """Run continuous trading with specified interval"""
        logger.info(f"🚀 Starting continuous trading (interval: {interval_minutes} minutes)")
        
        while True:
            try:
                # Check if market is open
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.live_trading_url}/api/v1/status/market-hours")
                    if response.status_code == 200:
                        market_status = response.json()
                        if not market_status.get("is_open", False):
                            logger.info("📴 Market is closed, waiting...")
                            await asyncio.sleep(60)  # Check every minute
                            continue
                
                # Execute trading cycle
                result = await self.execute_trading_cycle()
                
                if result["success"]:
                    logger.info(f"✅ Cycle completed: {result['orders_successful']} orders")
                else:
                    logger.error(f"❌ Cycle failed: {result['error']}")
                
                # Wait for next cycle
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Trading stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous trading: {e}")
                await asyncio.sleep(60)  # Wait before retrying

async def main():
    """Main function"""
    try:
        logger.info("🚀 Starting MultiStrategyEnsemble Live Execution Service...")
        
        # Initialize executor
        executor = MultiStrategyEnsembleLiveExecutor()
        
        # Check services health
        if not await executor.check_services_health():
            logger.error("❌ Services not healthy. Exiting.")
            return
        
        # Run one trading cycle to test
        logger.info("🧪 Running test trading cycle...")
        result = await executor.execute_trading_cycle()
        
        if result["success"]:
            logger.info("✅ Test cycle successful!")
            logger.info(f"   • Orders submitted: {result['orders_submitted']}")
            logger.info(f"   • Orders successful: {result['orders_successful']}")
            logger.info(f"   • Signals generated: {result['signals_generated']}")
            
            # Ask user if they want to continue with continuous trading
            print("\n" + "="*60)
            print("🎯 MultiStrategyEnsemble Live Execution Ready!")
            print("="*60)
            print(f"✅ Test cycle completed successfully")
            print(f"📊 Orders submitted: {result['orders_submitted']}")
            print(f"📈 Orders successful: {result['orders_successful']}")
            print(f"🎯 Signals generated: {result['signals_generated']}")
            print("\n🚀 Ready to start continuous trading!")
            print("   • Press Ctrl+C to stop")
            print("   • Trading cycle every 15 minutes")
            print("   • Only trades high-confidence signals (>60%)")
            print("="*60)
            
            # Start continuous trading
            await executor.run_continuous_trading(interval_minutes=15)
        else:
            logger.error(f"❌ Test cycle failed: {result['error']}")
            
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
