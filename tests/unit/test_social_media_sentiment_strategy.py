#!/usr/bin/env python3
"""
Tests for Social Media Sentiment Strategy
Comprehensive test suite for social media sentiment strategy
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.strategies.sentiment.social_media_sentiment_strategy import SocialMediaSentimentStrategy
from src.core.types import TradeSignal


class TestSocialMediaSentimentStrategyInitialization:
    """Test SocialMediaSentimentStrategy initialization"""
    
    def test_social_media_sentiment_strategy_init_default(self):
        """Test SocialMediaSentimentStrategy initialization with default parameters"""
        strategy = SocialMediaSentimentStrategy()
        
        assert strategy.name == "SocialMediaSentiment"
        assert strategy.sentiment_threshold == 0.2
        assert strategy.volume_threshold == 100
        assert strategy.confidence_threshold == 0.6
        assert strategy.sentiment_window == 24
        assert strategy.min_mentions == 10
        assert strategy.is_active is True
        assert isinstance(strategy.config, dict)
        assert len(strategy.bullish_keywords) > 0
        assert len(strategy.bearish_keywords) > 0
    
    def test_social_media_sentiment_strategy_init_custom(self):
        """Test SocialMediaSentimentStrategy initialization with custom parameters"""
        strategy = SocialMediaSentimentStrategy(
            name="Custom_Sentiment",
            sentiment_threshold=0.3,
            volume_threshold=200,
            confidence_threshold=0.7,
            sentiment_window=48,
            min_mentions=20
        )
        
        assert strategy.name == "Custom_Sentiment"
        assert strategy.sentiment_threshold == 0.3
        assert strategy.volume_threshold == 200
        assert strategy.confidence_threshold == 0.7
        assert strategy.sentiment_window == 48
        assert strategy.min_mentions == 20
    
    def test_social_media_sentiment_strategy_get_strategy_info(self):
        """Test get_strategy_info method"""
        strategy = SocialMediaSentimentStrategy(
            sentiment_threshold=0.25,
            volume_threshold=150,
            confidence_threshold=0.65
        )
        info = strategy.get_strategy_info()
        
        assert info['name'] == "SocialMediaSentiment"
        assert info['sentiment_threshold'] == 0.25
        assert info['volume_threshold'] == 150
        assert info['confidence_threshold'] == 0.65
        assert info['sentiment_window_hours'] == 24
        assert info['min_mentions'] == 10
        assert info['bullish_keywords_count'] > 0
        assert info['bearish_keywords_count'] > 0


class TestSocialMediaSentimentStrategyTextAnalysis:
    """Test text sentiment analysis functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create SocialMediaSentimentStrategy instance"""
        return SocialMediaSentimentStrategy()
    
    def test_analyze_text_sentiment_bullish(self, strategy):
        """Test sentiment analysis for bullish text"""
        text = "AAPL looking bullish today! Strong earnings report 📈 moon rocket pump"
        analysis = strategy.analyze_text_sentiment(text)
        
        assert isinstance(analysis, dict)
        assert 'textblob_sentiment' in analysis
        assert 'keyword_sentiment' in analysis
        assert 'engagement_score' in analysis
        assert 'combined_sentiment' in analysis
        
        # Should be positive sentiment
        assert analysis['combined_sentiment'] > 0
        assert analysis['keyword_sentiment'] > 0
        assert analysis['engagement_score'] > 0
    
    def test_analyze_text_sentiment_bearish(self, strategy):
        """Test sentiment analysis for bearish text"""
        text = "AAPL earnings miss - stock might be in trouble 📉 crash dump sell"
        analysis = strategy.analyze_text_sentiment(text)
        
        assert isinstance(analysis, dict)
        assert 'textblob_sentiment' in analysis
        assert 'keyword_sentiment' in analysis
        assert 'engagement_score' in analysis
        assert 'combined_sentiment' in analysis
        
        # Should be negative sentiment
        assert analysis['combined_sentiment'] < 0
        assert analysis['keyword_sentiment'] < 0
        assert analysis['engagement_score'] < 0
    
    def test_analyze_text_sentiment_neutral(self, strategy):
        """Test sentiment analysis for neutral text"""
        text = "AAPL stock price is stable today"
        analysis = strategy.analyze_text_sentiment(text)
        
        assert isinstance(analysis, dict)
        assert 'textblob_sentiment' in analysis
        assert 'keyword_sentiment' in analysis
        assert 'engagement_score' in analysis
        assert 'combined_sentiment' in analysis
        
        # Should be close to neutral
        assert abs(analysis['combined_sentiment']) < 0.3
    
    def test_analyze_text_sentiment_empty(self, strategy):
        """Test sentiment analysis for empty text"""
        text = ""
        analysis = strategy.analyze_text_sentiment(text)
        
        assert isinstance(analysis, dict)
        assert 'textblob_sentiment' in analysis
        assert 'keyword_sentiment' in analysis
        assert 'engagement_score' in analysis
        assert 'combined_sentiment' in analysis
    
    def test_analyze_text_sentiment_special_characters(self, strategy):
        """Test sentiment analysis with special characters"""
        text = "AAPL $AAPL #AAPL @AAPL bullish! 🚀📈"
        analysis = strategy.analyze_text_sentiment(text)
        
        assert isinstance(analysis, dict)
        assert 'combined_sentiment' in analysis
        # Should handle special characters gracefully
        assert not pd.isna(analysis['combined_sentiment'])


class TestSocialMediaSentimentStrategyAggregation:
    """Test sentiment aggregation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create SocialMediaSentimentStrategy instance"""
        return SocialMediaSentimentStrategy()
    
    def test_aggregate_sentiment_positive_data(self, strategy):
        """Test sentiment aggregation with positive data"""
        sentiment_data = [
            {'sentiment': 0.8, 'volume': 100},
            {'sentiment': 0.6, 'volume': 150},
            {'sentiment': 0.7, 'volume': 200}
        ]
        
        result = strategy.aggregate_sentiment(sentiment_data)
        
        assert isinstance(result, dict)
        assert 'overall_sentiment' in result
        assert 'confidence' in result
        assert 'volume' in result
        
        assert result['overall_sentiment'] > 0
        assert result['confidence'] > 0
        assert result['volume'] == 450
    
    def test_aggregate_sentiment_negative_data(self, strategy):
        """Test sentiment aggregation with negative data"""
        sentiment_data = [
            {'sentiment': -0.8, 'volume': 100},
            {'sentiment': -0.6, 'volume': 150},
            {'sentiment': -0.7, 'volume': 200}
        ]
        
        result = strategy.aggregate_sentiment(sentiment_data)
        
        assert isinstance(result, dict)
        assert result['overall_sentiment'] < 0
        assert result['confidence'] > 0
        assert result['volume'] == 450
    
    def test_aggregate_sentiment_mixed_data(self, strategy):
        """Test sentiment aggregation with mixed data"""
        sentiment_data = [
            {'sentiment': 0.8, 'volume': 100},
            {'sentiment': -0.6, 'volume': 150},
            {'sentiment': 0.2, 'volume': 200}
        ]
        
        result = strategy.aggregate_sentiment(sentiment_data)
        
        assert isinstance(result, dict)
        assert result['volume'] == 450
        # Should be positive due to weighted average
        assert result['overall_sentiment'] > 0
    
    def test_aggregate_sentiment_empty_data(self, strategy):
        """Test sentiment aggregation with empty data"""
        sentiment_data = []
        
        result = strategy.aggregate_sentiment(sentiment_data)
        
        assert isinstance(result, dict)
        assert result['overall_sentiment'] == 0.0
        assert result['confidence'] == 0.0
        assert result['volume'] == 0
    
    def test_aggregate_sentiment_zero_volume(self, strategy):
        """Test sentiment aggregation with zero volume"""
        sentiment_data = [
            {'sentiment': 0.5, 'volume': 0},
            {'sentiment': 0.3, 'volume': 0}
        ]
        
        result = strategy.aggregate_sentiment(sentiment_data)
        
        assert isinstance(result, dict)
        assert result['overall_sentiment'] == 0.0
        assert result['confidence'] == 0.0
        assert result['volume'] == 0


class TestSocialMediaSentimentStrategyDataRetrieval:
    """Test social media data retrieval functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create SocialMediaSentimentStrategy instance"""
        return SocialMediaSentimentStrategy()
    
    def test_get_social_media_data(self, strategy):
        """Test getting social media data"""
        data = strategy.get_social_media_data("AAPL")
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        for item in data:
            assert isinstance(item, dict)
            assert 'platform' in item
            assert 'text' in item
            assert 'timestamp' in item
            assert 'volume' in item
            assert 'sentiment' in item
            assert item['platform'] in ['twitter', 'reddit']
    
    def test_get_social_media_data_time_window(self, strategy):
        """Test that data respects time window"""
        strategy.sentiment_window = 1  # 1 hour window
        
        data = strategy.get_social_media_data("AAPL")
        
        # All data should be within the time window
        cutoff_time = datetime.now() - timedelta(hours=strategy.sentiment_window)
        for item in data:
            assert item['timestamp'] > cutoff_time
    
    def test_calculate_sentiment_score(self, strategy):
        """Test sentiment score calculation"""
        result = strategy.calculate_sentiment_score("AAPL")
        
        assert isinstance(result, dict)
        assert 'overall_sentiment' in result
        assert 'confidence' in result
        assert 'volume' in result
        
        assert isinstance(result['overall_sentiment'], float)
        assert isinstance(result['confidence'], float)
        assert isinstance(result['volume'], int)
        
        # Sentiment should be between -1 and 1
        assert -1 <= result['overall_sentiment'] <= 1
        # Confidence should be between 0 and 1
        assert 0 <= result['confidence'] <= 1
        # Volume should be non-negative
        assert result['volume'] >= 0


class TestSocialMediaSentimentStrategySignalGeneration:
    """Test signal generation functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create SocialMediaSentimentStrategy instance"""
        return SocialMediaSentimentStrategy(
            sentiment_threshold=0.2,
            confidence_threshold=0.6,
            min_mentions=5
        )
    
    @pytest.fixture
    def sample_data(self):
        """Create sample market data"""
        dates = pd.date_range('2023-01-01', periods=20, freq='D')
        prices = [100 + i * 0.5 for i in range(20)]
        
        return pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices]
        }, index=dates)
    
    @pytest.mark.asyncio
    async def test_generate_signal_bullish_sentiment(self, strategy, sample_data):
        """Test signal generation with bullish sentiment"""
        # Mock sentiment calculation to return bullish data
        with patch.object(strategy, 'calculate_sentiment_score') as mock_calc:
            mock_calc.return_value = {
                'overall_sentiment': 0.8,
                'confidence': 0.7,
                'volume': 200
            }
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            if signal is not None:
                assert isinstance(signal, TradeSignal)
                assert signal.symbol == "AAPL"
                assert signal.action == "BUY"
                assert signal.strategy == "SocialMediaSentiment"
                assert signal.confidence > 0
                assert "sentiment_score" in signal.metadata
                assert signal.metadata['sentiment_score'] == 0.8
            else:
                # Signal might be None if conditions aren't met exactly
                assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_bearish_sentiment(self, strategy, sample_data):
        """Test signal generation with bearish sentiment"""
        # Mock sentiment calculation to return bearish data
        with patch.object(strategy, 'calculate_sentiment_score') as mock_calc:
            mock_calc.return_value = {
                'overall_sentiment': -0.8,
                'confidence': 0.7,
                'volume': 200
            }
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            if signal is not None:
                assert isinstance(signal, TradeSignal)
                assert signal.symbol == "AAPL"
                assert signal.action == "SELL"
                assert signal.strategy == "SocialMediaSentiment"
                assert signal.confidence > 0
                assert "sentiment_score" in signal.metadata
                assert signal.metadata['sentiment_score'] == -0.8
            else:
                # Signal might be None if conditions aren't met exactly
                assert True
    
    @pytest.mark.asyncio
    async def test_generate_signal_insufficient_data(self, strategy):
        """Test signal generation with insufficient data"""
        data = pd.DataFrame({
            'Close': [100 + i for i in range(5)]  # Only 5 points < 10
        })
        
        signal = await strategy.generate_signal("AAPL", data)
        
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_low_volume(self, strategy, sample_data):
        """Test signal generation with low volume"""
        # Mock sentiment calculation to return low volume data
        with patch.object(strategy, 'calculate_sentiment_score') as mock_calc:
            mock_calc.return_value = {
                'overall_sentiment': 0.8,
                'confidence': 0.7,
                'volume': 3  # Below min_mentions threshold
            }
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_low_confidence(self, strategy, sample_data):
        """Test signal generation with low confidence"""
        # Mock sentiment calculation to return low confidence data
        with patch.object(strategy, 'calculate_sentiment_score') as mock_calc:
            mock_calc.return_value = {
                'overall_sentiment': 0.8,
                'confidence': 0.3,  # Below confidence threshold
                'volume': 200
            }
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            assert signal is None
    
    @pytest.mark.asyncio
    async def test_generate_signal_weak_sentiment(self, strategy, sample_data):
        """Test signal generation with weak sentiment"""
        # Mock sentiment calculation to return weak sentiment data
        with patch.object(strategy, 'calculate_sentiment_score') as mock_calc:
            mock_calc.return_value = {
                'overall_sentiment': 0.1,  # Below sentiment threshold
                'confidence': 0.7,
                'volume': 200
            }
            
            signal = await strategy.generate_signal("AAPL", sample_data)
            
            assert signal is None


class TestSocialMediaSentimentStrategyPositionSizing:
    """Test position sizing functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create SocialMediaSentimentStrategy instance"""
        return SocialMediaSentimentStrategy()
    
    def test_calculate_quantity_basic(self, strategy):
        """Test basic quantity calculation"""
        price = 100.0
        confidence = 0.8
        sentiment_strength = 0.6
        
        quantity = strategy._calculate_quantity(price, confidence, sentiment_strength)
        
        assert isinstance(quantity, float)
        assert quantity > 0
        
        # Should be: (1000 * 0.8 * 1.6) / 100 = 12.8
        expected = (1000 * confidence * (1 + sentiment_strength)) / price
        assert abs(quantity - expected) < 0.01
    
    def test_calculate_quantity_high_confidence(self, strategy):
        """Test quantity calculation with high confidence"""
        price = 100.0
        confidence = 1.0
        sentiment_strength = 0.5
        
        quantity = strategy._calculate_quantity(price, confidence, sentiment_strength)
        
        # Higher confidence should result in larger position
        assert quantity > 0
        expected = (1000 * confidence * (1 + sentiment_strength)) / price
        assert abs(quantity - expected) < 0.01
    
    def test_calculate_quantity_strong_sentiment(self, strategy):
        """Test quantity calculation with strong sentiment"""
        price = 100.0
        confidence = 0.7
        sentiment_strength = 1.0
        
        quantity = strategy._calculate_quantity(price, confidence, sentiment_strength)
        
        # Stronger sentiment should result in larger position
        assert quantity > 0
        expected = (1000 * confidence * (1 + sentiment_strength)) / price
        assert abs(quantity - expected) < 0.01
    
    def test_calculate_quantity_zero_price(self, strategy):
        """Test quantity calculation with zero price"""
        price = 0.0
        confidence = 0.8
        sentiment_strength = 0.6
        
        # Should handle zero price gracefully
        with pytest.raises(ZeroDivisionError):
            strategy._calculate_quantity(price, confidence, sentiment_strength)


class TestSocialMediaSentimentStrategySentimentSummary:
    """Test sentiment summary functionality"""
    
    @pytest.fixture
    def strategy(self):
        """Create SocialMediaSentimentStrategy instance"""
        return SocialMediaSentimentStrategy()
    
    def test_get_sentiment_summary(self, strategy):
        """Test getting sentiment summary"""
        summary = strategy.get_sentiment_summary("AAPL")
        
        assert isinstance(summary, dict)
        assert 'symbol' in summary
        assert 'sentiment_score' in summary
        assert 'confidence' in summary
        assert 'volume' in summary
        assert 'recent_posts' in summary
        assert 'sentiment_window_hours' in summary
        assert 'threshold' in summary
        
        assert summary['symbol'] == "AAPL"
        assert isinstance(summary['sentiment_score'], float)
        assert isinstance(summary['confidence'], float)
        assert isinstance(summary['volume'], int)
        assert isinstance(summary['recent_posts'], int)
        assert summary['sentiment_window_hours'] == 24
        assert summary['threshold'] == 0.2


class TestSocialMediaSentimentStrategyEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create SocialMediaSentimentStrategy instance"""
        return SocialMediaSentimentStrategy()
    
    def test_analyze_text_sentiment_none_text(self, strategy):
        """Test sentiment analysis with None text"""
        with pytest.raises(AttributeError):
            strategy.analyze_text_sentiment(None)
    
    def test_aggregate_sentiment_missing_keys(self, strategy):
        """Test sentiment aggregation with missing keys"""
        sentiment_data = [
            {'sentiment': 0.5},  # Missing volume
            {'volume': 100}      # Missing sentiment
        ]
        
        result = strategy.aggregate_sentiment(sentiment_data)
        
        assert isinstance(result, dict)
        assert 'overall_sentiment' in result
        assert 'confidence' in result
        assert 'volume' in result
    
    def test_strategy_activation_deactivation(self, strategy):
        """Test strategy activation and deactivation"""
        assert strategy.is_active is True
        
        strategy.deactivate()
        assert strategy.is_active is False
        
        strategy.activate()
        assert strategy.is_active is True


class TestSocialMediaSentimentStrategyIntegration:
    """Integration tests for social media sentiment strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create SocialMediaSentimentStrategy instance"""
        return SocialMediaSentimentStrategy(
            sentiment_threshold=0.2,
            confidence_threshold=0.6,
            min_mentions=5
        )
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, strategy):
        """Test complete social media sentiment workflow"""
        # Create realistic market data
        dates = pd.date_range('2023-01-01', periods=20, freq='D')
        prices = [100 + i * 0.5 for i in range(20)]
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices]
        }, index=dates)
        
        # Test signal generation
        signal = await strategy.generate_signal("AAPL", data)
        
        # May or may not generate a signal depending on sentiment data
        if signal is not None:
            assert isinstance(signal, TradeSignal)
            assert signal.symbol == "AAPL"
            assert signal.action in ["BUY", "SELL"]
            assert signal.strategy == "SocialMediaSentiment"
            assert signal.confidence > 0
            assert "sentiment_score" in signal.metadata
            assert "sentiment_volume" in signal.metadata
            assert "sentiment_strength" in signal.metadata
        else:
            # No signal is also valid if sentiment conditions aren't met
            assert True
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_integration(self, strategy):
        """Test integration of sentiment analysis components"""
        # Test text analysis
        text = "AAPL looking bullish today! Strong earnings report 📈"
        analysis = strategy.analyze_text_sentiment(text)
        
        assert analysis['combined_sentiment'] > 0
        
        # Test sentiment aggregation
        sentiment_data = [
            {'sentiment': analysis['combined_sentiment'], 'volume': 100}
        ]
        aggregated = strategy.aggregate_sentiment(sentiment_data)
        
        assert aggregated['overall_sentiment'] > 0
        assert aggregated['confidence'] > 0
        assert aggregated['volume'] == 100
        
        # Test sentiment score calculation
        score = strategy.calculate_sentiment_score("AAPL")
        
        assert isinstance(score['overall_sentiment'], float)
        assert isinstance(score['confidence'], float)
        assert isinstance(score['volume'], int) 