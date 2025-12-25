"""
Account Balance Sync Service

Periodically syncs account balances from Public.com to keep database up-to-date.
"""

import logging
import json
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
            # Use portfolio/v2 endpoint which returns both positions and orders
            response = await self.api_client.client.get(
                f"/trading/{public_account_id}/portfolio/v2"
            )
            response.raise_for_status()
            
            portfolio_data = response.json()
            
            # Extract balance and position information from portfolio/v2 response
            buying_power_data = portfolio_data.get("buyingPower", {})
            equity_data = portfolio_data.get("equity", [])
            positions = portfolio_data.get("positions", [])
            
            # Calculate cash balance from equity data
            cash_balance = 0.0
            for equity_item in equity_data:
                if equity_item.get("type") == "CASH":
                    cash_balance = float(equity_item.get("value", 0))
            
            # Build account data from portfolio
            account_data = {
                "cashBalance": cash_balance,
                "buyingPower": float(buying_power_data.get("buyingPower", 0)),
                "positions": positions
            }
            
            logger.info(f"✅ Portfolio data retrieved: {len(positions)} positions, ${cash_balance:.2f} cash")
            
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
            
            # Fetch positions from Public.com using portfolio/v2 endpoint
            response = await self.api_client.client.get(
                f"/trading/{public_account_id}/portfolio/v2"
            )
            response.raise_for_status()
            
            portfolio_data = response.json()
            public_positions = portfolio_data.get("positions", [])
            
            logger.info(f"📊 Received {len(public_positions)} positions from Public.com")
            
            # First, mark ALL existing positions as CLOSED
            await self.db_session.execute(text("""
                UPDATE live_positions
                SET status = 'CLOSED', updated_at = NOW()
                WHERE account_id = :account_id
                  AND status = 'OPEN'
            """), {'account_id': account_id})
            
            # Process positions directly (simple version without complex parser)
            stock_count = 0
            option_count = 0
            inserted_count = 0
            
            for pos in public_positions:
                try:
                    instrument = pos.get("instrument", {})
                    symbol = instrument.get("symbol")
                    instrument_type = instrument.get("type")  # EQUITY or OPTION
                    
                    if not symbol:
                        continue
                    
                    quantity = int(float(pos.get("quantity", 0)))
                    
                    # Get pricing
                    cost_basis = pos.get("costBasis", {})
                    avg_price = float(cost_basis.get("unitCost", 0))
                    
                    last_price_data = pos.get("lastPrice", {})
                    current_price = float(last_price_data.get("lastPrice", 0))
                    
                    # Get P&L
                    gain_data = pos.get("instrumentGain", {})
                    unrealized_pnl = float(gain_data.get("gainValue", 0))
                    
                    # Get opened time (convert to naive UTC for database consistency)
                    opened_at_str = pos.get("openedAt")
                    if opened_at_str:
                        opened_at = datetime.fromisoformat(opened_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    else:
                        opened_at = datetime.utcnow()
                    
                    # Create legs data for options
                    legs_data = None
                    if instrument_type == "OPTION":
                        option_count += 1
                        # Parse option symbol to get strike and expiration
                        # Format: "SPY251021C00580000" = SPY Oct 21 2025 $580 Call
                        legs_data = json.dumps([{
                            "action": "BUY",
                            "option_type": "CALL" if "C" in symbol else "PUT",
                            "strike_price": 0,  # Parse from symbol if needed
                            "expiration_date": None,  # Parse from symbol if needed
                            "quantity": quantity,
                            "premium": avg_price
                        }])
                        logger.info(f"   📊 Syncing option: {symbol} x{quantity}")
                    else:
                        stock_count += 1
                        logger.info(f"   📈 Syncing stock: {symbol} x{quantity}")
                    
                    # Insert new position or reopen existing closed position
                    # First try to reopen the most recently closed position for this symbol
                    result = await self.db_session.execute(text("""
                        UPDATE live_positions
                        SET 
                            quantity = :quantity,
                            average_price = :average_price,
                            current_price = :current_price,
                            unrealized_pnl = :unrealized_pnl,
                            status = 'OPEN',
                            legs_data = :legs_data,
                            updated_at = NOW()
                        WHERE position_id = (
                            SELECT position_id FROM live_positions
                            WHERE account_id = :account_id
                              AND symbol = :symbol
                              AND status = 'CLOSED'
                            ORDER BY updated_at DESC
                            LIMIT 1
                        )
                    """), {
                        'account_id': account_id,
                        'symbol': symbol,
                        'quantity': quantity,
                        'average_price': avg_price,
                        'current_price': current_price,
                        'unrealized_pnl': unrealized_pnl,
                        'legs_data': legs_data
                    })
                    
                    # Check if UPDATE affected any rows
                    if result.rowcount == 0:
                        # No CLOSED position found, insert new position with generated UUID
                        await self.db_session.execute(text("""
                            INSERT INTO live_positions (
                                position_id, account_id, symbol, strategy, quantity, average_price,
                                current_price, unrealized_pnl, status, opened_at,
                                legs_data, created_at, updated_at
                            ) VALUES (
                                gen_random_uuid(), :account_id, :symbol, :strategy, :quantity, :average_price,
                                :current_price, :unrealized_pnl, 'OPEN', :opened_at,
                                :legs_data, NOW(), NOW()
                            )
                        """), {
                            'account_id': account_id,
                            'symbol': symbol,
                            'strategy': 'MULTI_STRATEGY_ENSEMBLE',
                            'quantity': quantity,
                            'average_price': avg_price,
                            'current_price': current_price,
                            'unrealized_pnl': unrealized_pnl,
                            'opened_at': opened_at,
                            'legs_data': legs_data
                        })
                    
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing position {pos.get('instrument', {}).get('symbol')}: {e}")
                    continue
            
            await self.db_session.commit()
            
            logger.info(f"✅ Position sync complete:")
            logger.info(f"   Total synced: {inserted_count}")
            logger.info(f"   Stock: {stock_count}")
            logger.info(f"   Options: {option_count}")
            
            return {
                "success": True,
                "positions_synced": len(public_positions),
                "stock_positions": stock_count,
                "options_positions": option_count,
                "positions_inserted": inserted_count,
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Failed to sync positions: {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"❌ Position sync error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

            
        except Exception as e:
            logger.error(f"❌ Failed to sync positions: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
