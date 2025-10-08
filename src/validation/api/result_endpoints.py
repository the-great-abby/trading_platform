"""
Result retrieval API endpoints

This module provides REST API endpoints for retrieving and managing
validation results in the validation framework.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
from datetime import datetime

from ..models.backtest_result import BacktestResult
from ..models.validation_report import ValidationReport
from ..integration import get_validation_logger

logger = get_validation_logger(__name__)

router = APIRouter(prefix="/api/v1/results", tags=["result-retrieval"])


class ResultQueryRequest(BaseModel):
    """Request model for result query operations"""
    script_ids: Optional[List[str]] = None
    batch_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status_filter: Optional[str] = None
    metrics_filter: Optional[Dict[str, Any]] = None


class ResultResponse(BaseModel):
    """Response model for result operations"""
    success: bool
    message: str
    results: List[BacktestResult]
    total_count: int
    query_time: float


class ResultAPI:
    """
    API endpoints for result retrieval operations.
    """
    
    def __init__(self):
        # In a real implementation, this would connect to a database
        self.mock_results: Dict[str, BacktestResult] = {}
        self.mock_reports: Dict[str, ValidationReport] = {}
    
    @router.get("/", response_model=ResultResponse)
    async def query_results(
        self,
        script_ids: Optional[str] = Query(None, description="Comma-separated list of script IDs"),
        batch_id: Optional[str] = Query(None, description="Batch identifier"),
        status: Optional[str] = Query(None, description="Filter by validation status"),
        date_from: Optional[datetime] = Query(None, description="Filter results from this date"),
        date_to: Optional[datetime] = Query(None, description="Filter results to this date"),
        limit: int = Query(100, description="Maximum number of results to return"),
        offset: int = Query(0, description="Number of results to skip")
    ):
        """
        Query validation results with optional filtering.
        
        Args:
            script_ids: Comma-separated list of script IDs to filter by
            batch_id: Batch identifier to filter by
            status: Validation status to filter by
            date_from: Start date for filtering
            date_to: End date for filtering
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination
            
        Returns:
            Filtered validation results
        """
        try:
            logger.info("Querying validation results")
            
            # Parse script IDs if provided
            script_id_list = None
            if script_ids:
                script_id_list = [sid.strip() for sid in script_ids.split(",")]
            
            # TODO: In a real implementation, this would query the database
            # For now, return mock data
            mock_results = self._generate_mock_results()
            
            # Apply filters
            filtered_results = mock_results
            
            if script_id_list:
                filtered_results = [r for r in filtered_results if r.script_id in script_id_list]
            
            if batch_id:
                filtered_results = [r for r in filtered_results if batch_id in r.metadata.get("batch_id", "")]
            
            if status:
                filtered_results = [r for r in filtered_results if r.validation_status == status]
            
            if date_from:
                filtered_results = [r for r in filtered_results if r.execution_time >= date_from]
            
            if date_to:
                filtered_results = [r for r in filtered_results if r.execution_time <= date_to]
            
            # Apply pagination
            total_count = len(filtered_results)
            paginated_results = filtered_results[offset:offset + limit]
            
            logger.info(f"Results queried - Total: {total_count}, Returned: {len(paginated_results)}")
            
            return ResultResponse(
                success=True,
                message=f"Successfully queried {len(paginated_results)} results",
                results=paginated_results,
                total_count=total_count,
                query_time=0.0
            )
            
        except Exception as e:
            logger.error(f"Failed to query results: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to query results: {str(e)}")
    
    @router.get("/{script_id}/latest")
    async def get_latest_result(
        self,
        script_id: str = Path(..., description="Script identifier")
    ):
        """
        Get the latest validation result for a specific script.
        
        Args:
            script_id: Unique identifier for the script
            
        Returns:
            Latest validation result
        """
        try:
            logger.info(f"Getting latest result for script - ID: {script_id}")
            
            # TODO: In a real implementation, this would query the database
            # For now, return mock data
            mock_results = self._generate_mock_results()
            script_results = [r for r in mock_results if r.script_id == script_id]
            
            if not script_results:
                raise HTTPException(status_code=404, detail=f"No results found for script {script_id}")
            
            # Get the latest result (assuming results are sorted by execution time)
            latest_result = max(script_results, key=lambda r: r.execution_time)
            
            logger.info(f"Latest result retrieved for script - ID: {script_id}")
            
            return {
                "success": True,
                "result": latest_result,
                "message": "Latest result retrieved successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get latest result for script {script_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get latest result: {str(e)}")
    
    @router.get("/{script_id}/history")
    async def get_result_history(
        self,
        script_id: str = Path(..., description="Script identifier"),
        limit: int = Query(10, description="Maximum number of history entries"),
        offset: int = Query(0, description="Number of entries to skip")
    ):
        """
        Get validation result history for a specific script.
        
        Args:
            script_id: Unique identifier for the script
            limit: Maximum number of history entries to return
            offset: Number of entries to skip for pagination
            
        Returns:
            Validation result history
        """
        try:
            logger.info(f"Getting result history for script - ID: {script_id}")
            
            # TODO: In a real implementation, this would query the database
            # For now, return mock data
            mock_results = self._generate_mock_results()
            script_results = [r for r in mock_results if r.script_id == script_id]
            
            # Sort by execution time (newest first)
            script_results.sort(key=lambda r: r.execution_time, reverse=True)
            
            # Apply pagination
            total_count = len(script_results)
            paginated_results = script_results[offset:offset + limit]
            
            logger.info(f"Result history retrieved for script - ID: {script_id}, Total: {total_count}")
            
            return {
                "success": True,
                "history": paginated_results,
                "total_count": total_count,
                "message": "Result history retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get result history for script {script_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get result history: {str(e)}")
    
    @router.get("/{script_id}/metrics")
    async def get_script_metrics(
        self,
        script_id: str = Path(..., description="Script identifier"),
        metric_names: Optional[str] = Query(None, description="Comma-separated list of metric names"),
        date_from: Optional[datetime] = Query(None, description="Filter metrics from this date"),
        date_to: Optional[datetime] = Query(None, description="Filter metrics to this date")
    ):
        """
        Get metrics for a specific script.
        
        Args:
            script_id: Unique identifier for the script
            metric_names: Comma-separated list of metric names to retrieve
            date_from: Start date for filtering
            date_to: End date for filtering
            
        Returns:
            Script metrics
        """
        try:
            logger.info(f"Getting metrics for script - ID: {script_id}")
            
            # Parse metric names if provided
            metric_list = None
            if metric_names:
                metric_list = [name.strip() for name in metric_names.split(",")]
            
            # TODO: In a real implementation, this would query the database
            # For now, return mock data
            mock_results = self._generate_mock_results()
            script_results = [r for r in mock_results if r.script_id == script_id]
            
            # Apply date filters
            if date_from:
                script_results = [r for r in script_results if r.execution_time >= date_from]
            if date_to:
                script_results = [r for r in script_results if r.execution_time <= date_to]
            
            # Extract metrics
            metrics_data = []
            for result in script_results:
                result_metrics = {}
                for metric_name, value in result.metrics.items():
                    if metric_list is None or metric_name in metric_list:
                        result_metrics[metric_name] = value
                
                metrics_data.append({
                    "execution_time": result.execution_time,
                    "validation_status": result.validation_status,
                    "metrics": result_metrics
                })
            
            logger.info(f"Metrics retrieved for script - ID: {script_id}, Results: {len(metrics_data)}")
            
            return {
                "success": True,
                "script_id": script_id,
                "metrics": metrics_data,
                "message": "Metrics retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get metrics for script {script_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
    
    @router.get("/comparison/{script_id_1}/{script_id_2}")
    async def compare_results(
        self,
        script_id_1: str = Path(..., description="First script identifier"),
        script_id_2: str = Path(..., description="Second script identifier"),
        metric_names: Optional[str] = Query(None, description="Comma-separated list of metrics to compare")
    ):
        """
        Compare validation results between two scripts.
        
        Args:
            script_id_1: First script identifier
            script_id_2: Second script identifier
            metric_names: Comma-separated list of metrics to compare
            
        Returns:
            Comparison results
        """
        try:
            logger.info(f"Comparing results - Script 1: {script_id_1}, Script 2: {script_id_2}")
            
            # Parse metric names if provided
            metric_list = None
            if metric_names:
                metric_list = [name.strip() for name in metric_names.split(",")]
            
            # TODO: In a real implementation, this would query the database
            # For now, return mock data
            mock_results = self._generate_mock_results()
            
            # Get latest results for both scripts
            script1_results = [r for r in mock_results if r.script_id == script_id_1]
            script2_results = [r for r in mock_results if r.script_id == script_id_2]
            
            if not script1_results:
                raise HTTPException(status_code=404, detail=f"No results found for script {script_id_1}")
            if not script2_results:
                raise HTTPException(status_code=404, detail=f"No results found for script {script_id_2}")
            
            latest1 = max(script1_results, key=lambda r: r.execution_time)
            latest2 = max(script2_results, key=lambda r: r.execution_time)
            
            # Compare metrics
            comparison = {}
            for metric_name in latest1.metrics.keys():
                if metric_list is None or metric_name in metric_list:
                    if metric_name in latest2.metrics:
                        comparison[metric_name] = {
                            "script_1": latest1.metrics[metric_name],
                            "script_2": latest2.metrics[metric_name],
                            "difference": latest1.metrics[metric_name] - latest2.metrics[metric_name],
                            "percentage_diff": (
                                (latest1.metrics[metric_name] - latest2.metrics[metric_name]) / 
                                latest2.metrics[metric_name] * 100
                                if latest2.metrics[metric_name] != 0 else 0
                            )
                        }
            
            logger.info(f"Results compared - Script 1: {script_id_1}, Script 2: {script_id_2}")
            
            return {
                "success": True,
                "comparison": {
                    "script_1": {
                        "script_id": script_id_1,
                        "execution_time": latest1.execution_time,
                        "validation_status": latest1.validation_status
                    },
                    "script_2": {
                        "script_id": script_id_2,
                        "execution_time": latest2.execution_time,
                        "validation_status": latest2.validation_status
                    },
                    "metrics_comparison": comparison
                },
                "message": "Results compared successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to compare results: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to compare results: {str(e)}")
    
    @router.get("/stats/summary")
    async def get_results_summary(
        self,
        date_from: Optional[datetime] = Query(None, description="Filter summary from this date"),
        date_to: Optional[datetime] = Query(None, description="Filter summary to this date")
    ):
        """
        Get summary statistics for validation results.
        
        Args:
            date_from: Start date for filtering
            date_to: End date for filtering
            
        Returns:
            Results summary statistics
        """
        try:
            logger.info("Getting results summary")
            
            # TODO: In a real implementation, this would query the database
            # For now, return mock data
            mock_results = self._generate_mock_results()
            
            # Apply date filters
            if date_from:
                mock_results = [r for r in mock_results if r.execution_time >= date_from]
            if date_to:
                mock_results = [r for r in mock_results if r.execution_time <= date_to]
            
            # Calculate statistics
            total_results = len(mock_results)
            successful_results = sum(1 for r in mock_results if r.validation_status == "PASSED")
            failed_results = total_results - successful_results
            
            # Calculate average metrics
            avg_metrics = {}
            if mock_results:
                for metric_name in mock_results[0].metrics.keys():
                    values = [r.metrics[metric_name] for r in mock_results if metric_name in r.metrics]
                    if values:
                        avg_metrics[metric_name] = sum(values) / len(values)
            
            summary = {
                "total_results": total_results,
                "successful_results": successful_results,
                "failed_results": failed_results,
                "success_rate": successful_results / total_results if total_results > 0 else 0,
                "average_metrics": avg_metrics,
                "date_range": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None
                }
            }
            
            logger.info(f"Results summary calculated - Total: {total_results}")
            
            return {
                "success": True,
                "summary": summary,
                "message": "Results summary retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get results summary: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get results summary: {str(e)}")
    
    def _generate_mock_results(self) -> List[BacktestResult]:
        """Generate mock validation results for testing."""
        from datetime import timedelta
        
        mock_results = []
        base_time = datetime.now()
        
        for i in range(10):
            result = BacktestResult(
                script_id=f"script_{i % 5}",  # 5 different scripts
                execution_time=base_time - timedelta(hours=i),
                validation_status="PASSED" if i % 3 != 0 else "FAILED",
                metrics={
                    "total_return_pct": 10.0 + i * 2.0,
                    "sharpe_ratio": 1.5 + i * 0.1,
                    "max_drawdown_pct": -5.0 - i * 0.5
                },
                metadata={
                    "batch_id": f"batch_{i // 3}",
                    "execution_duration": 3.0 + i * 0.5
                }
            )
            mock_results.append(result)
        
        return mock_results


# Create router instance
result_api = ResultAPI()













