#!/usr/bin/env python3
"""
Integration tests for portfolio management system
"""
import pytest
import asyncio
import aiohttp
import json
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

# Import system components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.portfolio.services.portfolio_manager import PortfolioManager
from src.portfolio.optimization.mpt_optimizer import MPTOptimizer
from src.portfolio.risk.risk_manager import RiskManager
from src.portfolio.models.portfolio import Portfolio, RiskTolerance
from src.portfolio.models.position import Position
from src.portfolio.models.asset import Asset, AssetType


class TestPortfolioSystemIntegration:
    """Test complete portfolio system integration"""
    
    def setup_method(self):
        """Set up test data"""
        self.portfolio_manager = PortfolioManager()
        self.mpt_optimizer = MPTOptimizer()
        self.risk_manager = RiskManager()
        
        # Create test portfolio
        self.portfolio = Portfolio(
            portfolio_id="integration-test-portfolio",
            name="Integration Test Portfolio",
            owner_id="integration-test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD",
            total_value=100000.0
        )
        
        # Create test assets
        self.assets = [
            Asset(
                asset_id="AAPL",
                symbol="AAPL",
                name="Apple Inc.",
                asset_type=AssetType.STOCK,
                exchange="NASDAQ",
                currency="USD",
                current_price=175.0,
                daily_volatility=0.025,
                beta=1.2
            ),
            Asset(
                asset_id="GOOGL",
                symbol="GOOGL",
                name="Alphabet Inc.",
                asset_type=AssetType.STOCK,
                exchange="NASDAQ",
                currency="USD",
                current_price=2800.0,
                daily_volatility=0.030,
                beta=1.1
            ),
            Asset(
                asset_id="MSFT",
                symbol="MSFT",
                name="Microsoft Corporation",
                asset_type=AssetType.STOCK,
                exchange="NASDAQ",
                currency="USD",
                current_price=350.0,
                daily_volatility=0.022,
                beta=0.9
            ),
            Asset(
                asset_id="TSLA",
                symbol="TSLA",
                name="Tesla Inc.",
                asset_type=AssetType.STOCK,
                exchange="NASDAQ",
                currency="USD",
                current_price=250.0,
                daily_volatility=0.045,
                beta=1.8
            ),
            Asset(
                asset_id="SPY",
                symbol="SPY",
                name="SPDR S&P 500 ETF",
                asset_type=AssetType.ETF,
                exchange="NYSE",
                currency="USD",
                current_price=420.0,
                daily_volatility=0.015,
                beta=1.0
            )
        ]
        
        # Create test positions
        self.positions = [
            Position(
                position_id="pos-001",
                portfolio_id="integration-test-portfolio",
                asset_id="AAPL",
                quantity=100,
                average_cost=150.0,
                current_price=175.0
            ),
            Position(
                position_id="pos-002",
                portfolio_id="integration-test-portfolio",
                asset_id="GOOGL",
                quantity=50,
                average_cost=2500.0,
                current_price=2800.0
            ),
            Position(
                position_id="pos-003",
                portfolio_id="integration-test-portfolio",
                asset_id="MSFT",
                quantity=75,
                average_cost=300.0,
                current_price=350.0
            ),
            Position(
                position_id="pos-004",
                portfolio_id="integration-test-portfolio",
                asset_id="TSLA",
                quantity=25,
                average_cost=200.0,
                current_price=250.0
            ),
            Position(
                position_id="pos-005",
                portfolio_id="integration-test-portfolio",
                asset_id="SPY",
                quantity=200,
                average_cost=400.0,
                current_price=420.0
            )
        ]
        
        self.portfolio.positions = self.positions
        
        # Create correlation and covariance matrices
        self.correlation_matrix = np.array([
            [1.0, 0.7, 0.6, 0.5, 0.8],  # AAPL correlations
            [0.7, 1.0, 0.8, 0.4, 0.7],  # GOOGL correlations
            [0.6, 0.8, 1.0, 0.3, 0.6],  # MSFT correlations
            [0.5, 0.4, 0.3, 1.0, 0.4],  # TSLA correlations
            [0.8, 0.7, 0.6, 0.4, 1.0]   # SPY correlations
        ])
        
        volatilities = np.array([0.025, 0.030, 0.022, 0.045, 0.015])
        self.covariance_matrix = np.outer(volatilities, volatilities) * self.correlation_matrix
    
    def test_portfolio_lifecycle_integration(self):
        """Test complete portfolio lifecycle"""
        # Step 1: Create portfolio
        created_portfolio = self.portfolio_manager.create_portfolio(
            name="Integration Test Portfolio",
            owner_id="integration-test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD"
        )
        
        assert created_portfolio is not None
        assert created_portfolio.portfolio_id is not None
        assert created_portfolio.name == "Integration Test Portfolio"
        
        # Step 2: Add positions
        for position in self.positions:
            added_position = self.portfolio_manager.add_position(
                portfolio_id=created_portfolio.portfolio_id,
                asset_id=position.asset_id,
                quantity=position.quantity,
                average_cost=position.average_cost,
                current_price=position.current_price
            )
            
            assert added_position is not None
            assert added_position.portfolio_id == created_portfolio.portfolio_id
        
        # Step 3: Update portfolio value
        updated_portfolio = self.portfolio_manager.get_portfolio(created_portfolio.portfolio_id)
        current_value = updated_portfolio.calculate_current_value()
        
        assert current_value > 0
        assert updated_portfolio.total_value == current_value
        
        # Step 4: Calculate performance metrics
        performance_metrics = self.portfolio_manager.calculate_performance_metrics(
            portfolio_id=created_portfolio.portfolio_id
        )
        
        assert performance_metrics is not None
        assert "total_return" in performance_metrics
        assert "current_value" in performance_metrics
        assert "unrealized_pnl" in performance_metrics
        
        # Step 5: Validate portfolio constraints
        violations = updated_portfolio.validate_constraints()
        assert isinstance(violations, list)
    
    def test_optimization_integration(self):
        """Test portfolio optimization integration"""
        # Step 1: Calculate expected returns
        expected_returns = np.array([0.12, 0.15, 0.10, 0.20, 0.08])  # For the 5 assets
        
        # Step 2: Run MPT optimization
        optimization_result = self.mpt_optimizer.maximize_sharpe_ratio(
            expected_returns=expected_returns,
            covariance_matrix=self.covariance_matrix,
            risk_free_rate=0.02
        )
        
        assert optimization_result is not None
        assert "weights" in optimization_result
        assert "expected_return" in optimization_result
        assert "expected_volatility" in optimization_result
        assert "sharpe_ratio" in optimization_result
        
        # Step 3: Validate optimization results
        weights = optimization_result["weights"]
        assert abs(np.sum(weights) - 1.0) < 1e-6  # Weights sum to 1
        assert np.all(weights >= 0)  # Long-only constraint
        
        # Step 4: Generate efficient frontier
        frontier = self.mpt_optimizer.generate_efficient_frontier(
            expected_returns=expected_returns,
            covariance_matrix=self.covariance_matrix,
            num_portfolios=20,
            risk_free_rate=0.02
        )
        
        assert frontier is not None
        assert "returns" in frontier
        assert "volatilities" in frontier
        assert "weights" in frontier
        
        # Step 5: Validate frontier properties
        returns = frontier["returns"]
        volatilities = frontier["volatilities"]
        
        # Returns should be increasing
        assert np.all(np.diff(returns) >= 0)
        # Volatilities should be increasing with returns
        assert np.all(np.diff(volatilities) >= 0)
    
    def test_risk_management_integration(self):
        """Test risk management integration"""
        portfolio_value = self.portfolio.calculate_current_value()
        
        # Step 1: Calculate VaR
        var_result = self.risk_manager.calculate_var(
            portfolio_value=portfolio_value,
            covariance_matrix=self.covariance_matrix,
            positions=self.positions,
            confidence_level=0.95,
            time_horizon=1
        )
        
        assert var_result is not None
        assert "var_value" in var_result
        assert "var_percentage" in var_result
        assert var_result["var_value"] > 0
        
        # Step 2: Calculate CVaR
        cvar_result = self.risk_manager.calculate_cvar(
            portfolio_value=portfolio_value,
            covariance_matrix=self.covariance_matrix,
            positions=self.positions,
            confidence_level=0.95,
            time_horizon=1
        )
        
        assert cvar_result is not None
        assert "cvar_value" in cvar_result
        assert cvar_result["cvar_value"] > var_result["var_value"]  # CVaR > VaR
        
        # Step 3: Calculate portfolio volatility
        volatility_result = self.risk_manager.calculate_portfolio_volatility(
            positions=self.positions,
            covariance_matrix=self.covariance_matrix
        )
        
        assert volatility_result is not None
        assert "portfolio_volatility" in volatility_result
        assert volatility_result["portfolio_volatility"] > 0
        
        # Step 4: Calculate portfolio beta
        beta_result = self.risk_manager.calculate_portfolio_beta(
            positions=self.positions,
            assets=self.assets,
            market_return=0.08,
            risk_free_rate=0.02
        )
        
        assert beta_result is not None
        assert "portfolio_beta" in beta_result
        assert 0.5 <= beta_result["portfolio_beta"] <= 2.0  # Reasonable beta range
        
        # Step 5: Perform stress testing
        stress_scenarios = [
            {"name": "Market Crash", "shock_return": -0.20},
            {"name": "Interest Rate Shock", "shock_return": 0.05}
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
        assert len(stress_result["scenarios"]) == len(stress_scenarios)
    
    def test_end_to_end_workflow_integration(self):
        """Test complete end-to-end workflow"""
        # Step 1: Create and populate portfolio
        portfolio = self.portfolio_manager.create_portfolio(
            name="E2E Test Portfolio",
            owner_id="e2e-test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD"
        )
        
        for position in self.positions:
            self.portfolio_manager.add_position(
                portfolio_id=portfolio.portfolio_id,
                asset_id=position.asset_id,
                quantity=position.quantity,
                average_cost=position.average_cost,
                current_price=position.current_price
            )
        
        # Step 2: Calculate current performance
        performance = self.portfolio_manager.calculate_performance_metrics(
            portfolio_id=portfolio.portfolio_id
        )
        
        # Step 3: Run optimization
        expected_returns = np.array([0.12, 0.15, 0.10, 0.20, 0.08])
        optimization = self.mpt_optimizer.maximize_sharpe_ratio(
            expected_returns=expected_returns,
            covariance_matrix=self.covariance_matrix,
            risk_free_rate=0.02
        )
        
        # Step 4: Calculate risk metrics
        portfolio_value = performance["current_value"]
        risk_metrics = self.risk_manager.calculate_comprehensive_risk_metrics(
            portfolio=portfolio,
            positions=self.positions,
            assets=self.assets,
            portfolio_value=portfolio_value,
            covariance_matrix=self.covariance_matrix
        )
        
        # Step 5: Validate integration results
        assert portfolio is not None
        assert performance is not None
        assert optimization is not None
        assert risk_metrics is not None
        
        # Check data consistency
        assert portfolio.portfolio_id is not None
        assert performance["current_value"] > 0
        assert optimization["sharpe_ratio"] > 0
        assert risk_metrics.portfolio_value == portfolio_value
    
    def test_error_handling_integration(self):
        """Test error handling across system components"""
        # Test with invalid portfolio ID
        with pytest.raises(Exception):
            self.portfolio_manager.get_portfolio("invalid-portfolio-id")
        
        # Test with invalid optimization parameters
        with pytest.raises(Exception):
            self.mpt_optimizer.maximize_sharpe_ratio(
                expected_returns=np.array([0.12]),  # Only one asset
                covariance_matrix=self.covariance_matrix,  # 5x5 matrix
                risk_free_rate=0.02
            )
        
        # Test with invalid risk calculation parameters
        with pytest.raises(Exception):
            self.risk_manager.calculate_var(
                portfolio_value=-1000.0,  # Negative portfolio value
                covariance_matrix=self.covariance_matrix,
                positions=self.positions,
                confidence_level=0.95,
                time_horizon=1
            )
    
    def test_performance_integration(self):
        """Test system performance under load"""
        # Test with larger portfolio
        large_portfolio = Portfolio(
            portfolio_id="large-test-portfolio",
            name="Large Test Portfolio",
            owner_id="performance-test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD",
            total_value=1000000.0  # $1M portfolio
        )
        
        # Create 50 positions
        large_positions = []
        for i in range(50):
            position = Position(
                position_id=f"pos-{i:03d}",
                portfolio_id="large-test-portfolio",
                asset_id=f"ASSET_{i:03d}",
                quantity=100 + i,
                average_cost=100.0 + i,
                current_price=105.0 + i
            )
            large_positions.append(position)
        
        large_portfolio.positions = large_positions
        
        # Create corresponding covariance matrix (50x50)
        np.random.seed(42)
        large_covariance = np.random.rand(50, 50)
        large_covariance = large_covariance @ large_covariance.T  # Make positive definite
        
        # Test optimization performance
        expected_returns = np.random.rand(50) * 0.2  # Random returns 0-20%
        
        start_time = datetime.now()
        optimization_result = self.mpt_optimizer.maximize_sharpe_ratio(
            expected_returns=expected_returns,
            covariance_matrix=large_covariance,
            risk_free_rate=0.02
        )
        end_time = datetime.now()
        
        # Should complete within reasonable time (< 10 seconds)
        duration = (end_time - start_time).total_seconds()
        assert duration < 10.0
        assert optimization_result is not None
        
        # Test risk calculation performance
        start_time = datetime.now()
        risk_result = self.risk_manager.calculate_var(
            portfolio_value=1000000.0,
            covariance_matrix=large_covariance,
            positions=large_positions,
            confidence_level=0.95,
            time_horizon=1
        )
        end_time = datetime.now()
        
        # Should complete within reasonable time (< 5 seconds)
        duration = (end_time - start_time).total_seconds()
        assert duration < 5.0
        assert risk_result is not None
    
    def test_data_consistency_integration(self):
        """Test data consistency across system components"""
        # Create portfolio with known data
        test_portfolio = Portfolio(
            portfolio_id="consistency-test-portfolio",
            name="Consistency Test Portfolio",
            owner_id="consistency-test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD",
            total_value=100000.0
        )
        
        # Add known positions
        known_positions = [
            Position(
                position_id="pos-001",
                portfolio_id="consistency-test-portfolio",
                asset_id="AAPL",
                quantity=100,
                average_cost=150.0,
                current_price=175.0
            ),
            Position(
                position_id="pos-002",
                portfolio_id="consistency-test-portfolio",
                asset_id="GOOGL",
                quantity=50,
                average_cost=2500.0,
                current_price=2800.0
            )
        ]
        
        test_portfolio.positions = known_positions
        
        # Calculate expected values
        expected_aapl_value = 100 * 175.0
        expected_googl_value = 50 * 2800.0
        expected_total_value = expected_aapl_value + expected_googl_value
        
        # Test portfolio value calculation consistency
        calculated_value = test_portfolio.calculate_current_value()
        assert abs(calculated_value - expected_total_value) < 1e-6
        
        # Test position value consistency
        for position in known_positions:
            position_value = position.calculate_current_value()
            if position.asset_id == "AAPL":
                assert abs(position_value - expected_aapl_value) < 1e-6
            elif position.asset_id == "GOOGL":
                assert abs(position_value - expected_googl_value) < 1e-6
        
        # Test P&L calculation consistency
        aapl_position = known_positions[0]
        aapl_pnl = aapl_position.calculate_unrealized_pnl()
        expected_aapl_pnl = (175.0 - 150.0) * 100
        assert abs(aapl_pnl - expected_aapl_pnl) < 1e-6
        
        googl_position = known_positions[1]
        googl_pnl = googl_position.calculate_unrealized_pnl()
        expected_googl_pnl = (2800.0 - 2500.0) * 50
        assert abs(googl_pnl - expected_googl_pnl) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

