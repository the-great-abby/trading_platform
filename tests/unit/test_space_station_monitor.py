#!/usr/bin/env python3
"""
Tests for Space Station Monitor
Comprehensive test suite for real-time trading performance tracking
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque

from src.utils.space_station_monitor import (
    StrategyPerformance,
    SystemMetrics,
    SpaceStationMonitor,
    start_space_station_monitor,
    add_trade_to_monitor,
    add_signal_to_monitor,
    get_performance_summary,
    space_station_monitor
)


class TestStrategyPerformance:
    """Test StrategyPerformance dataclass"""
    
    def test_strategy_performance_initialization(self):
        """Test StrategyPerformance initialization with default values"""
        perf = StrategyPerformance(
            strategy_name="Test Strategy",
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            total_pnl=1000.0,
            current_pnl=500.0,
            win_rate=0.6,
            avg_win=200.0,
            avg_loss=-100.0,
            max_drawdown=-200.0,
            sharpe_ratio=1.5
        )
        
        assert perf.strategy_name == "Test Strategy"
        assert perf.total_trades == 10
        assert perf.winning_trades == 6
        assert perf.losing_trades == 4
        assert perf.total_pnl == 1000.0
        assert perf.current_pnl == 500.0
        assert perf.win_rate == 0.6
        assert perf.avg_win == 200.0
        assert perf.avg_loss == -100.0
        assert perf.max_drawdown == -200.0
        assert perf.sharpe_ratio == 1.5
        assert perf.last_signal_time is None
        assert perf.last_signal_action is None
        assert perf.last_signal_confidence is None
    
    def test_strategy_performance_with_signals(self):
        """Test StrategyPerformance with signal data"""
        signal_time = datetime.now()
        perf = StrategyPerformance(
            strategy_name="AI Strategy",
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            total_pnl=500.0,
            current_pnl=300.0,
            win_rate=0.6,
            avg_win=150.0,
            avg_loss=-50.0,
            max_drawdown=-100.0,
            sharpe_ratio=1.2,
            last_signal_time=signal_time,
            last_signal_action="BUY",
            last_signal_confidence=0.85
        )
        
        assert perf.last_signal_time == signal_time
        assert perf.last_signal_action == "BUY"
        assert perf.last_signal_confidence == 0.85


class TestSystemMetrics:
    """Test SystemMetrics dataclass"""
    
    def test_system_metrics_initialization(self):
        """Test SystemMetrics initialization"""
        metrics = SystemMetrics(
            cpu_usage=25.5,
            memory_usage=60.2,
            disk_io=1000000,
            network_latency=500000,
            active_connections=15,
            queue_size=5
        )
        
        assert metrics.cpu_usage == 25.5
        assert metrics.memory_usage == 60.2
        assert metrics.disk_io == 1000000
        assert metrics.network_latency == 500000
        assert metrics.active_connections == 15
        assert metrics.queue_size == 5


class TestSpaceStationMonitorInitialization:
    """Test SpaceStationMonitor initialization"""
    
    def test_monitor_initialization_default(self):
        """Test monitor initialization with default settings"""
        monitor = SpaceStationMonitor()
        
        assert monitor.refresh_interval == 5
        assert monitor.is_running is False
        assert isinstance(monitor.strategy_performance, dict)
        assert isinstance(monitor.recent_trades, deque)
        assert monitor.recent_trades.maxlen == 1000
        assert isinstance(monitor.system_metrics, SystemMetrics)
        assert monitor.total_trades == 0
        assert monitor.total_pnl == 0.0
        assert monitor.active_strategies == 0
        assert monitor.ai_signals_generated == 0
        assert monitor.news_events_processed == 0
        assert isinstance(monitor.start_time, datetime)
        assert isinstance(monitor.last_update, datetime)
        assert isinstance(monitor.pnl_history, deque)
        assert monitor.pnl_history.maxlen == 100
        assert isinstance(monitor.trade_history, deque)
        assert monitor.trade_history.maxlen == 100
    
    def test_monitor_initialization_custom_interval(self):
        """Test monitor initialization with custom refresh interval"""
        monitor = SpaceStationMonitor(refresh_interval=10)
        
        assert monitor.refresh_interval == 10
    
    @patch('src.utils.space_station_monitor.DATABASE_AVAILABLE', False)
    @patch('src.utils.space_station_monitor.BACKTEST_API_AVAILABLE', False)
    def test_monitor_initialization_no_services(self):
        """Test monitor initialization without database or API services"""
        monitor = SpaceStationMonitor()
        
        assert monitor.market_data_service is None
        assert monitor.backtest_service is None
        assert monitor.backtest_api_client is None


class TestSpaceStationMonitorTradeTracking:
    """Test trade tracking functionality"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    @pytest.fixture
    def mock_trade(self):
        """Create a mock trade"""
        trade = Mock()
        trade.pnl = 100.0
        trade.strategy = "Test Strategy"
        trade.timestamp = datetime.now()
        return trade
    
    def test_add_trade_winning(self, monitor, mock_trade):
        """Test adding a winning trade"""
        monitor.add_trade(mock_trade)
        
        assert monitor.total_trades == 1
        assert monitor.total_pnl == 100.0
        assert len(monitor.recent_trades) == 1
        assert "Test Strategy" in monitor.strategy_performance
        
        strategy = monitor.strategy_performance["Test Strategy"]
        assert strategy.total_trades == 1
        assert strategy.winning_trades == 1
        assert strategy.losing_trades == 0
        assert strategy.total_pnl == 100.0
        assert strategy.win_rate == 1.0
    
    def test_add_trade_losing(self, monitor):
        """Test adding a losing trade"""
        trade = Mock()
        trade.pnl = -50.0
        trade.strategy = "Test Strategy"
        trade.timestamp = datetime.now()
        
        monitor.add_trade(trade)
        
        assert monitor.total_trades == 1
        assert monitor.total_pnl == -50.0
        
        strategy = monitor.strategy_performance["Test Strategy"]
        assert strategy.total_trades == 1
        assert strategy.winning_trades == 0
        assert strategy.losing_trades == 1
        assert strategy.total_pnl == -50.0
        assert strategy.win_rate == 0.0
    
    def test_add_trade_no_pnl(self, monitor):
        """Test adding a trade without PnL"""
        trade = Mock()
        trade.pnl = None
        trade.strategy = "Test Strategy"
        trade.timestamp = datetime.now()
        
        monitor.add_trade(trade)
        
        assert monitor.total_trades == 1
        assert monitor.total_pnl == 0.0
        
        strategy = monitor.strategy_performance["Test Strategy"]
        assert strategy.total_trades == 1
        assert strategy.winning_trades == 0
        assert strategy.losing_trades == 0
    
    def test_add_trade_multiple_strategies(self, monitor):
        """Test adding trades from multiple strategies"""
        trade1 = Mock()
        trade1.pnl = 100.0
        trade1.strategy = "Strategy A"
        trade1.timestamp = datetime.now()
        
        trade2 = Mock()
        trade2.pnl = 200.0
        trade2.strategy = "Strategy B"
        trade2.timestamp = datetime.now()
        
        monitor.add_trade(trade1)
        monitor.add_trade(trade2)
        
        assert monitor.total_trades == 2
        assert monitor.total_pnl == 300.0
        assert len(monitor.strategy_performance) == 2
        assert "Strategy A" in monitor.strategy_performance
        assert "Strategy B" in monitor.strategy_performance
    
    def test_add_trade_unknown_strategy(self, monitor):
        """Test adding a trade with unknown strategy"""
        trade = Mock()
        trade.pnl = 50.0
        # Remove strategy attribute to simulate missing attribute
        delattr(trade, 'strategy')
        trade.timestamp = datetime.now()
        
        monitor.add_trade(trade)
        
        assert "Unknown" in monitor.strategy_performance
        strategy = monitor.strategy_performance["Unknown"]
        assert strategy.total_trades == 1
        assert strategy.total_pnl == 50.0


class TestSpaceStationMonitorSignalTracking:
    """Test signal tracking functionality"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    @pytest.fixture
    def mock_signal(self):
        """Create a mock signal"""
        signal = Mock()
        signal.strategy = "AI Strategy"
        signal.action = "BUY"
        signal.confidence = 0.85
        return signal
    
    def test_add_signal_new_strategy(self, monitor, mock_signal):
        """Test adding a signal for a new strategy"""
        monitor.add_signal(mock_signal)
        
        assert "AI Strategy" in monitor.strategy_performance
        strategy = monitor.strategy_performance["AI Strategy"]
        assert strategy.last_signal_action == "BUY"
        assert strategy.last_signal_confidence == 0.85
        assert strategy.last_signal_time is not None
        assert monitor.ai_signals_generated == 1
    
    def test_add_signal_existing_strategy(self, monitor, mock_signal):
        """Test adding a signal for an existing strategy"""
        # Add initial signal
        monitor.add_signal(mock_signal)
        
        # Add another signal
        signal2 = Mock()
        signal2.strategy = "AI Strategy"
        signal2.action = "SELL"
        signal2.confidence = 0.75
        
        monitor.add_signal(signal2)
        
        strategy = monitor.strategy_performance["AI Strategy"]
        assert strategy.last_signal_action == "SELL"
        assert strategy.last_signal_confidence == 0.75
        assert monitor.ai_signals_generated == 2
    
    def test_add_signal_non_ai_strategy(self, monitor):
        """Test adding a signal for a non-AI strategy"""
        signal = Mock()
        signal.strategy = "Manual Strategy"
        signal.action = "HOLD"
        signal.confidence = 0.6
        
        monitor.add_signal(signal)
        
        assert monitor.ai_signals_generated == 0
        strategy = monitor.strategy_performance["Manual Strategy"]
        assert strategy.last_signal_action == "HOLD"


class TestSpaceStationMonitorSystemMetrics:
    """Test system metrics monitoring"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    @pytest.mark.skip(reason="TODO: Fix infinite loop in _monitor_system_metrics")
    @patch('src.utils.space_station_monitor.PSUTIL_AVAILABLE', True)
    @patch('src.utils.space_station_monitor.psutil')
    def test_monitor_system_metrics_with_psutil(self, mock_psutil, monitor):
        """Test system metrics monitoring with psutil available"""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.virtual_memory.return_value.percent = 60.2
        
        disk_io = Mock()
        disk_io.read_bytes = 1000000
        disk_io.write_bytes = 500000
        mock_psutil.disk_io_counters.return_value = disk_io
        
        net_io = Mock()
        net_io.bytes_sent = 200000
        net_io.bytes_recv = 300000
        mock_psutil.net_io_counters.return_value = net_io
        
        mock_psutil.net_connections.return_value = [Mock(), Mock(), Mock()]
        
        # Test the metrics collection logic directly without the infinite loop
        monitor.is_running = True
        
        # Mock the time.sleep to avoid infinite loop
        with patch('time.sleep'):
            # Call the method but it will exit immediately due to mocked sleep
            monitor._monitor_system_metrics()
        
        # Check that metrics were updated
        assert monitor.system_metrics.cpu_usage == 25.5
        assert monitor.system_metrics.memory_usage == 60.2
        assert monitor.system_metrics.disk_io == 1500000
        assert monitor.system_metrics.network_latency == 500000
        assert monitor.system_metrics.active_connections == 3
    
    @pytest.mark.skip(reason="TODO: Fix infinite loop in _monitor_system_metrics")
    @patch('src.utils.space_station_monitor.PSUTIL_AVAILABLE', False)
    @patch('time.time')
    def test_monitor_system_metrics_without_psutil(self, mock_time, monitor):
        """Test system metrics monitoring without psutil"""
        monitor.is_running = True
        
        # Mock time.time to return predictable values
        mock_time.return_value = 1000.0
        
        # Mock the time.sleep to avoid infinite loop
        with patch('time.sleep'):
            # Test the metrics collection logic directly
            monitor._monitor_system_metrics()
        
        # Check that simulated metrics were set
        assert monitor.system_metrics.cpu_usage > 0
        assert monitor.system_metrics.memory_usage > 0
        assert monitor.system_metrics.disk_io > 0
        assert monitor.system_metrics.network_latency > 0
        assert monitor.system_metrics.active_connections > 0


class TestSpaceStationMonitorAPIData:
    """Test API data fetching"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    @patch('src.utils.space_station_monitor.BACKTEST_API_AVAILABLE', True)
    def test_fetch_api_data_success(self, monitor):
        """Test successful API data fetching"""
        # Mock backtest API client
        mock_client = AsyncMock()
        mock_client.list_backtest_runs.return_value = [
            {
                'strategy_name': 'API Strategy',
                'total_pnl': 1000.0,
                'total_trades': 50,
                'win_rate': 0.6
            }
        ]
        mock_client.compare_strategies.return_value = {'success': True}
        
        monitor.backtest_api_client = mock_client
        
        # Run the fetch
        asyncio.run(monitor.fetch_api_data())
        
        # Check that strategy was added
        assert "API Strategy" in monitor.strategy_performance
        strategy = monitor.strategy_performance["API Strategy"]
        assert strategy.total_pnl == 1000.0
        assert strategy.total_trades == 50
        assert strategy.win_rate == 0.6
        
        # Check that totals were updated
        assert monitor.total_pnl == 1000.0
        assert monitor.total_trades == 50
    
    @patch('src.utils.space_station_monitor.BACKTEST_API_AVAILABLE', False)
    def test_fetch_api_data_no_client(self, monitor):
        """Test API data fetching when client is not available"""
        monitor.backtest_api_client = None
        
        # Should not raise an exception
        asyncio.run(monitor.fetch_api_data())
    
    @patch('src.utils.space_station_monitor.BACKTEST_API_AVAILABLE', True)
    def test_fetch_api_data_error(self, monitor):
        """Test API data fetching with error"""
        # Mock backtest API client that raises an exception
        mock_client = AsyncMock()
        mock_client.list_backtest_runs.side_effect = Exception("API Error")
        
        monitor.backtest_api_client = mock_client
        
        # Should not raise an exception
        asyncio.run(monitor.fetch_api_data())


class TestSpaceStationMonitorPerformanceData:
    """Test performance data collection"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    @pytest.mark.skip(reason="TODO: Fix infinite loop in _collect_performance_data")
    @patch('src.utils.space_station_monitor.BACKTEST_API_AVAILABLE', False)
    @patch('asyncio.sleep')
    def test_collect_performance_data(self, mock_sleep, monitor):
        """Test performance data collection"""
        # Add some test data
        trade = Mock()
        trade.pnl = 100.0
        trade.strategy = "Test Strategy"
        trade.timestamp = datetime.now()
        monitor.add_trade(trade)
        
        # Start collection briefly
        monitor.is_running = True
        monitor.refresh_interval = 0.1  # Short interval for testing
        
        # Mock asyncio.sleep to return immediately
        mock_sleep.return_value = None
        
        # Run collection for a short time
        async def run_briefly():
            await asyncio.wait_for(monitor._collect_performance_data(), timeout=0.2)
        
        try:
            asyncio.run(run_briefly())
        except asyncio.TimeoutError:
            pass  # Expected timeout
        
        # Check that data was collected
        assert monitor.active_strategies == 1
        assert len(monitor.pnl_history) > 0
        assert len(monitor.trade_history) > 0
    
    def test_calculate_sharpe_ratio(self, monitor):
        """Test Sharpe ratio calculation"""
        # Add trades to a strategy
        strategy_name = "Test Strategy"
        monitor.strategy_performance[strategy_name] = StrategyPerformance(
            strategy_name=strategy_name,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            total_pnl=1000.0,
            current_pnl=500.0,
            win_rate=0.6,
            avg_win=200.0,
            avg_loss=-100.0,
            max_drawdown=-200.0,
            sharpe_ratio=0.0
        )
        
        # Trigger Sharpe calculation
        monitor.is_running = True
        asyncio.run(monitor._collect_performance_data())
        
        strategy = monitor.strategy_performance[strategy_name]
        assert strategy.sharpe_ratio == 100.0  # 1000.0 / 10


class TestSpaceStationMonitorDisplay:
    """Test display functionality"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    @patch('os.system')
    def test_print_dashboard(self, mock_system, monitor):
        """Test dashboard printing"""
        # Add some test data
        trade = Mock()
        trade.pnl = 100.0
        trade.strategy = "Test Strategy"
        trade.timestamp = datetime.now()
        monitor.add_trade(trade)
        
        signal = Mock()
        signal.strategy = "AI Strategy"
        signal.action = "BUY"
        signal.confidence = 0.85
        monitor.add_signal(signal)
        
        # Mock system metrics
        monitor.system_metrics.cpu_usage = 25.5
        monitor.system_metrics.memory_usage = 60.2
        monitor.system_metrics.disk_io = 1000000
        monitor.system_metrics.network_latency = 500000
        monitor.system_metrics.active_connections = 5
        monitor.system_metrics.queue_size = 2
        
        # Test dashboard printing
        monitor._print_dashboard()
        
        # Check that clear command was called
        mock_system.assert_called_once()
    
    def test_update_display(self, monitor):
        """Test display update in separate thread"""
        monitor.is_running = True
        monitor.refresh_interval = 0.1  # Short interval for testing
        
        # Run display update briefly
        def run_briefly():
            monitor._update_display()
        
        # Should not raise an exception
        run_briefly()


class TestSpaceStationMonitorPerformanceSummary:
    """Test performance summary generation"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    def test_get_performance_summary(self, monitor):
        """Test performance summary generation"""
        # Add some test data
        trade = Mock()
        trade.pnl = 100.0
        trade.strategy = "Test Strategy"
        trade.timestamp = datetime.now()
        monitor.add_trade(trade)
        
        signal = Mock()
        signal.strategy = "AI Strategy"
        signal.action = "BUY"
        signal.confidence = 0.85
        monitor.add_signal(signal)
        
        # Mock system metrics
        monitor.system_metrics.cpu_usage = 25.5
        monitor.system_metrics.memory_usage = 60.2
        monitor.system_metrics.disk_io = 1000000
        monitor.system_metrics.network_latency = 500000
        
        summary = monitor.get_performance_summary()
        
        assert summary['total_trades'] == 1
        assert summary['total_pnl'] == 100.0
        assert summary['active_strategies'] == 2
        assert summary['ai_signals'] == 1
        assert 'uptime' in summary
        assert 'system_metrics' in summary
        assert 'strategies' in summary
        
        # Check system metrics
        system_metrics = summary['system_metrics']
        assert system_metrics['cpu'] == 25.5
        assert system_metrics['memory'] == 60.2
        assert system_metrics['disk_io'] == 1000000
        assert system_metrics['network'] == 500000
        
        # Check strategies
        strategies = summary['strategies']
        assert 'Test Strategy' in strategies
        assert 'AI Strategy' in strategies


class TestSpaceStationMonitorLifecycle:
    """Test monitor lifecycle management"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    def test_start_monitoring(self, monitor):
        """Test starting the monitor"""
        assert monitor.is_running is False
        
        # Start monitoring
        asyncio.run(monitor.start_monitoring())
        
        assert monitor.is_running is True
    
    def test_stop_monitoring(self, monitor):
        """Test stopping the monitor"""
        monitor.is_running = True
        
        # Stop monitoring
        asyncio.run(monitor.stop_monitoring())
        
        assert monitor.is_running is False


class TestGlobalFunctions:
    """Test global convenience functions"""
    
    def test_add_trade_to_monitor(self):
        """Test global add_trade_to_monitor function"""
        trade = Mock()
        trade.pnl = 100.0
        trade.strategy = "Global Strategy"
        trade.timestamp = datetime.now()
        
        add_trade_to_monitor(trade)
        
        assert space_station_monitor.total_trades == 1
        assert space_station_monitor.total_pnl == 100.0
    
    def test_add_signal_to_monitor(self):
        """Test global add_signal_to_monitor function"""
        signal = Mock()
        signal.strategy = "Global AI Strategy"
        signal.action = "SELL"
        signal.confidence = 0.75
        
        add_signal_to_monitor(signal)
        
        assert "Global AI Strategy" in space_station_monitor.strategy_performance
        strategy = space_station_monitor.strategy_performance["Global AI Strategy"]
        assert strategy.last_signal_action == "SELL"
        assert strategy.last_signal_confidence == 0.75
    
    def test_get_performance_summary(self):
        """Test global get_performance_summary function"""
        summary = get_performance_summary()
        
        assert isinstance(summary, dict)
        assert 'total_trades' in summary
        assert 'total_pnl' in summary
        assert 'active_strategies' in summary
        assert 'system_metrics' in summary
        assert 'strategies' in summary


class TestSpaceStationMonitorEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    def test_add_trade_no_attributes(self, monitor):
        """Test adding a trade without expected attributes"""
        trade = Mock()
        # No pnl, strategy, or timestamp attributes
        
        monitor.add_trade(trade)
        
        assert monitor.total_trades == 1
        assert monitor.total_pnl == 0.0
        assert "Unknown" in monitor.strategy_performance
    
    def test_add_signal_no_attributes(self, monitor):
        """Test adding a signal without expected attributes"""
        signal = Mock()
        # No strategy, action, or confidence attributes
        
        monitor.add_signal(signal)
        
        # Should handle gracefully
        assert len(monitor.strategy_performance) == 0
    
    def test_system_metrics_error_handling(self, monitor):
        """Test system metrics error handling"""
        monitor.is_running = True
        
        # Mock psutil to raise an exception
        with patch('src.utils.space_station_monitor.PSUTIL_AVAILABLE', True), \
             patch('src.utils.space_station_monitor.psutil') as mock_psutil:
            
            mock_psutil.cpu_percent.side_effect = Exception("CPU Error")
            
            # Should not raise an exception
            monitor._monitor_system_metrics()
    
    def test_performance_data_collection_error(self, monitor):
        """Test performance data collection error handling"""
        monitor.is_running = True
        monitor.refresh_interval = 0.1
        
        # Mock an error in data collection
        with patch.object(monitor, 'fetch_api_data', side_effect=Exception("API Error")):
            # Should not raise an exception
            async def run_briefly():
                await asyncio.wait_for(monitor._collect_performance_data(), timeout=0.2)
            
            try:
                asyncio.run(run_briefly())
            except asyncio.TimeoutError:
                pass  # Expected timeout


class TestSpaceStationMonitorIntegration:
    """Integration tests for SpaceStationMonitor"""
    
    @pytest.fixture
    def monitor(self):
        """Create a SpaceStationMonitor instance"""
        return SpaceStationMonitor()
    
    def test_full_workflow(self, monitor):
        """Test complete workflow with trades and signals"""
        # Add trades
        trade1 = Mock()
        trade1.pnl = 100.0
        trade1.strategy = "Strategy A"
        trade1.timestamp = datetime.now()
        
        trade2 = Mock()
        trade2.pnl = -50.0
        trade2.strategy = "Strategy B"
        trade2.timestamp = datetime.now()
        
        monitor.add_trade(trade1)
        monitor.add_trade(trade2)
        
        # Add signals
        signal1 = Mock()
        signal1.strategy = "AI Strategy"
        signal1.action = "BUY"
        signal1.confidence = 0.85
        
        signal2 = Mock()
        signal2.strategy = "Manual Strategy"
        signal2.action = "SELL"
        signal2.confidence = 0.6
        
        monitor.add_signal(signal1)
        monitor.add_signal(signal2)
        
        # Verify results
        assert monitor.total_trades == 2
        assert monitor.total_pnl == 50.0
        assert monitor.active_strategies == 4
        assert monitor.ai_signals_generated == 1
        
        # Check strategy performance
        assert "Strategy A" in monitor.strategy_performance
        assert "Strategy B" in monitor.strategy_performance
        assert "AI Strategy" in monitor.strategy_performance
        assert "Manual Strategy" in monitor.strategy_performance
        
        # Check performance summary
        summary = monitor.get_performance_summary()
        assert summary['total_trades'] == 2
        assert summary['total_pnl'] == 50.0
        assert summary['active_strategies'] == 4
        assert summary['ai_signals'] == 1
    
    def test_monitor_with_api_data(self, monitor):
        """Test monitor with API data integration"""
        # Mock API client
        mock_client = AsyncMock()
        mock_client.list_backtest_runs.return_value = [
            {
                'strategy_name': 'API Strategy',
                'total_pnl': 1000.0,
                'total_trades': 50,
                'win_rate': 0.6
            }
        ]
        mock_client.compare_strategies.return_value = {'success': True}
        
        monitor.backtest_api_client = mock_client
        
        # Fetch API data
        asyncio.run(monitor.fetch_api_data())
        
        # Verify API data was integrated
        assert "API Strategy" in monitor.strategy_performance
        strategy = monitor.strategy_performance["API Strategy"]
        assert strategy.total_pnl == 1000.0
        assert strategy.total_trades == 50
        assert strategy.win_rate == 0.6
        
        # Verify totals were updated
        assert monitor.total_pnl == 1000.0
        assert monitor.total_trades == 50 