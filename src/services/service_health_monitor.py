#!/usr/bin/env python3
"""
Service Health Monitor
Monitors the health of all trading system services
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class ServiceHealthMonitor:
    """Monitor health of all trading system services"""
    
    def __init__(self):
        self.services = {
            'elliott-wave-service': 'http://localhost:11001/health',
            'options-data-service': 'http://localhost:11002/health',
            'market-data-service': 'http://localhost:11003/health',
            'llm-service': 'http://localhost:12001/health',
            'backtest-service': 'http://localhost:10001/health'
        }
        self.health_status = {}
        self.last_check = {}
        
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services"""
        logger.info("🔍 Checking health of all services...")
        
        tasks = []
        for service_name, health_url in self.services.items():
            task = asyncio.create_task(self._check_service_health(service_name, health_url))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            service_name = list(self.services.keys())[i]
            if isinstance(result, Exception):
                self.health_status[service_name] = {
                    'status': 'unhealthy',
                    'error': str(result),
                    'last_check': datetime.now()
                }
            else:
                self.health_status[service_name] = result
        
        return self.health_status
    
    async def _check_service_health(self, service_name: str, health_url: str) -> Dict[str, Any]:
        """Check health of a single service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                response.raise_for_status()
                
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'last_check': datetime.now()
                }
                
        except Exception as e:
            logger.warning(f"⚠️ Service {service_name} health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now()
            }
    
    def get_service_status(self, service_name: str) -> str:
        """Get status of a specific service"""
        if service_name not in self.health_status:
            return 'unknown'
        
        return self.health_status[service_name].get('status', 'unknown')
    
    def get_unhealthy_services(self) -> list:
        """Get list of unhealthy services"""
        return [service for service, status in self.health_status.items() 
                if status.get('status') == 'unhealthy']
    
    async def wait_for_service_recovery(self, service_name: str, max_wait: int = 300) -> bool:
        """Wait for a service to recover"""
        logger.info(f"⏳ Waiting for {service_name} to recover...")
        
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < max_wait:
            await self._check_service_health(service_name, self.services[service_name])
            
            if self.get_service_status(service_name) == 'healthy':
                logger.info(f"✅ {service_name} recovered!")
                return True
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        logger.warning(f"⏰ Timeout waiting for {service_name} to recover")
        return False
