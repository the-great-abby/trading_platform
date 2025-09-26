"""
Performance tests for live trading system.

Tests system performance, scalability, and response times.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone
import uuid
import statistics

from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, LiveTrade, RiskProfile, OrderStatus,
    StrategyType, TradeAction, TradeStatus, PositionStatus, RiskLevel
)


@pytest.fixture
def performance_database():
    """Create performance test database."""
    db = AsyncMock()
    
    # Mock account
    account = LiveTradingAccount(
        account_id="perf-test-account-123",
        public_account_id="public-perf-123",
        account_name="Performance Test Account",
        account_type="CASH",
        buying_power=100000.0,
        cash_balance=50000.0,
        equity=150000.0,
        is_active=True
    )
    
    # Mock risk profile
    risk_profile = RiskProfile(
        account_id="perf-test-account-123",
        max_position_size=50000.0,
        max_portfolio_risk=0.10,
        max_daily_loss=5000.0,
        max_daily_trades=100,
        allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD", "CALENDAR_SPREAD"]',
        max_greeks_exposure='{"delta": 5000.0, "gamma": 500.0}',
        emergency_stop_active=False,
        risk_level=RiskLevel.MODERATE
    )
    
    # Configure database responses
    def mock_execute(query_result):
        if hasattr(query_result, 'scalar_one_or_none'):
            if 'account' in str(query_result):
                return account
            elif 'risk_profile' in str(query_result):
                return risk_profile
            else:
                return None
        elif hasattr(query_result, 'scalars'):
            return []  # No existing positions/trades
        elif hasattr(query_result, 'scalar'):
            return 0  # Mock count queries
        return query_result
    
    db.execute.side_effect = mock_execute
    return db


@pytest.fixture
def performance_redis():
    """Create performance test Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None  # No emergency stop
    redis.set.return_value = True
    redis.delete.return_value = True
    redis.ping.return_value = True
    redis.info.return_value = {
        "connected_clients": 5,
        "used_memory": 4096000,
        "keyspace_hits": 10000,
        "keyspace_misses": 1000
    }
    return redis


@pytest.fixture
def performance_public_api():
    """Create performance test Public.com API client."""
    api = AsyncMock()
    
    # Mock authentication
    api.authenticate.return_value = {
        "access_token": "perf_access_token_123",
        "refresh_token": "perf_refresh_token_456",
        "expires_in": 3600
    }
    
    # Mock account info
    api.get_account_info.return_value = {
        "account_id": "public-perf-123",
        "buying_power": 100000.0,
        "cash_balance": 50000.0,
        "equity": 150000.0
    }
    
    # Mock positions
    api.get_positions.return_value = {
        "positions": []
    }
    
    # Mock market data
    api.get_market_data.return_value = {
        "symbol": "SPY",
        "price": 405.50,
        "bid": 405.45,
        "ask": 405.55,
        "volume": 1000000
    }
    
    # Mock options chain
    api.get_options_chain.return_value = {
        "symbol": "SPY",
        "expiration_dates": ["2024-01-19", "2024-01-26"],
        "strikes": [400, 405, 410],
        "options": [
            {
                "strike": 400,
                "expiration": "2024-01-19",
                "type": "CALL",
                "bid": 5.50,
                "ask": 5.75
            }
        ]
    }
    
    return api


class TestTradeExecutionPerformance:
    """Test trade execution performance."""
    
    @pytest.mark.asyncio
    async def test_single_trade_execution_time(self, performance_database, performance_redis, performance_public_api):
        """Test single trade execution time."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(performance_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(performance_database, performance_redis)
        
        trading_service = TradingService(
            db_session=performance_database,
            public_api_client=performance_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            performance_public_api.execute_order.return_value = {
                "order_id": "perf_single_trade_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute trade and measure time
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            start_time = time.time()
            result = await trading_service.execute_trade("perf-test-account-123", trade_details)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Verify trade execution
            assert result["success"] is True
            assert result["order_id"] == "perf_single_trade_123"
            assert result["status"] == "FILLED"
            
            # Performance assertions
            assert execution_time < 1.0, f"Trade execution took {execution_time:.3f}s, expected < 1.0s"
            print(f"Single trade execution time: {execution_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_multiple_trade_execution_time(self, performance_database, performance_redis, performance_public_api):
        """Test multiple trade execution time."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(performance_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(performance_database, performance_redis)
        
        trading_service = TradingService(
            db_session=performance_database,
            public_api_client=performance_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            performance_public_api.execute_order.return_value = {
                "order_id": "perf_multiple_trade_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute multiple trades and measure time
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            num_trades = 10
            execution_times = []
            
            for i in range(num_trades):
                start_time = time.time()
                result = await trading_service.execute_trade("perf-test-account-123", trade_details)
                end_time = time.time()
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                # Verify trade execution
                assert result["success"] is True
                assert result["status"] == "FILLED"
            
            # Performance analysis
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            min_execution_time = min(execution_times)
            
            print(f"Multiple trade execution times:")
            print(f"  Average: {avg_execution_time:.3f}s")
            print(f"  Max: {max_execution_time:.3f}s")
            print(f"  Min: {min_execution_time:.3f}s")
            
            # Performance assertions
            assert avg_execution_time < 1.0, f"Average execution time {avg_execution_time:.3f}s, expected < 1.0s"
            assert max_execution_time < 2.0, f"Max execution time {max_execution_time:.3f}s, expected < 2.0s"
    
    @pytest.mark.asyncio
    async def test_concurrent_trade_execution_performance(self, performance_database, performance_redis, performance_public_api):
        """Test concurrent trade execution performance."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(performance_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(performance_database, performance_redis)
        
        trading_service = TradingService(
            db_session=performance_database,
            public_api_client=performance_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            performance_public_api.execute_order.return_value = {
                "order_id": "perf_concurrent_trade_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute concurrent trades and measure time
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            num_concurrent_trades = 20
            
            async def execute_trade():
                start_time = time.time()
                result = await trading_service.execute_trade("perf-test-account-123", trade_details)
                end_time = time.time()
                return end_time - start_time, result
            
            # Execute concurrent trades
            start_time = time.time()
            tasks = [execute_trade() for _ in range(num_concurrent_trades)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Analyze results
            successful_trades = 0
            execution_times = []
            
            for result in results:
                if isinstance(result, Exception):
                    print(f"Trade failed: {result}")
                else:
                    execution_time, trade_result = result
                    execution_times.append(execution_time)
                    if trade_result["success"]:
                        successful_trades += 1
            
            # Performance analysis
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0
            max_execution_time = max(execution_times) if execution_times else 0
            min_execution_time = min(execution_times) if execution_times else 0
            
            print(f"Concurrent trade execution performance:")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Successful trades: {successful_trades}/{num_concurrent_trades}")
            print(f"  Average execution time: {avg_execution_time:.3f}s")
            print(f"  Max execution time: {max_execution_time:.3f}s")
            print(f"  Min execution time: {min_execution_time:.3f}s")
            
            # Performance assertions
            assert successful_trades > 0, "No trades were successful"
            assert total_time < 10.0, f"Total execution time {total_time:.3f}s, expected < 10.0s"
            assert avg_execution_time < 2.0, f"Average execution time {avg_execution_time:.3f}s, expected < 2.0s"


class TestRiskManagementPerformance:
    """Test risk management performance."""
    
    @pytest.mark.asyncio
    async def test_risk_check_performance(self, performance_database, performance_redis, performance_public_api):
        """Test risk check performance."""
        from src.services.live_trading.risk_service import RiskService
        
        # Create risk service
        risk_service = RiskService(performance_database)
        
        # Test risk check performance
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        num_checks = 100
        execution_times = []
        
        for i in range(num_checks):
            start_time = time.time()
            result = await risk_service.comprehensive_risk_check("perf-test-account-123", trade_details)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # Verify risk check
            assert result["passed"] is True
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        
        print(f"Risk check performance:")
        print(f"  Average: {avg_execution_time:.3f}s")
        print(f"  Max: {max_execution_time:.3f}s")
        print(f"  Min: {min_execution_time:.3f}s")
        
        # Performance assertions
        assert avg_execution_time < 0.1, f"Average risk check time {avg_execution_time:.3f}s, expected < 0.1s"
        assert max_execution_time < 0.5, f"Max risk check time {max_execution_time:.3f}s, expected < 0.5s"
    
    @pytest.mark.asyncio
    async def test_position_risk_calculation_performance(self, performance_database, performance_redis, performance_public_api):
        """Test position risk calculation performance."""
        from src.services.live_trading.risk_service import RiskService
        
        # Create risk service
        risk_service = RiskService(performance_database)
        
        # Test position risk calculation performance
        positions = [
            {"symbol": "SPY", "quantity": 100, "price": 400.0, "volatility": 0.20},
            {"symbol": "QQQ", "quantity": 50, "price": 300.0, "volatility": 0.25},
            {"symbol": "AAPL", "quantity": 75, "price": 150.0, "volatility": 0.30}
        ]
        
        num_calculations = 50
        execution_times = []
        
        for i in range(num_calculations):
            start_time = time.time()
            var_95 = await risk_service.calculate_var(positions, confidence_level=0.95)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # Verify calculation
            assert var_95 > 0
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        
        print(f"Position risk calculation performance:")
        print(f"  Average: {avg_execution_time:.3f}s")
        print(f"  Max: {max_execution_time:.3f}s")
        print(f"  Min: {min_execution_time:.3f}s")
        
        # Performance assertions
        assert avg_execution_time < 0.05, f"Average calculation time {avg_execution_time:.3f}s, expected < 0.05s"
        assert max_execution_time < 0.2, f"Max calculation time {max_execution_time:.3f}s, expected < 0.2s"


class TestPositionManagementPerformance:
    """Test position management performance."""
    
    @pytest.mark.asyncio
    async def test_position_update_performance(self, performance_database, performance_redis, performance_public_api):
        """Test position update performance."""
        from src.services.live_trading.position_service import PositionService
        
        # Create position service
        position_service = PositionService(performance_database)
        
        # Test position update performance
        update_data = {
            "quantity": 50,
            "price": Decimal("410.00")
        }
        
        num_updates = 100
        execution_times = []
        
        for i in range(num_updates):
            start_time = time.time()
            result = await position_service.update_position_quantity("perf-test-account-123", "SPY", update_data)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # Verify update
            assert result["quantity"] == 50
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        
        print(f"Position update performance:")
        print(f"  Average: {avg_execution_time:.3f}s")
        print(f"  Max: {max_execution_time:.3f}s")
        print(f"  Min: {min_execution_time:.3f}s")
        
        # Performance assertions
        assert avg_execution_time < 0.1, f"Average update time {avg_execution_time:.3f}s, expected < 0.1s"
        assert max_execution_time < 0.5, f"Max update time {max_execution_time:.3f}s, expected < 0.5s"
    
    @pytest.mark.asyncio
    async def test_portfolio_calculation_performance(self, performance_database, performance_redis, performance_public_api):
        """Test portfolio calculation performance."""
        from src.services.live_trading.position_service import PositionService
        
        # Create position service
        position_service = PositionService(performance_database)
        
        # Test portfolio calculation performance
        num_calculations = 50
        execution_times = []
        
        for i in range(num_calculations):
            start_time = time.time()
            portfolio_value = await position_service.calculate_portfolio_value("perf-test-account-123")
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # Verify calculation
            assert portfolio_value >= 0
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        
        print(f"Portfolio calculation performance:")
        print(f"  Average: {avg_execution_time:.3f}s")
        print(f"  Max: {max_execution_time:.3f}s")
        print(f"  Min: {min_execution_time:.3f}s")
        
        # Performance assertions
        assert avg_execution_time < 0.1, f"Average calculation time {avg_execution_time:.3f}s, expected < 0.1s"
        assert max_execution_time < 0.5, f"Max calculation time {max_execution_time:.3f}s, expected < 0.5s"


class TestSystemPerformance:
    """Test system performance."""
    
    @pytest.mark.asyncio
    async def test_system_health_check_performance(self, performance_database, performance_redis, performance_public_api):
        """Test system health check performance."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(performance_database, performance_redis)
        
        # Test health check performance
        num_checks = 50
        execution_times = []
        
        for i in range(num_checks):
            start_time = time.time()
            result = await system_service.perform_health_check()
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # Verify health check
            assert result["overall_status"] in ["healthy", "degraded", "critical"]
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        
        print(f"System health check performance:")
        print(f"  Average: {avg_execution_time:.3f}s")
        print(f"  Max: {max_execution_time:.3f}s")
        print(f"  Min: {min_execution_time:.3f}s")
        
        # Performance assertions
        assert avg_execution_time < 0.2, f"Average health check time {avg_execution_time:.3f}s, expected < 0.2s"
        assert max_execution_time < 1.0, f"Max health check time {max_execution_time:.3f}s, expected < 1.0s"
    
    @pytest.mark.asyncio
    async def test_emergency_stop_performance(self, performance_database, performance_redis, performance_public_api):
        """Test emergency stop performance."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(performance_database, performance_redis)
        
        # Test emergency stop performance
        num_operations = 50
        execution_times = []
        
        for i in range(num_operations):
            start_time = time.time()
            result = await system_service.activate_emergency_stop("perf-test-account-123", "Performance test")
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # Verify emergency stop
            assert result["success"] is True
            
            # Deactivate
            await system_service.deactivate_emergency_stop("perf-test-account-123")
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        
        print(f"Emergency stop performance:")
        print(f"  Average: {avg_execution_time:.3f}s")
        print(f"  Max: {max_execution_time:.3f}s")
        print(f"  Min: {min_execution_time:.3f}s")
        
        # Performance assertions
        assert avg_execution_time < 0.1, f"Average emergency stop time {avg_execution_time:.3f}s, expected < 0.1s"
        assert max_execution_time < 0.5, f"Max emergency stop time {max_execution_time:.3f}s, expected < 0.5s"


class TestMarketHoursPerformance:
    """Test market hours performance."""
    
    @pytest.mark.asyncio
    async def test_market_hours_check_performance(self, performance_database, performance_redis, performance_public_api):
        """Test market hours check performance."""
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create market hours service
        market_hours_service = MarketHoursService()
        
        # Test market hours check performance
        num_checks = 100
        execution_times = []
        
        for i in range(num_checks):
            start_time = time.time()
            result = market_hours_service.is_market_open()
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # Verify market hours check
            assert isinstance(result, bool)
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        
        print(f"Market hours check performance:")
        print(f"  Average: {avg_execution_time:.3f}s")
        print(f"  Max: {max_execution_time:.3f}s")
        print(f"  Min: {min_execution_time:.3f}s")
        
        # Performance assertions
        assert avg_execution_time < 0.01, f"Average market hours check time {avg_execution_time:.3f}s, expected < 0.01s"
        assert max_execution_time < 0.05, f"Max market hours check time {max_execution_time:.3f}s, expected < 0.05s"
    
    @pytest.mark.asyncio
    async def test_holiday_check_performance(self, performance_database, performance_redis, performance_public_api):
        """Test holiday check performance."""
        from src.services.live_trading.market_hours_service import MarketHoursService
        from datetime import date
        
        # Create market hours service
        market_hours_service = MarketHoursService()
        
        # Test holiday check performance
        test_dates = [
            date(2024, 1, 1),   # New Year's Day
            date(2024, 7, 4),   # Independence Day
            date(2024, 12, 25), # Christmas Day
            date(2024, 1, 15),  # Regular day
            date(2024, 6, 15),  # Regular day
        ]
        
        num_checks = 100
        execution_times = []
        
        for i in range(num_checks):
            test_date = test_dates[i % len(test_dates)]
            
            start_time = time.time()
            result = market_hours_service.is_holiday(test_date)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            # Verify holiday check
            assert isinstance(result, bool)
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        
        print(f"Holiday check performance:")
        print(f"  Average: {avg_execution_time:.3f}s")
        print(f"  Max: {max_execution_time:.3f}s")
        print(f"  Min: {min_execution_time:.3f}s")
        
        # Performance assertions
        assert avg_execution_time < 0.01, f"Average holiday check time {avg_execution_time:.3f}s, expected < 0.01s"
        assert max_execution_time < 0.05, f"Max holiday check time {max_execution_time:.3f}s, expected < 0.05s"


class TestScalabilityPerformance:
    """Test system scalability performance."""
    
    @pytest.mark.asyncio
    async def test_large_volume_trade_performance(self, performance_database, performance_redis, performance_public_api):
        """Test large volume trade performance."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(performance_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(performance_database, performance_redis)
        
        trading_service = TradingService(
            db_session=performance_database,
            public_api_client=performance_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution for large volume
            performance_public_api.execute_order.return_value = {
                "order_id": "perf_large_volume_123",
                "status": "FILLED",
                "filled_quantity": 10000,
                "average_price": 400.25
            }
            
            # Execute large volume trade and measure time
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 10000,  # Large volume
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            start_time = time.time()
            result = await trading_service.execute_trade("perf-test-account-123", trade_details)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Verify trade execution
            assert result["success"] is True
            assert result["filled_quantity"] == 10000
            
            print(f"Large volume trade execution time: {execution_time:.3f}s")
            
            # Performance assertions
            assert execution_time < 2.0, f"Large volume trade execution took {execution_time:.3f}s, expected < 2.0s"
    
    @pytest.mark.asyncio
    async def test_high_frequency_trade_performance(self, performance_database, performance_redis, performance_public_api):
        """Test high frequency trade performance."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(performance_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(performance_database, performance_redis)
        
        trading_service = TradingService(
            db_session=performance_database,
            public_api_client=performance_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            performance_public_api.execute_order.return_value = {
                "order_id": "perf_hf_trade_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute high frequency trades
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            num_trades = 50
            execution_times = []
            
            for i in range(num_trades):
                start_time = time.time()
                result = await trading_service.execute_trade("perf-test-account-123", trade_details)
                end_time = time.time()
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                # Verify trade execution
                assert result["success"] is True
            
            # Performance analysis
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            min_execution_time = min(execution_times)
            
            print(f"High frequency trade performance:")
            print(f"  Average: {avg_execution_time:.3f}s")
            print(f"  Max: {max_execution_time:.3f}s")
            print(f"  Min: {min_execution_time:.3f}s")
            
            # Performance assertions
            assert avg_execution_time < 0.5, f"Average HF trade time {avg_execution_time:.3f}s, expected < 0.5s"
            assert max_execution_time < 1.0, f"Max HF trade time {max_execution_time:.3f}s, expected < 1.0s"
