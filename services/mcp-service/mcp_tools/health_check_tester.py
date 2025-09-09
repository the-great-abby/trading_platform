"""
Health Check Tester for MCP Service
Comprehensive health endpoint testing and validation
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HealthTestResult:
    service_name: str
    endpoint: str
    status_code: int
    response_time: float
    success: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

class HealthCheckTester:
    """Comprehensive health endpoint testing and validation"""
    
    def __init__(self):
        # Health endpoints configuration - using internal Kubernetes service names
        self.health_endpoints = {
            "unified-analytics-dashboard": "http://unified-analytics-dashboard.trading-system.svc.cluster.local/health",
            "unified-trading-dashboard": "http://unified-trading-dashboard.trading-system.svc.cluster.local/health",
            "unified-news-dashboard": "http://unified-news-dashboard.trading-system.svc.cluster.local/health",
            "trading-engine": "http://cqrs-api-service.trading-system.svc.cluster.local/health",
            "market-data-service": "http://market-data-service.trading-system.svc.cluster.local/health",
            "strategy-service": "http://strategy-service.trading-system.svc.cluster.local/health",
            "ai-analysis-service": "http://ai-analysis-service.trading-system.svc.cluster.local/health",
            "portfolio-management": "http://portfolio-service.trading-system.svc.cluster.local/health",
            "risk-management": "http://risk-management-service.trading-system.svc.cluster.local/health",
            "news-service": "http://news-service.trading-system.svc.cluster.local/health",
            "rss-feed-service": "http://rss-feed-service.trading-system.svc.cluster.local/health",
            "vector-storage": "http://vector-storage.trading-system.svc.cluster.local/health",
            "llm-proxy": "http://llm-proxy.trading-system.svc.cluster.local/health",
            "prometheus": "http://prometheus.trading-system.svc.cluster.local/health",
            "grafana": "http://grafana.trading-system.svc.cluster.local/health",
            "mcp-service": "http://mcp-service.trading-system.svc.cluster.local/health"
        }
        
        # Test configuration
        self.timeout = 10  # seconds
        self.max_concurrent_tests = 10
    
    async def test_all_endpoints(self) -> Dict[str, Any]:
        """Test all health endpoints concurrently"""
        logger.info("Starting comprehensive health endpoint testing...")
        
        start_time = datetime.utcnow()
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent_tests)
        
        # Create tasks for all endpoints
        tasks = []
        for service_name, endpoint in self.health_endpoints.items():
            task = asyncio.create_task(
                self._test_endpoint_with_semaphore(semaphore, service_name, endpoint)
            )
            tasks.append(task)
        
        # Wait for all tests to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        test_results = []
        successful_tests = 0
        failed_tests = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(self.health_endpoints.keys())[i]
                endpoint = list(self.health_endpoints.values())[i]
                test_result = HealthTestResult(
                    service_name=service_name,
                    endpoint=endpoint,
                    status_code=0,
                    response_time=0.0,
                    success=False,
                    error_message=str(result),
                    timestamp=datetime.utcnow()
                )
                failed_tests += 1
            else:
                test_result = result
                if test_result.success:
                    successful_tests += 1
                else:
                    failed_tests += 1
            
            test_results.append(test_result)
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        return {
            "success": successful_tests > 0,
            "total_tests": len(test_results),
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round((successful_tests / len(test_results)) * 100, 2) if test_results else 0,
            "total_time_seconds": round(total_time, 2),
            "average_response_time": round(
                sum(r.response_time for r in test_results if r.success) / successful_tests, 2
            ) if successful_tests > 0 else 0,
            "results": [
                {
                    "service_name": result.service_name,
                    "endpoint": result.endpoint,
                    "status_code": result.status_code,
                    "response_time_ms": round(result.response_time, 2),
                    "success": result.success,
                    "error_message": result.error_message,
                    "response_data": result.response_data,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in test_results
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def test_specific_service(self, service_name: str) -> Dict[str, Any]:
        """Test a specific service health endpoint"""
        if service_name not in self.health_endpoints:
            return {
                "success": False,
                "error": f"Service {service_name} not found in health endpoints",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        endpoint = self.health_endpoints[service_name]
        result = await self._test_endpoint(service_name, endpoint)
        
        return {
            "success": result.success,
            "service_name": result.service_name,
            "endpoint": result.endpoint,
            "status_code": result.status_code,
            "response_time_ms": round(result.response_time, 2),
            "error_message": result.error_message,
            "response_data": result.response_data,
            "timestamp": result.timestamp.isoformat()
        }
    
    async def _test_endpoint_with_semaphore(self, semaphore: asyncio.Semaphore, service_name: str, endpoint: str) -> HealthTestResult:
        """Test endpoint with semaphore for concurrency control"""
        async with semaphore:
            return await self._test_endpoint(service_name, endpoint)
    
    async def _test_endpoint(self, service_name: str, endpoint: str) -> HealthTestResult:
        """Test a single health endpoint"""
        start_time = datetime.utcnow()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=self.timeout) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms
                    
                    # Try to parse JSON response
                    response_data = None
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"raw_response": await response.text()}
                    
                    success = response.status == 200
                    
                    return HealthTestResult(
                        service_name=service_name,
                        endpoint=endpoint,
                        status_code=response.status,
                        response_time=response_time,
                        success=success,
                        response_data=response_data,
                        timestamp=datetime.utcnow()
                    )
        
        except asyncio.TimeoutError:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthTestResult(
                service_name=service_name,
                endpoint=endpoint,
                status_code=0,
                response_time=response_time,
                success=False,
                error_message=f"Timeout after {self.timeout} seconds",
                timestamp=datetime.utcnow()
            )
        
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthTestResult(
                service_name=service_name,
                endpoint=endpoint,
                status_code=0,
                response_time=response_time,
                success=False,
                error_message=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def test_endpoint_connectivity(self, service_name: str) -> Dict[str, Any]:
        """Test basic connectivity to a service endpoint"""
        if service_name not in self.health_endpoints:
            return {
                "success": False,
                "error": f"Service {service_name} not found in health endpoints",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        endpoint = self.health_endpoints[service_name]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=5) as response:
                    return {
                        "success": True,
                        "service_name": service_name,
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "reachable": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except Exception as e:
            return {
                "success": False,
                "service_name": service_name,
                "endpoint": endpoint,
                "reachable": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of all health endpoints"""
        results = await self.test_all_endpoints()
        
        # Categorize results
        healthy_services = []
        unhealthy_services = []
        unreachable_services = []
        
        for result in results.get("results", []):
            if result["success"]:
                healthy_services.append(result["service_name"])
            elif result["status_code"] > 0:
                unhealthy_services.append(result["service_name"])
            else:
                unreachable_services.append(result["service_name"])
        
        return {
            "total_services": len(self.health_endpoints),
            "healthy_services": {
                "count": len(healthy_services),
                "services": healthy_services
            },
            "unhealthy_services": {
                "count": len(unhealthy_services),
                "services": unhealthy_services
            },
            "unreachable_services": {
                "count": len(unreachable_services),
                "services": unreachable_services
            },
            "overall_health_percentage": round(
                (len(healthy_services) / len(self.health_endpoints)) * 100, 2
            ),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def test_service_dependencies(self, service_name: str) -> Dict[str, Any]:
        """Test dependencies for a specific service"""
        # This would be expanded based on actual service dependencies
        # For now, return a placeholder
        return {
            "service_name": service_name,
            "dependencies": [],
            "message": "Dependency testing not yet implemented",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_configured_endpoints(self) -> Dict[str, str]:
        """Get all configured health endpoints"""
        return self.health_endpoints.copy()
    
    def add_endpoint(self, service_name: str, endpoint: str) -> None:
        """Add a new health endpoint"""
        self.health_endpoints[service_name] = endpoint
        logger.info(f"Added health endpoint for {service_name}: {endpoint}")
    
    def remove_endpoint(self, service_name: str) -> bool:
        """Remove a health endpoint"""
        if service_name in self.health_endpoints:
            del self.health_endpoints[service_name]
            logger.info(f"Removed health endpoint for {service_name}")
            return True
        return False
