"""
Options Execution Service

Handles execution of options trades from scanner opportunities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StrategyType, TradeAction, OrderType
from .trading_service import TradingService, OrderRequest, TradeLeg
from .position_sizing_service import PositionSizingService

logger = logging.getLogger(__name__)


class OptionsExecutionService:
    """Service for executing options trades from scanner opportunities."""
    
    def __init__(self, db_session: AsyncSession, trading_service: TradingService):
        """Initialize options execution service."""
        self.db_session = db_session
        self.trading_service = trading_service
        self.sizing_service = PositionSizingService(db_session)
        
    async def execute_options_opportunities(
        self, 
        account_id: str, 
        opportunities: List[Dict[str, Any]],
        max_trades: int = 3
    ) -> Dict[str, Any]:
        """
        Execute options trades from scanner opportunities.
        
        Args:
            account_id: Account ID
            opportunities: List of options opportunities from scanner
            max_trades: Maximum number of trades to execute (default: 3)
            
        Returns:
            Execution results
        """
        logger.info(f"🔍 Processing {len(opportunities)} options opportunities for account {account_id}")
        
        orders_submitted = 0
        orders_successful = 0
        orders_failed = []
        
        # Sort by confidence (highest first)
        sorted_opps = sorted(opportunities, key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Execute top opportunities up to max_trades
        for opp in sorted_opps[:max_trades]:
            try:
                symbol = opp.get('symbol')
                confidence = opp.get('confidence', 0)
                strategy_name = opp.get('suggested_strategy', 'iron_condor')
                estimated_cost = opp.get('estimated_cost', 100)
                entry_price = opp.get('entry_price', 0)
                target_price = opp.get('target_price', 0)
                stop_loss = opp.get('stop_loss', 0)
                
                logger.info(f"📊 {symbol}: {strategy_name} opportunity (confidence: {confidence:.2%})")
                
                # Check affordability
                if not opp.get('affordable', False):
                    logger.warning(f"⏭️  Skipping {symbol}: Not affordable (${estimated_cost:.2f})")
                    continue
                
                # Skip if confidence too low
                if confidence < 0.6:
                    logger.warning(f"⏭️  Skipping {symbol}: Confidence too low ({confidence:.2%})")
                    continue
                
                # Convert strategy name to StrategyType enum
                strategy_map = {
                    'iron_condor': StrategyType.IRON_CONDOR,
                    'butterfly_spread': StrategyType.BUTTERFLY_SPREAD,
                    'calendar_spread': StrategyType.CALENDAR_SPREAD,
                    'diagonal_spread': StrategyType.DIAGONAL_SPREAD,
                    'straddle': StrategyType.STRADDLE,
                    'strangle': StrategyType.STRANGLE,
                    'covered_call': StrategyType.COVERED_CALL,
                    'cash_secured_put': StrategyType.CASH_SECURED_PUT
                }
                
                strategy_type = strategy_map.get(strategy_name, StrategyType.IRON_CONDOR)
                
                # Create options order
                # Note: This is simplified - real options orders need strike prices, expirations, etc.
                # For now, we'll create a STOCK order as a placeholder until options API is fully integrated
                
                # Calculate position size
                size_result = await self.sizing_service.calculate_position_size(
                    account_id=account_id,
                    symbol=symbol,
                    current_price=entry_price,
                    signal_confidence=confidence,
                    max_position_pct=0.15  # 15% max for options (higher risk)
                )
                
                quantity = size_result['quantity']
                
                if quantity == 0 or not size_result['can_afford']:
                    logger.warning(f"⏭️  Skipping {symbol}: Insufficient buying power")
                    continue
                
                # Create order request
                # TODO: Replace with actual options legs when Public.com API supports options
                order = OrderRequest(
                    account_id=account_id,
                    symbol=symbol,
                    strategy=strategy_type,
                    legs=[TradeLeg(
                        action=TradeAction.BUY,
                        option_type=None,  # Stock order for now
                        strike_price=None,
                        expiration_date=None,
                        quantity=quantity,
                        premium=entry_price
                    )],
                    order_type=OrderType.LIMIT,  # Use limit orders for options
                    limit_price=entry_price * 1.02,  # 2% slippage allowance
                    time_in_force="DAY",
                    estimated_premium=estimated_cost,
                    estimated_risk=estimated_cost,  # Max loss for options = premium paid
                    greeks={}
                )
                
                # Execute order
                result = await self.trading_service.execute_order(account_id, order)
                orders_submitted += 1
                
                if result.get('success'):
                    orders_successful += 1
                    logger.info(f"✅ Options order submitted: {symbol} {strategy_name} - Trade ID: {result.get('trade_id')}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    orders_failed.append({
                        'symbol': symbol,
                        'strategy': strategy_name,
                        'error': error_msg
                    })
                    logger.error(f"❌ Options order failed for {symbol}: {error_msg}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing opportunity for {symbol}: {e}")
                orders_failed.append({
                    'symbol': opp.get('symbol'),
                    'error': str(e)
                })
        
        return {
            'success': True,
            'opportunities_processed': len(sorted_opps[:max_trades]),
            'orders_submitted': orders_submitted,
            'orders_successful': orders_successful,
            'orders_failed': orders_failed,
            'message': f"Executed {orders_successful}/{orders_submitted} options orders successfully"
        }
