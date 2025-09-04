"""
Architecture Tool for MCP Service
Provides system architecture analysis and overview
"""

import aiohttp
from typing import Dict, Any, List
from datetime import datetime
from clients.service_client import ServiceClient

class ArchitectureTool:
    """Tool for system architecture analysis"""
    
    def __init__(self):
        self.service_client = ServiceClient()
        self.architecture_data = {
            "type": "Microservices with Kubernetes",
            "total_services": 37,
            "main_components": {
                "trading_services": [
                    "trading-engine", "strategy-service", "market-data-service",
                    "portfolio-service", "order-service", "risk-service"
                ],
                "ai_services": [
                    "ai-analysis-service", "llm-proxy", "vector-storage",
                    "background-vectorization-service"
                ],
                "data_services": [
                    "timescaledb", "redis", "rabbitmq", "postgres-vector-storage"
                ],
                "dashboards": [
                    "unified-analytics-dashboard", "unified-trading-dashboard",
                    "unified-news-dashboard", "performance-dashboard"
                ],
                "monitoring": [
                    "prometheus", "grafana", "infrastructure-metrics-collector"
                ]
            },
            "data_flow": [
                "Market Data Service → Data Processing → Strategy Service → Trading Engine",
                "News Service → Sentiment Analysis → AI Analysis → Trading Decisions",
                "Trading Engine → Portfolio Service → Risk Service → Order Execution"
            ]
        }
    
    async def get_system_architecture(self) -> Dict[str, Any]:
        """Get complete system architecture"""
        try:
            # Get current service status
            service_status = await self.service_client.get_services_status()
            
            return {
                **self.architecture_data,
                "current_status": service_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            # Return static architecture data if service discovery fails
            return {
                **self.architecture_data,
                "current_status": {"error": f"Service discovery failed: {str(e)}"},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_architecture_overview(self) -> Dict[str, Any]:
        """Get high-level architecture overview"""
        return {
            "architecture_type": self.architecture_data["type"],
            "total_services": self.architecture_data["total_services"],
            "main_components": self.architecture_data["main_components"],
            "data_flow": self.architecture_data["data_flow"]
        }
    
    async def get_data_flow(self) -> Dict[str, Any]:
        """Get detailed data flow information"""
        return {
            "data_flows": self.architecture_data["data_flow"],
            "data_sources": ["Polygon API", "RSS Feeds", "News APIs"],
            "data_destinations": ["TimescaleDB", "Redis", "Vector Storage"],
            "processing_stages": [
                "Data Ingestion", "Data Processing", "AI Analysis", 
                "Strategy Execution", "Portfolio Management"
            ]
        }
