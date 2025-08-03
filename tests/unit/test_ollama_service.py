"""
Tests for Ollama AI Service with LLM Proxy Integration
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.services.ai.ollama_service import OllamaService, AIAnalysis
from src.services.llm_service.llm_client import LLMRequest, LLMResponse, LLMError, LLMTaskType, ProxyCallbackConfig


class TestOllamaService:
    """Test OllamaService with LLM proxy integration"""
    
    @pytest.fixture
    def service(self):
        """Create OllamaService instance"""
        return OllamaService(base_url="http://test:12001", model="test-model")
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client"""
        client = AsyncMock()
        client.health_check.return_value = True
        return client
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service"""
        service = AsyncMock()
        return service
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service is not None
        assert service.proxy_base_url == "http://test:12001"
        assert service.model == "test-model"
        assert service.is_initialized is False
    
    def test_service_initialization_defaults(self):
        """Test service initialization with defaults"""
        with patch.dict('os.environ', {
            'LLM_PROXY_BASE_URL': 'http://default:12001', 
            'OLLAMA_MODEL': 'default-model',
            'LLM_PROXY_API_KEY': 'test-key',
            'LLM_PROXY_TIMEOUT': '30',
            'LLM_PROXY_MAX_RETRIES': '3'
        }):
            service = OllamaService()
            assert service.proxy_base_url == "http://default:12001"
            assert service.model == "default-model"
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, service):
        """Test async context manager"""
        def mock_initialize():
            service.is_initialized = True
            return True
            
        with patch.object(service, 'initialize', side_effect=mock_initialize) as mock_init:
            with patch.object(service, 'cleanup'):
                async with service as s:
                    assert s == service
                    # The initialize method should be called and set is_initialized to True
                    mock_init.assert_called_once()
                    assert service.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, service, mock_llm_client):
        """Test successful initialization"""
        with patch.object(service, 'llm_client', mock_llm_client):
            result = await service.initialize()
            
            assert result is True
            assert service.is_initialized is True
            mock_llm_client.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, service, mock_llm_client):
        """Test initialization failure"""
        mock_llm_client.health_check.return_value = False
        
        with patch.object(service, 'llm_client', mock_llm_client):
            result = await service.initialize()
            
            assert result is False
            assert service.is_initialized is False  # Should be False when health check fails
    
    @pytest.mark.asyncio
    async def test_verify_model_availability_success(self, service, mock_llm_client):
        """Test successful model availability verification"""
        # Mock successful LLM response
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content="Test response",
            task_type=LLMTaskType.SENTIMENT_ANALYSIS,
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            finish_reason="stop",
            response_time=1.5,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_response
        
        with patch.object(service, 'llm_client', mock_llm_client):
            with patch.object(service, 'initialize', return_value=True):
                service.is_initialized = True
                
                result = await service.verify_model_availability()
                
                assert result['available'] is True
                assert result['proxy_healthy'] is True
                assert result['model_available'] is True
                assert result['target_model'] == 'test-model'
                assert result['proxy_url'] == 'http://test:12001'
    
    @pytest.mark.asyncio
    async def test_verify_model_availability_model_not_found(self, service, mock_llm_client):
        """Test model availability when target model not found"""
        # Mock LLM error response
        mock_error = LLMError(
            request_id="test-123",
            error_type="model_not_found",
            error_message="Model test-model not available",
            status_code=404,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_error
        
        with patch.object(service, 'llm_client', mock_llm_client):
            with patch.object(service, 'initialize', return_value=True):
                service.is_initialized = True
                
                result = await service.verify_model_availability()
                
                assert result['available'] is False
                assert result['proxy_healthy'] is True
                assert result['model_available'] is False
                assert result['error'] == "Model test-model not available"
    
    @pytest.mark.asyncio
    async def test_verify_model_availability_connection_error(self, service):
        """Test model availability with connection error"""
        with patch.object(service, 'initialize', side_effect=Exception("Connection failed")):
            result = await service.verify_model_availability()
            
            assert result['available'] is False
            assert result['proxy_healthy'] is False
            assert 'Connection failed' in result['error']
    
    @pytest.mark.asyncio
    async def test_test_model_response_success(self, service, mock_llm_client):
        """Test successful model response test"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content="OK",
            task_type=LLMTaskType.SENTIMENT_ANALYSIS,
            usage={"prompt_tokens": 10, "completion_tokens": 2},
            finish_reason="stop",
            response_time=1.0,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_response
        
        with patch.object(service, 'llm_client', mock_llm_client):
            result = await service.test_model_response()
            
            assert result['success'] is True
            assert result['model_used'] == 'test-model'
            assert result['response'] == 'OK'
            assert result['proxy_used'] is True
            assert result['response_time'] == 1.0
    
    @pytest.mark.asyncio
    async def test_test_model_response_failure(self, service, mock_llm_client):
        """Test model response test failure"""
        mock_error = LLMError(
            request_id="test-123",
            error_type="timeout",
            error_message="Request timeout",
            status_code=408,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_error
        
        with patch.object(service, 'llm_client', mock_llm_client):
            result = await service.test_model_response()
            
            assert result['success'] is False
            assert result['error'] == "Request timeout"
    
    @pytest.mark.asyncio
    async def test_analyze_market_sentiment_success(self, service, mock_llm_client):
        """Test successful market sentiment analysis"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content='{"overall_sentiment": 0.5, "confidence": 0.8, "reasoning": "Test", "risk_assessment": "medium", "market_impact": "bullish", "recommended_action": "Buy"}',
            task_type=LLMTaskType.MARKET_ANALYSIS,
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            finish_reason="stop",
            response_time=2.0,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_response
        
        with patch.object(service, 'llm_client', mock_llm_client):
            news_events = [{"title": "Test news"}]
            technical_signals = [{"indicator": "RSI", "value": 65}]
            market_data = {"symbol": "TEST", "price": 100}
            
            result = await service.analyze_market_sentiment(news_events, technical_signals, market_data)
            
            assert isinstance(result, AIAnalysis)
            assert result.sentiment_score == 0.5
            assert result.confidence == 0.8
            assert result.reasoning == "Test"
            assert result.risk_assessment == "medium"
            assert result.market_impact == "bullish"
            assert result.recommended_action == "Buy"
            assert result.metadata['proxy_used'] is True
    
    @pytest.mark.asyncio
    async def test_analyze_market_sentiment_with_callback(self, service, mock_llm_client):
        """Test market sentiment analysis with callback URL"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content='{"overall_sentiment": 0.3, "confidence": 0.7, "reasoning": "Test with callback", "risk_assessment": "low", "market_impact": "neutral", "recommended_action": "Hold"}',
            task_type=LLMTaskType.MARKET_ANALYSIS,
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            finish_reason="stop",
            response_time=1.5,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_response
        
        with patch.object(service, 'llm_client', mock_llm_client):
            news_events = [{"title": "Test news"}]
            technical_signals = [{"indicator": "RSI", "value": 65}]
            market_data = {"symbol": "TEST", "price": 100}
            
            callback = ProxyCallbackConfig(
                success_url="http://localhost:8080/api/success",
                timeout_url="http://localhost:8080/api/timeout",
                timeout_seconds=30
            )
            
            result = await service.analyze_market_sentiment(
                news_events, technical_signals, market_data, proxy_callback=callback
            )
            
            assert isinstance(result, AIAnalysis)
            assert result.sentiment_score == 0.3
            assert result.confidence == 0.7
    
    @pytest.mark.asyncio
    async def test_enhance_news_sentiment_success(self, service, mock_llm_client):
        """Test successful news sentiment enhancement"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content='{"enhanced_sentiment": 0.6, "market_impact": "high", "risk_level": "medium", "reasoning": "Test reasoning", "trading_implications": "Positive impact"}',
            task_type=LLMTaskType.NEWS_ANALYSIS,
            usage={"prompt_tokens": 80, "completion_tokens": 40},
            finish_reason="stop",
            response_time=1.2,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_response
        
        with patch.object(service, 'llm_client', mock_llm_client):
            news_event = {
                "title": "Test news",
                "content": "Test content",
                "source": "Test source"
            }
            
            result = await service.enhance_news_sentiment(news_event)
            
            assert result['enhanced_sentiment'] == 0.6
            assert result['market_impact'] == "high"
            assert result['risk_level'] == "medium"
            assert result['reasoning'] == "Test reasoning"
            assert result['trading_implications'] == "Positive impact"
    
    @pytest.mark.asyncio
    async def test_generate_multi_factor_signal_success(self, service, mock_llm_client):
        """Test successful multi-factor signal generation"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content='{"action": "BUY", "confidence": 0.8, "reasoning": "Strong signals", "risk_level": "medium", "position_size": "10%", "stop_loss": "2%", "take_profit": "15%"}',
            task_type=LLMTaskType.SIGNAL_GENERATION,
            usage={"prompt_tokens": 120, "completion_tokens": 60},
            finish_reason="stop",
            response_time=2.5,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_response
        
        with patch.object(service, 'llm_client', mock_llm_client):
            technical_signals = [{"indicator": "RSI", "value": 65}]
            news_sentiment = {"sentiment_score": 0.5, "confidence": 0.7}
            market_context = {"current_price": 100, "volume": 1000000}
            
            result = await service.generate_multi_factor_signal(
                symbol="TEST",
                technical_signals=technical_signals,
                news_sentiment=news_sentiment,
                market_context=market_context
            )
            
            assert result is not None
            assert result.symbol == "TEST"
            assert result.action == "BUY"
            assert result.confidence == 0.8
            assert result.quantity == 0.1  # 10%
            assert result.price == 100
            assert result.strategy == "AI_MULTI_FACTOR"
            assert result.metadata['proxy_used'] is True
            assert result.metadata['reasoning'] == "Strong signals"
    
    @pytest.mark.asyncio
    async def test_generate_multi_factor_signal_hold(self, service, mock_llm_client):
        """Test multi-factor signal generation with HOLD action"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content='{"action": "HOLD", "confidence": 0.6, "reasoning": "Uncertain conditions", "risk_level": "low", "position_size": "0%", "stop_loss": "0%", "take_profit": "0%"}',
            task_type=LLMTaskType.SIGNAL_GENERATION,
            usage={"prompt_tokens": 120, "completion_tokens": 60},
            finish_reason="stop",
            response_time=2.0,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_response
        
        with patch.object(service, 'llm_client', mock_llm_client):
            technical_signals = [{"indicator": "RSI", "value": 50}]
            news_sentiment = {"sentiment_score": 0.0, "confidence": 0.5}
            market_context = {"current_price": 100, "volume": 1000000}
            
            result = await service.generate_multi_factor_signal(
                symbol="TEST",
                technical_signals=technical_signals,
                news_sentiment=news_sentiment,
                market_context=market_context
            )
            
            assert result is None  # HOLD actions return None
    
    def test_build_analysis_prompt(self, service):
        """Test analysis prompt building"""
        news_events = [{"title": "Test news"}]
        technical_signals = [{"indicator": "RSI", "value": 65}]
        market_data = {"symbol": "TEST", "price": 100}
        
        prompt = service._build_analysis_prompt(news_events, technical_signals, market_data)
        
        assert "NEWS EVENTS (1 events)" in prompt
        assert "TECHNICAL SIGNALS (1 signals)" in prompt
        assert "MARKET DATA" in prompt
        assert "overall_sentiment" in prompt
        assert "confidence" in prompt
    
    def test_parse_ai_response(self, service):
        """Test AI response parsing"""
        response = '{"overall_sentiment": 0.5, "confidence": 0.8, "reasoning": "Test", "risk_assessment": "medium", "market_impact": "bullish", "recommended_action": "Buy", "key_factors": ["factor1"], "market_volatility": "high"}'
        
        result = service._parse_ai_response(response)
        
        assert isinstance(result, AIAnalysis)
        assert result.sentiment_score == 0.5
        assert result.confidence == 0.8
        assert result.reasoning == "Test"
        assert result.risk_assessment == "medium"
        assert result.market_impact == "bullish"
        assert result.recommended_action == "Buy"
        assert result.metadata['key_factors'] == ["factor1"]
        assert result.metadata['market_volatility'] == "high"
        assert result.metadata['proxy_used'] is True
    
    def test_parse_ai_response_fallback(self, service):
        """Test AI response parsing fallback"""
        response = "Invalid JSON response"
        
        result = service._parse_ai_response(response)
        
        assert isinstance(result, AIAnalysis)
        assert result.sentiment_score == 0.0
        assert result.confidence == 0.3
        assert "fallback" in result.reasoning
        assert result.metadata['fallback'] is True
        assert result.metadata['proxy_used'] is True
    
    def test_fallback_analysis(self, service):
        """Test fallback analysis"""
        result = service._fallback_analysis()
        
        assert isinstance(result, AIAnalysis)
        assert result.sentiment_score == 0.0
        assert result.confidence == 0.3
        assert "fallback" in result.reasoning
        assert result.metadata['fallback'] is True
        assert result.metadata['proxy_used'] is True
    
    def test_calculate_quantity(self, service):
        """Test quantity calculation"""
        signal_data = {"position_size": "15%"}
        quantity = service._calculate_quantity(signal_data)
        assert quantity == 0.15
        
        signal_data = {"position_size": "5%"}
        quantity = service._calculate_quantity(signal_data)
        assert quantity == 0.05
        
        signal_data = {"position_size": "invalid"}
        quantity = service._calculate_quantity(signal_data)
        assert quantity == 0.05  # Default
    
    @pytest.mark.asyncio
    async def test_cleanup(self, service, mock_llm_client):
        """Test cleanup"""
        with patch.object(service, 'llm_client', mock_llm_client):
            await service.cleanup()
            mock_llm_client.disconnect.assert_called_once()
    
    def test_destructor(self, service):
        """Test destructor"""
        # Should not raise any exceptions
        del service


class TestOllamaServiceEdgeCases:
    """Test OllamaService edge cases"""
    
    @pytest.fixture
    def service(self):
        """Create OllamaService instance"""
        return OllamaService(base_url="http://test:12001", model="test-model")
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client"""
        client = AsyncMock()
        return client
    
    @pytest.mark.asyncio
    async def test_verify_model_availability_empty_response(self, service, mock_llm_client):
        """Test model availability with empty response"""
        mock_error = LLMError(
            request_id="test-123",
            error_type="empty_response",
            error_message="Empty response from model",
            status_code=200,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_error
        
        with patch.object(service, 'llm_client', mock_llm_client):
            with patch.object(service, 'initialize', return_value=True):
                service.is_initialized = True
                
                result = await service.verify_model_availability()
                
                assert result['available'] is False
                assert result['model_available'] is False
                assert result['error'] == "Empty response from model"
    
    @pytest.mark.asyncio
    async def test_call_ollama_timeout(self, service, mock_llm_client):
        """Test timeout handling"""
        mock_error = LLMError(
            request_id="test-123",
            error_type="timeout",
            error_message="Request timeout",
            status_code=408,
            timestamp=datetime.now()
        )
        
        mock_llm_client.generate.return_value = mock_error
        
        with patch.object(service, 'llm_client', mock_llm_client):
            result = await service.test_model_response()
            
            assert result['success'] is False
            assert result['error'] == "Request timeout"
    
    def test_parse_ai_response_malformed(self, service):
        """Test parsing malformed AI response"""
        response = '{"overall_sentiment": "invalid", "confidence": "invalid"}'
        
        result = service._parse_ai_response(response)
        
        assert isinstance(result, AIAnalysis)
        assert result.sentiment_score == 0.0
        assert result.confidence == 0.5
        assert result.metadata['proxy_used'] is True
    
    def test_calculate_quantity_edge_cases(self, service):
        """Test quantity calculation edge cases"""
        # Test various percentage formats
        test_cases = [
            ({"position_size": "10%"}, 0.1),
            ({"position_size": "5.5%"}, 0.055),
            ({"position_size": "0%"}, 0.0),
            ({"position_size": "100%"}, 1.0),
            ({"position_size": "invalid"}, 0.05),  # Default
            ({"position_size": ""}, 0.05),  # Default
            ({}, 0.05),  # Default
        ]
        
        for signal_data, expected in test_cases:
            quantity = service._calculate_quantity(signal_data)
            assert quantity == expected


class TestOllamaServiceIntegration:
    """Test OllamaService integration scenarios"""
    
    @pytest.fixture
    def service(self):
        """Create OllamaService instance"""
        return OllamaService(base_url="http://test:12001", model="test-model")
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client"""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_full_workflow_analysis(self, service, mock_llm_client):
        """Test full workflow market analysis"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content='{"overall_sentiment": 0.7, "confidence": 0.9, "reasoning": "Strong positive signals", "risk_assessment": "low", "market_impact": "bullish", "recommended_action": "Strong Buy", "key_factors": ["earnings", "technical"], "market_volatility": "medium"}',
            task_type=LLMTaskType.MARKET_ANALYSIS,
            usage={"prompt_tokens": 150, "completion_tokens": 75},
            finish_reason="stop",
            response_time=3.0,
            timestamp=datetime.now()
        )
        
        # Make the mock method itself async
        async def mock_generate(request):
            return mock_response
        mock_llm_client.generate = mock_generate
        
        with patch.object(service, 'llm_client', mock_llm_client):
            # Test full workflow
            news_events = [
                {"title": "Strong earnings report", "content": "Company exceeded expectations"},
                {"title": "Market rally", "content": "Broad market gains"}
            ]
            technical_signals = [
                {"indicator": "RSI", "value": 70, "signal": "bullish"},
                {"indicator": "MACD", "value": 0.5, "signal": "bullish"}
            ]
            market_data = {
                "symbol": "TEST",
                "current_price": 150.25,
                "volume": 2000000,
                "change_1d": 5.5
            }
            
            result = await service.analyze_market_sentiment(news_events, technical_signals, market_data)
            
            assert isinstance(result, AIAnalysis)
            assert result.sentiment_score == 0.7
            assert result.confidence == 0.9
            assert result.recommended_action == "Strong Buy"
            assert result.metadata['key_factors'] == ["earnings", "technical"]
    
    @pytest.mark.asyncio
    async def test_multi_factor_signal_generation(self, service, mock_llm_client):
        """Test multi-factor signal generation workflow"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content='{"action": "SELL", "confidence": 0.85, "reasoning": "Technical and fundamental signals align", "risk_level": "high", "position_size": "20%", "stop_loss": "3%", "take_profit": "20%"}',
            task_type=LLMTaskType.SIGNAL_GENERATION,
            usage={"prompt_tokens": 200, "completion_tokens": 100},
            finish_reason="stop",
            response_time=4.0,
            timestamp=datetime.now()
        )
        
        # Make the mock method itself async
        async def mock_generate(request):
            return mock_response
        mock_llm_client.generate = mock_generate
        
        with patch.object(service, 'llm_client', mock_llm_client):
            technical_signals = [
                {"indicator": "RSI", "value": 80, "signal": "overbought"},
                {"indicator": "MACD", "value": -0.3, "signal": "bearish"}
            ]
            news_sentiment = {
                "sentiment_score": -0.4,
                "confidence": 0.8,
                "impact": "negative"
            }
            market_context = {
                "current_price": 200.50,
                "volume": 1500000,
                "volatility": 0.25,
                "market_condition": "bearish"
            }
            
            result = await service.generate_multi_factor_signal(
                symbol="TEST",
                technical_signals=technical_signals,
                news_sentiment=news_sentiment,
                market_context=market_context
            )
            
            assert result is not None
            assert result.action == "SELL"
            assert result.confidence == 0.85
            assert result.quantity == 0.2  # 20%
            assert result.metadata['risk_level'] == "high"
            assert result.metadata['position_size'] == "20%"
    
    @pytest.mark.asyncio
    async def test_news_sentiment_enhancement_workflow(self, service, mock_llm_client):
        """Test news sentiment enhancement workflow"""
        mock_response = LLMResponse(
            request_id="test-123",
            model="test-model",
            content='{"enhanced_sentiment": 0.8, "market_impact": "high", "risk_level": "medium", "reasoning": "Positive earnings surprise", "trading_implications": "Expect upward price movement"}',
            task_type=LLMTaskType.NEWS_ANALYSIS,
            usage={"prompt_tokens": 120, "completion_tokens": 60},
            finish_reason="stop",
            response_time=2.5,
            timestamp=datetime.now()
        )
        
        # Make the mock method itself async
        async def mock_generate(request):
            return mock_response
        mock_llm_client.generate = mock_generate
        
        with patch.object(service, 'llm_client', mock_llm_client):
            news_event = {
                "title": "Tech Company Reports Record Earnings",
                "content": "Company XYZ reported Q4 earnings that exceeded analyst expectations by 25%",
                "source": "Financial Times",
                "event_type": "earnings",
                "affected_symbols": ["XYZ", "TECH"],
                "timestamp": "2024-01-15T10:30:00Z"
            }
            
            result = await service.enhance_news_sentiment(news_event)
            
            assert result['enhanced_sentiment'] == 0.8
            assert result['market_impact'] == "high"
            assert result['risk_level'] == "medium"
            assert result['reasoning'] == "Positive earnings surprise"
            assert result['trading_implications'] == "Expect upward price movement"
            assert result['title'] == "Tech Company Reports Record Earnings"  # Original data preserved 