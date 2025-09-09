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
    
    async def detect_port_conflicts(self) -> Dict[str, Any]:
        """Detect port conflicts and suggest solutions"""
        try:
            # Get active port forwards
            active_forwards = await self.get_active_port_forwards()
            
            # Parse port forwards to extract ports
            used_ports = set()
            port_details = {}
            
            for forward in active_forwards.get("active_port_forwards", []):
                # Extract port from kubectl port-forward command
                # Format: kubectl port-forward service/name local_port:remote_port
                parts = forward.split()
                for i, part in enumerate(parts):
                    if 'port-forward' in part and i + 1 < len(parts):
                        port_spec = parts[i + 1]
                        if ':' in port_spec:
                            local_port = port_spec.split(':')[0]
                            try:
                                port_num = int(local_port)
                                used_ports.add(port_num)
                                port_details[port_num] = {
                                    "command": forward,
                                    "service": parts[i + 1].split('/')[-1] if '/' in parts[i + 1] else "unknown"
                                }
                            except ValueError:
                                continue
            
            # Check for conflicts with our known port mappings
            conflicts = []
            available_ports = []
            
            for port_str, service_name in self.port_mappings.items():
                port_num = int(port_str)
                if port_num in used_ports:
                    conflicts.append({
                        "port": port_num,
                        "service": service_name,
                        "conflict_type": "already_in_use",
                        "current_user": port_details.get(port_num, {}).get("service", "unknown"),
                        "suggestion": f"Port {port_num} is already in use by {port_details.get(port_num, {}).get('service', 'unknown')}. Consider using a different port or stopping the existing forward."
                    })
                else:
                    available_ports.append({
                        "port": port_num,
                        "service": service_name,
                        "status": "available"
                    })
            
            # Check for duplicate port forwards
            port_counts = {}
            for port in used_ports:
                port_counts[port] = port_counts.get(port, 0) + 1
            
            duplicates = []
            for port, count in port_counts.items():
                if count > 1:
                    duplicates.append({
                        "port": port,
                        "count": count,
                        "suggestion": f"Port {port} has {count} active forwards. This may cause conflicts."
                    })
            
            return {
                "total_ports_checked": len(self.port_mappings),
                "ports_in_use": len(used_ports),
                "available_ports": len(available_ports),
                "conflicts_found": len(conflicts),
                "duplicates_found": len(duplicates),
                "conflicts": conflicts,
                "duplicates": duplicates,
                "available_ports": available_ports,
                "used_ports": list(used_ports),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to detect port conflicts: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_port_utilization_summary(self) -> Dict[str, Any]:
        """Get port utilization summary"""
        try:
            # Get port conflicts
            conflicts = await self.detect_port_conflicts()
            
            # Get active port forwards
            active_forwards = await self.get_active_port_forwards()
            
            # Calculate utilization
            total_configured_ports = len(self.port_mappings)
            ports_in_use = len(conflicts.get("used_ports", []))
            utilization_percentage = round((ports_in_use / total_configured_ports) * 100, 1) if total_configured_ports > 0 else 0
            
            return {
                "total_configured_ports": total_configured_ports,
                "ports_in_use": ports_in_use,
                "ports_available": total_configured_ports - ports_in_use,
                "utilization_percentage": utilization_percentage,
                "active_port_forwards": active_forwards.get("count", 0),
                "conflicts": conflicts.get("conflicts_found", 0),
                "duplicates": conflicts.get("duplicates_found", 0),
                "status": "healthy" if conflicts.get("conflicts_found", 0) == 0 else "conflicts_detected",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get port utilization summary: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def suggest_port_alternatives(self, port: int) -> Dict[str, Any]:
        """Suggest alternative ports for a given port"""
        try:
            # Get current conflicts
            conflicts = await self.detect_port_conflicts()
            used_ports = set(conflicts.get("used_ports", []))
            
            # Find available ports in the same range
            base_port = (port // 100) * 100  # Get the hundred range
            suggestions = []
            
            # Look for available ports in the same range
            for i in range(base_port, base_port + 100):
                if i not in used_ports and i != port:
                    suggestions.append(i)
                    if len(suggestions) >= 5:  # Limit to 5 suggestions
                        break
            
            # If no ports in same range, suggest from other ranges
            if not suggestions:
                for i in range(11000, 12000):
                    if i not in used_ports and i != port:
                        suggestions.append(i)
                        if len(suggestions) >= 5:
                            break
            
            return {
                "requested_port": port,
                "is_available": port not in used_ports,
                "alternative_ports": suggestions,
                "total_alternatives": len(suggestions),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to suggest port alternatives: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }