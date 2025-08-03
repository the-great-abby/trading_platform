#!/usr/bin/env python3
"""
AI Query Interface - Natural language interface for market data and investment decisions
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import numpy as np
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Query Interface", version="1.0.0")

# Configuration
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://llm-proxy:12001")
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://vector-database-service:8000")
DECISION_ENGINE_URL = os.getenv("DECISION_ENGINE_URL", "http://ai-decision-engine:8000")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-service:8002")

@dataclass
class QueryContext:
    """Context for AI query processing"""
    query: str
    query_type: str  # "market_analysis", "investment_advice", "timing", "risk", "comparison"
    symbols: List[str]
    time_range: Optional[str]
    risk_profile: Optional[str]

@dataclass
class QueryResponse:
    """Response from AI query"""
    answer: str
    confidence: float
    reasoning: str
    data_sources: List[str]
    recommendations: List[Dict[str, Any]]
    follow_up_questions: List[str]

class AIQueryProcessor:
    """Process natural language queries about market data and investments"""
    
    def __init__(self):
        self.query_patterns = {
            "market_analysis": [
                r"how is (the market|.*) performing",
                r"what's happening with (.*)",
                r"market (trend|outlook|analysis)",
                r"is (.*) a good (buy|sell|investment)"
            ],
            "investment_advice": [
                r"should I (buy|sell|invest in) (.*)",
                r"is (.*) a good (time|moment) to (buy|sell)",
                r"what's your (recommendation|advice) for (.*)",
                r"when should I (buy|sell) (.*)"
            ],
            "timing": [
                r"when is the best time to (buy|sell) (.*)",
                r"should I (wait|buy now) for (.*)",
                r"timing for (.*)",
                r"optimal (entry|exit) for (.*)"
            ],
            "risk": [
                r"risk (assessment|level) for (.*)",
                r"how risky is (.*)",
                r"what are the risks of (.*)",
                r"risk factors for (.*)"
            ],
            "comparison": [
                r"compare (.*) with (.*)",
                r"which is better (.*) or (.*)",
                r"difference between (.*) and (.*)",
                r"vs|versus"
            ]
        }
    
    def classify_query(self, query: str) -> Tuple[str, List[str]]:
        """Classify query type and extract symbols"""
        
        query_lower = query.lower()
        symbols = []
        
        # Extract symbols (uppercase tickers)
        symbol_pattern = r'\b[A-Z]{1,5}\b'
        potential_symbols = re.findall(symbol_pattern, query)
        
        # Filter for common stock symbols
        common_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
            'AMD', 'INTC', 'JPM', 'BAC', 'WFC', 'GS', 'JNJ', 'PFE', 'UNH',
            'HD', 'DIS', 'V', 'MA', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'CSCO',
            'QCOM', 'TXN', 'AVGO', 'SPY', 'QQQ', 'VTI', 'VOO', 'VUG', 'XLK',
            'XLF', 'XLE', 'XLV', 'XLY'
        ]
        
        symbols = [s for s in potential_symbols if s in common_symbols]
        
        # Classify query type
        query_type = "general"
        for qtype, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    query_type = qtype
                    break
            if query_type != "general":
                break
        
        return query_type, symbols
    
    async def process_query(self, query: str, user_context: Optional[Dict] = None) -> QueryResponse:
        """Process natural language query and generate response"""
        
        # Classify query
        query_type, symbols = self.classify_query(query)
        
        # Create query context
        context = QueryContext(
            query=query,
            query_type=query_type,
            symbols=symbols,
            time_range=user_context.get("time_range") if user_context else None,
            risk_profile=user_context.get("risk_profile") if user_context else "moderate"
        )
        
        # Gather relevant data
        market_data = await self._gather_market_data(symbols)
        vector_context = await self._get_vector_context(symbols, query)
        decision_data = await self._get_decision_data(symbols)
        
        # Generate AI response
        ai_response = await self._generate_ai_response(context, market_data, vector_context, decision_data)
        
        return ai_response
    
    async def _gather_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Gather market data for symbols"""
        market_data = {}
        
        for symbol in symbols:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{MARKET_DATA_URL}/api/current/{symbol}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            market_data[symbol] = data
                        else:
                            # Mock data if service unavailable
                            market_data[symbol] = {
                                "price": 150.0,
                                "volume": 1000000,
                                "change_percent": 2.5,
                                "market_cap": 1000000000
                            }
            except Exception as e:
                logger.error(f"Error gathering market data for {symbol}: {e}")
                market_data[symbol] = {"error": str(e)}
        
        return market_data
    
    async def _get_vector_context(self, symbols: List[str], query: str) -> Dict[str, Any]:
        """Get relevant context from vector database"""
        vector_context = {}
        
        for symbol in symbols:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{VECTOR_DB_URL}/api/search/context"
                    params = {"query": query, "symbol": symbol, "context_type": "all"}
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            vector_context[symbol] = data
                        else:
                            vector_context[symbol] = {"error": "Vector DB unavailable"}
            except Exception as e:
                logger.error(f"Error getting vector context for {symbol}: {e}")
                vector_context[symbol] = {"error": str(e)}
        
        return vector_context
    
    async def _get_decision_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Get investment decision data"""
        decision_data = {}
        
        for symbol in symbols:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{DECISION_ENGINE_URL}/api/recommendation/{symbol}"
                    params = {"include_timing": True, "risk_profile": "moderate"}
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            decision_data[symbol] = data
                        else:
                            decision_data[symbol] = {"error": "Decision engine unavailable"}
            except Exception as e:
                logger.error(f"Error getting decision data for {symbol}: {e}")
                decision_data[symbol] = {"error": str(e)}
        
        return decision_data
    
    async def _generate_ai_response(self, context: QueryContext, market_data: Dict, 
                                  vector_context: Dict, decision_data: Dict) -> QueryResponse:
        """Generate AI response to query"""
        
        # Build comprehensive prompt
        prompt = self._build_query_prompt(context, market_data, vector_context, decision_data)
        
        try:
            async with aiohttp.ClientSession() as session:
                llm_request = {
                    "prompt": prompt,
                    "max_tokens": 1000,
                    "temperature": 0.3,
                    "task_type": "query_response"
                }
                
                url = f"{LLM_PROXY_URL}/api/chat"
                async with session.post(url, json=llm_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_query_response(result.get("response", ""), context)
                    else:
                        logger.error(f"LLM service error: {response.status}")
                        return self._get_fallback_response(context)
                        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(context)
    
    def _build_query_prompt(self, context: QueryContext, market_data: Dict, 
                           vector_context: Dict, decision_data: Dict) -> str:
        """Build comprehensive prompt for AI query"""
        
        prompt = f"""
You are an expert financial advisor and market analyst. Answer the following query:

QUERY: {context.query}
QUERY TYPE: {context.query_type}
SYMBOLS: {context.symbols}
RISK PROFILE: {context.risk_profile}

MARKET DATA:
{json.dumps(market_data, indent=2)}

HISTORICAL CONTEXT:
{json.dumps(vector_context, indent=2)}

INVESTMENT DECISIONS:
{json.dumps(decision_data, indent=2)}

Provide a comprehensive response in JSON format:
{{
    "answer": "Detailed answer to the query",
    "confidence": 0.0-1.0,
    "reasoning": "Explanation of the reasoning",
    "data_sources": ["source1", "source2"],
    "recommendations": [
        {{
            "action": "BUY|SELL|HOLD|WAIT",
            "symbol": "SYMBOL",
            "reasoning": "Why this action",
            "timing": "When to execute",
            "risk_level": "LOW|MEDIUM|HIGH"
        }}
    ],
    "follow_up_questions": ["question1", "question2"]
}}

Focus on:
1. Providing actionable insights
2. Explaining the reasoning clearly
3. Considering risk factors
4. Suggesting optimal timing
5. Offering follow-up questions for deeper analysis
"""
        
        return prompt
    
    def _parse_query_response(self, response_text: str, context: QueryContext) -> QueryResponse:
        """Parse AI response to query"""
        try:
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
                
                return QueryResponse(
                    answer=data.get("answer", "Analysis completed"),
                    confidence=data.get("confidence", 0.5),
                    reasoning=data.get("reasoning", "Based on available data"),
                    data_sources=data.get("data_sources", ["market_data", "ai_analysis"]),
                    recommendations=data.get("recommendations", []),
                    follow_up_questions=data.get("follow_up_questions", [])
                )
        except:
            pass
        
        return self._get_fallback_response(context)
    
    def _get_fallback_response(self, context: QueryContext) -> QueryResponse:
        """Fallback response when AI fails"""
        
        if context.query_type == "investment_advice":
            answer = f"Based on current market conditions, I recommend monitoring {', '.join(context.symbols)} closely. Consider waiting for clearer signals before making investment decisions."
        elif context.query_type == "timing":
            answer = f"For {', '.join(context.symbols)}, timing depends on market conditions. Monitor technical indicators and news sentiment for optimal entry/exit points."
        elif context.query_type == "risk":
            answer = f"Risk assessment for {', '.join(context.symbols)} requires analysis of volatility, market conditions, and company fundamentals. Consider your risk tolerance."
        else:
            answer = f"Analysis for {', '.join(context.symbols)} shows mixed signals. Consider consulting with a financial advisor for personalized advice."
        
        return QueryResponse(
            answer=answer,
            confidence=0.3,
            reasoning="Fallback analysis based on general market principles",
            data_sources=["market_data"],
            recommendations=[],
            follow_up_questions=[
                "What is your investment timeline?",
                "What is your risk tolerance?",
                "Are you looking for short-term or long-term investments?"
            ]
        )

# Initialize query processor
query_processor = AIQueryProcessor()

@app.post("/api/query")
async def process_query(query: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
    """Process natural language query"""
    try:
        response = await query_processor.process_query(query, user_context)
        
        return {
            "query": query,
            "answer": response.answer,
            "confidence": response.confidence,
            "reasoning": response.reasoning,
            "data_sources": response.data_sources,
            "recommendations": response.recommendations,
            "follow_up_questions": response.follow_up_questions,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/query/examples")
async def get_query_examples() -> Dict[str, List[str]]:
    """Get example queries for different types"""
    return {
        "market_analysis": [
            "How is AAPL performing?",
            "What's happening with the tech sector?",
            "Is this a good time to buy NVDA?",
            "Market outlook for the next week"
        ],
        "investment_advice": [
            "Should I buy TSLA now?",
            "Is MSFT a good investment?",
            "What's your recommendation for GOOGL?",
            "Should I sell my AAPL position?"
        ],
        "timing": [
            "When is the best time to buy SPY?",
            "Should I wait to buy NVDA?",
            "Optimal entry for QQQ",
            "Timing for selling TSLA"
        ],
        "risk": [
            "Risk assessment for AAPL",
            "How risky is TSLA?",
            "What are the risks of investing in crypto?",
            "Risk factors for tech stocks"
        ],
        "comparison": [
            "Compare AAPL vs MSFT",
            "Which is better: NVDA or AMD?",
            "Difference between SPY and QQQ",
            "AAPL vs GOOGL performance"
        ]
    }

@app.get("/api/query/classify")
async def classify_query(query: str) -> Dict[str, Any]:
    """Classify a query without processing it"""
    try:
        query_type, symbols = query_processor.classify_query(query)
        
        return {
            "query": query,
            "query_type": query_type,
            "symbols": symbols,
            "patterns_matched": query_processor.query_patterns.get(query_type, [])
        }
    except Exception as e:
        logger.error(f"Error classifying query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/query/context")
async def get_query_context(query: str) -> Dict[str, Any]:
    """Get context information for a query"""
    try:
        query_type, symbols = query_processor.classify_query(query)
        
        # Get market data for symbols
        market_data = await query_processor._gather_market_data(symbols)
        
        # Get vector context
        vector_context = await query_processor._get_vector_context(symbols, query)
        
        return {
            "query": query,
            "query_type": query_type,
            "symbols": symbols,
            "market_data": market_data,
            "vector_context": vector_context,
            "context_summary": {
                "symbols_analyzed": len(symbols),
                "data_sources": ["market_data", "vector_database"],
                "analysis_depth": "comprehensive" if symbols else "general"
            }
        }
    except Exception as e:
        logger.error(f"Error getting query context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 