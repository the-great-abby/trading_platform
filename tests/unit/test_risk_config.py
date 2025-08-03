"""
Comprehensive tests for Risk Configuration System
Tests all risk profiles, data classes, configuration methods, and utility functions
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.utils.risk_config import (
    RiskProfile,
    MarketRegime,
    PositionLimits,
    PortfolioLimits,
    TradingLimits,
    RiskThresholds,
    MarketConditionAdjustments,
    StopLossConfig,
    RiskAlertConfig,
    RiskConfig,
    get_risk_config,
    get_risk_config_by_name,
    DEFAULT_RISK_CONFIG
)


class TestRiskProfile:
    """Test risk profile enumeration"""
    
    def test_risk_profile_values(self):
        """Test all risk profile values"""
        assert RiskProfile.ULTRA_CONSERVATIVE.value == "ultra_conservative"
        assert RiskProfile.CONSERVATIVE.value == "conservative"
        assert RiskProfile.MODERATE.value == "moderate"
        assert RiskProfile.AGGRESSIVE.value == "aggressive"
        assert RiskProfile.ULTRA_AGGRESSIVE.value == "ultra_aggressive"
    
    def test_risk_profile_ordering(self):
        """Test risk profile ordering (conservative to aggressive)"""
        profiles = list(RiskProfile)
        assert profiles[0] == RiskProfile.ULTRA_CONSERVATIVE
        assert profiles[-1] == RiskProfile.ULTRA_AGGRESSIVE


class TestMarketRegime:
    """Test market regime enumeration"""
    
    def test_market_regime_values(self):
        """Test all market regime values"""
        assert MarketRegime.BULL_MARKET.value == "bull_market"
        assert MarketRegime.BEAR_MARKET.value == "bear_market"
        assert MarketRegime.SIDEWAYS.value == "sideways"
        assert MarketRegime.CRISIS.value == "crisis"
        assert MarketRegime.VOLATILE.value == "volatile"


class TestPositionLimits:
    """Test position limits data class"""
    
    def test_position_limits_defaults(self):
        """Test position limits default values"""
        limits = PositionLimits()
        
        assert limits.max_position_size == 0.15
        assert limits.min_position_size == 0.01
        assert limits.max_position_value == 15000.0
        assert limits.min_position_value == 50.0
        assert limits.max_sector_concentration == 0.30
        assert limits.max_tech_concentration == 0.25
        assert limits.max_financial_concentration == 0.20
        assert limits.max_correlation == 0.70
        assert limits.max_similar_positions == 3
    
    def test_position_limits_custom_values(self):
        """Test position limits with custom values"""
        limits = PositionLimits(
            max_position_size=0.20,
            min_position_size=0.02,
            max_position_value=20000.0,
            min_position_value=100.0
        )
        
        assert limits.max_position_size == 0.20
        assert limits.min_position_size == 0.02
        assert limits.max_position_value == 20000.0
        assert limits.min_position_value == 100.0


class TestPortfolioLimits:
    """Test portfolio limits data class"""
    
    def test_portfolio_limits_defaults(self):
        """Test portfolio limits default values"""
        limits = PortfolioLimits()
        
        assert limits.max_positions == 5
        assert limits.max_portfolio_leverage == 1.5
        assert limits.min_cash_reserve == 0.10
        assert limits.max_drawdown == 0.25
        # Note: max_sector_concentration is not in PortfolioLimits, it's in PositionLimits
        assert limits.max_daily_drawdown == 0.05
        assert limits.min_positions == 1
        assert limits.max_positions_per_sector == 2
    
    def test_portfolio_limits_custom_values(self):
        """Test portfolio limits with custom values"""
        limits = PortfolioLimits(
            max_positions=10,
            max_portfolio_leverage=2.0,
            min_cash_reserve=0.20
        )
        
        assert limits.max_positions == 10
        assert limits.max_portfolio_leverage == 2.0
        assert limits.min_cash_reserve == 0.20


class TestTradingLimits:
    """Test trading limits data class"""
    
    def test_trading_limits_defaults(self):
        """Test trading limits default values"""
        limits = TradingLimits()
        
        assert limits.max_daily_loss == 100.0
        assert limits.max_daily_trades == 10
        assert limits.max_trades_per_symbol == 3
        assert limits.min_trade_interval == 1  # Actual value is 1, not 300
        assert limits.max_daily_volume == 50000.0
        assert limits.cooldown_period == 5
        assert limits.market_hours_only is True
        assert limits.pre_market_allowed is False
        assert limits.after_hours_allowed is False
    
    def test_trading_limits_custom_values(self):
        """Test trading limits with custom values"""
        limits = TradingLimits(
            max_daily_loss=200.0,
            max_daily_trades=20,
            max_trades_per_symbol=5
        )
        
        assert limits.max_daily_loss == 200.0
        assert limits.max_daily_trades == 20
        assert limits.max_trades_per_symbol == 5


class TestRiskThresholds:
    """Test risk thresholds data class"""
    
    def test_risk_thresholds_defaults(self):
        """Test risk thresholds default values"""
        thresholds = RiskThresholds()
        
        assert thresholds.var_95_limit == 0.02
        assert thresholds.var_99_limit == 0.03
        assert thresholds.volatility_limit == 0.30
        assert thresholds.beta_limit == 1.5
        assert thresholds.min_sharpe_ratio == 0.5  # Actual attribute name
        assert thresholds.target_sharpe_ratio == 1.0
        assert thresholds.expected_shortfall_limit == 0.025
        assert thresholds.max_volatility_spike == 0.50
        assert thresholds.min_beta == 0.5
    
    def test_risk_thresholds_custom_values(self):
        """Test risk thresholds with custom values"""
        thresholds = RiskThresholds(
            var_95_limit=0.015,
            volatility_limit=0.25,
            beta_limit=1.2
        )
        
        assert thresholds.var_95_limit == 0.015
        assert thresholds.volatility_limit == 0.25
        assert thresholds.beta_limit == 1.2


class TestMarketConditionAdjustments:
    """Test market condition adjustments data class"""
    
    def test_market_adjustments_defaults(self):
        """Test market adjustments default values"""
        adjustments = MarketConditionAdjustments()
        
        assert adjustments.high_volatility_multiplier == 0.7
        assert adjustments.low_volatility_multiplier == 1.2
        assert adjustments.bull_market_multiplier == 1.1
        assert adjustments.bear_market_multiplier == 0.6  # Actual value is 0.6, not 0.8
        assert adjustments.crisis_multiplier == 0.3
        assert adjustments.earnings_season_multiplier == 0.8
        assert adjustments.fomc_meeting_multiplier == 0.7
        assert adjustments.options_expiry_multiplier == 0.9
    
    def test_market_adjustments_custom_values(self):
        """Test market adjustments with custom values"""
        adjustments = MarketConditionAdjustments(
            high_volatility_multiplier=0.6,
            bull_market_multiplier=1.2
        )
        
        assert adjustments.high_volatility_multiplier == 0.6
        assert adjustments.bull_market_multiplier == 1.2


class TestStopLossConfig:
    """Test stop loss configuration data class"""
    
    def test_stop_loss_config_defaults(self):
        """Test stop loss config default values"""
        config = StopLossConfig()
        
        assert config.stop_loss_pct == 0.08
        assert config.take_profit_pct == 0.15
        assert config.trailing_stop_pct == 0.05
        assert config.volatility_adjusted_stop is True
        assert config.atr_multiplier == 2.0
        assert config.trailing_take_profit is True
        assert config.max_holding_period == 30
        assert config.time_decay_stop is True
    
    def test_stop_loss_config_custom_values(self):
        """Test stop loss config with custom values"""
        config = StopLossConfig(
            stop_loss_pct=0.10,
            take_profit_pct=0.20,
            trailing_stop_pct=0.06
        )
        
        assert config.stop_loss_pct == 0.10
        assert config.take_profit_pct == 0.20
        assert config.trailing_stop_pct == 0.06


class TestRiskAlertConfig:
    """Test risk alert configuration data class"""
    
    def test_risk_alert_config_defaults(self):
        """Test risk alert config default values"""
        config = RiskAlertConfig()
        
        assert config.high_risk_threshold == 0.7
        assert config.medium_risk_threshold == 0.5
        assert config.low_risk_threshold == 0.3
        assert config.position_limit_breach is True
        assert config.daily_loss_limit_breach is True
        assert config.concentration_risk_alert is True
        assert config.correlation_risk_alert is True
        assert config.volatility_spike_alert is True
        assert config.var_breach_alert is True
        assert config.email_alerts is True
        assert config.slack_alerts is True
        assert config.dashboard_alerts is True
        assert config.sms_alerts is False
    
    def test_risk_alert_config_custom_values(self):
        """Test risk alert config with custom values"""
        config = RiskAlertConfig(
            high_risk_threshold=0.8,
            email_alerts=False,
            sms_alerts=True
        )
        
        assert config.high_risk_threshold == 0.8
        assert config.email_alerts is False
        assert config.sms_alerts is True


class TestRiskConfig:
    """Test comprehensive risk configuration"""
    
    def test_risk_config_defaults(self):
        """Test risk config default values"""
        config = RiskConfig()
        
        assert config.risk_profile == RiskProfile.MODERATE
        assert config.current_market_regime == MarketRegime.SIDEWAYS
        assert config.account_size == 1000.0
        assert config.initial_capital == 1000.0
        assert config.dynamic_position_sizing is True
        assert config.volatility_adjustment is True
        assert config.market_regime_adjustment is True
        assert config.correlation_analysis is True
        assert config.stress_testing is True
        
        # Check nested objects
        assert isinstance(config.position_limits, PositionLimits)
        assert isinstance(config.portfolio_limits, PortfolioLimits)
        assert isinstance(config.trading_limits, TradingLimits)
        assert isinstance(config.risk_thresholds, RiskThresholds)
        assert isinstance(config.market_adjustments, MarketConditionAdjustments)
        assert isinstance(config.stop_loss_config, StopLossConfig)
        assert isinstance(config.alert_config, RiskAlertConfig)
    
    def test_risk_config_custom_values(self):
        """Test risk config with custom values"""
        config = RiskConfig(
            risk_profile=RiskProfile.AGGRESSIVE,
            account_size=5000.0,
            initial_capital=5000.0
        )
        
        assert config.risk_profile == RiskProfile.AGGRESSIVE
        assert config.account_size == 5000.0
        assert config.initial_capital == 5000.0
    
    def test_ultra_conservative_settings(self):
        """Test ultra conservative risk settings"""
        config = RiskConfig(risk_profile=RiskProfile.ULTRA_CONSERVATIVE)
        
        assert config.position_limits.max_position_size == 0.05
        assert config.position_limits.max_position_value == 50.0
        assert config.portfolio_limits.max_positions == 3
        assert config.trading_limits.max_daily_loss == 25.0
        assert config.trading_limits.max_daily_trades == 3
        assert config.risk_thresholds.var_95_limit == 0.01
        assert config.stop_loss_config.stop_loss_pct == 0.03
        assert config.stop_loss_config.take_profit_pct == 0.08
    
    def test_conservative_settings(self):
        """Test conservative risk settings"""
        config = RiskConfig(risk_profile=RiskProfile.CONSERVATIVE)
        
        assert config.position_limits.max_position_size == 0.08
        assert config.position_limits.max_position_value == 80.0
        assert config.portfolio_limits.max_positions == 4
        assert config.trading_limits.max_daily_loss == 50.0
        assert config.trading_limits.max_daily_trades == 5
        assert config.risk_thresholds.var_95_limit == 0.015
        assert config.stop_loss_config.stop_loss_pct == 0.05
        assert config.stop_loss_config.take_profit_pct == 0.10
    
    def test_moderate_settings(self):
        """Test moderate risk settings (default)"""
        config = RiskConfig(risk_profile=RiskProfile.MODERATE)
        
        # Should use default values
        assert config.position_limits.max_position_size == 0.15
        assert config.position_limits.max_position_value == 15000.0
        assert config.portfolio_limits.max_positions == 5
        assert config.trading_limits.max_daily_loss == 100.0
        assert config.trading_limits.max_daily_trades == 10
    
    def test_aggressive_settings(self):
        """Test aggressive risk settings"""
        config = RiskConfig(risk_profile=RiskProfile.AGGRESSIVE)
        
        assert config.position_limits.max_position_size == 0.25
        assert config.position_limits.max_position_value == 250.0
        assert config.portfolio_limits.max_positions == 6
        assert config.trading_limits.max_daily_loss == 150.0
        assert config.trading_limits.max_daily_trades == 15
        assert config.risk_thresholds.var_95_limit == 0.025
        assert config.stop_loss_config.stop_loss_pct == 0.12
        assert config.stop_loss_config.take_profit_pct == 0.20
    
    def test_ultra_aggressive_settings(self):
        """Test ultra aggressive risk settings"""
        config = RiskConfig(risk_profile=RiskProfile.ULTRA_AGGRESSIVE)
        
        assert config.position_limits.max_position_size == 0.35
        assert config.position_limits.max_position_value == 350.0
        assert config.portfolio_limits.max_positions == 8
        assert config.trading_limits.max_daily_loss == 200.0
        assert config.trading_limits.max_daily_trades == 20
        assert config.risk_thresholds.var_95_limit == 0.03
        assert config.stop_loss_config.stop_loss_pct == 0.15
        assert config.stop_loss_config.take_profit_pct == 0.25
    
    def test_get_adjusted_position_size_no_conditions(self):
        """Test position size adjustment with no market conditions"""
        config = RiskConfig()
        base_size = 0.10
        
        adjusted_size = config.get_adjusted_position_size(base_size)
        
        assert adjusted_size == 0.10  # No adjustment
    
    def test_get_adjusted_position_size_with_volatility(self):
        """Test position size adjustment with volatility"""
        config = RiskConfig()
        base_size = 0.10
        market_conditions = {"volatility": 0.30}  # High volatility
        
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be reduced by high volatility multiplier
        expected_size = base_size * config.market_adjustments.high_volatility_multiplier
        assert adjusted_size == expected_size
    
    def test_get_adjusted_position_size_with_market_regime(self):
        """Test position size adjustment with market regime"""
        config = RiskConfig()
        base_size = 0.10
        market_conditions = {"market_regime": MarketRegime.BULL_MARKET}
        
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be increased by bull market multiplier
        expected_size = base_size * config.market_adjustments.bull_market_multiplier
        assert adjusted_size == expected_size
    
    def test_get_adjusted_position_size_with_earnings_season(self):
        """Test position size adjustment with earnings season"""
        config = RiskConfig()
        base_size = 0.10
        market_conditions = {"earnings_season": True}
        
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be reduced by earnings season multiplier
        expected_size = base_size * config.market_adjustments.earnings_season_multiplier
        assert adjusted_size == expected_size
    
    def test_get_adjusted_position_size_with_fomc_meeting(self):
        """Test position size adjustment with FOMC meeting"""
        config = RiskConfig()
        base_size = 0.10
        market_conditions = {"fomc_meeting": True}
        
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be reduced by FOMC meeting multiplier
        expected_size = base_size * config.market_adjustments.fomc_meeting_multiplier
        assert adjusted_size == expected_size
    
    def test_get_adjusted_position_size_within_limits(self):
        """Test position size adjustment respects limits"""
        config = RiskConfig()
        base_size = 0.50  # Too large
        market_conditions = {"volatility": 0.10}  # Low volatility (increases size)
        
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be capped at max position size
        assert adjusted_size == config.position_limits.max_position_size
    
    def test_get_adjusted_position_size_minimum_limit(self):
        """Test position size adjustment respects minimum limit"""
        config = RiskConfig()
        base_size = 0.005  # Too small
        market_conditions = {"volatility": 0.30}  # High volatility (decreases size)
        
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be raised to minimum position size
        assert adjusted_size == config.position_limits.min_position_size


class TestRiskConfigFunctions:
    """Test risk configuration utility functions"""
    
    def test_get_risk_config_default(self):
        """Test get_risk_config with default parameters"""
        config = get_risk_config()
        
        assert config.risk_profile == RiskProfile.MODERATE
        assert config.account_size == 1000.0
        assert config.initial_capital == 1000.0
    
    def test_get_risk_config_custom_profile(self):
        """Test get_risk_config with custom risk profile"""
        config = get_risk_config(RiskProfile.AGGRESSIVE, 5000.0)
        
        assert config.risk_profile == RiskProfile.AGGRESSIVE
        assert config.account_size == 5000.0
        assert config.initial_capital == 5000.0
    
    def test_get_risk_config_by_name_valid(self):
        """Test get_risk_config_by_name with valid profile name"""
        config = get_risk_config_by_name("conservative", 2000.0)
        
        assert config.risk_profile == RiskProfile.CONSERVATIVE
        assert config.account_size == 2000.0
        assert config.initial_capital == 2000.0
    
    def test_get_risk_config_by_name_invalid(self):
        """Test get_risk_config_by_name with invalid profile name"""
        config = get_risk_config_by_name("invalid_profile", 1000.0)
        
        # Should default to moderate
        assert config.risk_profile == RiskProfile.MODERATE
        assert config.account_size == 1000.0
    
    def test_get_risk_config_by_name_case_insensitive(self):
        """Test get_risk_config_by_name is case insensitive"""
        config = get_risk_config_by_name("AGGRESSIVE", 1000.0)
        
        assert config.risk_profile == RiskProfile.AGGRESSIVE


class TestRiskConfigIntegration:
    """Integration tests for risk configuration"""
    
    def test_complete_risk_config_workflow(self):
        """Test complete risk configuration workflow"""
        # Create aggressive config
        config = get_risk_config(RiskProfile.AGGRESSIVE, 10000.0)
        
        # Verify aggressive settings
        assert config.position_limits.max_position_size == 0.25
        assert config.trading_limits.max_daily_loss == 150.0
        
        # Test position size adjustment
        base_size = 0.20
        market_conditions = {
            "volatility": 0.25,
            "market_regime": MarketRegime.BULL_MARKET,
            "earnings_season": True
        }
        
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be within limits
        assert adjusted_size >= config.position_limits.min_position_size
        assert adjusted_size <= config.position_limits.max_position_size
    
    def test_risk_config_serialization(self):
        """Test risk config can be serialized (for storage/transmission)"""
        config = get_risk_config(RiskProfile.MODERATE, 5000.0)
        
        # Test that we can access all attributes without errors
        assert config.risk_profile.value is not None
        assert config.account_size > 0
        assert config.position_limits.max_position_size > 0
        assert config.portfolio_limits.max_positions > 0
        assert config.trading_limits.max_daily_loss > 0
        assert config.risk_thresholds.var_95_limit > 0
        assert config.market_adjustments.high_volatility_multiplier > 0
        assert config.stop_loss_config.stop_loss_pct > 0
        assert config.alert_config.high_risk_threshold > 0


class TestRiskConfigEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_risk_config_with_zero_account_size(self):
        """Test risk config with zero account size"""
        config = get_risk_config(RiskProfile.MODERATE, 0.0)
        
        assert config.account_size == 0.0
        assert config.initial_capital == 0.0
    
    def test_risk_config_with_negative_account_size(self):
        """Test risk config with negative account size"""
        config = get_risk_config(RiskProfile.MODERATE, -1000.0)
        
        assert config.account_size == -1000.0
        assert config.initial_capital == -1000.0
    
    def test_position_size_adjustment_with_extreme_conditions(self):
        """Test position size adjustment with extreme market conditions"""
        config = RiskConfig()
        base_size = 0.10
        
        # Test with very high volatility
        market_conditions = {"volatility": 0.50}
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be reduced but still within limits
        assert adjusted_size >= config.position_limits.min_position_size
        assert adjusted_size <= config.position_limits.max_position_size
        
        # Test with very low volatility
        market_conditions = {"volatility": 0.05}
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be increased but still within limits
        assert adjusted_size >= config.position_limits.min_position_size
        assert adjusted_size <= config.position_limits.max_position_size
    
    def test_multiple_market_conditions(self):
        """Test position size adjustment with multiple market conditions"""
        config = RiskConfig()
        base_size = 0.10
        market_conditions = {
            "volatility": 0.30,
            "market_regime": MarketRegime.BEAR_MARKET,
            "earnings_season": True,
            "fomc_meeting": True
        }
        
        adjusted_size = config.get_adjusted_position_size(base_size, market_conditions)
        
        # Should be within limits despite multiple adjustments
        assert adjusted_size >= config.position_limits.min_position_size
        assert adjusted_size <= config.position_limits.max_position_size 