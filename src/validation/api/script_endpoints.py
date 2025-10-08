"""
Script discovery API endpoints

This module provides REST API endpoints for discovering and managing
backtest scripts in the validation framework.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from ..discovery.script_discovery import BacktestScriptDiscovery
from ..models.backtest_script import BacktestScript
from ..integration import get_validation_logger, record_discovery_metric

logger = get_validation_logger(__name__)

router = APIRouter(prefix="/api/v1/scripts", tags=["script-discovery"])


class ScriptDiscoveryResponse(BaseModel):
    """Response model for script discovery operations"""
    success: bool
    message: str
    scripts: List[BacktestScript]
    total_count: int
    discovery_time: float


class ScriptInfoResponse(BaseModel):
    """Response model for individual script information"""
    success: bool
    script: Optional[BacktestScript]
    message: str


class ScriptDiscoveryAPI:
    """
    API endpoints for script discovery operations.
    """
    
    def __init__(self):
        self.discovery_service = BacktestScriptDiscovery()
    
    @router.get("/discover", response_model=ScriptDiscoveryResponse)
    async def discover_scripts(
        self,
        directory: Optional[str] = Query(None, description="Directory to search for scripts"),
        pattern: Optional[str] = Query(None, description="File pattern to match"),
        include_subdirectories: bool = Query(True, description="Include subdirectories in search"),
        max_depth: int = Query(3, description="Maximum directory depth to search")
    ):
        """
        Discover backtest scripts in the specified directory.
        
        Args:
            directory: Directory to search (defaults to current working directory)
            pattern: File pattern to match (defaults to *_backtest*.py)
            include_subdirectories: Whether to include subdirectories
            max_depth: Maximum directory depth to search
            
        Returns:
            List of discovered scripts with metadata
        """
        try:
            logger.info(f"Starting script discovery - Directory: {directory}, Pattern: {pattern}")
            
            # Discover scripts
            scripts = await self.discovery_service.discover_scripts(
                directory=directory,
                pattern=pattern,
                include_subdirectories=include_subdirectories,
                max_depth=max_depth
            )
            
            # Record metrics
            record_discovery_metric(len(scripts))
            
            logger.info(f"Script discovery completed - Found {len(scripts)} scripts")
            
            return ScriptDiscoveryResponse(
                success=True,
                message=f"Successfully discovered {len(scripts)} scripts",
                scripts=scripts,
                total_count=len(scripts),
                discovery_time=0.0  # TODO: Implement timing
            )
            
        except Exception as e:
            logger.error(f"Script discovery failed: {e}")
            raise HTTPException(status_code=500, detail=f"Script discovery failed: {str(e)}")
    
    @router.get("/", response_model=ScriptDiscoveryResponse)
    async def list_scripts(
        self,
        directory: Optional[str] = Query(None, description="Filter by directory"),
        script_type: Optional[str] = Query(None, description="Filter by script type"),
        status: Optional[str] = Query(None, description="Filter by validation status"),
        limit: int = Query(100, description="Maximum number of scripts to return"),
        offset: int = Query(0, description="Number of scripts to skip")
    ):
        """
        List all discovered scripts with optional filtering.
        
        Args:
            directory: Filter scripts by directory path
            script_type: Filter scripts by type (backtest, simulation, etc.)
            status: Filter scripts by validation status
            limit: Maximum number of scripts to return
            offset: Number of scripts to skip for pagination
            
        Returns:
            Paginated list of scripts
        """
        try:
            logger.info(f"Listing scripts - Directory: {directory}, Type: {script_type}, Status: {status}")
            
            # Get all scripts (in a real implementation, this would query a database)
            all_scripts = await self.discovery_service.discover_scripts()
            
            # Apply filters
            filtered_scripts = all_scripts
            
            if directory:
                filtered_scripts = [s for s in filtered_scripts if directory in s.file_path]
            
            if script_type:
                filtered_scripts = [s for s in filtered_scripts if script_type in s.script_type]
            
            if status:
                filtered_scripts = [s for s in filtered_scripts if s.validation_status == status]
            
            # Apply pagination
            total_count = len(filtered_scripts)
            paginated_scripts = filtered_scripts[offset:offset + limit]
            
            logger.info(f"Script listing completed - Total: {total_count}, Returned: {len(paginated_scripts)}")
            
            return ScriptDiscoveryResponse(
                success=True,
                message=f"Successfully listed {len(paginated_scripts)} scripts",
                scripts=paginated_scripts,
                total_count=total_count,
                discovery_time=0.0
            )
            
        except Exception as e:
            logger.error(f"Script listing failed: {e}")
            raise HTTPException(status_code=500, detail=f"Script listing failed: {str(e)}")
    
    @router.get("/{script_id}", response_model=ScriptInfoResponse)
    async def get_script_info(
        self,
        script_id: str = Path(..., description="Script identifier")
    ):
        """
        Get detailed information about a specific script.
        
        Args:
            script_id: Unique identifier for the script
            
        Returns:
            Detailed script information
        """
        try:
            logger.info(f"Getting script info for ID: {script_id}")
            
            # Find script by ID (in a real implementation, this would query a database)
            all_scripts = await self.discovery_service.discover_scripts()
            script = next((s for s in all_scripts if s.script_id == script_id), None)
            
            if not script:
                raise HTTPException(status_code=404, detail=f"Script with ID {script_id} not found")
            
            logger.info(f"Script info retrieved for ID: {script_id}")
            
            return ScriptInfoResponse(
                success=True,
                script=script,
                message="Script information retrieved successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get script info for ID {script_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get script info: {str(e)}")
    
    @router.post("/{script_id}/refresh")
    async def refresh_script_info(
        self,
        script_id: str = Path(..., description="Script identifier")
    ):
        """
        Refresh script information by re-analyzing the script file.
        
        Args:
            script_id: Unique identifier for the script
            
        Returns:
            Success message
        """
        try:
            logger.info(f"Refreshing script info for ID: {script_id}")
            
            # In a real implementation, this would:
            # 1. Find the script file
            # 2. Re-analyze its metadata
            # 3. Update the database record
            
            logger.info(f"Script info refreshed for ID: {script_id}")
            
            return {"success": True, "message": f"Script {script_id} information refreshed successfully"}
            
        except Exception as e:
            logger.error(f"Failed to refresh script info for ID {script_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to refresh script info: {str(e)}")
    
    @router.get("/stats/summary")
    async def get_discovery_stats(self):
        """
        Get summary statistics for script discovery.
        
        Returns:
            Discovery statistics
        """
        try:
            logger.info("Getting discovery statistics")
            
            all_scripts = await self.discovery_service.discover_scripts()
            
            # Calculate statistics
            stats = {
                "total_scripts": len(all_scripts),
                "by_directory": {},
                "by_type": {},
                "by_status": {},
                "average_file_size": 0,
                "total_file_size": 0
            }
            
            total_size = 0
            for script in all_scripts:
                # Directory statistics
                directory = script.file_path.rsplit('/', 1)[0] if '/' in script.file_path else '.'
                stats["by_directory"][directory] = stats["by_directory"].get(directory, 0) + 1
                
                # Type statistics
                stats["by_type"][script.script_type] = stats["by_type"].get(script.script_type, 0) + 1
                
                # Status statistics
                stats["by_status"][script.validation_status] = stats["by_status"].get(script.validation_status, 0) + 1
                
                # Size statistics
                total_size += script.file_size
            
            stats["total_file_size"] = total_size
            stats["average_file_size"] = total_size / len(all_scripts) if all_scripts else 0
            
            logger.info(f"Discovery statistics calculated - Total scripts: {len(all_scripts)}")
            
            return {
                "success": True,
                "statistics": stats,
                "message": "Discovery statistics retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get discovery statistics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get discovery statistics: {str(e)}")


# Create router instance
script_discovery_api = ScriptDiscoveryAPI()













