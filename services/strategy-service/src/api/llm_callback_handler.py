"""
LLM Callback Handler API
Handles callback notifications from LLM proxy for timeouts and successful completions
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router for callback endpoints
router = APIRouter(prefix="/api/llm", tags=["llm-callbacks"])


class CallbackPayload(BaseModel):
    """Callback payload from LLM proxy"""
    request_id: str
    status: str  # "success" or "timeout"
    timestamp: str
    model: Optional[str] = None
    content: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    response_time: Optional[float] = None


class TimeoutCallbackPayload(BaseModel):
    """Timeout callback payload"""
    request_id: str
    timeout_reason: str
    timestamp: str
    model: Optional[str] = None
    metadata: Dict[str, Any] = {}
    elapsed_time: Optional[float] = None


# Global callback handlers
callback_handlers: Dict[str, callable] = {}
timeout_handlers: Dict[str, callable] = {}


def register_callback_handler(request_id: str, handler: callable):
    """Register a callback handler for a specific request"""
    callback_handlers[request_id] = handler
    logger.info(f"Registered callback handler for request: {request_id}")


def register_timeout_handler(request_id: str, handler: callable):
    """Register a timeout handler for a specific request"""
    timeout_handlers[request_id] = handler
    logger.info(f"Registered timeout handler for request: {request_id}")


@router.post("/success")
async def handle_success_callback(payload: CallbackPayload):
    """Handle successful LLM completion callback"""
    try:
        logger.info(f"✅ Success callback received for request: {payload.request_id}")
        logger.info(f"   Model: {payload.model}")
        logger.info(f"   Response time: {payload.response_time:.2f}s")
        logger.info(f"   Content length: {len(payload.content) if payload.content else 0}")
        
        # Execute registered handler if exists
        if payload.request_id in callback_handlers:
            try:
                await callback_handlers[payload.request_id](payload)
                logger.info(f"✅ Success handler executed for request: {payload.request_id}")
            except Exception as e:
                logger.error(f"❌ Success handler failed for request {payload.request_id}: {e}")
        else:
            logger.warning(f"⚠️  No success handler registered for request: {payload.request_id}")
        
        # Store result in cache/database for later retrieval
        await store_success_result(payload)
        
        return {"status": "success", "message": "Success callback processed"}
        
    except Exception as e:
        logger.error(f"❌ Error processing success callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timeout")
async def handle_timeout_callback(payload: TimeoutCallbackPayload):
    """Handle LLM timeout callback"""
    try:
        logger.warning(f"⏰ Timeout callback received for request: {payload.request_id}")
        logger.warning(f"   Model: {payload.model}")
        logger.warning(f"   Elapsed time: {payload.elapsed_time:.2f}s")
        logger.warning(f"   Timeout reason: {payload.timeout_reason}")
        
        # Execute registered timeout handler if exists
        if payload.request_id in timeout_handlers:
            try:
                await timeout_handlers[payload.request_id](payload)
                logger.info(f"✅ Timeout handler executed for request: {payload.request_id}")
            except Exception as e:
                logger.error(f"❌ Timeout handler failed for request {payload.request_id}: {e}")
        else:
            logger.warning(f"⚠️  No timeout handler registered for request: {payload.request_id}")
        
        # Execute fallback strategy
        fallback_result = await execute_fallback_strategy(payload)
        
        # Store timeout result
        await store_timeout_result(payload, fallback_result)
        
        return {"status": "success", "message": "Timeout callback processed", "fallback_result": fallback_result}
        
    except Exception as e:
        logger.error(f"❌ Error processing timeout callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def store_success_result(payload: CallbackPayload):
    """Store successful LLM result"""
    try:
        # Store in Redis cache
        cache_key = f"llm_result:{payload.request_id}"
        result_data = {
            "status": "success",
            "content": payload.content,
            "model": payload.model,
            "response_time": payload.response_time,
            "timestamp": payload.timestamp,
            "metadata": payload.metadata
        }
        
        # This would be implemented with your actual cache/database
        logger.info(f"📊 Stored success result for request: {payload.request_id}")
        
    except Exception as e:
        logger.error(f"❌ Error storing success result: {e}")


async def store_timeout_result(payload: TimeoutCallbackPayload, fallback_result: Dict[str, Any]):
    """Store timeout result with fallback"""
    try:
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
        
        # This would be implemented with your actual cache/database
        logger.info(f"📊 Stored timeout result for request: {payload.request_id}")
        
    except Exception as e:
        logger.error(f"❌ Error storing timeout result: {e}")


async def execute_fallback_strategy(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    """Execute fallback strategy for timeout"""
    try:
        logger.info(f"🔄 Executing fallback strategy for request: {payload.request_id}")
        
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
        logger.info(f"✅ Fallback strategy completed for request: {payload.request_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Fallback strategy failed for request {payload.request_id}: {e}")
        return await execute_emergency_fallback(payload)


async def execute_sentiment_fallback(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    """Execute sentiment analysis fallback"""
    return {
        "sentiment": "neutral",
        "confidence": 0.5,
        "reason": "LLM timeout - using neutral sentiment",
        "fallback_type": "sentiment",
        "timestamp": datetime.utcnow().isoformat()
    }


async def execute_signal_fallback(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    """Execute trading signal fallback"""
    return {
        "signal": "HOLD",
        "confidence": 0.5,
        "reason": "LLM timeout - using conservative signal",
        "fallback_type": "signal",
        "timestamp": datetime.utcnow().isoformat()
    }


async def execute_risk_fallback(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    """Execute risk assessment fallback"""
    return {
        "risk_level": "medium",
        "confidence": 0.5,
        "reason": "LLM timeout - using medium risk assessment",
        "fallback_type": "risk",
        "timestamp": datetime.utcnow().isoformat()
    }


async def execute_market_fallback(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    """Execute market analysis fallback"""
    return {
        "market_outlook": "neutral",
        "confidence": 0.5,
        "reason": "LLM timeout - using neutral market outlook",
        "fallback_type": "market",
        "timestamp": datetime.utcnow().isoformat()
    }


async def execute_trade_evaluation_fallback(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    """Execute trade evaluation fallback"""
    return {
        "recommendation": "HOLD",
        "confidence": 0.5,
        "reason": "LLM timeout - using conservative trade evaluation",
        "fallback_type": "trade_evaluation",
        "timestamp": datetime.utcnow().isoformat()
    }


async def execute_generic_fallback(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    """Execute generic fallback"""
    return {
        "recommendation": "SKIP",
        "confidence": 0.0,
        "reason": "LLM timeout - no specific fallback available",
        "fallback_type": "generic",
        "timestamp": datetime.utcnow().isoformat()
    }


async def execute_emergency_fallback(payload: TimeoutCallbackPayload) -> Dict[str, Any]:
    """Execute emergency fallback when all else fails"""
    return {
        "recommendation": "SKIP",
        "confidence": 0.0,
        "reason": "LLM service unavailable - emergency fallback",
        "fallback_type": "emergency",
        "timestamp": datetime.utcnow().isoformat()
    }


# Health check endpoint for callback service
@router.get("/callback/health")
async def callback_health_check():
    """Health check for callback service"""
    return {
        "status": "healthy",
        "service": "llm-callback-handler",
        "timestamp": datetime.utcnow().isoformat(),
        "registered_handlers": {
            "success_handlers": len(callback_handlers),
            "timeout_handlers": len(timeout_handlers)
        }
    }


# Metrics endpoint
@router.get("/callback/metrics")
async def callback_metrics():
    """Get callback metrics"""
    return {
        "registered_handlers": {
            "success_handlers": len(callback_handlers),
            "timeout_handlers": len(timeout_handlers)
        },
        "handler_ids": {
            "success": list(callback_handlers.keys()),
            "timeout": list(timeout_handlers.keys())
        },
        "timestamp": datetime.utcnow().isoformat()
    } 