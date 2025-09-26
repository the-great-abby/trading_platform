"""
Load tests for live trading system.

Tests system behavior under high load and stress conditions.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone
import uuid
import statistics
import random

from src.services.live_trading.models import (
    LiveTradingAccount, LivePosition, LiveTrade, RiskProfile, OrderStatus,
    StrategyType, TradeAction, TradeStatus, PositionStatus, RiskLevel
)


@pytest.fixture
def load_test_database():
    """Create load test database."""
    db = AsyncMock()
    
    # Mock account
    account = LiveTradingAccount(
        account_id="load-test-account-123",
        public_account_id="public-load-123",
        account_name="Load Test Account",
        account_type="CASH",
        buying_power=1000000.0,
        cash_balance=500000.0,
        equity=1500000.0,
        is_active=True
    )
    
    # Mock risk profile
    risk_profile = RiskProfile(
        account_id="load-test-account-123",
        max_position_size=100000.0,
        max_portfolio_risk=0.15,
        max_daily_loss=10000.0,
        max_daily_trades=500,
        allowed_strategies='["IRON_CONDOR", "BUTTERFLY_SPREAD", "CALENDAR_SPREAD"]',
        max_greeks_exposure='{"delta": 10000.0, "gamma": 1000.0}',
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
            return random.randint(0, 100)  # Mock count queries
        return query_result
    
    db.execute.side_effect = mock_execute
    return db


@pytest.fixture
def load_test_redis():
    """Create load test Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None  # No emergency stop
    redis.set.return_value = True
    redis.delete.return_value = True
    redis.ping.return_value = True
    redis.info.return_value = {
        "connected_clients": 10,
        "used_memory": 8388608,  # 8MB
        "keyspace_hits": 50000,
        "keyspace_misses": 5000
    }
    return redis


@pytest.fixture
def load_test_public_api():
    """Create load test Public.com API client."""
    api = AsyncMock()
    
    # Mock authentication
    api.authenticate.return_value = {
        "access_token": "load_access_token_123",
        "refresh_token": "load_refresh_token_456",
        "expires_in": 3600
    }
    
    # Mock account info
    api.get_account_info.return_value = {
        "account_id": "public-load-123",
        "buying_power": 1000000.0,
        "cash_balance": 500000.0,
        "equity": 1500000.0
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


class TestHighLoadTradeExecution:
    """Test trade execution under high load."""
    
    @pytest.mark.asyncio
    async def test_high_load_trade_execution(self, load_test_database, load_test_redis, load_test_public_api):
        """Test trade execution under high load."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(load_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(load_test_database, load_test_redis)
        
        trading_service = TradingService(
            db_session=load_test_database,
            public_api_client=load_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            load_test_public_api.execute_order.return_value = {
                "order_id": "load_trade_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute high load trades
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            num_trades = 100
            execution_times = []
            successful_trades = 0
            
            for i in range(num_trades):
                start_time = time.time()
                try:
                    result = await trading_service.execute_trade("load-test-account-123", trade_details)
                    end_time = time.time()
                    
                    execution_time = end_time - start_time
                    execution_times.append(execution_time)
                    
                    if result["success"]:
                        successful_trades += 1
                        
                except Exception as e:
                    print(f"Trade {i} failed: {e}")
                    end_time = time.time()
                    execution_time = end_time - start_time
                    execution_times.append(execution_time)
            
            # Performance analysis
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            min_execution_time = min(execution_times)
            p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
            
            print(f"High load trade execution performance:")
            print(f"  Total trades: {num_trades}")
            print(f"  Successful trades: {successful_trades}")
            print(f"  Success rate: {successful_trades/num_trades*100:.1f}%")
            print(f"  Average execution time: {avg_execution_time:.3f}s")
            print(f"  Max execution time: {max_execution_time:.3f}s")
            print(f"  Min execution time: {min_execution_time:.3f}s")
            print(f"  95th percentile: {p95_execution_time:.3f}s")
            
            # Performance assertions
            assert successful_trades > 0, "No trades were successful"
            assert successful_trades/num_trades > 0.8, f"Success rate {successful_trades/num_trades*100:.1f}% too low, expected > 80%"
            assert avg_execution_time < 2.0, f"Average execution time {avg_execution_time:.3f}s too high, expected < 2.0s"
            assert p95_execution_time < 5.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 5.0s"
    
    @pytest.mark.asyncio
    async def test_concurrent_high_load_trade_execution(self, load_test_database, load_test_redis, load_test_public_api):
        """Test concurrent trade execution under high load."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(load_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(load_test_database, load_test_redis)
        
        trading_service = TradingService(
            db_session=load_test_database,
            public_api_client=load_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            load_test_public_api.execute_order.return_value = {
                "order_id": "load_concurrent_trade_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute concurrent high load trades
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            num_concurrent_trades = 200
            batch_size = 20  # Process in batches to avoid overwhelming the system
            
            async def execute_trade_batch(batch_id):
                batch_results = []
                for i in range(batch_size):
                    start_time = time.time()
                    try:
                        result = await trading_service.execute_trade("load-test-account-123", trade_details)
                        end_time = time.time()
                        
                        execution_time = end_time - start_time
                        batch_results.append({
                            "success": result["success"],
                            "execution_time": execution_time,
                            "batch_id": batch_id,
                            "trade_id": i
                        })
                        
                    except Exception as e:
                        end_time = time.time()
                        execution_time = end_time - start_time
                        batch_results.append({
                            "success": False,
                            "execution_time": execution_time,
                            "batch_id": batch_id,
                            "trade_id": i,
                            "error": str(e)
                        })
                
                return batch_results
            
            # Execute trades in concurrent batches
            start_time = time.time()
            tasks = [execute_trade_batch(i) for i in range(num_concurrent_trades // batch_size)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Analyze results
            all_results = []
            for batch_result in batch_results:
                if isinstance(batch_result, Exception):
                    print(f"Batch failed: {batch_result}")
                else:
                    all_results.extend(batch_result)
            
            successful_trades = sum(1 for result in all_results if result["success"])
            execution_times = [result["execution_time"] for result in all_results]
            
            # Performance analysis
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            min_execution_time = min(execution_times)
            p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
            
            print(f"Concurrent high load trade execution performance:")
            print(f"  Total trades: {len(all_results)}")
            print(f"  Successful trades: {successful_trades}")
            print(f"  Success rate: {successful_trades/len(all_results)*100:.1f}%")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Trades per second: {len(all_results)/total_time:.1f}")
            print(f"  Average execution time: {avg_execution_time:.3f}s")
            print(f"  Max execution time: {max_execution_time:.3f}s")
            print(f"  Min execution time: {min_execution_time:.3f}s")
            print(f"  95th percentile: {p95_execution_time:.3f}s")
            
            # Performance assertions
            assert successful_trades > 0, "No trades were successful"
            assert successful_trades/len(all_results) > 0.7, f"Success rate {successful_trades/len(all_results)*100:.1f}% too low, expected > 70%"
            assert len(all_results)/total_time > 10, f"Throughput {len(all_results)/total_time:.1f} trades/sec too low, expected > 10"
            assert avg_execution_time < 3.0, f"Average execution time {avg_execution_time:.3f}s too high, expected < 3.0s"
            assert p95_execution_time < 10.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 10.0s"


class TestHighLoadRiskManagement:
    """Test risk management under high load."""
    
    @pytest.mark.asyncio
    async def test_high_load_risk_checks(self, load_test_database, load_test_redis, load_test_public_api):
        """Test risk checks under high load."""
        from src.services.live_trading.risk_service import RiskService
        
        # Create risk service
        risk_service = RiskService(load_test_database)
        
        # Test risk checks under high load
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        num_checks = 500
        execution_times = []
        successful_checks = 0
        
        for i in range(num_checks):
            start_time = time.time()
            try:
                result = await risk_service.comprehensive_risk_check("load-test-account-123", trade_details)
                end_time = time.time()
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                if result["passed"]:
                    successful_checks += 1
                    
            except Exception as e:
                print(f"Risk check {i} failed: {e}")
                end_time = time.time()
                execution_time = end_time - start_time
                execution_times.append(execution_time)
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
        
        print(f"High load risk check performance:")
        print(f"  Total checks: {num_checks}")
        print(f"  Successful checks: {successful_checks}")
        print(f"  Success rate: {successful_checks/num_checks*100:.1f}%")
        print(f"  Average execution time: {avg_execution_time:.3f}s")
        print(f"  Max execution time: {max_execution_time:.3f}s")
        print(f"  Min execution time: {min_execution_time:.3f}s")
        print(f"  95th percentile: {p95_execution_time:.3f}s")
        
        # Performance assertions
        assert successful_checks > 0, "No risk checks were successful"
        assert successful_checks/num_checks > 0.9, f"Success rate {successful_checks/num_checks*100:.1f}% too low, expected > 90%"
        assert avg_execution_time < 0.5, f"Average execution time {avg_execution_time:.3f}s too high, expected < 0.5s"
        assert p95_execution_time < 1.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 1.0s"
    
    @pytest.mark.asyncio
    async def test_concurrent_high_load_risk_checks(self, load_test_database, load_test_redis, load_test_public_api):
        """Test concurrent risk checks under high load."""
        from src.services.live_trading.risk_service import RiskService
        
        # Create risk service
        risk_service = RiskService(load_test_database)
        
        # Test concurrent risk checks under high load
        trade_details = {
            "symbol": "SPY",
            "action": TradeAction.BUY,
            "quantity": 100,
            "price": Decimal("400.00"),
            "side": "BUY"
        }
        
        num_concurrent_checks = 1000
        
        async def execute_risk_check(check_id):
            start_time = time.time()
            try:
                result = await risk_service.comprehensive_risk_check("load-test-account-123", trade_details)
                end_time = time.time()
                
                execution_time = end_time - start_time
                return {
                    "success": result["passed"],
                    "execution_time": execution_time,
                    "check_id": check_id
                }
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                return {
                    "success": False,
                    "execution_time": execution_time,
                    "check_id": check_id,
                    "error": str(e)
                }
        
        # Execute concurrent risk checks
        start_time = time.time()
        tasks = [execute_risk_check(i) for i in range(num_concurrent_checks)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Analyze results
        successful_checks = sum(1 for result in results if isinstance(result, dict) and result["success"])
        execution_times = [result["execution_time"] for result in results if isinstance(result, dict)]
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
        
        print(f"Concurrent high load risk check performance:")
        print(f"  Total checks: {len(results)}")
        print(f"  Successful checks: {successful_checks}")
        print(f"  Success rate: {successful_checks/len(results)*100:.1f}%")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Checks per second: {len(results)/total_time:.1f}")
        print(f"  Average execution time: {avg_execution_time:.3f}s")
        print(f"  Max execution time: {max_execution_time:.3f}s")
        print(f"  Min execution time: {min_execution_time:.3f}s")
        print(f"  95th percentile: {p95_execution_time:.3f}s")
        
        # Performance assertions
        assert successful_checks > 0, "No risk checks were successful"
        assert successful_checks/len(results) > 0.8, f"Success rate {successful_checks/len(results)*100:.1f}% too low, expected > 80%"
        assert len(results)/total_time > 50, f"Throughput {len(results)/total_time:.1f} checks/sec too low, expected > 50"
        assert avg_execution_time < 1.0, f"Average execution time {avg_execution_time:.3f}s too high, expected < 1.0s"
        assert p95_execution_time < 2.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 2.0s"


class TestHighLoadPositionManagement:
    """Test position management under high load."""
    
    @pytest.mark.asyncio
    async def test_high_load_position_updates(self, load_test_database, load_test_redis, load_test_public_api):
        """Test position updates under high load."""
        from src.services.live_trading.position_service import PositionService
        
        # Create position service
        position_service = PositionService(load_test_database)
        
        # Test position updates under high load
        update_data = {
            "quantity": 50,
            "price": Decimal("410.00")
        }
        
        num_updates = 300
        execution_times = []
        successful_updates = 0
        
        for i in range(num_updates):
            start_time = time.time()
            try:
                result = await position_service.update_position_quantity("load-test-account-123", "SPY", update_data)
                end_time = time.time()
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                if result["quantity"] == 50:
                    successful_updates += 1
                    
            except Exception as e:
                print(f"Position update {i} failed: {e}")
                end_time = time.time()
                execution_time = end_time - start_time
                execution_times.append(execution_time)
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
        
        print(f"High load position update performance:")
        print(f"  Total updates: {num_updates}")
        print(f"  Successful updates: {successful_updates}")
        print(f"  Success rate: {successful_updates/num_updates*100:.1f}%")
        print(f"  Average execution time: {avg_execution_time:.3f}s")
        print(f"  Max execution time: {max_execution_time:.3f}s")
        print(f"  Min execution time: {min_execution_time:.3f}s")
        print(f"  95th percentile: {p95_execution_time:.3f}s")
        
        # Performance assertions
        assert successful_updates > 0, "No position updates were successful"
        assert successful_updates/num_updates > 0.8, f"Success rate {successful_updates/num_updates*100:.1f}% too low, expected > 80%"
        assert avg_execution_time < 0.3, f"Average execution time {avg_execution_time:.3f}s too high, expected < 0.3s"
        assert p95_execution_time < 1.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 1.0s"
    
    @pytest.mark.asyncio
    async def test_concurrent_high_load_position_updates(self, load_test_database, load_test_redis, load_test_public_api):
        """Test concurrent position updates under high load."""
        from src.services.live_trading.position_service import PositionService
        
        # Create position service
        position_service = PositionService(load_test_database)
        
        # Test concurrent position updates under high load
        update_data = {
            "quantity": 50,
            "price": Decimal("410.00")
        }
        
        num_concurrent_updates = 500
        
        async def execute_position_update(update_id):
            start_time = time.time()
            try:
                result = await position_service.update_position_quantity("load-test-account-123", "SPY", update_data)
                end_time = time.time()
                
                execution_time = end_time - start_time
                return {
                    "success": result["quantity"] == 50,
                    "execution_time": execution_time,
                    "update_id": update_id
                }
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                return {
                    "success": False,
                    "execution_time": execution_time,
                    "update_id": update_id,
                    "error": str(e)
                }
        
        # Execute concurrent position updates
        start_time = time.time()
        tasks = [execute_position_update(i) for i in range(num_concurrent_updates)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Analyze results
        successful_updates = sum(1 for result in results if isinstance(result, dict) and result["success"])
        execution_times = [result["execution_time"] for result in results if isinstance(result, dict)]
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
        
        print(f"Concurrent high load position update performance:")
        print(f"  Total updates: {len(results)}")
        print(f"  Successful updates: {successful_updates}")
        print(f"  Success rate: {successful_updates/len(results)*100:.1f}%")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Updates per second: {len(results)/total_time:.1f}")
        print(f"  Average execution time: {avg_execution_time:.3f}s")
        print(f"  Max execution time: {max_execution_time:.3f}s")
        print(f"  Min execution time: {min_execution_time:.3f}s")
        print(f"  95th percentile: {p95_execution_time:.3f}s")
        
        # Performance assertions
        assert successful_updates > 0, "No position updates were successful"
        assert successful_updates/len(results) > 0.7, f"Success rate {successful_updates/len(results)*100:.1f}% too low, expected > 70%"
        assert len(results)/total_time > 100, f"Throughput {len(results)/total_time:.1f} updates/sec too low, expected > 100"
        assert avg_execution_time < 0.5, f"Average execution time {avg_execution_time:.3f}s too high, expected < 0.5s"
        assert p95_execution_time < 1.5, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 1.5s"


class TestHighLoadSystemOperations:
    """Test system operations under high load."""
    
    @pytest.mark.asyncio
    async def test_high_load_health_checks(self, load_test_database, load_test_redis, load_test_public_api):
        """Test health checks under high load."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(load_test_database, load_test_redis)
        
        # Test health checks under high load
        num_checks = 200
        execution_times = []
        successful_checks = 0
        
        for i in range(num_checks):
            start_time = time.time()
            try:
                result = await system_service.perform_health_check()
                end_time = time.time()
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                if result["overall_status"] in ["healthy", "degraded", "critical"]:
                    successful_checks += 1
                    
            except Exception as e:
                print(f"Health check {i} failed: {e}")
                end_time = time.time()
                execution_time = end_time - start_time
                execution_times.append(execution_time)
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
        
        print(f"High load health check performance:")
        print(f"  Total checks: {num_checks}")
        print(f"  Successful checks: {successful_checks}")
        print(f"  Success rate: {successful_checks/num_checks*100:.1f}%")
        print(f"  Average execution time: {avg_execution_time:.3f}s")
        print(f"  Max execution time: {max_execution_time:.3f}s")
        print(f"  Min execution time: {min_execution_time:.3f}s")
        print(f"  95th percentile: {p95_execution_time:.3f}s")
        
        # Performance assertions
        assert successful_checks > 0, "No health checks were successful"
        assert successful_checks/num_checks > 0.9, f"Success rate {successful_checks/num_checks*100:.1f}% too low, expected > 90%"
        assert avg_execution_time < 0.5, f"Average execution time {avg_execution_time:.3f}s too high, expected < 0.5s"
        assert p95_execution_time < 1.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 1.0s"
    
    @pytest.mark.asyncio
    async def test_concurrent_high_load_health_checks(self, load_test_database, load_test_redis, load_test_public_api):
        """Test concurrent health checks under high load."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(load_test_database, load_test_redis)
        
        # Test concurrent health checks under high load
        num_concurrent_checks = 300
        
        async def execute_health_check(check_id):
            start_time = time.time()
            try:
                result = await system_service.perform_health_check()
                end_time = time.time()
                
                execution_time = end_time - start_time
                return {
                    "success": result["overall_status"] in ["healthy", "degraded", "critical"],
                    "execution_time": execution_time,
                    "check_id": check_id
                }
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                return {
                    "success": False,
                    "execution_time": execution_time,
                    "check_id": check_id,
                    "error": str(e)
                }
        
        # Execute concurrent health checks
        start_time = time.time()
        tasks = [execute_health_check(i) for i in range(num_concurrent_checks)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Analyze results
        successful_checks = sum(1 for result in results if isinstance(result, dict) and result["success"])
        execution_times = [result["execution_time"] for result in results if isinstance(result, dict)]
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
        
        print(f"Concurrent high load health check performance:")
        print(f"  Total checks: {len(results)}")
        print(f"  Successful checks: {successful_checks}")
        print(f"  Success rate: {successful_checks/len(results)*100:.1f}%")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Checks per second: {len(results)/total_time:.1f}")
        print(f"  Average execution time: {avg_execution_time:.3f}s")
        print(f"  Max execution time: {max_execution_time:.3f}s")
        print(f"  Min execution time: {min_execution_time:.3f}s")
        print(f"  95th percentile: {p95_execution_time:.3f}s")
        
        # Performance assertions
        assert successful_checks > 0, "No health checks were successful"
        assert successful_checks/len(results) > 0.8, f"Success rate {successful_checks/len(results)*100:.1f}% too low, expected > 80%"
        assert len(results)/total_time > 30, f"Throughput {len(results)/total_time:.1f} checks/sec too low, expected > 30"
        assert avg_execution_time < 1.0, f"Average execution time {avg_execution_time:.3f}s too high, expected < 1.0s"
        assert p95_execution_time < 2.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 2.0s"


class TestStressTesting:
    """Test system behavior under extreme stress conditions."""
    
    @pytest.mark.asyncio
    async def test_extreme_load_trade_execution(self, load_test_database, load_test_redis, load_test_public_api):
        """Test trade execution under extreme load."""
        from src.services.live_trading.trading_service import TradingService
        from src.services.live_trading.risk_service import RiskService
        from src.services.live_trading.position_service import PositionService
        from src.services.live_trading.system_service import SystemService
        from src.services.live_trading.market_hours_service import MarketHoursService
        
        # Create services
        risk_service = RiskService(load_test_database)
        market_hours_service = MarketHoursService()
        system_service = SystemService(load_test_database, load_test_redis)
        
        trading_service = TradingService(
            db_session=load_test_database,
            public_api_client=load_test_public_api,
            risk_service=risk_service,
            market_hours_service=market_hours_service,
            system_service=system_service
        )
        
        # Mock market hours
        with patch.object(market_hours_service, 'is_market_open', return_value=True):
            # Mock successful order execution
            load_test_public_api.execute_order.return_value = {
                "order_id": "stress_trade_123",
                "status": "FILLED",
                "filled_quantity": 100,
                "average_price": 400.25
            }
            
            # Execute extreme load trades
            trade_details = {
                "symbol": "SPY",
                "action": TradeAction.BUY,
                "quantity": 100,
                "price": Decimal("400.25"),
                "order_type": "MARKET",
                "strategy": StrategyType.IRON_CONDOR
            }
            
            num_trades = 1000
            batch_size = 50  # Process in smaller batches to avoid overwhelming the system
            
            async def execute_trade_batch(batch_id):
                batch_results = []
                for i in range(batch_size):
                    start_time = time.time()
                    try:
                        result = await trading_service.execute_trade("load-test-account-123", trade_details)
                        end_time = time.time()
                        
                        execution_time = end_time - start_time
                        batch_results.append({
                            "success": result["success"],
                            "execution_time": execution_time,
                            "batch_id": batch_id,
                            "trade_id": i
                        })
                        
                    except Exception as e:
                        end_time = time.time()
                        execution_time = end_time - start_time
                        batch_results.append({
                            "success": False,
                            "execution_time": execution_time,
                            "batch_id": batch_id,
                            "trade_id": i,
                            "error": str(e)
                        })
                
                return batch_results
            
            # Execute trades in extreme load batches
            start_time = time.time()
            tasks = [execute_trade_batch(i) for i in range(num_trades // batch_size)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Analyze results
            all_results = []
            for batch_result in batch_results:
                if isinstance(batch_result, Exception):
                    print(f"Batch failed: {batch_result}")
                else:
                    all_results.extend(batch_result)
            
            successful_trades = sum(1 for result in all_results if result["success"])
            execution_times = [result["execution_time"] for result in all_results]
            
            # Performance analysis
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            min_execution_time = min(execution_times)
            p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
            
            print(f"Extreme load trade execution performance:")
            print(f"  Total trades: {len(all_results)}")
            print(f"  Successful trades: {successful_trades}")
            print(f"  Success rate: {successful_trades/len(all_results)*100:.1f}%")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Trades per second: {len(all_results)/total_time:.1f}")
            print(f"  Average execution time: {avg_execution_time:.3f}s")
            print(f"  Max execution time: {max_execution_time:.3f}s")
            print(f"  Min execution time: {min_execution_time:.3f}s")
            print(f"  95th percentile: {p95_execution_time:.3f}s")
            
            # Performance assertions
            assert successful_trades > 0, "No trades were successful"
            assert successful_trades/len(all_results) > 0.5, f"Success rate {successful_trades/len(all_results)*100:.1f}% too low, expected > 50%"
            assert len(all_results)/total_time > 5, f"Throughput {len(all_results)/total_time:.1f} trades/sec too low, expected > 5"
            assert avg_execution_time < 5.0, f"Average execution time {avg_execution_time:.3f}s too high, expected < 5.0s"
            assert p95_execution_time < 15.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 15.0s"
    
    @pytest.mark.asyncio
    async def test_system_recovery_under_load(self, load_test_database, load_test_redis, load_test_public_api):
        """Test system recovery under load."""
        from src.services.live_trading.system_service import SystemService
        
        # Create system service
        system_service = SystemService(load_test_database, load_test_redis)
        
        # Test system recovery under load
        num_operations = 100
        
        async def execute_system_operation(operation_id):
            start_time = time.time()
            try:
                # Simulate system operation (health check)
                result = await system_service.perform_health_check()
                end_time = time.time()
                
                execution_time = end_time - start_time
                return {
                    "success": result["overall_status"] in ["healthy", "degraded", "critical"],
                    "execution_time": execution_time,
                    "operation_id": operation_id
                }
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                return {
                    "success": False,
                    "execution_time": execution_time,
                    "operation_id": operation_id,
                    "error": str(e)
                }
        
        # Execute system operations under load
        start_time = time.time()
        tasks = [execute_system_operation(i) for i in range(num_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Analyze results
        successful_operations = sum(1 for result in results if isinstance(result, dict) and result["success"])
        execution_times = [result["execution_time"] for result in results if isinstance(result, dict)]
        
        # Performance analysis
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        p95_execution_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile
        
        print(f"System recovery under load performance:")
        print(f"  Total operations: {len(results)}")
        print(f"  Successful operations: {successful_operations}")
        print(f"  Success rate: {successful_operations/len(results)*100:.1f}%")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Operations per second: {len(results)/total_time:.1f}")
        print(f"  Average execution time: {avg_execution_time:.3f}s")
        print(f"  Max execution time: {max_execution_time:.3f}s")
        print(f"  Min execution time: {min_execution_time:.3f}s")
        print(f"  95th percentile: {p95_execution_time:.3f}s")
        
        # Performance assertions
        assert successful_operations > 0, "No operations were successful"
        assert successful_operations/len(results) > 0.8, f"Success rate {successful_operations/len(results)*100:.1f}% too low, expected > 80%"
        assert len(results)/total_time > 20, f"Throughput {len(results)/total_time:.1f} operations/sec too low, expected > 20"
        assert avg_execution_time < 2.0, f"Average execution time {avg_execution_time:.3f}s too high, expected < 2.0s"
        assert p95_execution_time < 5.0, f"95th percentile execution time {p95_execution_time:.3f}s too high, expected < 5.0s"
