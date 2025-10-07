"""
Health check service for validation framework

This service provides health check endpoints and monitoring capabilities
for the validation framework components.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from .database_adapter import DatabaseAdapter

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status information"""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None


class HealthChecker:
    """
    Health check service for validation framework components.
    """
    
    def __init__(self):
        self.database_adapter = DatabaseAdapter()
        self.checks = []
    
    async def check_database(self) -> HealthStatus:
        """Check database connectivity and health."""
        try:
            health_data = await self.database_adapter.health_check()
            
            if health_data["status"] == "healthy":
                return HealthStatus(
                    component="database",
                    status="healthy",
                    message="Database connection and tables are accessible",
                    timestamp=datetime.now(),
                    details=health_data
                )
            else:
                return HealthStatus(
                    component="database",
                    status="unhealthy",
                    message=f"Database health check failed: {health_data.get('error', 'Unknown error')}",
                    timestamp=datetime.now(),
                    details=health_data
                )
                
        except Exception as e:
            return HealthStatus(
                component="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    async def check_disk_space(self) -> HealthStatus:
        """Check available disk space."""
        try:
            import shutil
            
            # Check disk space for current directory
            total, used, free = shutil.disk_usage(".")
            free_percent = (free / total) * 100
            
            if free_percent > 20:
                status = "healthy"
                message = f"Disk space available: {free_percent:.1f}%"
            elif free_percent > 10:
                status = "degraded"
                message = f"Low disk space: {free_percent:.1f}%"
            else:
                status = "unhealthy"
                message = f"Critical disk space: {free_percent:.1f}%"
            
            return HealthStatus(
                component="disk_space",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "total_bytes": total,
                    "used_bytes": used,
                    "free_bytes": free,
                    "free_percent": free_percent
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="disk_space",
                status="unhealthy",
                message=f"Failed to check disk space: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    async def check_memory(self) -> HealthStatus:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent < 80:
                status = "healthy"
                message = f"Memory usage: {memory_percent:.1f}%"
            elif memory_percent < 90:
                status = "degraded"
                message = f"High memory usage: {memory_percent:.1f}%"
            else:
                status = "unhealthy"
                message = f"Critical memory usage: {memory_percent:.1f}%"
            
            return HealthStatus(
                component="memory",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_bytes": memory.used,
                    "percent": memory_percent
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="memory",
                status="unhealthy",
                message=f"Failed to check memory: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    async def check_cpu(self) -> HealthStatus:
        """Check CPU usage."""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent < 80:
                status = "healthy"
                message = f"CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent < 90:
                status = "degraded"
                message = f"High CPU usage: {cpu_percent:.1f}%"
            else:
                status = "unhealthy"
                message = f"Critical CPU usage: {cpu_percent:.1f}%"
            
            return HealthStatus(
                component="cpu",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "cpu_percent": cpu_percent,
                    "cpu_count": psutil.cpu_count()
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="cpu",
                status="unhealthy",
                message=f"Failed to check CPU: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        checks = [
            self.check_database(),
            self.check_disk_space(),
            self.check_memory(),
            self.check_cpu()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Process results
        health_results = []
        overall_status = "healthy"
        
        for result in results:
            if isinstance(result, Exception):
                health_results.append(HealthStatus(
                    component="unknown",
                    status="unhealthy",
                    message=f"Health check failed: {str(result)}",
                    timestamp=datetime.now(),
                    details={"error": str(result)}
                ))
                overall_status = "unhealthy"
            else:
                health_results.append(result)
                if result.status == "unhealthy":
                    overall_status = "unhealthy"
                elif result.status == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": [
                {
                    "component": check.component,
                    "status": check.status,
                    "message": check.message,
                    "details": check.details
                }
                for check in health_results
            ]
        }
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health."""
        health_data = await self.run_all_checks()
        
        # Count status types
        status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}
        for check in health_data["checks"]:
            status_counts[check["status"]] += 1
        
        return {
            "overall_status": health_data["status"],
            "timestamp": health_data["timestamp"],
            "component_status": status_counts,
            "total_components": len(health_data["checks"]),
            "details": health_data["checks"]
        }











