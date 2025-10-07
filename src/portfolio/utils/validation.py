"""
Portfolio Validation Utilities
Comprehensive validation for portfolio data, configurations, and operations
"""
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date
from decimal import Decimal
import re
from dataclasses import dataclass

from ..models.portfolio import Portfolio
from ..models.position import Position
from ..models.asset import Asset
from ..models.optimization_result import OptimizationResult
from ..models.risk_metrics import RiskMetrics
from ..config.portfolio_config import PortfolioConfig, RiskTolerance, RebalancingFrequency

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def __post_init__(self):
        if self.errors:
            self.is_valid = False

class PortfolioValidator:
    """Comprehensive portfolio validation"""
    
    def __init__(self, config: Optional[PortfolioConfig] = None):
        self.config = config or PortfolioConfig()
    
    def validate_portfolio(self, portfolio: Portfolio) -> ValidationResult:
        """Validate portfolio data"""
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation
        basic_result = self._validate_portfolio_basic(portfolio)
        errors.extend(basic_result.errors)
        warnings.extend(basic_result.warnings)
        suggestions.extend(basic_result.suggestions)
        
        # Configuration validation
        config_result = self._validate_portfolio_config(portfolio)
        errors.extend(config_result.errors)
        warnings.extend(config_result.warnings)
        suggestions.extend(config_result.suggestions)
        
        # Position validation
        position_result = self._validate_portfolio_positions(portfolio)
        errors.extend(position_result.errors)
        warnings.extend(position_result.warnings)
        suggestions.extend(position_result.suggestions)
        
        # Risk validation
        risk_result = self._validate_portfolio_risk(portfolio)
        errors.extend(risk_result.errors)
        warnings.extend(risk_result.warnings)
        suggestions.extend(risk_result.suggestions)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_portfolio_basic(self, portfolio: Portfolio) -> ValidationResult:
        """Validate basic portfolio data"""
        errors = []
        warnings = []
        suggestions = []
        
        # Portfolio ID validation
        if not portfolio.portfolio_id:
            errors.append("Portfolio ID is required")
        elif not self._is_valid_id(portfolio.portfolio_id):
            errors.append("Portfolio ID must be alphanumeric and start with a letter")
        
        # Name validation
        if not portfolio.name:
            errors.append("Portfolio name is required")
        elif len(portfolio.name) < 3:
            errors.append("Portfolio name must be at least 3 characters")
        elif len(portfolio.name) > 255:
            errors.append("Portfolio name must be less than 255 characters")
        
        # Owner ID validation
        if not portfolio.owner_id:
            errors.append("Owner ID is required")
        elif not self._is_valid_id(portfolio.owner_id):
            errors.append("Owner ID must be alphanumeric and start with a letter")
        
        # Currency validation
        if not portfolio.base_currency:
            errors.append("Base currency is required")
        elif not self._is_valid_currency(portfolio.base_currency):
            errors.append("Base currency must be a valid 3-letter currency code")
        
        # Value validation
        if portfolio.total_value < 0:
            errors.append("Total portfolio value cannot be negative")
        elif portfolio.total_value == 0:
            warnings.append("Portfolio has zero value")
        
        if portfolio.cash_balance < 0:
            errors.append("Cash balance cannot be negative")
        
        # Date validation
        if not portfolio.creation_date:
            errors.append("Creation date is required")
        elif portfolio.creation_date > datetime.now():
            errors.append("Creation date cannot be in the future")
        
        if portfolio.last_updated and portfolio.last_updated < portfolio.creation_date:
            errors.append("Last updated date cannot be before creation date")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_portfolio_config(self, portfolio: Portfolio) -> ValidationResult:
        """Validate portfolio configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        # Risk tolerance validation
        if portfolio.risk_tolerance not in [rt.value for rt in RiskTolerance]:
            errors.append(f"Invalid risk tolerance: {portfolio.risk_tolerance}")
        
        # Rebalancing frequency validation
        if portfolio.rebalancing_frequency not in [rf.value for rf in RebalancingFrequency]:
            errors.append(f"Invalid rebalancing frequency: {portfolio.rebalancing_frequency}")
        
        # Weight constraints validation
        if portfolio.max_single_asset_weight <= 0 or portfolio.max_single_asset_weight > 1:
            errors.append("Max single asset weight must be between 0 and 1")
        elif portfolio.max_single_asset_weight > 0.5:
            warnings.append("Max single asset weight is very high (>50%)")
        
        if portfolio.max_sector_weight <= 0 or portfolio.max_sector_weight > 1:
            errors.append("Max sector weight must be between 0 and 1")
        elif portfolio.max_sector_weight > 0.8:
            warnings.append("Max sector weight is very high (>80%)")
        
        # Long-only validation
        if not isinstance(portfolio.long_only, bool):
            errors.append("Long-only flag must be a boolean")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_portfolio_positions(self, portfolio: Portfolio) -> ValidationResult:
        """Validate portfolio positions"""
        errors = []
        warnings = []
        suggestions = []
        
        if not portfolio.positions:
            warnings.append("Portfolio has no positions")
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
        
        total_position_value = 0
        asset_weights = {}
        sector_weights = {}
        
        for position in portfolio.positions:
            # Validate individual position
            position_result = self.validate_position(position)
            errors.extend(position_result.errors)
            warnings.extend(position_result.warnings)
            suggestions.extend(position_result.suggestions)
            
            # Accumulate portfolio-level metrics
            position_value = position.quantity * position.current_price
            total_position_value += position_value
            
            if position.asset:
                asset_weight = position_value / portfolio.total_value if portfolio.total_value > 0 else 0
                asset_weights[position.asset_id] = asset_weight
                
                if position.asset.sector:
                    sector = position.asset.sector
                    sector_weights[sector] = sector_weights.get(sector, 0) + asset_weight
        
        # Validate portfolio-level constraints
        if portfolio.total_value > 0:
            # Check single asset weight limits
            for asset_id, weight in asset_weights.items():
                if weight > portfolio.max_single_asset_weight:
                    errors.append(f"Asset {asset_id} exceeds max weight limit: {weight:.2%} > {portfolio.max_single_asset_weight:.2%}")
            
            # Check sector weight limits
            for sector, weight in sector_weights.items():
                if weight > portfolio.max_sector_weight:
                    errors.append(f"Sector {sector} exceeds max weight limit: {weight:.2%} > {portfolio.max_sector_weight:.2%}")
            
            # Check for concentration
            if len(asset_weights) < 5:
                warnings.append("Portfolio has fewer than 5 positions - consider diversification")
            
            # Check for cash allocation
            cash_weight = portfolio.cash_balance / portfolio.total_value
            if cash_weight < 0.05:
                warnings.append("Cash allocation is very low (<5%)")
            elif cash_weight > 0.5:
                warnings.append("Cash allocation is very high (>50%)")
        
        # Validate position values sum
        expected_total = total_position_value + portfolio.cash_balance
        if abs(expected_total - portfolio.total_value) > 0.01:  # Allow for small rounding errors
            warnings.append(f"Position values ({expected_total:.2f}) don't match total value ({portfolio.total_value:.2f})")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_portfolio_risk(self, portfolio: Portfolio) -> ValidationResult:
        """Validate portfolio risk characteristics"""
        errors = []
        warnings = []
        suggestions = []
        
        # This would typically involve risk calculations
        # For now, we'll do basic checks
        
        if portfolio.positions:
            # Check for high-risk assets
            high_risk_positions = [
                pos for pos in portfolio.positions
                if pos.asset and pos.asset.beta and pos.asset.beta > 2.0
            ]
            
            if high_risk_positions:
                warnings.append(f"Portfolio contains {len(high_risk_positions)} high-beta positions (>2.0)")
            
            # Check for concentration in volatile sectors
            tech_positions = [
                pos for pos in portfolio.positions
                if pos.asset and pos.asset.sector and 'technology' in pos.asset.sector.lower()
            ]
            
            if len(tech_positions) > len(portfolio.positions) * 0.4:
                warnings.append("Portfolio is heavily concentrated in technology sector")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_position(self, position: Position) -> ValidationResult:
        """Validate individual position"""
        errors = []
        warnings = []
        suggestions = []
        
        # Position ID validation
        if not position.position_id:
            errors.append("Position ID is required")
        elif not self._is_valid_id(position.position_id):
            errors.append("Position ID must be alphanumeric and start with a letter")
        
        # Asset ID validation
        if not position.asset_id:
            errors.append("Asset ID is required")
        elif not self._is_valid_id(position.asset_id):
            errors.append("Asset ID must be alphanumeric and start with a letter")
        
        # Quantity validation
        if position.quantity <= 0:
            errors.append("Position quantity must be positive")
        elif position.quantity < 0.0001:
            warnings.append("Position quantity is very small")
        
        # Price validation
        if position.average_cost <= 0:
            errors.append("Average cost must be positive")
        
        if position.current_price is not None and position.current_price <= 0:
            errors.append("Current price must be positive")
        
        # Date validation
        if not position.created_at:
            errors.append("Position creation date is required")
        elif position.created_at > datetime.now():
            errors.append("Position creation date cannot be in the future")
        
        if position.last_updated and position.last_updated < position.created_at:
            errors.append("Position last updated cannot be before creation date")
        
        # Market value validation
        if position.current_price is not None:
            calculated_market_value = position.quantity * position.current_price
            if abs(calculated_market_value - position.market_value) > 0.01:
                warnings.append(f"Market value mismatch: calculated {calculated_market_value:.2f} vs stored {position.market_value:.2f}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_asset(self, asset: Asset) -> ValidationResult:
        """Validate asset data"""
        errors = []
        warnings = []
        suggestions = []
        
        # Asset ID validation
        if not asset.asset_id:
            errors.append("Asset ID is required")
        elif not self._is_valid_id(asset.asset_id):
            errors.append("Asset ID must be alphanumeric and start with a letter")
        
        # Symbol validation
        if not asset.symbol:
            errors.append("Asset symbol is required")
        elif not self._is_valid_symbol(asset.symbol):
            errors.append("Asset symbol must be 1-10 alphanumeric characters")
        
        # Name validation
        if not asset.name:
            errors.append("Asset name is required")
        elif len(asset.name) < 3:
            errors.append("Asset name must be at least 3 characters")
        
        # Currency validation
        if asset.currency and not self._is_valid_currency(asset.currency):
            errors.append("Asset currency must be a valid 3-letter currency code")
        
        # Price validation
        if asset.current_price is not None and asset.current_price <= 0:
            errors.append("Current price must be positive")
        
        # Beta validation
        if asset.beta is not None and asset.beta < -5 or asset.beta > 5:
            warnings.append(f"Asset beta is extreme: {asset.beta}")
        
        # Market cap validation
        if asset.market_cap is not None and asset.market_cap <= 0:
            errors.append("Market cap must be positive")
        
        # PE ratio validation
        if asset.pe_ratio is not None and asset.pe_ratio < 0:
            warnings.append(f"Asset has negative PE ratio: {asset.pe_ratio}")
        elif asset.pe_ratio is not None and asset.pe_ratio > 100:
            warnings.append(f"Asset has very high PE ratio: {asset.pe_ratio}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_optimization_result(self, result: OptimizationResult) -> ValidationResult:
        """Validate optimization result"""
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation
        if not result.optimization_id:
            errors.append("Optimization ID is required")
        
        if not result.portfolio_id:
            errors.append("Portfolio ID is required")
        
        if not result.optimization_date:
            errors.append("Optimization date is required")
        elif result.optimization_date > datetime.now():
            errors.append("Optimization date cannot be in the future")
        
        # Weight validation
        if not result.optimal_weights:
            errors.append("Optimal weights are required")
        else:
            total_weight = sum(result.optimal_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"Weights don't sum to 1.0: {total_weight:.4f}")
            
            for asset_id, weight in result.optimal_weights.items():
                if weight < 0:
                    errors.append(f"Negative weight for asset {asset_id}: {weight}")
                elif weight > 1:
                    errors.append(f"Weight > 1 for asset {asset_id}: {weight}")
        
        # Performance validation
        if result.expected_return is not None and (result.expected_return < -1 or result.expected_return > 2):
            warnings.append(f"Extreme expected return: {result.expected_return:.2%}")
        
        if result.expected_volatility is not None and (result.expected_volatility < 0 or result.expected_volatility > 1):
            errors.append(f"Invalid expected volatility: {result.expected_volatility:.2%}")
        
        if result.sharpe_ratio is not None and result.sharpe_ratio < -5 or result.sharpe_ratio > 10:
            warnings.append(f"Extreme Sharpe ratio: {result.sharpe_ratio:.2f}")
        
        # Convergence validation
        if not result.convergence_achieved:
            warnings.append("Optimization did not achieve convergence")
        
        if result.iterations is not None and result.iterations > 10000:
            warnings.append(f"High number of iterations: {result.iterations}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_risk_metrics(self, metrics: RiskMetrics) -> ValidationResult:
        """Validate risk metrics"""
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation
        if not metrics.risk_metrics_id:
            errors.append("Risk metrics ID is required")
        
        if not metrics.portfolio_id:
            errors.append("Portfolio ID is required")
        
        if not metrics.calculation_date:
            errors.append("Calculation date is required")
        
        # VaR validation
        if metrics.var_95 is not None and metrics.var_95 > 0:
            errors.append("VaR should be negative (represents loss)")
        
        if metrics.var_99 is not None and metrics.var_99 > 0:
            errors.append("VaR 99% should be negative (represents loss)")
        
        if metrics.var_95 is not None and metrics.var_99 is not None and metrics.var_95 > metrics.var_99:
            errors.append("VaR 95% should be less negative than VaR 99%")
        
        # CVaR validation
        if metrics.cvar_95 is not None and metrics.cvar_95 > 0:
            errors.append("CVaR should be negative (represents loss)")
        
        if metrics.cvar_99 is not None and metrics.cvar_99 > 0:
            errors.append("CVaR 99% should be negative (represents loss)")
        
        # Risk contribution validation
        if metrics.risk_contributions:
            total_contribution = sum(metrics.risk_contributions.values())
            if abs(total_contribution - 1.0) > 0.01:
                warnings.append(f"Risk contributions don't sum to 1.0: {total_contribution:.4f}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _is_valid_id(self, id_str: str) -> bool:
        """Check if ID is valid"""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', id_str))
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid"""
        return bool(re.match(r'^[A-Z0-9]{1,10}$', symbol))
    
    def _is_valid_currency(self, currency: str) -> bool:
        """Check if currency code is valid"""
        return bool(re.match(r'^[A-Z]{3}$', currency))

class ConfigurationValidator:
    """Validate portfolio configuration"""
    
    def __init__(self):
        self.required_fields = [
            'default_risk_tolerance',
            'default_base_currency',
            'default_rebalancing_frequency'
        ]
    
    def validate_config(self, config: PortfolioConfig) -> ValidationResult:
        """Validate portfolio configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        # Risk tolerance validation
        if config.default_risk_tolerance not in [rt for rt in RiskTolerance]:
            errors.append(f"Invalid default risk tolerance: {config.default_risk_tolerance}")
        
        # Currency validation
        if not self._is_valid_currency(config.default_base_currency):
            errors.append(f"Invalid base currency: {config.default_base_currency}")
        
        # Rebalancing frequency validation
        if config.default_rebalancing_frequency not in [rf for rf in RebalancingFrequency]:
            errors.append(f"Invalid rebalancing frequency: {config.default_rebalancing_frequency}")
        
        # Optimization config validation
        opt_result = self._validate_optimization_config(config.optimization)
        errors.extend(opt_result.errors)
        warnings.extend(opt_result.warnings)
        suggestions.extend(opt_result.suggestions)
        
        # Risk config validation
        risk_result = self._validate_risk_config(config.risk)
        errors.extend(risk_result.errors)
        warnings.extend(risk_result.warnings)
        suggestions.extend(risk_result.suggestions)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_optimization_config(self, config) -> ValidationResult:
        """Validate optimization configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        if config.mpt_risk_free_rate < 0 or config.mpt_risk_free_rate > 1:
            errors.append("Risk-free rate must be between 0 and 1")
        
        if config.mpt_max_iterations <= 0:
            errors.append("Max iterations must be positive")
        
        if config.mpt_max_single_asset_weight <= 0 or config.mpt_max_single_asset_weight > 1:
            errors.append("Max single asset weight must be between 0 and 1")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_risk_config(self, config) -> ValidationResult:
        """Validate risk configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        if config.max_portfolio_volatility <= 0 or config.max_portfolio_volatility > 1:
            errors.append("Max portfolio volatility must be between 0 and 1")
        
        if config.max_single_asset_weight <= 0 or config.max_single_asset_weight > 1:
            errors.append("Max single asset weight must be between 0 and 1")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _is_valid_currency(self, currency: str) -> bool:
        """Check if currency code is valid"""
        return bool(re.match(r'^[A-Z]{3}$', currency))

# Global validators
_portfolio_validator: Optional[PortfolioValidator] = None
_config_validator: Optional[ConfigurationValidator] = None

def get_portfolio_validator(config: Optional[PortfolioConfig] = None) -> PortfolioValidator:
    """Get global portfolio validator"""
    global _portfolio_validator
    if _portfolio_validator is None or config is not None:
        _portfolio_validator = PortfolioValidator(config)
    return _portfolio_validator

def get_config_validator() -> ConfigurationValidator:
    """Get global configuration validator"""
    global _config_validator
    if _config_validator is None:
        _config_validator = ConfigurationValidator()
    return _config_validator

def validate_portfolio(portfolio: Portfolio, config: Optional[PortfolioConfig] = None) -> ValidationResult:
    """Validate portfolio"""
    validator = get_portfolio_validator(config)
    return validator.validate_portfolio(portfolio)

def validate_config(config: PortfolioConfig) -> ValidationResult:
    """Validate configuration"""
    validator = get_config_validator()
    return validator.validate_config(config)






















