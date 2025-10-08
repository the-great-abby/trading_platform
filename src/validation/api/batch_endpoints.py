"""
Batch validation API endpoints

This module provides REST API endpoints for executing and managing
batch validation operations in the validation framework.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, BackgroundTasks
from pydantic import BaseModel

from ..execution.batch_validator import BatchValidator
from ..models.test_configuration import TestConfiguration
from ..models.validation_report import ValidationReport
from ..integration import get_validation_logger, record_batch_metric

logger = get_validation_logger(__name__)

router = APIRouter(prefix="/api/v1/batch", tags=["batch-validation"])


class BatchValidationRequest(BaseModel):
    """Request model for batch validation operations"""
    script_ids: List[str]
    test_config_id: Optional[str] = None
    parallel_execution: bool = True
    max_concurrent: int = 5
    timeout_seconds: Optional[int] = None


class BatchValidationResponse(BaseModel):
    """Response model for batch validation operations"""
    success: bool
    message: str
    batch_id: str
    total_scripts: int
    estimated_duration: Optional[float] = None


class BatchStatusResponse(BaseModel):
    """Response model for batch status"""
    batch_id: str
    status: str
    progress: float
    completed_scripts: int
    total_scripts: int
    successful_scripts: int
    failed_scripts: int
    message: str


class BatchResultsResponse(BaseModel):
    """Response model for batch results"""
    batch_id: str
    status: str
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    execution_time: float


class BatchValidationAPI:
    """
    API endpoints for batch validation operations.
    """
    
    def __init__(self):
        self.batch_validator = BatchValidator()
        self.active_batches: Dict[str, Dict[str, Any]] = {}
        self.batch_counter = 0
    
    @router.post("/execute", response_model=BatchValidationResponse)
    async def execute_batch_validation(
        self,
        request: BatchValidationRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Execute batch validation for multiple scripts.
        
        Args:
            request: Batch validation request parameters
            background_tasks: FastAPI background tasks
            
        Returns:
            Batch validation execution response
        """
        try:
            logger.info(f"Starting batch validation for {len(request.script_ids)} scripts")
            
            # Generate batch ID
            self.batch_counter += 1
            batch_id = f"batch_{self.batch_counter}_{int(logging.time.time())}"
            
            # Initialize batch tracking
            self.active_batches[batch_id] = {
                "status": "running",
                "progress": 0.0,
                "completed_scripts": 0,
                "total_scripts": len(request.script_ids),
                "successful_scripts": 0,
                "failed_scripts": 0,
                "start_time": None,
                "script_ids": request.script_ids,
                "results": []
            }
            
            # Execute batch validation in background
            background_tasks.add_task(
                self._execute_batch_validation_background,
                batch_id,
                request
            )
            
            # Estimate duration (rough calculation)
            estimated_duration = len(request.script_ids) * 3.0  # 3 seconds per script average
            
            logger.info(f"Batch validation started - Batch ID: {batch_id}")
            
            return BatchValidationResponse(
                success=True,
                message=f"Batch validation started with ID {batch_id}",
                batch_id=batch_id,
                total_scripts=len(request.script_ids),
                estimated_duration=estimated_duration
            )
            
        except Exception as e:
            logger.error(f"Failed to start batch validation: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to start batch validation: {str(e)}")
    
    async def _execute_batch_validation_background(self, batch_id: str, request: BatchValidationRequest):
        """Execute batch validation in background task."""
        try:
            batch_info = self.active_batches[batch_id]
            batch_info["start_time"] = logging.time.time()
            
            # Update status
            batch_info["status"] = "running"
            batch_info["progress"] = 0.0
            
            # Execute batch validation
            results = await self.batch_validator.validate_batch(
                script_ids=request.script_ids,
                test_config_id=request.test_config_id,
                parallel_execution=request.parallel_execution,
                max_concurrent=request.max_concurrent,
                timeout_seconds=request.timeout_seconds
            )
            
            # Update batch info with results
            batch_info["results"] = results
            batch_info["completed_scripts"] = len(results)
            
            # Count successful and failed scripts
            successful = sum(1 for r in results if r.get("status") == "PASSED")
            failed = len(results) - successful
            
            batch_info["successful_scripts"] = successful
            batch_info["failed_scripts"] = failed
            batch_info["progress"] = 100.0
            batch_info["status"] = "completed"
            
            # Record metrics
            record_batch_metric(len(request.script_ids), successful, failed)
            
            logger.info(f"Batch validation completed - Batch ID: {batch_id}")
            
        except Exception as e:
            # Mark batch as failed
            if batch_id in self.active_batches:
                self.active_batches[batch_id]["status"] = "failed"
                self.active_batches[batch_id]["progress"] = 0.0
            
            logger.error(f"Batch validation failed - Batch ID: {batch_id}: {e}")
        
        finally:
            # Clean up after a delay
            import asyncio
            await asyncio.sleep(3600)  # Keep batch info for 1 hour
            if batch_id in self.active_batches:
                del self.active_batches[batch_id]
    
    @router.get("/status/{batch_id}", response_model=BatchStatusResponse)
    async def get_batch_status(
        self,
        batch_id: str = Path(..., description="Batch identifier")
    ):
        """
        Get the current status of a batch validation operation.
        
        Args:
            batch_id: Unique identifier for the batch
            
        Returns:
            Current batch validation status
        """
        try:
            if batch_id not in self.active_batches:
                raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
            
            batch_info = self.active_batches[batch_id]
            
            return BatchStatusResponse(
                batch_id=batch_id,
                status=batch_info["status"],
                progress=batch_info["progress"],
                completed_scripts=batch_info["completed_scripts"],
                total_scripts=batch_info["total_scripts"],
                successful_scripts=batch_info["successful_scripts"],
                failed_scripts=batch_info["failed_scripts"],
                message=f"Batch validation {batch_info['status']}"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get batch status for {batch_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")
    
    @router.get("/results/{batch_id}", response_model=BatchResultsResponse)
    async def get_batch_results(
        self,
        batch_id: str = Path(..., description="Batch identifier")
    ):
        """
        Get results for a completed batch validation.
        
        Args:
            batch_id: Unique identifier for the batch
            
        Returns:
            Batch validation results and summary
        """
        try:
            if batch_id not in self.active_batches:
                raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
            
            batch_info = self.active_batches[batch_id]
            
            if batch_info["status"] != "completed":
                raise HTTPException(
                    status_code=400, 
                    detail=f"Batch {batch_id} is not completed yet (status: {batch_info['status']})"
                )
            
            # Calculate execution time
            execution_time = 0.0
            if batch_info["start_time"]:
                execution_time = logging.time.time() - batch_info["start_time"]
            
            # Create summary
            summary = {
                "total_scripts": batch_info["total_scripts"],
                "successful_scripts": batch_info["successful_scripts"],
                "failed_scripts": batch_info["failed_scripts"],
                "success_rate": batch_info["successful_scripts"] / batch_info["total_scripts"] if batch_info["total_scripts"] > 0 else 0,
                "execution_time": execution_time,
                "average_time_per_script": execution_time / batch_info["total_scripts"] if batch_info["total_scripts"] > 0 else 0
            }
            
            return BatchResultsResponse(
                batch_id=batch_id,
                status=batch_info["status"],
                results=batch_info["results"],
                summary=summary,
                execution_time=execution_time
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get batch results for {batch_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get batch results: {str(e)}")
    
    @router.delete("/cancel/{batch_id}")
    async def cancel_batch_validation(
        self,
        batch_id: str = Path(..., description="Batch identifier")
    ):
        """
        Cancel a running batch validation operation.
        
        Args:
            batch_id: Unique identifier for the batch
            
        Returns:
            Cancellation confirmation
        """
        try:
            logger.info(f"Cancelling batch validation - Batch ID: {batch_id}")
            
            if batch_id not in self.active_batches:
                raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
            
            batch_info = self.active_batches[batch_id]
            
            if batch_info["status"] != "running":
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot cancel batch {batch_id} (status: {batch_info['status']})"
                )
            
            # TODO: In a real implementation, this would:
            # 1. Cancel all running script executions
            # 2. Clean up resources
            # 3. Update status in database
            
            # Mark as cancelled
            batch_info["status"] = "cancelled"
            batch_info["progress"] = 0.0
            
            logger.info(f"Batch validation cancelled - Batch ID: {batch_id}")
            
            return {
                "success": True,
                "message": f"Batch validation {batch_id} cancelled successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel batch validation {batch_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to cancel batch validation: {str(e)}")
    
    @router.get("/history")
    async def get_batch_history(
        self,
        limit: int = Query(10, description="Maximum number of batch entries"),
        offset: int = Query(0, description="Number of entries to skip"),
        status_filter: Optional[str] = Query(None, description="Filter by batch status")
    ):
        """
        Get batch validation history.
        
        Args:
            limit: Maximum number of batch entries to return
            offset: Number of entries to skip for pagination
            status_filter: Filter batches by status
            
        Returns:
            Batch validation history
        """
        try:
            logger.info("Getting batch validation history")
            
            # TODO: In a real implementation, this would query the database
            # For now, return mock data
            mock_history = [
                {
                    "batch_id": "batch_1_1642248000",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "status": "completed",
                    "total_scripts": 5,
                    "successful_scripts": 4,
                    "failed_scripts": 1,
                    "execution_time": 15.2
                },
                {
                    "batch_id": "batch_2_1642241400",
                    "timestamp": "2024-01-15T08:30:00Z",
                    "status": "failed",
                    "total_scripts": 3,
                    "successful_scripts": 0,
                    "failed_scripts": 3,
                    "execution_time": 8.5,
                    "error": "Timeout during execution"
                }
            ]
            
            # Apply status filter
            if status_filter:
                mock_history = [b for b in mock_history if b["status"] == status_filter]
            
            # Apply pagination
            total_count = len(mock_history)
            paginated_history = mock_history[offset:offset + limit]
            
            logger.info(f"Batch history retrieved - Total: {total_count}, Returned: {len(paginated_history)}")
            
            return {
                "success": True,
                "history": paginated_history,
                "total_count": total_count,
                "message": "Batch validation history retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get batch history: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get batch history: {str(e)}")
    
    @router.get("/active")
    async def get_active_batches(self):
        """
        Get list of currently active batch validations.
        
        Returns:
            List of active batch validations
        """
        try:
            logger.info("Getting active batch validations")
            
            active_list = []
            for batch_id, info in self.active_batches.items():
                active_list.append({
                    "batch_id": batch_id,
                    "status": info["status"],
                    "progress": info["progress"],
                    "total_scripts": info["total_scripts"],
                    "completed_scripts": info["completed_scripts"],
                    "start_time": info.get("start_time")
                })
            
            logger.info(f"Active batch validations retrieved: {len(active_list)}")
            
            return {
                "success": True,
                "active_batches": active_list,
                "total_count": len(active_list),
                "message": "Active batch validations retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get active batch validations: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get active batch validations: {str(e)}")


# Create router instance
batch_validation_api = BatchValidationAPI()













