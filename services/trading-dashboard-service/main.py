"""
Trading Dashboard Service - RSS feeds for trade information and strategy events
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
from datetime import datetime, timedelta
import requests
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Dashboard Service", version="1.0.0")

class TradeInfo(BaseModel):
    timestamp: str
    symbol: str
    action: str
    quantity: int
    price: float
    value: float
    pnl: float
    confidence: float
    strategy: str
    portfolio_value: float
    cash: float
    total_pnl: float

class ActivePosition(BaseModel):
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    entry_date: str
    strategy: str
    holding_days: int

class StrategyEvent(BaseModel):
    timestamp: str
    strategy: str
    symbol: str
    event_type: str
    action: str
    confidence: float
    metadata: Dict[str, Any]

class PortfolioSummary(BaseModel):
    total_value: float
    cash: float
    total_pnl: float
    total_pnl_percentage: float
    num_positions: int
    positions: List[ActivePosition]
    recent_trades: List[TradeInfo]

def get_database_connection():
    """Get database connection"""
    try:
        engine = create_engine(
            'postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot',
            echo=False,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_current_price_from_market_data(symbol: str) -> Optional[float]:
    """Get current price from market data service"""
    try:
        response = requests.get(f"http://market-data-service:8000/price/{symbol}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('price')
    except Exception as e:
        logger.warning(f"Could not get price for {symbol}: {e}")
    return None

@app.get("/dashboard/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """Get comprehensive portfolio summary with active positions and recent trades"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get latest backtest run
            run_result = conn.execute(text("""
                SELECT run_id, strategy_name, initial_capital, final_capital, total_return_pct
                FROM backtest_runs 
                ORDER BY created_at DESC 
                LIMIT 1
            """))
            
            latest_run = run_result.fetchone()
            if not latest_run:
                raise HTTPException(status_code=404, detail="No backtest runs found")
            
            run_id = latest_run.run_id
            
            # Get recent trades (last 50)
            trades_result = conn.execute(text("""
                SELECT 
                    timestamp,
                    symbol,
                    action,
                    quantity,
                    price,
                    value,
                    pnl,
                    confidence,
                    portfolio_value,
                    cash,
                    total_pnl
                FROM backtest_trades 
                WHERE run_id = :run_id
                ORDER BY LENGTH(symbol) DESC, timestamp DESC
                LIMIT 50
            """), {"run_id": run_id})
            
            recent_trades = []
            for trade_row in trades_result:
                recent_trades.append(TradeInfo(
                    timestamp=trade_row.timestamp.isoformat() if trade_row.timestamp else "",
                    symbol=trade_row.symbol,
                    action=trade_row.action,
                    quantity=trade_row.quantity,
                    price=trade_row.price,
                    value=trade_row.value,
                    pnl=trade_row.pnl,
                    confidence=trade_row.confidence,
                    strategy=latest_run.strategy_name,
                    portfolio_value=trade_row.portfolio_value,
                    cash=trade_row.cash,
                    total_pnl=trade_row.total_pnl
                ))
            
            # Calculate active positions from recent trades
            positions = {}
            for trade in recent_trades:
                symbol = trade.symbol
                if trade.action == "BUY":
                    if symbol not in positions:
                        positions[symbol] = {
                            'quantity': 0,
                            'total_cost': 0.0,
                            'entry_date': trade.timestamp,
                            'strategy': trade.strategy
                        }
                    positions[symbol]['quantity'] += trade.quantity
                    positions[symbol]['total_cost'] += trade.value
                elif trade.action == "SELL":
                    if symbol in positions:
                        positions[symbol]['quantity'] -= trade.quantity
                        if positions[symbol]['quantity'] <= 0:
                            del positions[symbol]
            
            # Convert to ActivePosition objects
            active_positions = []
            total_market_value = 0.0
            total_cost_basis = 0.0
            
            for symbol, pos_data in positions.items():
                if pos_data['quantity'] > 0:
                    avg_price = pos_data['total_cost'] / pos_data['quantity']
                    
                    # Get current price
                    current_price = get_current_price_from_market_data(symbol)
                    if current_price is None:
                        current_price = avg_price * 1.05  # Fallback
                    
                    market_value = pos_data['quantity'] * current_price
                    cost_basis = pos_data['quantity'] * avg_price
                    unrealized_pnl = market_value - cost_basis
                    unrealized_pnl_percent = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                    
                    # Calculate holding days
                    entry_date = datetime.fromisoformat(pos_data['entry_date'].replace('Z', '+00:00'))
                    holding_days = (datetime.now() - entry_date).days
                    
                    position = ActivePosition(
                        symbol=symbol,
                        quantity=pos_data['quantity'],
                        avg_price=avg_price,
                        current_price=current_price,
                        market_value=market_value,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_percent=unrealized_pnl_percent,
                        entry_date=pos_data['entry_date'],
                        strategy=pos_data['strategy'],
                        holding_days=holding_days
                    )
                    active_positions.append(position)
                    total_market_value += market_value
                    total_cost_basis += cost_basis
            
            # Mock cash balance (in real system, this would come from portfolio service)
            cash = 50000.0
            total_value = total_market_value + cash
            total_pnl = total_market_value - total_cost_basis
            total_pnl_percentage = (total_pnl / total_cost_basis) * 100 if total_cost_basis > 0 else 0
            
            return PortfolioSummary(
                total_value=total_value,
                cash=cash,
                total_pnl=total_pnl,
                total_pnl_percentage=total_pnl_percentage,
                num_positions=len(active_positions),
                positions=active_positions,
                recent_trades=recent_trades
            )
            
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio summary: {str(e)}")

@app.get("/dashboard/rss/trades", response_class=PlainTextResponse)
async def get_trades_rss_feed():
    """Get RSS feed for recent trades"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get recent trades from all runs with enhanced information
            trades_result = conn.execute(text("""
                SELECT 
                    bt.timestamp,
                    bt.symbol,
                    bt.action,
                    bt.quantity,
                    bt.price,
                    bt.value,
                    bt.pnl,
                    bt.confidence,
                    bt.portfolio_value,
                    bt.cash,
                    bt.total_pnl,
                    bt.position_value,
                    br.strategy_name,
                    br.backtest_name,
                    br.initial_capital,
                    br.final_capital,
                    br.total_return_pct
                FROM backtest_trades bt
                JOIN backtest_runs br ON bt.run_id = br.run_id
                ORDER BY bt.timestamp DESC
                LIMIT 100
            """))
            
            # Create RSS feed
            rss = ET.Element('rss', version='2.0')
            channel = ET.SubElement(rss, 'channel')
            
            title = ET.SubElement(channel, 'title')
            title.text = 'Space Trading Station - Recent Trades & Transactions'
            
            link = ET.SubElement(channel, 'link')
            link.text = 'http://localhost:8000/dashboard/rss/trades'
            
            description = ET.SubElement(channel, 'description')
            description.text = 'Detailed trading activity and transaction history from the Space Trading Station'
            
            last_build_date = ET.SubElement(channel, 'lastBuildDate')
            last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            for trade_row in trades_result:
                item = ET.SubElement(channel, 'item')
                
                # Enhanced trade identification with emojis and details
                if trade_row.action == "BUY":
                    action_emoji = "🟢"
                    action_desc = "BUY"
                    trade_type = "Purchase"
                else:
                    action_emoji = "🔴"
                    action_desc = "SELL"
                    trade_type = "Sale"
                
                # Calculate trade impact
                trade_impact = "High" if trade_row.value > 10000 else "Medium" if trade_row.value > 5000 else "Low"
                
                # Determine P&L status
                if trade_row.pnl > 0:
                    pnl_emoji = "📈"
                    pnl_status = "Profit"
                elif trade_row.pnl < 0:
                    pnl_emoji = "📉"
                    pnl_status = "Loss"
                else:
                    pnl_emoji = "➖"
                    pnl_status = "Neutral"
                
                # Handle empty symbols with fallback and note
                if trade_row.symbol and len(trade_row.symbol.strip()) > 0:
                    symbol_display = trade_row.symbol
                    unknown_note = ""
                else:
                    symbol_display = "UNKNOWN SECURITY"
                    unknown_note = "<br/><strong>Note:</strong> This trade did not have a security symbol recorded. This may indicate a data or strategy issue."
                item_title = ET.SubElement(item, 'title')
                item_title.text = f"{action_emoji} {action_desc} {trade_row.quantity:,} {symbol_display} @ ${trade_row.price:.2f} = ${trade_row.value:,.2f}"
                
                item_link = ET.SubElement(item, 'link')
                item_link.text = f"http://localhost:8000/dashboard/trade/{symbol_display}"
                
                item_description = ET.SubElement(item, 'description')
                item_description.text = f"""
                <strong>Trade Details:</strong><br/>
                <strong>Security:</strong> {symbol_display}<br/>
                <strong>Transaction Type:</strong> {action_emoji} {trade_type}<br/>
                <strong>Quantity:</strong> {trade_row.quantity:,} shares<br/>
                <strong>Price:</strong> ${trade_row.price:.2f}<br/>
                <strong>Total Value:</strong> ${trade_row.value:,.2f}<br/>
                <strong>Trade Impact:</strong> {trade_impact}<br/>
                <strong>P&L:</strong> {pnl_emoji} ${trade_row.pnl:,.2f} ({pnl_status})<br/>
                <strong>Confidence:</strong> {trade_row.confidence:.1%}<br/>
                <strong>Strategy:</strong> {trade_row.strategy_name or 'Unknown'}<br/>
                <strong>Backtest:</strong> {trade_row.backtest_name or 'Unknown'}<br/>
                <strong>Portfolio Value:</strong> ${trade_row.portfolio_value:,.2f}<br/>
                <strong>Cash Balance:</strong> ${trade_row.cash:,.2f}<br/>
                <strong>Position Value:</strong> ${trade_row.position_value:,.2f}<br/>
                <strong>Total P&L:</strong> ${trade_row.total_pnl:,.2f}<br/>
                <strong>Backtest Performance:</strong> {trade_row.total_return_pct:+.2f}%<br/>
                <strong>Initial Capital:</strong> ${trade_row.initial_capital:,.2f}<br/>
                <strong>Final Capital:</strong> ${trade_row.final_capital:,.2f}
                {unknown_note}
                """
                
                item_pub_date = ET.SubElement(item, 'pubDate')
                item_pub_date.text = trade_row.timestamp.strftime('%a, %d %b %Y %H:%M:%S %z') if trade_row.timestamp else datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
                
                item_guid = ET.SubElement(item, 'guid')
                item_guid.text = f"trade_{symbol_display}_{trade_row.action}_{trade_row.timestamp.isoformat()}"
            
            # Add a summary item if no trades found
            if not trades_result.fetchone():
                item = ET.SubElement(channel, 'item')
                item_title = ET.SubElement(item, 'title')
                item_title.text = "📊 No Recent Trades"
                
                item_description = ET.SubElement(item, 'description')
                item_description.text = """
                <strong>Trading Activity Status:</strong><br/>
                No recent trading activity detected.<br/>
                This could indicate:<br/>
                • No backtest runs have been completed<br/>
                • Strategies are in observation mode<br/>
                • Market conditions are unfavorable<br/>
                • Risk management is preventing trades
                """
                
                item_pub_date = ET.SubElement(item, 'pubDate')
                item_pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
                
                item_guid = ET.SubElement(item, 'guid')
                item_guid.text = "no_trades_status"
            
            # Pretty print XML
            rough_string = ET.tostring(rss, 'unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
            
    except Exception as e:
        logger.error(f"Failed to generate trades RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate RSS feed: {str(e)}")

@app.get("/dashboard/rss/positions", response_class=PlainTextResponse)
async def get_positions_rss_feed():
    """Get RSS feed for active positions"""
    try:
        portfolio_summary = await get_portfolio_summary()
        
        # Create RSS feed
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        
        title = ET.SubElement(channel, 'title')
        title.text = 'Space Trading Station - Active Positions'
        
        link = ET.SubElement(channel, 'link')
        link.text = 'http://localhost:8000/dashboard/rss/positions'
        
        description = ET.SubElement(channel, 'description')
        description.text = f'Active trading positions. Total Value: ${portfolio_summary.total_value:,.2f}, P&L: ${portfolio_summary.total_pnl:,.2f} ({portfolio_summary.total_pnl_percentage:+.2f}%)'
        
        last_build_date = ET.SubElement(channel, 'lastBuildDate')
        last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        for position in portfolio_summary.positions:
            item = ET.SubElement(channel, 'item')
            
            item_title = ET.SubElement(item, 'title')
            item_title.text = f"{position.symbol}: {position.quantity} shares @ ${position.avg_price:.2f} (P&L: ${position.unrealized_pnl:+.2f})"
            
            item_link = ET.SubElement(item, 'link')
            item_link.text = f"http://localhost:8000/dashboard/position/{position.symbol}"
            
            item_description = ET.SubElement(item, 'description')
            item_description.text = f"""
            <strong>Position Details:</strong><br/>
            Symbol: {position.symbol}<br/>
            Quantity: {position.quantity}<br/>
            Average Price: ${position.avg_price:.2f}<br/>
            Current Price: ${position.current_price:.2f}<br/>
            Market Value: ${position.market_value:.2f}<br/>
            Unrealized P&L: ${position.unrealized_pnl:+.2f} ({position.unrealized_pnl_percent:+.2f}%)<br/>
            Strategy: {position.strategy}<br/>
            Entry Date: {position.entry_date}<br/>
            Holding Days: {position.holding_days}
            """
            
            item_pub_date = ET.SubElement(item, 'pubDate')
            item_pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            item_guid = ET.SubElement(item, 'guid')
            item_guid.text = f"position_{position.symbol}"
        
        # Pretty print XML
        rough_string = ET.tostring(rss, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
        
    except Exception as e:
        logger.error(f"Failed to generate positions RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate RSS feed: {str(e)}")

@app.get("/dashboard/rss/strategy-events", response_class=PlainTextResponse)
async def get_strategy_events_rss_feed():
    """Get RSS feed for strategy events and signals"""
    try:
        engine = get_database_connection()
        if not engine:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        with engine.connect() as conn:
            # Get recent trades with strategy information and create events
            events_result = conn.execute(text("""
                SELECT 
                    bt.timestamp,
                    bt.symbol,
                    bt.action,
                    bt.confidence,
                    bt.portfolio_value,
                    bt.total_pnl,
                    bt.quantity,
                    bt.price,
                    bt.value,
                    br.strategy_name,
                    br.backtest_name
                FROM backtest_trades bt
                JOIN backtest_runs br ON bt.run_id = br.run_id
                ORDER BY LENGTH(bt.symbol) DESC, bt.timestamp DESC
                LIMIT 100
            """))
            
            # Create RSS feed
            rss = ET.Element('rss', version='2.0')
            channel = ET.SubElement(rss, 'channel')
            
            title = ET.SubElement(channel, 'title')
            title.text = 'Space Trading Station - Strategy Events & Signals'
            
            link = ET.SubElement(channel, 'link')
            link.text = 'http://localhost:8000/dashboard/rss/strategy-events'
            
            description = ET.SubElement(channel, 'description')
            description.text = 'Trading signals, strategy events, and market analysis from the Space Trading Station'
            
            last_build_date = ET.SubElement(channel, 'lastBuildDate')
            last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Track unique events to avoid duplicates
            seen_events = set()
            
            for event_row in events_result:
                # Create unique event identifier
                event_id = f"{event_row.strategy_name}_{event_row.symbol}_{event_row.action}_{event_row.timestamp.strftime('%Y%m%d_%H%M')}"
                
                if event_id in seen_events:
                    continue
                seen_events.add(event_id)
                
                # Determine event type and significance
                if event_row.confidence > 0.8:
                    event_type = "🔥 STRONG_SIGNAL"
                    signal_strength = "🔥 Strong Signal"
                    significance = "HIGH"
                elif event_row.confidence > 0.7:
                    event_type = "✅ CONFIRMED_SIGNAL"
                    signal_strength = "✅ Confirmed Signal"
                    significance = "MEDIUM"
                elif event_row.confidence > 0.6:
                    event_type = "📊 SIGNAL"
                    signal_strength = "📊 Signal"
                    significance = "LOW"
                else:
                    event_type = "📈 TRADE_EXECUTED"
                    signal_strength = "📈 Trade Executed"
                    significance = "EXECUTION"
                
                # Create detailed event title
                if event_row.action == "BUY":
                    action_emoji = "🟢"
                    action_desc = "BUY"
                else:
                    action_emoji = "🔴"
                    action_desc = "SELL"
                
                item = ET.SubElement(channel, 'item')
                
                # Handle empty symbols with fallback
                symbol_display = event_row.symbol if event_row.symbol and len(event_row.symbol.strip()) > 0 else "UNKNOWN"
                
                item_title = ET.SubElement(item, 'title')
                item_title.text = f"{event_type}: {action_emoji} {action_desc} {symbol_display} ({event_row.confidence:.1%} confidence)"
                
                item_link = ET.SubElement(item, 'link')
                item_link.text = f"http://localhost:8000/dashboard/strategy/{event_row.strategy_name}"
                
                # Enhanced description with more details
                item_description = ET.SubElement(item, 'description')
                item_description.text = f"""
                <strong>Strategy Event Details:</strong><br/>
                <strong>Event Type:</strong> {event_type}<br/>
                <strong>Strategy:</strong> {event_row.strategy_name}<br/>
                <strong>Backtest:</strong> {event_row.backtest_name or 'Unknown'}<br/>
                <strong>Symbol:</strong> {symbol_display}<br/>
                <strong>Action:</strong> {action_emoji} {action_desc}<br/>
                <strong>Quantity:</strong> {event_row.quantity:,} shares<br/>
                <strong>Price:</strong> ${event_row.price:.2f}<br/>
                <strong>Value:</strong> ${event_row.value:,.2f}<br/>
                <strong>Confidence:</strong> {event_row.confidence:.1%}<br/>
                <strong>Signal Strength:</strong> {signal_strength}<br/>
                <strong>Significance:</strong> {significance}<br/>
                <strong>Portfolio Value:</strong> ${event_row.portfolio_value:,.2f}<br/>
                <strong>Total P&L:</strong> ${event_row.total_pnl:,.2f}<br/>
                <strong>Market Impact:</strong> {'High' if event_row.value > 10000 else 'Medium' if event_row.value > 5000 else 'Low'}<br/>
                <strong>Strategy Performance:</strong> {'Profitable' if event_row.total_pnl > 0 else 'Loss' if event_row.total_pnl < 0 else 'Neutral'}
                """
                
                item_pub_date = ET.SubElement(item, 'pubDate')
                item_pub_date.text = event_row.timestamp.strftime('%a, %d %b %Y %H:%M:%S %z') if event_row.timestamp else datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
                
                item_guid = ET.SubElement(item, 'guid')
                item_guid.text = f"event_{event_id}"
            
            # Add a summary item if no events found
            if not seen_events:
                item = ET.SubElement(channel, 'item')
                item_title = ET.SubElement(item, 'title')
                item_title.text = "📊 No Recent Strategy Events"
                
                item_description = ET.SubElement(item, 'description')
                item_description.text = """
                <strong>Strategy Events Status:</strong><br/>
                No recent high-confidence trading signals or strategy events detected.<br/>
                This could indicate:<br/>
                • Markets are in a neutral state<br/>
                • Strategies are waiting for better opportunities<br/>
                • Risk management is preventing low-confidence trades<br/>
                • Recent backtest data is being processed
                """
                
                item_pub_date = ET.SubElement(item, 'pubDate')
                item_pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
                
                item_guid = ET.SubElement(item, 'guid')
                item_guid.text = "no_events_status"
            
            # Pretty print XML
            rough_string = ET.tostring(rss, 'unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
            
    except Exception as e:
        logger.error(f"Failed to generate strategy events RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate RSS feed: {str(e)}")

@app.get("/dashboard/rss/portfolio-summary", response_class=PlainTextResponse)
async def get_portfolio_summary_rss_feed():
    """Get RSS feed for portfolio summary"""
    try:
        portfolio_summary = await get_portfolio_summary()
        
        # Create RSS feed
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        
        title = ET.SubElement(channel, 'title')
        title.text = 'Space Trading Station - Portfolio Summary'
        
        link = ET.SubElement(channel, 'link')
        link.text = 'http://localhost:8000/dashboard/rss/portfolio-summary'
        
        description = ET.SubElement(channel, 'description')
        description.text = f'Portfolio Summary - Total Value: ${portfolio_summary.total_value:,.2f}, P&L: ${portfolio_summary.total_pnl:,.2f} ({portfolio_summary.total_pnl_percentage:+.2f}%), Positions: {portfolio_summary.num_positions}'
        
        last_build_date = ET.SubElement(channel, 'lastBuildDate')
        last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Portfolio summary item
        item = ET.SubElement(channel, 'item')
        
        item_title = ET.SubElement(item, 'title')
        item_title.text = f"Portfolio Summary - ${portfolio_summary.total_value:,.2f} ({portfolio_summary.total_pnl_percentage:+.2f}%)"
        
        item_link = ET.SubElement(item, 'link')
        item_link.text = 'http://localhost:8000/dashboard/portfolio/summary'
        
        item_description = ET.SubElement(item, 'description')
        
        # Build detailed description
        desc_parts = [
            f"<strong>Portfolio Summary:</strong><br/>",
            f"Total Value: ${portfolio_summary.total_value:,.2f}<br/>",
            f"Cash: ${portfolio_summary.cash:,.2f}<br/>",
            f"Total P&L: ${portfolio_summary.total_pnl:,.2f} ({portfolio_summary.total_pnl_percentage:+.2f}%)<br/>",
            f"Active Positions: {portfolio_summary.num_positions}<br/><br/>"
        ]
        
        if portfolio_summary.positions:
            desc_parts.append("<strong>Active Positions:</strong><br/>")
            for pos in portfolio_summary.positions:
                desc_parts.append(
                    f"• {pos.symbol}: {pos.quantity} shares @ ${pos.avg_price:.2f} "
                    f"(P&L: ${pos.unrealized_pnl:+.2f}, {pos.unrealized_pnl_percent:+.2f}%)<br/>"
                )
        
        if portfolio_summary.recent_trades:
            desc_parts.append("<br/><strong>Recent Trades:</strong><br/>")
            for trade in portfolio_summary.recent_trades[:5]:  # Show last 5 trades
                desc_parts.append(
                    f"• {trade.action} {trade.quantity} {trade.symbol} @ ${trade.price:.2f} "
                    f"(P&L: ${trade.pnl:+.2f})<br/>"
                )
        
        item_description.text = "".join(desc_parts)
        
        item_pub_date = ET.SubElement(item, 'pubDate')
        item_pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        item_guid = ET.SubElement(item, 'guid')
        item_guid.text = f"portfolio_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Pretty print XML
        rough_string = ET.tostring(rss, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
        
    except Exception as e:
        logger.error(f"Failed to generate portfolio summary RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate RSS feed: {str(e)}")

@app.get("/dashboard/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "trading-dashboard", "timestamp": datetime.now().isoformat()}

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard HTML page"""
    try:
        with open("dashboard.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
        <head><title>Trading Dashboard</title></head>
        <body>
            <h1>Trading Dashboard Service</h1>
            <p>Dashboard HTML file not found. Available endpoints:</p>
            <ul>
                <li><a href="/dashboard/portfolio/summary">Portfolio Summary (JSON)</a></li>
                <li><a href="/dashboard/rss/trades">Recent Trades (RSS)</a></li>
                <li><a href="/dashboard/rss/positions">Active Positions (RSS)</a></li>
                <li><a href="/dashboard/rss/strategy-events">Strategy Events (RSS)</a></li>
                <li><a href="/dashboard/rss/portfolio-summary">Portfolio Summary (RSS)</a></li>
            </ul>
        </body>
        </html>
        """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 