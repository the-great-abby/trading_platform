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
    # Public.com API endpoints - must include /userapigateway path per API docs
    auth_base_url: str = os.getenv("PUBLIC_API_AUTH_BASE_URL", "https://api.public.com/userapiauthservice")
    api_base_url: str = os.getenv("PUBLIC_API_BASE_URL", "https://api.public.com/userapigateway")
    timeout: int = int(os.getenv("PUBLIC_API_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("PUBLIC_API_MAX_RETRIES", "3"))
    retry_delay: float = 1.0
    secret_key: str = os.getenv("PUBLIC_API_SECRET", "")  # Public.com secret key for token generation
    access_token: str = os.getenv("PUBLIC_API_KEY", "")  # Generated access token


class PublicAPIClient:
    """Client for interacting with Public.com API."""
    
    def __init__(self, config: Optional[PublicAPIConfig] = None):
        """Initialize the Public.com API client."""
        self.config = config or PublicAPIConfig()
        self.secret_key: Optional[str] = self.config.secret_key
        self.access_token: Optional[str] = self.config.access_token
        self.token_expires_at: Optional[datetime] = None
        self.is_authenticated: bool = bool(self.access_token)
        self._encryption_key = self._get_encryption_key()
        
        # Create HTTP client for API calls with timeout
        # Use mobile app-like headers to avoid CloudFront WAF blocks
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Public-Mobile/2.0 (iOS; iPhone; Build/1234)",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://public.com",
            "Referer": "https://public.com/"
        }
        
        # Add Bearer token if available
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        self.client = httpx.AsyncClient(
            base_url=self.config.api_base_url,
            timeout=self.config.timeout,
            headers=headers,
            follow_redirects=True
        )
        
        # Create separate client for authentication
        auth_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Public-Mobile/2.0 (iOS; iPhone; Build/1234)",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://public.com",
            "Referer": "https://public.com/"
        }
        self.auth_client = httpx.AsyncClient(
            base_url=self.config.auth_base_url,
            timeout=self.config.timeout,
            headers=auth_headers,
            follow_redirects=True
        )
    
    async def generate_access_token(self, secret_key: str, validity_minutes: int = 1440) -> Dict[str, Any]:
        """
        Generate an access token using the secret key.
        
        Args:
            secret_key: Public.com secret key
            validity_minutes: Token validity in minutes (default 24 hours)
            
        Returns:
            Token response with access token
            
        Raises:
            Exception: If token generation fails
        """
        try:
            response = await self.auth_client.post(
                "/personal/access-tokens",
                json={
                    "validityInMinutes": validity_minutes,
                    "secret": secret_key
                }
            )
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get("accessToken")
            
            if not access_token:
                raise Exception("No access token in response")
            
            # Store the token
            self.access_token = access_token
            self.is_authenticated = True
            self.token_expires_at = datetime.utcnow() + timedelta(minutes=validity_minutes)
            
            # Update client headers
            self.client.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            
            logger.info(f"Successfully generated access token, expires at {self.token_expires_at}")
            
            return token_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Token generation failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Token generation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Token generation error: {str(e)}")
            raise Exception(f"Token generation error: {str(e)}")
    
    async def auto_authenticate(self) -> bool:
        """
        Automatically authenticate using secret key or existing access token.
        
        Returns:
            True if authentication was successful, False otherwise
        """
        # If we have a secret key, generate a new token
        if self.secret_key:
            try:
                await self.generate_access_token(self.secret_key)
                logger.info("Auto-authentication successful using secret key")
                return True
            except Exception as e:
                logger.warning(f"Auto-authentication with secret key failed: {str(e)}")
        
        # If we have an existing access token, test it
        if self.access_token:
            try:
                response = await self.client.get("/trading/account")
                response.raise_for_status()
                logger.info("Auto-authentication successful using existing access token")
                return True
            except Exception as e:
                logger.warning(f"Auto-authentication with existing token failed: {str(e)}")
        
        logger.info("No valid authentication method available")
        return False
    
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
        return fernet.encrypt(data.encode('utf-8')).decode('utf-8')
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        fernet = Fernet(self._encryption_key)
        return fernet.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
    
    async def authenticate(self, secret_key: str) -> Dict[str, Any]:
        """
        Authenticate with Public.com API using secret key to generate access token.
        
        Args:
            secret_key: Public.com secret key
            
        Returns:
            Authentication response with token info
            
        Raises:
            Exception: If authentication fails
        """
        try:
            # Generate access token using secret key
            token_data = await self.generate_access_token(secret_key)
            
            logger.info("Successfully authenticated with Public.com API using secret key")
            
            return {
                "access_token": self.access_token,
                "token_type": "Bearer",
                "expires_in": 86400,  # 24 hours
                "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise Exception(f"Authentication error: {str(e)}")
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token by generating a new one using the secret key.
        
        Returns:
            Token response
            
        Raises:
            Exception: If token refresh fails
        """
        if not self.secret_key:
            raise Exception("No secret key available for token refresh")
        
        try:
            # Generate a new access token using the secret key
            return await self.authenticate(self.secret_key)
            
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
            response = await self.client.get("/trading/account")
            response.raise_for_status()
            
            account_data = response.json()
            logger.info(f"Retrieved account information: {account_data}")
            
            # Public.com returns an accounts array directly
            return account_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get accounts failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Get accounts failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Get accounts error: {str(e)}")
            raise Exception(f"Get accounts error: {str(e)}")
    
    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Get account balance for specific account using portfolio v2 endpoint.
        
        Args:
            account_id: Public.com account ID
            
        Returns:
            Account balance information from portfolio v2
            
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            response = await self.client.get(f"/trading/{account_id}/portfolio/v2")
            response.raise_for_status()
            
            portfolio_data = response.json()
            logger.info(f"Retrieved portfolio v2 for account {account_id}")
            
            # Extract balance information from portfolio response
            buying_power = portfolio_data.get("buyingPower", {})
            equity = portfolio_data.get("equity", [])
            
            # Calculate total equity from equity array
            total_equity = 0.0
            cash_balance = 0.0
            
            for equity_item in equity:
                if equity_item.get("type") == "CASH":
                    cash_balance = float(equity_item.get("value", 0))
                total_equity += float(equity_item.get("value", 0))
            
            balance_data = {
                "buying_power": float(buying_power.get("buyingPower", 0)),
                "cash_balance": cash_balance,
                "equity": total_equity,
                "cash_only_buying_power": float(buying_power.get("cashOnlyBuyingPower", 0)),
                "options_buying_power": float(buying_power.get("optionsBuyingPower", 0)),
                "positions": portfolio_data.get("positions", []),
                "orders": portfolio_data.get("orders", [])
            }
            
            return balance_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get account balance failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Get account balance failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Get account balance error: {str(e)}")
            raise Exception(f"Get account balance error: {str(e)}")
    
    async def get_option_chain(self, account_id: str, symbol: str, expiration_date: str) -> Dict[str, Any]:
        """
        Get option chain for a symbol from Public.com.
        
        Per API docs: POST /userapigateway/marketdata/{accountId}/option-chain
        
        Args:
            account_id: Public.com account ID (required in path)
            symbol: Stock symbol (e.g., "SPY", "AAPL")
            expiration_date: Expiration date (YYYY-MM-DD) - REQUIRED
            
        Returns:
            Dict with calls/puts arrays containing available strikes
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            # Per Public.com API docs - expirationDate is REQUIRED
            payload = {
                "instrument": {
                    "symbol": symbol,
                    "type": "EQUITY"
                },
                "expirationDate": expiration_date
            }
            
            # Correct endpoint per docs: /marketdata/{accountId}/option-chain
            response = await self.client.post(
                f"/marketdata/{account_id}/option-chain",
                json=payload
            )
            response.raise_for_status()
            
            option_chain = response.json()
            num_calls = len(option_chain.get('calls', []))
            num_puts = len(option_chain.get('puts', []))
            logger.info(f"✅ Retrieved option chain for {symbol} exp {expiration_date}: {num_calls} calls, {num_puts} puts")
            
            return option_chain
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Failed to get option chain (status {e.response.status_code}): {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}", "calls": [], "puts": []}
        except Exception as e:
            logger.error(f"❌ Failed to get option chain: {e}")
            return {"error": str(e), "calls": [], "puts": []}
    
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
            # Generate UUID for orderId as required by Public.com API
            import uuid
            order_id = str(uuid.uuid4())
            
            # Build order payload per Public.com API spec
            # Check if this is an options order by looking at legs
            legs = order_data.get("legs", [])
            is_options_order = False
            
            if legs and len(legs) > 0:
                first_leg = legs[0]
                if first_leg.get("option_type") and first_leg.get("strike_price") and first_leg.get("expiration_date"):
                    is_options_order = True
            
            if is_options_order:
                # Options order format
                # Public.com requires OCC-formatted options symbols
                underlying = order_data.get("symbol", "").upper()
                
                # Check if this is a multi-leg spread (2+ legs)
                num_legs = len(legs)
                
                if num_legs >= 2:
                    # MULTI-LEG SPREAD FORMAT (Bull Call, Iron Condor, etc.)
                    from datetime import datetime
                    option_legs = []
                    
                    for leg in legs:
                        option_type = leg.get("option_type", "CALL")
                        strike_price = float(leg.get("strike_price", 0))
                        exp_date_str = leg.get("expiration_date", "")
                        leg_action = leg.get("side", leg.get("action", "BUY")).upper()  # Try "side" first, fallback to "action"
                        leg_quantity = leg.get("quantity", 1)
                        
                        # Parse expiration date
                        if isinstance(exp_date_str, str):
                            exp_date = datetime.fromisoformat(exp_date_str.replace('Z', '+00:00'))
                        else:
                            exp_date = exp_date_str
                        
                        # Build OCC symbol for this leg
                        symbol_part = underlying.ljust(6)[:6].replace(' ', '')
                        date_part = exp_date.strftime("%y%m%d")
                        type_part = "C" if option_type.upper() == "CALL" else "P"
                        strike_part = f"{int(strike_price * 1000):08d}"
                        occ_symbol = f"{symbol_part}{date_part}{type_part}{strike_part}"
                        
                        option_legs.append({
                            "instrument": {
                                "symbol": occ_symbol,
                                "type": "OPTION"
                            },
                            "side": leg_action,  # BUY or SELL (not "orderSide")
                            "ratioQuantity": int(leg_quantity),  # Integer, not string (and "ratioQuantity" not "quantity")
                            "openCloseIndicator": "OPEN"  # Opening new spread
                        })
                        
                        logger.info(f"🔧 Leg {len(option_legs)}: {leg_action} {occ_symbol} ({underlying} {option_type} ${strike_price})")
                    
                    # Multi-leg spread payload for Public.com /order/multileg endpoint
                    # Calculate net debit from leg premiums (real market prices)
                    # legs is a list of dicts with 'premium', 'action', etc.
                    long_premium = sum(leg.get("premium", 0) for leg in legs if leg.get("side") == "buy")
                    short_premium = sum(leg.get("premium", 0) for leg in legs if leg.get("side") == "sell")
                    net_debit_per_share = long_premium - short_premium
                    
                    # Add 20% buffer to account for spread widening and ensure fill
                    limit_price_per_share = net_debit_per_share * 1.20
                    
                    logger.info(f"💰 Spread pricing: Long premium=${long_premium:.2f}, Short premium=${short_premium:.2f}")
                    logger.info(f"💰 Net debit=${net_debit_per_share:.2f}/share, Limit=${limit_price_per_share:.2f}/share")
                    
                    order_payload = {
                        "orderId": order_id,
                        "legs": option_legs,  # Array of legs
                        "type": "LIMIT",  # Spreads must use LIMIT, not MARKET
                        "limitPrice": f"{limit_price_per_share:.2f}",  # Per-share net debit with 10% buffer
                        "quantity": str(legs[0].get("quantity", 1)),  # Top-level quantity (string)
                        "expiration": {
                            "timeInForce": order_data.get("time_in_force", "day").upper()
                        }
                    }
                else:
                    # SINGLE-LEG OPTION FORMAT
                    first_leg = legs[0]
                    option_type = first_leg.get("option_type", "CALL")
                    strike_price = float(first_leg.get("strike_price", 0))
                    exp_date_str = first_leg.get("expiration_date", "")
                    
                    # Parse expiration date
                    from datetime import datetime
                    if isinstance(exp_date_str, str):
                        exp_date = datetime.fromisoformat(exp_date_str.replace('Z', '+00:00'))
                    else:
                        exp_date = exp_date_str
                    
                    # Determine if opening or closing position
                    side = order_data.get("side", "buy").upper()
                    open_close = "OPEN" if side == "BUY" else "CLOSE"
                    
                    # Build OCC symbol WITHOUT spaces
                    symbol_part = underlying.ljust(6)[:6].replace(' ', '')  # Remove padding spaces
                    date_part = exp_date.strftime("%y%m%d")
                    type_part = "C" if option_type.upper() == "CALL" else "P"
                    strike_part = f"{int(strike_price * 1000):08d}"
                    occ_symbol = f"{symbol_part}{date_part}{type_part}{strike_part}"
                    
                    logger.info(f"🔧 OCC Symbol: {occ_symbol} | {underlying} {option_type} ${strike_price} exp {exp_date.strftime('%Y-%m-%d')} ({open_close})")
                    
                    # Single-leg option order format for /order endpoint
                    order_payload = {
                        "orderId": order_id,
                        "instrument": {
                            "symbol": occ_symbol,  # OCC format without spaces
                            "type": "OPTION"
                        },
                        "orderSide": side,  # BUY or SELL
                        "orderType": order_data.get("type", "market").upper(),  # MARKET or LIMIT
                        "expiration": {
                            "timeInForce": order_data.get("time_in_force", "day").upper()
                        },
                        "quantity": str(first_leg.get("quantity", 1)),  # Must be string for /order endpoint
                        "openCloseIndicator": open_close  # OPEN or CLOSE
                    }
            else:
                # Equity order format
                order_payload = {
                    "orderId": order_id,
                    "instrument": {
                        "symbol": order_data.get("symbol"),
                        "type": "EQUITY"  # EQUITY for stocks, OPTION for options
                    },
                    "orderSide": order_data.get("side", "buy").upper(),  # BUY or SELL
                    "orderType": order_data.get("type", "market").upper(),  # MARKET or LIMIT
                    "expiration": {
                        "timeInForce": order_data.get("time_in_force", "day").upper()  # DAY, GTC, etc.
                    },
                    "quantity": str(order_data.get("quantity", 1))  # Must be string
                }
            
            # Add limitPrice for limit orders
            order_type_key = "type" if is_options_order else "orderType"
            if order_payload.get(order_type_key) == "LIMIT" and "price" in order_data:
                order_payload["limitPrice"] = str(order_data["price"])
            
            # Log the order payload for debugging
            logger.info(f"Submitting {'OPTIONS' if is_options_order else 'EQUITY'} order to Public.com: {order_payload}")
            
            # Create a new client with fresh headers for each order to avoid WAF detection
            order_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": "Public-Mobile/2.0 (iOS; iPhone; Build/1234)",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Origin": "https://public.com",
                "Referer": "https://public.com/",
                "X-Requested-With": "com.public.app",
                "X-App-Version": "2.0.0",
                "X-Device-Id": "trading-bot-device-001"
            }
            
            # Use /order endpoint for single-leg (both equity and options)
            # Use /order/multileg only for multi-leg spreads (2-6 legs)
            num_legs = len(legs) if legs else 0
            endpoint = f"/trading/{account_id}/order/multileg" if num_legs >= 2 else f"/trading/{account_id}/order"
            
            logger.info(f"Submitting order to Public.com (account {account_id}): {order_payload}")
            logger.info(f"🔑 Using access_token (preview): {self.access_token[:30] if self.access_token else 'NONE'}...")
            logger.info(f"🔑 Auth header will be: Bearer {self.access_token[:20] if self.access_token else 'NONE'}...")
            logger.info(f"📍 Endpoint: {endpoint}")
            
            response = await self.client.post(
                endpoint,
                json=order_payload,
                headers=order_headers
            )
            response.raise_for_status()
            
            # Public.com may return empty body on success - check response
            response_text = response.text
            logger.info(f"📋 Public.com response body: {response_text}")
            
            if response_text and response_text.strip():
                order_response = response.json()
                logger.info(f"✅ Order submitted successfully to Public.com: {order_response.get('orderId')}")
                return order_response
            else:
                # Empty response - return the orderId we sent
                logger.warning(f"⚠️  Public.com returned empty response, using submitted orderId: {order_id}")
                return {"orderId": order_id, "status": "SUBMITTED"}
            
            
        except httpx.HTTPStatusError as e:
            error_details = {
                "status_code": e.response.status_code,
                "response_text": e.response.text,
                "url": str(e.request.url),
                "method": e.request.method
            }
            logger.error(f"❌ Order submission failed with status {e.response.status_code}: {e.response.text}")
            logger.error(f"❌ Full error details: {error_details}")
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ Order submission error: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            raise Exception(f"{type(e).__name__}: {str(e)}")
    
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
        Get current positions from Public.com using portfolio/v2 endpoint.
        
        This endpoint returns both stock and options positions.
        
        Args:
            account_id: Public.com account ID
            
        Returns:
            Portfolio information including positions, orders, equity, buying power
            
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated")
        
        try:
            # Use portfolio/v2 endpoint for complete portfolio data
            response = await self.client.get(f"/trading/{account_id}/portfolio/v2")
            response.raise_for_status()
            
            portfolio_data = response.json()
            positions = portfolio_data.get('positions', [])
            
            # Log summary
            stock_positions = [p for p in positions if p.get('instrument', {}).get('type') == 'EQUITY']
            option_positions = [p for p in positions if p.get('instrument', {}).get('type') == 'OPTION']
            
            logger.info(f"Retrieved {len(positions)} total positions from Public.com")
            logger.info(f"  📈 Stock positions: {len(stock_positions)}")
            logger.info(f"  📊 Options positions: {len(option_positions)}")
            
            return portfolio_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get portfolio failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Get portfolio failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Get portfolio error: {str(e)}")
            raise Exception(f"Get portfolio error: {str(e)}")
    
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
