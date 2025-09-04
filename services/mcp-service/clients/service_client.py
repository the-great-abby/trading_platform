"""
Service Client for MCP Service
Handles communication with other services
"""

import aiohttp
from typing import Dict, Any, List
from datetime import datetime

class ServiceClient:
    """Client for communicating with other services"""
    
    def __init__(self):
        self.services = {
            "unified-analytics-dashboard": {"port": 11115, "purpose": "Analytics & AI"},
            "unified-trading-dashboard": {"port": 11114, "purpose": "Trading Interface"},
            "unified-news-dashboard": {"port": 11116, "purpose": "News & Sentiment"},
            "market-data-service": {"port": 11084, "purpose": "Market Data Feeds"},
            "ai-analysis-service": {"port": 11085, "purpose": "AI Analysis"},
            "backtest-api": {"port": 11101, "purpose": "Backtesting"},
            "strategy-service": {"port": 11103, "purpose": "Strategy Management"},
            "grafana": {"port": 11044, "purpose": "Monitoring"},
            "prometheus": {"port": 11190, "purpose": "Metrics Collection"},
            "timescaledb": {"port": 11140, "purpose": "Primary Database"},
            "redis": {"port": 11142, "purpose": "Cache & Sessions"},
            "rabbitmq": {"port": 11144, "purpose": "Message Queue"}
        }
    
    async def get_services_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {}
        for name, info in self.services.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://localhost:{info['port']}/health", 
                        timeout=5
                    ) as response:
                        status[name] = {
                            "status": "✅ Healthy" if response.status == 200 else "❌ Unhealthy",
                            "port": info["port"],
                            "purpose": info["purpose"],
                            "response_code": response.status
                        }
            except Exception as e:
                status[name] = {
                    "status": "❌ Unreachable",
                    "port": info["port"],
                    "purpose": info["purpose"],
                    "error": str(e)
                }
        return status
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status of a specific service"""
        if service_name not in self.services:
            return {"error": "Service not found"}
        
        info = self.services[service_name]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{info['port']}/health", 
                    timeout=5
                ) as response:
                    return {
                        "status": "✅ Healthy" if response.status == 200 else "❌ Unhealthy",
                        "port": info["port"],
                        "purpose": info["purpose"],
                        "response_code": response.status,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            return {
                "status": "❌ Unreachable",
                "port": info["port"],
                "purpose": info["purpose"],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def call_service_endpoint(self, service_name: str, endpoint: str) -> Dict[str, Any]:
        """Call a specific endpoint on a service"""
        if service_name not in self.services:
            return {"error": "Service not found"}
        
        info = self.services[service_name]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{info['port']}{endpoint}", 
                    timeout=10
                ) as response:
                    data = await response.json()
                    return {
                        "status": "success",
                        "data": data,
                        "response_code": response.status,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
