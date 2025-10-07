"""
Discord Notification Helper
Sends trading alerts to Discord via webhook
"""

import asyncio
import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Simple Discord notification service for trading alerts"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    async def send_message(self, message: str, embeds: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Send a simple message to Discord"""
        try:
            payload = {
                "content": message,
                "embeds": embeds or []
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)
                
                if response.status_code == 204:
                    logger.info("✅ Discord notification sent")
                    return True
                else:
                    logger.error(f"❌ Discord notification failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Discord notification error: {e}")
            return False
    
    async def send_trade_alert(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        status: str,
        trade_id: str,
        pnl: Optional[float] = None,
        confidence: Optional[float] = None,
        reason: Optional[str] = None
    ) -> bool:
        """Send a formatted trade alert to Discord"""
        
        # Determine emoji based on action and status
        if action == "BUY":
            emoji = "📈"
            color = 0x00ff00  # Green
        elif action == "SELL":
            emoji = "📉"
            color = 0xff0000 if pnl and pnl < 0 else 0x00ff00  # Red if loss, green if profit
        else:
            emoji = "📊"
            color = 0x3498db  # Blue
            
        # Build embed
        embed = {
            "title": f"{emoji} {action} Order {status}",
            "color": color,
            "fields": [
                {
                    "name": "Symbol",
                    "value": symbol,
                    "inline": True
                },
                {
                    "name": "Quantity",
                    "value": str(quantity),
                    "inline": True
                },
                {
                    "name": "Price",
                    "value": f"${price:.2f}",
                    "inline": True
                },
                {
                    "name": "Status",
                    "value": status,
                    "inline": True
                },
                {
                    "name": "Trade ID",
                    "value": trade_id[:8] + "...",
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add optional fields
        if pnl is not None:
            pnl_emoji = "💰" if pnl >= 0 else "📉"
            embed["fields"].append({
                "name": f"{pnl_emoji} P&L",
                "value": f"${pnl:+.2f}",
                "inline": True
            })
            
        if confidence is not None:
            embed["fields"].append({
                "name": "Confidence",
                "value": f"{confidence:.1%}",
                "inline": True
            })
            
        if reason:
            embed["fields"].append({
                "name": "Signal",
                "value": reason,
                "inline": False
            })
        
        # Send message
        message = f"**Trading Alert** - {action} {symbol}"
        return await self.send_message(message, [embed])
    
    async def send_exit_alert(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        exit_price: float,
        pnl: float,
        confidence: float,
        status: str = "SUBMITTED"
    ) -> bool:
        """Send an exit/sell alert"""
        pnl_pct = (pnl / (entry_price * quantity)) * 100 if quantity > 0 else 0
        
        reason = f"Exit Signal ({confidence:.1%} confidence)\nEntry: ${entry_price:.2f} → Exit: ${exit_price:.2f}"
        
        return await self.send_trade_alert(
            symbol=symbol,
            action="SELL",
            quantity=quantity,
            price=exit_price,
            status=status,
            trade_id=f"EXIT_{symbol}_{datetime.now().strftime('%H%M%S')}",
            pnl=pnl,
            confidence=confidence,
            reason=reason
        )
    
    async def send_position_summary(self, positions: List[Dict[str, Any]]) -> bool:
        """Send a position summary to Discord"""
        if not positions:
            return await self.send_message("📊 **Position Summary**: No open positions")
        
        total_value = sum(float(p.get("value", 0)) for p in positions)
        total_pnl = sum(float(p.get("unrealized_pnl", 0)) for p in positions)
        
        fields = []
        for pos in positions:
            symbol = pos.get("symbol", "UNKNOWN")
            qty = pos.get("quantity", 0)
            avg_price = float(pos.get("average_price", 0))
            current_price = float(pos.get("current_price", avg_price))
            pnl = float(pos.get("unrealized_pnl", 0))
            
            value = f"{qty} @ ${avg_price:.2f} (now ${current_price:.2f})"
            pnl_str = f"${pnl:+.2f}"
            
            fields.append({
                "name": f"{symbol}",
                "value": f"{value}\nP&L: {pnl_str}",
                "inline": True
            })
        
        embed = {
            "title": "📊 Position Summary",
            "color": 0x3498db,
            "fields": fields + [
                {
                    "name": "Total Value",
                    "value": f"${total_value:.2f}",
                    "inline": True
                },
                {
                    "name": "Total P&L",
                    "value": f"${total_pnl:+.2f}",
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.send_message("", [embed])

