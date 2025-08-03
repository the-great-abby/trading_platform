"""
Tests for the main application entry point
"""

import pytest
import asyncio
import signal
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from src.main import AlgoTrader, main
from src.core.trading_engine import TradingEngine, TradingMode
from src.strategies.breakout.sma_crossover import SMACrossoverStrategy
from src.strategies.momentum.rsi_strategy import RSIStrategy
from src.utils.config import Config


class TestAlgoTrader:
    """Test the main AlgoTrader application"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        config = Mock(spec=Config)
        config.log_file = "/tmp/test.log"
        config.log_level = "INFO"
        config.initial_capital = 100000.0
        config.validate.return_value = True
        return config
    
    @pytest.fixture
    def mock_engine(self):
        """Mock trading engine"""
        engine = Mock(spec=TradingEngine)
        engine.strategies = {}
        engine.mode = TradingMode.PAPER
        engine.is_running = False
        engine.start = AsyncMock()
        engine.stop = AsyncMock()
        return engine
    
    @pytest.fixture
    def trader(self, mock_config, mock_engine):
        """Create AlgoTrader instance with mocked dependencies"""
        with patch('src.main.Config', return_value=mock_config), \
             patch('src.main.TradingEngine', return_value=mock_engine):
            return AlgoTrader()
    
    def test_algo_trader_initialization(self, trader, mock_config, mock_engine):
        """Test AlgoTrader initialization"""
        assert trader.config == mock_config
        assert trader.engine == mock_engine
        assert trader.running is False
    
    @patch('src.main.logger')
    def test_setup_logging(self, mock_logger, trader):
        """Test logging setup"""
        trader.setup_logging()
        
        # Verify logger configuration
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2  # File and stdout handlers
    
    def test_setup_strategies(self, trader, mock_engine):
        """Test strategy setup"""
        trader.setup_strategies()
        
        # Verify strategies were registered
        assert mock_engine.register_strategy.call_count == 2
        
        # Check SMA strategy registration
        sma_call = mock_engine.register_strategy.call_args_list[0]
        assert sma_call[0][0] == "AAPL"  # symbol
        assert isinstance(sma_call[0][1], SMACrossoverStrategy)
        
        # Check RSI strategy registration
        rsi_call = mock_engine.register_strategy.call_args_list[1]
        assert rsi_call[0][0] == "MSFT"  # symbol
        assert isinstance(rsi_call[0][1], RSIStrategy)
    
    @patch('src.main.signal')
    @patch('src.main.logger')
    def test_setup_signal_handlers(self, mock_logger, mock_signal, trader):
        """Test signal handler setup"""
        trader.setup_signal_handlers()
        
        # Verify signal handlers were registered
        assert mock_signal.signal.call_count == 2
        calls = mock_signal.signal.call_args_list
        assert calls[0][0][0] == signal.SIGINT
        assert calls[1][0][0] == signal.SIGTERM
    
    @patch('src.main.logger')
    async def test_run_success(self, mock_logger, trader, mock_engine, mock_config):
        """Test successful run"""
        mock_config.validate.return_value = True
        
        # Mock the running flag
        trader.running = True
        
        await trader.run()
        
        # Verify setup methods were called
        mock_logger.info.assert_called()
        mock_engine.set_mode.assert_called_with(TradingMode.PAPER)
        mock_engine.start.assert_called_once()
    
    @patch('src.main.logger')
    async def test_run_with_config_validation_failure(self, mock_logger, trader, mock_config):
        """Test run with configuration validation failure"""
        mock_config.validate.return_value = False
        
        await trader.run()
        
        # Verify warning was logged but execution continued
        mock_logger.warning.assert_called_with("Configuration validation failed, but continuing...")
    
    @patch('src.main.logger')
    async def test_run_with_exception(self, mock_logger, trader, mock_engine):
        """Test run with exception handling"""
        mock_engine.start.side_effect = Exception("Engine failed")
        
        await trader.run()
        
        # Verify error was logged
        mock_logger.error.assert_called_with("Error in main loop: Engine failed")
    
    @patch('src.main.logger')
    async def test_cleanup_with_running_engine(self, mock_logger, trader, mock_engine):
        """Test cleanup with running engine"""
        mock_engine.is_running = True
        
        await trader.cleanup()
        
        mock_logger.info.assert_called()
        mock_engine.stop.assert_called_once()
    
    @patch('src.main.logger')
    async def test_cleanup_with_stopped_engine(self, mock_logger, trader, mock_engine):
        """Test cleanup with stopped engine"""
        mock_engine.is_running = False
        
        await trader.cleanup()
        
        mock_logger.info.assert_called()
        mock_engine.stop.assert_not_called()
    
    def test_signal_handler(self, trader):
        """Test signal handler functionality"""
        # Test that signal handler sets running to False
        trader.running = True
        
        # Simulate signal handler call
        trader._signal_handler = trader.__class__.__dict__['setup_signal_handlers'].__func__.__closure__[0].cell_contents
        trader._signal_handler(signal.SIGINT, None)
        
        assert trader.running is False


class TestMainFunction:
    """Test the main function"""
    
    @patch('src.main.AlgoTrader')
    async def test_main_function(self, mock_algo_trader_class):
        """Test main function execution"""
        mock_trader = Mock()
        mock_trader.run = AsyncMock()
        mock_algo_trader_class.return_value = mock_trader
        
        await main()
        
        # Verify AlgoTrader was created and run was called
        mock_algo_trader_class.assert_called_once()
        mock_trader.run.assert_called_once()


class TestAlgoTraderIntegration:
    """Integration tests for AlgoTrader"""
    
    @pytest.fixture
    def real_config(self):
        """Real configuration for integration tests"""
        config = Config()
        config.log_file = "/tmp/test_integration.log"
        config.log_level = "DEBUG"
        config.initial_capital = 50000.0
        return config
    
    @pytest.fixture
    def real_engine(self, real_config):
        """Real trading engine for integration tests"""
        return TradingEngine(real_config)
    
    @pytest.fixture
    def integration_trader(self, real_config, real_engine):
        """AlgoTrader with real components for integration testing"""
        trader = AlgoTrader()
        trader.config = real_config
        trader.engine = real_engine
        return trader
    
    def test_integration_strategy_registration(self, integration_trader):
        """Test strategy registration with real components"""
        integration_trader.setup_strategies()
        
        # Verify strategies were registered
        assert len(integration_trader.engine.strategies) == 2
        assert "AAPL" in integration_trader.engine.strategies
        assert "MSFT" in integration_trader.engine.strategies
        
        # Verify strategy types
        assert isinstance(integration_trader.engine.strategies["AAPL"], SMACrossoverStrategy)
        assert isinstance(integration_trader.engine.strategies["MSFT"], RSIStrategy)
    
    def test_integration_config_validation(self, integration_trader):
        """Test configuration validation"""
        # Test with valid config
        assert integration_trader.config.validate() is True
        
        # Test with invalid config (modify to make invalid)
        original_validate = integration_trader.config.validate
        integration_trader.config.validate = lambda: False
        
        # Should still work but log warning
        integration_trader.config.validate = original_validate
    
    @patch('src.main.logger')
    async def test_integration_run_cycle(self, mock_logger, integration_trader):
        """Test complete run cycle with real components"""
        # Mock the engine start to avoid actual trading
        integration_trader.engine.start = AsyncMock()
        
        await integration_trader.run()
        
        # Verify the run cycle completed
        mock_logger.info.assert_called()
        integration_trader.engine.start.assert_called_once()


class TestAlgoTraderEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.fixture
    def edge_case_trader(self):
        """AlgoTrader for edge case testing"""
        return AlgoTrader()
    
    def test_empty_strategies(self, edge_case_trader):
        """Test behavior with no strategies"""
        # Clear strategies
        edge_case_trader.engine.strategies = {}
        
        # Should not raise exception
        edge_case_trader.setup_strategies()
        
        # Should have registered strategies
        assert len(edge_case_trader.engine.strategies) > 0
    
    @patch('src.main.logger')
    async def test_engine_start_failure(self, mock_logger, edge_case_trader):
        """Test handling of engine start failure"""
        edge_case_trader.engine.start = AsyncMock(side_effect=Exception("Start failed"))
        
        await edge_case_trader.run()
        
        # Should handle exception gracefully
        mock_logger.error.assert_called()
    
    @patch('src.main.logger')
    async def test_cleanup_with_exception(self, mock_logger, edge_case_trader):
        """Test cleanup with exception"""
        edge_case_trader.engine.is_running = True
        edge_case_trader.engine.stop = AsyncMock(side_effect=Exception("Stop failed"))
        
        await edge_case_trader.cleanup()
        
        # Should handle exception gracefully
        mock_logger.info.assert_called()
    
    def test_signal_handler_multiple_calls(self, edge_case_trader):
        """Test signal handler with multiple calls"""
        edge_case_trader.running = True
        
        # Call signal handler multiple times
        for _ in range(3):
            edge_case_trader._signal_handler = edge_case_trader.__class__.__dict__['setup_signal_handlers'].__func__.__closure__[0].cell_contents
            edge_case_trader._signal_handler(signal.SIGINT, None)
        
        # Should be stopped after first call
        assert edge_case_trader.running is False


class TestAlgoTraderPerformance:
    """Performance tests for AlgoTrader"""
    
    @pytest.fixture
    def performance_trader(self):
        """AlgoTrader for performance testing"""
        return AlgoTrader()
    
    def test_strategy_setup_performance(self, performance_trader):
        """Test strategy setup performance"""
        import time
        
        start_time = time.time()
        performance_trader.setup_strategies()
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 1.0  # Less than 1 second
    
    def test_logging_setup_performance(self, performance_trader):
        """Test logging setup performance"""
        import time
        
        start_time = time.time()
        performance_trader.setup_logging()
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 0.1  # Less than 100ms
    
    @patch('src.main.logger')
    async def test_run_performance(self, mock_logger, performance_trader):
        """Test run performance"""
        import time
        
        performance_trader.engine.start = AsyncMock()
        
        start_time = time.time()
        await performance_trader.run()
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 2.0  # Less than 2 seconds 