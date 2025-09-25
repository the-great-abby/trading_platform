"""
Prometheus Tester for MCP Service
Prometheus query testing and metrics integration
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class PrometheusQueryResult:
    query_name: str
    query: str
    success: bool
    result_count: int
    execution_time: float
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

class PrometheusTester:
    """Prometheus query testing and metrics integration"""
    
    def __init__(self, prometheus_url: str = "http://localhost:11190"):
        self.prometheus_url = prometheus_url
        self.timeout = 30  # seconds
        
        # Prometheus queries configuration
        self.queries = {
            "memory_usage": {
                "query": 'container_memory_usage_bytes{name=~".*{service_name}.*"}',
                "description": "Memory usage for service containers"
            },
            "cpu_usage": {
                "query": 'rate(container_cpu_usage_seconds_total{name=~".*{service_name}.*"}[5m])',
                "description": "CPU usage rate for service containers"
            },
            "response_time": {
                "query": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service="{service_name}"}[5m]))',
                "description": "95th percentile response time"
            },
            "error_rate": {
                "query": 'rate(http_requests_total{service="{service_name}",status=~"5.."}[5m]) / rate(http_requests_total{service="{service_name}"}[5m])',
                "description": "Error rate percentage"
            },
            "request_rate": {
                "query": 'rate(http_requests_total{service="{service_name}"}[5m])',
                "description": "Request rate per second"
            },
            "active_connections": {
                "query": 'http_connections_active{service="{service_name}"}',
                "description": "Active HTTP connections"
            },
            "memory_limit": {
                "query": 'container_spec_memory_limit_bytes{name=~".*{service_name}.*"}',
                "description": "Memory limit for service containers"
            },
            "cpu_limit": {
                "query": 'container_spec_cpu_quota{name=~".*{service_name}.*"}',
                "description": "CPU limit for service containers"
            }
        }
        
        # Service names for testing
        self.services = [
            "unified-analytics-dashboard",
            "unified-trading-dashboard", 
            "unified-news-dashboard",
            "trading-engine",
            "market-data-service",
            "strategy-service",
            "ai-analysis-service",
            "portfolio-management",
            "risk-management",
            "news-service",
            "rss-feed-service",
            "vector-storage",
            "llm-proxy",
            "prometheus",
            "grafana",
            "mcp-service"
        ]
    
    async def test_all_queries(self) -> Dict[str, Any]:
        """Test all Prometheus queries for all services"""
        logger.info("Starting comprehensive Prometheus query testing...")
        
        start_time = datetime.utcnow()
        
        # Test Prometheus connectivity first
        connectivity_test = await self.test_prometheus_connectivity()
        if not connectivity_test["success"]:
            return {
                "success": False,
                "error": "Prometheus is not reachable",
                "connectivity_test": connectivity_test,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Test all queries for all services
        all_results = []
        successful_queries = 0
        failed_queries = 0
        
        for service_name in self.services:
            service_results = await self.test_service_queries(service_name)
            all_results.extend(service_results)
            
            for result in service_results:
                if result.success:
                    successful_queries += 1
                else:
                    failed_queries += 1
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        return {
            "success": successful_queries > 0,
            "total_queries": len(all_results),
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": round((successful_queries / len(all_results)) * 100, 2) if all_results else 0,
            "total_time_seconds": round(total_time, 2),
            "average_execution_time": round(
                sum(r.execution_time for r in all_results if r.success) / successful_queries, 2
            ) if successful_queries > 0 else 0,
            "results": [
                {
                    "query_name": result.query_name,
                    "query": result.query,
                    "success": result.success,
                    "result_count": result.result_count,
                    "execution_time_ms": round(result.execution_time, 2),
                    "error_message": result.error_message,
                    "data": result.data,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in all_results
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def test_service_queries(self, service_name: str) -> List[PrometheusQueryResult]:
        """Test all queries for a specific service"""
        results = []
        
        for query_name, query_config in self.queries.items():
            # Replace {service_name} placeholder
            query = query_config["query"].format(service_name=service_name)
            
            result = await self._execute_query(query_name, query, service_name)
            results.append(result)
        
        return results
    
    async def test_specific_query(self, query_name: str, service_name: str) -> Dict[str, Any]:
        """Test a specific query for a specific service"""
        if query_name not in self.queries:
            return {
                "success": False,
                "error": f"Query {query_name} not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        query_config = self.queries[query_name]
        query = query_config["query"].format(service_name=service_name)
        
        result = await self._execute_query(query_name, query, service_name)
        
        return {
            "success": result.success,
            "query_name": result.query_name,
            "query": result.query,
            "service_name": service_name,
            "result_count": result.result_count,
            "execution_time_ms": round(result.execution_time, 2),
            "error_message": result.error_message,
            "data": result.data,
            "timestamp": result.timestamp.isoformat()
        }
    
    async def test_prometheus_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to Prometheus"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test basic connectivity
                async with session.get(f"{self.prometheus_url}/api/v1/status/config", timeout=10) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "prometheus_url": self.prometheus_url,
                            "status_code": response.status,
                            "reachable": True,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            "success": False,
                            "prometheus_url": self.prometheus_url,
                            "status_code": response.status,
                            "reachable": False,
                            "error": f"HTTP {response.status}",
                            "timestamp": datetime.utcnow().isoformat()
                        }
        
        except Exception as e:
            return {
                "success": False,
                "prometheus_url": self.prometheus_url,
                "reachable": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_query(self, query_name: str, query: str, service_name: str) -> PrometheusQueryResult:
        """Execute a Prometheus query"""
        start_time = datetime.utcnow()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Execute the query
                params = {
                    "query": query,
                    "time": datetime.utcnow().isoformat()
                }
                
                async with session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params=params,
                    timeout=self.timeout
                ) as response:
                    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse the result
                        result_count = 0
                        if "data" in data and "result" in data["data"]:
                            result_count = len(data["data"]["result"])
                        
                        return PrometheusQueryResult(
                            query_name=query_name,
                            query=query,
                            success=True,
                            result_count=result_count,
                            execution_time=execution_time,
                            data=data,
                            timestamp=datetime.utcnow()
                        )
                    else:
                        error_data = await response.text()
                        return PrometheusQueryResult(
                            query_name=query_name,
                            query=query,
                            success=False,
                            result_count=0,
                            execution_time=execution_time,
                            error_message=f"HTTP {response.status}: {error_data}",
                            timestamp=datetime.utcnow()
                        )
        
        except asyncio.TimeoutError:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return PrometheusQueryResult(
                query_name=query_name,
                query=query,
                success=False,
                result_count=0,
                execution_time=execution_time,
                error_message=f"Timeout after {self.timeout} seconds",
                timestamp=datetime.utcnow()
            )
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return PrometheusQueryResult(
                query_name=query_name,
                query=query,
                success=False,
                result_count=0,
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def get_service_metrics(self, service_name: str) -> Dict[str, Any]:
        """Get comprehensive metrics for a service"""
        results = await self.test_service_queries(service_name)
        
        metrics = {}
        for result in results:
            if result.success and result.data:
                metrics[result.query_name] = {
                    "value": result.data.get("data", {}).get("result", []),
                    "execution_time_ms": round(result.execution_time, 2),
                    "result_count": result.result_count
                }
            else:
                metrics[result.query_name] = {
                    "error": result.error_message,
                    "execution_time_ms": round(result.execution_time, 2)
                }
        
        return {
            "service_name": service_name,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get system-wide metrics overview"""
        # Test key system queries
        system_queries = [
            "container_memory_usage_bytes",
            "container_cpu_usage_seconds_total",
            "http_requests_total",
            "http_request_duration_seconds"
        ]
        
        results = {}
        for query in system_queries:
            try:
                async with aiohttp.ClientSession() as session:
                    params = {"query": query}
                    async with session.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params=params,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results[query] = {
                                "success": True,
                                "result_count": len(data.get("data", {}).get("result", [])),
                                "data": data
                            }
                        else:
                            results[query] = {
                                "success": False,
                                "error": f"HTTP {response.status}"
                            }
            except Exception as e:
                results[query] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "system_queries": results,
            "prometheus_url": self.prometheus_url,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_configured_queries(self) -> Dict[str, Dict[str, str]]:
        """Get all configured queries"""
        return self.queries.copy()
    
    def add_query(self, query_name: str, query: str, description: str) -> None:
        """Add a new query"""
        self.queries[query_name] = {
            "query": query,
            "description": description
        }
        logger.info(f"Added Prometheus query: {query_name}")
    
    def remove_query(self, query_name: str) -> bool:
        """Remove a query"""
        if query_name in self.queries:
            del self.queries[query_name]
            logger.info(f"Removed Prometheus query: {query_name}")
            return True
        return False

