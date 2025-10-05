"""
Report generation API endpoints

This module provides REST API endpoints for generating and retrieving
validation reports in the validation framework.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
from datetime import datetime

from ..reporting.report_generator import ReportGenerator
from ..models.validation_report import ValidationReport
from ..integration import get_validation_logger

logger = get_validation_logger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["report-generation"])


class ReportGenerationRequest(BaseModel):
    """Request model for report generation operations"""
    script_ids: Optional[List[str]] = None
    batch_id: Optional[str] = None
    report_type: str = "summary"  # summary, detailed, comparison
    format: str = "json"  # json, html, pdf
    include_metrics: bool = True
    include_charts: bool = False


class ReportResponse(BaseModel):
    """Response model for report operations"""
    success: bool
    message: str
    report_id: str
    report_url: Optional[str] = None
    generation_time: float


class ReportAPI:
    """
    API endpoints for report generation operations.
    """
    
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.generated_reports: Dict[str, Dict[str, Any]] = {}
    
    @router.post("/generate", response_model=ReportResponse)
    async def generate_report(self, request: ReportGenerationRequest):
        """
        Generate a validation report.
        
        Args:
            request: Report generation parameters
            
        Returns:
            Report generation response
        """
        try:
            logger.info(f"Starting report generation - Type: {request.report_type}, Format: {request.format}")
            
            # Generate report ID
            report_id = f"report_{int(datetime.now().timestamp())}"
            
            # Generate report
            start_time = datetime.now()
            report_data = await self.report_generator.generate_report(
                script_ids=request.script_ids,
                batch_id=request.batch_id,
                report_type=request.report_type,
                format=request.format,
                include_metrics=request.include_metrics,
                include_charts=request.include_charts
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Store report data
            self.generated_reports[report_id] = {
                "report_id": report_id,
                "report_type": request.report_type,
                "format": request.format,
                "generated_at": datetime.now().isoformat(),
                "generation_time": generation_time,
                "data": report_data
            }
            
            logger.info(f"Report generation completed - Report ID: {report_id}")
            
            return ReportResponse(
                success=True,
                message=f"Report generated successfully",
                report_id=report_id,
                report_url=f"/api/v1/reports/{report_id}",
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    
    @router.get("/{report_id}")
    async def get_report(
        self,
        report_id: str = Path(..., description="Report identifier"),
        format: Optional[str] = Query(None, description="Report format override")
    ):
        """
        Retrieve a generated report.
        
        Args:
            report_id: Unique identifier for the report
            format: Optional format override
            
        Returns:
            Report data
        """
        try:
            logger.info(f"Retrieving report - Report ID: {report_id}")
            
            if report_id not in self.generated_reports:
                raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
            
            report_info = self.generated_reports[report_id]
            
            # Apply format override if specified
            if format and format != report_info["format"]:
                # In a real implementation, this would regenerate the report in the new format
                logger.warning(f"Format override requested but not implemented: {format}")
            
            logger.info(f"Report retrieved - Report ID: {report_id}")
            
            return {
                "success": True,
                "report": report_info,
                "message": "Report retrieved successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve report {report_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")
    
    @router.get("/{report_id}/download")
    async def download_report(
        self,
        report_id: str = Path(..., description="Report identifier")
    ):
        """
        Download a report file.
        
        Args:
            report_id: Unique identifier for the report
            
        Returns:
            Report file download
        """
        try:
            logger.info(f"Downloading report - Report ID: {report_id}")
            
            if report_id not in self.generated_reports:
                raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
            
            report_info = self.generated_reports[report_id]
            
            # In a real implementation, this would return the actual file
            # For now, return the report data as JSON
            from fastapi.responses import JSONResponse
            
            return JSONResponse(
                content=report_info["data"],
                headers={
                    "Content-Disposition": f"attachment; filename={report_id}.{report_info['format']}"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to download report {report_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")
    
    @router.get("/")
    async def list_reports(
        self,
        report_type: Optional[str] = Query(None, description="Filter by report type"),
        format: Optional[str] = Query(None, description="Filter by format"),
        limit: int = Query(20, description="Maximum number of reports to return"),
        offset: int = Query(0, description="Number of reports to skip")
    ):
        """
        List generated reports with optional filtering.
        
        Args:
            report_type: Filter reports by type
            format: Filter reports by format
            limit: Maximum number of reports to return
            offset: Number of reports to skip for pagination
            
        Returns:
            List of reports
        """
        try:
            logger.info("Listing reports")
            
            # Filter reports
            filtered_reports = []
            for report_id, report_info in self.generated_reports.items():
                if report_type and report_info["report_type"] != report_type:
                    continue
                if format and report_info["format"] != format:
                    continue
                
                filtered_reports.append({
                    "report_id": report_id,
                    "report_type": report_info["report_type"],
                    "format": report_info["format"],
                    "generated_at": report_info["generated_at"],
                    "generation_time": report_info["generation_time"]
                })
            
            # Sort by generation time (newest first)
            filtered_reports.sort(key=lambda x: x["generated_at"], reverse=True)
            
            # Apply pagination
            total_count = len(filtered_reports)
            paginated_reports = filtered_reports[offset:offset + limit]
            
            logger.info(f"Reports listed - Total: {total_count}, Returned: {len(paginated_reports)}")
            
            return {
                "success": True,
                "reports": paginated_reports,
                "total_count": total_count,
                "message": "Reports listed successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")
    
    @router.delete("/{report_id}")
    async def delete_report(
        self,
        report_id: str = Path(..., description="Report identifier")
    ):
        """
        Delete a generated report.
        
        Args:
            report_id: Unique identifier for the report
            
        Returns:
            Deletion confirmation
        """
        try:
            logger.info(f"Deleting report - Report ID: {report_id}")
            
            if report_id not in self.generated_reports:
                raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
            
            # Remove report
            del self.generated_reports[report_id]
            
            logger.info(f"Report deleted - Report ID: {report_id}")
            
            return {
                "success": True,
                "message": f"Report {report_id} deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")
    
    @router.get("/templates/available")
    async def get_available_templates(self):
        """
        Get list of available report templates.
        
        Returns:
            Available report templates
        """
        try:
            logger.info("Getting available report templates")
            
            templates = [
                {
                    "template_id": "summary",
                    "name": "Summary Report",
                    "description": "High-level summary of validation results",
                    "supported_formats": ["json", "html"]
                },
                {
                    "template_id": "detailed",
                    "name": "Detailed Report",
                    "description": "Comprehensive validation results with metrics",
                    "supported_formats": ["json", "html", "pdf"]
                },
                {
                    "template_id": "comparison",
                    "name": "Comparison Report",
                    "description": "Compare multiple script validations",
                    "supported_formats": ["json", "html", "pdf"]
                }
            ]
            
            logger.info(f"Report templates retrieved - Count: {len(templates)}")
            
            return {
                "success": True,
                "templates": templates,
                "message": "Report templates retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get report templates: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get report templates: {str(e)}")


# Create router instance
report_api = ReportAPI()

