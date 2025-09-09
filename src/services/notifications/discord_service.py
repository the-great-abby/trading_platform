"""
Discord Notification Service
Handles sending notifications to Discord channels
"""

import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class DiscordService:
    """Service for sending Discord notifications"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize the Discord service"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the Discord service"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def send_order_notification(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Optional[Decimal],
        status: str,
        user_id: str,
        account_id: str
    ) -> bool:
        """Send order notification to Discord"""
        try:
            if not self.webhook_url:
                logger.warning("Discord webhook URL not configured")
                return False
            
            # Create embed for order notification
            embed = {
                "title": f"📈 Order {status.title()}",
                "color": self._get_status_color(status),
                "fields": [
                    {
                        "name": "Order ID",
                        "value": order_id,
                        "inline": True
                    },
                    {
                        "name": "Symbol",
                        "value": symbol,
                        "inline": True
                    },
                    {
                        "name": "Side",
                        "value": side.upper(),
                        "inline": True
                    },
                    {
                        "name": "Quantity",
                        "value": str(quantity),
                        "inline": True
                    },
                    {
                        "name": "Price",
                        "value": f"${price:.2f}" if price else "Market",
                        "inline": True
                    },
                    {
                        "name": "Status",
                        "value": status.upper(),
                        "inline": True
                    },
                    {
                        "name": "User",
                        "value": user_id,
                        "inline": True
                    },
                    {
                        "name": "Account",
                        "value": account_id,
                        "inline": True
                    },
                    {
                        "name": "Time",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Trading System Bot"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {
                "embeds": [embed]
            }
            
            return await self._send_webhook(payload)
            
        except Exception as e:
            logger.error(f"Error sending order notification: {e}")
            return False
    
    async def send_portfolio_notification(
        self,
        user_id: str,
        account_id: str,
        portfolio_value: Decimal,
        total_pnl: Decimal,
        positions: List[Dict[str, Any]]
    ) -> bool:
        """Send portfolio update notification to Discord"""
        try:
            if not self.webhook_url:
                logger.warning("Discord webhook URL not configured")
                return False
            
            # Calculate P&L color
            pnl_color = 0x00ff00 if total_pnl >= 0 else 0xff0000
            pnl_emoji = "📈" if total_pnl >= 0 else "📉"
            
            # Create embed for portfolio notification
            embed = {
                "title": f"{pnl_emoji} Portfolio Update",
                "color": pnl_color,
                "fields": [
                    {
                        "name": "Portfolio Value",
                        "value": f"${portfolio_value:,.2f}",
                        "inline": True
                    },
                    {
                        "name": "Total P&L",
                        "value": f"${total_pnl:,.2f}",
                        "inline": True
                    },
                    {
                        "name": "P&L %",
                        "value": f"{(total_pnl / portfolio_value * 100):.2f}%" if portfolio_value > 0 else "0.00%",
                        "inline": True
                    },
                    {
                        "name": "Positions",
                        "value": str(len(positions)),
                        "inline": True
                    },
                    {
                        "name": "User",
                        "value": user_id,
                        "inline": True
                    },
                    {
                        "name": "Account",
                        "value": account_id,
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Trading System Bot"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add top positions if any
            if positions:
                top_positions = sorted(positions, key=lambda x: abs(x.get('unrealized_pnl', 0)), reverse=True)[:3]
                position_text = "\n".join([
                    f"**{pos.get('symbol', 'N/A')}**: {pos.get('quantity', 0)} @ ${pos.get('avg_price', 0):.2f} "
                    f"({pos.get('unrealized_pnl', 0):.2f})"
                    for pos in top_positions
                ])
                
                embed["fields"].append({
                    "name": "Top Positions",
                    "value": position_text,
                    "inline": False
                })
            
            payload = {
                "embeds": [embed]
            }
            
            return await self._send_webhook(payload)
            
        except Exception as e:
            logger.error(f"Error sending portfolio notification: {e}")
            return False
    
    async def send_risk_alert(
        self,
        alert_type: str,
        message: str,
        user_id: str,
        account_id: str,
        severity: str = "warning"
    ) -> bool:
        """Send risk alert notification to Discord"""
        try:
            if not self.webhook_url:
                logger.warning("Discord webhook URL not configured")
                return False
            
            # Get alert emoji and color
            emoji = self._get_alert_emoji(severity)
            color = self._get_alert_color(severity)
            
            # Create embed for risk alert
            embed = {
                "title": f"{emoji} Risk Alert: {alert_type}",
                "description": message,
                "color": color,
                "fields": [
                    {
                        "name": "Severity",
                        "value": severity.upper(),
                        "inline": True
                    },
                    {
                        "name": "User",
                        "value": user_id,
                        "inline": True
                    },
                    {
                        "name": "Account",
                        "value": account_id,
                        "inline": True
                    },
                    {
                        "name": "Time",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Trading System Bot - Risk Management"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {
                "embeds": [embed]
            }
            
            return await self._send_webhook(payload)
            
        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")
            return False
    
    async def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info"
    ) -> bool:
        """Send system alert notification to Discord"""
        try:
            if not self.webhook_url:
                logger.warning("Discord webhook URL not configured")
                return False
            
            # Get alert emoji and color
            emoji = self._get_alert_emoji(severity)
            color = self._get_alert_color(severity)
            
            # Create embed for system alert
            embed = {
                "title": f"{emoji} System Alert: {alert_type}",
                "description": message,
                "color": color,
                "fields": [
                    {
                        "name": "Severity",
                        "value": severity.upper(),
                        "inline": True
                    },
                    {
                        "name": "Time",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Trading System Bot - System Monitoring"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {
                "embeds": [embed]
            }
            
            return await self._send_webhook(payload)
            
        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
            return False
    
    async def _send_webhook(self, payload: Dict[str, Any]) -> bool:
        """Send webhook to Discord"""
        try:
            if not self.session:
                await self.initialize()
            
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 204:
                    logger.info("Discord notification sent successfully")
                    return True
                else:
                    logger.error(f"Discord webhook failed: {response.status} - {await response.text()}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {e}")
            return False
    
    def _get_status_color(self, status: str) -> int:
        """Get color code for order status"""
        colors = {
            "pending": 0xffff00,      # Yellow
            "submitted": 0x0099ff,    # Blue
            "filled": 0x00ff00,       # Green
            "partially_filled": 0xffa500,  # Orange
            "cancelled": 0xff0000,    # Red
            "rejected": 0xff0000,     # Red
            "expired": 0x808080       # Gray
        }
        return colors.get(status.lower(), 0x808080)
    
    def _get_alert_emoji(self, severity: str) -> str:
        """Get emoji for alert severity"""
        emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        return emojis.get(severity.lower(), "ℹ️")
    
    def _get_alert_color(self, severity: str) -> int:
        """Get color code for alert severity"""
        colors = {
            "info": 0x0099ff,         # Blue
            "warning": 0xffa500,      # Orange
            "error": 0xff0000,        # Red
            "critical": 0x8b0000      # Dark Red
        }
        return colors.get(severity.lower(), 0x0099ff)
