"""
Log Analysis Tool for MCP Service
Provides log analysis and error detection capabilities using kubectl
"""

import subprocess
import re
import json
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter

class LogAnalysisTool:
    """Tool for log analysis and error detection using kubectl and direct health checks"""
    
    def __init__(self):
        # Kubernetes service mappings for log analysis
        self.k8s_services = {
            "trading-engine": "trading-engine",
            "strategy-service": "strategy-service", 
            "market-data-service": "market-data-service",
            "ai-analysis-service": "ai-analysis-service",
            "unified-analytics-dashboard": "unified-analytics-dashboard",
            "unified-trading-dashboard": "unified-trading-dashboard",
            "unified-news-dashboard": "unified-news-dashboard",
            "mcp-service": "mcp-service",
            "backtest-api": "backtest-api",
            "cqrs-api": "cqrs-api"
        }
        
        # Service health endpoints
        self.health_endpoints = {
            "unified-analytics-dashboard": "http://localhost:11115/health",
            "unified-trading-dashboard": "http://localhost:11114/health", 
            "unified-news-dashboard": "http://localhost:11116/health",
            "market-data-service": "http://localhost:11084/health",
            "ai-analysis-service": "http://localhost:11085/health",
            "mcp-service": "http://localhost:11117/health"
        }
        
        # Common error patterns
        self.error_patterns = {
            "connection_error": r"(?i)(connection|connect|timeout|refused|unreachable)",
            "database_error": r"(?i)(database|sql|postgres|timescale|query failed)",
            "authentication_error": r"(?i)(auth|login|unauthorized|forbidden|invalid.*token)",
            "memory_error": r"(?i)(memory|oom|out of memory|allocation failed)",
            "network_error": r"(?i)(network|socket|dns|host.*not.*found)",
            "api_error": r"(?i)(api.*error|http.*error|status.*[45]\d\d)",
            "trading_error": r"(?i)(trading.*error|order.*failed|position.*error)",
            "ai_error": r"(?i)(ai.*error|llm.*error|model.*error|inference.*failed)"
        }
    
    async def get_recent_errors(self, hours: int = 24) -> Dict[str, Any]:
        """Get recent errors from all service logs using kubectl and health checks"""
        try:
            errors = []
            error_counts = Counter()
            
            # Check Kubernetes pod logs for errors
            for service_name, k8s_service in self.k8s_services.items():
                try:
                    # Get pod logs using kubectl
                    result = subprocess.run(
                        ["kubectl", "logs", "-n", "trading-system", "-l", f"app={k8s_service}", 
                         "--since", f"{hours}h", "--tail", "100"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        log_lines = result.stdout.split('\n')
                        service_errors = self._analyze_log_errors(log_lines, service_name)
                        errors.extend(service_errors)
                        
                        # Count error types
                        for error in service_errors:
                            error_counts[error.get("type", "unknown")] += 1
                    else:
                        # If kubectl fails, try health check
                        health_error = await self._check_service_health_error(service_name)
                        if health_error:
                            errors.append(health_error)
                            error_counts[health_error.get("type", "unknown")] += 1
                    
                except subprocess.TimeoutExpired:
                    errors.append({
                        "service": service_name,
                        "type": "log_timeout",
                        "message": f"Log analysis timed out for {service_name}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    errors.append({
                        "service": service_name,
                        "type": "log_error",
                        "message": f"Failed to analyze logs for {service_name}: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Check pod status for additional errors
            pod_errors = await self._check_pod_status_errors()
            errors.extend(pod_errors)
            for error in pod_errors:
                error_counts[error.get("type", "unknown")] += 1
            
            # Sort errors by timestamp (most recent first)
            errors.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return {
                "total_errors": len(errors),
                "error_types": dict(error_counts),
                "recent_errors": errors[:50],  # Limit to 50 most recent
                "time_range_hours": hours,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get recent errors: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _analyze_log_errors(self, log_lines: List[str], service_name: str) -> List[Dict[str, Any]]:
        """Analyze log lines for errors"""
        errors = []
        
        for line in log_lines:
            if not line.strip():
                continue
                
            # Check for error level logs
            if any(level in line.lower() for level in ["error", "err", "fatal", "critical", "exception"]):
                error_info = self._classify_error(line, service_name)
                if error_info:
                    errors.append(error_info)
        
        return errors
    
    def _classify_error(self, log_line: str, service_name: str) -> Optional[Dict[str, Any]]:
        """Classify and extract error information from a log line"""
        try:
            # Extract timestamp if present
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', log_line)
            timestamp = timestamp_match.group(1) if timestamp_match else datetime.utcnow().isoformat()
            
            # Classify error type
            error_type = "unknown"
            for pattern_name, pattern in self.error_patterns.items():
                if re.search(pattern, log_line):
                    error_type = pattern_name
                    break
            
            # Extract error message (simplified)
            message = log_line.strip()
            if len(message) > 200:
                message = message[:200] + "..."
            
            return {
                "service": service_name,
                "type": error_type,
                "message": message,
                "timestamp": timestamp,
                "severity": self._determine_severity(log_line)
            }
            
        except Exception:
            return None
    
    def _determine_severity(self, log_line: str) -> str:
        """Determine error severity from log line"""
        line_lower = log_line.lower()
        
        if any(level in line_lower for level in ["fatal", "critical"]):
            return "critical"
        elif any(level in line_lower for level in ["error", "err"]):
            return "high"
        elif any(level in line_lower for level in ["warn", "warning"]):
            return "medium"
        else:
            return "low"
    
    async def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary and statistics"""
        try:
            recent_errors = await self.get_recent_errors(24)
            
            # Analyze error patterns
            error_types = recent_errors.get("error_types", {})
            total_errors = recent_errors.get("total_errors", 0)
            
            # Get most problematic services
            service_errors = Counter()
            for error in recent_errors.get("recent_errors", []):
                service_errors[error.get("service", "unknown")] += 1
            
            # Get severity breakdown
            severity_counts = Counter()
            for error in recent_errors.get("recent_errors", []):
                severity_counts[error.get("severity", "unknown")] += 1
            
            return {
                "total_errors_24h": total_errors,
                "error_types": error_types,
                "most_problematic_services": dict(service_errors.most_common(5)),
                "severity_breakdown": dict(severity_counts),
                "error_rate": "high" if total_errors > 50 else "medium" if total_errors > 10 else "low",
                "critical_errors": severity_counts.get("critical", 0),
                "high_errors": severity_counts.get("high", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get error summary: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def search_logs(self, query: str, service: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Search logs for specific patterns using kubectl"""
        try:
            results = []
            
            services_to_search = [service] if service else list(self.k8s_services.keys())
            
            for service_name in services_to_search:
                if service_name not in self.k8s_services:
                    continue
                    
                k8s_service = self.k8s_services[service_name]
                try:
                    # Use kubectl to search logs
                    cmd = ["kubectl", "logs", "-n", "trading-system", "-l", f"app={k8s_service}", 
                           "--since", f"{hours}h", "--tail", "1000"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if line.strip() and query.lower() in line.lower():
                                results.append({
                                    "service": service_name,
                                    "line": line.strip(),
                                    "timestamp": self._extract_timestamp(line)
                                })
                    else:
                        # If kubectl fails, try health check as fallback
                        health_error = await self._check_service_health_error(service_name)
                        if health_error and query.lower() in health_error["message"].lower():
                            results.append({
                                "service": service_name,
                                "line": health_error["message"],
                                "timestamp": health_error["timestamp"]
                            })
                    
                except subprocess.TimeoutExpired:
                    results.append({
                        "service": service_name,
                        "line": f"Search timed out for {service_name}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    results.append({
                        "service": service_name,
                        "line": f"Search error for {service_name}: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            return {
                "query": query,
                "service_filter": service,
                "time_range_hours": hours,
                "total_matches": len(results),
                "results": results[:100],  # Limit to 100 results
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to search logs: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _extract_timestamp(self, log_line: str) -> str:
        """Extract timestamp from log line"""
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', log_line)
        return timestamp_match.group(1) if timestamp_match else datetime.utcnow().isoformat()
    
    async def _check_service_health_error(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Check service health and return error if unhealthy"""
        if service_name in self.health_endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.health_endpoints[service_name], 
                        timeout=5
                    ) as response:
                        if response.status != 200:
                            return {
                                "service": service_name,
                                "type": "health_error",
                                "message": f"Service health check failed with status {response.status}",
                                "timestamp": datetime.utcnow().isoformat(),
                                "severity": "high"
                            }
            except Exception as e:
                return {
                    "service": service_name,
                    "type": "connection_error",
                    "message": f"Service health check failed: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "high"
                }
        return None
    
    async def _check_pod_status_errors(self) -> List[Dict[str, Any]]:
        """Check Kubernetes pod status for errors"""
        errors = []
        try:
            # Get pod status
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "trading-system", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                pod_data = json.loads(result.stdout)
                for pod in pod_data.get("items", []):
                    pod_name = pod.get("metadata", {}).get("name", "unknown")
                    status = pod.get("status", {})
                    phase = status.get("phase", "Unknown")
                    conditions = status.get("conditions", [])
                    
                    # Check for error states
                    if phase in ["Failed", "CrashLoopBackOff", "Error"]:
                        errors.append({
                            "service": pod_name,
                            "type": "pod_error",
                            "message": f"Pod in {phase} state",
                            "timestamp": datetime.utcnow().isoformat(),
                            "severity": "critical"
                        })
                    
                    # Check container status
                    for container in status.get("containerStatuses", []):
                        container_name = container.get("name", "unknown")
                        container_state = container.get("state", {})
                        
                        if "waiting" in container_state:
                            reason = container_state["waiting"].get("reason", "Unknown")
                            if reason in ["CrashLoopBackOff", "ImagePullBackOff", "ErrImageNeverPull"]:
                                errors.append({
                                    "service": f"{pod_name}:{container_name}",
                                    "type": "container_error",
                                    "message": f"Container {reason}: {container_state['waiting'].get('message', '')}",
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "severity": "critical" if reason in ["CrashLoopBackOff", "ImagePullBackOff"] else "high"
                                })
                        
                        if "terminated" in container_state:
                            exit_code = container_state["terminated"].get("exitCode", 0)
                            if exit_code != 0:
                                errors.append({
                                    "service": f"{pod_name}:{container_name}",
                                    "type": "container_terminated",
                                    "message": f"Container terminated with exit code {exit_code}",
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "severity": "high"
                                })
            
        except Exception as e:
            errors.append({
                "service": "kubectl",
                "type": "kubectl_error",
                "message": f"Failed to check pod status: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "medium"
            })
        
        return errors
    
    async def get_log_health_score(self) -> Dict[str, Any]:
        """Get log-based health score"""
        try:
            error_summary = await self.get_error_summary()
            
            total_errors = error_summary.get("total_errors_24h", 0)
            critical_errors = error_summary.get("critical_errors", 0)
            high_errors = error_summary.get("high_errors", 0)
            
            # Calculate health score based on errors
            if critical_errors > 0:
                health_score = 0
                health_status = "🔴 Critical"
            elif high_errors > 10:
                health_score = 25
                health_status = "🟠 Poor"
            elif total_errors > 50:
                health_score = 50
                health_status = "🟡 Fair"
            elif total_errors > 10:
                health_score = 75
                health_status = "🟢 Good"
            else:
                health_score = 100
                health_status = "🟢 Excellent"
            
            return {
                "log_health_score": health_score,
                "health_status": health_status,
                "total_errors_24h": total_errors,
                "critical_errors": critical_errors,
                "high_errors": high_errors,
                "error_rate": error_summary.get("error_rate", "unknown"),
                "most_problematic_services": error_summary.get("most_problematic_services", {}),
                "recommendations": self._generate_log_recommendations(error_summary),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to calculate log health score: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _generate_log_recommendations(self, error_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on log analysis"""
        recommendations = []
        
        total_errors = error_summary.get("total_errors_24h", 0)
        critical_errors = error_summary.get("critical_errors", 0)
        most_problematic = error_summary.get("most_problematic_services", {})
        
        if critical_errors > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": f"{critical_errors} critical errors in the last 24 hours",
                "action": "Immediately investigate and fix critical errors",
                "impact": "System stability at risk"
            })
        
        if total_errors > 50:
            recommendations.append({
                "priority": "HIGH",
                "issue": f"High error volume: {total_errors} errors in 24h",
                "action": "Review error patterns and address root causes",
                "impact": "System reliability concerns"
            })
        
        if most_problematic:
            top_problematic = max(most_problematic.items(), key=lambda x: x[1])
            recommendations.append({
                "priority": "MEDIUM",
                "issue": f"Service {top_problematic[0]} has {top_problematic[1]} errors",
                "action": f"Focus on fixing issues in {top_problematic[0]}",
                "impact": "Service-specific reliability issues"
            })
        
        return recommendations
