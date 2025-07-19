"""
Economic Calendar Events System
Provides structured economic events for trading strategies
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import calendar
from loguru import logger


@dataclass
class EconomicEvent:
    """Economic calendar event"""
    event_type: str
    date: date
    time: Optional[str] = None  # "08:30", "14:00", etc.
    description: str = ""
    impact_level: str = "medium"  # low, medium, high, critical
    affected_sectors: List[str] = None
    volatility_multiplier: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.affected_sectors is None:
            self.affected_sectors = []
        if self.metadata is None:
            self.metadata = {}


class EconomicCalendar:
    """Economic calendar for trading strategies"""
    
    def __init__(self):
        self.events = []
        self._initialize_calendar()
    
    def _initialize_calendar(self):
        """Initialize the economic calendar with recurring events"""
        current_year = datetime.now().year
        
        # FOMC Meeting Dates (typically 8 meetings per year)
        fomc_dates = [
            f"{current_year}-01-31", f"{current_year}-03-20", f"{current_year}-05-01",
            f"{current_year}-06-12", f"{current_year}-07-31", f"{current_year}-09-18",
            f"{current_year}-11-07", f"{current_year}-12-18"
        ]
        
        for fomc_date in fomc_dates:
            self.events.append(EconomicEvent(
                event_type="fomc_meeting",
                date=datetime.strptime(fomc_date, "%Y-%m-%d").date(),
                time="14:00",
                description="Federal Open Market Committee Meeting",
                impact_level="critical",
                affected_sectors=["financial", "technology", "real_estate"],
                volatility_multiplier=1.5,
                metadata={"rate_decision": True, "dot_plot": True}
            ))
        
        # Earnings Seasons (Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec)
        earnings_seasons = [
            (f"{current_year}-01-15", f"{current_year}-02-15", "Q4 Earnings Season"),
            (f"{current_year}-04-15", f"{current_year}-05-15", "Q1 Earnings Season"),
            (f"{current_year}-07-15", f"{current_year}-08-15", "Q2 Earnings Season"),
            (f"{current_year}-10-15", f"{current_year}-11-15", "Q3 Earnings Season"),
        ]
        
        for start_date, end_date, description in earnings_seasons:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Add earnings season events
            self.events.append(EconomicEvent(
                event_type="earnings_season",
                date=start,
                description=f"{description} Start",
                impact_level="high",
                affected_sectors=["all"],
                volatility_multiplier=1.3,
                metadata={"season_duration": (end - start).days}
            ))
            
            self.events.append(EconomicEvent(
                event_type="earnings_season",
                date=end,
                description=f"{description} End",
                impact_level="medium",
                affected_sectors=["all"],
                volatility_multiplier=1.1,
                metadata={"season_duration": (end - start).days}
            ))
        
        # Options Expiration (Third Friday of each month)
        for month in range(1, 13):
            third_friday = self._get_third_friday(current_year, month)
            self.events.append(EconomicEvent(
                event_type="options_expiry",
                date=third_friday,
                description="Monthly Options Expiration",
                impact_level="medium",
                affected_sectors=["all"],
                volatility_multiplier=1.2,
                metadata={"expiry_type": "monthly"}
            ))
        
        # Economic Data Releases
        self._add_economic_data_events(current_year)
        
        # Holiday Effects
        self._add_holiday_effects(current_year)
    
    def _get_third_friday(self, year: int, month: int) -> date:
        """Get the third Friday of a given month"""
        c = calendar.monthcalendar(year, month)
        for week in c:
            if week[calendar.FRIDAY] != 0:
                return date(year, month, week[calendar.FRIDAY])
        return date(year, month, 1)  # Fallback
    
    def _add_economic_data_events(self, year: int):
        """Add economic data release events"""
        
        # CPI Releases (typically around 13th of each month)
        for month in range(1, 13):
            cpi_date = date(year, month, 13)
            self.events.append(EconomicEvent(
                event_type="cpi_release",
                date=cpi_date,
                time="08:30",
                description="Consumer Price Index Release",
                impact_level="high",
                affected_sectors=["financial", "real_estate", "consumer"],
                volatility_multiplier=1.4,
                metadata={"data_type": "inflation"}
            ))
        
        # Jobs Report (First Friday of each month)
        for month in range(1, 13):
            first_friday = self._get_first_friday(year, month)
            self.events.append(EconomicEvent(
                event_type="jobs_report",
                date=first_friday,
                time="08:30",
                description="Non-Farm Payrolls Report",
                impact_level="high",
                affected_sectors=["all"],
                volatility_multiplier=1.4,
                metadata={"data_type": "employment"}
            ))
        
        # GDP Releases (Quarterly)
        gdp_dates = [
            f"{year}-01-26", f"{year}-04-26", f"{year}-07-26", f"{year}-10-26"
        ]
        
        for gdp_date in gdp_dates:
            self.events.append(EconomicEvent(
                event_type="gdp_release",
                date=datetime.strptime(gdp_date, "%Y-%m-%d").date(),
                time="08:30",
                description="GDP Growth Rate Release",
                impact_level="high",
                affected_sectors=["all"],
                volatility_multiplier=1.3,
                metadata={"data_type": "growth"}
            ))
    
    def _get_first_friday(self, year: int, month: int) -> date:
        """Get the first Friday of a given month"""
        c = calendar.monthcalendar(year, month)
        for week in c:
            if week[calendar.FRIDAY] != 0:
                return date(year, month, week[calendar.FRIDAY])
        return date(year, month, 1)  # Fallback
    
    def _add_holiday_effects(self, year: int):
        """Add holiday-related market effects"""
        
        # Pre-holiday effects (day before major holidays)
        holidays = [
            (f"{year}-01-01", "New Year's Day"),
            (f"{year}-07-04", "Independence Day"),
            (f"{year}-12-25", "Christmas Day"),
        ]
        
        for holiday_date, description in holidays:
            holiday = datetime.strptime(holiday_date, "%Y-%m-%d").date()
            pre_holiday = holiday - timedelta(days=1)
            
            self.events.append(EconomicEvent(
                event_type="pre_holiday",
                date=pre_holiday,
                description=f"Pre-{description} Trading",
                impact_level="low",
                affected_sectors=["all"],
                volatility_multiplier=0.8,
                metadata={"holiday": description}
            ))
    
    def get_events_for_date(self, target_date: date) -> List[EconomicEvent]:
        """Get all economic events for a specific date"""
        return [event for event in self.events if event.date == target_date]
    
    def get_events_for_period(self, start_date: date, end_date: date) -> List[EconomicEvent]:
        """Get all economic events in a date range"""
        return [event for event in self.events if start_date <= event.date <= end_date]
    
    def get_events_by_type(self, event_type: str) -> List[EconomicEvent]:
        """Get all events of a specific type"""
        return [event for event in self.events if event.event_type == event_type]
    
    def get_market_regime(self, target_date: date) -> Dict[str, Any]:
        """Get market regime based on economic events"""
        events = self.get_events_for_date(target_date)
        
        # Calculate volatility multiplier
        volatility_mult = 1.0
        impact_levels = []
        
        for event in events:
            volatility_mult *= event.volatility_multiplier
            impact_levels.append(event.impact_level)
        
        # Determine market regime
        if any(level == "critical" for level in impact_levels):
            regime = "high_volatility"
        elif any(level == "high" for level in impact_levels):
            regime = "elevated_volatility"
        elif any(level == "medium" for level in impact_levels):
            regime = "normal_volatility"
        else:
            regime = "low_volatility"
        
        return {
            "regime": regime,
            "volatility_multiplier": volatility_mult,
            "events": [event.event_type for event in events],
            "impact_levels": impact_levels
        }
    
    def is_earnings_season(self, target_date: date) -> bool:
        """Check if date is during earnings season"""
        events = self.get_events_for_date(target_date)
        return any(event.event_type == "earnings_season" for event in events)
    
    def is_fomc_week(self, target_date: date) -> bool:
        """Check if date is during FOMC meeting week"""
        fomc_events = self.get_events_by_type("fomc_meeting")
        for event in fomc_events:
            # Check if within 3 days of FOMC meeting
            days_diff = abs((target_date - event.date).days)
            if days_diff <= 3:
                return True
        return False


# Global economic calendar instance
economic_calendar = EconomicCalendar()


def get_economic_calendar() -> EconomicCalendar:
    """Get the global economic calendar instance"""
    return economic_calendar


def get_market_regime_for_date(target_date: date) -> Dict[str, Any]:
    """Get market regime for a specific date"""
    return economic_calendar.get_market_regime(target_date)


def is_high_impact_day(target_date: date) -> bool:
    """Check if date has high-impact economic events"""
    events = economic_calendar.get_events_for_date(target_date)
    return any(event.impact_level in ["high", "critical"] for event in events) 