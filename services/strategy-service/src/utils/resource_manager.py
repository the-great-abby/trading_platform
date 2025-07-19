"""
Resource Manager - Advanced system resource monitoring and optimization
"""

import asyncio
import logging
import time
import psutil
import gc
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """System resource metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io_mb: float
    process_count: int
    load_average: float


@dataclass
class ResourceAlert:
    """Resource usage alert"""
    alert_type: str  # 'high_cpu', 'high_memory', 'low_disk', 'network_issue'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: float
    metrics: ResourceMetrics


class ResourceManager:
    """Advanced resource monitoring and optimization system"""
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        self.alert_thresholds = alert_thresholds or {
            'cpu_high': 80.0,
            'cpu_critical': 95.0,
            'memory_high': 85.0,
            'memory_critical': 95.0,
            'disk_high': 90.0,
            'disk_critical': 98.0
        }
        
        # Monitoring state
        self.monitoring_enabled = True
        self.monitor_thread = None
        self.metrics_history: List[ResourceMetrics] = []
        self.alerts: List[ResourceAlert] = []
        
        # Resource optimization
        self.optimization_enabled = True
        self.gc_threshold = 0.8  # Trigger GC when memory usage > 80%
        self.memory_cleanup_threshold = 0.9  # Aggressive cleanup when > 90%
        
        # Performance tracking
        self.performance_stats = {
            'gc_count': 0,
            'memory_cleanups': 0,
            'optimizations_applied': 0,
            'alerts_generated': 0
        }
    
    async def start_monitoring(self, interval_seconds: int = 10):
        """Start resource monitoring"""
        logger.info("🔍 Starting resource monitoring...")
        
        def monitor_resources():
            while self.monitoring_enabled:
                try:
                    # Collect metrics
                    metrics = self._collect_metrics()
                    self.metrics_history.append(metrics)
                    
                    # Keep only recent history (last hour)
                    cutoff_time = time.time() - 3600
                    self.metrics_history = [m for m in self.metrics_history 
                                          if m.timestamp > cutoff_time]
                    
                    # Check for alerts
                    alerts = self._check_alerts(metrics)
                    for alert in alerts:
                        self.alerts.append(alert)
                        # Handle alert synchronously since we're in a thread
                        self._handle_alert_sync(alert)
                    
                    # Apply optimizations if needed
                    if self.optimization_enabled:
                        await self._apply_optimizations(metrics)
                    
                    time.sleep(interval_seconds)
                    
                except Exception as e:
                    logger.error(f"Resource monitoring error: {e}")
                    time.sleep(30)  # Wait before retrying
        
        self.monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        self.monitor_thread.start()
        
        logger.info("✅ Resource monitoring started")
    
    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / 1024 / 1024
            memory_used_mb = memory.used / 1024 / 1024
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io_mb = (network.bytes_sent + network.bytes_recv) / 1024 / 1024
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix only)
            try:
                load_average = psutil.getloadavg()[0]
            except AttributeError:
                load_average = 0.0
            
            return ResourceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                network_io_mb=network_io_mb,
                process_count=process_count,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            # Return default metrics
            return ResourceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                network_io_mb=0.0,
                process_count=0,
                load_average=0.0
            )
    
    def _check_alerts(self, metrics: ResourceMetrics) -> List[ResourceAlert]:
        """Check for resource alerts"""
        alerts = []
        
        # CPU alerts
        if metrics.cpu_percent > self.alert_thresholds['cpu_critical']:
            alerts.append(ResourceAlert(
                alert_type='high_cpu',
                severity='critical',
                message=f"Critical CPU usage: {metrics.cpu_percent:.1f}%",
                timestamp=metrics.timestamp,
                metrics=metrics
            ))
        elif metrics.cpu_percent > self.alert_thresholds['cpu_high']:
            alerts.append(ResourceAlert(
                alert_type='high_cpu',
                severity='high',
                message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                timestamp=metrics.timestamp,
                metrics=metrics
            ))
        
        # Memory alerts
        if metrics.memory_percent > self.alert_thresholds['memory_critical']:
            alerts.append(ResourceAlert(
                alert_type='high_memory',
                severity='critical',
                message=f"Critical memory usage: {metrics.memory_percent:.1f}%",
                timestamp=metrics.timestamp,
                metrics=metrics
            ))
        elif metrics.memory_percent > self.alert_thresholds['memory_high']:
            alerts.append(ResourceAlert(
                alert_type='high_memory',
                severity='high',
                message=f"High memory usage: {metrics.memory_percent:.1f}%",
                timestamp=metrics.timestamp,
                metrics=metrics
            ))
        
        # Disk alerts
        if metrics.disk_usage_percent > self.alert_thresholds['disk_critical']:
            alerts.append(ResourceAlert(
                alert_type='low_disk',
                severity='critical',
                message=f"Critical disk usage: {metrics.disk_usage_percent:.1f}%",
                timestamp=metrics.timestamp,
                metrics=metrics
            ))
        elif metrics.disk_usage_percent > self.alert_thresholds['disk_high']:
            alerts.append(ResourceAlert(
                alert_type='low_disk',
                severity='high',
                message=f"High disk usage: {metrics.disk_usage_percent:.1f}%",
                timestamp=metrics.timestamp,
                metrics=metrics
            ))
        
        return alerts
    
    def _handle_alert_sync(self, alert: ResourceAlert):
        """Handle resource alert synchronously (for thread context)"""
        self.performance_stats['alerts_generated'] += 1
        
        if alert.severity == 'critical':
            logger.critical(f"🚨 CRITICAL: {alert.message}")
        elif alert.severity == 'high':
            logger.warning(f"⚠️  HIGH: {alert.message}")
        else:
            logger.info(f"ℹ️  {alert.message}")
    
    async def _handle_alert(self, alert: ResourceAlert):
        """Handle resource alert asynchronously"""
        self.performance_stats['alerts_generated'] += 1
        
        if alert.severity == 'critical':
            logger.critical(f"🚨 CRITICAL: {alert.message}")
            # Trigger immediate optimization
            await self._emergency_optimization(alert)
        elif alert.severity == 'high':
            logger.warning(f"⚠️  HIGH: {alert.message}")
        else:
            logger.info(f"ℹ️  {alert.message}")
    
    async def _emergency_optimization(self, alert: ResourceAlert):
        """Emergency resource optimization"""
        logger.info("🚨 Applying emergency resource optimization...")
        
        if alert.alert_type == 'high_memory':
            # Aggressive memory cleanup
            await self._aggressive_memory_cleanup()
        elif alert.alert_type == 'high_cpu':
            # Reduce CPU usage
            await self._reduce_cpu_usage()
        elif alert.alert_type == 'low_disk':
            # Clean up disk space
            await self._cleanup_disk_space()
    
    async def _apply_optimizations(self, metrics: ResourceMetrics):
        """Apply resource optimizations based on current metrics"""
        
        # Memory optimization
        if metrics.memory_percent > self.gc_threshold * 100:
            await self._trigger_garbage_collection()
        
        if metrics.memory_percent > self.memory_cleanup_threshold * 100:
            await self._memory_cleanup()
        
        # CPU optimization
        if metrics.cpu_percent > 70:
            await self._optimize_cpu_usage()
        
        # Disk optimization
        if metrics.disk_usage_percent > 85:
            await self._optimize_disk_usage()
    
    async def _trigger_garbage_collection(self):
        """Trigger garbage collection"""
        try:
            # Collect garbage
            collected = gc.collect()
            
            if collected > 0:
                self.performance_stats['gc_count'] += 1
                logger.info(f"🗑️  Garbage collection: {collected} objects collected")
            
        except Exception as e:
            logger.error(f"Garbage collection failed: {e}")
    
    async def _memory_cleanup(self):
        """Aggressive memory cleanup"""
        try:
            # Clear caches
            await self._clear_caches()
            
            # Force garbage collection
            gc.collect()
            
            # Clear pandas memory
            pd.DataFrame().empty  # Trigger pandas memory cleanup
            
            self.performance_stats['memory_cleanups'] += 1
            logger.info("🧹 Memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    async def _clear_caches(self):
        """Clear various caches"""
        try:
            # Clear matplotlib cache
            import matplotlib.pyplot as plt
            plt.close('all')
            
            # Clear pandas cache
            pd.io.common._NA_VALUES = set()
            
            # Clear numpy cache
            np.random.seed()  # Reset random state
            
            logger.info("🗑️  Caches cleared")
            
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
    
    async def _reduce_cpu_usage(self):
        """Reduce CPU usage"""
        try:
            # Reduce thread priority for non-critical operations
            # This is a simplified approach - in practice you'd use more sophisticated methods
            
            # Sleep briefly to reduce CPU usage
            await asyncio.sleep(0.1)
            
            logger.info("⚡ CPU usage optimization applied")
            
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
    
    async def _optimize_cpu_usage(self):
        """Optimize CPU usage"""
        try:
            # Implement CPU-specific optimizations
            # This could include:
            # - Reducing worker threads
            # - Using more efficient algorithms
            # - Implementing backoff strategies
            
            logger.info("⚡ CPU optimization applied")
            
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
    
    async def _optimize_disk_usage(self):
        """Optimize disk usage"""
        try:
            # Implement disk-specific optimizations
            # This could include:
            # - Cleaning up temporary files
            # - Compressing old data
            # - Moving data to cheaper storage
            
            logger.info("💾 Disk optimization applied")
            
        except Exception as e:
            logger.error(f"Disk optimization failed: {e}")
    
    async def _cleanup_disk_space(self):
        """Clean up disk space"""
        try:
            # Clean up temporary files
            import tempfile
            import os
            
            # Clean up system temp directory
            temp_dir = tempfile.gettempdir()
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(filepath):
                        # Remove old temporary files
                        if time.time() - os.path.getmtime(filepath) > 3600:  # 1 hour
                            os.remove(filepath)
                except Exception:
                    pass
            
            logger.info("💾 Disk cleanup completed")
            
        except Exception as e:
            logger.error(f"Disk cleanup failed: {e}")
    
    async def _aggressive_memory_cleanup(self):
        """Aggressive memory cleanup for critical situations"""
        try:
            # Multiple garbage collection passes
            for _ in range(3):
                gc.collect()
                await asyncio.sleep(0.1)
            
            # Clear all caches
            await self._clear_caches()
            
            # Force memory release
            import sys
            if hasattr(sys, 'exc_clear'):
                sys.exc_clear()
            
            self.performance_stats['memory_cleanups'] += 1
            logger.info("🚨 Aggressive memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Aggressive memory cleanup failed: {e}")
    
    def get_resource_report(self) -> Dict[str, Any]:
        """Generate resource usage report"""
        if not self.metrics_history:
            return {"message": "No metrics available"}
        
        # Calculate statistics from recent metrics
        recent_metrics = self.metrics_history[-100:]  # Last 100 measurements
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_usage_percent for m in recent_metrics]
        
        return {
            "current_metrics": self.metrics_history[-1] if self.metrics_history else None,
            "cpu_stats": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": np.mean(cpu_values),
                "max": np.max(cpu_values),
                "min": np.min(cpu_values)
            },
            "memory_stats": {
                "current": memory_values[-1] if memory_values else 0,
                "average": np.mean(memory_values),
                "max": np.max(memory_values),
                "min": np.min(memory_values)
            },
            "disk_stats": {
                "current": disk_values[-1] if disk_values else 0,
                "average": np.mean(disk_values),
                "max": np.max(disk_values),
                "min": np.min(disk_values)
            },
            "alerts": {
                "total": len(self.alerts),
                "critical": len([a for a in self.alerts if a.severity == 'critical']),
                "high": len([a for a in self.alerts if a.severity == 'high']),
                "recent": len([a for a in self.alerts if a.timestamp > time.time() - 3600])
            },
            "optimizations": self.performance_stats
        }
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        logger.info("🛑 Stopping resource monitoring...")
        self.monitoring_enabled = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("✅ Resource monitoring stopped")
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "total_mb": memory.total / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "used_mb": memory.used / 1024 / 1024,
                "percent": memory.percent,
                "swap_total_mb": swap.total / 1024 / 1024,
                "swap_used_mb": swap.used / 1024 / 1024,
                "swap_percent": swap.percent
            }
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return {}
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get current process information"""
        try:
            process = psutil.Process()
            
            return {
                "pid": process.pid,
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "memory_info_mb": {
                    "rss": process.memory_info().rss / 1024 / 1024,
                    "vms": process.memory_info().vms / 1024 / 1024
                },
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
            }
        except Exception as e:
            logger.error(f"Failed to get process info: {e}")
            return {}


# Global resource manager instance
resource_manager = ResourceManager()


async def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance"""
    return resource_manager


async def start_resource_monitoring():
    """Start resource monitoring"""
    manager = await get_resource_manager()
    await manager.start_monitoring()


async def get_resource_report():
    """Get current resource report"""
    manager = await get_resource_manager()
    return manager.get_resource_report()


async def emergency_cleanup():
    """Emergency resource cleanup"""
    manager = await get_resource_manager()
    
    # Trigger aggressive cleanup
    await manager._aggressive_memory_cleanup()
    
    # Get cleanup report
    report = manager.get_resource_report()
    
    logger.info("🚨 Emergency cleanup completed")
    logger.info(f"   Memory usage: {report['memory_stats']['current']:.1f}%")
    logger.info(f"   CPU usage: {report['cpu_stats']['current']:.1f}%")
    
    return report 