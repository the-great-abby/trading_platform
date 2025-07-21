# 🤖 LLM Proxy Timeout Handling Strategy

## 📊 **Current Timeout Architecture**

### **🔄 Multi-Layer Timeout Handling**

Our LLM proxy system implements a comprehensive timeout strategy across multiple layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIMEOUT HANDLING LAYERS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🎯 CLIENT LAYER (LLMClient)                                  │
│  ├─ Request Timeout: 30s (configurable)                       │
│  ├─ Max Retries: 3 (configurable)                             │
│  ├─ Retry Delay: Exponential backoff                          │
│  └─ Health Check: 60s interval                                │
│                                                                 │
│  🔧 SERVICE LAYER (LLMService)                                │
│  ├─ Operation Timeout: 30s                                    │
│  ├─ Callback Timeout: Configurable per request                │
│  ├─ Rate Limiting: 100 req/min                                │
│  └─ Cache TTL: 300s (5 minutes)                              │
│                                                                 │
│  🤖 OLLAMA LAYER (OllamaService)                             │
│  ├─ API Timeout: 120s (configurable)                          │
│  ├─ Max Retries: 3 (configurable)                             │
│  ├─ Base Delay: 10s                                           │
│  └─ Max Delay: 300s                                           │
│                                                                 │
│  📡 PROXY LAYER (LLM Proxy)                                  │
│  ├─ External Timeout: 120s                                    │
│  ├─ Internal Timeout: 30s                                     │
│  ├─ Callback URLs: Success/Timeout                            │
│  └─ Fire-and-Forget: Async processing                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## ⚡ **Timeout Configuration**

### **🔧 Environment Variables**

```bash
# LLM Client Configuration
LLM_TIMEOUT=30                    # Request timeout in seconds
LLM_MAX_RETRIES=3                 # Maximum retry attempts
LLM_RATE_LIMIT=100                # Requests per minute
LLM_CACHE_TTL=300                 # Cache TTL in seconds

# Ollama Service Configuration
OLLAMA_TIMEOUT=120.0              # Ollama API timeout
OLLAMA_MAX_RETRIES=3              # Ollama retry attempts
OLLAMA_BASE_DELAY=10.0            # Base retry delay
OLLAMA_MAX_DELAY=300.0            # Maximum retry delay

# Proxy Configuration
LLM_PROXY_TIMEOUT=30              # Proxy request timeout
LLM_PROXY_CALLBACK_TIMEOUT=60     # Callback timeout
```

### **📋 Timeout Configuration Table**

| Component | Default Timeout | Configurable | Retry Strategy |
|-----------|----------------|--------------|----------------|
| LLM Client | 30s | ✅ | Exponential backoff |
| LLM Service | 30s | ✅ | Fixed retries |
| Ollama Service | 120s | ✅ | Exponential backoff |
| LLM Proxy | 30s | ✅ | Callback-based |
| Health Check | 60s | ✅ | Periodic |

## 🚨 **Timeout Error Handling**

### **🎯 Error Types & Responses**

```python
# Timeout Error Types
TIMEOUT_ERRORS = {
    "timeout": {
        "status_code": 408,
        "error_message": "Request timeout",
        "retry_strategy": "exponential_backoff"
    },
    "service_unavailable": {
        "status_code": 503,
        "error_message": "LLM proxy service is not available",
        "retry_strategy": "health_check"
    },
    "rate_limit_exceeded": {
        "status_code": 429,
        "error_message": "Rate limit exceeded",
        "retry_strategy": "delay_and_retry"
    },
    "connection_error": {
        "status_code": 0,
        "error_message": "Connection failed",
        "retry_strategy": "exponential_backoff"
    }
}
```

### **🔄 Retry Strategies**

#### **1. Exponential Backoff**
```python
async def exponential_backoff_retry(self, attempt: int) -> float:
    """Calculate delay for exponential backoff"""
    base_delay = self.retry_delay
    max_delay = 300  # 5 minutes
    delay = min(base_delay * (2 ** attempt), max_delay)
    return delay
```

#### **2. Health Check Retry**
```python
async def health_check_retry(self) -> bool:
    """Retry after health check"""
    if await self.health_check():
        return True
    await asyncio.sleep(self.health_check_interval)
    return False
```

#### **3. Rate Limit Retry**
```python
async def rate_limit_retry(self) -> bool:
    """Retry after rate limit delay"""
    await asyncio.sleep(self.rate_limit_window)
    return await self._rate_limit_check()
```

## 📡 **Callback-Based Timeout Handling**

### **🎯 Fire-and-Forget with Callbacks**

```python
# Callback Configuration
callback_config = ProxyCallbackConfig(
    success_url="http://localhost:8080/api/llm/success",
    timeout_url="http://localhost:8080/api/llm/timeout",
    timeout_seconds=60,
    metadata={
        "request_type": "trade_evaluation",
        "priority": "high"
    }
)

# Request with Callback
request = LLMRequest(
    model="gemma3:1b",
    messages=[{"role": "user", "content": "Analyze this trade signal"}],
    task_type=LLMTaskType.SIGNAL_ANALYSIS,
    proxy_callback=callback_config
)
```

### **📊 Callback Flow**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLIENT        │    │   LLM PROXY     │    │   CALLBACK      │
│   REQUEST       │───►│   PROCESSING    │───►│   HANDLER       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TIMEOUT       │    │   SUCCESS       │    │   TIMEOUT       │
│   CALLBACK      │    │   CALLBACK      │    │   CALLBACK      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 **Implementation Examples**

### **🎯 Client-Side Timeout Handling**

```python
async def handle_llm_timeout(self, request: LLMRequest) -> LLMResponse:
    """Handle LLM timeout with fallback strategy"""
    
    # Try direct Ollama call as fallback
    try:
        ollama_service = OllamaService(
            base_url="http://localhost:11434",
            model=request.model
        )
        
        # Convert messages to prompt
        prompt = self._messages_to_prompt(request.messages)
        
        # Call Ollama directly with shorter timeout
        response = await asyncio.wait_for(
            ollama_service._call_ollama(prompt),
            timeout=15.0  # Shorter timeout for fallback
        )
        
        return LLMResponse(
            request_id=request.request_id,
            content=response,
            model=request.model,
            response_time=0.0,
            timestamp=datetime.utcnow(),
            callback_urls_configured=False
        )
        
    except Exception as e:
        logger.error(f"Fallback LLM call failed: {e}")
        return self._create_fallback_response(request)
```

### **🔄 Service-Side Timeout Handling**

```python
async def handle_service_timeout(self, operation: str, data: Dict) -> Dict:
    """Handle service-level timeout with operation-specific fallbacks"""
    
    fallback_strategies = {
        'sentiment': self._fallback_sentiment_analysis,
        'signal': self._fallback_signal_evaluation,
        'risk': self._fallback_risk_assessment,
        'market': self._fallback_market_analysis
    }
    
    fallback_handler = fallback_strategies.get(operation)
    if fallback_handler:
        return await fallback_handler(data)
    else:
        return self._generic_fallback(data)
```

### **📊 Monitoring & Metrics**

```python
class TimeoutMetrics:
    """Track timeout-related metrics"""
    
    def __init__(self):
        self.metrics = {
            'total_timeouts': 0,
            'timeout_by_component': {
                'client': 0,
                'service': 0,
                'ollama': 0,
                'proxy': 0
            },
            'retry_success_rate': 0.0,
            'fallback_usage': 0,
            'average_timeout_duration': 0.0
        }
    
    async def record_timeout(self, component: str, duration: float):
        """Record a timeout event"""
        self.metrics['total_timeouts'] += 1
        self.metrics['timeout_by_component'][component] += 1
        
        # Update average duration
        current_avg = self.metrics['average_timeout_duration']
        total_timeouts = self.metrics['total_timeouts']
        self.metrics['average_timeout_duration'] = (
            (current_avg * (total_timeouts - 1) + duration) / total_timeouts
        )
```

## 🚀 **Best Practices**

### **✅ Recommended Timeout Values**

| Use Case | Client Timeout | Service Timeout | Ollama Timeout | Retries |
|----------|----------------|-----------------|----------------|---------|
| Real-time Trading | 5s | 10s | 15s | 2 |
| Market Analysis | 15s | 30s | 60s | 3 |
| Backtesting | 30s | 60s | 120s | 3 |
| Batch Processing | 60s | 120s | 300s | 5 |

### **🔄 Retry Strategy Guidelines**

1. **Exponential Backoff**: Use for network-related timeouts
2. **Fixed Retries**: Use for service-level timeouts
3. **Health Check**: Use for service unavailability
4. **Rate Limit**: Use for rate limit exceeded errors

### **📊 Monitoring Guidelines**

1. **Track timeout rates by component**
2. **Monitor retry success rates**
3. **Alert on high timeout frequencies**
4. **Log timeout durations for optimization**

## 🔧 **Configuration Examples**

### **🎯 High-Performance Configuration**

```python
# For real-time trading
LLM_TIMEOUT=5
LLM_MAX_RETRIES=2
OLLAMA_TIMEOUT=15.0
OLLAMA_MAX_RETRIES=2
```

### **📊 Batch Processing Configuration**

```python
# For backtesting and analysis
LLM_TIMEOUT=60
LLM_MAX_RETRIES=5
OLLAMA_TIMEOUT=300.0
OLLAMA_MAX_RETRIES=3
```

### **🔄 Development Configuration**

```python
# For development and testing
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3
OLLAMA_TIMEOUT=120.0
OLLAMA_MAX_RETRIES=3
```

This comprehensive timeout handling strategy ensures reliable LLM proxy operation across all use cases while providing appropriate fallbacks and monitoring capabilities. 