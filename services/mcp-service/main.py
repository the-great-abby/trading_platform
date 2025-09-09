"""
Trading System MCP Service
Model Context Protocol service for trading system control and monitoring
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
import logging
import os
from datetime import datetime

# Import MCP tools
from mcp_tools.architecture_tool import ArchitectureTool
from mcp_tools.service_discovery_tool import ServiceDiscoveryTool
from mcp_tools.system_control_tool import SystemControlTool
from mcp_tools.configuration_tool import ConfigurationTool
from mcp_tools.log_analysis_tool import LogAnalysisTool
from mcp_tools.intelligent_automation_tool import IntelligentAutomationTool
from mcp_tools.health_check_tester import HealthCheckTester
from mcp_tools.prometheus_tester import PrometheusTester
from mcp_tools.monitoring_integration import MonitoringIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading System MCP Service",
    description="Model Context Protocol service for trading system control and monitoring",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP tools
architecture_tool = ArchitectureTool()
service_discovery_tool = ServiceDiscoveryTool()
system_control_tool = SystemControlTool()
configuration_tool = ConfigurationTool()
log_analysis_tool = LogAnalysisTool()
intelligent_automation_tool = IntelligentAutomationTool()
health_check_tester = HealthCheckTester()
prometheus_tester = PrometheusTester()
monitoring_integration = MonitoringIntegration()

# Auto-start automation system on service startup
@app.on_event("startup")
async def startup_event():
    """Startup event handler - auto-start automation if enabled"""
    try:
        # Check if auto-start is enabled via environment variable
        auto_start = os.getenv("AUTO_START_AUTOMATION", "false").lower() == "true"
        if auto_start:
            logger.info("Auto-starting automation system...")
            result = await intelligent_automation_tool.start_automation_system()
            if result.get("status") == "started":
                logger.info("Automation system started successfully")
            else:
                logger.warning(f"Failed to start automation: {result.get('message')}")
        else:
            logger.info("Automation system ready - call /api/mcp/automation/start to begin")
        
        # Start background health monitoring task
        asyncio.create_task(background_health_monitor())
    except Exception as e:
        logger.error(f"Error during startup: {e}")

async def background_health_monitor():
    """Background task to monitor system health and auto-start automation if needed"""
    while True:
        try:
            # Check if automation is running
            if not intelligent_automation_tool.automation_running:
                # Check if we should auto-start based on system health
                health_check = await health_check_tester.test_all_endpoints()
                if health_check.get("success_rate", 0) > 50:  # If more than 50% of services are healthy
                    logger.info("System health detected - auto-starting automation...")
                    result = await intelligent_automation_tool.start_automation_system()
                    if result.get("status") == "started":
                        logger.info("Automation auto-started successfully")
                    else:
                        logger.warning(f"Failed to auto-start automation: {result.get('message')}")
            
            # Wait 5 minutes before next check
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Error in background health monitor: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler - stop automation system"""
    try:
        if intelligent_automation_tool.automation_running:
            logger.info("Stopping automation system...")
            await intelligent_automation_tool.stop_automation_system()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint with automation status"""
    automation_status = await intelligent_automation_tool.get_automation_status()
    return {
        "status": "healthy",
        "service": "mcp-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "automation": {
            "running": automation_status.get("automation_running", False),
            "monitoring_tasks": automation_status.get("monitoring_tasks", 0),
            "total_actions": automation_status.get("total_actions_taken", 0)
        }
    }

@app.get("/api/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "architecture",
                "description": "System architecture analysis and overview",
                "endpoints": ["/api/mcp/architecture", "/api/mcp/architecture/overview", "/api/mcp/architecture/trading-status"]
            },
            {
                "name": "service_discovery",
                "description": "Service discovery and status monitoring",
                "endpoints": ["/api/mcp/services", "/api/mcp/services/status", "/api/mcp/services/health/score"]
            },
            {
                "name": "system_control",
                "description": "Basic system control operations",
                "endpoints": ["/api/mcp/control", "/api/mcp/control/ports", "/api/mcp/control/ports/conflicts"]
            },
            {
                "name": "configuration",
                "description": "Configuration management and inspection",
                "endpoints": ["/api/mcp/config", "/api/mcp/config/ports", "/api/mcp/config/environment"]
            },
            {
                "name": "log_analysis",
                "description": "Log analysis and error detection",
                "endpoints": ["/api/mcp/logs/errors", "/api/mcp/logs/search", "/api/mcp/logs/health"]
            }
        ]
    }

# Architecture Tool Endpoints
@app.get("/api/mcp/architecture")
async def get_system_architecture():
    """Get complete system architecture"""
    try:
        return await architecture_tool.get_system_architecture()
    except Exception as e:
        logger.error(f"Error getting system architecture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/architecture/overview")
async def get_architecture_overview():
    """Get high-level architecture overview"""
    try:
        return await architecture_tool.get_architecture_overview()
    except Exception as e:
        logger.error(f"Error getting architecture overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/architecture/data-flow")
async def get_data_flow():
    """Get system data flow diagram"""
    try:
        return await architecture_tool.get_data_flow()
    except Exception as e:
        logger.error(f"Error getting data flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/architecture/trading-status")
async def get_trading_system_status():
    """Get current trading system operational status"""
    try:
        return await architecture_tool.get_trading_system_status()
    except Exception as e:
        logger.error(f"Error getting trading system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/architecture/trading-summary")
async def get_trading_architecture_summary():
    """Get trading-specific architecture summary"""
    try:
        return await architecture_tool.get_trading_architecture_summary()
    except Exception as e:
        logger.error(f"Error getting trading architecture summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/architecture/capabilities")
async def get_system_capabilities():
    """Get system capabilities and features"""
    try:
        return await architecture_tool.get_system_capabilities()
    except Exception as e:
        logger.error(f"Error getting system capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Service Discovery Tool Endpoints
@app.get("/api/mcp/services")
async def list_services():
    """List all services in the system"""
    try:
        return await service_discovery_tool.list_all_services()
    except Exception as e:
        logger.error(f"Error listing services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/status")
async def get_services_status():
    """Get status of all services"""
    try:
        return await service_discovery_tool.get_services_status()
    except Exception as e:
        logger.error(f"Error getting services status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/{service_name}")
async def get_service_details(service_name: str):
    """Get detailed information about a specific service"""
    try:
        return await service_discovery_tool.get_service_details(service_name)
    except Exception as e:
        logger.error(f"Error getting service details for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/{service_name}/health")
async def check_service_health(service_name: str):
    """Check health of a specific service"""
    try:
        return await service_discovery_tool.check_service_health(service_name)
    except Exception as e:
        logger.error(f"Error checking health for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/{service_name}/metrics")
async def get_service_metrics(service_name: str):
    """Get detailed metrics for a specific service"""
    try:
        return await service_discovery_tool.get_service_metrics(service_name)
    except Exception as e:
        logger.error(f"Error getting metrics for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/{service_name}/dependencies")
async def get_service_dependencies(service_name: str):
    """Get dependencies for a specific service"""
    try:
        return await service_discovery_tool.get_service_dependencies(service_name)
    except Exception as e:
        logger.error(f"Error getting dependencies for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/health/ranking")
async def get_services_health_ranking():
    """Get services ranked by health status"""
    try:
        return await service_discovery_tool.get_services_ranked_by_health()
    except Exception as e:
        logger.error(f"Error getting health ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/health/score")
async def get_comprehensive_health_score():
    """Get comprehensive health score for the entire system"""
    try:
        return await service_discovery_tool.get_comprehensive_health_score()
    except Exception as e:
        logger.error(f"Error getting comprehensive health score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/health/trends")
async def get_service_health_trends():
    """Get health trends and patterns"""
    try:
        return await service_discovery_tool.get_service_health_trends()
    except Exception as e:
        logger.error(f"Error getting health trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/services/health/recommendations")
async def get_health_recommendations():
    """Get health improvement recommendations"""
    try:
        return await service_discovery_tool.get_health_recommendations()
    except Exception as e:
        logger.error(f"Error getting health recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System Control Tool Endpoints
@app.get("/api/mcp/control/ports")
async def get_port_mappings():
    """Get current port mappings"""
    try:
        return await system_control_tool.get_port_mappings()
    except Exception as e:
        logger.error(f"Error getting port mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcp/control/ports/forward")
async def forward_ports(ports: List[int]):
    """Forward specific ports"""
    try:
        return await system_control_tool.forward_ports(ports)
    except Exception as e:
        logger.error(f"Error forwarding ports {ports}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/control/kubernetes/pods")
async def get_kubernetes_pods():
    """Get Kubernetes pod status"""
    try:
        return await system_control_tool.get_kubernetes_pods()
    except Exception as e:
        logger.error(f"Error getting Kubernetes pods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/control/ports/conflicts")
async def detect_port_conflicts():
    """Detect port conflicts and suggest solutions"""
    try:
        return await system_control_tool.detect_port_conflicts()
    except Exception as e:
        logger.error(f"Error detecting port conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/control/ports/utilization")
async def get_port_utilization():
    """Get port utilization summary"""
    try:
        return await system_control_tool.get_port_utilization_summary()
    except Exception as e:
        logger.error(f"Error getting port utilization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/control/ports/alternatives/{port}")
async def suggest_port_alternatives(port: int):
    """Suggest alternative ports for a given port"""
    try:
        return await system_control_tool.suggest_port_alternatives(port)
    except Exception as e:
        logger.error(f"Error suggesting port alternatives for {port}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/control/ports/active")
async def get_active_port_forwards():
    """Get currently active port forwards"""
    try:
        return await system_control_tool.get_active_port_forwards()
    except Exception as e:
        logger.error(f"Error getting active port forwards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Tool Endpoints
@app.get("/api/mcp/config")
async def get_system_config():
    """Get system configuration"""
    try:
        return await configuration_tool.get_system_config()
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/config/ports")
async def get_port_config():
    """Get port configuration"""
    try:
        return await configuration_tool.get_port_config()
    except Exception as e:
        logger.error(f"Error getting port config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/config/environment")
async def get_environment_config():
    """Get environment variables"""
    try:
        return await configuration_tool.get_environment_config()
    except Exception as e:
        logger.error(f"Error getting environment config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Log Analysis Tool Endpoints
@app.get("/api/mcp/logs/errors")
async def get_recent_errors(hours: int = 24):
    """Get recent errors from all service logs"""
    try:
        return await log_analysis_tool.get_recent_errors(hours)
    except Exception as e:
        logger.error(f"Error getting recent errors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/logs/errors/summary")
async def get_error_summary():
    """Get error summary and statistics"""
    try:
        return await log_analysis_tool.get_error_summary()
    except Exception as e:
        logger.error(f"Error getting error summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/logs/search")
async def search_logs(query: str, service: Optional[str] = None, hours: int = 24):
    """Search logs for specific patterns"""
    try:
        return await log_analysis_tool.search_logs(query, service, hours)
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/logs/health")
async def get_log_health_score():
    """Get log-based health score"""
    try:
        return await log_analysis_tool.get_log_health_score()
    except Exception as e:
        logger.error(f"Error getting log health score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Automation Endpoints
@app.post("/api/mcp/automation/start")
async def start_automation():
    """Start the intelligent automation system"""
    try:
        return await intelligent_automation_tool.start_automation_system()
    except Exception as e:
        logger.error(f"Error starting automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcp/automation/stop")
async def stop_automation():
    """Stop the intelligent automation system"""
    try:
        return await intelligent_automation_tool.stop_automation_system()
    except Exception as e:
        logger.error(f"Error stopping automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/automation/status")
async def get_automation_status():
    """Get automation system status"""
    try:
        return await intelligent_automation_tool.get_automation_status()
    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/automation/recent-actions")
async def get_recent_actions(limit: int = 10):
    """Get recent automation actions"""
    try:
        return await intelligent_automation_tool.get_recent_actions(limit)
    except Exception as e:
        logger.error(f"Error getting recent actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health Check Testing Endpoints
@app.get("/api/mcp/health/test-all")
async def test_all_health_endpoints():
    """Test all health endpoints"""
    try:
        return await health_check_tester.test_all_endpoints()
    except Exception as e:
        logger.error(f"Error testing health endpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/health/test/{service_name}")
async def test_service_health(service_name: str):
    """Test specific service health endpoint"""
    try:
        return await health_check_tester.test_specific_service(service_name)
    except Exception as e:
        logger.error(f"Error testing service health for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/health/summary")
async def get_health_summary():
    """Get health summary for all services"""
    try:
        return await health_check_tester.get_health_summary()
    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Prometheus Testing Endpoints
@app.get("/api/mcp/prometheus/test-all")
async def test_all_prometheus_queries():
    """Test all Prometheus queries"""
    try:
        return await prometheus_tester.test_all_queries()
    except Exception as e:
        logger.error(f"Error testing Prometheus queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/prometheus/test/{service_name}")
async def test_service_prometheus_queries(service_name: str):
    """Test Prometheus queries for specific service"""
    try:
        return await prometheus_tester.test_service_queries(service_name)
    except Exception as e:
        logger.error(f"Error testing Prometheus queries for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/prometheus/connectivity")
async def test_prometheus_connectivity():
    """Test Prometheus connectivity"""
    try:
        return await prometheus_tester.test_prometheus_connectivity()
    except Exception as e:
        logger.error(f"Error testing Prometheus connectivity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Monitoring Integration Endpoints
@app.post("/api/mcp/monitoring/start")
async def start_monitoring():
    """Start real-time monitoring"""
    try:
        return await monitoring_integration.start_monitoring()
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcp/monitoring/stop")
async def stop_monitoring():
    """Stop real-time monitoring"""
    try:
        return await monitoring_integration.stop_monitoring()
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/monitoring/status")
async def get_monitoring_status():
    """Get monitoring status"""
    try:
        return await monitoring_integration.get_monitoring_status()
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/monitoring/overview")
async def get_monitoring_overview():
    """Get system monitoring overview"""
    try:
        return await monitoring_integration.get_system_overview()
    except Exception as e:
        logger.error(f"Error getting monitoring overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/monitoring/service/{service_name}")
async def get_service_monitoring_data(service_name: str):
    """Get monitoring data for specific service"""
    try:
        return await monitoring_integration.get_service_health_data(service_name)
    except Exception as e:
        logger.error(f"Error getting monitoring data for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/monitoring/alerts")
async def get_recent_alerts(limit: int = 20):
    """Get recent alerts"""
    try:
        return await monitoring_integration.get_recent_alerts(limit)
    except Exception as e:
        logger.error(f"Error getting recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
