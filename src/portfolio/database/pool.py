"""
Database Connection Pool Management
Handles connection pooling, health monitoring, and pool optimization
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool.base import Pool
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PoolMetrics:
    """Database connection pool metrics"""
    size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int
    created: int
    closed: int
    total_connections: int
    active_connections: int
    idle_connections: int
    pool_utilization: float
    overflow_utilization: float
    last_checked: datetime

class PoolHealthMonitor:
    """Monitors database connection pool health"""
    
    def __init__(self, pool: Pool, check_interval: int = 60):
        self.pool = pool
        self.check_interval = check_interval
        self.is_monitoring = False
        self.metrics_history: List[PoolMetrics] = []
        self.max_history = 100
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self):
        """Start pool health monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Database pool health monitoring started")
    
    async def stop_monitoring(self):
        """Stop pool health monitoring"""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Database pool health monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only recent history
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]
                
                # Check for health issues
                await self._check_pool_health(metrics)
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in pool monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def _collect_metrics(self) -> PoolMetrics:
        """Collect current pool metrics"""
        return PoolMetrics(
            size=self.pool.size(),
            checked_in=self.pool.checkedin(),
            checked_out=self.pool.checkedout(),
            overflow=self.pool.overflow(),
            invalid=self.pool.invalid(),
            created=getattr(self.pool, '_created_on_connect', 0),
            closed=getattr(self.pool, '_closed_on_disconnect', 0),
            total_connections=self.pool.size() + self.pool.overflow(),
            active_connections=self.pool.checkedout(),
            idle_connections=self.pool.checkedin(),
            pool_utilization=self.pool.checkedout() / max(self.pool.size(), 1),
            overflow_utilization=self.pool.overflow() / max(self.pool.max_overflow(), 1) if hasattr(self.pool, 'max_overflow') else 0.0,
            last_checked=datetime.now()
        )
    
    async def _check_pool_health(self, metrics: PoolMetrics):
        """Check pool health and log warnings"""
        # Check for high utilization
        if metrics.pool_utilization > 0.8:
            logger.warning(f"High pool utilization: {metrics.pool_utilization:.2%}")
        
        # Check for overflow usage
        if metrics.overflow_utilization > 0.5:
            logger.warning(f"High overflow utilization: {metrics.overflow_utilization:.2%}")
        
        # Check for invalid connections
        if metrics.invalid > 0:
            logger.warning(f"Invalid connections detected: {metrics.invalid}")
        
        # Check for connection leaks
        if metrics.checked_out > metrics.size * 0.9:
            logger.warning(f"Potential connection leak: {metrics.checked_out} connections checked out")
    
    def get_current_metrics(self) -> PoolMetrics:
        """Get current pool metrics"""
        return self._collect_metrics()
    
    def get_metrics_history(self, hours: int = 24) -> List[PoolMetrics]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.last_checked >= cutoff_time]
    
    def get_pool_summary(self) -> Dict[str, Any]:
        """Get pool summary statistics"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.get_metrics_history(hours=1)
        if not recent_metrics:
            recent_metrics = self.metrics_history[-10:] if self.metrics_history else []
        
        avg_utilization = sum(m.pool_utilization for m in recent_metrics) / len(recent_metrics)
        max_utilization = max(m.pool_utilization for m in recent_metrics)
        avg_overflow = sum(m.overflow_utilization for m in recent_metrics) / len(recent_metrics)
        max_overflow = max(m.overflow_utilization for m in recent_metrics)
        
        return {
            "current_metrics": self._collect_metrics(),
            "average_utilization": avg_utilization,
            "max_utilization": max_utilization,
            "average_overflow": avg_overflow,
            "max_overflow": max_overflow,
            "total_invalid": sum(m.invalid for m in recent_metrics),
            "monitoring_duration": len(self.metrics_history),
            "health_status": "HEALTHY" if avg_utilization < 0.8 and avg_overflow < 0.5 else "WARNING"
        }

class PoolOptimizer:
    """Optimizes database connection pool settings"""
    
    def __init__(self, pool: Pool):
        self.pool = pool
        self.optimization_history: List[Dict[str, Any]] = []
    
    def analyze_pool_performance(self, metrics_history: List[PoolMetrics]) -> Dict[str, Any]:
        """Analyze pool performance and provide optimization recommendations"""
        if not metrics_history:
            return {"status": "NO_DATA", "recommendations": []}
        
        recommendations = []
        
        # Analyze utilization patterns
        avg_utilization = sum(m.pool_utilization for m in metrics_history) / len(metrics_history)
        max_utilization = max(m.pool_utilization for m in metrics_history)
        
        # Analyze overflow patterns
        avg_overflow = sum(m.overflow_utilization for m in metrics_history) / len(metrics_history)
        max_overflow = max(m.overflow_utilization for m in metrics_history)
        
        # Pool size recommendations
        if avg_utilization > 0.8:
            recommended_size = int(self.pool.size() * 1.5)
            recommendations.append({
                "type": "INCREASE_POOL_SIZE",
                "current": self.pool.size(),
                "recommended": recommended_size,
                "reason": f"High average utilization: {avg_utilization:.2%}"
            })
        elif avg_utilization < 0.3:
            recommended_size = max(1, int(self.pool.size() * 0.7))
            recommendations.append({
                "type": "DECREASE_POOL_SIZE",
                "current": self.pool.size(),
                "recommended": recommended_size,
                "reason": f"Low average utilization: {avg_utilization:.2%}"
            })
        
        # Overflow recommendations
        if avg_overflow > 0.3:
            if hasattr(self.pool, 'max_overflow'):
                recommended_overflow = int(self.pool.max_overflow() * 1.5)
                recommendations.append({
                    "type": "INCREASE_MAX_OVERFLOW",
                    "current": self.pool.max_overflow(),
                    "recommended": recommended_overflow,
                    "reason": f"High overflow usage: {avg_overflow:.2%}"
                })
        
        return {
            "status": "ANALYZED",
            "average_utilization": avg_utilization,
            "max_utilization": max_utilization,
            "average_overflow": avg_overflow,
            "max_overflow": max_overflow,
            "recommendations": recommendations
        }
    
    def get_optimization_suggestions(self) -> Dict[str, Any]:
        """Get optimization suggestions based on current pool state"""
        current_size = self.pool.size()
        current_overflow = getattr(self.pool, 'max_overflow', lambda: 0)()
        
        suggestions = {
            "pool_size": {
                "current": current_size,
                "min_recommended": max(1, current_size // 2),
                "max_recommended": current_size * 3,
                "optimal_range": f"{max(1, current_size // 2)} - {current_size * 2}"
            },
            "max_overflow": {
                "current": current_overflow,
                "min_recommended": max(0, current_overflow // 2),
                "max_recommended": current_overflow * 3,
                "optimal_range": f"{max(0, current_overflow // 2)} - {current_overflow * 2}"
            },
            "general_recommendations": [
                "Monitor pool utilization during peak hours",
                "Adjust pool size based on application load patterns",
                "Use connection pooling for better resource utilization",
                "Implement connection health checks",
                "Consider read replicas for read-heavy workloads"
            ]
        }
        
        return suggestions

class PoolEventLogger:
    """Logs database pool events for debugging and monitoring"""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.max_events = 1000
    
    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log a pool event"""
        event_data = {
            "timestamp": datetime.now(),
            "type": event_type,
            "details": details
        }
        
        self.events.append(event_data)
        
        # Keep only recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        logger.debug(f"Pool event: {event_type} - {details}")
    
    def get_recent_events(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent events within specified minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [e for e in self.events if e["timestamp"] >= cutoff_time]
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get events of specific type"""
        return [e for e in self.events if e["type"] == event_type]

def setup_pool_event_listeners(engine: Engine, event_logger: PoolEventLogger):
    """Setup SQLAlchemy event listeners for pool monitoring"""
    
    @event.listens_for(engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        event_logger.log_event("CONNECTION_CREATED", {
            "connection_id": id(dbapi_connection)
        })
    
    @event.listens_for(engine, "close")
    def on_close(dbapi_connection, connection_record):
        event_logger.log_event("CONNECTION_CLOSED", {
            "connection_id": id(dbapi_connection)
        })
    
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        event_logger.log_event("CONNECTION_CHECKOUT", {
            "connection_id": id(dbapi_connection)
        })
    
    @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_connection, connection_record):
        event_logger.log_event("CONNECTION_CHECKIN", {
            "connection_id": id(dbapi_connection)
        })
    
    @event.listens_for(engine, "invalidate")
    def on_invalidate(dbapi_connection, connection_record, exception):
        event_logger.log_event("CONNECTION_INVALIDATED", {
            "connection_id": id(dbapi_connection),
            "exception": str(exception) if exception else None
        })

class AdvancedPoolManager:
    """Advanced database pool management with monitoring and optimization"""
    
    def __init__(self, engine: Engine, check_interval: int = 60):
        self.engine = engine
        self.pool = engine.pool
        self.health_monitor = PoolHealthMonitor(self.pool, check_interval)
        self.optimizer = PoolOptimizer(self.pool)
        self.event_logger = PoolEventLogger()
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Setup event listeners for pool monitoring"""
        setup_pool_event_listeners(self.engine, self.event_logger)
    
    async def start_monitoring(self):
        """Start comprehensive pool monitoring"""
        await self.health_monitor.start_monitoring()
        logger.info("Advanced pool monitoring started")
    
    async def stop_monitoring(self):
        """Stop comprehensive pool monitoring"""
        await self.health_monitor.stop_monitoring()
        logger.info("Advanced pool monitoring stopped")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get comprehensive pool status"""
        current_metrics = self.health_monitor.get_current_metrics()
        summary = self.health_monitor.get_pool_summary()
        optimization_analysis = self.optimizer.analyze_pool_performance(
            self.health_monitor.get_metrics_history(hours=1)
        )
        optimization_suggestions = self.optimizer.get_optimization_suggestions()
        recent_events = self.event_logger.get_recent_events(minutes=10)
        
        return {
            "current_metrics": current_metrics,
            "summary": summary,
            "optimization_analysis": optimization_analysis,
            "optimization_suggestions": optimization_suggestions,
            "recent_events": recent_events,
            "monitoring_active": self.health_monitor.is_monitoring,
            "pool_type": type(self.pool).__name__,
            "engine_url": str(self.engine.url).replace(self.engine.url.password or "", "***") if self.engine.url.password else str(self.engine.url)
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get detailed performance report"""
        metrics_history = self.health_monitor.get_metrics_history(hours)
        events = self.event_logger.get_recent_events(minutes=hours * 60)
        
        if not metrics_history:
            return {"status": "NO_DATA"}
        
        # Calculate performance metrics
        avg_utilization = sum(m.pool_utilization for m in metrics_history) / len(metrics_history)
        max_utilization = max(m.pool_utilization for m in metrics_history)
        avg_overflow = sum(m.overflow_utilization for m in metrics_history) / len(metrics_history)
        max_overflow = max(m.overflow_utilization for m in metrics_history)
        
        # Count events by type
        event_counts = {}
        for event in events:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "period_hours": hours,
            "data_points": len(metrics_history),
            "performance_metrics": {
                "average_utilization": avg_utilization,
                "max_utilization": max_utilization,
                "average_overflow": avg_overflow,
                "max_overflow": max_overflow,
                "total_connections_created": sum(m.created for m in metrics_history),
                "total_connections_closed": sum(m.closed for m in metrics_history),
                "total_invalid_connections": sum(m.invalid for m in metrics_history)
            },
            "event_summary": event_counts,
            "recommendations": self.optimizer.analyze_pool_performance(metrics_history).get("recommendations", [])
        }
























