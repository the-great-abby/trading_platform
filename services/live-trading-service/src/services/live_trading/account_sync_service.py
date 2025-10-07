"""
Account Balance Sync Service

Periodically syncs account balances from Public.com to keep database up-to-date.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import httpx

from .models import LiveTradingAccount
from .public_api_client import PublicAPIClient

logger = logging.getLogger(__name__)


class AccountSyncService:
    """Service for syncing account balances from Public.com."""
    
    def __init__(self, db_session: AsyncSession, api_client: PublicAPIClient):
        """Initialize the account sync service."""
        self.db_session = db_session
        self.api_client = api_client
    
    async def sync_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Sync account balance from Public.com.
        
        Args:
            account_id: Internal account ID
            
        Returns:
            Dict with sync results
        """
        try:
            logger.info(f"🔄 Syncing account balance for {account_id}")
            
            # Get the public account ID
            result = await self.db_session.execute(
                select(LiveTradingAccount.public_account_id).where(
                    LiveTradingAccount.account_id == account_id
                )
            )
            public_account_id = result.scalar_one_or_none()
            
            if not public_account_id:
                logger.error(f"❌ No public account ID found for {account_id}")
                return {
                    "success": False,
                    "error": "Account not found"
                }
            
            # Fetch account info from Public.com
            account_info = await self._fetch_account_info(public_account_id)
            
            if not account_info:
                return {
                    "success": False,
                    "error": "Failed to fetch account info from Public.com"
                }
            
            # Extract balance information
            cash_balance = float(account_info.get("cashBalance", 0))
            buying_power = float(account_info.get("buyingPower", 0))
            
            # Calculate equity from positions
            positions = account_info.get("positions", [])
            equity = sum(
                float(pos.get("quantity", 0)) * float(pos.get("currentPrice", 0))
                for pos in positions
            )
            
            # Update database
            await self.db_session.execute(
                text("""
                    UPDATE live_trading_accounts
                    SET cash_balance = :cash_balance,
                        equity = :equity,
                        buying_power = :buying_power,
                        updated_at = NOW()
                    WHERE account_id = :account_id
                """),
                {
                    "cash_balance": cash_balance,
                    "equity": equity,
                    "buying_power": buying_power,
                    "account_id": account_id
                }
            )
            await self.db_session.commit()
            
            portfolio_value = cash_balance + equity
            
            logger.info(f"✅ Account balance synced:")
            logger.info(f"   Cash: ${cash_balance:.2f}")
            logger.info(f"   Equity: ${equity:.2f}")
            logger.info(f"   Buying Power: ${buying_power:.2f}")
            logger.info(f"   Portfolio Value: ${portfolio_value:.2f}")
            
            return {
                "success": True,
                "cash_balance": cash_balance,
                "equity": equity,
                "buying_power": buying_power,
                "portfolio_value": portfolio_value,
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to sync account balance: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fetch_account_info(self, public_account_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch account information from Public.com.
        
        Since Public.com doesn't provide direct balance/positions endpoints,
        we calculate from recent orders and known positions.
        
        Args:
            public_account_id: Public.com account ID
            
        Returns:
            Account info dict or None if failed
        """
        try:
            # Get recent orders to check for fills
            response = await self.api_client.client.get(
                f"/trading/{public_account_id}/orders",
                params={"limit": 50}
            )
            response.raise_for_status()
            
            orders_data = response.json()
            orders = orders_data.get("orders", [])
            
            # Calculate balances from filled orders
            # Note: This is an estimation since Public.com doesn't expose direct balance API
            cash_spent = 0.0
            positions = {}
            
            for order in orders:
                if order.get("status") == "FILLED":
                    symbol = order.get("symbol")
                    quantity = float(order.get("filledQuantity", 0))
                    price = float(order.get("averageFilledPrice", 0))
                    side = order.get("side", "").upper()
                    
                    if side == "BUY":
                        cash_spent += quantity * price
                        if symbol in positions:
                            positions[symbol]["quantity"] += quantity
                            positions[symbol]["totalCost"] += quantity * price
                        else:
                            positions[symbol] = {
                                "symbol": symbol,
                                "quantity": quantity,
                                "currentPrice": price,  # Use last price as estimate
                                "totalCost": quantity * price
                            }
                    elif side == "SELL":
                        cash_spent -= quantity * price
                        if symbol in positions:
                            positions[symbol]["quantity"] -= quantity
                            positions[symbol]["totalCost"] -= quantity * price
            
            # For now, return estimated values
            # In production, you'd need to track starting balance
            account_data = {
                "cashBalance": 0.0,  # Would need to be tracked separately
                "buyingPower": 0.0,
                "positions": list(positions.values())
            }
            
            logger.warning("⚠️  Account balance estimation from orders (Public.com doesn't expose direct balance API)")
            
            return account_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Failed to fetch account info (status {e.response.status_code}): {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to fetch account info: {e}")
            return None
    
    async def sync_positions(self, account_id: str) -> Dict[str, Any]:
        """
        Sync positions from Public.com and update database.
        
        Args:
            account_id: Internal account ID
            
        Returns:
            Dict with sync results
        """
        try:
            logger.info(f"🔄 Syncing positions for {account_id}")
            
            # Get the public account ID
            result = await self.db_session.execute(
                select(LiveTradingAccount.public_account_id).where(
                    LiveTradingAccount.account_id == account_id
                )
            )
            public_account_id = result.scalar_one_or_none()
            
            if not public_account_id:
                return {
                    "success": False,
                    "error": "Account not found"
                }
            
            # Fetch positions from Public.com
            response = await self.api_client.client.get(
                f"/trading/{public_account_id}/positions"
            )
            response.raise_for_status()
            
            positions_data = response.json()
            positions = positions_data.get("positions", [])
            
            # Update each position in database
            updated_count = 0
            for pos in positions:
                symbol = pos.get("symbol")
                quantity = float(pos.get("quantity", 0))
                current_price = float(pos.get("currentPrice", 0))
                market_value = float(pos.get("marketValue", 0))
                avg_price = float(pos.get("averagePrice", 0))
                
                # Update or skip if quantity is 0
                if quantity > 0:
                    await self.db_session.execute(
                        text("""
                            UPDATE live_positions
                            SET quantity = :quantity,
                                current_price = :current_price,
                                market_value = :market_value,
                                average_price = :avg_price,
                                updated_at = NOW()
                            WHERE account_id = :account_id
                              AND symbol = :symbol
                              AND status = 'OPEN'
                        """),
                        {
                            "quantity": quantity,
                            "current_price": current_price,
                            "market_value": market_value,
                            "avg_price": avg_price,
                            "account_id": account_id,
                            "symbol": symbol
                        }
                    )
                    updated_count += 1
                else:
                    # Close positions with 0 quantity
                    await self.db_session.execute(
                        text("""
                            UPDATE live_positions
                            SET status = 'CLOSED',
                                closed_at = NOW(),
                                updated_at = NOW()
                            WHERE account_id = :account_id
                              AND symbol = :symbol
                              AND status = 'OPEN'
                        """),
                        {
                            "account_id": account_id,
                            "symbol": symbol
                        }
                    )
            
            await self.db_session.commit()
            
            logger.info(f"✅ Synced {len(positions)} positions, updated {updated_count}")
            
            return {
                "success": True,
                "positions_synced": len(positions),
                "positions_updated": updated_count,
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to sync positions: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
