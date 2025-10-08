"""
Order Synchronization Service

Polls Public.com for order status and updates database when orders are filled.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from .models import LiveTrade, TradeStatus
from .public_api_client import PublicAPIClient
from .discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)


class OrderSyncService:
    """Service for synchronizing order status with Public.com."""
    
    def __init__(self, db_session: AsyncSession, public_api_client: PublicAPIClient):
        """Initialize the order sync service."""
        self.db_session = db_session
        self.public_api_client = public_api_client
        
        # Initialize Discord notifier if webhook URL is configured
        discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.discord = DiscordNotifier(discord_webhook) if discord_webhook else None
        if self.discord:
            logger.info("✅ Discord notifications enabled for order fills")
        else:
            logger.warning("⚠️  Discord webhook not configured - fill notifications disabled")
    
    async def sync_pending_orders(self, account_id: str) -> Dict[str, Any]:
        """
        Sync all pending orders for an account with Public.com.
        
        Args:
            account_id: Internal account ID
            
        Returns:
            Summary of sync results
        """
        try:
            # Get all pending orders from database
            result = await self.db_session.execute(
                select(LiveTrade).where(
                    LiveTrade.account_id == account_id,
                    LiveTrade.status == TradeStatus.PENDING
                )
            )
            pending_trades = result.scalars().all()
            
            if not pending_trades:
                logger.info(f"No pending orders to sync for account {account_id}")
                return {"synced": 0, "filled": 0, "still_pending": 0}
            
            logger.info(f"Found {len(pending_trades)} pending orders to sync")
            
            synced_count = 0
            filled_count = 0
            still_pending_count = 0
            
            # Get public_account_id for API calls
            from .models import LiveTradingAccount
            acc_result = await self.db_session.execute(
                select(LiveTradingAccount.public_account_id).where(
                    LiveTradingAccount.account_id == account_id
                ).limit(1)
            )
            public_account_id = acc_result.scalar_one_or_none()
            
            if not public_account_id:
                raise Exception(f"Public account ID not found for {account_id}")
            
            # Sync each pending order
            for trade in pending_trades:
                try:
                    # Skip if we don't have a real Public.com order ID yet
                    if not trade.public_order_id or trade.public_order_id.startswith("TEMP_"):
                        logger.warning(f"Trade {trade.trade_id} has temporary order ID, skipping sync")
                        still_pending_count += 1
                        continue
                    
                    # Get order status from Public.com
                    order_status = await self.public_api_client.get_order_status(
                        public_account_id, 
                        trade.public_order_id
                    )
                    
                    # Update trade based on status
                    updated = await self._update_trade_from_status(trade, order_status)
                    
                    if updated:
                        synced_count += 1
                        if trade.status == TradeStatus.FILLED:
                            filled_count += 1
                        elif trade.status == TradeStatus.PENDING:
                            still_pending_count += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing order {trade.public_order_id}: {str(e)}")
                    still_pending_count += 1
            
            # Commit all updates
            await self.db_session.commit()
            
            logger.info(f"Order sync complete: {synced_count} synced, {filled_count} filled, {still_pending_count} still pending")
            
            return {
                "synced": synced_count,
                "filled": filled_count,
                "still_pending": still_pending_count,
                "total_pending": len(pending_trades)
            }
            
        except Exception as e:
            logger.error(f"Error syncing pending orders: {str(e)}")
            await self.db_session.rollback()
            raise
    
    async def _update_trade_from_status(self, trade: LiveTrade, order_status: Dict[str, Any]) -> bool:
        """
        Update trade record based on Public.com order status.
        
        Args:
            trade: LiveTrade database record
            order_status: Order status from Public.com API
            
        Returns:
            True if trade was updated, False otherwise
        """
        status = order_status.get("status", "").upper()
        updated = False
        
        logger.info(f"Processing order {trade.public_order_id} with status: {status}")
        
        # Map Public.com status to our status
        if status == "FILLED":
            trade.status = TradeStatus.FILLED
            trade.filled_quantity = int(order_status.get("filledQuantity", 0))
            trade.remaining_quantity = 0
            
            # Update price if we have average fill price
            if "averagePrice" in order_status:
                trade.price = float(order_status["averagePrice"])
                trade.total_amount = trade.price * trade.filled_quantity
            
            # Set filled timestamp
            if "updatedAt" in order_status or "filledAt" in order_status:
                filled_time = order_status.get("filledAt") or order_status.get("updatedAt")
                if filled_time:
                    trade.filled_at = datetime.fromisoformat(filled_time.replace('Z', '+00:00'))
            
            logger.info(f"✅ Order {trade.public_order_id} FILLED: {trade.symbol} {trade.filled_quantity} @ ${trade.price}")
            updated = True
            
            # Send Discord notification for filled order
            if self.discord:
                try:
                    await self.discord.send_trade_alert(
                        symbol=trade.symbol,
                        action=trade.action.value if hasattr(trade.action, 'value') else str(trade.action),
                        quantity=trade.filled_quantity,
                        price=float(trade.price) if trade.price else 0.0,
                        status="FILLED",
                        trade_id=str(trade.trade_id),
                        reason=f"Order filled via {trade.strategy}"
                    )
                    logger.info(f"📢 Discord notification sent for filled order: {trade.symbol}")
                except Exception as e:
                    logger.error(f"Failed to send Discord notification: {e}")
            
        elif status == "PARTIALLY_FILLED":
            trade.filled_quantity = int(order_status.get("filledQuantity", 0))
            trade.remaining_quantity = trade.quantity - trade.filled_quantity
            
            if "averagePrice" in order_status:
                trade.price = float(order_status["averagePrice"])
            
            logger.info(f"📊 Order {trade.public_order_id} PARTIALLY FILLED: {trade.filled_quantity}/{trade.quantity}")
            updated = True
            
        elif status == "CANCELLED" or status == "CANCELED":
            trade.status = TradeStatus.CANCELLED
            trade.cancelled_at = datetime.utcnow()
            
            logger.info(f"❌ Order {trade.public_order_id} CANCELLED")
            updated = True
            
        elif status == "REJECTED":
            trade.status = TradeStatus.REJECTED
            trade.rejection_reason = order_status.get("rejectReason", "Order rejected by broker")
            
            logger.error(f"❌ Order {trade.public_order_id} REJECTED: {trade.rejection_reason}")
            updated = True
            
        elif status in ["PENDING", "OPEN", "SUBMITTED", "ACCEPTED"]:
            # Still pending, no update needed
            logger.debug(f"⏳ Order {trade.public_order_id} still {status}")
            pass
        
        if updated:
            trade.updated_at = datetime.utcnow()
        
        return updated
    
    async def sync_single_order(self, account_id: str, trade_id: str) -> Dict[str, Any]:
        """
        Sync a single order by trade ID.
        
        Args:
            account_id: Internal account ID
            trade_id: Trade ID to sync
            
        Returns:
            Updated trade information
        """
        try:
            # Get the trade
            result = await self.db_session.execute(
                select(LiveTrade).where(
                    LiveTrade.trade_id == trade_id,
                    LiveTrade.account_id == account_id
                )
            )
            trade = result.scalar_one_or_none()
            
            if not trade:
                raise Exception(f"Trade {trade_id} not found")
            
            if not trade.public_order_id or trade.public_order_id.startswith("TEMP_"):
                raise Exception(f"Trade has temporary order ID: {trade.public_order_id}")
            
            # Get public_account_id
            from .models import LiveTradingAccount
            acc_result = await self.db_session.execute(
                select(LiveTradingAccount.public_account_id).where(
                    LiveTradingAccount.account_id == account_id
                ).limit(1)
            )
            public_account_id = acc_result.scalar_one_or_none()
            
            # Get order status from Public.com
            order_status = await self.public_api_client.get_order_status(
                public_account_id,
                trade.public_order_id
            )
            
            # Update trade
            await self._update_trade_from_status(trade, order_status)
            await self.db_session.commit()
            
            return {
                "trade_id": str(trade.trade_id),
                "symbol": trade.symbol,
                "status": trade.status.value,
                "filled_quantity": trade.filled_quantity,
                "price": float(trade.price) if trade.price else None
            }
            
        except Exception as e:
            logger.error(f"Error syncing single order: {str(e)}")
            await self.db_session.rollback()
            raise


    async def recalculate_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Recalculate account balance based on filled trades.
        
        This provides an estimated balance since Public.com doesn't expose
        direct balance API. Useful for keeping track after orders fill.
        
        Args:
            account_id: Internal account ID
            
        Returns:
            Updated balance information
        """
        try:
            from sqlalchemy import text
            
            # Get all FILLED trades
            result = await self.db_session.execute(text("""
                SELECT 
                    symbol,
                    action,
                    quantity,
                    price,
                    total_amount
                FROM live_trades
                WHERE account_id = :account_id
                  AND status = 'FILLED'
                ORDER BY created_at
            """), {"account_id": account_id})
            
            filled_trades = result.fetchall()
            
            # Calculate positions and cash flow
            positions = {}
            cash_flow = 0.0
            
            for symbol, action, quantity, price, total_amount in filled_trades:
                qty = float(quantity)
                prc = float(price)
                amt = float(total_amount) if total_amount else qty * prc
                
                if action == "BUY":
                    # Buying costs cash
                    cash_flow -= amt
                    if symbol in positions:
                        # Average cost basis
                        old_qty = positions[symbol]["quantity"]
                        old_cost = positions[symbol]["total_cost"]
                        positions[symbol]["quantity"] = old_qty + qty
                        positions[symbol]["total_cost"] = old_cost + amt
                        positions[symbol]["avg_price"] = (old_cost + amt) / (old_qty + qty)
                    else:
                        positions[symbol] = {
                            "quantity": qty,
                            "avg_price": prc,
                            "total_cost": amt
                        }
                elif action == "SELL":
                    # Selling gives cash
                    cash_flow += amt
                    if symbol in positions:
                        positions[symbol]["quantity"] -= qty
                        # If position closed, remove it
                        if positions[symbol]["quantity"] <= 0:
                            del positions[symbol]
            
            # Calculate equity (current value of positions)
            # Note: We don't have real-time prices, so this is an estimate
            equity = sum(pos["total_cost"] for pos in positions.values())
            
            # Update account balance in database
            # Note: Starting balance needs to be set manually once
            # For cash-only accounts, buying_power = cash_balance
            await self.db_session.execute(text("""
                UPDATE live_trading_accounts
                SET equity = :equity,
                    buying_power = cash_balance,
                    updated_at = NOW()
                WHERE account_id = :account_id
            """), {
                "equity": equity,
                "account_id": account_id
            })
            
            await self.db_session.commit()
            
            logger.info(f"📊 Balance recalculated:")
            logger.info(f"   Positions: {len(positions)}")
            logger.info(f"   Equity (estimated): ${equity:.2f}")
            logger.info(f"   Cash flow from trades: ${cash_flow:.2f}")
            
            return {
                "success": True,
                "positions_count": len(positions),
                "equity": equity,
                "cash_flow": cash_flow,
                "positions": list(positions.keys())
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to recalculate balance: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
