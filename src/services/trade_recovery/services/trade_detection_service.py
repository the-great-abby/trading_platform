"""
TradeDetectionService for trade recovery system
Handles detection of active trades from broker APIs
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
import httpx
from decimal import Decimal

from ..models.active_trade import ActiveTrade, ActiveTradeCreate, TradeSide, PositionType, OptionDetails
from ..models.recovery_log import RecoveryLog, LogAction, LogSeverity

logger = logging.getLogger(__name__)


class TradeDetectionService:
    """Service for detecting active trades from broker APIs"""
    
    def __init__(self, broker_api_url: str, api_key: str, timeout: int = 30):
        """
        Initialize TradeDetectionService
        
        Args:
            broker_api_url: Base URL for broker API
            api_key: API key for broker authentication
            timeout: Request timeout in seconds
        """
        self.broker_api_url = broker_api_url
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def detect_active_trades(self, account_id: str, include_closed: bool = False) -> List[ActiveTrade]:
        """
        Detect active trades for a given account
        
        Args:
            account_id: Trading account identifier
            include_closed: Whether to include recently closed trades
            
        Returns:
            List of detected active trades
            
        Raises:
            TradeDetectionError: If trade detection fails
        """
        try:
            logger.info(f"Detecting active trades for account: {account_id}")
            
            # Get positions from broker API
            positions = await self._get_positions_from_broker(account_id, include_closed)
            
            # Convert to ActiveTrade objects
            active_trades = []
            for position in positions:
                try:
                    trade = await self._convert_position_to_trade(position, account_id)
                    active_trades.append(trade)
                except Exception as e:
                    logger.error(f"Failed to convert position to trade: {e}")
                    continue
            
            logger.info(f"Detected {len(active_trades)} active trades for account {account_id}")
            return active_trades
            
        except Exception as e:
            logger.error(f"Failed to detect active trades for account {account_id}: {e}")
            raise TradeDetectionError(f"Failed to detect active trades: {str(e)}")
    
    async def get_trade_details(self, account_id: str, symbol: str) -> Optional[ActiveTrade]:
        """
        Get detailed information for a specific trade
        
        Args:
            account_id: Trading account identifier
            symbol: Trading symbol
            
        Returns:
            Detailed trade information or None if not found
        """
        try:
            logger.info(f"Getting trade details for {symbol} in account {account_id}")
            
            # Get position details from broker API
            position = await self._get_position_details_from_broker(account_id, symbol)
            
            if position:
                return await self._convert_position_to_trade(position, account_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get trade details for {symbol}: {e}")
            raise TradeDetectionError(f"Failed to get trade details: {str(e)}")
    
    async def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """
        Get account-level position summary
        
        Args:
            account_id: Trading account identifier
            
        Returns:
            Account summary information
        """
        try:
            logger.info(f"Getting account summary for {account_id}")
            
            # Get account summary from broker API
            summary = await self._get_account_summary_from_broker(account_id)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get account summary for {account_id}: {e}")
            raise TradeDetectionError(f"Failed to get account summary: {str(e)}")
    
    async def _get_positions_from_broker(self, account_id: str, include_closed: bool = False) -> List[Dict[str, Any]]:
        """Get positions from broker API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "account_id": account_id,
                "include_closed": include_closed
            }
            
            response = await self.client.get(
                f"{self.broker_api_url}/positions",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("positions", [])
            else:
                raise Exception(f"Broker API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Broker API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Broker API request failed: {str(e)}")
    
    async def _get_position_details_from_broker(self, account_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position details from broker API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.get(
                f"{self.broker_api_url}/positions/{symbol}",
                headers=headers,
                params={"account_id": account_id}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise Exception(f"Broker API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Broker API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Broker API request failed: {str(e)}")
    
    async def _get_account_summary_from_broker(self, account_id: str) -> Dict[str, Any]:
        """Get account summary from broker API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = await self.client.get(
                f"{self.broker_api_url}/accounts/{account_id}/summary",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Broker API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Broker API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Broker API request failed: {str(e)}")
    
    async def _convert_position_to_trade(self, position: Dict[str, Any], account_id: str) -> ActiveTrade:
        """Convert broker position to ActiveTrade object"""
        try:
            # Extract basic position data
            symbol = position.get("symbol", "")
            quantity = Decimal(str(position.get("quantity", 0)))
            side = TradeSide(position.get("side", "BUY"))
            entry_price = Decimal(str(position.get("entry_price", 0)))
            current_price = Decimal(str(position.get("current_price", 0)))
            position_type = PositionType(position.get("position_type", "STOCK"))
            
            # Extract optional data
            entry_date = None
            if position.get("entry_date"):
                entry_date = datetime.fromisoformat(position["entry_date"].replace("Z", "+00:00"))
            
            # Handle option details
            option_details = None
            if position_type == PositionType.OPTION and position.get("option_details"):
                option_data = position["option_details"]
                option_details = OptionDetails(
                    strike=Decimal(str(option_data.get("strike", 0))) if option_data.get("strike") else None,
                    expiration=datetime.fromisoformat(option_data["expiration"].replace("Z", "+00:00")) if option_data.get("expiration") else None,
                    option_type=option_data.get("option_type")
                )
            
            # Create ActiveTrade object
            trade_data = ActiveTradeCreate(
                account_id=account_id,
                symbol=symbol,
                quantity=quantity,
                side=side,
                entry_price=entry_price,
                current_price=current_price,
                entry_date=entry_date,
                position_type=position_type,
                option_details=option_details
            )
            
            return ActiveTrade(**trade_data.dict())
            
        except Exception as e:
            logger.error(f"Failed to convert position to trade: {e}")
            raise TradeDetectionError(f"Failed to convert position to trade: {str(e)}")
    
    async def create_recovery_log(self, recovery_session_id: UUID, action: LogAction, 
                                 details: Dict[str, Any], user_id: Optional[str] = None,
                                 trade_id: Optional[UUID] = None, strategy_name: Optional[str] = None,
                                 severity: LogSeverity = LogSeverity.INFO) -> RecoveryLog:
        """Create a recovery log entry"""
        return RecoveryLog(
            recovery_session_id=recovery_session_id,
            action=action,
            details=details,
            user_id=user_id,
            trade_id=trade_id,
            strategy_name=strategy_name,
            severity=severity
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class TradeDetectionError(Exception):
    """Exception raised when trade detection fails"""
    pass


class BrokerAPIError(Exception):
    """Exception raised when broker API calls fail"""
    pass


class TradeConversionError(Exception):
    """Exception raised when converting broker data to trade objects fails"""
    pass


















