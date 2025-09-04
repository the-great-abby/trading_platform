"""
System Control Tool for MCP Service
Provides basic system control operations
"""

import subprocess
import json
from typing import Dict, Any, List
from datetime import datetime
from clients.kubernetes_client import KubernetesClient

class SystemControlTool:
    """Tool for basic system control operations"""
    
    def __init__(self):
        self.kubernetes_client = KubernetesClient()
        self.port_mappings = {
            "11115": "Unified Analytics Dashboard",
            "11114": "Unified Trading Dashboard", 
            "11116": "Unified News Dashboard",
            "11084": "Market Data Service",
            "11085": "AI Analysis Service",
            "11101": "Backtest API",
            "11103": "Strategy Service",
            "11044": "Grafana",
            "11190": "Prometheus",
            "11140": "TimescaleDB",
            "11142": "Redis",
            "11144": "RabbitMQ"
        }
    
    async def get_port_mappings(self) -> Dict[str, Any]:
        """Get current port mappings"""
        return {
            "port_mappings": self.port_mappings,
            "total_ports": len(self.port_mappings),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def forward_ports(self, ports: List[int]) -> Dict[str, Any]:
        """Forward specific ports (placeholder - would need kubectl integration)"""
        # This is a placeholder - in a real implementation, this would use kubectl
        return {
            "message": f"Port forwarding for ports {ports} would be initiated",
            "ports": ports,
            "status": "placeholder",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_kubernetes_pods(self) -> Dict[str, Any]:
        """Get Kubernetes pod status"""
        try:
            return await self.kubernetes_client.get_pods()
        except Exception as e:
            return {
                "error": f"Failed to get Kubernetes pods: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_active_port_forwards(self) -> Dict[str, Any]:
        """Get currently active port forwards"""
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            port_forwards = []
            for line in result.stdout.split('\n'):
                if 'kubectl port-forward' in line:
                    port_forwards.append(line.strip())
            
            return {
                "active_port_forwards": port_forwards,
                "count": len(port_forwards),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "error": f"Failed to get active port forwards: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
