"""
Public API data provider for market data and trading
Based on Public API documentation: https://public.com/api/docs
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from loguru import logger

from ..utils.config import Config


class PublicDataProvider:
    """Public API data provider for market data and trading"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.public_base_url
        self.username = config.public_username
        self.password = config.public_password
        self.session = None
        self.auth_token = None
        self.connected = False
        
    async def connect(self):
        """Connect to Public API and authenticate"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Authenticate with Public API
            await self._authenticate()
            
            self.connected = True
            logger.info("Connected to Public API")
            
        except Exception as e:
            logger.error(f"Failed to connect to Public API: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Public API"""
        if self.session:
            await self.session.close()
        self.connected = False
        logger.info("Disconnected from Public API")
    
    async def _authenticate(self):
        """Authenticate with Public API using personal access token"""
        try:
            auth_url = f"{self.base_url}/create-personal-access-token"
            auth_data = {
                "username": self.username,
                "password": self.password
            }
            
            async with self.session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    auth_response = await response.json()
                    self.auth_token = auth_response.get("access_token")
                    if not self.auth_token:
                        raise Exception("No access token received")
                    logger.info("Successfully authenticated with Public API")
                else:
                    error_text = await response.text()
                    raise Exception(f"Authentication failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
    
    async def get_latest_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Get latest market data for symbols using POST /quotes"""
        data = {}
        
        try:
            # Public API uses POST for quotes with symbols array
            quotes_url = f"{self.base_url}/quotes"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {"symbols": symbols}
            
            async with self.session.post(quotes_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    quotes_data = await response.json()
                    
                    # Process each symbol's quote data
                    for symbol_data in quotes_data:
                        symbol = symbol_data.get('symbol')
                        if symbol:
                            df = self._quote_to_dataframe(symbol_data)
                            df = self._add_technical_indicators(df)
                            data[symbol] = df
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch quotes: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error fetching latest data: {e}")
        
        return data
    
    def _quote_to_dataframe(self, quote_data: Dict) -> pd.DataFrame:
        """Convert Public API quote to DataFrame format"""
        # Create a single row DataFrame with current quote data
        data = {
            'Open': [quote_data.get('open', 0)],
            'High': [quote_data.get('high', 0)],
            'Low': [quote_data.get('low', 0)],
            'Close': [quote_data.get('last', 0)],
            'Volume': [quote_data.get('volume', 0)],
            'timestamp': [datetime.now()]
        }
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe"""
        try:
            # For real-time data, we'll use simple calculations
            # In a real implementation, you'd want to maintain historical data
            
            # Simple moving averages (using current price as approximation)
            df['SMA_20'] = df['Close']
            df['SMA_50'] = df['Close']
            
            # RSI (simplified for real-time)
            df['RSI'] = 50  # Neutral RSI for real-time data
            
            # MACD (simplified)
            df['MACD'] = 0
            df['MACD_Signal'] = 0
            df['MACD_Histogram'] = 0
            
            # Bollinger Bands (simplified)
            df['BB_Middle'] = df['Close']
            df['BB_Upper'] = df['Close'] * 1.02
            df['BB_Lower'] = df['Close'] * 0.98
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            return df
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get historical data for a symbol"""
        try:
            # Note: Public API may have different historical data endpoints
            # This is a placeholder - check the actual API docs for historical data
            logger.warning("Historical data endpoint not yet implemented for Public API")
            return None
                    
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def place_order(self, symbol: str, side: str, quantity: int, order_type: str = "market") -> Dict:
        """Place an order through Public API using POST /orders"""
        try:
            order_url = f"{self.base_url}/orders"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            order_data = {
                "symbol": symbol,
                "side": side.lower(),
                "quantity": quantity,
                "type": order_type
            }
            
            async with self.session.post(order_url, json=order_data, headers=headers) as response:
                if response.status == 200:
                    order_response = await response.json()
                    logger.info(f"Order placed successfully: {order_response}")
                    return order_response
                else:
                    error_msg = await response.text()
                    logger.error(f"Order failed: {response.status} - {error_msg}")
                    raise Exception(f"Order failed: {error_msg}")
                    
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def get_order(self, order_id: str) -> Dict:
        """Get order details using GET /orders/{order_id}"""
        try:
            order_url = f"{self.base_url}/orders/{order_id}"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(order_url, headers=headers) as response:
                if response.status == 200:
                    order_data = await response.json()
                    return order_data
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to get order {order_id}: {response.status} - {error_msg}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return {}
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order using DELETE /orders/{order_id}"""
        try:
            order_url = f"{self.base_url}/orders/{order_id}"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.delete(order_url, headers=headers) as response:
                if response.status == 200:
                    cancel_response = await response.json()
                    logger.info(f"Order {order_id} cancelled successfully")
                    return cancel_response
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to cancel order {order_id}: {response.status} - {error_msg}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return {}
    
    async def get_accounts(self) -> List[Dict]:
        """Get accounts using GET /accounts"""
        try:
            accounts_url = f"{self.base_url}/accounts"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(accounts_url, headers=headers) as response:
                if response.status == 200:
                    accounts_data = await response.json()
                    return accounts_data
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to get accounts: {response.status} - {error_msg}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return []
    
    async def get_account_portfolio(self, account_id: str) -> Dict:
        """Get account portfolio using GET /accounts/{account_id}/portfolio/v2"""
        try:
            portfolio_url = f"{self.base_url}/accounts/{account_id}/portfolio/v2"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(portfolio_url, headers=headers) as response:
                if response.status == 200:
                    portfolio_data = await response.json()
                    return portfolio_data
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to get portfolio: {response.status} - {error_msg}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return {}
    
    async def get_account_history(self, account_id: str) -> List[Dict]:
        """Get account history using GET /accounts/{account_id}/history"""
        try:
            history_url = f"{self.base_url}/accounts/{account_id}/history"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(history_url, headers=headers) as response:
                if response.status == 200:
                    history_data = await response.json()
                    return history_data
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to get account history: {response.status} - {error_msg}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting account history: {e}")
            return []
    
    async def get_instruments(self) -> List[Dict]:
        """Get all instruments using GET /instruments"""
        try:
            instruments_url = f"{self.base_url}/instruments"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(instruments_url, headers=headers) as response:
                if response.status == 200:
                    instruments_data = await response.json()
                    return instruments_data
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to get instruments: {response.status} - {error_msg}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting instruments: {e}")
            return []
    
    async def get_instrument(self, instrument_id: str) -> Dict:
        """Get specific instrument using GET /instruments/{instrument_id}"""
        try:
            instrument_url = f"{self.base_url}/instruments/{instrument_id}"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(instrument_url, headers=headers) as response:
                if response.status == 200:
                    instrument_data = await response.json()
                    return instrument_data
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to get instrument {instrument_id}: {response.status} - {error_msg}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting instrument {instrument_id}: {e}")
            return {}
    
    async def get_option_expirations(self, symbol: str) -> List[Dict]:
        """Get option expirations using POST /option-expirations"""
        try:
            expirations_url = f"{self.base_url}/option-expirations"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {"symbol": symbol}
            
            async with self.session.post(expirations_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    expirations_data = await response.json()
                    return expirations_data
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to get option expirations: {response.status} - {error_msg}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting option expirations: {e}")
            return []
    
    async def get_option_chain(self, symbol: str, expiration: str) -> List[Dict]:
        """Get option chain using POST /option-chain"""
        try:
            chain_url = f"{self.base_url}/option-chain"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "symbol": symbol,
                "expiration": expiration
            }
            
            async with self.session.post(chain_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    chain_data = await response.json()
                    return chain_data
                else:
                    error_msg = await response.text()
                    logger.error(f"Failed to get option chain: {response.status} - {error_msg}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return []
    
    async def preflight_order(self, order_data: Dict) -> Dict:
        """Preflight an order using POST /preflight"""
        try:
            preflight_url = f"{self.base_url}/preflight"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.post(preflight_url, json=order_data, headers=headers) as response:
                if response.status == 200:
                    preflight_response = await response.json()
                    return preflight_response
                else:
                    error_msg = await response.text()
                    logger.error(f"Preflight failed: {response.status} - {error_msg}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error preflighting order: {e}")
            return {} 