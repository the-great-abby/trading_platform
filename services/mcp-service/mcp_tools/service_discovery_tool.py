"""
Service Discovery Tool for MCP Service
Provides service discovery and monitoring capabilities
"""

import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from clients.service_client import ServiceClient

class ServiceDiscoveryTool:
    """Tool for service discovery and monitoring"""
    
    def __init__(self):
        self.service_client = ServiceClient()
        # Use your existing PORT_MAP.md data
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
    
    async def list_all_services(self) -> Dict[str, Any]:
        """List all services in the system"""
        return {
            "services": [
                {
                    "name": name,
                    "port": info["port"],
                    "purpose": info["purpose"],
                    "url": f"http://localhost:{info['port']}"
                }
                for name, info in self.services.items()
            ],
            "total_services": len(self.services)
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
    
    async def get_service_details(self, service_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific service"""
        if service_name not in self.services:
            return {"error": "Service not found"}
        
        info = self.services[service_name]
        health_status = await self.check_service_health(service_name)
        
        return {
            "name": service_name,
            "port": info["port"],
            "url": f"http://localhost:{info['port']}",
            "purpose": info["purpose"],
            "health": health_status,
            "endpoints": await self._get_service_endpoints(service_name)
        }
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
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
                        "response_code": response.status,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            return {
                "status": "❌ Unreachable",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_service_endpoints(self, service_name: str) -> List[str]:
        """Get available endpoints for a service"""
        # This would query the service's OpenAPI spec or known endpoints
        common_endpoints = ["/health", "/metrics", "/docs"]
        return common_endpoints
