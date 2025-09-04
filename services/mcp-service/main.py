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
from datetime import datetime

# Import MCP tools
from mcp_tools.architecture_tool import ArchitectureTool
from mcp_tools.service_discovery_tool import ServiceDiscoveryTool
from mcp_tools.system_control_tool import SystemControlTool
from mcp_tools.configuration_tool import ConfigurationTool

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "architecture",
                "description": "System architecture analysis and overview",
                "endpoints": ["/api/mcp/architecture", "/api/mcp/architecture/overview"]
            },
            {
                "name": "service_discovery",
                "description": "Service discovery and status monitoring",
                "endpoints": ["/api/mcp/services", "/api/mcp/services/status"]
            },
            {
                "name": "system_control",
                "description": "Basic system control operations",
                "endpoints": ["/api/mcp/control", "/api/mcp/control/ports"]
            },
            {
                "name": "configuration",
                "description": "Configuration management and inspection",
                "endpoints": ["/api/mcp/config", "/api/mcp/config/ports"]
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
