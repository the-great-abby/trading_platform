"""
Broker API Client Integration
Connects TradeDetectionService to actual broker APIs
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from decimal import Decimal

from ..services.trade_detection_service import TradeDetectionService, TradeDetectionError
from ...utils.trading_config import get_trade_recovery_config

logger = logging.getLogger(__name__)


class BrokerAPIClient:
    """Client for broker API integration"""
    
    def __init__(self, broker_type: str = "public_com"):
        """
        Initialize broker API client
        
        Args:
            broker_type: Type of broker (public_com, alpaca, etc.)
        """
        self.broker_type = broker_type
        self.config = get_trade_recovery_config()
        self.broker_config = self.config['broker_api']
        
        self.client = httpx.AsyncClient(
            base_url=self.broker_config['base_url'],
            timeout=self.broker_config['timeout'],
            headers={
                "Authorization": f"Bearer {self.broker_config['api_key']}",
                "Content-Type": "application/json"
            }
        )
    
    async def get_positions(self, account_id: str, include_closed: bool = False) -> List[Dict[str, Any]]:
        """
        Get positions from broker API
        
        Args:
            account_id: Account identifier
            include_closed: Whether to include closed positions
            
        Returns:
            List of position data
        """
        try:
            logger.info(f"Fetching positions for account {account_id} from {self.broker_type}")
            
            if self.broker_type == "public_com":
                return await self._get_public_com_positions(account_id, include_closed)
            elif self.broker_type == "alpaca":
                return await self._get_alpaca_positions(account_id, include_closed)
            else:
                raise TradeDetectionError(f"Unsupported broker type: {self.broker_type}")
                
        except Exception as e:
            logger.error(f"Failed to get positions from {self.broker_type}: {e}")
            raise TradeDetectionError(f"Broker API error: {str(e)}")
    
    async def get_position_details(self, account_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed position information for a specific symbol
        
        Args:
            account_id: Account identifier
            symbol: Trading symbol
            
        Returns:
            Position details or None if not found
        """
        try:
            logger.info(f"Fetching position details for {symbol} in account {account_id}")
            
            if self.broker_type == "public_com":
                return await self._get_public_com_position_details(account_id, symbol)
            elif self.broker_type == "alpaca":
                return await self._get_alpaca_position_details(account_id, symbol)
            else:
                raise TradeDetectionError(f"Unsupported broker type: {self.broker_type}")
                
        except Exception as e:
            logger.error(f"Failed to get position details for {symbol}: {e}")
            raise TradeDetectionError(f"Broker API error: {str(e)}")
    
    async def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """
        Get account summary information
        
        Args:
            account_id: Account identifier
            
        Returns:
            Account summary data
        """
        try:
            logger.info(f"Fetching account summary for {account_id}")
            
            if self.broker_type == "public_com":
                return await self._get_public_com_account_summary(account_id)
            elif self.broker_type == "alpaca":
                return await self._get_alpaca_account_summary(account_id)
            else:
                raise TradeDetectionError(f"Unsupported broker type: {self.broker_type}")
                
        except Exception as e:
            logger.error(f"Failed to get account summary for {account_id}: {e}")
            raise TradeDetectionError(f"Broker API error: {str(e)}")
    
    async def _get_public_com_positions(self, account_id: str, include_closed: bool) -> List[Dict[str, Any]]:
        """Get positions from Public.com API"""
        try:
            response = await self.client.get(
                "/v1/positions",
                params={
                    "account_id": account_id,
                    "include_closed": include_closed
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("positions", [])
            else:
                raise Exception(f"Public.com API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Public.com API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Public.com API request failed: {str(e)}")
    
    async def _get_public_com_position_details(self, account_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position details from Public.com API"""
        try:
            response = await self.client.get(
                f"/v1/positions/{symbol}",
                params={"account_id": account_id}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise Exception(f"Public.com API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Public.com API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Public.com API request failed: {str(e)}")
    
    async def _get_public_com_account_summary(self, account_id: str) -> Dict[str, Any]:
        """Get account summary from Public.com API"""
        try:
            response = await self.client.get(f"/v1/accounts/{account_id}/summary")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Public.com API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Public.com API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Public.com API request failed: {str(e)}")
    
    async def _get_alpaca_positions(self, account_id: str, include_closed: bool) -> List[Dict[str, Any]]:
        """Get positions from Alpaca API"""
        try:
            response = await self.client.get(
                "/v2/positions",
                params={
                    "status": "all" if include_closed else "open"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Alpaca API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Alpaca API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Alpaca API request failed: {str(e)}")
    
    async def _get_alpaca_position_details(self, account_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position details from Alpaca API"""
        try:
            response = await self.client.get(f"/v2/positions/{symbol}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise Exception(f"Alpaca API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Alpaca API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Alpaca API request failed: {str(e)}")
    
    async def _get_alpaca_account_summary(self, account_id: str) -> Dict[str, Any]:
        """Get account summary from Alpaca API"""
        try:
            response = await self.client.get("/v2/account")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Alpaca API error: {response.status_code} - {response.text}")
                
        except httpx.TimeoutException:
            raise TradeDetectionError("Alpaca API timeout")
        except httpx.RequestError as e:
            raise TradeDetectionError(f"Alpaca API request failed: {str(e)}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class IntegratedTradeDetectionService(TradeDetectionService):
    """TradeDetectionService with integrated broker API client"""
    
    def __init__(self, broker_type: str = "public_com"):
        """
        Initialize integrated trade detection service
        
        Args:
            broker_type: Type of broker to use
        """
        config = get_trade_recovery_config()
        super().__init__(
            broker_api_url=config['broker_api']['base_url'],
            api_key=config['broker_api']['api_key'],
            timeout=config['broker_api']['timeout']
        )
        
        self.broker_client = BrokerAPIClient(broker_type)
    
    async def detect_active_trades(self, account_id: str, include_closed: bool = False):
        """Override to use integrated broker client"""
        try:
            logger.info(f"Detecting active trades for account {account_id} using {self.broker_client.broker_type}")
            
            # Get positions from broker
            positions = await self.broker_client.get_positions(account_id, include_closed)
            
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
    
    async def get_trade_details(self, account_id: str, symbol: str):
        """Override to use integrated broker client"""
        try:
            logger.info(f"Getting trade details for {symbol} in account {account_id}")
            
            position = await self.broker_client.get_position_details(account_id, symbol)
            if position:
                return await self._convert_position_to_trade(position, account_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get trade details for {symbol}: {e}")
            raise TradeDetectionError(f"Failed to get trade details: {str(e)}")
    
    async def get_account_summary(self, account_id: str):
        """Override to use integrated broker client"""
        try:
            logger.info(f"Getting account summary for {account_id}")
            
            return await self.broker_client.get_account_summary(account_id)
            
        except Exception as e:
            logger.error(f"Failed to get account summary for {account_id}: {e}")
            raise TradeDetectionError(f"Failed to get account summary: {str(e)}")
    
    async def close(self):
        """Close both clients"""
        await super().close()
        await self.broker_client.close()








