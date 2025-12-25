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
from .rejection_tracking_service import RejectionTrackingService

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
        self.timeout = 120  # Increased timeout for multi-timeframe analysis of multiple symbols
        
        # Initialize rejection tracking service
        self.rejection_tracker = RejectionTrackingService(db_session)
        
        # Initialize Discord notifier if webhook URL is configured
        discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.discord = DiscordNotifier(discord_webhook) if discord_webhook else None
        if self.discord:
            logger.info("✅ Discord notifications enabled")
        else:
            logger.warning("⚠️  Discord webhook not configured - notifications disabled")
        
        # Symbols will be loaded from database per strategy
        # This ensures we always use the latest configuration from the database
        self.symbols = []  # Default empty, will be populated from DB
        
        logger.info("🚀 Strategy Execution Service initialized")
        logger.info(f"   • Strategy Service URL: {self.strategy_service_url}")
        logger.info(f"   • Market Data URL: {self.market_data_url}")
        logger.info(f"   • Symbols will be loaded from database per strategy")
    
    async def _get_strategy_symbols(self, strategy_name: str, account_id: str) -> List[str]:
        """
        Load trading symbols for a strategy from the database.
        
        Args:
            strategy_name: Name of the strategy
            account_id: Account ID
            
        Returns:
            List of symbols to trade
        """
        try:
            from sqlalchemy import text
            
            result = await self.db_session.execute(
                text("""
                    SELECT symbols 
                    FROM strategy_configurations 
                    WHERE strategy_name = :strategy_name 
                    AND account_id = :account_id
                    AND enabled = true
                """),
                {"strategy_name": strategy_name, "account_id": account_id}
            )
            
            row = result.fetchone()
            if row and row[0]:
                import json
                symbols = json.loads(row[0])
                logger.info(f"📊 Loaded {len(symbols)} symbols for {strategy_name}: {symbols}")
                return symbols
            else:
                logger.warning(f"⚠️ No symbols found for {strategy_name}, using defaults")
                # Fallback to Elliott Wave top performers
                return ['SPY', 'NVDA', 'AAPL', 'QQQ', 'TSLA', 'GOOGL', 'AMD', 'META']
                
        except Exception as e:
            logger.error(f"❌ Error loading symbols from database: {e}")
            # Fallback to Elliott Wave top performers
            return ['SPY', 'NVDA', 'AAPL', 'QQQ', 'TSLA', 'GOOGL', 'AMD', 'META']
    
    def _calculate_volatility_based_dte(self, symbol: str, implied_volatility: Optional[float] = None) -> int:
        """
        Calculate optimal DTE (Days To Expiration) based on implied volatility.
        
        Uses volatility to determine how much time the trade needs to materialize:
        - High IV (>40%): Fast movers like TSLA, NVDA → 60 days
        - Medium IV (20-40%): Blue chips like MSFT, AAPL → 75 days  
        - Low IV (<20%): Slow ETFs like SPY, VOO → 90 days
        
        If IV is not available, falls back to symbol-based classification.
        
        Args:
            symbol: The trading symbol
            implied_volatility: Implied volatility as a decimal (e.g., 0.45 for 45%)
            
        Returns:
            Target DTE in days
        """
        # If we have real IV data, use it
        if implied_volatility is not None:
            if implied_volatility > 0.40:  # High volatility (>40%)
                dte = 60
                reason = f"High IV ({implied_volatility:.1%})"
            elif implied_volatility < 0.20:  # Low volatility (<20%)
                dte = 90
                reason = f"Low IV ({implied_volatility:.1%})"
            else:  # Medium volatility (20-40%)
                dte = 75
                reason = f"Medium IV ({implied_volatility:.1%})"
            
            logger.info(f"   ⏰ DTE for {symbol}: {dte} days ({reason})")
            return dte
        
        # Fallback: Symbol-based classification
        # ETFs (slow moving, diversified)
        ETF_SYMBOLS = ['SPY', 'QQQ', 'VOO', 'VTI', 'IWM', 'DIA', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY']
        
        # High volatility stocks (move fast, high beta)
        VOLATILE_SYMBOLS = ['TSLA', 'NVDA', 'AMD', 'MSTR', 'COIN', 'RIOT', 'MARA', 'PLTR', 'ARKK']
        
        if symbol in ETF_SYMBOLS:
            dte = 90
            reason = "ETF (slow mover)"
        elif symbol in VOLATILE_SYMBOLS:
            dte = 60
            reason = "Volatile stock (fast mover)"
        else:
            dte = 75
            reason = "Blue chip (moderate)"
        
        logger.info(f"   ⏰ DTE for {symbol}: {dte} days ({reason}, fallback)")
        return dte
    
    def _extract_implied_volatility_from_chain(self, option_chain: Dict[str, Any], current_price: float) -> Optional[float]:
        """
        Extract or estimate implied volatility from option chain data.
        
        Tries to:
        1. Find IV directly in the option data (if Public.com provides it)
        2. Estimate IV from ATM option premiums
        
        Args:
            option_chain: Option chain data from Public.com
            current_price: Current stock price
            
        Returns:
            Implied volatility as decimal (e.g., 0.35 for 35%), or None if unavailable
        """
        try:
            calls = option_chain.get("calls", [])
            if not calls:
                return None
            
            # Try to find IV in the first few calls
            for call in calls[:5]:
                # Check if Public.com includes IV in the response
                iv = call.get("impliedVolatility") or call.get("iv") or call.get("impliedVol")
                if iv:
                    logger.info(f"   📊 Found IV in option chain: {float(iv):.1%}")
                    return float(iv)
            
            # If no IV found, estimate from ATM option premium
            # Find the call closest to current price (ATM)
            atm_call = None
            min_diff = float('inf')
            
            for call in calls:
                instrument = call.get("instrument", {})
                occ_symbol = instrument.get("symbol", "")
                
                if occ_symbol and len(occ_symbol) >= 15:
                    try:
                        strike_str = occ_symbol[-8:]
                        strike = int(strike_str) / 1000.0
                        diff = abs(strike - current_price)
                        
                        if diff < min_diff:
                            min_diff = diff
                            atm_call = call
                    except:
                        continue
            
            if atm_call:
                # Estimate IV from ATM premium
                # Rule of thumb: ATM premium ≈ stock_price * IV * sqrt(DTE/365)
                # Rearrange: IV ≈ premium / (stock_price * sqrt(DTE/365))
                ask_price = atm_call.get("askPrice") or atm_call.get("ask") or 0.0
                
                if ask_price > 0:
                    # Assume 90 days for estimation
                    estimated_iv = ask_price / (current_price * (90/365)**0.5)
                    
                    # Sanity check: IV should be between 10% and 200%
                    if 0.10 <= estimated_iv <= 2.0:
                        logger.info(f"   📊 Estimated IV from ATM premium: {estimated_iv:.1%}")
                        return estimated_iv
            
            return None
            
        except Exception as e:
            logger.warning(f"   ⚠️  Could not extract IV from option chain: {e}")
            return None
    
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
            
            # Get strategy symbols for this account
            symbols = await self._get_strategy_symbols("MULTI_STRATEGY_ENSEMBLE", account_id)
            if not symbols:
                # Default to primary trading symbols
                symbols = ["SPY", "NVDA", "AAPL", "QQQ"]
            
            logger.info(f"📊 Analyzing {len(symbols)} symbols: {', '.join(symbols[:5])}{' ...' if len(symbols) > 5 else ''}")
            
            # Get live trading recommendations from strategy service (MULTI-TIMEFRAME)
            # Use multi-timeframe endpoint for better entry timing and trend alignment
            # Analyzes: Daily (40%) + Hourly (40%) + 15-minute (20%)
            # Note: multi-timeframe endpoint uses configured symbols when no symbol specified
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.strategy_service_url}/api/trading/recommendations/multi-timeframe",
                    params={"limit": 10}  # Will analyze all configured symbols
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
            from sqlalchemy import select, and_, or_
            position_result = await self.db_session.execute(
                select(LivePosition).where(
                    and_(
                        LivePosition.account_id == account_id,
                        LivePosition.quantity > 0,
                        or_(
                            LivePosition.status == 'OPEN',
                            LivePosition.status == 'PENDING_CLOSE'  # Include positions marked for exit
                        )
                    )
                )
            )
            all_positions = list(position_result.scalars().all())
            current_positions = {pos.symbol: pos for pos in all_positions if pos.status == 'OPEN'}
            pending_close_positions = [pos for pos in all_positions if pos.status == 'PENDING_CLOSE']
            
            logger.info(f"📊 Current positions: {list(current_positions.keys())}")
            logger.info(f"🚨 Positions marked for exit: {len(pending_close_positions)}")
            
            # First, execute exits for positions marked PENDING_CLOSE by the position monitor
            for position in pending_close_positions:
                logger.info(f"📤 Executing exit for {position.symbol} (marked by position monitor)")
                logger.info(f"   Position: {position.quantity} @ ${position.average_price}, Current: ${position.current_price}")
                
                # Create SELL order - convert Decimal to float for compatibility
                current_price_float = float(position.current_price) if position.current_price else 0.0
                
                # Parse option details from OCC symbol if it's an option
                # Format: QCOM260116C00185000 = QCOM Jan 16, 2026, $185 Call
                symbol_clean = position.symbol.replace("-OPTION", "")
                option_type = None
                strike_price = None
                expiration_date = None
                underlying_symbol = symbol_clean
                
                if len(symbol_clean) >= 15 and ('C' in symbol_clean or 'P' in symbol_clean):
                    # This is an option - parse OCC format
                    # Format: SYMBOL(variable)YYMMDDC/P########
                    # Example: QCOM260116C00185000 = QCOM Jan 16, 2026, $185 Call
                    from datetime import datetime
                    
                    # Find C or P position (should be after a 6-digit date)
                    c_pos = -1
                    p_pos = -1
                    
                    # Look for C or P that follows 6 digits (YYMMDD)
                    for i in range(len(symbol_clean) - 6):
                        if symbol_clean[i:i+6].isdigit():
                            # Found 6 consecutive digits - this is likely the date
                            if i + 6 < len(symbol_clean):
                                if symbol_clean[i+6] == 'C':
                                    c_pos = i + 6
                                    break
                                elif symbol_clean[i+6] == 'P':
                                    p_pos = i + 6
                                    break
                    
                    if c_pos > 0:
                        option_type = "CALL"
                        type_pos = c_pos
                    elif p_pos > 0:
                        option_type = "PUT"
                        type_pos = p_pos
                    else:
                        type_pos = None
                    
                    if option_type and type_pos:
                        # Extract components
                        date_str = symbol_clean[type_pos-6:type_pos]  # 6 chars before C/P = YYMMDD
                        underlying_symbol = symbol_clean[:type_pos-6]  # Everything before date
                        strike_str = symbol_clean[type_pos+1:]  # Everything after C/P
                        
                        # Parse date - keep as datetime object (not isoformat string)
                        year = 2000 + int(date_str[0:2])
                        month = int(date_str[2:4])
                        day = int(date_str[4:6])
                        expiration_date = datetime(year, month, day)
                        
                        # Parse strike
                        strike_price = float(strike_str) / 1000.0
                        
                        logger.info(f"   Parsed option: {underlying_symbol} {option_type} ${strike_price} exp {year}-{month:02d}-{day:02d}")
                
                order = OrderRequest(
                    account_id=account_id,
                    symbol=underlying_symbol,  # Just the underlying for options
                    strategy=position.strategy if position.strategy else StrategyType.MULTI_STRATEGY_ENSEMBLE,
                    legs=[TradeLeg(
                        action=TradeAction.SELL,
                        option_type=option_type,
                        strike_price=strike_price,
                        expiration_date=expiration_date,
                        quantity=position.quantity,
                        premium=current_price_float
                    )],
                    order_type=OrderType.MARKET,
                    limit_price=None,
                    time_in_force="DAY",
                    estimated_premium=current_price_float * position.quantity,
                    estimated_risk=0,
                    greeks={}
                )
                
                # Submit exit order
                result = await self.trading_service.execute_order(account_id, order)
                orders_submitted += 1
                
                if result.get("success"):
                    orders_successful += 1
                    logger.info(f"✅ Exit order submitted for {position.symbol}")
                else:
                    logger.error(f"❌ Exit order failed for {position.symbol}: {result.get('error')}")
            
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
                    elliott_wave = rec.get("elliott_wave") or {}
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
                    
                    if has_position and action in ["SELL", "STRONG_SELL", "STRONG SELL", "EXIT"] and exit_confidence >= required_confidence:
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
                            # Discord notification will be sent when order is FILLED (via order sync)
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            logger.error(f"❌ EXIT order failed for {symbol}: {error_msg}")
                    
                    # BUY logic - only if we DON'T have a position and get a buy signal
                    elif not has_position and action in ["BUY", "STRONG_BUY", "STRONG BUY"] and confidence >= min_confidence:
                        logger.info(f"📈 {symbol}: {action} signal (confidence: {confidence:.2f}, score: {score:.2f})")
                        
                        # Calculate position size based on buying power and risk
                        current_price = rec.get("current_price", 100.0)
                        
                        # Initialize position sizing service
                        sizing_service = PositionSizingService(self.db_session)
                        
                        # Calculate buying power
                        size_result = await sizing_service.calculate_position_size(
                            account_id=account_id,
                            symbol=symbol,
                            current_price=current_price,
                            signal_confidence=confidence,
                            max_position_pct=max_position_pct
                        )
                        
                        buying_power = size_result.get('buying_power', 0)
                        
                        # Skip if insufficient buying power
                        if buying_power < 100:
                            logger.warning(f"⏭️  Skipping {symbol}: Insufficient buying power (${buying_power:.2f})")
                            
                            # Log rejection
                            await self.rejection_tracker.log_rejection(
                                account_id=account_id,
                                symbol=symbol,
                                strategy="MULTI_STRATEGY_ENSEMBLE",
                                action="BUY",
                                rejection_reason=f"Insufficient buying power: ${buying_power:.2f} (minimum $100 required)",
                                rejection_category="BUYING_POWER",
                                confidence_score=confidence,
                                current_price=current_price,
                                rejection_details={
                                    "buying_power": buying_power,
                                    "minimum_required": 100,
                                    "recommendation_score": score
                                }
                            )
                            continue
                        
                        # === BULL CALL SPREAD - Budget Friendly ($100-$300) ===
                        # Buy ATM call, Sell OTM call = Defined risk, lower cost
                        from datetime import datetime, timedelta
                        from sqlalchemy import select
                        from .models import LiveTradingAccount
                        
                        # Get public_account_id for option chain queries
                        acc_result = await self.db_session.execute(
                            select(LiveTradingAccount.public_account_id).where(
                                LiveTradingAccount.account_id == account_id
                            )
                        )
                        public_account_id = acc_result.scalar_one_or_none()
                        if not public_account_id:
                            logger.warning(f"   ⚠️  No public account ID found, skipping {symbol}")
                            continue
                        
                        # STEP 1: Calculate target expiration using volatility-based DTE
                        # We'll estimate IV first (before option chain call), then adjust after we get real data
                        # For now, use symbol-based defaults until we fetch the chain
                        target_dte = self._calculate_volatility_based_dte(symbol, implied_volatility=None)
                        target_date = datetime.now() + timedelta(days=target_dte)
                        
                        # Find the 3rd Friday of the target month
                        first_of_month = target_date.replace(day=1)
                        days_to_friday = (4 - first_of_month.weekday()) % 7
                        first_friday = first_of_month + timedelta(days=days_to_friday)
                        third_friday = first_friday + timedelta(days=14)
                        
                        # If we're past the 3rd Friday, use next month's
                        if third_friday < datetime.now():
                            next_month = (target_date.month % 12) + 1
                            next_year = target_date.year + (1 if next_month == 1 else 0)
                            first_of_next = datetime(next_year, next_month, 1)
                            days_to_friday = (4 - first_of_next.weekday()) % 7
                            first_friday = first_of_next + timedelta(days=days_to_friday)
                            third_friday = first_friday + timedelta(days=14)
                        
                        target_expiration = third_friday.strftime("%Y-%m-%d")
                        
                        # STEP 2: Query option chain for that specific expiration
                        logger.info(f"   🔍 Querying option chain for {symbol} exp {target_expiration}...")
                        option_chain = await self.trading_service.public_api_client.get_option_chain(
                            public_account_id, 
                            symbol, 
                            target_expiration
                        )
                        
                        if option_chain.get("error") or not option_chain.get("calls"):
                            logger.warning(f"   ⚠️  No options available for {symbol} exp {target_expiration}")
                            # Log rejection
                            await self.rejection_tracker.log_rejection(
                                account_id=account_id,
                                symbol=symbol,
                                strategy="MULTI_STRATEGY_ENSEMBLE",
                                action="BUY",
                                rejection_reason=f"No options available for {symbol} on {target_expiration}",
                                rejection_category="NO_OPTIONS",
                                confidence_score=confidence,
                                current_price=current_price,
                                rejection_details={"error": option_chain.get("error", "No calls available"), "expiration": target_expiration}
                            )
                            continue
                        
                        # STEP 2.5: Extract IV from option chain and recalculate DTE if needed
                        implied_vol = self._extract_implied_volatility_from_chain(option_chain, current_price)
                        if implied_vol is not None:
                            # Recalculate DTE with actual IV data
                            refined_dte = self._calculate_volatility_based_dte(symbol, implied_vol)
                            if refined_dte != target_dte:
                                logger.info(f"   🔄 Adjusting DTE from {target_dte} → {refined_dte} days based on IV")
                                # Note: We already fetched the chain for target_expiration, so we'll use it
                                # In future runs, it will use the refined DTE from the start
                        
                        # STEP 3: Parse available CALLs and extract REAL prices from option chain
                        calls = option_chain.get("calls", [])
                        
                        # Build strike map with real bid/ask prices
                        strike_prices = {}  # {strike: {"bid": X, "ask": Y, "occ": "symbol"}}
                        available_strikes = []
                        
                        for call in calls:
                            # Log first call to see structure
                            if len(strike_prices) == 0:
                                logger.info(f"   🔍 Sample call data structure: {list(call.keys())[:10]}")
                            
                            instrument = call.get("instrument", {})
                            occ_symbol = instrument.get("symbol", "")
                            
                            # Extract real market prices - try multiple possible field names
                            bid_price = call.get("bidPrice") or call.get("bid") or call.get("bidprice") or 0.0
                            ask_price = call.get("askPrice") or call.get("ask") or call.get("askprice") or 0.0
                            
                            if occ_symbol and len(occ_symbol) >= 15:
                                # Parse strike from OCC symbol (last 8 digits / 1000)
                                try:
                                    strike_str = occ_symbol[-8:]
                                    strike = int(strike_str) / 1000.0
                                    available_strikes.append(strike)
                                    strike_prices[strike] = {
                                        "bid": float(bid_price) if bid_price else 0.0,
                                        "ask": float(ask_price) if ask_price else 0.0,
                                        "occ": occ_symbol
                                    }
                                except:
                                    continue
                        
                        if not available_strikes:
                            logger.warning(f"   ⚠️  No valid strike prices found for {symbol}")
                            continue
                        
                        # BULL CALL SPREAD: Buy ATM, Sell OTM
                        # Find ATM strike (at-the-money)
                        atm_strike = min(available_strikes, key=lambda s: abs(s - current_price))
                        
                        # Find OTM strike ~10% above current price for the short leg
                        target_otm = current_price * 1.10
                        otm_strikes = [s for s in available_strikes if s > current_price]
                        if not otm_strikes:
                            sell_strike = max(available_strikes)
                        else:
                            sell_strike = min(otm_strikes, key=lambda s: abs(s - target_otm))
                        
                        buy_strike = atm_strike  # Buy ATM
                        # sell_strike already set above
                        
                        expiration_date = datetime.strptime(target_expiration, "%Y-%m-%d")
                        exit_dte = 21  # Exit at 21 DTE
                        
                        logger.info(f"   ✅ Found valid option: ${buy_strike} CALL exp {target_expiration}")
                        
                        # Get Elliott Wave target price (only if pattern is recent)
                        elliott_wave = rec.get("elliott_wave") or {}
                        ew_target_price = None
                        
                        # Check if Elliott Wave pattern is recent (within 60 days)
                        waves = elliott_wave.get("waves", [])
                        if waves and isinstance(waves, list) and len(waves) > 0:
                            # Get the most recent wave timestamp
                            last_wave = waves[-1]
                            if isinstance(last_wave, dict) and "timestamp" in last_wave:
                                from datetime import datetime
                                try:
                                    wave_date = datetime.fromisoformat(last_wave["timestamp"].replace("Z", "+00:00"))
                                    days_old = (datetime.now(wave_date.tzinfo) - wave_date).days
                                    
                                    if days_old <= 60:
                                        ew_target_price = elliott_wave.get("target_price", current_price * 1.15)
                                        logger.info(f"   ✅ Using Elliott Wave target (pattern {days_old} days old)")
                                    else:
                                        logger.info(f"   ⚠️  Skipping Elliott Wave target (pattern {days_old} days old, max 60)")
                                        ew_target_price = current_price * 1.15  # Use default
                                except Exception as e:
                                    logger.warning(f"   ⚠️  Could not parse Elliott Wave date: {e}")
                                    ew_target_price = current_price * 1.15
                        
                        if ew_target_price is None:
                            ew_target_price = current_price * 1.15  # Default 15% upside
                        
                        # Get Ichimoku indicators (if available from technical analysis)
                        tech_indicators = rec.get("technical_indicators") or {}
                        ichimoku_data = tech_indicators.get("ichimoku") or {}
                        
                        # Calculate Ichimoku profit targets
                        kijun_sen = ichimoku_data.get("kijun_sen", current_price * 1.05)  # 5% default
                        senkou_b = ichimoku_data.get("senkou_span_b", current_price * 1.10)  # 10% default
                        ichimoku_target = max(kijun_sen, senkou_b)  # Use higher target
                        
                        # Use both EW and Ichimoku - take the higher target for profit
                        profit_target_price = max(ew_target_price, ichimoku_target)
                        
                        # === LONG STRANGLE - Level 2 Compatible ===
                        # BUY OTM Call + BUY OTM Put = Profit from volatility in either direction
                        # Both legs are BUY actions (no SELL) - works with Public.com Level 2!
                        
                        # STEP 1: Parse PUTs from option chain (same as calls above)
                        puts = option_chain.get("puts", [])
                        put_strike_prices = {}  # {strike: {"bid": X, "ask": Y, "occ": "symbol"}}
                        available_put_strikes = []
                        
                        for put in puts:
                            instrument = put.get("instrument", {})
                            occ_symbol = instrument.get("symbol", "")
                            
                            # Extract real market prices
                            bid_price = put.get("bid") or put.get("bidPrice") or 0.0
                            ask_price = put.get("ask") or put.get("askPrice") or 0.0
                            
                            if occ_symbol and len(occ_symbol) >= 15:
                                try:
                                    strike_str = occ_symbol[-8:]
                                    strike = int(strike_str) / 1000.0
                                    available_put_strikes.append(strike)
                                    put_strike_prices[strike] = {
                                        "bid": float(bid_price) if bid_price else 0.0,
                                        "ask": float(ask_price) if ask_price else 0.0,
                                        "occ": occ_symbol
                                    }
                                except:
                                    continue
                        
                        # STEP 2: Select OTM strikes (5-10% away from current price)
                        otm_call_strike = sell_strike  # Use the OTM call strike we already calculated (5-10% above)
                        
                        # Find OTM put strike (5-10% below current price)
                        target_put_strike = current_price * 0.93  # 7% below current (middle of 5-10% range)
                        put_strikes_below_current = sorted([s for s in available_put_strikes if s < current_price])
                        
                        if put_strikes_below_current:
                            # Find closest strike to target (5-10% OTM)
                            otm_put_strike = min(put_strikes_below_current, key=lambda x: abs(x - target_put_strike))
                        else:
                            logger.warning(f"   ⚠️  No put strikes available below current price ${current_price:.2f}")
                            # Fallback: use 7% below current price
                            otm_put_strike = round(current_price * 0.93 / 5) * 5  # Round to nearest $5
                        
                        # STEP 3: Get real market prices from option chain
                        call_data = strike_prices.get(otm_call_strike, {})
                        put_data = put_strike_prices.get(otm_put_strike, {})
                        
                        # Use ASK prices for both legs (we're buying both)
                        call_premium_per_share = call_data.get("ask", current_price * 0.035)  # Fallback to estimate
                        put_premium_per_share = put_data.get("ask", current_price * 0.025)  # Fallback to estimate
                        
                        # Total cost = Both premiums
                        call_cost_per_contract = call_premium_per_share * 100
                        put_cost_per_contract = put_premium_per_share * 100
                        total_cost_per_contract = call_cost_per_contract + put_cost_per_contract
                        
                        logger.info(f"   💰 Real Market Prices:")
                        logger.info(f"      OTM ${otm_call_strike} CALL: ask=${call_premium_per_share:.2f} (${call_cost_per_contract:.2f}/contract)")
                        logger.info(f"      OTM ${otm_put_strike} PUT: ask=${put_premium_per_share:.2f} (${put_cost_per_contract:.2f}/contract)")
                        logger.info(f"      Total Cost: ${total_cost_per_contract:.2f}/contract")
                        
                        # Calculate profit/loss metrics for Long Strangle
                        upper_breakeven = otm_call_strike + (total_cost_per_contract / 100)
                        lower_breakeven = otm_put_strike - (total_cost_per_contract / 100)
                        
                        # Max loss = Total premium paid (if stock stays between strikes)
                        max_loss_per_contract = total_cost_per_contract
                        
                        # Max profit = Unlimited (theoretically) - but estimate for 20% move
                        estimated_profit_20pct_move = max(
                            (current_price * 1.20 - otm_call_strike) * 100 - total_cost_per_contract,  # 20% upside
                            (otm_put_strike - current_price * 0.80) * 100 - total_cost_per_contract   # 20% downside
                        )
                        
                        # Calculate contracts based on buying power and risk
                        max_contracts_by_bp = int(buying_power / total_cost_per_contract)
                        max_contracts_by_risk = int(buying_power * 0.12 / max_loss_per_contract)  # Risk 12% per trade (strangles need bigger moves)
                        
                        # Use 1 contract for budget-friendly trading (typically $600-900)
                        quantity = 1
                        
                        total_cost = total_cost_per_contract * quantity
                        total_max_loss = max_loss_per_contract * quantity
                        estimated_profit_20pct = estimated_profit_20pct_move * quantity
                        
                        logger.info(f"📊 LONG STRANGLE (Volatility Play): {symbol}")
                        logger.info(f"   BUY ${otm_call_strike} CALL (OTM)")
                        logger.info(f"   BUY ${otm_put_strike} PUT (OTM)")
                        logger.info(f"   Expiration: {expiration_date.strftime('%Y-%m-%d')} (~{target_dte} DTE)")
                        logger.info(f"   Contracts: {quantity} @ ${total_cost_per_contract:.2f} = ${total_cost:.2f} total cost")
                        logger.info(f"   Breakeven Range: ${lower_breakeven:.2f} - ${upper_breakeven:.2f}")
                        logger.info(f"   Max Loss: ${total_max_loss:.2f} (if stock stays ${otm_put_strike:.2f}-${otm_call_strike:.2f})")
                        logger.info(f"   Estimated Profit (20% move): ${estimated_profit_20pct:.2f}")
                        logger.info(f"   Current Price: ${current_price:.2f}")
                        
                        # Create Long Strangle order (2 BUY legs)
                        order = OrderRequest(
                            account_id=account_id,
                            symbol=symbol,
                            strategy=StrategyType.MULTI_STRATEGY_ENSEMBLE,
                            legs=[
                                # Leg 1: BUY OTM call - Profit from upside move
                                TradeLeg(
                                    action=TradeAction.BUY,  # BUY to open long position
                                    option_type="CALL",
                                    strike_price=otm_call_strike,
                                    expiration_date=expiration_date,
                                    quantity=quantity,
                                    premium=call_premium_per_share
                                ),
                                # Leg 2: BUY OTM put - Profit from downside move
                                TradeLeg(
                                    action=TradeAction.BUY,  # BUY to open long position
                                    option_type="PUT",
                                    strike_price=otm_put_strike,
                                    expiration_date=expiration_date,
                                    quantity=quantity,
                                    premium=put_premium_per_share
                                )
                            ],
                            order_type=OrderType.MARKET,
                            limit_price=None,
                            time_in_force="DAY",
                            estimated_premium=total_cost,  # Total premium paid
                            estimated_risk=total_max_loss,  # Max loss = total premium
                            greeks={}
                        )
                        
                        # Submit order
                        result = await self.trading_service.execute_order(account_id, order)
                        orders_submitted += 1
                        
                        if result.get("success"):
                            orders_successful += 1
                            logger.info(f"✅ LONG STRANGLE submitted: {symbol}")
                            logger.info(f"   {quantity}x ${otm_call_strike} CALL + ${otm_put_strike} PUT @ ${total_cost_per_contract:.2f}")
                            logger.info(f"   Trade ID: {result.get('trade_id')}")
                            logger.info(f"   Total Cost: ${total_cost:.2f} | Est. Profit (20% move): ${estimated_profit_20pct:.2f}")
                            logger.info(f"   Breakeven: ${lower_breakeven:.2f} or ${upper_breakeven:.2f}")
                            # Discord notification will be sent when order is FILLED (via order sync)
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
                        # Log why we're skipping and track rejection
                        if has_position and action in ["SELL", "STRONG_SELL", "STRONG SELL", "EXIT"]:
                            threshold_msg = f"{required_confidence:.2f}"
                            if is_overallocated:
                                threshold_msg += " (over-allocated)"
                            logger.info(f"⏭️  Skipping {symbol}: {action} EXIT (EW: {ew_confidence:.2f}, need {threshold_msg})")
                            
                            # Log rejection
                            await self.rejection_tracker.log_rejection(
                                account_id=account_id,
                                symbol=symbol,
                                strategy="MULTI_STRATEGY_ENSEMBLE",
                                action="SELL",
                                rejection_reason=f"Exit confidence too low: {exit_confidence:.2f} (need {required_confidence:.2f})",
                                rejection_category="CONFIDENCE",
                                confidence_score=exit_confidence,
                                current_price=rec.get("current_price"),
                                rejection_details={
                                    "elliott_wave_confidence": ew_confidence,
                                    "overall_confidence": confidence,
                                    "required_confidence": required_confidence,
                                    "is_overallocated": is_overallocated
                                }
                            )
                        elif has_position:
                            logger.info(f"⏭️  Skipping {symbol}: {action} (already holding)")
                            
                            # Log rejection
                            await self.rejection_tracker.log_rejection(
                                account_id=account_id,
                                symbol=symbol,
                                strategy="MULTI_STRATEGY_ENSEMBLE",
                                action="BUY",
                                rejection_reason=f"Already holding position in {symbol}",
                                rejection_category="POSITION_EXISTS",
                                confidence_score=confidence,
                                current_price=rec.get("current_price"),
                                rejection_details={
                                    "action_signal": action,
                                    "recommendation_score": score
                                }
                            )
                        else:
                            logger.info(f"⏭️  Skipping {symbol}: {action} (confidence: {confidence:.2f})")
                            
                            # Log rejection
                            await self.rejection_tracker.log_rejection(
                                account_id=account_id,
                                symbol=symbol,
                                strategy="MULTI_STRATEGY_ENSEMBLE",
                                action=action,
                                rejection_reason=f"Signal confidence too low: {confidence:.2f} (minimum {min_confidence:.2f} required)",
                                rejection_category="CONFIDENCE",
                                confidence_score=confidence,
                                current_price=rec.get("current_price"),
                                rejection_details={
                                    "action_signal": action,
                                    "recommendation_score": score,
                                    "minimum_confidence": min_confidence
                                }
                            )
                        
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
                "message": f"Strategy execution failed: {str(e)}",
                "error": str(e),
                "orders_submitted": 0,
                "orders_successful": 0
            }
    
    async def _submit_strategy_order(self, account_id: str, symbol: str, signal) -> bool:
        """Submit an order generated by a strategy."""
        try:
            # Determine order type based on signal
            if signal.action == "BUY":
                action = "BUY"
            else:
                action = "SELL"
            
            # Calculate position size based on ensemble weights
            base_position_size = 0.20  # 20% max position size
            position_size = base_position_size * signal.confidence
            
            # Create order request for STOCK trading
            # Multi-strategy ensemble currently only supports stock trading
            # TODO: Add options support with proper strike selection and expiration
            order_data = OrderRequest(
                account_id=account_id,
                symbol=symbol,
                strategy=StrategyType.MULTI_STRATEGY_ENSEMBLE,
                legs=[TradeLeg(
                    action=action,
                    option_type=None,  # STOCK ORDER - not options
                    strike_price=None,  # Not applicable for stocks
                    expiration_date=None,  # Not applicable for stocks
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
                    "message": f"Strategy {strategy_name} not implemented",
                    "error": f"Strategy {strategy_name} not implemented",
                    "orders_submitted": 0,
                    "orders_successful": 0
                }
                
        except ValueError:
            return {
                "success": False,
                "message": f"Invalid strategy name: {strategy_name}",
                "error": f"Invalid strategy name: {strategy_name}",
                "orders_submitted": 0,
                "orders_successful": 0
            }
        except Exception as e:
            logger.error(f"❌ Error executing strategy {strategy_name}: {e}")
            return {
                "success": False,
                "message": f"Strategy execution error: {str(e)}",
                "error": str(e),
                "orders_submitted": 0,
                "orders_successful": 0
            }
