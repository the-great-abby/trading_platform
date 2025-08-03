"""
Tests for Trade Evaluator AI Service
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.services.ai.trade_evaluator import TradeEvaluator
from src.core.types import TradeSignal


class TestTradeEvaluator:
    """Test TradeEvaluator"""
    
    @pytest.fixture
    def evaluator(self):
        """Create TradeEvaluator instance with LLM disabled"""
        return TradeEvaluator(model_name="test-model", enable_llm=False)
    
    @pytest.fixture
    def evaluator_with_llm(self):
        """Create TradeEvaluator instance with LLM enabled"""
        with patch('src.services.ai.trade_evaluator.OllamaService'):
            return TradeEvaluator(model_name="test-model", enable_llm=True)
    
    @pytest.fixture
    def sample_signal(self):
        """Create a sample trade signal"""
        return TradeSignal(
            symbol="AAPL",
            action="BUY",
            quantity=100,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.8,
            strategy="test_strategy",
            metadata={"source": "test", "confidence": 0.8}
        )
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data"""
        return pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': [150.0, 151.0, 152.0],
            'high': [152.0, 153.0, 154.0],
            'low': [149.0, 150.0, 151.0],
            'Close': [151.0, 152.0, 153.0],  # Changed to uppercase to match implementation
            'volume': [1000000, 1100000, 1200000]
        })
    
    def test_evaluator_initialization_disabled(self, evaluator):
        """Test evaluator initialization with LLM disabled"""
        assert evaluator is not None
        assert evaluator.enable_llm is False
        assert evaluator.ollama_service is None
        assert len(evaluator.evaluations) == 0
        assert evaluator.performance_stats['total_signals'] == 0
    
    def test_evaluator_initialization_enabled(self, evaluator_with_llm):
        """Test evaluator initialization with LLM enabled"""
        assert evaluator_with_llm is not None
        assert evaluator_with_llm.enable_llm is True
        assert evaluator_with_llm.ollama_service is not None
        assert len(evaluator_with_llm.evaluations) == 0
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_signal_disabled(self, evaluator, sample_signal, sample_market_data):
        """Test trade signal evaluation when LLM is disabled"""
        strategy_name = "test_strategy"
        
        result = await evaluator.evaluate_trade_signal(sample_signal, sample_market_data, strategy_name)
        
        assert result is not None
        assert result['approved'] is True
        assert result['confidence'] == 0.5
        assert result['reason'] == 'LLM evaluation disabled'
        assert 'timestamp' in result
        assert result['signal'] == sample_signal
        assert result['strategy'] == strategy_name
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_signal_enabled(self, evaluator_with_llm, sample_signal, sample_market_data):
        """Test trade signal evaluation when LLM is enabled"""
        strategy_name = "test_strategy"
        
        # Mock the LLM service
        async def mock_call_ollama(prompt):
            return """
            {
                "approved": true,
                "confidence": 0.85,
                "reason": "Strong technical indicators support this trade",
                "risk_level": "medium",
                "expected_return": "positive"
            }
            """
        
        with patch.object(evaluator_with_llm.ollama_service, '_call_ollama', side_effect=mock_call_ollama) as mock_call:
            
            result = await evaluator_with_llm.evaluate_trade_signal(sample_signal, sample_market_data, strategy_name)
            
            assert result is not None
            assert result['approved'] is True
            assert result['confidence'] == 0.85
            assert 'Strong technical indicators' in result['reason']
            assert 'timestamp' in result
            assert result['signal'] == sample_signal
            assert result['strategy'] == strategy_name
            assert len(evaluator_with_llm.evaluations) == 1
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_signal_llm_failure(self, evaluator_with_llm, sample_signal, sample_market_data):
        """Test trade signal evaluation when LLM fails"""
        strategy_name = "test_strategy"
        
        # Mock the LLM service to raise an exception
        with patch.object(evaluator_with_llm.ollama_service, '_call_ollama') as mock_call:
            mock_call.side_effect = Exception("LLM service unavailable")
            
            result = await evaluator_with_llm.evaluate_trade_signal(sample_signal, sample_market_data, strategy_name)
            
            assert result is not None
            assert result['approved'] is True  # Default to approve on failure
            assert result['confidence'] == 0.5
            assert 'LLM evaluation failed' in result['reason']
    
    def test_prepare_evaluation_context(self, evaluator, sample_signal, sample_market_data):
        """Test evaluation context preparation"""
        strategy_name = "test_strategy"
        
        context = evaluator._prepare_evaluation_context(sample_signal, sample_market_data, strategy_name)
        
        assert context is not None
        assert isinstance(context, dict)
        assert context['symbol'] == "AAPL"
        assert context['action'] == "BUY"
        assert context['quantity'] == 100
        assert context['price'] == 150.0
        assert context['strategy'] == strategy_name
        assert 'confidence' in context
        assert 'price_change_1d' in context
        assert 'price_change_5d' in context
        assert 'volatility' in context
        assert 'recent_prices' in context
    
    def test_generate_evaluation_prompt(self, evaluator):
        """Test evaluation prompt generation"""
        context = {
            'symbol': 'AAPL',
            'action': 'BUY',
            'quantity': 100,
            'price': 150.0,
            'strategy': 'test_strategy',
            'confidence': 0.8,
            'price_change_1d': 2.5,
            'price_change_5d': 5.0,
            'volatility': 15.5,
            'recent_prices': [145.0, 147.0, 149.0, 151.0, 153.0],
            'signal_metadata': {'rsi': 65, 'macd': 'positive'}
        }
        
        prompt = evaluator._generate_evaluation_prompt(context)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'AAPL' in prompt
        assert 'BUY' in prompt
        assert 'test_strategy' in prompt
        assert '150.0' in prompt
    
    def test_parse_evaluation_response_approved(self, evaluator):
        """Test parsing approved evaluation response"""
        response = """
        {
            "approved": true,
            "confidence": 0.85,
            "reason": "Strong technical indicators and positive market sentiment support this trade",
            "risk_level": "medium",
            "expected_return": "positive"
        }
        """
        signal = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        
        result = evaluator._parse_evaluation_response(response, signal)
        
        assert result['approved'] is True
        assert result['confidence'] == 0.85
        assert 'Strong technical indicators' in result['reason']
    
    def test_parse_evaluation_response_rejected(self, evaluator):
        """Test parsing rejected evaluation response"""
        response = """
        {
            "approved": false,
            "confidence": 0.75,
            "reason": "High market volatility and negative technical indicators suggest avoiding this trade",
            "risk_level": "high",
            "expected_return": "negative"
        }
        """
        signal = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        
        result = evaluator._parse_evaluation_response(response, signal)
        
        assert result['approved'] is False
        assert result['confidence'] == 0.75
        assert 'High market volatility' in result['reason']
    
    def test_parse_evaluation_response_malformed(self, evaluator):
        """Test parsing malformed evaluation response"""
        response = "Invalid response format"
        signal = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        
        result = evaluator._parse_evaluation_response(response, signal)
        
        assert result['approved'] is True  # Default to approve
        assert result['confidence'] == 0.5
        assert 'fallback' in result['reason'].lower()
    
    def test_update_performance(self, evaluator):
        """Test performance update"""
        # Add some evaluations first
        signal1 = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        signal2 = TradeSignal(symbol="MSFT", action="SELL", quantity=50, price=200.0, timestamp=datetime.now(), confidence=0.7, strategy="test", metadata={})
        
        evaluator.evaluations = [
            {
                'approved': True,
                'confidence': 0.8,
                'signal': signal1
            },
            {
                'approved': False,
                'confidence': 0.7,
                'signal': signal2
            }
        ]
        
        # Update performance with positive PnL for approved trade
        signal_id = f"{signal1.symbol}_{signal1.timestamp}"
        evaluator.update_performance(signal_id, 500.0)
        
        assert evaluator.performance_stats['approved_correct'] == 1
        assert evaluator.performance_stats['llm_accuracy'] == 1.0
    
    def test_get_performance_report(self, evaluator):
        """Test performance report generation"""
        # Add some evaluations
        signal1 = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        signal2 = TradeSignal(symbol="MSFT", action="SELL", quantity=50, price=200.0, timestamp=datetime.now(), confidence=0.7, strategy="test", metadata={})
        
        evaluator.evaluations = [
            {
                'approved': True,
                'confidence': 0.8,
                'signal': signal1
            },
            {
                'approved': False,
                'confidence': 0.7,
                'signal': signal2
            }
        ]
        
        # Update performance
        signal_id1 = f"{signal1.symbol}_{signal1.timestamp}"
        signal_id2 = f"{signal2.symbol}_{signal2.timestamp}"
        evaluator.update_performance(signal_id1, 500.0)
        evaluator.update_performance(signal_id2, -200.0)
        
        report = evaluator.get_performance_report()
        
        assert report is not None
        assert isinstance(report, dict)
        assert 'evaluations_summary' in report
        assert 'llm_performance' in report
        assert 'recent_evaluations' in report
        assert report['evaluations_summary']['total_evaluations'] == 2
        assert report['llm_performance']['llm_approved'] == 1
        assert report['llm_performance']['llm_rejected'] == 1
    
    def test_reset_performance(self, evaluator):
        """Test performance reset"""
        # Add some evaluations and performance data
        evaluator.evaluations = [{'approved': True, 'confidence': 0.8}]
        evaluator.performance_stats['total_signals'] = 5
        evaluator.performance_stats['llm_approved'] = 3
        
        evaluator.reset_performance()
        
        assert len(evaluator.evaluations) == 0
        assert evaluator.performance_stats['total_signals'] == 0
        assert evaluator.performance_stats['llm_approved'] == 0


class TestTradeEvaluatorEdgeCases:
    """Test edge cases for TradeEvaluator"""
    
    @pytest.fixture
    def evaluator(self):
        """Create TradeEvaluator instance"""
        return TradeEvaluator(model_name="test-model", enable_llm=False)
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_signal_empty_market_data(self, evaluator):
        """Test evaluation with empty market data"""
        signal = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        market_data = pd.DataFrame()  # Empty dataframe
        strategy_name = "test_strategy"
        
        result = await evaluator.evaluate_trade_signal(signal, market_data, strategy_name)
        
        assert result is not None
        assert result['approved'] is True
        assert result['confidence'] == 0.5
    
    @pytest.mark.asyncio
    async def test_evaluate_trade_signal_none_market_data(self, evaluator):
        """Test evaluation with None market data"""
        signal = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        market_data = None
        strategy_name = "test_strategy"
        
        result = await evaluator.evaluate_trade_signal(signal, market_data, strategy_name)
        
        assert result is not None
        assert result['approved'] is True
        assert result['confidence'] == 0.5
    
    def test_parse_evaluation_response_no_confidence(self, evaluator):
        """Test parsing response without confidence score"""
        response = """
        Approved: YES
        Reasoning: Good trade opportunity
        """
        signal = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        
        result = evaluator._parse_evaluation_response(response, signal)
        
        assert result['approved'] is True
        assert result['confidence'] == 0.5  # Default confidence
        assert 'Good trade opportunity' in result['reason']
    
    def test_parse_evaluation_response_no_approval(self, evaluator):
        """Test parsing response without approval status"""
        response = """
        Confidence: 0.8
        Reasoning: Mixed signals
        """
        signal = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        
        result = evaluator._parse_evaluation_response(response, signal)
        
        assert result['approved'] is True  # Default to approve
        assert result['confidence'] == 0.8
        assert 'Mixed signals' in result['reason']
    
    def test_update_performance_invalid_signal_id(self, evaluator):
        """Test performance update with invalid signal ID"""
        # This should not raise an error
        evaluator.update_performance("nonexistent_signal", 100.0)
        
        # Performance stats should remain unchanged
        assert evaluator.performance_stats['total_signals'] == 0
    
    def test_get_performance_report_empty(self, evaluator):
        """Test performance report with no evaluations"""
        report = evaluator.get_performance_report()
        
        assert report is not None
        assert report['evaluations_summary']['total_evaluations'] == 0
        assert report['llm_performance']['llm_accuracy'] == 0.0
        assert report['llm_performance']['llm_confidence_avg'] == 0.0


class TestTradeEvaluatorIntegration:
    """Integration tests for TradeEvaluator"""
    
    @pytest.fixture
    def evaluator_with_llm(self):
        """Create TradeEvaluator instance with LLM enabled"""
        with patch('src.services.ai.trade_evaluator.OllamaService'):
            return TradeEvaluator(model_name="test-model", enable_llm=True)
    
    @pytest.mark.asyncio
    async def test_full_workflow_evaluation(self, evaluator_with_llm):
        """Test complete workflow of trade evaluation"""
        signal = TradeSignal(
            symbol="AAPL",
            action="BUY",
            quantity=100,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.8,
            strategy="momentum_strategy",
            metadata={"source": "momentum", "confidence": 0.8}
        )
        
        market_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': [150.0, 151.0, 152.0],
            'high': [152.0, 153.0, 154.0],
            'low': [149.0, 150.0, 151.0],
            'Close': [151.0, 152.0, 153.0],
            'volume': [1000000, 1100000, 1200000]
        })
        
        strategy_name = "momentum_strategy"
        
        # Mock the LLM service
        with patch.object(evaluator_with_llm.ollama_service, '_call_ollama') as mock_call:
            async def mock_call_ollama(prompt):
                return """
                Approved: YES
                Confidence: 0.85
                Reasoning: Strong upward momentum with increasing volume supports this BUY signal
                """
            mock_call.side_effect = mock_call_ollama
            
            # Evaluate the trade signal
            result = await evaluator_with_llm.evaluate_trade_signal(signal, market_data, strategy_name)
            
            assert result is not None
            assert result['approved'] is True
            assert result['confidence'] == 0.85
            assert 'Strong upward momentum' in result['reason']
            assert len(evaluator_with_llm.evaluations) == 1
            
            # Update performance using the correct signal ID format
            signal_id = f"{signal.symbol}_{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}"
            evaluator_with_llm.update_performance(signal_id, 500.0)
            
            # Get performance report
            report = evaluator_with_llm.get_performance_report()
            
            assert report['llm_performance']['total_signals'] == 1
            assert report['llm_performance']['llm_approved'] == 1
            assert report['llm_performance']['llm_accuracy'] == 1.0
            assert report['llm_performance']['llm_confidence_avg'] == 0.85
    
    @pytest.mark.asyncio
    async def test_multiple_evaluations_workflow(self, evaluator_with_llm):
        """Test workflow with multiple trade evaluations"""
        signals = [
            TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={}),
            TradeSignal(symbol="MSFT", action="SELL", quantity=50, price=200.0, timestamp=datetime.now(), confidence=0.7, strategy="test", metadata={}),
            TradeSignal(symbol="GOOGL", action="BUY", quantity=25, price=300.0, timestamp=datetime.now(), confidence=0.9, strategy="test", metadata={})
        ]
        
        market_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'open': [150.0, 151.0],
            'high': [152.0, 153.0],
            'low': [149.0, 150.0],
            'Close': [151.0, 152.0],
            'volume': [1000000, 1100000]
        })
        
        strategy_name = "test_strategy"
        
        # Mock the LLM service with different responses
        with patch.object(evaluator_with_llm.ollama_service, '_call_ollama') as mock_call:
            call_count = 0
            responses = [
                "Approved: YES\nConfidence: 0.8\nReasoning: Good opportunity",
                "Approved: NO\nConfidence: 0.6\nReasoning: High risk",
                "Approved: YES\nConfidence: 0.9\nReasoning: Excellent setup"
            ]
            
            async def mock_call_ollama(prompt):
                nonlocal call_count
                response = responses[call_count]
                call_count += 1
                return response
            
            mock_call.side_effect = mock_call_ollama
            
            # Evaluate multiple signals
            results = []
            for signal in signals:
                result = await evaluator_with_llm.evaluate_trade_signal(signal, market_data, strategy_name)
                results.append(result)
            
            assert len(results) == 3
            assert results[0]['approved'] is True
            assert results[1]['approved'] is False
            assert results[2]['approved'] is True
            assert len(evaluator_with_llm.evaluations) == 3
            
            # Update performance for all signals using correct signal ID format
            signal_id_1 = f"{signals[0].symbol}_{signals[0].timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}"
            signal_id_2 = f"{signals[1].symbol}_{signals[1].timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}"
            signal_id_3 = f"{signals[2].symbol}_{signals[2].timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}"
            evaluator_with_llm.update_performance(signal_id_1, 300.0)  # Approved, profitable
            evaluator_with_llm.update_performance(signal_id_2, -100.0)  # Rejected, would have been loss
            evaluator_with_llm.update_performance(signal_id_3, 200.0)   # Approved, profitable
            
            # Get performance report
            report = evaluator_with_llm.get_performance_report()
            
            assert report['llm_performance']['total_signals'] == 3
            assert report['llm_performance']['llm_approved'] == 2
            assert report['llm_performance']['llm_rejected'] == 1
            assert report['llm_performance']['approved_correct'] == 2
            assert report['llm_performance']['rejected_correct'] == 1
            assert report['llm_performance']['llm_accuracy'] == 1.0  # All decisions were correct
    
    @pytest.mark.asyncio
    async def test_performance_tracking_workflow(self, evaluator_with_llm):
        """Test performance tracking workflow"""
        signal = TradeSignal(symbol="AAPL", action="BUY", quantity=100, price=150.0, timestamp=datetime.now(), confidence=0.8, strategy="test", metadata={})
        market_data = pd.DataFrame({'Close': [150.0, 151.0, 152.0]})
        strategy_name = "test_strategy"
        
        # Mock LLM service
        with patch.object(evaluator_with_llm.ollama_service, '_call_ollama') as mock_call:
            async def mock_call_ollama(prompt):
                return "Approved: YES\nConfidence: 0.8\nReasoning: Good setup"
            mock_call.side_effect = mock_call_ollama
            
            # Initial state
            assert evaluator_with_llm.performance_stats['total_signals'] == 0
            assert evaluator_with_llm.performance_stats['llm_accuracy'] == 0.0
            
            # Evaluate signal
            result = await evaluator_with_llm.evaluate_trade_signal(signal, market_data, strategy_name)
            
            # Check that evaluation was stored
            assert len(evaluator_with_llm.evaluations) == 1
            assert evaluator_with_llm.evaluations[0]['approved'] is True
            
            # Update performance with positive result using correct signal ID format
            signal_id = f"{signal.symbol}_{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}"
            evaluator_with_llm.update_performance(signal_id, 500.0)
            
            # Check performance stats
            stats = evaluator_with_llm.performance_stats
            assert stats['total_signals'] == 1
            assert stats['llm_approved'] == 1
            assert stats['approved_correct'] == 1
            assert stats['llm_accuracy'] == 1.0
            assert stats['llm_confidence_avg'] == 0.8
            
            # Reset performance
            evaluator_with_llm.reset_performance()
            
            # Check reset state
            assert len(evaluator_with_llm.evaluations) == 0
            assert evaluator_with_llm.performance_stats['total_signals'] == 0
            assert evaluator_with_llm.performance_stats['llm_accuracy'] == 0.0 