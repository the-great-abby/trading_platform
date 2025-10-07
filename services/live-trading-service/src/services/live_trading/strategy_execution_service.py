"""
Strategy Execution Service
========================

Handles strategy execution within the live trading service.
Runs strategies like MultiStrategyEnsemble and automatically generates orders.
"""

import asyncio
import json
import logging
import os
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StrategyType, TradeAction, LivePosition
from .trading_service import TradingService, OrderRequest, TradeLeg, OrderType
from .public_api_client import PublicAPIClient
from .risk_service import RiskService
from .position_sizing_service import PositionSizingService
from .position_service import PositionService
from .discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)


class StrategyExecutionService:
    """Service for executing trading strategies and generating orders."""
    
    def __init__(self, 
                 db_session: AsyncSession,
                 trading_service: TradingService,
                 strategy_service_url: str = "http://strategy-service.trading-system.svc.cluster.local:80",
                 market_data_url: str = "http://market-data-service.trading-system.svc.cluster.local:11084"):
        """Initialize the strategy execution service."""
        self.db_session = db_session
        self.trading_service = trading_service
        self.strategy_service_url = strategy_service_url
        self.market_data_url = market_data_url
        self.timeout = 30
        
        # Initialize Discord notifier if webhook URL is configured
        discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.discord = DiscordNotifier(discord_webhook) if discord_webhook else None
        if self.discord:
            logger.info("✅ Discord notifications enabled")
        else:
            logger.warning("⚠️  Discord webhook not configured - notifications disabled")
        
        # Trading symbols - core high-performance symbols from backtesting
        # Use only the proven high-performance symbols for live trading
        self.symbols = [
            # Core high-performance symbols (from backtesting results)
            'SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'
        ]
        
        logger.info("🚀 Strategy Execution Service initialized")
        logger.info(f"   • Strategy Service URL: {self.strategy_service_url}")
        logger.info(f"   • Market Data URL: {self.market_data_url}")
    
    async def _get_strategy_signals(self, strategy_name: str) -> Dict[str, Any]:
        """Get trading signals from the strategy service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, get the live trading configuration for MultiStrategyEnsemble
                if strategy_name == "MultiStrategyEnsemble":
                    config_response = await client.get(
                        f"{self.strategy_service_url}/api/config/multi-strategy-ensemble/live_trading"
                    )
                    if config_response.status_code == 200:
                        config_data = config_response.json()
                        logger.info(f"📋 Retrieved live trading config: {config_data['config']}")
                    else:
                        logger.warning(f"⚠️ Could not get live trading config: {config_response.status_code}")
                
                # Get recent market data for all symbols
                end_date = datetime.now()
                start_date = end_date - timedelta(days=100)
                
                response = await client.post(
                    f"{self.strategy_service_url}/api/backtest/run",
                    json={
                        "symbols": self.symbols,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "strategies": [strategy_name]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Strategy service response: {result}")
                    return result
                else:
                    logger.error(f"❌ Strategy service error: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"Strategy service returned {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"❌ Error getting strategy signals: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_multi_strategy_ensemble(self, account_id: str) -> Dict[str, Any]:
        """Execute the MultiStrategyEnsemble strategy for an account."""
        try:
            logger.info(f"🔄 Executing MultiStrategyEnsemble for account {account_id}")
            
            # Get live trading recommendations from strategy service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.strategy_service_url}/api/trading/recommendations",
                    params={"limit": 10}
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to get recommendations: HTTP {response.status_code}"
                    }
                
                strategy_result = response.json()
                logger.info(f"📊 Got {len(strategy_result.get('recommendations', []))} recommendations")
            
            if not strategy_result.get("recommendations"):
                logger.info("ℹ️  No recommendations available")
                return {
                    "success": True,
                    "orders_submitted": 0,
                    "orders_successful": 0,
                    "strategy_result": strategy_result,
                    "message": "No recommendations available"
                }
            
            # Process recommendations and generate orders
            orders_submitted = 0
            orders_successful = 0
            
            # Get current positions to check for exits
            from sqlalchemy import select, and_
            position_result = await self.db_session.execute(
                select(LivePosition).where(
                    and_(
                        LivePosition.account_id == account_id,
                        LivePosition.quantity > 0,
                        LivePosition.status == 'OPEN'
                    )
                )
            )
            current_positions = {pos.symbol: pos for pos in position_result.scalars().all()}
            logger.info(f"📊 Current positions: {list(current_positions.keys())}")
            
            # Get recommendations
            recommendations = strategy_result.get("recommendations", [])
            min_confidence = 0.50  # Minimum 50% confidence to trade
            min_exit_confidence = 0.60  # Higher confidence required for exits (normal positions)
            min_exit_confidence_overallocated = 0.50  # Lower threshold for over-allocated positions
            
            # Get risk profile to check allocation limits
            from .models import RiskProfile
            from sqlalchemy import select as sql_select
            risk_result = await self.db_session.execute(
                sql_select(RiskProfile).where(RiskProfile.account_id == account_id)
            )
            risk_profile = risk_result.scalar_one_or_none()
            max_position_pct = float(risk_profile.max_position_size) if risk_profile else 0.15
            
            # Calculate portfolio value for allocation checks
            from .models import LiveTradingAccount
            acc_result = await self.db_session.execute(
                sql_select(LiveTradingAccount.cash_balance, LiveTradingAccount.equity).where(
                    LiveTradingAccount.account_id == account_id
                )
            )
            acc_data = acc_result.fetchone()
            portfolio_value = float(acc_data.cash_balance) + float(acc_data.equity) if acc_data else 4000.0
            max_position_value = portfolio_value * max_position_pct
            
            # Process each recommendation
            for rec in recommendations:
                try:
                    symbol = rec.get("symbol")
                    action = rec.get("action")
                    confidence = rec.get("confidence", 0)
                    score = rec.get("score", 0)
                    
                    # For EXIT signals, use Elliott Wave confidence directly
                    elliott_wave = rec.get("elliott_wave", {})
                    ew_confidence = elliott_wave.get("confidence", 0)
                    ew_signal = elliott_wave.get("signal", "")
                    
                    # Check if we have a position in this symbol
                    has_position = symbol in current_positions
                    
                    # SELL/EXIT logic - if we hold the position and get a sell signal
                    # Use Elliott Wave confidence for exit decisions (more reliable)
                    exit_confidence = ew_confidence if ew_signal == "SELL" else confidence
                    
                    # Check if position is over-allocated
                    position = current_positions.get(symbol)
                    is_overallocated = False
                    if position:
                        position_value = position.quantity * float(position.average_price)
                        is_overallocated = position_value > max_position_value
                        
                        if is_overallocated:
                            logger.info(f"⚠️  {symbol} is OVER-ALLOCATED: ${position_value:.2f} > ${max_position_value:.2f} (using 50% exit threshold)")
                    
                    # Use lower threshold for over-allocated positions
                    required_confidence = min_exit_confidence_overallocated if is_overallocated else min_exit_confidence
                    
                    if has_position and action in ["SELL", "STRONG SELL", "EXIT"] and exit_confidence >= required_confidence:
                        position = current_positions[symbol]
                        logger.info(f"📉 {symbol}: {action} EXIT signal (EW confidence: {ew_confidence:.2f}, overall: {confidence:.2f})")
                        logger.info(f"   Current position: {position.quantity} shares @ avg ${position.average_price}")
                        
                        # Create SELL order for the position
                        current_price = rec.get("current_price", position.average_price)
                        
                        order = OrderRequest(
                            account_id=account_id,
                            symbol=symbol,
                            strategy=StrategyType.MULTI_STRATEGY_ENSEMBLE,
                            legs=[TradeLeg(
                                action=TradeAction.SELL,
                                option_type=None,
                                strike_price=None,
                                expiration_date=None,
                                quantity=position.quantity,  # Sell entire position
                                premium=current_price
                            )],
                            order_type=OrderType.MARKET,
                            limit_price=None,
                            time_in_force="DAY",
                            estimated_premium=current_price * position.quantity,
                            estimated_risk=0,  # Selling reduces risk
                            greeks={}
                        )
                        
                        # Submit exit order
                        result = await self.trading_service.execute_order(account_id, order)
                        orders_submitted += 1
                        
                        if result.get("success"):
                            orders_successful += 1
                            pnl = (current_price - float(position.average_price)) * position.quantity
                            logger.info(f"✅ EXIT order submitted: {symbol} SELL {position.quantity} shares @ ${current_price:.2f} (P&L: ${pnl:.2f})")
                            
                            # Send Discord notification for exit
                            if self.discord:
                                try:
                                    await self.discord.send_exit_alert(
                                        symbol=symbol,
                                        quantity=position.quantity,
                                        entry_price=float(position.average_price),
                                        exit_price=current_price,
                                        pnl=pnl,
                                        confidence=ew_confidence,
                                        status="SUBMITTED"
                                    )
                                except Exception as e:
                                    logger.error(f"Discord notification failed: {e}")
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            logger.error(f"❌ EXIT order failed for {symbol}: {error_msg}")
                    
                    # BUY logic - only if we DON'T have a position and get a buy signal
                    elif not has_position and action in ["BUY", "STRONG BUY"] and confidence >= min_confidence:
                        logger.info(f"📈 {symbol}: {action} signal (confidence: {confidence:.2f}, score: {score:.2f})")
                        
                        # Calculate position size based on buying power and risk
                        current_price = rec.get("current_price", 100.0)
                        
                        # Initialize position sizing service
                        sizing_service = PositionSizingService(self.db_session)
                        
                        # Calculate optimal position size
                        size_result = await sizing_service.calculate_position_size(
                            account_id=account_id,
                            symbol=symbol,
                            current_price=current_price,
                            signal_confidence=confidence,
                            max_position_pct=max_position_pct
                        )
                        
                        quantity = size_result["quantity"]
                        estimated_cost = size_result["estimated_cost"]
                        
                        # Skip if we can't afford even 1 share
                        if quantity == 0 or not size_result["can_afford"]:
                            logger.warning(f"⏭️  Skipping {symbol}: Insufficient buying power (${size_result.get('buying_power', 0):.2f})")
                            continue
                        
                        order = OrderRequest(
                            account_id=account_id,
                            symbol=symbol,
                            strategy=StrategyType.MULTI_STRATEGY_ENSEMBLE,
                            legs=[TradeLeg(
                                action=TradeAction.BUY,
                                option_type=None,  # Stock trade
                                strike_price=None,
                                expiration_date=None,
                                quantity=quantity,  # Dynamic sizing based on buying power
                                premium=current_price  # Stock price as premium
                            )],
                            order_type=OrderType.MARKET,
                            limit_price=None,
                            time_in_force="DAY",
                            estimated_premium=estimated_cost,  # Total cost
                            estimated_risk=estimated_cost * 0.10,  # 10% risk estimate
                            greeks={}
                        )
                        
                        # Submit order
                        result = await self.trading_service.execute_order(account_id, order)
                        orders_submitted += 1
                        
                        if result.get("success"):
                            orders_successful += 1
                            logger.info(f"✅ Order submitted: {symbol} BUY 1 share - Trade ID: {result.get('trade_id')}")
                            
                            # Send Discord notification for BUY
                            if self.discord:
                                try:
                                    await self.discord.send_trade_alert(
                                        symbol=symbol,
                                        action="BUY",
                                        quantity=1,
                                        price=current_price,
                                        status="SUBMITTED",
                                        trade_id=result.get('trade_id', 'UNKNOWN'),
                                        confidence=confidence,
                                        reason=f"{action} signal (score: {score:.2f})"
                                    )
                                except Exception as e:
                                    logger.error(f"Discord notification failed: {e}")
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            details = result.get('details', [])
                            warnings = result.get('warnings', [])
                            logger.error(f"❌ Order failed for {symbol}: {error_msg}")
                            if details:
                                logger.error(f"   Details: {', '.join(details)}")
                            if warnings:
                                logger.warning(f"   Warnings: {', '.join(warnings)}")
                    else:
                        # Log why we're skipping
                        if has_position and action in ["SELL", "STRONG SELL", "EXIT"]:
                            threshold_msg = f"{required_confidence:.2f}"
                            if is_overallocated:
                                threshold_msg += " (over-allocated)"
                            logger.info(f"⏭️  Skipping {symbol}: {action} EXIT (EW: {ew_confidence:.2f}, need {threshold_msg})")
                        elif has_position:
                            logger.info(f"⏭️  Skipping {symbol}: {action} (already holding)")
                        else:
                            logger.info(f"⏭️  Skipping {symbol}: {action} (confidence: {confidence:.2f})")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing recommendation: {e}")
            
            return {
                "success": True,
                "orders_submitted": orders_submitted,
                "orders_successful": orders_successful,
                "strategy_result": strategy_result,
                "message": f"MultiStrategyEnsemble executed: {orders_successful}/{orders_submitted} orders successful"
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing MultiStrategyEnsemble: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _submit_strategy_order(self, account_id: str, symbol: str, signal) -> bool:
        """Submit an order generated by a strategy."""
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
            order_data = OrderRequest(
                account_id=account_id,
                symbol=symbol,
                strategy=StrategyType.MULTI_STRATEGY_ENSEMBLE,
                legs=[TradeLeg(
                    action=action,
                    option_type=option_type,
                    strike_price=None,  # Market order
                    expiration_date=None,  # Will be determined by market
                    quantity=int(position_size * 100),  # Convert to shares
                    premium=None
                )],
                order_type=OrderType.MARKET,
                limit_price=None,
                time_in_force="DAY",
                estimated_premium=0.0,
                estimated_risk=position_size,
                greeks={}
            )
            
            # Execute order through trading service
            result = await self.trading_service.execute_order(account_id, order_data)
            
            if result.get("success"):
                logger.info(f"✅ Order submitted for {symbol}: {action} {result.get('trade_id')}")
                return True
            else:
                logger.error(f"❌ Order failed for {symbol}: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error submitting order for {symbol}: {e}")
            return False
    
    async def execute_strategy(self, account_id: str, strategy_name: str) -> Dict[str, Any]:
        """Execute a specific strategy by name."""
        try:
            strategy_type = StrategyType(strategy_name)
            
            if strategy_type == StrategyType.MULTI_STRATEGY_ENSEMBLE:
                return await self.execute_multi_strategy_ensemble(account_id)
            else:
                return {
                    "success": False,
                    "error": f"Strategy {strategy_name} not implemented"
                }
                
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid strategy name: {strategy_name}"
            }
        except Exception as e:
            logger.error(f"❌ Error executing strategy {strategy_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
