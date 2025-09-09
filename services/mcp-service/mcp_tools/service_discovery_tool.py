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
    
    async def get_service_metrics(self, service_name: str) -> Dict[str, Any]:
        """Get detailed metrics for a service"""
        if service_name not in self.services:
            return {"error": "Service not found"}
        
        info = self.services[service_name]
        metrics = {
            "service_name": service_name,
            "port": info["port"],
            "purpose": info["purpose"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Get health status
            health_status = await self.check_service_health(service_name)
            metrics["health"] = health_status
            
            # Try to get metrics endpoint
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"http://localhost:{info['port']}/metrics", 
                        timeout=5
                    ) as response:
                        if response.status == 200:
                            metrics_text = await response.text()
                            # Parse basic metrics (simplified)
                            metrics["has_metrics"] = True
                            metrics["metrics_lines"] = len(metrics_text.split('\n'))
                        else:
                            metrics["has_metrics"] = False
                except:
                    metrics["has_metrics"] = False
                
                # Try to get response time
                start_time = datetime.utcnow()
                try:
                    async with session.get(
                        f"http://localhost:{info['port']}/health", 
                        timeout=5
                    ) as response:
                        end_time = datetime.utcnow()
                        response_time = (end_time - start_time).total_seconds() * 1000
                        metrics["response_time_ms"] = round(response_time, 2)
                        metrics["response_code"] = response.status
                except:
                    metrics["response_time_ms"] = None
                    metrics["response_code"] = None
            
        except Exception as e:
            metrics["error"] = str(e)
        
        return metrics
    
    async def get_service_dependencies(self, service_name: str) -> Dict[str, Any]:
        """Get what services depend on this service"""
        # Define service dependencies based on your architecture
        dependencies = {
            "timescaledb": ["trading-engine", "strategy-service", "market-data-service", "ai-analysis-service"],
            "redis": ["trading-engine", "ai-analysis-service", "unified-analytics-dashboard"],
            "rabbitmq": ["trading-engine", "market-data-service", "ai-analysis-service"],
            "market-data-service": ["strategy-service", "trading-engine", "backtest-api"],
            "ai-analysis-service": ["unified-analytics-dashboard", "trading-engine"],
            "strategy-service": ["trading-engine", "backtest-api"],
            "trading-engine": ["portfolio-service", "order-service", "risk-service"],
            "unified-analytics-dashboard": ["ai-analysis-service", "timescaledb"],
            "unified-trading-dashboard": ["trading-engine", "portfolio-service"],
            "unified-news-dashboard": ["news-service", "sentiment-analysis"],
            "backtest-api": ["strategy-service", "market-data-service", "timescaledb"]
        }
        
        if service_name not in dependencies:
            return {
                "service_name": service_name,
                "dependents": [],
                "dependency_level": "unknown"
            }
        
        dependents = dependencies[service_name]
        
        # Check if dependents are healthy
        dependent_status = {}
        for dependent in dependents:
            if dependent in self.services:
                health = await self.check_service_health(dependent)
                dependent_status[dependent] = health
        
        return {
            "service_name": service_name,
            "dependents": dependents,
            "dependent_count": len(dependents),
            "dependent_status": dependent_status,
            "dependency_level": "critical" if len(dependents) > 5 else "important" if len(dependents) > 2 else "standard"
        }
    
    async def get_services_ranked_by_health(self) -> Dict[str, Any]:
        """Get services ranked by health status"""
        all_services = await self.get_services_status()
        
        # Categorize services by health
        healthy_services = []
        unhealthy_services = []
        unreachable_services = []
        
        for service_name, status in all_services.items():
            if "✅ Healthy" in status["status"]:
                healthy_services.append(service_name)
            elif "❌ Unhealthy" in status["status"]:
                unhealthy_services.append(service_name)
            else:
                unreachable_services.append(service_name)
        
        return {
            "total_services": len(all_services),
            "healthy_count": len(healthy_services),
            "unhealthy_count": len(unhealthy_services),
            "unreachable_count": len(unreachable_services),
            "health_percentage": round((len(healthy_services) / len(all_services)) * 100, 1),
            "healthy_services": healthy_services,
            "unhealthy_services": unhealthy_services,
            "unreachable_services": unreachable_services,
            "summary": f"{len(healthy_services)}/{len(all_services)} services healthy ({round((len(healthy_services) / len(all_services)) * 100, 1)}%)"
        }
    
    async def get_comprehensive_health_score(self) -> Dict[str, Any]:
        """Get comprehensive health score for the entire system"""
        try:
            all_services = await self.get_services_status()
            
            # Define service criticality levels
            critical_services = ["timescaledb", "redis", "rabbitmq", "trading-engine"]
            important_services = ["market-data-service", "strategy-service", "ai-analysis-service"]
            standard_services = ["unified-analytics-dashboard", "unified-trading-dashboard", "unified-news-dashboard"]
            
            # Calculate health scores by category
            health_scores = {}
            total_score = 0
            total_weight = 0
            
            for category, services in [
                ("critical", critical_services),
                ("important", important_services), 
                ("standard", standard_services)
            ]:
                category_healthy = 0
                category_total = 0
                
                for service in services:
                    if service in all_services:
                        category_total += 1
                        if "✅ Healthy" in all_services[service]["status"]:
                            category_healthy += 1
                
                if category_total > 0:
                    category_score = round((category_healthy / category_total) * 100, 1)
                    weight = 3 if category == "critical" else 2 if category == "important" else 1
                    health_scores[category] = {
                        "score": category_score,
                        "healthy": category_healthy,
                        "total": category_total,
                        "weight": weight
                    }
                    total_score += category_score * weight
                    total_weight += weight
            
            # Calculate overall health score
            overall_score = round(total_score / total_weight, 1) if total_weight > 0 else 0
            
            # Determine health status
            if overall_score >= 90:
                health_status = "🟢 Excellent"
                health_color = "green"
            elif overall_score >= 75:
                health_status = "🟡 Good"
                health_color = "yellow"
            elif overall_score >= 50:
                health_status = "🟠 Fair"
                health_color = "orange"
            else:
                health_status = "🔴 Poor"
                health_color = "red"
            
            # Get service details for recommendations
            recommendations = []
            for category, scores in health_scores.items():
                if scores["score"] < 100:
                    missing_services = []
                    for service in (critical_services if category == "critical" 
                                  else important_services if category == "important" 
                                  else standard_services):
                        if service in all_services and "✅ Healthy" not in all_services[service]["status"]:
                            missing_services.append(service)
                    
                    if missing_services:
                        recommendations.append({
                            "category": category,
                            "issue": f"{category.title()} services need attention",
                            "missing_services": missing_services,
                            "priority": "high" if category == "critical" else "medium" if category == "important" else "low"
                        })
            
            return {
                "overall_health_score": overall_score,
                "health_status": health_status,
                "health_color": health_color,
                "category_scores": health_scores,
                "recommendations": recommendations,
                "total_services_checked": sum(scores["total"] for scores in health_scores.values()),
                "total_services_healthy": sum(scores["healthy"] for scores in health_scores.values()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to calculate health score: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_service_health_trends(self) -> Dict[str, Any]:
        """Get health trends and patterns (simplified version)"""
        try:
            all_services = await self.get_services_status()
            
            # Analyze service health patterns
            response_times = []
            error_services = []
            slow_services = []
            
            for service_name, status in all_services.items():
                if "error" in status:
                    error_services.append({
                        "service": service_name,
                        "error": status["error"]
                    })
                
                # Check response times (if available in metrics)
                if "response_time_ms" in status:
                    response_times.append({
                        "service": service_name,
                        "response_time": status["response_time_ms"]
                    })
                    if status["response_time_ms"] and status["response_time_ms"] > 1000:  # > 1 second
                        slow_services.append(service_name)
            
            # Calculate trends
            avg_response_time = round(
                sum(rt["response_time"] for rt in response_times if rt["response_time"]) / len(response_times), 2
            ) if response_times else 0
            
            return {
                "error_analysis": {
                    "services_with_errors": len(error_services),
                    "error_services": error_services,
                    "error_rate": round((len(error_services) / len(all_services)) * 100, 1)
                },
                "performance_analysis": {
                    "average_response_time_ms": avg_response_time,
                    "slow_services": slow_services,
                    "services_checked": len(response_times)
                },
                "health_patterns": {
                    "most_reliable_services": [name for name, status in all_services.items() 
                                             if "✅ Healthy" in status["status"] and "error" not in status],
                    "problematic_services": [name for name, status in all_services.items() 
                                           if "❌" in status["status"] or "error" in status]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to analyze health trends: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_health_recommendations(self) -> Dict[str, Any]:
        """Get health improvement recommendations"""
        try:
            health_score = await self.get_comprehensive_health_score()
            trends = await self.get_service_health_trends()
            
            recommendations = []
            
            # Critical service recommendations
            if health_score.get("category_scores", {}).get("critical", {}).get("score", 100) < 100:
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Critical Services",
                    "issue": "Critical services are not fully operational",
                    "action": "Immediately check and restart critical services (TimescaleDB, Redis, RabbitMQ, Trading Engine)",
                    "impact": "System may be non-functional"
                })
            
            # Performance recommendations
            if trends.get("performance_analysis", {}).get("average_response_time_ms", 0) > 2000:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Performance",
                    "issue": "High response times detected",
                    "action": "Check system resources and optimize slow services",
                    "impact": "User experience degradation"
                })
            
            # Error recommendations
            error_rate = trends.get("error_analysis", {}).get("error_rate", 0)
            if error_rate > 20:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Errors",
                    "issue": f"High error rate: {error_rate}%",
                    "action": "Investigate and fix service errors",
                    "impact": "System reliability issues"
                })
            elif error_rate > 10:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Errors",
                    "issue": f"Moderate error rate: {error_rate}%",
                    "action": "Monitor and address service errors",
                    "impact": "Potential reliability issues"
                })
            
            # Overall health recommendations
            overall_score = health_score.get("overall_health_score", 0)
            if overall_score < 50:
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Overall Health",
                    "issue": f"System health is critically low: {overall_score}%",
                    "action": "Immediate system-wide health check and remediation",
                    "impact": "System may be unstable"
                })
            elif overall_score < 75:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Overall Health",
                    "issue": f"System health needs improvement: {overall_score}%",
                    "action": "Address service issues and optimize performance",
                    "impact": "System stability concerns"
                })
            
            return {
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "critical_count": len([r for r in recommendations if r["priority"] == "CRITICAL"]),
                "high_count": len([r for r in recommendations if r["priority"] == "HIGH"]),
                "medium_count": len([r for r in recommendations if r["priority"] == "MEDIUM"]),
                "overall_health_score": overall_score,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to generate recommendations: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }