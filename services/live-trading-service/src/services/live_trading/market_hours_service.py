"""
Market Hours Service

Handles market hours validation and trading time restrictions.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, time, timedelta, timezone
from dataclasses import dataclass
import pytz

logger = logging.getLogger(__name__)


@dataclass
class MarketHours:
    """Market hours configuration."""
    open_time: time = time(9, 30)  # 9:30 AM ET
    close_time: time = time(16, 0)  # 4:00 PM ET
    timezone: str = "US/Eastern"


@dataclass
class MarketStatus:
    """Market status information."""
    is_open: bool
    current_time: datetime
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    reason: Optional[str] = None


class MarketHoursService:
    """Service for managing market hours and trading time restrictions."""
    
    def __init__(self, market_hours: Optional[MarketHours] = None):
        """Initialize the market hours service."""
        self.market_hours = market_hours or MarketHours()
        self.et_timezone = pytz.timezone(self.market_hours.timezone)
        
        # Market holidays (simplified list)
        self.holidays = [
            (1, 1),   # New Year's Day
            (1, 15),  # Martin Luther King Jr. Day (third Monday)
            (2, 19),  # Presidents' Day (third Monday)
            (3, 29),  # Good Friday (varies by year)
            (5, 27),  # Memorial Day (last Monday)
            (6, 19),  # Juneteenth
            (7, 4),   # Independence Day
            (9, 2),   # Labor Day (first Monday)
            (11, 28), # Thanksgiving Day (fourth Thursday)
            (12, 25), # Christmas Day
        ]
    
    async def is_market_open(self) -> bool:
        """
        Check if the market is currently open.
        
        Returns:
            True if market is open, False otherwise
        """
        try:
            market_status = await self.get_market_status()
            return market_status.is_open
        except Exception as e:
            logger.error(f"Error checking market hours: {str(e)}")
            return False
    
    async def get_market_status(self) -> MarketStatus:
        """
        Get current market status.
        
        Returns:
            Market status information
        """
        try:
            current_time = datetime.now(self.et_timezone)
            current_date = current_time.date()
            current_time_only = current_time.time()
            
            # Check if it's a weekend
            if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                next_open = self._get_next_market_open(current_date)
                return MarketStatus(
                    is_open=False,
                    current_time=current_time,
                    next_open=next_open,
                    reason="Weekend - Market closed"
                )
            
            # Check if it's a holiday
            if self._is_market_holiday(current_date):
                holiday_name = self._get_holiday_name(current_date)
                next_open = self._get_next_market_open(current_date)
                return MarketStatus(
                    is_open=False,
                    current_time=current_time,
                    next_open=next_open,
                    reason=f"Market Holiday - {holiday_name}"
                )
            
            # Check if it's within market hours
            if self.market_hours.open_time <= current_time_only <= self.market_hours.close_time:
                next_close = self._get_next_market_close(current_time)
                return MarketStatus(
                    is_open=True,
                    current_time=current_time,
                    next_close=next_close
                )
            
            # Market is closed
            if current_time_only < self.market_hours.open_time:
                # Before market open
                next_open = self._get_next_market_open(current_date)
                return MarketStatus(
                    is_open=False,
                    current_time=current_time,
                    next_open=next_open,
                    reason="Pre-market hours - Trading not allowed"
                )
            else:
                # After market close
                next_open = self._get_next_market_open(current_date + timedelta(days=1))
                return MarketStatus(
                    is_open=False,
                    current_time=current_time,
                    next_open=next_open,
                    reason="After hours - Trading not allowed"
                )
            
        except Exception as e:
            logger.error(f"Error getting market status: {str(e)}")
            return MarketStatus(
                is_open=False,
                current_time=datetime.now(self.et_timezone),
                reason=f"Error determining market status: {str(e)}"
            )
    
    async def get_next_market_open(self) -> Dict[str, Any]:
        """
        Get next market open time.
        
        Returns:
            Next market open information
        """
        try:
            current_time = datetime.now(self.et_timezone)
            next_open = self._get_next_market_open(current_time.date())
            
            if next_open:
                hours_until_open = (next_open - current_time).total_seconds() / 3600
                return {
                    "next_open": next_open.isoformat(),
                    "hours_until_open": round(hours_until_open, 2),
                    "days_until_open": round(hours_until_open / 24, 2)
                }
            else:
                return {
                    "next_open": None,
                    "hours_until_open": None,
                    "days_until_open": None
                }
                
        except Exception as e:
            logger.error(f"Error getting next market open: {str(e)}")
            return {
                "next_open": None,
                "hours_until_open": None,
                "days_until_open": None,
                "error": str(e)
            }
    
    async def get_next_market_close(self) -> Dict[str, Any]:
        """
        Get next market close time.
        
        Returns:
            Next market close information
        """
        try:
            current_time = datetime.now(self.et_timezone)
            next_close = self._get_next_market_close(current_time)
            
            if next_close:
                hours_until_close = (next_close - current_time).total_seconds() / 3600
                return {
                    "next_close": next_close.isoformat(),
                    "hours_until_close": round(hours_until_close, 2),
                    "minutes_until_close": round(hours_until_close * 60, 0)
                }
            else:
                return {
                    "next_close": None,
                    "hours_until_close": None,
                    "minutes_until_close": None
                }
                
        except Exception as e:
            logger.error(f"Error getting next market close: {str(e)}")
            return {
                "next_close": None,
                "hours_until_close": None,
                "minutes_until_close": None,
                "error": str(e)
            }
    
    async def validate_trading_time(self) -> Dict[str, Any]:
        """
        Validate if trading is allowed at current time.
        
        Returns:
            Trading time validation result
        """
        try:
            market_status = await self.get_market_status()
            
            if market_status.is_open:
                return {
                    "trading_allowed": True,
                    "reason": "Market is open",
                    "current_time": market_status.current_time.isoformat(),
                    "next_close": market_status.next_close.isoformat() if market_status.next_close else None
                }
            else:
                return {
                    "trading_allowed": False,
                    "reason": market_status.reason or "Market is closed",
                    "current_time": market_status.current_time.isoformat(),
                    "next_open": market_status.next_open.isoformat() if market_status.next_open else None
                }
                
        except Exception as e:
            logger.error(f"Error validating trading time: {str(e)}")
            return {
                "trading_allowed": False,
                "reason": f"Error validating trading time: {str(e)}",
                "current_time": datetime.now(self.et_timezone).isoformat()
            }
    
    async def get_market_calendar(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get market calendar for date range.
        
        Args:
            start_date: Start date for calendar
            end_date: End date for calendar
            
        Returns:
            Market calendar information
        """
        try:
            calendar = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                is_trading_day = True
                reason = None
                
                # Check weekend
                if current_date.weekday() >= 5:
                    is_trading_day = False
                    reason = "Weekend"
                
                # Check holiday
                elif self._is_market_holiday(current_date):
                    is_trading_day = False
                    reason = self._get_holiday_name(current_date)
                
                calendar.append({
                    "date": current_date.isoformat(),
                    "is_trading_day": is_trading_day,
                    "reason": reason,
                    "market_open": f"{current_date}T{self.market_hours.open_time.strftime('%H:%M:%S')}" if is_trading_day else None,
                    "market_close": f"{current_date}T{self.market_hours.close_time.strftime('%H:%M:%S')}" if is_trading_day else None
                })
                
                current_date += timedelta(days=1)
            
            return {
                "calendar": calendar,
                "total_days": len(calendar),
                "trading_days": len([d for d in calendar if d["is_trading_day"]]),
                "non_trading_days": len([d for d in calendar if not d["is_trading_day"]])
            }
            
        except Exception as e:
            logger.error(f"Error getting market calendar: {str(e)}")
            return {
                "calendar": [],
                "total_days": 0,
                "trading_days": 0,
                "non_trading_days": 0,
                "error": str(e)
            }
    
    async def get_trading_session_info(self) -> Dict[str, Any]:
        """
        Get current trading session information.
        
        Returns:
            Trading session information
        """
        try:
            market_status = await self.get_market_status()
            current_time = market_status.current_time
            
            # Calculate session metrics
            session_start = current_time.replace(
                hour=self.market_hours.open_time.hour,
                minute=self.market_hours.open_time.minute,
                second=0,
                microsecond=0
            )
            
            session_end = current_time.replace(
                hour=self.market_hours.close_time.hour,
                minute=self.market_hours.close_time.minute,
                second=0,
                microsecond=0
            )
            
            session_duration = (session_end - session_start).total_seconds() / 3600
            
            if market_status.is_open:
                time_elapsed = (current_time - session_start).total_seconds() / 3600
                time_remaining = (session_end - current_time).total_seconds() / 3600
                session_progress = (time_elapsed / session_duration) * 100
            else:
                time_elapsed = 0
                time_remaining = 0
                session_progress = 0
            
            return {
                "session_start": session_start.isoformat(),
                "session_end": session_end.isoformat(),
                "session_duration_hours": session_duration,
                "time_elapsed_hours": time_elapsed,
                "time_remaining_hours": time_remaining,
                "session_progress_percent": session_progress,
                "is_active": market_status.is_open,
                "current_time": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting trading session info: {str(e)}")
            return {
                "error": str(e),
                "current_time": datetime.now(self.et_timezone).isoformat()
            }
    
    # Private helper methods
    
    def _is_market_holiday(self, date: datetime.date) -> bool:
        """Check if date is a market holiday."""
        try:
            # Check fixed holidays
            month_day = (date.month, date.day)
            if month_day in self.holidays:
                return True
            
            # Check variable holidays (simplified)
            year = date.year
            
            # Martin Luther King Jr. Day (third Monday in January)
            if date.month == 1:
                third_monday = self._get_nth_weekday_in_month(year, 1, 0, 3)  # Monday = 0
                if date == third_monday:
                    return True
            
            # Presidents' Day (third Monday in February)
            if date.month == 2:
                third_monday = self._get_nth_weekday_in_month(year, 2, 0, 3)
                if date == third_monday:
                    return True
            
            # Memorial Day (last Monday in May)
            if date.month == 5:
                last_monday = self._get_last_weekday_in_month(year, 5, 0)
                if date == last_monday:
                    return True
            
            # Labor Day (first Monday in September)
            if date.month == 9:
                first_monday = self._get_nth_weekday_in_month(year, 9, 0, 1)
                if date == first_monday:
                    return True
            
            # Thanksgiving Day (fourth Thursday in November)
            if date.month == 11:
                fourth_thursday = self._get_nth_weekday_in_month(year, 11, 3, 4)  # Thursday = 3
                if date == fourth_thursday:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _get_holiday_name(self, date: datetime.date) -> str:
        """Get holiday name for date."""
        holiday_names = {
            (1, 1): "New Year's Day",
            (1, 15): "Martin Luther King Jr. Day",
            (2, 19): "Presidents' Day",
            (3, 29): "Good Friday",
            (5, 27): "Memorial Day",
            (6, 19): "Juneteenth",
            (7, 4): "Independence Day",
            (9, 2): "Labor Day",
            (11, 28): "Thanksgiving Day",
            (12, 25): "Christmas Day"
        }
        
        month_day = (date.month, date.day)
        return holiday_names.get(month_day, "Market Holiday")
    
    def _get_nth_weekday_in_month(self, year: int, month: int, weekday: int, n: int) -> datetime.date:
        """Get nth weekday in month."""
        first_day = datetime.date(year, month, 1)
        first_weekday = first_day.weekday()
        
        # Calculate days to first occurrence of target weekday
        days_to_target = (weekday - first_weekday) % 7
        
        # Calculate target date
        target_date = first_day + timedelta(days=days_to_target + (n - 1) * 7)
        
        return target_date
    
    def _get_last_weekday_in_month(self, year: int, month: int, weekday: int) -> datetime.date:
        """Get last weekday in month."""
        # Get last day of month
        if month == 12:
            last_day = datetime.date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime.date(year, month + 1, 1) - timedelta(days=1)
        
        # Find last occurrence of target weekday
        days_back = (last_day.weekday() - weekday) % 7
        target_date = last_day - timedelta(days=days_back)
        
        return target_date
    
    def _get_next_market_open(self, current_date: datetime.date) -> Optional[datetime]:
        """Get next market open datetime."""
        try:
            # Start from current date
            check_date = current_date
            
            # Check up to 7 days ahead
            for _ in range(7):
                # Skip weekends
                if check_date.weekday() < 5 and not self._is_market_holiday(check_date):
                    market_open = self.et_timezone.localize(
                        datetime.combine(check_date, self.market_hours.open_time)
                    )
                    return market_open
                
                check_date += timedelta(days=1)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting next market open: {str(e)}")
            return None
    
    def _get_next_market_close(self, current_time: datetime) -> Optional[datetime]:
        """Get next market close datetime."""
        try:
            current_date = current_time.date()
            
            # If it's a trading day, return close time for today
            if current_date.weekday() < 5 and not self._is_market_holiday(current_date):
                market_close = self.et_timezone.localize(
                    datetime.combine(current_date, self.market_hours.close_time)
                )
                return market_close
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting next market close: {str(e)}")
            return None
