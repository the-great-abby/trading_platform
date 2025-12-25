"""
Position Parser for Public.com Portfolio Data
==============================================
Parses position data from Public.com's portfolio/v2 API endpoint
and converts it to our internal database format.

Handles both stock and options positions.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PublicPositionParser:
    """Parser for Public.com position data"""
    
    @staticmethod
    def parse_position(position_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a position from Public.com portfolio/v2 response.
        
        Args:
            position_data: Position data from Public.com
            
        Returns:
            Parsed position data for database storage
        """
        try:
            instrument = position_data.get("instrument", {})
            instrument_type = instrument.get("type")  # EQUITY or OPTION
            symbol = instrument.get("symbol")
            
            if not symbol:
                logger.warning("Position missing symbol, skipping")
                return None
            
            # Common fields
            quantity = float(position_data.get("quantity", 0))
            
            # Get cost basis
            cost_basis = position_data.get("costBasis", {})
            unit_cost = float(cost_basis.get("unitCost", 0))
            total_cost = float(cost_basis.get("totalCost", 0))
            
            # Get current value
            current_value = float(position_data.get("currentValue", 0))
            
            # Get last price
            last_price_data = position_data.get("lastPrice", {})
            current_price = float(last_price_data.get("lastPrice", 0))
            
            # Calculate P&L
            gain_data = position_data.get("instrumentGain", {})
            unrealized_pnl = float(gain_data.get("gainValue", 0))
            unrealized_pnl_pct = float(gain_data.get("gainPercentage", 0))
            
            # Parse opened_at timestamp
            opened_at_str = position_data.get("openedAt")
            opened_at = datetime.fromisoformat(opened_at_str.replace("Z", "+00:00")) if opened_at_str else datetime.utcnow()
            
            parsed_position = {
                "symbol": symbol,
                "instrument_type": instrument_type,
                "quantity": int(quantity) if quantity else 0,
                "average_price": unit_cost,
                "current_price": current_price,
                "current_value": current_value,
                "total_cost": total_cost,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct / 100 if unrealized_pnl_pct else 0,  # Convert to decimal
                "opened_at": opened_at,
                "status": "OPEN"
            }
            
            # Handle options-specific fields
            if instrument_type == "OPTION":
                option_details = PublicPositionParser._parse_option_details(instrument)
                if option_details:
                    parsed_position.update(option_details)
            
            return parsed_position
            
        except Exception as e:
            logger.error(f"Error parsing position: {e}")
            logger.error(f"Position data: {position_data}")
            return None
    
    @staticmethod
    def _parse_option_details(instrument: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse option-specific details from instrument data.
        
        Public.com option symbol format: "AAPL250117C00150000"
        Which decodes to: AAPL Jan 17, 2025 $150 Call
        
        Args:
            instrument: Instrument dict from Public.com
            
        Returns:
            Option details dict
        """
        try:
            symbol = instrument.get("symbol", "")
            name = instrument.get("name", "")
            
            # Option symbol format from Public.com:
            # Example: "SPY251021C00580000" = SPY Oct 21, 2025 $580 Call
            # Format: [TICKER][YYMMDD][C/P][STRIKE*1000]
            
            if len(symbol) < 15:
                logger.warning(f"Option symbol too short: {symbol}")
                return None
            
            # Parse option symbol
            underlying = symbol[:symbol.find("2")]  # Get ticker before year
            
            # Find C or P for call/put
            c_index = symbol.find("C")
            p_index = symbol.find("P")
            
            if c_index > 0:
                option_type = "CALL"
                date_str = symbol[len(underlying):c_index]
                strike_str = symbol[c_index+1:]
            elif p_index > 0:
                option_type = "PUT"
                date_str = symbol[len(underlying):p_index]
                strike_str = symbol[p_index+1:]
            else:
                logger.warning(f"Could not determine option type from symbol: {symbol}")
                return None
            
            # Parse date (YYMMDD)
            year = 2000 + int(date_str[0:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            expiration = datetime(year, month, day)
            
            # Parse strike (divided by 1000)
            strike = float(strike_str) / 1000.0
            
            logger.info(f"📊 Parsed option: {underlying} {expiration.strftime('%Y-%m-%d')} ${strike} {option_type}")
            
            return {
                "underlying_symbol": underlying,
                "option_type": option_type,
                "strike_price": strike,
                "expiration_date": expiration,
                "option_symbol": symbol
            }
            
        except Exception as e:
            logger.error(f"Error parsing option details: {e}")
            logger.error(f"Instrument: {instrument}")
            return None
    
    @staticmethod
    def parse_positions_list(positions_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse multiple positions from Public.com.
        
        Args:
            positions_list: List of positions from Public.com
            
        Returns:
            List of parsed positions
        """
        parsed_positions = []
        
        for position in positions_list:
            parsed = PublicPositionParser.parse_position(position)
            if parsed:
                parsed_positions.append(parsed)
        
        logger.info(f"✅ Parsed {len(parsed_positions)}/{len(positions_list)} positions successfully")
        
        return parsed_positions









