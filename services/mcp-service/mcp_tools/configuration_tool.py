"""
Configuration Tool for MCP Service
Provides configuration management and inspection
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime

class ConfigurationTool:
    """Tool for configuration management and inspection"""
    
    def __init__(self):
        self.port_config = {
            "11115": {"service": "Unified Analytics Dashboard", "type": "dashboard"},
            "11114": {"service": "Unified Trading Dashboard", "type": "dashboard"},
            "11116": {"service": "Unified News Dashboard", "type": "dashboard"},
            "11084": {"service": "Market Data Service", "type": "trading"},
            "11085": {"service": "AI Analysis Service", "type": "ai"},
            "11101": {"service": "Backtest API", "type": "trading"},
            "11103": {"service": "Strategy Service", "type": "trading"},
            "11044": {"service": "Grafana", "type": "monitoring"},
            "11190": {"service": "Prometheus", "type": "monitoring"},
            "11140": {"service": "TimescaleDB", "type": "database"},
            "11142": {"service": "Redis", "type": "cache"},
            "11144": {"service": "RabbitMQ", "type": "message_queue"}
        }
    
    async def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "namespace": os.getenv("NAMESPACE", "trading-system"),
            "port_range": "11000-11999",
            "architecture": "microservices",
            "orchestration": "kubernetes",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_port_config(self) -> Dict[str, Any]:
        """Get port configuration"""
        return {
            "port_mappings": self.port_config,
            "port_range": "11000-11999",
            "total_ports": len(self.port_config),
            "port_types": {
                "dashboard": len([p for p in self.port_config.values() if p["type"] == "dashboard"]),
                "trading": len([p for p in self.port_config.values() if p["type"] == "trading"]),
                "ai": len([p for p in self.port_config.values() if p["type"] == "ai"]),
                "monitoring": len([p for p in self.port_config.values() if p["type"] == "monitoring"]),
                "database": len([p for p in self.port_config.values() if p["type"] == "database"]),
                "cache": len([p for p in self.port_config.values() if p["type"] == "cache"]),
                "message_queue": len([p for p in self.port_config.values() if p["type"] == "message_queue"])
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_environment_config(self) -> Dict[str, Any]:
        """Get environment variables"""
        env_vars = {}
        for key, value in os.environ.items():
            if key.startswith(('TRADING_', 'KUBERNETES_', 'DATABASE_', 'REDIS_', 'RABBITMQ_')):
                env_vars[key] = value
        
        return {
            "environment_variables": env_vars,
            "total_vars": len(env_vars),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service"""
        # This would query the service's configuration
        return {
            "service": service_name,
            "config": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "namespace": os.getenv("NAMESPACE", "trading-system")
            },
            "timestamp": datetime.utcnow().isoformat()
        }
