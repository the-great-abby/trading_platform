"""
Monitoring Integration for MCP Service
Real-time monitoring and background task management
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class MonitoringStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class MonitoringData:
    service_name: str
    health_score: int
    memory_usage: float
    cpu_usage: float
    response_time: float
    error_rate: float
    status: str
    timestamp: datetime
    alerts: List[str] = None

@dataclass
class Alert:
    service_name: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False

class MonitoringIntegration:
    """Real-time monitoring and background task management"""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self.monitoring_data: Dict[str, MonitoringData] = {}
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # Monitoring configuration
        self.monitoring_interval = 30  # seconds
        self.alert_thresholds = {
            "memory_high": 85.0,
            "cpu_high": 80.0,
            "response_time_slow": 2000.0,  # ms
            "error_rate_high": 5.0,  # %
            "health_score_low": 50.0
        }
        
        # Service endpoints for monitoring
        self.service_endpoints = {
            "unified-analytics-dashboard": "http://localhost:11115",
            "unified-trading-dashboard": "http://localhost:11114",
            "unified-news-dashboard": "http://localhost:11116",
            "trading-engine": "http://localhost:11080",
            "market-data-service": "http://localhost:11084",
            "strategy-service": "http://localhost:11081",
            "ai-analysis-service": "http://localhost:11085",
            "portfolio-management": "http://localhost:11083",
            "risk-management": "http://localhost:11085",
            "news-service": "http://localhost:11086",
            "rss-feed-service": "http://localhost:11087",
            "vector-storage": "http://localhost:11088",
            "llm-proxy": "http://localhost:12001",
            "prometheus": "http://localhost:11190",
            "grafana": "http://localhost:11044",
            "mcp-service": "http://localhost:11117"
        }
        
        # Prometheus configuration
        self.prometheus_url = "http://localhost:11190"
        self.prometheus_queries = {
            "memory_usage": 'container_memory_usage_bytes{name=~".*{service_name}.*"}',
            "cpu_usage": 'rate(container_cpu_usage_seconds_total{name=~".*{service_name}.*"}[5m])',
            "response_time": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service="{service_name}"}[5m]))',
            "error_rate": 'rate(http_requests_total{service="{service_name}",status=~"5.."}[5m]) / rate(http_requests_total{service="{service_name}"}[5m])'
        }
    
    async def start_monitoring(self) -> Dict[str, Any]:
        """Start real-time monitoring"""
        try:
            if self.monitoring_active:
                return {
                    "status": "already_active",
                    "message": "Monitoring is already active",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info("Starting real-time monitoring...")
            
            # Test connectivity to services
            connectivity_test = await self._test_connectivity()
            if not connectivity_test["success"]:
                return {
                    "status": "failed",
                    "message": "Connectivity test failed",
                    "details": connectivity_test,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Start monitoring tasks
            self.monitoring_active = True
            self.monitoring_tasks = []
            
            # Main monitoring task
            main_task = asyncio.create_task(self._monitoring_loop())
            self.monitoring_tasks.append(main_task)
            
            # Alert processing task
            alert_task = asyncio.create_task(self._alert_processing_loop())
            self.monitoring_tasks.append(alert_task)
            
            return {
                "status": "started",
                "message": "Real-time monitoring started successfully",
                "monitoring_tasks": len(self.monitoring_tasks),
                "services_monitored": len(self.service_endpoints),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return {
                "status": "error",
                "message": f"Failed to start monitoring: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """Stop real-time monitoring"""
        try:
            if not self.monitoring_active:
                return {
                    "status": "not_active",
                    "message": "Monitoring is not active",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info("Stopping real-time monitoring...")
            
            # Cancel all monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()
            
            self.monitoring_tasks = []
            self.monitoring_active = False
            
            return {
                "status": "stopped",
                "message": "Real-time monitoring stopped successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            return {
                "status": "error",
                "message": f"Failed to stop monitoring: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "monitoring_active": self.monitoring_active,
            "monitoring_tasks": len(self.monitoring_tasks),
            "active_tasks": [task.get_name() for task in self.monitoring_tasks if not task.done()],
            "services_monitored": len(self.service_endpoints),
            "monitoring_data_count": len(self.monitoring_data),
            "active_alerts": len([alert for alert in self.alerts if not alert.resolved]),
            "total_alerts": len(self.alert_history),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        if not self.monitoring_data:
            return {
                "message": "No monitoring data available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Calculate system health metrics
        total_services = len(self.monitoring_data)
        healthy_services = sum(1 for data in self.monitoring_data.values() if data.health_score >= 80)
        unhealthy_services = total_services - healthy_services
        
        # Calculate average metrics
        avg_memory = sum(data.memory_usage for data in self.monitoring_data.values()) / total_services
        avg_cpu = sum(data.cpu_usage for data in self.monitoring_data.values()) / total_services
        avg_response_time = sum(data.response_time for data in self.monitoring_data.values()) / total_services
        avg_error_rate = sum(data.error_rate for data in self.monitoring_data.values()) / total_services
        
        # Get active alerts
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        return {
            "system_health": {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": unhealthy_services,
                "health_percentage": round((healthy_services / total_services) * 100, 2) if total_services > 0 else 0
            },
            "average_metrics": {
                "memory_usage": round(avg_memory, 2),
                "cpu_usage": round(avg_cpu, 2),
                "response_time_ms": round(avg_response_time, 2),
                "error_rate": round(avg_error_rate, 2)
            },
            "alerts": {
                "active_alerts": len(active_alerts),
                "total_alerts": len(self.alert_history),
                "recent_alerts": [
                    {
                        "service_name": alert.service_name,
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts[-10:]  # Last 10 alerts
                ]
            },
            "services": {
                name: {
                    "health_score": data.health_score,
                    "memory_usage": data.memory_usage,
                    "cpu_usage": data.cpu_usage,
                    "response_time": data.response_time,
                    "error_rate": data.error_rate,
                    "status": data.status,
                    "alerts": data.alerts or [],
                    "last_updated": data.timestamp.isoformat()
                }
                for name, data in self.monitoring_data.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_service_health_data(self, service_name: str) -> Dict[str, Any]:
        """Get health data for a specific service"""
        if service_name not in self.monitoring_data:
            return {
                "error": f"No monitoring data available for service {service_name}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        data = self.monitoring_data[service_name]
        return {
            "service_name": service_name,
            "health_score": data.health_score,
            "memory_usage": data.memory_usage,
            "cpu_usage": data.cpu_usage,
            "response_time": data.response_time,
            "error_rate": data.error_rate,
            "status": data.status,
            "alerts": data.alerts or [],
            "last_updated": data.timestamp.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        logger.info("Starting monitoring loop...")
        
        while self.monitoring_active:
            try:
                # Monitor all services
                for service_name in self.service_endpoints:
                    await self._monitor_service(service_name)
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _monitor_service(self, service_name: str) -> None:
        """Monitor a specific service"""
        try:
            # Get health data
            health_data = await self._collect_service_metrics(service_name)
            
            # Update monitoring data
            self.monitoring_data[service_name] = health_data
            
            # Check for alerts
            await self._check_alerts(service_name, health_data)
            
        except Exception as e:
            logger.error(f"Error monitoring service {service_name}: {e}")
    
    async def _collect_service_metrics(self, service_name: str) -> MonitoringData:
        """Collect comprehensive metrics for a service"""
        endpoint = self.service_endpoints[service_name]
        
        # Initialize default values
        health_score = 100
        memory_usage = 0.0
        cpu_usage = 0.0
        response_time = 0.0
        error_rate = 0.0
        status = "unknown"
        alerts = []
        
        try:
            # Health check
            start_time = datetime.utcnow()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/health", timeout=10) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms
                    
                    if response.status == 200:
                        status = "healthy"
                        health_score = 100
                    else:
                        status = "unhealthy"
                        health_score = 50
                        alerts.append("Service health check failed")
            
            # Get Prometheus metrics
            prometheus_metrics = await self._get_prometheus_metrics(service_name)
            memory_usage = prometheus_metrics.get("memory_usage", 0.0)
            cpu_usage = prometheus_metrics.get("cpu_usage", 0.0)
            error_rate = prometheus_metrics.get("error_rate", 0.0)
            
            # Calculate health score based on metrics
            if memory_usage > self.alert_thresholds["memory_high"]:
                health_score -= 20
                alerts.append("High memory usage")
            elif memory_usage > 70:
                health_score -= 10
            
            if cpu_usage > self.alert_thresholds["cpu_high"]:
                health_score -= 15
                alerts.append("High CPU usage")
            elif cpu_usage > 60:
                health_score -= 5
            
            if response_time > self.alert_thresholds["response_time_slow"]:
                health_score -= 20
                alerts.append("Slow response time")
            elif response_time > 1000:
                health_score -= 10
            
            if error_rate > self.alert_thresholds["error_rate_high"]:
                health_score -= 25
                alerts.append("High error rate")
            elif error_rate > 1:
                health_score -= 10
            
            # Ensure health score doesn't go below 0
            health_score = max(0, health_score)
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {service_name}: {e}")
            status = "unreachable"
            health_score = 0
            alerts.append(f"Service unreachable: {str(e)}")
        
        return MonitoringData(
            service_name=service_name,
            health_score=health_score,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            response_time=response_time,
            error_rate=error_rate,
            status=status,
            timestamp=datetime.utcnow(),
            alerts=alerts
        )
    
    async def _get_prometheus_metrics(self, service_name: str) -> Dict[str, float]:
        """Get metrics from Prometheus for a service"""
        metrics = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                for metric_name, query_template in self.prometheus_queries.items():
                    query = query_template.format(service_name=service_name)
                    params = {"query": query}
                    
                    async with session.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params=params,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "data" in data and "result" in data["data"] and data["data"]["result"]:
                                # Extract the first value (simplified)
                                result = data["data"]["result"][0]
                                if "value" in result:
                                    metrics[metric_name] = float(result["value"][1])
                        else:
                            metrics[metric_name] = 0.0
        except Exception as e:
            logger.error(f"Error getting Prometheus metrics for {service_name}: {e}")
            # Return default values
            metrics = {
                "memory_usage": 0.0,
                "cpu_usage": 0.0,
                "error_rate": 0.0
            }
        
        return metrics
    
    async def _check_alerts(self, service_name: str, health_data: MonitoringData) -> None:
        """Check for alerts based on health data"""
        # Check memory usage
        if health_data.memory_usage > self.alert_thresholds["memory_high"]:
            await self._create_alert(
                service_name, "memory_high", "high",
                f"Memory usage is {health_data.memory_usage:.1f}% (threshold: {self.alert_thresholds['memory_high']}%)"
            )
        
        # Check CPU usage
        if health_data.cpu_usage > self.alert_thresholds["cpu_high"]:
            await self._create_alert(
                service_name, "cpu_high", "high",
                f"CPU usage is {health_data.cpu_usage:.1f}% (threshold: {self.alert_thresholds['cpu_high']}%)"
            )
        
        # Check response time
        if health_data.response_time > self.alert_thresholds["response_time_slow"]:
            await self._create_alert(
                service_name, "response_time_slow", "medium",
                f"Response time is {health_data.response_time:.1f}ms (threshold: {self.alert_thresholds['response_time_slow']}ms)"
            )
        
        # Check error rate
        if health_data.error_rate > self.alert_thresholds["error_rate_high"]:
            await self._create_alert(
                service_name, "error_rate_high", "high",
                f"Error rate is {health_data.error_rate:.1f}% (threshold: {self.alert_thresholds['error_rate_high']}%)"
            )
        
        # Check health score
        if health_data.health_score < self.alert_thresholds["health_score_low"]:
            await self._create_alert(
                service_name, "health_score_low", "critical",
                f"Health score is {health_data.health_score} (threshold: {self.alert_thresholds['health_score_low']})"
            )
    
    async def _create_alert(self, service_name: str, alert_type: str, severity: str, message: str) -> None:
        """Create a new alert"""
        # Check if alert already exists and is not resolved
        existing_alert = next(
            (alert for alert in self.alerts 
             if alert.service_name == service_name and alert.alert_type == alert_type and not alert.resolved),
            None
        )
        
        if existing_alert:
            # Update existing alert
            existing_alert.message = message
            existing_alert.timestamp = datetime.utcnow()
        else:
            # Create new alert
            alert = Alert(
                service_name=service_name,
                alert_type=alert_type,
                severity=severity,
                message=message,
                timestamp=datetime.utcnow()
            )
            self.alerts.append(alert)
            self.alert_history.append(alert)
            logger.warning(f"New alert created: {service_name} - {alert_type} - {message}")
    
    async def _alert_processing_loop(self) -> None:
        """Process and manage alerts"""
        logger.info("Starting alert processing loop...")
        
        while self.monitoring_active:
            try:
                # Process alerts (e.g., send notifications, auto-resolve)
                await self._process_alerts()
                
                # Wait before next processing cycle
                await asyncio.sleep(60)  # Process alerts every minute
                
            except asyncio.CancelledError:
                logger.info("Alert processing loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(60)
    
    async def _process_alerts(self) -> None:
        """Process active alerts"""
        # Auto-resolve alerts that are no longer active
        for alert in self.alerts[:]:  # Copy list to avoid modification during iteration
            if not alert.resolved:
                # Check if the condition still exists
                if alert.service_name in self.monitoring_data:
                    health_data = self.monitoring_data[alert.service_name]
                    
                    # Check if alert condition is resolved
                    resolved = False
                    if alert.alert_type == "memory_high" and health_data.memory_usage <= self.alert_thresholds["memory_high"]:
                        resolved = True
                    elif alert.alert_type == "cpu_high" and health_data.cpu_usage <= self.alert_thresholds["cpu_high"]:
                        resolved = True
                    elif alert.alert_type == "response_time_slow" and health_data.response_time <= self.alert_thresholds["response_time_slow"]:
                        resolved = True
                    elif alert.alert_type == "error_rate_high" and health_data.error_rate <= self.alert_thresholds["error_rate_high"]:
                        resolved = True
                    elif alert.alert_type == "health_score_low" and health_data.health_score >= self.alert_thresholds["health_score_low"]:
                        resolved = True
                    
                    if resolved:
                        alert.resolved = True
                        logger.info(f"Alert auto-resolved: {alert.service_name} - {alert.alert_type}")
    
    async def _test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to all services"""
        results = {}
        successful_connections = 0
        
        for service_name, endpoint in self.service_endpoints.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{endpoint}/health", timeout=5) as response:
                        if response.status == 200:
                            results[service_name] = {"status": "reachable", "response_code": response.status}
                            successful_connections += 1
                        else:
                            results[service_name] = {"status": "unhealthy", "response_code": response.status}
            except Exception as e:
                results[service_name] = {"status": "unreachable", "error": str(e)}
        
        return {
            "success": successful_connections > 0,
            "successful_connections": successful_connections,
            "total_services": len(self.service_endpoints),
            "results": results
        }
    
    async def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        recent_alerts = self.alert_history[-limit:] if self.alert_history else []
        return [
            {
                "service_name": alert.service_name,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "resolved": alert.resolved,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in recent_alerts
        ]

