#!/usr/bin/env python3
"""
Data Pipeline Dashboard
Comprehensive dashboard for data transformation and analysis pipeline
"""

import os
import logging
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiohttp
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Pipeline Dashboard",
    description="Comprehensive dashboard for data transformation and analysis pipeline",
    version="1.0.0"
)

# Configuration
TRANSFORMATION_PIPELINE_URL = os.getenv("TRANSFORMATION_PIPELINE_URL", "http://data-transformation-pipeline:11135")
ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL", "http://data-analysis-service:11136")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://market-data-service:80")

# Templates
templates = Jinja2Templates(directory="templates")

class DataPipelineDashboard:
    """Main dashboard service"""
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get overall pipeline status"""
        try:
            status = {
                "transformation_pipeline": "unknown",
                "analysis_service": "unknown",
                "market_data_service": "unknown",
                "last_updated": datetime.now().isoformat()
            }
            
            # Check transformation pipeline
            try:
                async with self.session.get(f"{TRANSFORMATION_PIPELINE_URL}/health") as response:
                    if response.status == 200:
                        status["transformation_pipeline"] = "healthy"
                    else:
                        status["transformation_pipeline"] = "unhealthy"
            except Exception as e:
                status["transformation_pipeline"] = "error"
                logger.error(f"Error checking transformation pipeline: {e}")
            
            # Check analysis service
            try:
                async with self.session.get(f"{ANALYSIS_SERVICE_URL}/health") as response:
                    if response.status == 200:
                        status["analysis_service"] = "healthy"
                    else:
                        status["analysis_service"] = "unhealthy"
            except Exception as e:
                status["analysis_service"] = "error"
                logger.error(f"Error checking analysis service: {e}")
            
            # Check market data service
            try:
                async with self.session.get(f"{MARKET_DATA_URL}/health") as response:
                    if response.status == 200:
                        status["market_data_service"] = "healthy"
                    else:
                        status["market_data_service"] = "unhealthy"
            except Exception as e:
                status["market_data_service"] = "error"
                logger.error(f"Error checking market data service: {e}")
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {
                "transformation_pipeline": "error",
                "analysis_service": "error",
                "market_data_service": "error",
                "last_updated": datetime.now().isoformat()
            }
    
    async def get_sample_analysis(self) -> Dict[str, Any]:
        """Get sample analysis results"""
        try:
            # Sample stock analysis
            sample_data = {
                "stocks": {
                    "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
                    "analysis_types": ["technical", "risk", "sentiment"],
                    "sample_results": {
                        "AAPL": {
                            "technical": {
                                "rsi": 65.2,
                                "sma_20": 175.50,
                                "sma_50": 172.30,
                                "trend": "bullish",
                                "confidence": 0.75
                            },
                            "risk": {
                                "volatility": 0.28,
                                "beta": 1.15,
                                "risk_level": "moderate",
                                "confidence": 0.80
                            },
                            "sentiment": {
                                "score": 0.65,
                                "label": "positive",
                                "confidence": 0.70
                            }
                        },
                        "GOOGL": {
                            "technical": {
                                "rsi": 58.7,
                                "sma_20": 2850.00,
                                "sma_50": 2820.00,
                                "trend": "neutral",
                                "confidence": 0.68
                            },
                            "risk": {
                                "volatility": 0.32,
                                "beta": 1.05,
                                "risk_level": "moderate",
                                "confidence": 0.75
                            },
                            "sentiment": {
                                "score": 0.45,
                                "label": "neutral",
                                "confidence": 0.65
                            }
                        }
                    }
                },
                "options": {
                    "symbols": ["AAPL", "TSLA"],
                    "analysis_types": ["technical", "risk"],
                    "sample_results": {
                        "AAPL": {
                            "technical": {
                                "delta": 0.65,
                                "gamma": 0.08,
                                "theta": -0.12,
                                "vega": 0.25,
                                "confidence": 0.70
                            },
                            "risk": {
                                "volatility": 0.35,
                                "risk_level": "high",
                                "confidence": 0.75
                            }
                        }
                    }
                },
                "trades": {
                    "total_trades": 156,
                    "win_rate": 0.68,
                    "avg_profit": 2.45,
                    "max_drawdown": -8.2,
                    "sharpe_ratio": 1.85,
                    "analysis_types": ["performance", "risk"],
                    "sample_results": {
                        "performance": {
                            "total_return": 15.6,
                            "monthly_return": 2.1,
                            "volatility": 12.3,
                            "confidence": 0.80
                        },
                        "risk": {
                            "var_95": -3.2,
                            "max_position_size": 5.0,
                            "correlation": 0.45,
                            "confidence": 0.75
                        }
                    }
                },
                "news": {
                    "symbols": ["AAPL", "TSLA", "MSFT"],
                    "analysis_types": ["sentiment", "risk"],
                    "sample_results": {
                        "AAPL": {
                            "sentiment": {
                                "score": 0.72,
                                "label": "positive",
                                "articles_analyzed": 24,
                                "confidence": 0.75
                            },
                            "risk": {
                                "impact_score": 0.65,
                                "risk_level": "low",
                                "confidence": 0.70
                            }
                        },
                        "TSLA": {
                            "sentiment": {
                                "score": -0.15,
                                "label": "slightly_negative",
                                "articles_analyzed": 18,
                                "confidence": 0.68
                            },
                            "risk": {
                                "impact_score": 0.45,
                                "risk_level": "moderate",
                                "confidence": 0.65
                            }
                        }
                    }
                }
            }
            
            return sample_data
            
        except Exception as e:
            logger.error(f"Error getting sample analysis: {e}")
            return {}
    
    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        try:
            metrics = {
                "data_processed": {
                    "stocks": 1250,
                    "options": 890,
                    "trades": 156,
                    "news_articles": 342
                },
                "transformation_quality": {
                    "average_score": 0.87,
                    "success_rate": 0.94,
                    "error_rate": 0.06
                },
                "analysis_performance": {
                    "average_confidence": 0.76,
                    "analysis_types": 4,
                    "symbols_analyzed": 25
                },
                "processing_times": {
                    "stock_analysis": 2.3,
                    "options_analysis": 1.8,
                    "trade_analysis": 0.9,
                    "news_analysis": 3.2
                },
                "data_sources": {
                    "market_data": "Yahoo Finance, Polygon",
                    "news_sources": "Reuters, Bloomberg, CNBC",
                    "options_data": "Polygon, CBOE",
                    "sentiment_data": "News APIs, Social Media"
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting pipeline metrics: {e}")
            return {}

# Global dashboard instance
dashboard = DataPipelineDashboard()

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    async with dashboard as d:
        status = await d.get_pipeline_status()
        sample_analysis = await d.get_sample_analysis()
        metrics = await d.get_pipeline_metrics()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "status": status,
        "sample_analysis": sample_analysis,
        "metrics": metrics,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "data-pipeline-dashboard",
        "version": "1.0.0"
    }

@app.get("/api/status")
async def get_status():
    """Get dashboard status"""
    async with dashboard as d:
        status = await d.get_pipeline_status()
    
    return {
        "service": "data-pipeline-dashboard",
        "version": "1.0.0",
        "status": "operational",
        "pipeline_status": status
    }

@app.get("/api/sample-analysis")
async def get_sample_analysis():
    """Get sample analysis data"""
    async with dashboard as d:
        sample_analysis = await d.get_sample_analysis()
    
    return sample_analysis

@app.get("/api/metrics")
async def get_metrics():
    """Get pipeline metrics"""
    async with dashboard as d:
        metrics = await d.get_pipeline_metrics()
    
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11137) 