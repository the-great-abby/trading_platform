"""
Comprehensive Risk Management Configuration
Centralized configuration for all risk management parameters
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class RiskProfile(Enum):
    """Risk profile levels"""
    ULTRA_CONSERVATIVE = "ultra_conservative"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ULTRA_AGGRESSIVE = "ultra_aggressive"


class MarketRegime(Enum):
    """Market regime types"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    CRISIS = "crisis"


@dataclass
class PositionLimits:
    """Position-level risk limits"""
    # Basic position limits
    max_position_size: float = 0.15  # 15% max per position
    min_position_size: float = 0.01  # 1% min position size
    max_position_value: float = 15000.0  # $15,000 max position value
    min_position_value: float = 50.0  # $50 min position value
    
    # Sector concentration limits
    max_sector_concentration: float = 0.30  # 30% max per sector
    max_tech_concentration: float = 0.25  # 25% max tech concentration
    max_financial_concentration: float = 0.20  # 20% max financial concentration
    
    # Correlation limits
    max_correlation: float = 0.70  # 70% max correlation between positions
    max_similar_positions: int = 3  # Max 3 similar positions (same sector/type)


@dataclass
class PortfolioLimits:
    """Portfolio-level risk limits"""
    # Leverage and cash limits
    max_portfolio_leverage: float = 1.5  # 150% max leverage
    min_cash_reserve: float = 0.10  # 10% min cash reserve
    max_cash_reserve: float = 0.50  # 50% max cash reserve
    
    # Drawdown limits
    max_drawdown: float = 0.25  # 25% max drawdown
    max_daily_drawdown: float = 0.05  # 5% max daily drawdown
    
    # Position count limits
    max_positions: int = 5  # 5 max concurrent positions
    min_positions: int = 1  # 1 min position for diversification
    max_positions_per_sector: int = 2  # 2 max positions per sector


@dataclass
class TradingLimits:
    """Trading activity limits"""
    # Daily limits
    max_daily_loss: float = 100.0  # $100 max daily loss
    max_daily_trades: int = 10  # 10 max trades per day
    max_daily_volume: float = 50000.0  # $50,000 max daily volume
    
    # Time-based limits
    min_trade_interval: int = 1  # 1 day minimum between trades
    max_trades_per_symbol: int = 3  # 3 max trades per symbol per day
    cooldown_period: int = 5  # 5-day cooldown after stop loss
    
    # Market hours
    market_hours_only: bool = True  # Only trade during market hours
    pre_market_allowed: bool = False  # No pre-market trading
    after_hours_allowed: bool = False  # No after-hours trading


@dataclass
class RiskThresholds:
    """Risk measurement thresholds"""
    # Value at Risk (VaR) limits
    var_95_limit: float = 0.02  # 2% VaR (95% confidence)
    var_99_limit: float = 0.03  # 3% VaR (99% confidence)
    expected_shortfall_limit: float = 0.025  # 2.5% expected shortfall
    
    # Volatility limits
    volatility_limit: float = 0.30  # 30% volatility limit
    max_volatility_spike: float = 0.50  # 50% max volatility spike
    
    # Beta limits
    beta_limit: float = 1.5  # 1.5 beta limit
    min_beta: float = 0.5  # 0.5 minimum beta
    
    # Sharpe ratio limits
    min_sharpe_ratio: float = 0.5  # 0.5 minimum Sharpe ratio
    target_sharpe_ratio: float = 1.0  # 1.0 target Sharpe ratio


@dataclass
class MarketConditionAdjustments:
    """Market condition-based risk adjustments"""
    # Volatility adjustments
    high_volatility_multiplier: float = 0.7  # Reduce position size by 30% in high volatility
    low_volatility_multiplier: float = 1.2  # Increase position size by 20% in low volatility
    
    # Market regime adjustments
    bull_market_multiplier: float = 1.1  # 10% increase in bull market
    bear_market_multiplier: float = 0.6  # 40% decrease in bear market
    crisis_multiplier: float = 0.3  # 70% decrease in crisis
    
    # Economic event adjustments
    earnings_season_multiplier: float = 0.8  # 20% decrease during earnings
    fomc_meeting_multiplier: float = 0.7  # 30% decrease around FOMC meetings
    options_expiry_multiplier: float = 0.9  # 10% decrease around options expiry


@dataclass
class StopLossConfig:
    """Stop loss configuration"""
    # Basic stop loss
    stop_loss_pct: float = 0.08  # 8% stop loss
    trailing_stop_pct: float = 0.05  # 5% trailing stop
    
    # Dynamic stop loss
    volatility_adjusted_stop: bool = True  # Adjust stop loss based on volatility
    atr_multiplier: float = 2.0  # 2x ATR for stop loss
    
    # Take profit
    take_profit_pct: float = 0.15  # 15% take profit
    trailing_take_profit: bool = True  # Use trailing take profit
    
    # Time-based stops
    max_holding_period: int = 30  # 30 days max holding period
    time_decay_stop: bool = True  # Tighten stops over time


@dataclass
class RiskAlertConfig:
    """Risk alert configuration"""
    # Alert thresholds
    high_risk_threshold: float = 0.7  # 70% risk score triggers high alert
    medium_risk_threshold: float = 0.5  # 50% risk score triggers medium alert
    low_risk_threshold: float = 0.3  # 30% risk score triggers low alert
    
    # Alert types
    position_limit_breach: bool = True
    daily_loss_limit_breach: bool = True
    concentration_risk_alert: bool = True
    correlation_risk_alert: bool = True
    volatility_spike_alert: bool = True
    var_breach_alert: bool = True
    
    # Notification channels
    email_alerts: bool = True
    slack_alerts: bool = True
    dashboard_alerts: bool = True
    sms_alerts: bool = False


@dataclass
class RiskConfig:
    """Comprehensive risk management configuration"""
    
    # Risk profile
    risk_profile: RiskProfile = RiskProfile.MODERATE
    
    # Market regime
    current_market_regime: MarketRegime = MarketRegime.SIDEWAYS
    
    # Risk limits
    position_limits: PositionLimits = field(default_factory=PositionLimits)
    portfolio_limits: PortfolioLimits = field(default_factory=PortfolioLimits)
    trading_limits: TradingLimits = field(default_factory=TradingLimits)
    risk_thresholds: RiskThresholds = field(default_factory=RiskThresholds)
    
    # Market adjustments
    market_adjustments: MarketConditionAdjustments = field(default_factory=MarketConditionAdjustments)
    
    # Stop loss configuration
    stop_loss_config: StopLossConfig = field(default_factory=StopLossConfig)
    
    # Alert configuration
    alert_config: RiskAlertConfig = field(default_factory=RiskAlertConfig)
    
    # Account-specific settings
    account_size: float = 1000.0  # $1,000 account size
    initial_capital: float = 1000.0  # $1,000 initial capital
    
    # Advanced features
    dynamic_position_sizing: bool = True
    volatility_adjustment: bool = True
    market_regime_adjustment: bool = True
    correlation_analysis: bool = True
    stress_testing: bool = True
    
    def __post_init__(self):
        """Apply risk profile settings after initialization"""
        self._apply_risk_profile()
    
    def _apply_risk_profile(self):
        """Apply settings based on risk profile"""
        if self.risk_profile == RiskProfile.ULTRA_CONSERVATIVE:
            self._apply_ultra_conservative_settings()
        elif self.risk_profile == RiskProfile.CONSERVATIVE:
            self._apply_conservative_settings()
        elif self.risk_profile == RiskProfile.MODERATE:
            self._apply_moderate_settings()
        elif self.risk_profile == RiskProfile.AGGRESSIVE:
            self._apply_aggressive_settings()
        elif self.risk_profile == RiskProfile.ULTRA_AGGRESSIVE:
            self._apply_ultra_aggressive_settings()
    
    def _apply_ultra_conservative_settings(self):
        """Apply ultra conservative risk settings"""
        self.position_limits.max_position_size = 0.05  # 5% max per position
        self.position_limits.max_position_value = 50.0  # $50 max position value
        self.portfolio_limits.max_positions = 3  # 3 max positions
        self.trading_limits.max_daily_loss = 25.0  # $25 max daily loss
        self.trading_limits.max_daily_trades = 3  # 3 max trades per day
        self.risk_thresholds.var_95_limit = 0.01  # 1% VaR limit
        self.stop_loss_config.stop_loss_pct = 0.03  # 3% stop loss
        self.stop_loss_config.take_profit_pct = 0.08  # 8% take profit
    
    def _apply_conservative_settings(self):
        """Apply conservative risk settings"""
        self.position_limits.max_position_size = 0.08  # 8% max per position
        self.position_limits.max_position_value = 80.0  # $80 max position value
        self.portfolio_limits.max_positions = 4  # 4 max positions
        self.trading_limits.max_daily_loss = 50.0  # $50 max daily loss
        self.trading_limits.max_daily_trades = 5  # 5 max trades per day
        self.risk_thresholds.var_95_limit = 0.015  # 1.5% VaR limit
        self.stop_loss_config.stop_loss_pct = 0.05  # 5% stop loss
        self.stop_loss_config.take_profit_pct = 0.10  # 10% take profit
    
    def _apply_moderate_settings(self):
        """Apply moderate risk settings (default)"""
        # Default settings are already moderate
        pass
    
    def _apply_aggressive_settings(self):
        """Apply aggressive risk settings"""
        self.position_limits.max_position_size = 0.25  # 25% max per position
        self.position_limits.max_position_value = 250.0  # $250 max position value
        self.portfolio_limits.max_positions = 6  # 6 max positions
        self.trading_limits.max_daily_loss = 150.0  # $150 max daily loss
        self.trading_limits.max_daily_trades = 15  # 15 max trades per day
        self.risk_thresholds.var_95_limit = 0.025  # 2.5% VaR limit
        self.stop_loss_config.stop_loss_pct = 0.12  # 12% stop loss
        self.stop_loss_config.take_profit_pct = 0.20  # 20% take profit
    
    def _apply_ultra_aggressive_settings(self):
        """Apply ultra aggressive risk settings"""
        self.position_limits.max_position_size = 0.35  # 35% max per position
        self.position_limits.max_position_value = 350.0  # $350 max position value
        self.portfolio_limits.max_positions = 8  # 8 max positions
        self.trading_limits.max_daily_loss = 200.0  # $200 max daily loss
        self.trading_limits.max_daily_trades = 20  # 20 max trades per day
        self.risk_thresholds.var_95_limit = 0.03  # 3% VaR limit
        self.stop_loss_config.stop_loss_pct = 0.15  # 15% stop loss
        self.stop_loss_config.take_profit_pct = 0.25  # 25% take profit
    
    def get_adjusted_position_size(self, base_size: float, market_conditions: Dict[str, Any] = None) -> float:
        """Get position size adjusted for market conditions"""
        adjusted_size = base_size
        
        if market_conditions:
            # Apply volatility adjustment
            if self.volatility_adjustment and 'volatility' in market_conditions:
                volatility = market_conditions['volatility']
                if volatility > 0.25:  # High volatility
                    adjusted_size *= self.market_adjustments.high_volatility_multiplier
                elif volatility < 0.10:  # Low volatility
                    adjusted_size *= self.market_adjustments.low_volatility_multiplier
            
            # Apply market regime adjustment
            if self.market_regime_adjustment and 'market_regime' in market_conditions:
                regime = market_conditions['market_regime']
                if regime == MarketRegime.BULL_MARKET:
                    adjusted_size *= self.market_adjustments.bull_market_multiplier
                elif regime == MarketRegime.BEAR_MARKET:
                    adjusted_size *= self.market_adjustments.bear_market_multiplier
                elif regime == MarketRegime.CRISIS:
                    adjusted_size *= self.market_adjustments.crisis_multiplier
            
            # Apply economic event adjustments
            if 'earnings_season' in market_conditions and market_conditions['earnings_season']:
                adjusted_size *= self.market_adjustments.earnings_season_multiplier
            
            if 'fomc_meeting' in market_conditions and market_conditions['fomc_meeting']:
                adjusted_size *= self.market_adjustments.fomc_meeting_multiplier
        
        # Ensure within limits
        adjusted_size = max(adjusted_size, self.position_limits.min_position_size)
        adjusted_size = min(adjusted_size, self.position_limits.max_position_size)
        
        return adjusted_size
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'risk_profile': self.risk_profile.value,
            'current_market_regime': self.current_market_regime.value,
            'account_size': self.account_size,
            'initial_capital': self.initial_capital,
            'position_limits': {
                'max_position_size': self.position_limits.max_position_size,
                'max_position_value': self.position_limits.max_position_value,
                'max_sector_concentration': self.position_limits.max_sector_concentration
            },
            'portfolio_limits': {
                'max_positions': self.portfolio_limits.max_positions,
                'max_drawdown': self.portfolio_limits.max_drawdown,
                'min_cash_reserve': self.portfolio_limits.min_cash_reserve
            },
            'trading_limits': {
                'max_daily_loss': self.trading_limits.max_daily_loss,
                'max_daily_trades': self.trading_limits.max_daily_trades,
                'stop_loss_pct': self.stop_loss_config.stop_loss_pct,
                'take_profit_pct': self.stop_loss_config.take_profit_pct
            },
            'risk_thresholds': {
                'var_95_limit': self.risk_thresholds.var_95_limit,
                'volatility_limit': self.risk_thresholds.volatility_limit
            }
        }


# Default risk configuration
DEFAULT_RISK_CONFIG = RiskConfig()


def get_risk_config(risk_profile: RiskProfile = RiskProfile.MODERATE, 
                   account_size: float = 1000.0) -> RiskConfig:
    """Get risk configuration for specified profile and account size"""
    config = RiskConfig(risk_profile=risk_profile, account_size=account_size, initial_capital=account_size)
    return config


def get_risk_config_by_name(profile_name: str, account_size: float = 1000.0) -> RiskConfig:
    """Get risk configuration by profile name"""
    try:
        risk_profile = RiskProfile(profile_name.lower())
        return get_risk_config(risk_profile, account_size)
    except ValueError:
        # Default to moderate if invalid profile
        return get_risk_config(RiskProfile.MODERATE, account_size) 