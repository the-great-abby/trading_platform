"""
Public.com API Client

Handles authentication and API communication with Public.com for live trading.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
from cryptography.fernet import Fernet
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PublicAPIConfig:
    """Configuration for Public.com API client."""
    base_url: str = "https://public.com/api"
    api_version: str = "v1"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class PublicAPIClient:
    """Client for interacting with Public.com API."""
    
    def __init__(self, config: Optional[PublicAPIConfig] = None):
        """Initialize the Public.com API client."""
        self.config = config or PublicAPIConfig()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.is_authenticated: bool = False
        self._encryption_key = self._get_encryption_key()
        
        # Create HTTP client with timeout
        self.client = httpx.AsyncClient(
            base_url=f"{self.config.base_url}/{self.config.api_version}",
            timeout=self.config.timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "LiveTradingService/1.0.0"
            }
        )
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key for sensitive data."""
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            # Generate a key if not provided (for development)
            key = Fernet.generate_key()
            logger.warning("No encryption key provided, using generated key")
        return key.encode() if isinstance(key, str) else key
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        fernet = Fernet(self._encryption_key)
        return fernet.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        fernet = Fernet(self._encryption_key)
        return fernet.decrypt(encrypted_data.encode()).decode()
    
    async def authenticate(self, api_key: str, api_secret: str) -> Dict[str, Any]:
        """
        Authenticate with Public.com API.
        
        Args:
            api_key: Public.com API key
            api_secret: Public.com API secret
            
        Returns:
            Authentication response with tokens
            
        Raises:
            Exception: If authentication fails
        """
        try:
            auth_data = {
                "api_key": api_key,
                "api_secret": api_secret,
                "grant_type": "client_credentials"
            }
            
            response = await self.client.post("/auth/token", json=auth_data)
            response.raise_for_status()
            
            auth_response = response.json()
            
            # Store tokens
            self.access_token = auth_response.get("access_token")
            self.refresh_token = auth_response.get("refresh_token")
            expires_in = auth_response.get("expires_in", 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            self.is_authenticated = True
            
            # Update client headers
            self.client.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            
            logger.info("Successfully authenticated with Public.com API")
            
            return {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in,
                "token_type": "Bearer"
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Authentication failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Authentication failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise Exception(f"Authentication error: {str(e)}")
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using refresh token.
        
        Returns:
            New token response
            
        Raises:
            Exception: If token refresh fails
        """
        if not self.refresh_token:
            raise Exception("No refresh token available")
        
        try:
            refresh_data = {
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token"
            }
            
            response = await self.client.post("/auth/refresh", json=refresh_data)
            response.raise_for_status()
            
            token_response = response.json()
            
            # Update tokens
            self.access_token = token_response.get("access_token")
            self.refresh_token = token_response.get("refresh_token", self.refresh_token)
            expires_in = token_response.get("expires_in", 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Update client headers
            self.client.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            
            logger.info("Successfully refreshed access token")
            
            return {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Token refresh failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise Exception(f"Token refresh error: {str(e)}")
    
    async def get_accounts(self) -> Dict[str, Any]:
        """
        Get account information from Public.com.
        
        Returns:
            Account information
            
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            response = await self.client.get("/accounts")
            response.raise_for_status()
            
            accounts_data = response.json()
            logger.info(f"Retrieved {len(accounts_data.get('accounts', []))} accounts")
            
            return accounts_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get accounts failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Get accounts failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Get accounts error: {str(e)}")
            raise Exception(f"Get accounts error: {str(e)}")
    
    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Get account balance for specific account.
        
        Args:
            account_id: Public.com account ID
            
        Returns:
            Account balance information
            
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            response = await self.client.get(f"/accounts/{account_id}/balance")
            response.raise_for_status()
            
            balance_data = response.json()
            logger.info(f"Retrieved balance for account {account_id}")
            
            return balance_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get account balance failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Get account balance failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Get account balance error: {str(e)}")
            raise Exception(f"Get account balance error: {str(e)}")
    
    async def submit_order(self, account_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit an order to Public.com.
        
        Args:
            account_id: Public.com account ID
            order_data: Order details
            
        Returns:
            Order submission response
            
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            response = await self.client.post(f"/accounts/{account_id}/orders", json=order_data)
            response.raise_for_status()
            
            order_response = response.json()
            logger.info(f"Order submitted successfully: {order_response.get('order_id')}")
            
            return order_response
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Order submission failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Order submission failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Order submission error: {str(e)}")
            raise Exception(f"Order submission error: {str(e)}")
    
    async def get_order_status(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """
        Get order status from Public.com.
        
        Args:
            account_id: Public.com account ID
            order_id: Order ID
            
        Returns:
            Order status information
            
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            response = await self.client.get(f"/accounts/{account_id}/orders/{order_id}")
            response.raise_for_status()
            
            status_data = response.json()
            logger.debug(f"Retrieved order status for {order_id}")
            
            return status_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get order status failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Get order status failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Get order status error: {str(e)}")
            raise Exception(f"Get order status error: {str(e)}")
    
    async def cancel_order(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order on Public.com.
        
        Args:
            account_id: Public.com account ID
            order_id: Order ID to cancel
            
        Returns:
            Cancellation response
            
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            response = await self.client.delete(f"/accounts/{account_id}/orders/{order_id}")
            response.raise_for_status()
            
            cancel_response = response.json()
            logger.info(f"Order {order_id} cancelled successfully")
            
            return cancel_response
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Order cancellation failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Order cancellation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Order cancellation error: {str(e)}")
            raise Exception(f"Order cancellation error: {str(e)}")
    
    async def get_positions(self, account_id: str) -> Dict[str, Any]:
        """
        Get current positions from Public.com.
        
        Args:
            account_id: Public.com account ID
            
        Returns:
            Positions information
            
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            response = await self.client.get(f"/accounts/{account_id}/positions")
            response.raise_for_status()
            
            positions_data = response.json()
            logger.info(f"Retrieved {len(positions_data.get('positions', []))} positions")
            
            return positions_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get positions failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Get positions failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Get positions error: {str(e)}")
            raise Exception(f"Get positions error: {str(e)}")
    
    async def get_market_data(self, symbol: str, data_type: str = "quote") -> Dict[str, Any]:
        """
        Get market data from Public.com.
        
        Args:
            symbol: Trading symbol
            data_type: Type of market data (quote, options, etc.)
            
        Returns:
            Market data
            
        Raises:
            Exception: If API call fails
        """
        try:
            response = await self.client.get(f"/market/{data_type}/{symbol}")
            response.raise_for_status()
            
            market_data = response.json()
            logger.debug(f"Retrieved market data for {symbol}")
            
            return market_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get market data failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Get market data failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Get market data error: {str(e)}")
            raise Exception(f"Get market data error: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Public.com API client closed")
    
    def __del__(self):
        """Cleanup when client is destroyed."""
        if hasattr(self, 'client'):
            asyncio.create_task(self.close())
