"""
Kubernetes Client for MCP Service
Handles Kubernetes operations
"""

import subprocess
import json
from typing import Dict, Any, List
from datetime import datetime

class KubernetesClient:
    """Client for Kubernetes operations"""
    
    def __init__(self):
        self.namespace = "trading-system"
    
    async def get_pods(self) -> Dict[str, Any]:
        """Get Kubernetes pods status"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "error": f"kubectl command failed: {result.stderr}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            pods_data = json.loads(result.stdout)
            pods = []
            
            for pod in pods_data.get("items", []):
                pod_info = {
                    "name": pod["metadata"]["name"],
                    "namespace": pod["metadata"]["namespace"],
                    "status": pod["status"]["phase"],
                    "ready": self._get_ready_status(pod),
                    "restarts": self._get_restart_count(pod),
                    "age": self._get_pod_age(pod)
                }
                pods.append(pod_info)
            
            return {
                "pods": pods,
                "total_pods": len(pods),
                "namespace": self.namespace,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get pods: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_services(self) -> Dict[str, Any]:
        """Get Kubernetes services"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "services", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "error": f"kubectl command failed: {result.stderr}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            services_data = json.loads(result.stdout)
            services = []
            
            for service in services_data.get("items", []):
                service_info = {
                    "name": service["metadata"]["name"],
                    "namespace": service["metadata"]["namespace"],
                    "type": service["spec"]["type"],
                    "cluster_ip": service["spec"].get("clusterIP", "None"),
                    "ports": service["spec"].get("ports", [])
                }
                services.append(service_info)
            
            return {
                "services": services,
                "total_services": len(services),
                "namespace": self.namespace,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get services: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_ready_status(self, pod: Dict[str, Any]) -> str:
        """Get pod ready status"""
        conditions = pod.get("status", {}).get("conditions", [])
        for condition in conditions:
            if condition["type"] == "Ready":
                return condition["status"]
        return "Unknown"
    
    def _get_restart_count(self, pod: Dict[str, Any]) -> int:
        """Get pod restart count"""
        containers = pod.get("status", {}).get("containerStatuses", [])
        total_restarts = 0
        for container in containers:
            total_restarts += container.get("restartCount", 0)
        return total_restarts
    
    def _get_pod_age(self, pod: Dict[str, Any]) -> str:
        """Get pod age"""
        creation_time = pod.get("metadata", {}).get("creationTimestamp")
        if creation_time:
            # This is a simplified age calculation
            # In a real implementation, you'd parse the timestamp and calculate the difference
            return "Unknown"
        return "Unknown"
