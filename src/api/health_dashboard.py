"""
System Health Dashboard - Real-time system status and metrics
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import asyncio
import psutil
import time
from datetime import datetime

from ..utils.cache_manager import get_cache_manager
from ..utils.circuit_breaker import get_circuit_breaker_manager
from ..utils.enhanced_logging import get_trading_logger

router = APIRouter(prefix="/health", tags=["Health Dashboard"])


class SystemHealthMonitor:
    """Monitor system health and performance"""
    
    def __init__(self):
        self.logger = get_trading_logger()
        self.start_time = time.time()
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'uptime': time.time() - self.start_time,
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'usage_percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        try:
            # Get cache manager status
            cache_manager = await get_cache_manager()
            cache_stats = await cache_manager.get_stats()
            
            # Get circuit breaker status
            cb_manager = get_circuit_breaker_manager()
            cb_stats = cb_manager.get_all_stats()
            
            # Check if services are healthy
            services_healthy = True
            service_details = {}
            
            # Cache service status
            if cache_stats.get('l1_hit_rate', 0) > 0:
                service_details['cache'] = {
                    'status': 'healthy',
                    'hit_rate': cache_stats['l1_hit_rate'],
                    'cache_size': cache_stats['l1_cache_size']
                }
            else:
                service_details['cache'] = {'status': 'warning', 'message': 'No cache hits'}
                services_healthy = False
            
            # Circuit breaker status
            open_circuits = sum(1 for stats in cb_stats.values() if stats['state'] == 'OPEN')
            if open_circuits > 0:
                service_details['circuit_breakers'] = {
                    'status': 'warning',
                    'open_circuits': open_circuits,
                    'total_circuits': len(cb_stats)
                }
                services_healthy = False
            else:
                service_details['circuit_breakers'] = {
                    'status': 'healthy',
                    'total_circuits': len(cb_stats)
                }
            
            return {
                'overall_status': 'healthy' if services_healthy else 'warning',
                'services': service_details,
                'cache_stats': cache_stats,
                'circuit_breaker_stats': cb_stats
            }
        except Exception as e:
            self.logger.error(f"Error getting service status: {e}")
            return {'error': str(e)}
    
    async def get_trading_metrics(self) -> Dict[str, Any]:
        """Get trading-specific metrics"""
        try:
            # This would be populated with actual trading metrics
            # For now, return mock data
            return {
                'timestamp': datetime.now().isoformat(),
                'active_strategies': 3,
                'total_positions': 5,
                'daily_pnl': 1250.50,
                'total_pnl': 8750.25,
                'win_rate': 0.68,
                'total_trades': 45,
                'risk_metrics': {
                    'var_95': 0.025,
                    'max_drawdown': 0.08,
                    'sharpe_ratio': 1.35
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting trading metrics: {e}")
            return {'error': str(e)}


# Global health monitor
health_monitor = SystemHealthMonitor()


@router.get("/")
async def get_health_overview() -> Dict[str, Any]:
    """Get overall system health overview"""
    try:
        system_metrics = await health_monitor.get_system_metrics()
        service_status = await health_monitor.get_service_status()
        trading_metrics = await health_monitor.get_trading_metrics()
        
        # Determine overall health
        overall_health = 'healthy'
        if service_status.get('overall_status') != 'healthy':
            overall_health = 'warning'
        if system_metrics.get('error') or service_status.get('error') or trading_metrics.get('error'):
            overall_health = 'error'
        
        return {
            'status': overall_health,
            'timestamp': datetime.now().isoformat(),
            'system': system_metrics,
            'services': service_status,
            'trading': trading_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/system")
async def get_system_health() -> Dict[str, Any]:
    """Get detailed system health metrics"""
    try:
        return await health_monitor.get_system_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System health check failed: {str(e)}")


@router.get("/services")
async def get_services_health() -> Dict[str, Any]:
    """Get services health status"""
    try:
        return await health_monitor.get_service_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Services health check failed: {str(e)}")


@router.get("/trading")
async def get_trading_health() -> Dict[str, Any]:
    """Get trading system health"""
    try:
        return await health_monitor.get_trading_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trading health check failed: {str(e)}")


@router.get("/cache")
async def get_cache_health() -> Dict[str, Any]:
    """Get cache system health"""
    try:
        cache_manager = await get_cache_manager()
        stats = await cache_manager.get_stats()
        
        # Determine cache health
        health = 'healthy'
        if stats['l1_hit_rate'] < 50:
            health = 'warning'
        if stats['l1_hit_rate'] < 20:
            health = 'error'
        
        return {
            'status': health,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache health check failed: {str(e)}")


@router.get("/circuit-breakers")
async def get_circuit_breakers_health() -> Dict[str, Any]:
    """Get circuit breakers health status"""
    try:
        cb_manager = get_circuit_breaker_manager()
        stats = cb_manager.get_all_stats()
        
        # Count circuit states
        open_circuits = sum(1 for s in stats.values() if s['state'] == 'OPEN')
        half_open_circuits = sum(1 for s in stats.values() if s['state'] == 'HALF_OPEN')
        closed_circuits = sum(1 for s in stats.values() if s['state'] == 'CLOSED')
        
        # Determine health
        health = 'healthy'
        if open_circuits > 0:
            health = 'warning'
        if open_circuits > 3:
            health = 'error'
        
        return {
            'status': health,
            'circuit_states': {
                'open': open_circuits,
                'half_open': half_open_circuits,
                'closed': closed_circuits,
                'total': len(stats)
            },
            'details': stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Circuit breakers health check failed: {str(e)}")


@router.get("/alerts")
async def get_system_alerts() -> List[Dict[str, Any]]:
    """Get current system alerts"""
    try:
        alerts = []
        
        # Check system metrics
        system_metrics = await health_monitor.get_system_metrics()
        if not system_metrics.get('error'):
            cpu_usage = system_metrics['cpu']['usage_percent']
            memory_usage = system_metrics['memory']['usage_percent']
            disk_usage = system_metrics['disk']['usage_percent']
            
            if cpu_usage > 90:
                alerts.append({
                    'level': 'critical',
                    'component': 'cpu',
                    'message': f'CPU usage is {cpu_usage:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            elif cpu_usage > 80:
                alerts.append({
                    'level': 'warning',
                    'component': 'cpu',
                    'message': f'CPU usage is {cpu_usage:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            if memory_usage > 90:
                alerts.append({
                    'level': 'critical',
                    'component': 'memory',
                    'message': f'Memory usage is {memory_usage:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            if disk_usage > 90:
                alerts.append({
                    'level': 'critical',
                    'component': 'disk',
                    'message': f'Disk usage is {disk_usage:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check service status
        service_status = await health_monitor.get_service_status()
        if service_status.get('overall_status') != 'healthy':
            alerts.append({
                'level': 'warning',
                'component': 'services',
                'message': 'Some services are not healthy',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alerts check failed: {str(e)}") 