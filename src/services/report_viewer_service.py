"""
Report Viewer Service - Web server for viewing HTML reports
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)


class ReportViewerService:
    """Web server for viewing HTML backtest reports"""
    
    def __init__(self, reports_dir: str = "reports/html", port: int = 8080):
        self.reports_dir = Path(reports_dir)
        self.port = port
        self.app = FastAPI(title="Backtest Report Viewer", version="1.0.0")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Mount static files
        if self.reports_dir.exists():
            self.app.mount("/reports", StaticFiles(directory=str(self.reports_dir)), name="reports")
        
        self._setup_routes()
        
        logger.info(f"Report viewer service initialized on port {port}")
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """Main index page with list of available reports"""
            reports = self._get_available_reports()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Backtest Report Viewer</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
                    .report-list {{ margin-top: 20px; }}
                    .report-item {{ 
                        background: #f8f9fa; 
                        border: 1px solid #e0e0e0; 
                        border-radius: 6px; 
                        padding: 15px; 
                        margin: 10px 0; 
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center;
                    }}
                    .report-link {{ 
                        background: #3498db; 
                        color: white; 
                        padding: 8px 16px; 
                        text-decoration: none; 
                        border-radius: 4px;
                    }}
                    .report-link:hover {{ background: #2980b9; }}
                    .no-reports {{ color: #666; font-style: italic; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📊 Backtest Report Viewer</h1>
                    <p>View and analyze your algorithmic trading backtest results</p>
                </div>
                
                <div class="report-list">
                    <h2>Available Reports ({len(reports)})</h2>
                    {self._generate_report_list_html(reports)}
                </div>
                
                <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 6px;">
                    <h3>📋 How to Generate Reports</h3>
                    <p>To generate new reports, use the CLI tool:</p>
                    <code>python scripts/generate_html_report.py --latest 5</code>
                    <br><br>
                    <p>Or generate a specific report:</p>
                    <code>python scripts/generate_html_report.py --run-id your_backtest_run_id</code>
                </div>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        
        @self.app.get("/reports/{report_name}")
        async def get_report(report_name: str):
            """Serve a specific report"""
            report_path = self.reports_dir / report_name
            
            if not report_path.exists():
                raise HTTPException(status_code=404, detail="Report not found")
            
            return FileResponse(report_path)
        
        @self.app.get("/api/reports")
        async def list_reports():
            """API endpoint to list available reports"""
            reports = self._get_available_reports()
            return {"reports": reports, "total": len(reports)}
    
    def _get_available_reports(self) -> List[dict]:
        """Get list of available HTML reports"""
        reports = []
        
        if not self.reports_dir.exists():
            return reports
        
        for file_path in self.reports_dir.glob("*.html"):
            stats = file_path.stat()
            reports.append({
                "name": file_path.name,
                "size": f"{stats.st_size / 1024:.1f} KB",
                "modified": stats.st_mtime,
                "url": f"/reports/{file_path.name}"
            })
        
        # Sort by modification time (newest first)
        reports.sort(key=lambda x: x["modified"], reverse=True)
        return reports
    
    def _generate_report_list_html(self, reports: List[dict]) -> str:
        """Generate HTML for report list"""
        if not reports:
            return '<p class="no-reports">No reports found. Generate some reports first!</p>'
        
        html = ""
        for report in reports:
            html += f"""
            <div class="report-item">
                <div>
                    <strong>{report['name']}</strong><br>
                    <small>Size: {report['size']} | Modified: {report['modified']}</small>
                </div>
                <a href="{report['url']}" class="report-link" target="_blank">View Report</a>
            </div>
            """
        
        return html
    
    def start_server(self, host: str = "0.0.0.0"):
        """Start the report viewer server"""
        logger.info(f"Starting report viewer server on {host}:{self.port}")
        logger.info(f"Reports directory: {self.reports_dir}")
        logger.info(f"Access the viewer at: http://{host}:{self.port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=self.port,
            log_level="info"
        )


def main():
    """CLI entry point for the report viewer service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the backtest report viewer server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--reports-dir", default="reports/html", help="Directory containing HTML reports")
    
    args = parser.parse_args()
    
    # Create reports directory if it doesn't exist
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Start the server
    service = ReportViewerService(reports_dir=str(reports_dir), port=args.port)
    service.start_server(host=args.host)


if __name__ == "__main__":
    main() 