"""
Order Import Service - Import existing Public.com orders into the database

This service is used when you've made trades directly on Public.com
and need to import them into your local database for tracking.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import LiveTrade, TradeStatus, TradeAction, LiveTradingAccount
from .public_api_client import PublicAPIClient

logger = logging.getLogger(__name__)


class OrderImportService:
    """Service for importing existing Public.com orders into the database."""
    
    def __init__(self, db_session: AsyncSession, public_api_client: PublicAPIClient):
        self.db_session = db_session
        self.public_api_client = public_api_client
    
    async def import_recent_orders(
        self, 
        account_id: str, 
        days: int = 7,
        import_filled_only: bool = False
    ) -> Dict[str, Any]:
        """
        Import recent orders from Public.com into the database.
        
        Args:
            account_id: Internal account ID
            days: How many days back to import (default: 7)
            import_filled_only: Only import filled orders (default: False)
        
        Returns:
            Dict with import statistics
        """
        logger.info(f"🔄 Starting order import for account {account_id} (last {days} days)")
        
        # Get public_account_id
        acc_result = await self.db_session.execute(
            select(LiveTradingAccount.public_account_id).where(
                LiveTradingAccount.account_id == account_id
            ).limit(1)
        )
        public_account_id = acc_result.scalar_one_or_none()
        
        if not public_account_id:
            raise Exception(f"Public account ID not found for {account_id}")
        
        # Get existing orders from database to avoid duplicates
        existing_result = await self.db_session.execute(
            select(LiveTrade.public_order_id).where(
                LiveTrade.account_id == account_id
            )
        )
        existing_order_ids = set(row[0] for row in existing_result.fetchall() if row[0] and not row[0].startswith('TEMP_'))
        
        logger.info(f"Found {len(existing_order_ids)} existing orders in database")
        
        # Fetch recent orders from Public.com
        try:
            public_orders = await self.public_api_client.get_recent_orders(
                public_account_id, 
                days=days
            )
        except Exception as e:
            logger.error(f"Failed to fetch orders from Public.com: {e}")
            raise
        
        logger.info(f"Fetched {len(public_orders)} orders from Public.com")
        
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        
        for order in public_orders:
            order_id = order.get('orderId')
            status = order.get('status', '').upper()
            
            # Skip if already in database
            if order_id in existing_order_ids:
                logger.debug(f"Skipping {order_id} - already in database")
                skipped_count += 1
                continue
            
            # Skip if not filled (if import_filled_only is True)
            if import_filled_only and status != 'FILLED':
                logger.debug(f"Skipping {order_id} - not filled (status: {status})")
                skipped_count += 1
                continue
            
            try:
                # Create database record from Public.com order
                trade = await self._create_trade_from_public_order(account_id, order)
                self.db_session.add(trade)
                imported_count += 1
                
                logger.info(
                    f"✅ Imported: {order.get('symbol')} {order.get('side')} "
                    f"{order.get('quantity')} @ {status} - Order ID: {order_id}"
                )
                
            except Exception as e:
                logger.error(f"❌ Failed to import order {order_id}: {e}")
                failed_count += 1
                continue
        
        # Commit all imports
        await self.db_session.commit()
        
        result = {
            "imported": imported_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total_from_public": len(public_orders),
            "days": days
        }
        
        logger.info(
            f"Import complete: {imported_count} imported, "
            f"{skipped_count} skipped, {failed_count} failed"
        )
        
        return result
    
    async def import_specific_order(
        self, 
        account_id: str, 
        public_order_id: str
    ) -> Dict[str, Any]:
        """
        Import a specific order by its Public.com order ID.
        
        Args:
            account_id: Internal account ID
            public_order_id: The orderId from Public.com
        
        Returns:
            Dict with import result
        """
        logger.info(f"🔄 Importing specific order {public_order_id}")
        
        # Check if already exists
        existing = await self.db_session.execute(
            select(LiveTrade).where(
                LiveTrade.account_id == account_id,
                LiveTrade.public_order_id == public_order_id
            )
        )
        
        if existing.scalar_one_or_none():
            return {
                "success": False,
                "message": f"Order {public_order_id} already exists in database",
                "public_order_id": public_order_id
            }
        
        # Get public_account_id
        acc_result = await self.db_session.execute(
            select(LiveTradingAccount.public_account_id).where(
                LiveTradingAccount.account_id == account_id
            ).limit(1)
        )
        public_account_id = acc_result.scalar_one_or_none()
        
        # Fetch order from Public.com
        try:
            order = await self.public_api_client.get_order_status(
                public_account_id, 
                public_order_id
            )
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to fetch order from Public.com: {str(e)}",
                "public_order_id": public_order_id
            }
        
        # Create database record
        try:
            trade = await self._create_trade_from_public_order(account_id, order)
            self.db_session.add(trade)
            await self.db_session.commit()
            
            return {
                "success": True,
                "message": f"Order imported successfully",
                "public_order_id": public_order_id,
                "trade_id": str(trade.trade_id),
                "symbol": trade.symbol,
                "status": trade.status.value
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create database record: {str(e)}",
                "public_order_id": public_order_id
            }
    
    async def _create_trade_from_public_order(
        self, 
        account_id: str, 
        order: Dict[str, Any]
    ) -> LiveTrade:
        """
        Create a LiveTrade database record from a Public.com order.
        
        Args:
            account_id: Internal account ID
            order: Order data from Public.com API
        
        Returns:
            LiveTrade instance
        """
        # Map Public.com status to our status enum
        status_mapping = {
            'FILLED': TradeStatus.FILLED,
            'PARTIALLY_FILLED': TradeStatus.PARTIALLY_FILLED,
            'PENDING': TradeStatus.PENDING,
            'SUBMITTED': TradeStatus.SUBMITTED,
            'CANCELLED': TradeStatus.CANCELLED,
            'REJECTED': TradeStatus.REJECTED,
            'EXPIRED': TradeStatus.EXPIRED
        }
        
        public_status = order.get('status', 'PENDING').upper()
        status = status_mapping.get(public_status, TradeStatus.PENDING)
        
        # Map side to action
        side = order.get('side', 'BUY').upper()
        action = TradeAction.BUY if side == 'BUY' else TradeAction.SELL
        
        # Extract other fields
        symbol = order.get('symbol', '').upper()
        quantity = int(float(order.get('quantity', 0)))
        filled_quantity = int(float(order.get('filledQuantity', 0)))
        remaining_quantity = quantity - filled_quantity
        
        # Price handling
        price = None
        if 'averagePrice' in order and order['averagePrice']:
            price = Decimal(str(order['averagePrice']))
        elif 'limitPrice' in order and order['limitPrice']:
            price = Decimal(str(order['limitPrice']))
        
        # Timestamps
        created_at = datetime.utcnow()
        if 'createdAt' in order and order['createdAt']:
            try:
                created_at = datetime.fromisoformat(order['createdAt'].replace('Z', '+00:00'))
            except:
                pass
        
        filled_at = None
        if status == TradeStatus.FILLED and 'filledAt' in order and order['filledAt']:
            try:
                filled_at = datetime.fromisoformat(order['filledAt'].replace('Z', '+00:00'))
            except:
                filled_at = datetime.utcnow()
        
        # Create trade record
        trade = LiveTrade(
            account_id=account_id,
            public_order_id=order.get('orderId'),
            symbol=symbol,
            action=action,
            quantity=quantity,
            filled_quantity=filled_quantity,
            remaining_quantity=remaining_quantity,
            status=status,
            price=price,
            order_type=order.get('type', 'MARKET').upper(),
            time_in_force=order.get('timeInForce', 'DAY').upper(),
            created_at=created_at,
            filled_at=filled_at,
            strategy_name='IMPORTED',  # Mark as imported
            notes=f"Imported from Public.com on {datetime.utcnow().isoformat()}"
        )
        
        return trade

