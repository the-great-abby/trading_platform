#!/usr/bin/env python3
"""
System Validation Test Script
Tests the core functionality of the Advanced Portfolio Management System
"""
import sys
import os
import traceback
from datetime import datetime, date

# Add the project root to the path
sys.path.append('.')

def test_portfolio_models():
    """Test portfolio model functionality"""
    print("🧪 Testing Portfolio Models...")
    
    try:
        from src.portfolio.models.portfolio import Portfolio, RiskTolerance, PortfolioStatus
        from src.portfolio.models.position import Position, PositionStatus
        from src.portfolio.models.asset import Asset, AssetType, AssetStatus
        
        # Test Portfolio creation
        portfolio = Portfolio(
            portfolio_id="test-portfolio-001",
            name="Test Portfolio",
            owner_id="test-user",
            risk_tolerance=RiskTolerance.MODERATE,
            base_currency="USD"
        )
        
        assert portfolio.portfolio_id == "test-portfolio-001"
        assert portfolio.risk_tolerance == RiskTolerance.MODERATE
        assert portfolio.status == PortfolioStatus.ACTIVE
        print("  ✅ Portfolio creation successful")
        
        # Test Position creation
        position = Position(
            position_id="test-position-001",
            portfolio_id="test-portfolio-001",
            asset_id="AAPL",
            quantity=100,
            average_cost=150.0,
            current_price=175.0
        )
        
        assert position.quantity == 100
        assert position.calculate_unrealized_pnl() == 2500.0  # (175-150) * 100
        print("  ✅ Position creation and P&L calculation successful")
        
        # Test Asset creation
        asset = Asset(
            asset_id="AAPL",
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.STOCK,
            exchange="NASDAQ",
            currency="USD",
            current_price=175.0,
            daily_volatility=0.025,
            beta=1.2
        )
        
        assert asset.symbol == "AAPL"
        assert asset.asset_type == AssetType.STOCK
        assert asset.beta == 1.2
        print("  ✅ Asset creation successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Portfolio models test failed: {e}")
        traceback.print_exc()
        return False

def test_optimization_algorithms():
    """Test optimization algorithm functionality"""
    print("🧪 Testing Optimization Algorithms...")
    
    try:
        from src.portfolio.optimization.mpt_optimizer import MPTOptimizer
        import numpy as np
        
        # Create test data
        expected_returns = np.array([0.12, 0.15, 0.10])
        covariance_matrix = np.array([
            [0.04, 0.02, 0.01],
            [0.02, 0.09, 0.02],
            [0.01, 0.02, 0.06]
        ])
        
        # Test MPT optimizer
        optimizer = MPTOptimizer()
        
        # Test Sharpe ratio maximization
        result = optimizer.maximize_sharpe_ratio(
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            risk_free_rate=0.02
        )
        
        assert result is not None
        assert "weights" in result
        assert "expected_return" in result
        assert "expected_volatility" in result
        assert "sharpe_ratio" in result
        
        # Check weights sum to 1
        weights = result["weights"]
        assert abs(np.sum(weights) - 1.0) < 1e-6
        print("  ✅ MPT optimization successful")
        
        # Test volatility minimization
        result2 = optimizer.minimize_volatility(covariance_matrix)
        assert result2 is not None
        assert "weights" in result2
        print("  ✅ Volatility minimization successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Optimization algorithms test failed: {e}")
        traceback.print_exc()
        return False

def test_risk_calculations():
    """Test risk calculation functionality"""
    print("🧪 Testing Risk Calculations...")
    
    try:
        from src.portfolio.risk.risk_manager import RiskManager
        from src.portfolio.models.position import Position
        import numpy as np
        
        # Create test data
        positions = [
            Position(
                position_id="pos-001",
                portfolio_id="test-portfolio",
                asset_id="AAPL",
                quantity=100,
                average_cost=150.0,
                current_price=175.0
            ),
            Position(
                position_id="pos-002",
                portfolio_id="test-portfolio",
                asset_id="GOOGL",
                quantity=50,
                average_cost=2500.0,
                current_price=2800.0
            )
        ]
        
        # Create covariance matrix
        covariance_matrix = np.array([
            [0.04, 0.02],
            [0.02, 0.09]
        ])
        
        # Test risk manager
        risk_manager = RiskManager()
        
        # Test VaR calculation
        var_result = risk_manager.calculate_var(
            portfolio_value=100000.0,
            covariance_matrix=covariance_matrix,
            positions=positions,
            confidence_level=0.95,
            time_horizon=1
        )
        
        assert var_result is not None
        assert "var_value" in var_result
        assert "var_percentage" in var_result
        assert var_result["var_value"] > 0
        print("  ✅ VaR calculation successful")
        
        # Test portfolio volatility
        volatility_result = risk_manager.calculate_portfolio_volatility(
            positions=positions,
            covariance_matrix=covariance_matrix
        )
        
        assert volatility_result is not None
        assert "portfolio_volatility" in volatility_result
        assert volatility_result["portfolio_volatility"] > 0
        print("  ✅ Portfolio volatility calculation successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Risk calculations test failed: {e}")
        traceback.print_exc()
        return False

def test_service_integration():
    """Test service integration"""
    print("🧪 Testing Service Integration...")
    
    try:
        from src.portfolio.services.portfolio_manager import PortfolioManager
        
        # Test portfolio manager
        portfolio_manager = PortfolioManager()
        
        # Test portfolio creation
        portfolio = portfolio_manager.create_portfolio(
            name="Integration Test Portfolio",
            owner_id="test-user",
            risk_tolerance="MODERATE",
            base_currency="USD"
        )
        
        assert portfolio is not None
        assert portfolio.name == "Integration Test Portfolio"
        assert portfolio.owner_id == "test-user"
        print("  ✅ Portfolio manager service successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Service integration test failed: {e}")
        traceback.print_exc()
        return False

def test_performance_optimizer():
    """Test performance optimization utilities"""
    print("🧪 Testing Performance Optimizer...")
    
    try:
        from src.portfolio.utils.performance_optimizer import PerformanceOptimizer, measure_performance
        
        # Test performance optimizer
        optimizer = PerformanceOptimizer()
        
        # Test decorator functionality
        @measure_performance
        def test_function(x):
            return x * 2
        
        result = test_function(5)
        assert result == 10
        print("  ✅ Performance optimizer decorator successful")
        
        # Test performance metrics
        report = optimizer.get_performance_report()
        assert report is not None
        print("  ✅ Performance metrics collection successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance optimizer test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all system validation tests"""
    print("🚀 Advanced Portfolio Management System - Validation Tests")
    print("=" * 60)
    
    tests = [
        test_portfolio_models,
        test_optimization_algorithms,
        test_risk_calculations,
        test_service_integration,
        test_performance_optimizer
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 60)
    print("📊 VALIDATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total:.1%}")
    
    if passed == total:
        print("🎉 All validation tests passed! System is working correctly.")
        return 0
    else:
        print("⚠️ Some validation tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)






















