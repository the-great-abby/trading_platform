"""
Database Health Monitoring
Comprehensive health monitoring for database connections and performance
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import psutil
import os

logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """Database health check result"""
    status: str  # HEALTHY, WARNING, CRITICAL
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    active_connections: int
    max_connections: int
    connection_utilization: float
    query_count: int
    avg_query_time_ms: float
    slow_queries: int
    deadlocks: int
    cache_hit_ratio: float
    disk_usage_percent: float
    memory_usage_percent: float
    cpu_usage_percent: float

class DatabaseHealthMonitor:
    """Comprehensive database health monitoring"""
    
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.health_history: List[HealthCheckResult] = []
        self.metrics_history: List[DatabaseMetrics] = []
        self.max_history = 1000
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._check_interval = 30  # seconds
    
    async def start_monitoring(self, check_interval: int = 30):
        """Start continuous health monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self._check_interval = check_interval
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Database health monitoring started (interval: {check_interval}s)")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Database health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Perform health check
                health_result = await self.perform_health_check()
                self.health_history.append(health_result)
                
                # Collect metrics
                metrics = await self.collect_metrics()
                if metrics:
                    self.metrics_history.append(metrics)
                
                # Keep history manageable
                self._trim_history()
                
                # Log warnings/critical issues
                if health_result.status in ["WARNING", "CRITICAL"]:
                    logger.warning(f"Database health issue: {health_result.status} - {health_result.error_message}")
                
                await asyncio.sleep(self._check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self._check_interval)
    
    def _trim_history(self):
        """Trim history to keep it manageable"""
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
    
    async def perform_health_check(self) -> HealthCheckResult:
        """Perform comprehensive database health check"""
        start_time = time.time()
        
        try:
            # Basic connectivity check
            async with self.database_manager.get_session() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                health_check = result.scalar()
            
            response_time = (time.time() - start_time) * 1000
            
            if health_check != 1:
                return HealthCheckResult(
                    status="CRITICAL",
                    response_time_ms=response_time,
                    error_message="Health check query returned unexpected result"
                )
            
            # Additional health checks
            health_details = await self._perform_detailed_health_checks()
            
            # Determine overall status
            status = self._determine_health_status(response_time, health_details)
            
            return HealthCheckResult(
                status=status,
                response_time_ms=response_time,
                details=health_details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                status="CRITICAL",
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _perform_detailed_health_checks(self) -> Dict[str, Any]:
        """Perform detailed health checks"""
        details = {}
        
        try:
            async with self.database_manager.get_session() as session:
                # Check database version
                version_result = await session.execute(text("SELECT version()"))
                details["version"] = version_result.scalar()
                
                # Check active connections
                connections_result = await session.execute(text("""
                    SELECT count(*) as active_connections 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """))
                details["active_connections"] = connections_result.scalar()
                
                # Check database size
                size_result = await session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """))
                details["database_size"] = size_result.scalar()
                
                # Check for long-running queries
                long_queries_result = await session.execute(text("""
                    SELECT count(*) as long_running_queries
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND query_start < NOW() - INTERVAL '5 minutes'
                """))
                details["long_running_queries"] = long_queries_result.scalar()
                
                # Check for locks
                locks_result = await session.execute(text("""
                    SELECT count(*) as active_locks
                    FROM pg_locks 
                    WHERE granted = false
                """))
                details["active_locks"] = locks_result.scalar()
                
                # Check cache hit ratio
                cache_result = await session.execute(text("""
                    SELECT 
                        round(100 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) as cache_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """))
                details["cache_hit_ratio"] = cache_result.scalar() or 0.0
                
        except Exception as e:
            details["health_check_error"] = str(e)
        
        return details
    
    def _determine_health_status(self, response_time: float, details: Dict[str, Any]) -> str:
        """Determine overall health status based on metrics"""
        # Check response time
        if response_time > 5000:  # 5 seconds
            return "CRITICAL"
        elif response_time > 1000:  # 1 second
            return "WARNING"
        
        # Check active connections
        active_connections = details.get("active_connections", 0)
        if active_connections > 80:
            return "CRITICAL"
        elif active_connections > 60:
            return "WARNING"
        
        # Check long-running queries
        long_queries = details.get("long_running_queries", 0)
        if long_queries > 5:
            return "CRITICAL"
        elif long_queries > 2:
            return "WARNING"
        
        # Check active locks
        active_locks = details.get("active_locks", 0)
        if active_locks > 10:
            return "CRITICAL"
        elif active_locks > 5:
            return "WARNING"
        
        # Check cache hit ratio
        cache_hit_ratio = details.get("cache_hit_ratio", 100.0)
        if cache_hit_ratio < 80:
            return "CRITICAL"
        elif cache_hit_ratio < 90:
            return "WARNING"
        
        return "HEALTHY"
    
    async def collect_metrics(self) -> Optional[DatabaseMetrics]:
        """Collect database performance metrics"""
        try:
            async with self.database_manager.get_session() as session:
                # Get connection metrics
                connections_result = await session.execute(text("""
                    SELECT 
                        count(*) as active_connections,
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """))
                conn_data = connections_result.fetchone()
                
                # Get query metrics
                query_result = await session.execute(text("""
                    SELECT 
                        sum(calls) as total_calls,
                        avg(total_time) as avg_time_ms,
                        sum(calls) FILTER (WHERE mean_time > 1000) as slow_queries
                    FROM pg_stat_statements
                """))
                query_data = query_result.fetchone()
                
                # Get deadlock count
                deadlock_result = await session.execute(text("""
                    SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()
                """))
                deadlocks = deadlock_result.scalar() or 0
                
                # Get cache hit ratio
                cache_result = await session.execute(text("""
                    SELECT 
                        round(100 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) as cache_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """))
                cache_hit_ratio = cache_result.scalar() or 100.0
                
                # Get system metrics
                disk_usage = psutil.disk_usage('/').percent
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)
                
                return DatabaseMetrics(
                    active_connections=conn_data.active_connections,
                    max_connections=conn_data.max_connections,
                    connection_utilization=conn_data.active_connections / conn_data.max_connections,
                    query_count=query_data.total_calls or 0,
                    avg_query_time_ms=query_data.avg_time_ms or 0.0,
                    slow_queries=query_data.slow_queries or 0,
                    deadlocks=deadlocks,
                    cache_hit_ratio=cache_hit_ratio,
                    disk_usage_percent=disk_usage,
                    memory_usage_percent=memory.percent,
                    cpu_usage_percent=cpu_percent
                )
                
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return None
    
    def get_current_health(self) -> HealthCheckResult:
        """Get current health status"""
        if self.health_history:
            return self.health_history[-1]
        return HealthCheckResult(status="UNKNOWN", response_time_ms=0.0)
    
    def get_health_history(self, hours: int = 24) -> List[HealthCheckResult]:
        """Get health history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [h for h in self.health_history if h.timestamp >= cutoff_time]
    
    def get_metrics_history(self, hours: int = 24) -> List[DatabaseMetrics]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if hasattr(m, 'timestamp') and m.timestamp >= cutoff_time]
    
    def get_health_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get health summary for specified period"""
        health_history = self.get_health_history(hours)
        metrics_history = self.get_metrics_history(hours)
        
        if not health_history:
            return {"status": "NO_DATA"}
        
        # Calculate health statistics
        total_checks = len(health_history)
        healthy_checks = len([h for h in health_history if h.status == "HEALTHY"])
        warning_checks = len([h for h in health_history if h.status == "WARNING"])
        critical_checks = len([h for h in health_history if h.status == "CRITICAL"])
        
        avg_response_time = sum(h.response_time_ms for h in health_history) / total_checks
        max_response_time = max(h.response_time_ms for h in health_history)
        min_response_time = min(h.response_time_ms for h in health_history)
        
        # Calculate uptime percentage
        uptime_percentage = (healthy_checks + warning_checks) / total_checks * 100
        
        # Calculate metrics averages
        avg_metrics = {}
        if metrics_history:
            avg_metrics = {
                "avg_connection_utilization": sum(m.connection_utilization for m in metrics_history) / len(metrics_history),
                "avg_query_time": sum(m.avg_query_time_ms for m in metrics_history) / len(metrics_history),
                "avg_cache_hit_ratio": sum(m.cache_hit_ratio for m in metrics_history) / len(metrics_history),
                "avg_disk_usage": sum(m.disk_usage_percent for m in metrics_history) / len(metrics_history),
                "avg_memory_usage": sum(m.memory_usage_percent for m in metrics_history) / len(metrics_history),
                "avg_cpu_usage": sum(m.cpu_usage_percent for m in metrics_history) / len(metrics_history)
            }
        
        return {
            "period_hours": hours,
            "total_checks": total_checks,
            "health_distribution": {
                "healthy": healthy_checks,
                "warning": warning_checks,
                "critical": critical_checks
            },
            "uptime_percentage": uptime_percentage,
            "response_time_stats": {
                "average": avg_response_time,
                "maximum": max_response_time,
                "minimum": min_response_time
            },
            "average_metrics": avg_metrics,
            "current_status": self.get_current_health().status,
            "last_check": self.get_current_health().timestamp.isoformat() if self.health_history else None
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts based on health status"""
        alerts = []
        current_health = self.get_current_health()
        
        if current_health.status == "CRITICAL":
            alerts.append({
                "severity": "CRITICAL",
                "message": f"Database is in critical state: {current_health.error_message}",
                "timestamp": current_health.timestamp.isoformat(),
                "response_time": current_health.response_time_ms
            })
        elif current_health.status == "WARNING":
            alerts.append({
                "severity": "WARNING",
                "message": f"Database health warning: {current_health.error_message}",
                "timestamp": current_health.timestamp.isoformat(),
                "response_time": current_health.response_time_ms
            })
        
        # Check for trends
        recent_health = self.get_health_history(hours=1)
        if len(recent_health) >= 3:
            recent_statuses = [h.status for h in recent_health[-3:]]
            if recent_statuses.count("CRITICAL") >= 2:
                alerts.append({
                    "severity": "CRITICAL",
                    "message": "Multiple critical health checks in the last hour",
                    "timestamp": datetime.now().isoformat()
                })
            elif recent_statuses.count("WARNING") >= 3:
                alerts.append({
                    "severity": "WARNING",
                    "message": "Multiple warning health checks in the last hour",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts

# Global health monitor instance
_health_monitor: Optional[DatabaseHealthMonitor] = None

def get_health_monitor() -> Optional[DatabaseHealthMonitor]:
    """Get global health monitor instance"""
    return _health_monitor

async def initialize_health_monitoring(database_manager, check_interval: int = 30):
    """Initialize global health monitoring"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = DatabaseHealthMonitor(database_manager)
        await _health_monitor.start_monitoring(check_interval)
        logger.info("Database health monitoring initialized")

async def stop_health_monitoring():
    """Stop global health monitoring"""
    global _health_monitor
    if _health_monitor:
        await _health_monitor.stop_monitoring()
        _health_monitor = None
        logger.info("Database health monitoring stopped")

