#!/usr/bin/env python3
"""
Unit tests for portfolio models
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any

# Import portfolio models
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.portfolio.models.portfolio import Portfolio, PortfolioStatus, RiskTolerance
from src.portfolio.models.position import Position, PositionStatus, TaxLot
from src.portfolio.models.asset import Asset, AssetType, AssetStatus
from src.portfolio.models.optimization_result import OptimizationResult, OptimizationType
from src.portfolio.models.market_view import MarketView, ViewType
from src.portfolio.models.rebalancing_recommendation import RebalancingRecommendation, RebalancingStatus
from src.portfolio.models.risk_metrics import RiskMetrics, RiskType


class TestPortfolioModel:
    """Test Portfolio model"""
    
    def test_portfolio_creation(self):
        """Test basic portfolio creation"""
        portfolio = Portfolio(
            portfolio_id="test-portfolio-001",
            name="Test Portfolio",
            owner_id="test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD"
        )
        
        assert portfolio.portfolio_id == "test-portfolio-001"
        assert portfolio.name == "Test Portfolio"
        assert portfolio.owner_id == "test-user"
        assert portfolio.risk_tolerance == RiskTolerance.MODERATE
        assert portfolio.base_currency == "USD"
        assert portfolio.status == PortfolioStatus.ACTIVE
        assert portfolio.created_at is not None
        assert portfolio.updated_at is not None
    
    def test_portfolio_validation(self):
        """Test portfolio validation"""
        # Valid portfolio
        portfolio = Portfolio(
            portfolio_id="test-portfolio-002",
            name="Valid Portfolio",
            owner_id="test-user",
            risk_tolerance=RiskTolerance.CONSERVATIVE,
            base_currency="USD",
            max_single_asset_weight=0.20,
            max_sector_weight=0.40
        )
        
        assert portfolio.is_valid()
        assert portfolio.validate_constraints() == []
        
        # Invalid portfolio - negative weights
        with pytest.raises(ValueError):
            Portfolio(
                portfolio_id="test-portfolio-003",
                name="Invalid Portfolio",
                owner_id="test-user",
                risk_tolerance=RiskTolerance.AGGRESSIVE,
                base_currency="USD",
                max_single_asset_weight=-0.10  # Invalid negative weight
            )
    
    def test_portfolio_performance_calculation(self):
        """Test portfolio performance calculations"""
        portfolio = Portfolio(
            portfolio_id="test-portfolio-004",
            name="Performance Test Portfolio",
            owner_id="test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD",
            total_value=100000.0
        )
        
        # Add positions
        positions = [
            Position(
                position_id="pos-001",
                portfolio_id="test-portfolio-004",
                asset_id="AAPL",
                quantity=100,
                average_cost=150.0,
                current_price=175.0
            ),
            Position(
                position_id="pos-002",
                portfolio_id="test-portfolio-004",
                asset_id="GOOGL",
                quantity=50,
                average_cost=2500.0,
                current_price=2800.0
            )
        ]
        
        portfolio.positions = positions
        
        # Test performance calculations
        total_return = portfolio.calculate_total_return()
        expected_return = ((175.0 - 150.0) * 100 + (2800.0 - 2500.0) * 50) / (150.0 * 100 + 2500.0 * 50)
        assert abs(total_return - expected_return) < 1e-6
        
        # Test current value calculation
        current_value = portfolio.calculate_current_value()
        expected_value = 175.0 * 100 + 2800.0 * 50
        assert abs(current_value - expected_value) < 1e-6
    
    def test_portfolio_constraints(self):
        """Test portfolio constraint validation"""
        portfolio = Portfolio(
            portfolio_id="test-portfolio-005",
            name="Constraint Test Portfolio",
            owner_id="test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD",
            max_single_asset_weight=0.20,
            max_sector_weight=0.40,
            long_only=True
        )
        
        # Add positions that violate constraints
        positions = [
            Position(
                position_id="pos-001",
                portfolio_id="test-portfolio-005",
                asset_id="AAPL",
                quantity=1000,  # This will be >20% of portfolio
                average_cost=150.0,
                current_price=175.0
            )
        ]
        
        portfolio.positions = positions
        portfolio.total_value = 500000.0  # Set total value
        
        violations = portfolio.validate_constraints()
        assert len(violations) > 0
        assert any("single asset weight" in violation.lower() for violation in violations)


class TestPositionModel:
    """Test Position model"""
    
    def test_position_creation(self):
        """Test basic position creation"""
        position = Position(
            position_id="test-position-001",
            portfolio_id="test-portfolio-001",
            asset_id="AAPL",
            quantity=100,
            average_cost=150.0,
            current_price=175.0
        )
        
        assert position.position_id == "test-position-001"
        assert position.portfolio_id == "test-portfolio-001"
        assert position.asset_id == "AAPL"
        assert position.quantity == 100
        assert position.average_cost == 150.0
        assert position.current_price == 175.0
        assert position.status == PositionStatus.ACTIVE
    
    def test_position_pnl_calculation(self):
        """Test position P&L calculations"""
        position = Position(
            position_id="test-position-002",
            portfolio_id="test-portfolio-002",
            asset_id="GOOGL",
            quantity=50,
            average_cost=2500.0,
            current_price=2800.0
        )
        
        # Test unrealized P&L
        unrealized_pnl = position.calculate_unrealized_pnl()
        expected_pnl = (2800.0 - 2500.0) * 50
        assert abs(unrealized_pnl - expected_pnl) < 1e-6
        
        # Test unrealized P&L percentage
        unrealized_pnl_pct = position.calculate_unrealized_pnl_percentage()
        expected_pct = (2800.0 - 2500.0) / 2500.0
        assert abs(unrealized_pnl_pct - expected_pct) < 1e-6
        
        # Test current value
        current_value = position.calculate_current_value()
        expected_value = 2800.0 * 50
        assert abs(current_value - expected_value) < 1e-6
    
    def test_tax_lot_management(self):
        """Test tax lot management"""
        position = Position(
            position_id="test-position-003",
            portfolio_id="test-portfolio-003",
            asset_id="MSFT",
            quantity=200,
            average_cost=300.0,
            current_price=350.0
        )
        
        # Add tax lots
        tax_lots = [
            TaxLot(
                lot_id="lot-001",
                position_id="test-position-003",
                quantity=100,
                cost_basis=280.0,
                acquisition_date=date(2023, 1, 15)
            ),
            TaxLot(
                lot_id="lot-002",
                position_id="test-position-003",
                quantity=100,
                cost_basis=320.0,
                acquisition_date=date(2023, 6, 20)
            )
        ]
        
        position.tax_lots = tax_lots
        
        # Test tax lot calculations
        total_cost_basis = position.calculate_total_cost_basis()
        expected_cost_basis = 100 * 280.0 + 100 * 320.0
        assert abs(total_cost_basis - expected_cost_basis) < 1e-6
        
        # Test tax loss harvesting candidates
        candidates = position.get_tax_loss_harvesting_candidates(current_price=250.0)
        assert len(candidates) == 2  # Both lots are at a loss
        
        # Test wash sale detection
        wash_sales = position.detect_wash_sales(
            sale_date=date(2023, 7, 15),
            sale_price=250.0
        )
        assert len(wash_sales) == 1  # One lot is within 30 days


class TestAssetModel:
    """Test Asset model"""
    
    def test_asset_creation(self):
        """Test basic asset creation"""
        asset = Asset(
            asset_id="test-asset-001",
            symbol="TEST",
            name="Test Asset",
            asset_type=AssetType.STOCK,
            exchange="NASDAQ",
            currency="USD"
        )
        
        assert asset.asset_id == "test-asset-001"
        assert asset.symbol == "TEST"
        assert asset.name == "Test Asset"
        assert asset.asset_type == AssetType.STOCK
        assert asset.exchange == "NASDAQ"
        assert asset.currency == "USD"
        assert asset.status == AssetStatus.ACTIVE
    
    def test_asset_risk_calculation(self):
        """Test asset risk calculations"""
        asset = Asset(
            asset_id="test-asset-002",
            symbol="RISKY",
            name="Risky Asset",
            asset_type=AssetType.STOCK,
            exchange="NYSE",
            currency="USD",
            current_price=100.0,
            daily_volatility=0.02,
            beta=1.5
        )
        
        # Test VaR calculation
        var_95 = asset.calculate_var(confidence_level=0.95, time_horizon=1)
        expected_var = 100.0 * 1.645 * 0.02  # 95% VaR approximation
        assert abs(var_95 - expected_var) < 1e-6
        
        # Test expected return calculation
        expected_return = asset.calculate_expected_return(risk_free_rate=0.02, market_return=0.08)
        expected_capm_return = 0.02 + 1.5 * (0.08 - 0.02)
        assert abs(expected_return - expected_capm_return) < 1e-6


class TestOptimizationResultModel:
    """Test OptimizationResult model"""
    
    def test_optimization_result_creation(self):
        """Test basic optimization result creation"""
        result = OptimizationResult(
            optimization_id="test-opt-001",
            portfolio_id="test-portfolio-001",
            optimization_type=OptimizationType.MPT,
            expected_return=0.12,
            expected_volatility=0.18,
            sharpe_ratio=0.67
        )
        
        assert result.optimization_id == "test-opt-001"
        assert result.portfolio_id == "test-portfolio-001"
        assert result.optimization_type == OptimizationType.MPT
        assert result.expected_return == 0.12
        assert result.expected_volatility == 0.18
        assert result.sharpe_ratio == 0.67
    
    def test_optimization_result_validation(self):
        """Test optimization result validation"""
        # Valid result
        result = OptimizationResult(
            optimization_id="test-opt-002",
            portfolio_id="test-portfolio-002",
            optimization_type=OptimizationType.BLACK_LITTERMAN,
            expected_return=0.15,
            expected_volatility=0.20,
            sharpe_ratio=0.75,
            convergence_achieved=True,
            iterations=150
        )
        
        assert result.is_valid()
        
        # Invalid result - negative volatility
        with pytest.raises(ValueError):
            OptimizationResult(
                optimization_id="test-opt-003",
                portfolio_id="test-portfolio-003",
                optimization_type=OptimizationType.RISK_PARITY,
                expected_return=0.10,
                expected_volatility=-0.05,  # Invalid negative volatility
                sharpe_ratio=0.50
            )
    
    def test_efficient_frontier_calculation(self):
        """Test efficient frontier calculation"""
        result = OptimizationResult(
            optimization_id="test-opt-004",
            portfolio_id="test-portfolio-004",
            optimization_type=OptimizationType.MPT,
            expected_return=0.12,
            expected_volatility=0.18,
            sharpe_ratio=0.67
        )
        
        # Add frontier points
        frontier_points = [
            {"return": 0.08, "volatility": 0.15, "weights": {"AAPL": 0.6, "GOOGL": 0.4}},
            {"return": 0.10, "volatility": 0.16, "weights": {"AAPL": 0.5, "GOOGL": 0.5}},
            {"return": 0.12, "volatility": 0.18, "weights": {"AAPL": 0.4, "GOOGL": 0.6}},
            {"return": 0.14, "volatility": 0.21, "weights": {"AAPL": 0.3, "GOOGL": 0.7}}
        ]
        
        result.efficient_frontier = frontier_points
        
        # Test frontier analysis
        max_sharpe_point = result.find_max_sharpe_portfolio()
        assert max_sharpe_point is not None
        assert "return" in max_sharpe_point
        assert "volatility" in max_sharpe_point
        
        min_variance_point = result.find_min_variance_portfolio()
        assert min_variance_point is not None
        assert min_variance_point["volatility"] == min(point["volatility"] for point in frontier_points)


class TestMarketViewModel:
    """Test MarketView model"""
    
    def test_market_view_creation(self):
        """Test basic market view creation"""
        view = MarketView(
            view_id="test-view-001",
            portfolio_id="test-portfolio-001",
            type=ViewType.ABSOLUTE,
            assets=["AAPL", "GOOGL"],
            expected_return=0.15,
            confidence=0.7,
            description="Tech stocks expected to outperform"
        )
        
        assert view.view_id == "test-view-001"
        assert view.portfolio_id == "test-portfolio-001"
        assert view.type == ViewType.ABSOLUTE
        assert view.assets == ["AAPL", "GOOGL"]
        assert view.expected_return == 0.15
        assert view.confidence == 0.7
        assert view.description == "Tech stocks expected to outperform"
    
    def test_market_view_validation(self):
        """Test market view validation"""
        # Valid absolute view
        absolute_view = MarketView(
            view_id="test-view-002",
            portfolio_id="test-portfolio-002",
            type=ViewType.ABSOLUTE,
            assets=["TSLA"],
            expected_return=0.20,
            confidence=0.6
        )
        
        assert absolute_view.is_valid()
        
        # Valid relative view
        relative_view = MarketView(
            view_id="test-view-003",
            portfolio_id="test-portfolio-003",
            type=ViewType.RELATIVE,
            assets=["AAPL", "MSFT"],
            expected_return_diff=0.05,
            confidence=0.8
        )
        
        assert relative_view.is_valid()
        
        # Invalid view - confidence out of range
        with pytest.raises(ValueError):
            MarketView(
                view_id="test-view-004",
                portfolio_id="test-portfolio-004",
                type=ViewType.ABSOLUTE,
                assets=["NVDA"],
                expected_return=0.18,
                confidence=1.5  # Invalid confidence > 1.0
            )
    
    def test_view_conflict_detection(self):
        """Test market view conflict detection"""
        views = [
            MarketView(
                view_id="view-001",
                portfolio_id="test-portfolio-005",
                type=ViewType.ABSOLUTE,
                assets=["AAPL"],
                expected_return=0.15,
                confidence=0.7
            ),
            MarketView(
                view_id="view-002",
                portfolio_id="test-portfolio-005",
                type=ViewType.ABSOLUTE,
                assets=["AAPL"],
                expected_return=0.08,  # Conflicting return expectation
                confidence=0.6
            )
        ]
        
        conflicts = MarketView.detect_conflicts(views)
        assert len(conflicts) > 0
        assert any("AAPL" in conflict for conflict in conflicts)


class TestRebalancingRecommendationModel:
    """Test RebalancingRecommendation model"""
    
    def test_rebalancing_recommendation_creation(self):
        """Test basic rebalancing recommendation creation"""
        recommendation = RebalancingRecommendation(
            recommendation_id="test-rec-001",
            portfolio_id="test-portfolio-001",
            strategy="intelligent",
            total_drift=0.15,
            number_of_trades=8
        )
        
        assert recommendation.recommendation_id == "test-rec-001"
        assert recommendation.portfolio_id == "test-portfolio-001"
        assert recommendation.strategy == "intelligent"
        assert recommendation.total_drift == 0.15
        assert recommendation.number_of_trades == 8
        assert recommendation.status == RebalancingStatus.PENDING
    
    def test_trade_recommendations(self):
        """Test trade recommendations"""
        recommendation = RebalancingRecommendation(
            recommendation_id="test-rec-002",
            portfolio_id="test-portfolio-002",
            strategy="threshold",
            total_drift=0.12,
            number_of_trades=5
        )
        
        # Add trade recommendations
        trade_recommendations = [
            {
                "asset_id": "AAPL",
                "action": "BUY",
                "quantity": 50,
                "current_weight": 0.15,
                "target_weight": 0.20,
                "drift": 0.05
            },
            {
                "asset_id": "GOOGL",
                "action": "SELL",
                "quantity": 25,
                "current_weight": 0.25,
                "target_weight": 0.20,
                "drift": -0.05
            }
        ]
        
        recommendation.trade_recommendations = trade_recommendations
        
        # Test trade analysis
        buy_trades = recommendation.get_buy_trades()
        assert len(buy_trades) == 1
        assert buy_trades[0]["asset_id"] == "AAPL"
        
        sell_trades = recommendation.get_sell_trades()
        assert len(sell_trades) == 1
        assert sell_trades[0]["asset_id"] == "GOOGL"
        
        # Test total trade value
        total_trade_value = recommendation.calculate_total_trade_value()
        assert total_trade_value > 0


class TestRiskMetricsModel:
    """Test RiskMetrics model"""
    
    def test_risk_metrics_creation(self):
        """Test basic risk metrics creation"""
        risk_metrics = RiskMetrics(
            risk_metrics_id="test-risk-001",
            portfolio_id="test-portfolio-001",
            risk_type=RiskType.VAR,
            confidence_level=0.95,
            time_horizon=1,
            value=5000.0
        )
        
        assert risk_metrics.risk_metrics_id == "test-risk-001"
        assert risk_metrics.portfolio_id == "test-portfolio-001"
        assert risk_metrics.risk_type == RiskType.VAR
        assert risk_metrics.confidence_level == 0.95
        assert risk_metrics.time_horizon == 1
        assert risk_metrics.value == 5000.0
    
    def test_risk_metrics_calculation(self):
        """Test risk metrics calculations"""
        risk_metrics = RiskMetrics(
            risk_metrics_id="test-risk-002",
            portfolio_id="test-portfolio-002",
            risk_type=RiskType.VAR,
            confidence_level=0.99,
            time_horizon=10,
            value=10000.0,
            portfolio_value=100000.0
        )
        
        # Test percentage calculation
        var_percentage = risk_metrics.calculate_percentage()
        expected_percentage = 10000.0 / 100000.0
        assert abs(var_percentage - expected_percentage) < 1e-6
        
        # Test annualized calculation
        annualized_value = risk_metrics.calculate_annualized_value()
        expected_annualized = 10000.0 * np.sqrt(252 / 10)  # Annualized from 10-day
        assert abs(annualized_value - expected_annualized) < 1e-6
    
    def test_stress_test_results(self):
        """Test stress test results"""
        risk_metrics = RiskMetrics(
            risk_metrics_id="test-risk-003",
            portfolio_id="test-portfolio-003",
            risk_type=RiskType.STRESS_TEST,
            confidence_level=0.95,
            time_horizon=1,
            value=15000.0
        )
        
        # Add stress test scenarios
        stress_scenarios = [
            {
                "name": "Market Crash",
                "shock_return": -0.20,
                "portfolio_impact": -0.18,
                "description": "20% market decline scenario"
            },
            {
                "name": "Interest Rate Shock",
                "shock_return": 0.05,
                "portfolio_impact": -0.08,
                "description": "5% interest rate increase scenario"
            }
        ]
        
        risk_metrics.stress_scenarios = stress_scenarios
        
        # Test scenario analysis
        worst_case = risk_metrics.find_worst_case_scenario()
        assert worst_case is not None
        assert worst_case["name"] == "Market Crash"
        
        # Test impact analysis
        total_impact = risk_metrics.calculate_total_impact()
        expected_impact = abs(-0.18) + abs(-0.08)
        assert abs(total_impact - expected_impact) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])












