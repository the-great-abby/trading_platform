#!/usr/bin/env python3
"""
Test LLMError class
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.llm_service.llm_client import LLMError, LLMResponse, LLMRequest, LLMTaskType
from datetime import datetime

def test_llm_error():
    """Test LLMError creation"""
    print("Testing LLMError creation...")
    
    try:
        # Test with all parameters
        error = LLMError(
            request_id="test-123",
            error_type="test_error",
            error_message="Test error message",
            status_code=500,
            timestamp=datetime.utcnow(),
            metadata={"test": True},
            callback_urls_configured=False
        )
        print(f"✅ LLMError created successfully: {error}")
        
        # Test with minimal parameters (should use __post_init__)
        error2 = LLMError(
            request_id="test-456",
            error_type="test_error2",
            error_message="Test error message 2",
            status_code=400,
            timestamp=None  # Should be set by __post_init__
        )
        print(f"✅ LLMError with minimal params created: {error2}")
        print(f"   Timestamp: {error2.timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLMError creation failed: {e}")
        return False

def test_llm_response():
    """Test LLMResponse creation"""
    print("\nTesting LLMResponse creation...")
    
    try:
        response = LLMResponse(
            request_id="test-789",
            model="gpt-3.5-turbo",
            content="Test response",
            task_type=LLMTaskType.SENTIMENT_ANALYSIS,
            usage={"tokens": 10},
            finish_reason="stop",
            response_time=1.5,
            timestamp=datetime.utcnow(),
            metadata={"test": True},
            callback_urls_configured=True
        )
        print(f"✅ LLMResponse created successfully: {response}")
        return True
        
    except Exception as e:
        print(f"❌ LLMResponse creation failed: {e}")
        return False

def test_llm_request():
    """Test LLMRequest creation"""
    print("\nTesting LLMRequest creation...")
    
    try:
        request = LLMRequest(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            task_type=LLMTaskType.SENTIMENT_ANALYSIS
        )
        print(f"✅ LLMRequest created successfully: {request}")
        print(f"   Request ID: {request.request_id}")
        return True
        
    except Exception as e:
        print(f"❌ LLMRequest creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing LLM Classes")
    print("=" * 40)
    
    success = True
    success &= test_llm_error()
    success &= test_llm_response()
    success &= test_llm_request()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!") 