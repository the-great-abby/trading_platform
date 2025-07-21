# 🔄 LLM Proxy Timeout Flow - What Happens When Timeout Occurs

## 📊 **Complete Timeout Flow Diagram**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LLM PROXY TIMEOUT FLOW                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1️⃣ CLIENT REQUEST                                                           │
│  ┌─────────────────┐                                                          │
│  │ Trading System  │                                                          │
│  │ Sends Request   │                                                          │
│  │ with Callback   │                                                          │
│  │ URLs            │                                                          │
│  └─────────────────┘                                                          │
│           │                                                                   │
│           ▼                                                                   │
│  ┌─────────────────┐                                                          │
│  │ LLM Proxy       │                                                          │
│  │ Receives Request│                                                          │
│  │ Starts Timer    │                                                          │
│  │ Begins Processing│                                                         │
│  └─────────────────┘                                                          │
│           │                                                                   │
│           ▼                                                                   │
│  ┌─────────────────┐                                                          │
│  │ Ollama Service  │                                                          │
│  │ Processes LLM   │                                                          │
│  │ Request         │                                                          │
│  └─────────────────┘                                                          │
│           │                                                                   │
│           ▼                                                                   │
│  ⏰ TIMEOUT OCCURS                                                            │
│  ┌─────────────────┐                                                          │
│  │ LLM Proxy       │                                                          │
│  │ Detects Timeout │                                                          │
│  │ Stops Processing│                                                          │
│  │ Calls Timeout   │                                                          │
│  │ URL             │                                                          │
│  └─────────────────┘                                                          │
│           │                                                                   │
│           ▼                                                                   │
│  ┌─────────────────┐                                                          │
│  │ Our System      │                                                          │
│  │ Receives Timeout│                                                          │
│  │ Callback        │                                                          │
│  └─────────────────┘                                                          │
│           │                                                                   │
│           ▼                                                                   │
│  ┌─────────────────┐                                                          │
│  │ Callback Handler│                                                          │
│  │ Processes       │                                                          │
│  │ Timeout         │                                                          │
│  └─────────────────┘                                                          │
│           │                                                                   │
│           ▼                                                                   │
│  ┌─────────────────┐                                                          │
│  │ Fallback        │                                                          │
│  │ Strategy        │                                                          │
│  │ Executed        │                                                          │
│  └─────────────────┘                                                          │
│           │                                                                   │
│           ▼                                                                   │
│  ┌─────────────────┐                                                          │
│  │ Result Stored   │                                                          │
│  │ in Cache/DB     │                                                          │
│  └─────────────────┘                                                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🎯 **Detailed Step-by-Step Process**

### **1️⃣ Initial Request Setup**

```python
# Client sends request with callback URLs
request = LLMRequest(
    model="gemma3:1b",
    messages=[{"role": "user", "content": "Analyze this complex trading signal"}],
    task_type=LLMTaskType.SIGNAL_ANALYSIS,
    proxy_callback=ProxyCallbackConfig(
        success_url="http://localhost:8080/api/llm/success",
        timeout_url="http://localhost:8080/api/llm/timeout",
        timeout_seconds=30,
        metadata={
            "request_type": "trade_evaluation",
            "priority": "high",
            "user_id": "trader_123"
        }
    )
)
```

### **2️⃣ LLM Proxy Processing**

```python
# LLM Proxy receives request and starts processing
proxy_payload = {
    "model": "gemma3:1b",
    "prompt": "Analyze this complex trading signal...",
    "callback_url": "http://localhost:8080/api/llm/success",
    "timeout_url": "http://localhost:8080/api/llm/timeout",
    "timeout_seconds": 30,
    "metadata": {
        "request_type": "trade_evaluation",
        "priority": "high"
    }
}

# Proxy starts timer and begins processing
start_time = time.time()
# ... LLM processing happens ...
```

### **3️⃣ Timeout Detection**

```python
# LLM Proxy detects timeout
if time.time() - start_time > timeout_seconds:
    logger.warning(f"⏰ Request {request_id} timed out after {timeout_seconds}s")
    
    # Prepare timeout callback payload
    timeout_payload = {
        "request_id": request_id,
        "timeout_reason": "LLM processing exceeded time limit",
        "timestamp": datetime.utcnow().isoformat(),
        "model": "gemma3:1b",
        "metadata": {
            "request_type": "trade_evaluation",
            "priority": "high"
        },
        "elapsed_time": time.time() - start_time
    }
    
    # Call timeout URL
    await call_timeout_url(timeout_url, timeout_payload)
```

### **4️⃣ Our System Receives Timeout Callback**

```python
# Our callback endpoint receives the timeout notification
@router.post("/api/llm/timeout")
async def handle_timeout_callback(payload: TimeoutCallbackPayload):
    logger.warning(f"⏰ Timeout callback received for request: {payload.request_id}")
    logger.warning(f"   Model: {payload.model}")
    logger.warning(f"   Elapsed time: {payload.elapsed_time:.2f}s")
    logger.warning(f"   Timeout reason: {payload.timeout_reason}")
    
    # Execute registered timeout handler if exists
    if payload.request_id in timeout_handlers:
        await timeout_handlers[payload.request_id](payload)
    
    # Execute fallback strategy
    fallback_result = await execute_fallback_strategy(payload)
    
    # Store timeout result
    await store_timeout_result(payload, fallback_result)
    
    return {
        "status": "success", 
        "message": "Timeout callback processed", 
        "fallback_result": fallback_result
    }
```

### **5️⃣ Fallback Strategy Execution**

```python
async def execute_fallback_strategy(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    # Determine fallback strategy based on metadata
    request_type = payload.metadata.get("request_type", "unknown")
    
    fallback_strategies = {
        "sentiment": execute_sentiment_fallback,
        "signal": execute_signal_fallback,
        "risk": execute_risk_fallback,
        "market": execute_market_fallback,
        "trade_evaluation": execute_trade_evaluation_fallback
    }
    
    fallback_handler = fallback_strategies.get(request_type, execute_generic_fallback)
    result = await fallback_handler(payload)
    
    return result

# For trade evaluation timeout:
async def execute_trade_evaluation_fallback(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    return {
        "recommendation": "HOLD",
        "confidence": 0.5,
        "reason": "LLM timeout - using conservative trade evaluation",
        "fallback_type": "trade_evaluation",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### **6️⃣ Result Storage**

```python
async def store_timeout_result(payload: TimeoutCallbackPayload, fallback_result: Dict[str, Any]):
    # Store in Redis cache
    cache_key = f"llm_result:{payload.request_id}"
    result_data = {
        "status": "timeout",
        "timeout_reason": payload.timeout_reason,
        "elapsed_time": payload.elapsed_time,
        "fallback_result": fallback_result,
        "timestamp": payload.timestamp,
        "metadata": payload.metadata
    }
    
    # Store in cache for later retrieval
    await redis_client.setex(cache_key, 3600, json.dumps(result_data))
    logger.info(f"📊 Stored timeout result for request: {payload.request_id}")
```

## 🔧 **What Happens Next**

### **📊 Result Retrieval**

```python
# Client can retrieve the result later
async def get_llm_result(request_id: str) -> Dict[str, Any]:
    cache_key = f"llm_result:{request_id}"
    result_data = await redis_client.get(cache_key)
    
    if result_data:
        return json.loads(result_data)
    else:
        return {"status": "not_found", "message": "Result not available"}
```

### **🔄 Trading System Response**

```python
# Trading system receives fallback result
result = await get_llm_result(request_id)

if result["status"] == "timeout":
    # Use fallback result for trading decision
    recommendation = result["fallback_result"]["recommendation"]
    confidence = result["fallback_result"]["confidence"]
    reason = result["fallback_result"]["reason"]
    
    logger.info(f"📊 Using fallback result: {recommendation} (confidence: {confidence})")
    logger.info(f"   Reason: {reason}")
    
    # Execute trading decision based on fallback
    await execute_trading_decision(recommendation, confidence)
```

## 🚨 **Error Handling Scenarios**

### **1️⃣ Callback URL Unreachable**

```python
# If our callback URL is down
try:
    await call_timeout_url(timeout_url, timeout_payload)
except Exception as e:
    logger.error(f"❌ Failed to call timeout URL: {e}")
    # LLM proxy logs the failure but continues
    # No fallback executed on our side
```

### **2️⃣ Fallback Strategy Failure**

```python
async def execute_fallback_strategy(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    try:
        # ... fallback logic ...
        return result
    except Exception as e:
        logger.error(f"❌ Fallback strategy failed: {e}")
        return await execute_emergency_fallback(payload)
```

### **3️⃣ Storage Failure**

```python
async def store_timeout_result(payload: TimeoutCallbackPayload, fallback_result: Dict[str, Any]):
    try:
        # ... storage logic ...
        logger.info(f"📊 Stored timeout result for request: {payload.request_id}")
    except Exception as e:
        logger.error(f"❌ Failed to store timeout result: {e}")
        # Result is lost but fallback was still executed
```

## 📈 **Monitoring & Metrics**

### **📊 Timeout Metrics**

```python
# Track timeout events
timeout_metrics = {
    "total_timeouts": 0,
    "timeout_by_request_type": {},
    "average_elapsed_time": 0.0,
    "fallback_success_rate": 0.0,
    "callback_failure_rate": 0.0
}

# Update metrics on timeout
def update_timeout_metrics(payload: TimeoutCallbackPayload):
    timeout_metrics["total_timeouts"] += 1
    request_type = payload.metadata.get("request_type", "unknown")
    timeout_metrics["timeout_by_request_type"][request_type] = \
        timeout_metrics["timeout_by_request_type"].get(request_type, 0) + 1
```

### **🚨 Alerts**

```python
# Alert on high timeout rates
if timeout_metrics["total_timeouts"] > 10:
    send_alert("High LLM timeout rate detected")
    
# Alert on callback failures
if timeout_metrics["callback_failure_rate"] > 0.1:
    send_alert("LLM callback failures detected")
```

This comprehensive flow ensures that when the LLM proxy times out, our system gracefully handles the timeout, executes appropriate fallbacks, and continues trading operations with conservative decisions. 