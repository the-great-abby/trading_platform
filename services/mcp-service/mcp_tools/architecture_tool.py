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
    
    async def get_trading_system_status(self) -> Dict[str, Any]:
        """Get current trading system operational status"""
        try:
            # Get service status
            service_status = await self.service_client.get_services_status()
            
            # Categorize services by trading function
            trading_services = ["trading-engine", "strategy-service", "market-data-service"]
            ai_services = ["ai-analysis-service", "llm-proxy"]
            data_services = ["timescaledb", "redis", "rabbitmq"]
            dashboard_services = ["unified-analytics-dashboard", "unified-trading-dashboard", "unified-news-dashboard"]
            
            # Check critical services
            critical_services_status = {}
            for service in trading_services + data_services:
                if service in service_status:
                    critical_services_status[service] = service_status[service]
            
            # Calculate system health
            healthy_critical = sum(1 for status in critical_services_status.values() 
                                 if "✅ Healthy" in status.get("status", ""))
            total_critical = len(critical_services_status)
            system_health = round((healthy_critical / total_critical) * 100, 1) if total_critical > 0 else 0
            
            # Determine trading system status
            if system_health >= 90:
                trading_status = "🟢 Fully Operational"
            elif system_health >= 70:
                trading_status = "🟡 Partially Operational"
            else:
                trading_status = "🔴 Critical Issues"
            
            return {
                "trading_system_status": trading_status,
                "system_health_percentage": system_health,
                "critical_services_healthy": healthy_critical,
                "critical_services_total": total_critical,
                "trading_services": {
                    service: service_status.get(service, {"status": "❌ Not Found"})
                    for service in trading_services
                },
                "ai_services": {
                    service: service_status.get(service, {"status": "❌ Not Found"})
                    for service in ai_services
                },
                "data_services": {
                    service: service_status.get(service, {"status": "❌ Not Found"})
                    for service in data_services
                },
                "dashboard_services": {
                    service: service_status.get(service, {"status": "❌ Not Found"})
                    for service in dashboard_services
                },
                "operational_notes": [
                    "Trading system requires all critical services to be healthy",
                    "AI services enhance trading decisions but are not critical",
                    "Dashboard services provide monitoring and control interfaces"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "trading_system_status": "🔴 Status Unknown",
                "error": f"Failed to get trading system status: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_trading_architecture_summary(self) -> Dict[str, Any]:
        """Get trading-specific architecture summary"""
        return {
            "trading_architecture": {
                "type": "Event-Driven Microservices",
                "pattern": "CQRS (Command Query Responsibility Segregation)",
                "communication": "Asynchronous via RabbitMQ",
                "data_storage": "TimescaleDB for time-series, Redis for caching",
                "ai_integration": "LLM-powered analysis with vector storage"
            },
            "trading_components": {
                "data_ingestion": [
                    "Market Data Service (Polygon API)",
                    "News Service (RSS Feeds)",
                    "Economic Calendar Service"
                ],
                "data_processing": [
                    "Data Transformation Pipeline",
                    "Sentiment Analysis",
                    "Technical Indicators Calculation"
                ],
                "ai_analysis": [
                    "LLM Proxy (Ollama Integration)",
                    "AI Analysis Service",
                    "Vector Storage (Embeddings)",
                    "Background Vectorization"
                ],
                "trading_execution": [
                    "Strategy Service",
                    "Trading Engine",
                    "Risk Management",
                    "Portfolio Service",
                    "Order Management"
                ],
                "monitoring": [
                    "Unified Dashboards",
                    "Prometheus Metrics",
                    "Grafana Visualization",
                    "MCP Service Management"
                ]
            },
            "data_flow_stages": [
                "1. Market Data Ingestion → TimescaleDB",
                "2. News Processing → Sentiment Analysis → Vector Storage",
                "3. AI Analysis → Strategy Signals → Trading Engine",
                "4. Risk Assessment → Order Execution → Portfolio Update",
                "5. Performance Monitoring → Dashboard Display"
            ],
            "key_features": [
                "Real-time market data processing",
                "AI-powered trading decisions",
                "Comprehensive risk management",
                "Multi-strategy portfolio management",
                "Advanced backtesting capabilities",
                "Real-time monitoring and alerting"
            ]
        }
    
    async def get_system_capabilities(self) -> Dict[str, Any]:
        """Get system capabilities and features"""
        try:
            # Get service status to determine capabilities
            service_status = await self.service_client.get_services_status()
            
            capabilities = {
                "data_processing": {
                    "market_data": "market-data-service" in service_status,
                    "news_analysis": "unified-news-dashboard" in service_status,
                    "sentiment_analysis": "ai-analysis-service" in service_status,
                    "time_series_storage": "timescaledb" in service_status
                },
                "trading_operations": {
                    "strategy_execution": "strategy-service" in service_status,
                    "portfolio_management": "unified-trading-dashboard" in service_status,
                    "risk_management": "trading-engine" in service_status,
                    "backtesting": "backtest-api" in service_status
                },
                "ai_features": {
                    "llm_integration": "ai-analysis-service" in service_status,
                    "vector_storage": "timescaledb" in service_status,
                    "ai_analysis": "unified-analytics-dashboard" in service_status,
                    "sentiment_analysis": "unified-news-dashboard" in service_status
                },
                "monitoring": {
                    "real_time_dashboards": "unified-analytics-dashboard" in service_status,
                    "metrics_collection": "prometheus" in service_status,
                    "visualization": "grafana" in service_status,
                    "system_management": "mcp-service" in service_status
                }
            }
            
            # Calculate capability scores
            capability_scores = {}
            for category, features in capabilities.items():
                total_features = len(features)
                active_features = sum(1 for active in features.values() if active)
                capability_scores[category] = {
                    "score": round((active_features / total_features) * 100, 1),
                    "active": active_features,
                    "total": total_features
                }
            
            return {
                "capabilities": capabilities,
                "capability_scores": capability_scores,
                "overall_capability_score": round(
                    sum(score["score"] for score in capability_scores.values()) / len(capability_scores), 1
                ),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get system capabilities: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }