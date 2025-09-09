"""
Log Analysis Tool for MCP Service
Provides log analysis and error detection capabilities
"""

import subprocess
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter

class LogAnalysisTool:
    """Tool for log analysis and error detection"""
    
    def __init__(self):
        self.log_paths = {
            "trading_engine": "/app/logs/trading_engine.log",
            "strategy_service": "/app/logs/strategy_service.log",
            "market_data_service": "/app/logs/market_data_service.log",
            "ai_analysis_service": "/app/logs/ai_analysis_service.log",
            "unified_analytics": "/app/logs/unified_analytics.log",
            "mcp_service": "/app/logs/mcp_service.log"
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
        """Get recent errors from all service logs"""
        try:
            errors = []
            error_counts = Counter()
            
            for service_name, log_path in self.log_paths.items():
                try:
                    # Use journalctl or tail to get recent logs
                    result = subprocess.run(
                        ["journalctl", "-u", service_name, "--since", f"{hours} hours ago", "--no-pager"],
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
        """Search logs for specific patterns"""
        try:
            results = []
            
            services_to_search = [service] if service else list(self.log_paths.keys())
            
            for service_name in services_to_search:
                try:
                    # Use journalctl to search logs
                    cmd = ["journalctl", "-u", service_name, "--since", f"{hours} hours ago", "--no-pager", "-g", query]
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
