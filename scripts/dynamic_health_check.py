#!/usr/bin/env python3
"""
Dynamic Health Check System
Actually tests real connectivity between services instead of just checking pod status
"""

import asyncio
import aiohttp
import psycopg2
import redis
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DynamicHealthChecker:
    """Real-time health checker that tests actual service connectivity"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    async def check_service_connectivity(self, service_name: str, url: str, timeout: int = 5) -> Dict[str, Any]:
        """Test if a service is actually responding to HTTP requests"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                start_time = time.time()
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    return {
                        "status": "healthy" if response.status == 200 else "degraded",
                        "response_time": round(response_time * 1000, 2),  # ms
                        "status_code": response.status,
                        "error": None
                    }
        except asyncio.TimeoutError:
            return {"status": "timeout", "response_time": None, "status_code": None, "error": "Request timed out"}
        except Exception as e:
            return {"status": "error", "response_time": None, "status_code": None, "error": str(e)}
    
    async def check_database_connectivity(self, service_name: str, connection_string: str) -> Dict[str, Any]:
        """Test if database connections are actually working"""
        try:
            start_time = time.time()
            conn = psycopg2.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            response_time = time.time() - start_time
            cursor.close()
            conn.close()
            
            return {
                "status": "healthy",
                "response_time": round(response_time * 1000, 2),
                "error": None
            }
        except Exception as e:
            return {"status": "error", "response_time": None, "error": str(e)}
    
    async def check_redis_connectivity(self, service_name: str, redis_url: str) -> Dict[str, Any]:
        """Test if Redis connections are actually working"""
        try:
            start_time = time.time()
            r = redis.from_url(redis_url, socket_connect_timeout=5, socket_timeout=5)
            r.ping()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": round(response_time * 1000, 2),
                "error": None
            }
        except Exception as e:
            return {"status": "error", "response_time": None, "error": str(e)}
    
    async def check_internal_service_communication(self, service_name: str, target_service: str, port: int) -> Dict[str, Any]:
        """Test if services can communicate with each other within the cluster"""
        try:
            # Get the first available pod for the service
            cmd = f"kubectl get pods -n trading-system -l app={service_name} --no-headers -o custom-columns=NAME:.metadata.name | head -1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0 or not result.stdout.strip():
                return {"status": "error", "error": f"Could not find pod for service {service_name}"}
            
            pod_name = result.stdout.strip()
            
            # Test communication from the pod
            cmd = f"kubectl exec {pod_name} -n trading-system -- curl -s --connect-timeout 5 http://{target_service}:{port}/health"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {"status": "healthy", "error": None}
            else:
                return {"status": "error", "error": f"Communication failed: {result.stderr}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_api_endpoints(self, service_name: str, base_url: str, endpoints: List[str]) -> Dict[str, Any]:
        """Test specific API endpoints of a service"""
        results = {}
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    start_time = time.time()
                    async with session.get(url) as response:
                        response_time = time.time() - start_time
                        results[endpoint] = {
                            "status": "healthy" if response.status == 200 else "degraded",
                            "response_time": round(response_time * 1000, 2),
                            "status_code": response.status
                        }
            except Exception as e:
                results[endpoint] = {"status": "error", "response_time": None, "status_code": None, "error": str(e)}
        
        return results
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive results"""
        logger.info("🚀 Starting comprehensive dynamic health check...")
        
        # Test external service connectivity (via port-forward)
        external_checks = await asyncio.gather(
            self.check_service_connectivity("unified-trading-dashboard", "http://localhost:11115/health"),
            self.check_service_connectivity("unified-news-dashboard", "http://localhost:11113/health"),
            self.check_service_connectivity("unified-analytics-dashboard", "http://localhost:11114/health"),
            self.check_service_connectivity("backtest-api", "http://localhost:11102/health"),
        )
        
        # Test database connectivity
        db_checks = await asyncio.gather(
            self.check_database_connectivity("timescaledb", "postgresql://trading_user:trading_pass@localhost:5432/trading_bot"),
        )
        
        # Test vector storage connectivity
        vector_checks = await asyncio.gather(
            self.check_service_connectivity("postgres-vector-storage", "http://localhost:11180/health"),
        )
        
        # Test Redis connectivity
        redis_checks = await asyncio.gather(
            self.check_redis_connectivity("redis", "redis://localhost:11379"),
        )
        
        # Test internal service communication (if we can access the cluster)
        try:
            internal_checks = await asyncio.gather(
                self.check_internal_service_communication("unified-trading-dashboard", "backtest-api", 11101),
                self.check_internal_service_communication("unified-news-dashboard", "rss-feed-service", 11004),
            )
        except Exception as e:
            internal_checks = [{"status": "skipped", "error": "Cluster access not available"}]
        
        # Test internal service communication (now that containers have curl)
        try:
            internal_checks = await asyncio.gather(
                self.check_internal_service_communication("unified-trading-dashboard", "backtest-api", 11101),
                self.check_internal_service_communication("unified-news-dashboard", "rss-feed-service", 11004),
            )
        except Exception as e:
            internal_checks = [
                {"status": "error", "error": f"Internal communication test failed: {str(e)}"},
                {"status": "error", "error": f"Internal communication test failed: {str(e)}"}
            ]
        
        # Compile results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "check_duration": round((datetime.now() - self.start_time).total_seconds(), 2),
            "external_services": {
                "unified-trading-dashboard": external_checks[0],
                "unified-news-dashboard": external_checks[1],
                "unified-analytics-dashboard": external_checks[2],
                "backtest-api": external_checks[3],
            },
            "databases": {
                "timescaledb": db_checks[0],
            },
            "vector_storage": {
                "postgres-vector-storage": vector_checks[0],
            },
            "caches": {
                "redis": redis_checks[0],
            },
            "internal_communication": {
                "trading-to-backtest": internal_checks[0] if len(internal_checks) > 0 else {"status": "skipped"},
                "news-to-rss": internal_checks[1] if len(internal_checks) > 1 else {"status": "skipped"},
            }
        }
        
        return self.results
    
    def generate_summary_report(self) -> str:
        """Generate a human-readable summary of the health check results"""
        if not self.results:
            return "❌ No health check results available"
        
        report = []
        report.append("🔍 DYNAMIC HEALTH CHECK SUMMARY")
        report.append("=" * 50)
        report.append(f"⏰ Timestamp: {self.results['timestamp']}")
        report.append(f"⏱️  Duration: {self.results['check_duration']}s")
        report.append("")
        
        # External Services
        report.append("🌐 EXTERNAL SERVICES (Port-Forward Access):")
        for service, result in self.results["external_services"].items():
            status_emoji = "✅" if result["status"] == "healthy" else "⚠️" if result["status"] == "degraded" else "❌"
            response_time = f"({result['response_time']}ms)" if result.get("response_time") else ""
            error_msg = f" - {result['error']}" if result.get("error") else ""
            report.append(f"  {status_emoji} {service}: {result['status']} {response_time}{error_msg}")
        
        report.append("")
        
        # Databases
        report.append("🗄️  DATABASES:")
        for db, result in self.results["databases"].items():
            status_emoji = "✅" if result["status"] == "healthy" else "❌"
            response_time = f"({result['response_time']}ms)" if result.get("response_time") else ""
            error_msg = f" - {result['error']}" if result.get("error") else ""
            report.append(f"  {status_emoji} {db}: {result['status']} {response_time}{error_msg}")
        
        report.append("")
        
        # Caches
        report.append("💾 CACHES:")
        for cache, result in self.results["caches"].items():
            status_emoji = "✅" if result["status"] == "healthy" else "❌"
            response_time = f"({result['response_time']}ms)" if result.get("response_time") else ""
            error_msg = f" - {result['error']}" if result.get("error") else ""
            report.append(f"  {status_emoji} {cache}: {result['status']} {response_time}{error_msg}")
        
        report.append("")
        
        # Vector Storage
        report.append("🧠 VECTOR STORAGE:")
        for vector, result in self.results["vector_storage"].items():
            status_emoji = "✅" if result["status"] == "healthy" else "❌"
            response_time = f"({result['response_time']}ms)" if result.get("response_time") else ""
            error_msg = f" - {result['error']}" if result.get("error") else ""
            report.append(f"  {status_emoji} {vector}: {result['status']} {response_time}{error_msg}")
        
        report.append("")
        
        # Internal Communication
        report.append("🔗 INTERNAL SERVICE COMMUNICATION:")
        for comm, result in self.results["internal_communication"].items():
            status_emoji = "✅" if result["status"] == "healthy" else "❌"
            error_msg = f" - {result['error']}" if result.get("error") else ""
            report.append(f"  {status_emoji} {comm}: {result['status']}{error_msg}")
        
        report.append("")
        
        # Overall Health with weighted scoring
        external_services = self.results["external_services"]
        database_services = self.results["databases"]
        cache_services = self.results["caches"]
        
        # Calculate weighted health score
        external_weight = 0.5  # 50% weight for external services
        database_weight = 0.2  # 20% weight for databases
        vector_weight = 0.2    # 20% weight for vector storage
        cache_weight = 0.1     # 10% weight for caches
        
        external_healthy = sum(1 for service in external_services.values() if service["status"] == "healthy")
        external_total = len(external_services)
        external_score = external_healthy / external_total if external_total > 0 else 0
        
        database_healthy = sum(1 for service in database_services.values() if service["status"] == "healthy")
        database_total = len(database_services)
        database_score = database_healthy / database_total if database_total > 0 else 0
        
        cache_healthy = sum(1 for service in cache_services.values() if service["status"] == "healthy")
        cache_total = len(cache_services)
        cache_score = cache_healthy / cache_total if cache_total > 0 else 0
        
        vector_healthy = sum(1 for service in self.results["vector_storage"].values() if service["status"] == "healthy")
        vector_total = len(self.results["vector_storage"])
        vector_score = vector_healthy / vector_total if vector_total > 0 else 0
        
        weighted_score = (external_score * external_weight) + (database_score * database_weight) + (vector_score * vector_weight) + (cache_score * cache_weight)
        weighted_percentage = round(weighted_score * 100, 1)
        
        if weighted_percentage >= 95:
            report.append("🎉 OVERALL STATUS: ALL SYSTEMS OPERATIONAL")
        elif weighted_percentage >= 80:
            report.append("✅ OVERALL STATUS: GOOD PERFORMANCE")
        elif weighted_percentage >= 70:
            report.append("⚠️  OVERALL STATUS: DEGRADED PERFORMANCE")
        else:
            report.append("🚨 OVERALL STATUS: CRITICAL ISSUES DETECTED")
        
        report.append(f"📊 Health Score: {weighted_percentage}% (Weighted)")
        report.append(f"  • External Services: {external_healthy}/{external_total} ({round(external_score*100, 1)}%)")
        report.append(f"  • Databases: {database_healthy}/{database_total} ({round(database_score*100, 1)}%)")
        report.append(f"  • Vector Storage: {vector_healthy}/{vector_total} ({round(vector_score*100, 1)}%)")
        report.append(f"  • Caches: {cache_healthy}/{cache_total} ({round(cache_score*100, 1)}%)")
        
        return "\n".join(report)

async def main():
    """Main function to run the health check"""
    checker = DynamicHealthChecker()
    
    try:
        # Run the health check
        results = await checker.run_comprehensive_health_check()
        
        # Generate and display the report
        report = checker.generate_summary_report()
        print(report)
        
        # Save results to file
        with open("dynamic_health_check_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: dynamic_health_check_results.json")
        
        # Add port watcher recommendation
        print(f"\n🔌 PORT FORWARDING RECOMMENDATION:")
        print(f"   For consistent, automated port forwarding of ALL services:")
        print(f"   Run: make port-watcher")
        print(f"   This will automatically manage all port forwarding and ensure consistency")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
