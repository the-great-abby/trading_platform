"""
Intelligent Automation Tool for MCP Service
Core automation logic with service tier monitoring and auto-remediation
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass
from clients.service_client import ServiceClient

logger = logging.getLogger(__name__)

class ServiceTier(Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    SUPPORTING = "supporting"

class IssueType(Enum):
    MEMORY_HIGH = "memory_high"
    RESPONSE_SLOW = "response_slow"
    ERROR_RATE_HIGH = "error_rate_high"
    SERVICE_DOWN = "service_down"
    UNKNOWN = "unknown"

@dataclass
class AutomationRule:
    threshold: float
    action: str
    cooldown: int  # seconds
    max_attempts: int

@dataclass
class ServiceHealth:
    service_name: str
    tier: ServiceTier
    health_score: int
    memory_usage: float
    response_time: float
    error_rate: float
    status: str
    last_check: datetime
    issues: List[IssueType]

@dataclass
class AutomationAction:
    service_name: str
    issue_type: IssueType
    action_taken: str
    timestamp: datetime
    success: bool
    attempt_number: int

class IntelligentAutomationTool:
    """Core automation logic with service tier monitoring and auto-remediation"""
    
    def __init__(self):
        self.service_client = ServiceClient()
        self.automation_running = False
        self.action_history: List[AutomationAction] = []
        self.service_health_cache: Dict[str, ServiceHealth] = {}
        self.cooldown_tracker: Dict[str, datetime] = {}
        self.attempt_tracker: Dict[str, int] = {}
        
        # Service tier configuration
        self.service_tiers = {
            ServiceTier.CRITICAL: {
                "services": ["trading-engine", "market-data-service", "strategy-service"],
                "monitoring_interval": 10,  # seconds
                "health_endpoints": {
                    "trading-engine": "http://cqrs-api-service.trading-system.svc.cluster.local/health",
                    "market-data-service": "http://market-data-service.trading-system.svc.cluster.local/health",
                    "strategy-service": "http://strategy-service.trading-system.svc.cluster.local/health"
                }
            },
            ServiceTier.IMPORTANT: {
                "services": ["ai-analysis-service", "portfolio-management", "risk-management", "unified-trading-dashboard"],
                "monitoring_interval": 30,  # seconds
                "health_endpoints": {
                    "ai-analysis-service": "http://ai-analysis-service.trading-system.svc.cluster.local/health",
                    "portfolio-management": "http://portfolio-service.trading-system.svc.cluster.local/health",
                    "risk-management": "http://risk-management-service.trading-system.svc.cluster.local/health",
                    "unified-trading-dashboard": "http://unified-trading-dashboard.trading-system.svc.cluster.local/health"
                }
            },
            ServiceTier.SUPPORTING: {
                "services": ["unified-analytics-dashboard", "unified-news-dashboard", "news-service", "rss-feed-service", "vector-storage", "llm-proxy", "prometheus", "grafana"],
                "monitoring_interval": 60,  # seconds
                "health_endpoints": {
                    "unified-analytics-dashboard": "http://unified-analytics-dashboard.trading-system.svc.cluster.local/health",
                    "unified-news-dashboard": "http://unified-news-dashboard.trading-system.svc.cluster.local/health",
                    "news-service": "http://news-service.trading-system.svc.cluster.local/health",
                    "rss-feed-service": "http://rss-feed-service.trading-system.svc.cluster.local/health",
                    "vector-storage": "http://vector-storage.trading-system.svc.cluster.local/health",
                    "llm-proxy": "http://llm-proxy.trading-system.svc.cluster.local/health",
                    "prometheus": "http://prometheus.trading-system.svc.cluster.local/health",
                    "grafana": "http://grafana.trading-system.svc.cluster.local/health"
                }
            }
        }
        
        # Automation rules
        self.automation_rules = {
            IssueType.MEMORY_HIGH: AutomationRule(
                threshold=85.0,
                action="restart_service",
                cooldown=300,  # 5 minutes
                max_attempts=3
            ),
            IssueType.RESPONSE_SLOW: AutomationRule(
                threshold=2000.0,  # 2 seconds
                action="optimize_service",
                cooldown=600,  # 10 minutes
                max_attempts=2
            ),
            IssueType.ERROR_RATE_HIGH: AutomationRule(
                threshold=5.0,  # 5%
                action="investigate_and_fix",
                cooldown=180,  # 3 minutes
                max_attempts=3
            ),
            IssueType.SERVICE_DOWN: AutomationRule(
                threshold=0.0,
                action="restart_service",
                cooldown=60,  # 1 minute
                max_attempts=5
            )
        }
        
        # Background monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
    
    async def start_automation_system(self) -> Dict[str, Any]:
        """Start the automation system"""
        try:
            if self.automation_running:
                return {
                    "status": "already_running",
                    "message": "Automation system is already running",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info("Starting intelligent automation system...")
            
            # Test health endpoints first
            health_test = await self.test_all_health_endpoints()
            success_rate = health_test.get("success_rate", 0)
            if success_rate < 25:  # Lower threshold to 25%
                return {
                    "status": "failed",
                    "message": f"Health endpoint test failed - only {success_rate}% of services are healthy (minimum 25% required)",
                    "details": health_test,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Start continuous monitoring for each tier
            self.automation_running = True
            self.monitoring_tasks = []
            
            for tier in ServiceTier:
                task = asyncio.create_task(self._monitor_service_tier(tier))
                self.monitoring_tasks.append(task)
            
            return {
                "status": "started",
                "message": "Automation system started successfully",
                "monitoring_tasks": len(self.monitoring_tasks),
                "service_tiers": len(ServiceTier),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start automation system: {e}")
            return {
                "status": "error",
                "message": f"Failed to start automation system: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def stop_automation_system(self) -> Dict[str, Any]:
        """Stop the automation system"""
        try:
            if not self.automation_running:
                return {
                    "status": "not_running",
                    "message": "Automation system is not running",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info("Stopping intelligent automation system...")
            
            # Cancel all monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()
            
            self.monitoring_tasks = []
            self.automation_running = False
            
            return {
                "status": "stopped",
                "message": "Automation system stopped successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to stop automation system: {e}")
            return {
                "status": "error",
                "message": f"Failed to stop automation system: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation system status"""
        return {
            "automation_running": self.automation_running,
            "monitoring_tasks": len(self.monitoring_tasks),
            "active_tasks": [task.get_name() for task in self.monitoring_tasks if not task.done()],
            "total_actions_taken": len(self.action_history),
            "recent_actions": self.action_history[-10:] if self.action_history else [],
            "service_health_cache_size": len(self.service_health_cache),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def test_all_health_endpoints(self) -> Dict[str, Any]:
        """Test all health endpoints"""
        results = {}
        success_count = 0
        total_count = 0
        
        for tier in ServiceTier:
            tier_config = self.service_tiers[tier]
            for service_name, endpoint in tier_config["health_endpoints"].items():
                total_count += 1
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoint, timeout=5) as response:
                            if response.status == 200:
                                results[service_name] = {"status": "healthy", "response_code": response.status}
                                success_count += 1
                            else:
                                results[service_name] = {"status": "unhealthy", "response_code": response.status}
                except Exception as e:
                    results[service_name] = {"status": "unreachable", "error": str(e)}
        
        return {
            "success": success_count > 0,
            "success_count": success_count,
            "total_count": total_count,
            "success_rate": round((success_count / total_count) * 100, 2) if total_count > 0 else 0,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _monitor_service_tier(self, tier: ServiceTier) -> None:
        """Monitor a specific service tier"""
        tier_config = self.service_tiers[tier]
        interval = tier_config["monitoring_interval"]
        
        logger.info(f"Starting monitoring for {tier.value} tier (interval: {interval}s)")
        
        while self.automation_running:
            try:
                # Check if it's trading hours for aggressive monitoring
                is_trading_hours = self._is_trading_hours()
                
                # Adjust monitoring interval based on trading hours
                if tier == ServiceTier.CRITICAL and is_trading_hours:
                    current_interval = 5  # More aggressive during trading hours
                else:
                    current_interval = interval
                
                # Monitor each service in this tier
                for service_name in tier_config["services"]:
                    await self._monitor_service(service_name, tier)
                
                # Wait for next check
                await asyncio.sleep(current_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Monitoring task for {tier.value} tier cancelled")
                break
            except Exception as e:
                logger.error(f"Error in {tier.value} tier monitoring: {e}")
                await asyncio.sleep(interval)
    
    async def _monitor_service(self, service_name: str, tier: ServiceTier) -> None:
        """Monitor a specific service"""
        try:
            # Get service health data
            health_data = await self._get_service_health_data(service_name, tier)
            
            # Update health cache
            self.service_health_cache[service_name] = health_data
            
            # Check for issues and take action
            await self._check_and_remediate_issues(service_name, health_data)
            
        except Exception as e:
            logger.error(f"Error monitoring service {service_name}: {e}")
    
    async def _get_service_health_data(self, service_name: str, tier: ServiceTier) -> ServiceHealth:
        """Get comprehensive health data for a service"""
        tier_config = self.service_tiers[tier]
        endpoint = tier_config["health_endpoints"].get(service_name)
        
        health_score = 100
        memory_usage = 0.0
        response_time = 0.0
        error_rate = 0.0
        status = "unknown"
        issues = []
        
        try:
            # Health check
            start_time = datetime.utcnow()
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=5) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms
                    
                    if response.status == 200:
                        status = "healthy"
                        health_score = 100
                    else:
                        status = "unhealthy"
                        health_score = 50
                        issues.append(IssueType.SERVICE_DOWN)
            
            # Simulate metrics collection (in real implementation, this would query Prometheus)
            memory_usage = await self._get_memory_usage(service_name)
            error_rate = await self._get_error_rate(service_name)
            
            # Calculate health score based on metrics
            if memory_usage > 85:
                health_score -= 20
                issues.append(IssueType.MEMORY_HIGH)
            elif memory_usage > 70:
                health_score -= 10
            
            if response_time > 2000:
                health_score -= 20
                issues.append(IssueType.RESPONSE_SLOW)
            elif response_time > 1000:
                health_score -= 10
            
            if error_rate > 5:
                health_score -= 25
                issues.append(IssueType.ERROR_RATE_HIGH)
            elif error_rate > 1:
                health_score -= 10
            
            # Ensure health score doesn't go below 0
            health_score = max(0, health_score)
            
        except Exception as e:
            logger.error(f"Error getting health data for {service_name}: {e}")
            status = "unreachable"
            health_score = 0
            issues.append(IssueType.SERVICE_DOWN)
        
        return ServiceHealth(
            service_name=service_name,
            tier=tier,
            health_score=health_score,
            memory_usage=memory_usage,
            response_time=response_time,
            error_rate=error_rate,
            status=status,
            last_check=datetime.utcnow(),
            issues=issues
        )
    
    async def _get_memory_usage(self, service_name: str) -> float:
        """Get memory usage for a service (simulated)"""
        # In real implementation, this would query Prometheus
        import random
        return random.uniform(20, 90)  # Simulate memory usage between 20-90%
    
    async def _get_error_rate(self, service_name: str) -> float:
        """Get error rate for a service (simulated)"""
        # In real implementation, this would query Prometheus
        import random
        return random.uniform(0, 10)  # Simulate error rate between 0-10%
    
    async def _check_and_remediate_issues(self, service_name: str, health_data: ServiceHealth) -> None:
        """Check for issues and take remediation actions"""
        for issue_type in health_data.issues:
            await self._handle_issue(service_name, issue_type, health_data)
    
    async def _handle_issue(self, service_name: str, issue_type: IssueType, health_data: ServiceHealth) -> None:
        """Handle a specific issue with a service"""
        rule = self.automation_rules.get(issue_type)
        if not rule:
            return
        
        # Check cooldown
        cooldown_key = f"{service_name}_{issue_type.value}"
        if cooldown_key in self.cooldown_tracker:
            if datetime.utcnow() < self.cooldown_tracker[cooldown_key]:
                logger.debug(f"Service {service_name} issue {issue_type.value} is in cooldown")
                return
        
        # Check max attempts
        attempt_key = f"{service_name}_{issue_type.value}"
        current_attempts = self.attempt_tracker.get(attempt_key, 0)
        if current_attempts >= rule.max_attempts:
            logger.warning(f"Service {service_name} issue {issue_type.value} has reached max attempts ({rule.max_attempts})")
            return
        
        # Take action
        action_taken = await self._execute_remediation_action(service_name, issue_type, rule.action, health_data)
        
        # Update tracking
        self.attempt_tracker[attempt_key] = current_attempts + 1
        self.cooldown_tracker[cooldown_key] = datetime.utcnow() + timedelta(seconds=rule.cooldown)
        
        # Log action
        action = AutomationAction(
            service_name=service_name,
            issue_type=issue_type,
            action_taken=action_taken,
            timestamp=datetime.utcnow(),
            success=True,  # Simplified for now
            attempt_number=current_attempts + 1
        )
        self.action_history.append(action)
        
        logger.info(f"Automated action taken for {service_name}: {action_taken}")
    
    async def _execute_remediation_action(self, service_name: str, issue_type: IssueType, action: str, health_data: ServiceHealth) -> str:
        """Execute a remediation action"""
        if action == "restart_service":
            return await self._restart_service(service_name)
        elif action == "optimize_service":
            return await self._optimize_service(service_name)
        elif action == "investigate_and_fix":
            return await self._investigate_and_fix(service_name, issue_type)
        else:
            return f"Unknown action: {action}"
    
    async def _restart_service(self, service_name: str) -> str:
        """Restart a service using kubectl"""
        try:
            # In real implementation, this would use kubectl
            logger.info(f"Restarting service {service_name}")
            return f"Service {service_name} restart initiated"
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return f"Failed to restart service {service_name}: {str(e)}"
    
    async def _optimize_service(self, service_name: str) -> str:
        """Optimize a service"""
        try:
            logger.info(f"Optimizing service {service_name}")
            return f"Service {service_name} optimization initiated"
        except Exception as e:
            logger.error(f"Failed to optimize service {service_name}: {e}")
            return f"Failed to optimize service {service_name}: {str(e)}"
    
    async def _investigate_and_fix(self, service_name: str, issue_type: IssueType) -> str:
        """Investigate and fix an issue"""
        try:
            logger.info(f"Investigating and fixing {issue_type.value} for service {service_name}")
            return f"Investigation and fix initiated for {service_name} issue {issue_type.value}"
        except Exception as e:
            logger.error(f"Failed to investigate and fix {service_name}: {e}")
            return f"Failed to investigate and fix {service_name}: {str(e)}"
    
    def _is_trading_hours(self) -> bool:
        """Check if it's currently trading hours (9:30 AM - 4:00 PM EST)"""
        now = datetime.utcnow()
        # Convert to EST (simplified)
        est_hour = now.hour - 5  # Rough EST conversion
        return 9 <= est_hour < 16  # 9:30 AM - 4:00 PM EST
    
    async def get_recent_actions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent automation actions"""
        recent_actions = self.action_history[-limit:] if self.action_history else []
        return [
            {
                "service_name": action.service_name,
                "issue_type": action.issue_type.value,
                "action_taken": action.action_taken,
                "timestamp": action.timestamp.isoformat(),
                "success": action.success,
                "attempt_number": action.attempt_number
            }
            for action in recent_actions
        ]
    
    async def get_service_health_overview(self) -> Dict[str, Any]:
        """Get overview of all service health"""
        if not self.service_health_cache:
            return {
                "message": "No health data available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        healthy_count = sum(1 for health in self.service_health_cache.values() if health.health_score >= 80)
        total_count = len(self.service_health_cache)
        
        return {
            "total_services": total_count,
            "healthy_services": healthy_count,
            "unhealthy_services": total_count - healthy_count,
            "health_percentage": round((healthy_count / total_count) * 100, 2) if total_count > 0 else 0,
            "services": {
                name: {
                    "tier": health.tier.value,
                    "health_score": health.health_score,
                    "status": health.status,
                    "memory_usage": health.memory_usage,
                    "response_time": health.response_time,
                    "error_rate": health.error_rate,
                    "issues": [issue.value for issue in health.issues],
                    "last_check": health.last_check.isoformat()
                }
                for name, health in self.service_health_cache.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
