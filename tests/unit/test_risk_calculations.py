#!/usr/bin/env python3
"""
Unit tests for risk calculations
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

# Import risk management components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.portfolio.risk.risk_manager import RiskManager
from src.portfolio.models.portfolio import Portfolio, RiskTolerance
from src.portfolio.models.position import Position
from src.portfolio.models.asset import Asset, AssetType
from src.portfolio.models.risk_metrics import RiskMetrics, RiskType


class TestRiskManager:
    """Test Risk Manager"""
    
    def setup_method(self):
        """Set up test data"""
        self.risk_manager = RiskManager()
        
        # Create test portfolio
        self.portfolio = Portfolio(
            portfolio_id="test-portfolio-risk",
            name="Risk Test Portfolio",
            owner_id="test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD",
            total_value=100000.0
        )
        
        # Create test positions
        self.positions = [
            Position(
                position_id="pos-001",
                portfolio_id="test-portfolio-risk",
                asset_id="AAPL",
                quantity=100,
                average_cost=150.0,
                current_price=175.0
            ),
            Position(
                position_id="pos-002",
                portfolio_id="test-portfolio-risk",
                asset_id="GOOGL",
                quantity=50,
                average_cost=2500.0,
                current_price=2800.0
            ),
            Position(
                position_id="pos-003",
                portfolio_id="test-portfolio-risk",
                asset_id="TSLA",
                quantity=25,
                average_cost=200.0,
                current_price=250.0
            )
        ]
        
        self.portfolio.positions = self.positions
        
        # Create test assets with risk data
        self.assets = [
            Asset(
                asset_id="AAPL",
                symbol="AAPL",
                name="Apple Inc.",
                asset_type=AssetType.STOCK,
                current_price=175.0,
                daily_volatility=0.025,
                beta=1.2
            ),
            Asset(
                asset_id="GOOGL",
                symbol="GOOGL",
                name="Alphabet Inc.",
                asset_type=AssetType.STOCK,
                current_price=2800.0,
                daily_volatility=0.030,
                beta=1.1
            ),
            Asset(
                asset_id="TSLA",
                symbol="TSLA",
                name="Tesla Inc.",
                asset_type=AssetType.STOCK,
                current_price=250.0,
                daily_volatility=0.045,
                beta=1.8
            )
        ]
        
        # Create correlation matrix
        self.correlation_matrix = np.array([
            [1.0, 0.7, 0.6],  # AAPL correlations
            [0.7, 1.0, 0.5],  # GOOGL correlations
            [0.6, 0.5, 1.0]   # TSLA correlations
        ])
        
        # Create covariance matrix
        volatilities = np.array([0.025, 0.030, 0.045])
        self.covariance_matrix = np.outer(volatilities, volatilities) * self.correlation_matrix
    
    def test_risk_manager_creation(self):
        """Test risk manager creation"""
        assert self.risk_manager is not None
        assert hasattr(self.risk_manager, 'calculate_var')
        assert hasattr(self.risk_manager, 'calculate_cvar')
        assert hasattr(self.risk_manager, 'calculate_portfolio_volatility')
    
    def test_var_calculation(self):
        """Test Value at Risk calculation"""
        portfolio_value = 100000.0
        confidence_levels = [0.95, 0.99]
        
        for confidence in confidence_levels:
            var_result = self.risk_manager.calculate_var(
                portfolio_value=portfolio_value,
                covariance_matrix=self.covariance_matrix,
                positions=self.positions,
                confidence_level=confidence,
                time_horizon=1
            )
            
            assert var_result is not None
            assert "var_value" in var_result
            assert "var_percentage" in var_result
            assert "confidence_level" in var_result
            
            # VaR should be positive (loss amount)
            assert var_result["var_value"] > 0
            assert var_result["var_percentage"] > 0
            
            # Higher confidence should result in higher VaR
            if confidence == 0.95:
                var_95 = var_result["var_value"]
            else:
                var_99 = var_result["var_value"]
                assert var_99 > var_95
    
    def test_cvar_calculation(self):
        """Test Conditional Value at Risk calculation"""
        portfolio_value = 100000.0
        confidence_level = 0.95
        
        cvar_result = self.risk_manager.calculate_cvar(
            portfolio_value=portfolio_value,
            covariance_matrix=self.covariance_matrix,
            positions=self.positions,
            confidence_level=confidence_level,
            time_horizon=1
        )
        
        assert cvar_result is not None
        assert "cvar_value" in cvar_result
        assert "cvar_percentage" in cvar_result
        assert "confidence_level" in cvar_result
        
        # CVaR should be positive and greater than VaR
        assert cvar_result["cvar_value"] > 0
        assert cvar_result["cvar_percentage"] > 0
        
        # CVaR should be greater than VaR for the same confidence level
        var_result = self.risk_manager.calculate_var(
            portfolio_value=portfolio_value,
            covariance_matrix=self.covariance_matrix,
            positions=self.positions,
            confidence_level=confidence_level,
            time_horizon=1
        )
        
        assert cvar_result["cvar_value"] > var_result["var_value"]
    
    def test_portfolio_volatility_calculation(self):
        """Test portfolio volatility calculation"""
        volatility_result = self.risk_manager.calculate_portfolio_volatility(
            positions=self.positions,
            covariance_matrix=self.covariance_matrix
        )
        
        assert volatility_result is not None
        assert "portfolio_volatility" in volatility_result
        assert "portfolio_variance" in volatility_result
        assert "risk_contributions" in volatility_result
        
        # Volatility should be positive
        assert volatility_result["portfolio_volatility"] > 0
        assert volatility_result["portfolio_variance"] > 0
        
        # Risk contributions should sum to portfolio variance
        risk_contributions = volatility_result["risk_contributions"]
        assert abs(np.sum(risk_contributions) - volatility_result["portfolio_variance"]) < 1e-6
        
        # All risk contributions should be positive
        assert np.all(risk_contributions >= 0)
    
    def test_beta_calculation(self):
        """Test portfolio beta calculation"""
        market_return = 0.08
        risk_free_rate = 0.02
        
        beta_result = self.risk_manager.calculate_portfolio_beta(
            positions=self.positions,
            assets=self.assets,
            market_return=market_return,
            risk_free_rate=risk_free_rate
        )
        
        assert beta_result is not None
        assert "portfolio_beta" in beta_result
        assert "individual_betas" in beta_result
        assert "beta_contribution" in beta_result
        
        # Portfolio beta should be reasonable (between 0.5 and 2.0)
        assert 0.5 <= beta_result["portfolio_beta"] <= 2.0
        
        # Individual betas should match asset betas
        individual_betas = beta_result["individual_betas"]
        assert len(individual_betas) == len(self.assets)
    
    def test_stress_testing(self):
        """Test stress testing scenarios"""
        stress_scenarios = [
            {
                "name": "Market Crash",
                "shock_return": -0.20,
                "description": "20% market decline"
            },
            {
                "name": "Interest Rate Shock",
                "shock_return": 0.05,
                "description": "5% interest rate increase"
            },
            {
                "name": "Tech Bubble Burst",
                "shock_return": -0.30,
                "description": "30% tech sector decline"
            }
        ]
        
        stress_result = self.risk_manager.perform_stress_test(
            portfolio=self.portfolio,
            positions=self.positions,
            assets=self.assets,
            scenarios=stress_scenarios
        )
        
        assert stress_result is not None
        assert "scenarios" in stress_result
        assert "worst_case_scenario" in stress_result
        assert "total_portfolio_impact" in stress_result
        
        scenarios = stress_result["scenarios"]
        assert len(scenarios) == len(stress_scenarios)
        
        # Each scenario should have impact calculation
        for scenario in scenarios:
            assert "name" in scenario
            assert "portfolio_impact" in scenario
            assert "impact_percentage" in scenario
        
        # Worst case scenario should be identified
        worst_case = stress_result["worst_case_scenario"]
        assert worst_case is not None
        assert "name" in worst_case
        assert "portfolio_impact" in worst_case
    
    def test_factor_analysis(self):
        """Test factor analysis"""
        factors = {
            "market": {"AAPL": 1.2, "GOOGL": 1.1, "TSLA": 1.8},
            "size": {"AAPL": 0.8, "GOOGL": 0.9, "TSLA": 1.2},
            "value": {"AAPL": -0.5, "GOOGL": -0.3, "TSLA": -0.8}
        }
        
        factor_result = self.risk_manager.perform_factor_analysis(
            positions=self.positions,
            factors=factors
        )
        
        assert factor_result is not None
        assert "factor_exposures" in factor_result
        assert "factor_contributions" in factor_result
        assert "concentration_risk" in factor_result
        
        factor_exposures = factor_result["factor_exposures"]
        assert len(factor_exposures) == len(factors)
        
        # Each factor should have exposure calculation
        for factor_name in factors.keys():
            assert factor_name in factor_exposures
            assert "exposure" in factor_exposures[factor_name]
            assert "contribution" in factor_exposures[factor_name]
    
    def test_correlation_analysis(self):
        """Test correlation analysis"""
        correlation_result = self.risk_manager.analyze_correlations(
            positions=self.positions,
            correlation_matrix=self.correlation_matrix
        )
        
        assert correlation_result is not None
        assert "average_correlation" in correlation_result
        assert "max_correlation" in correlation_result
        assert "min_correlation" in correlation_result
        assert "correlation_clusters" in correlation_result
        
        # Average correlation should be between -1 and 1
        assert -1.0 <= correlation_result["average_correlation"] <= 1.0
        assert -1.0 <= correlation_result["max_correlation"] <= 1.0
        assert -1.0 <= correlation_result["min_correlation"] <= 1.0
        
        # Max correlation should be >= min correlation
        assert correlation_result["max_correlation"] >= correlation_result["min_correlation"]
    
    def test_risk_limits_monitoring(self):
        """Test risk limits monitoring"""
        risk_limits = {
            "max_var_95": 5000.0,  # $5,000 VaR limit
            "max_volatility": 0.20,  # 20% volatility limit
            "max_beta": 1.5,  # 1.5 beta limit
            "max_single_asset_weight": 0.30  # 30% single asset limit
        }
        
        portfolio_value = 100000.0
        
        limits_result = self.risk_manager.monitor_risk_limits(
            portfolio=self.portfolio,
            positions=self.positions,
            assets=self.assets,
            risk_limits=risk_limits,
            portfolio_value=portfolio_value,
            covariance_matrix=self.covariance_matrix
        )
        
        assert limits_result is not None
        assert "limit_violations" in limits_result
        assert "current_metrics" in limits_result
        assert "compliance_status" in limits_result
        
        current_metrics = limits_result["current_metrics"]
        assert "var_95" in current_metrics
        assert "volatility" in current_metrics
        assert "beta" in current_metrics
        assert "max_weight" in current_metrics
        
        # Check if limits are violated
        limit_violations = limits_result["limit_violations"]
        for violation in limit_violations:
            assert "limit_name" in violation
            assert "current_value" in violation
            assert "limit_value" in violation
            assert "violation_amount" in violation
    
    def test_risk_decomposition(self):
        """Test risk decomposition"""
        decomposition_result = self.risk_manager.decompose_risk(
            positions=self.positions,
            covariance_matrix=self.covariance_matrix
        )
        
        assert decomposition_result is not None
        assert "asset_contributions" in decomposition_result
        assert "sector_contributions" in decomposition_result
        assert "factor_contributions" in decomposition_result
        assert "total_risk" in decomposition_result
        
        asset_contributions = decomposition_result["asset_contributions"]
        assert len(asset_contributions) == len(self.positions)
        
        # Asset contributions should sum to total risk
        total_asset_contribution = sum(asset_contributions.values())
        assert abs(total_asset_contribution - decomposition_result["total_risk"]) < 1e-6
        
        # All contributions should be positive
        assert all(contribution >= 0 for contribution in asset_contributions.values())
    
    def test_risk_metrics_calculation(self):
        """Test comprehensive risk metrics calculation"""
        portfolio_value = 100000.0
        
        risk_metrics = self.risk_manager.calculate_comprehensive_risk_metrics(
            portfolio=self.portfolio,
            positions=self.positions,
            assets=self.assets,
            portfolio_value=portfolio_value,
            covariance_matrix=self.covariance_matrix
        )
        
        assert risk_metrics is not None
        assert isinstance(risk_metrics, RiskMetrics)
        
        # Check all required metrics are calculated
        assert risk_metrics.risk_metrics_id is not None
        assert risk_metrics.portfolio_id == self.portfolio.portfolio_id
        assert risk_metrics.risk_type == RiskType.COMPREHENSIVE
        assert risk_metrics.value is not None
        assert risk_metrics.portfolio_value == portfolio_value
        
        # Check additional metrics are included
        assert hasattr(risk_metrics, 'var_95') or 'var_95' in risk_metrics.__dict__
        assert hasattr(risk_metrics, 'cvar_95') or 'cvar_95' in risk_metrics.__dict__
        assert hasattr(risk_metrics, 'portfolio_volatility') or 'portfolio_volatility' in risk_metrics.__dict__
        assert hasattr(risk_metrics, 'portfolio_beta') or 'portfolio_beta' in risk_metrics.__dict__
    
    def test_risk_metrics_validation(self):
        """Test risk metrics validation"""
        # Valid risk metrics
        valid_metrics = RiskMetrics(
            risk_metrics_id="test-risk-001",
            portfolio_id="test-portfolio-risk",
            risk_type=RiskType.VAR,
            confidence_level=0.95,
            time_horizon=1,
            value=5000.0,
            portfolio_value=100000.0
        )
        
        assert valid_metrics.is_valid()
        
        # Invalid risk metrics - negative value
        with pytest.raises(ValueError):
            RiskMetrics(
                risk_metrics_id="test-risk-002",
                portfolio_id="test-portfolio-risk",
                risk_type=RiskType.VAR,
                confidence_level=0.95,
                time_horizon=1,
                value=-1000.0,  # Invalid negative value
                portfolio_value=100000.0
            )
    
    def test_risk_calculations_with_missing_data(self):
        """Test risk calculations with missing data"""
        # Test with incomplete asset data
        incomplete_assets = [
            Asset(
                asset_id="AAPL",
                symbol="AAPL",
                name="Apple Inc.",
                asset_type=AssetType.STOCK,
                current_price=175.0,
                daily_volatility=0.025,
                beta=None  # Missing beta
            )
        ]
        
        # Should handle missing data gracefully
        try:
            beta_result = self.risk_manager.calculate_portfolio_beta(
                positions=self.positions[:1],  # Only AAPL position
                assets=incomplete_assets,
                market_return=0.08,
                risk_free_rate=0.02
            )
            # If no exception, should have default beta handling
            assert beta_result is not None
        except Exception as e:
            # Should raise informative error
            assert "beta" in str(e).lower() or "missing" in str(e).lower()
    
    def test_risk_calculations_edge_cases(self):
        """Test risk calculations with edge cases"""
        # Test with zero portfolio value
        zero_value_result = self.risk_manager.calculate_var(
            portfolio_value=0.0,
            covariance_matrix=self.covariance_matrix,
            positions=self.positions,
            confidence_level=0.95,
            time_horizon=1
        )
        
        assert zero_value_result is not None
        assert zero_value_result["var_value"] == 0.0
        assert zero_value_result["var_percentage"] == 0.0
        
        # Test with single position
        single_position = [self.positions[0]]  # Only AAPL
        single_pos_result = self.risk_manager.calculate_portfolio_volatility(
            positions=single_position,
            covariance_matrix=self.covariance_matrix[:1, :1]  # Single asset covariance
        )
        
        assert single_pos_result is not None
        assert "portfolio_volatility" in single_pos_result
        assert single_pos_result["portfolio_volatility"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])












