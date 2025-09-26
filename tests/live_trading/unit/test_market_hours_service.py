"""
Unit tests for market hours service.

Tests market hours validation, holiday handling, and timezone conversions.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, time, timezone, timedelta
import pytz

from src.services.live_trading.market_hours_service import (
    MarketHoursService, MarketClosedError, InvalidMarketHoursError
)


@pytest.fixture
def market_hours_service():
    """Create market hours service instance."""
    return MarketHoursService()


@pytest.fixture
def et_timezone():
    """Get Eastern Time timezone."""
    return pytz.timezone('US/Eastern')


class TestMarketHoursValidation:
    """Test market hours validation methods."""
    
    def test_is_market_open_during_regular_hours(self, market_hours_service, et_timezone):
        """Test market open check during regular trading hours."""
        # Mock current time to 10:00 AM ET on a weekday
        mock_now = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0))  # Monday
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = market_hours_service.is_market_open()
            
            assert result is True
    
    def test_is_market_open_before_market_hours(self, market_hours_service, et_timezone):
        """Test market open check before trading hours."""
        # Mock current time to 8:00 AM ET on a weekday
        mock_now = et_timezone.localize(datetime(2024, 1, 15, 8, 0, 0))  # Monday
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = market_hours_service.is_market_open()
            
            assert result is False
    
    def test_is_market_open_after_market_hours(self, market_hours_service, et_timezone):
        """Test market open check after trading hours."""
        # Mock current time to 5:00 PM ET on a weekday
        mock_now = et_timezone.localize(datetime(2024, 1, 15, 17, 0, 0))  # Monday
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = market_hours_service.is_market_open()
            
            assert result is False
    
    def test_is_market_open_on_weekend(self, market_hours_service, et_timezone):
        """Test market open check on weekend."""
        # Mock current time to 10:00 AM ET on Saturday
        mock_now = et_timezone.localize(datetime(2024, 1, 13, 10, 0, 0))  # Saturday
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = market_hours_service.is_market_open()
            
            assert result is False
    
    def test_is_market_open_on_holiday(self, market_hours_service, et_timezone):
        """Test market open check on holiday."""
        # Mock current time to 10:00 AM ET on New Year's Day (holiday)
        mock_now = et_timezone.localize(datetime(2024, 1, 1, 10, 0, 0))  # New Year's Day
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = market_hours_service.is_market_open()
            
            assert result is False
    
    def test_is_market_open_on_early_close_day(self, market_hours_service, et_timezone):
        """Test market open check on early close day (like Black Friday)."""
        # Mock current time to 10:00 AM ET on Black Friday (early close at 1:00 PM)
        mock_now = et_timezone.localize(datetime(2024, 11, 29, 10, 0, 0))  # Black Friday
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = market_hours_service.is_market_open()
            
            assert result is True
    
    def test_is_market_open_on_early_close_day_after_close(self, market_hours_service, et_timezone):
        """Test market open check after early close time."""
        # Mock current time to 2:00 PM ET on Black Friday (after 1:00 PM close)
        mock_now = et_timezone.localize(datetime(2024, 11, 29, 14, 0, 0))  # Black Friday
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = market_hours_service.is_market_open()
            
            assert result is False


class TestMarketHoursCalculation:
    """Test market hours calculation methods."""
    
    def test_get_market_open_time(self, market_hours_service, et_timezone):
        """Test getting market open time for a given date."""
        # Test regular trading day
        test_date = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0))  # Monday
        
        open_time = market_hours_service.get_market_open_time(test_date.date())
        
        assert open_time.hour == 9
        assert open_time.minute == 30
        assert open_time.tzinfo == et_timezone
    
    def test_get_market_close_time_regular_day(self, market_hours_service, et_timezone):
        """Test getting market close time for a regular trading day."""
        test_date = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0))  # Monday
        
        close_time = market_hours_service.get_market_close_time(test_date.date())
        
        assert close_time.hour == 16
        assert close_time.minute == 0
        assert close_time.tzinfo == et_timezone
    
    def test_get_market_close_time_early_close(self, market_hours_service, et_timezone):
        """Test getting market close time for an early close day."""
        # Black Friday (early close at 1:00 PM)
        test_date = et_timezone.localize(datetime(2024, 11, 29, 10, 0, 0))
        
        close_time = market_hours_service.get_market_close_time(test_date.date())
        
        assert close_time.hour == 13
        assert close_time.minute == 0
        assert close_time.tzinfo == et_timezone
    
    def test_get_next_market_open(self, market_hours_service, et_timezone):
        """Test getting next market open time."""
        # Mock current time to 8:00 AM ET on Monday (before market opens)
        mock_now = et_timezone.localize(datetime(2024, 1, 15, 8, 0, 0))
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            next_open = market_hours_service.get_next_market_open()
            
            assert next_open.hour == 9
            assert next_open.minute == 30
            assert next_open.date() == mock_now.date()
    
    def test_get_next_market_open_weekend(self, market_hours_service, et_timezone):
        """Test getting next market open time on weekend."""
        # Mock current time to 10:00 AM ET on Saturday
        mock_now = et_timezone.localize(datetime(2024, 1, 13, 10, 0, 0))
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            next_open = market_hours_service.get_next_market_open()
            
            # Should be Monday at 9:30 AM
            assert next_open.weekday() == 0  # Monday
            assert next_open.hour == 9
            assert next_open.minute == 30
    
    def test_get_next_market_close(self, market_hours_service, et_timezone):
        """Test getting next market close time."""
        # Mock current time to 10:00 AM ET on Monday
        mock_now = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0))
        
        with patch('src.services.live_trading.market_hours_service.datetime') as mock_dt:
            mock_dt.now.return_value = mock_now.astimezone(timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            next_close = market_hours_service.get_next_market_close()
            
            assert next_close.hour == 16
            assert next_close.minute == 0
            assert next_close.date() == mock_now.date()
    
    def test_get_market_hours_for_date(self, market_hours_service, et_timezone):
        """Test getting market hours for a specific date."""
        test_date = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0)).date()
        
        hours = market_hours_service.get_market_hours_for_date(test_date)
        
        assert hours["open_time"].hour == 9
        assert hours["open_time"].minute == 30
        assert hours["close_time"].hour == 16
        assert hours["close_time"].minute == 0
        assert hours["is_trading_day"] is True
        assert hours["is_early_close"] is False
    
    def test_get_market_hours_for_holiday(self, market_hours_service, et_timezone):
        """Test getting market hours for a holiday."""
        # New Year's Day
        test_date = et_timezone.localize(datetime(2024, 1, 1, 10, 0, 0)).date()
        
        hours = market_hours_service.get_market_hours_for_date(test_date)
        
        assert hours["is_trading_day"] is False
        assert hours["is_holiday"] is True


class TestHolidayHandling:
    """Test holiday handling and validation."""
    
    def test_is_holiday_new_years(self, market_hours_service, et_timezone):
        """Test New Year's Day holiday detection."""
        new_years = et_timezone.localize(datetime(2024, 1, 1, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(new_years)
        
        assert result is True
    
    def test_is_holiday_martin_luther_king(self, market_hours_service, et_timezone):
        """Test Martin Luther King Day holiday detection."""
        mlk_day = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(mlk_day)
        
        assert result is True
    
    def test_is_holiday_presidents_day(self, market_hours_service, et_timezone):
        """Test Presidents Day holiday detection."""
        presidents_day = et_timezone.localize(datetime(2024, 2, 19, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(presidents_day)
        
        assert result is True
    
    def test_is_holiday_good_friday(self, market_hours_service, et_timezone):
        """Test Good Friday holiday detection."""
        good_friday = et_timezone.localize(datetime(2024, 3, 29, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(good_friday)
        
        assert result is True
    
    def test_is_holiday_memorial_day(self, market_hours_service, et_timezone):
        """Test Memorial Day holiday detection."""
        memorial_day = et_timezone.localize(datetime(2024, 5, 27, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(memorial_day)
        
        assert result is True
    
    def test_is_holiday_juneteenth(self, market_hours_service, et_timezone):
        """Test Juneteenth holiday detection."""
        juneteenth = et_timezone.localize(datetime(2024, 6, 19, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(juneteenth)
        
        assert result is True
    
    def test_is_holiday_independence_day(self, market_hours_service, et_timezone):
        """Test Independence Day holiday detection."""
        independence_day = et_timezone.localize(datetime(2024, 7, 4, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(independence_day)
        
        assert result is True
    
    def test_is_holiday_labor_day(self, market_hours_service, et_timezone):
        """Test Labor Day holiday detection."""
        labor_day = et_timezone.localize(datetime(2024, 9, 2, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(labor_day)
        
        assert result is True
    
    def test_is_holiday_thanksgiving(self, market_hours_service, et_timezone):
        """Test Thanksgiving holiday detection."""
        thanksgiving = et_timezone.localize(datetime(2024, 11, 28, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(thanksgiving)
        
        assert result is True
    
    def test_is_holiday_christmas(self, market_hours_service, et_timezone):
        """Test Christmas Day holiday detection."""
        christmas = et_timezone.localize(datetime(2024, 12, 25, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(christmas)
        
        assert result is True
    
    def test_is_holiday_regular_day(self, market_hours_service, et_timezone):
        """Test holiday detection on a regular trading day."""
        regular_day = et_timezone.localize(datetime(2024, 1, 16, 10, 0, 0)).date()
        
        result = market_hours_service.is_holiday(regular_day)
        
        assert result is False


class TestEarlyCloseHandling:
    """Test early close day handling."""
    
    def test_is_early_close_black_friday(self, market_hours_service, et_timezone):
        """Test Black Friday early close detection."""
        black_friday = et_timezone.localize(datetime(2024, 11, 29, 10, 0, 0)).date()
        
        result = market_hours_service.is_early_close_day(black_friday)
        
        assert result is True
    
    def test_is_early_close_day_before_christmas(self, market_hours_service, et_timezone):
        """Test day before Christmas early close detection."""
        day_before_christmas = et_timezone.localize(datetime(2024, 12, 24, 10, 0, 0)).date()
        
        result = market_hours_service.is_early_close_day(day_before_christmas)
        
        assert result is True
    
    def test_is_early_close_regular_day(self, market_hours_service, et_timezone):
        """Test early close detection on a regular trading day."""
        regular_day = et_timezone.localize(datetime(2024, 1, 16, 10, 0, 0)).date()
        
        result = market_hours_service.is_early_close_day(regular_day)
        
        assert result is False
    
    def test_get_early_close_time(self, market_hours_service, et_timezone):
        """Test getting early close time."""
        black_friday = et_timezone.localize(datetime(2024, 11, 29, 10, 0, 0)).date()
        
        close_time = market_hours_service.get_early_close_time(black_friday)
        
        assert close_time.hour == 13
        assert close_time.minute == 0
        assert close_time.tzinfo == et_timezone


class TestTimezoneHandling:
    """Test timezone handling and conversions."""
    
    def test_convert_to_et_timezone(self, market_hours_service, et_timezone):
        """Test converting UTC time to Eastern Time."""
        utc_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)  # 9:30 AM ET
        
        et_time = market_hours_service._convert_to_et_timezone(utc_time)
        
        assert et_time.tzinfo == et_timezone
        assert et_time.hour == 9
        assert et_time.minute == 30
    
    def test_convert_to_utc_timezone(self, market_hours_service, et_timezone):
        """Test converting Eastern Time to UTC."""
        et_time = et_timezone.localize(datetime(2024, 1, 15, 9, 30, 0))  # 9:30 AM ET
        
        utc_time = market_hours_service._convert_to_utc_timezone(et_time)
        
        assert utc_time.tzinfo == timezone.utc
        assert utc_time.hour == 14
        assert utc_time.minute == 30
    
    def test_handle_dst_transition(self, market_hours_service, et_timezone):
        """Test handling of DST transitions."""
        # Spring forward (2nd Sunday in March)
        spring_forward = et_timezone.localize(datetime(2024, 3, 10, 9, 30, 0))
        
        # Fall back (1st Sunday in November)
        fall_back = et_timezone.localize(datetime(2024, 11, 3, 9, 30, 0))
        
        # Both should be valid market open times
        assert market_hours_service.is_market_open_at_time(spring_forward) is True
        assert market_hours_service.is_market_open_at_time(fall_back) is True


class TestTradingDayValidation:
    """Test trading day validation."""
    
    def test_is_trading_day_weekday(self, market_hours_service, et_timezone):
        """Test trading day validation on weekday."""
        weekday = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0)).date()  # Monday
        
        result = market_hours_service.is_trading_day(weekday)
        
        assert result is True
    
    def test_is_trading_day_weekend(self, market_hours_service, et_timezone):
        """Test trading day validation on weekend."""
        saturday = et_timezone.localize(datetime(2024, 1, 13, 10, 0, 0)).date()  # Saturday
        sunday = et_timezone.localize(datetime(2024, 1, 14, 10, 0, 0)).date()    # Sunday
        
        assert market_hours_service.is_trading_day(saturday) is False
        assert market_hours_service.is_trading_day(sunday) is False
    
    def test_is_trading_day_holiday(self, market_hours_service, et_timezone):
        """Test trading day validation on holiday."""
        holiday = et_timezone.localize(datetime(2024, 1, 1, 10, 0, 0)).date()  # New Year's Day
        
        result = market_hours_service.is_trading_day(holiday)
        
        assert result is False


class TestMarketHoursValidation:
    """Test market hours validation for specific times."""
    
    def test_is_market_open_at_time_during_hours(self, market_hours_service, et_timezone):
        """Test market open validation during trading hours."""
        market_time = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0))  # 10:00 AM ET
        
        result = market_hours_service.is_market_open_at_time(market_time)
        
        assert result is True
    
    def test_is_market_open_at_time_before_hours(self, market_hours_service, et_timezone):
        """Test market open validation before trading hours."""
        before_market = et_timezone.localize(datetime(2024, 1, 15, 8, 0, 0))  # 8:00 AM ET
        
        result = market_hours_service.is_market_open_at_time(before_market)
        
        assert result is False
    
    def test_is_market_open_at_time_after_hours(self, market_hours_service, et_timezone):
        """Test market open validation after trading hours."""
        after_market = et_timezone.localize(datetime(2024, 1, 15, 17, 0, 0))  # 5:00 PM ET
        
        result = market_hours_service.is_market_open_at_time(after_market)
        
        assert result is False
    
    def test_is_market_open_at_time_exact_open(self, market_hours_service, et_timezone):
        """Test market open validation at exact market open time."""
        exact_open = et_timezone.localize(datetime(2024, 1, 15, 9, 30, 0))  # 9:30 AM ET
        
        result = market_hours_service.is_market_open_at_time(exact_open)
        
        assert result is True
    
    def test_is_market_open_at_time_exact_close(self, market_hours_service, et_timezone):
        """Test market open validation at exact market close time."""
        exact_close = et_timezone.localize(datetime(2024, 1, 15, 16, 0, 0))  # 4:00 PM ET
        
        result = market_hours_service.is_market_open_at_time(exact_close)
        
        assert result is False  # Market closes at 4:00 PM, so 4:00 PM is not open


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_validate_market_hours_invalid_date(self, market_hours_service):
        """Test market hours validation with invalid date."""
        with pytest.raises(InvalidMarketHoursError, match="Invalid date"):
            market_hours_service.get_market_hours_for_date(None)
    
    def test_validate_market_hours_future_date(self, market_hours_service, et_timezone):
        """Test market hours validation with future date."""
        future_date = et_timezone.localize(datetime(2030, 1, 1, 10, 0, 0)).date()
        
        # Should handle future dates gracefully
        hours = market_hours_service.get_market_hours_for_date(future_date)
        
        assert hours is not None
        assert "open_time" in hours
        assert "close_time" in hours
    
    def test_validate_market_hours_past_date(self, market_hours_service, et_timezone):
        """Test market hours validation with past date."""
        past_date = et_timezone.localize(datetime(2020, 1, 1, 10, 0, 0)).date()
        
        # Should handle past dates gracefully
        hours = market_hours_service.get_market_hours_for_date(past_date)
        
        assert hours is not None
        assert "open_time" in hours
        assert "close_time" in hours


class TestMarketHoursUtilities:
    """Test utility methods for market hours."""
    
    def test_get_trading_days_in_range(self, market_hours_service, et_timezone):
        """Test getting trading days in a date range."""
        start_date = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0)).date()  # Monday
        end_date = et_timezone.localize(datetime(2024, 1, 19, 10, 0, 0)).date()    # Friday
        
        trading_days = market_hours_service.get_trading_days_in_range(start_date, end_date)
        
        assert len(trading_days) == 5  # Monday through Friday
        assert all(market_hours_service.is_trading_day(day) for day in trading_days)
    
    def test_get_trading_days_in_range_with_holiday(self, market_hours_service, et_timezone):
        """Test getting trading days in a range that includes a holiday."""
        start_date = et_timezone.localize(datetime(2024, 1, 1, 10, 0, 0)).date()   # New Year's Day
        end_date = et_timezone.localize(datetime(2024, 1, 5, 10, 0, 0)).date()     # Friday
        
        trading_days = market_hours_service.get_trading_days_in_range(start_date, end_date)
        
        # Should exclude New Year's Day but include other weekdays
        assert len(trading_days) == 4  # Jan 2, 3, 4, 5
        assert all(market_hours_service.is_trading_day(day) for day in trading_days)
    
    def test_get_market_hours_summary(self, market_hours_service, et_timezone):
        """Test getting market hours summary for a date."""
        test_date = et_timezone.localize(datetime(2024, 1, 15, 10, 0, 0)).date()
        
        summary = market_hours_service.get_market_hours_summary(test_date)
        
        assert "date" in summary
        assert "is_trading_day" in summary
        assert "is_holiday" in summary
        assert "is_early_close" in summary
        assert "open_time" in summary
        assert "close_time" in summary
        assert "duration_hours" in summary
        
        assert summary["is_trading_day"] is True
        assert summary["is_holiday"] is False
        assert summary["is_early_close"] is False
        assert summary["duration_hours"] == 6.5  # 9:30 AM to 4:00 PM = 6.5 hours
    
    def test_get_market_hours_summary_early_close(self, market_hours_service, et_timezone):
        """Test getting market hours summary for an early close day."""
        black_friday = et_timezone.localize(datetime(2024, 11, 29, 10, 0, 0)).date()
        
        summary = market_hours_service.get_market_hours_summary(black_friday)
        
        assert summary["is_trading_day"] is True
        assert summary["is_holiday"] is False
        assert summary["is_early_close"] is True
        assert summary["duration_hours"] == 3.5  # 9:30 AM to 1:00 PM = 3.5 hours
