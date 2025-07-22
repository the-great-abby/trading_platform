#!/usr/bin/env python3
"""
Start Report Viewer Server
Simple web server for viewing HTML backtest reports
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.report_viewer_service import ReportViewerService


def main():
    """Start the report viewer server"""
    
    print("🚀 Starting Backtest Report Viewer...")
    print("📊 This will serve HTML reports via web browser")
    print("💡 Access at: http://localhost:8080")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    try:
        # Initialize and start the report viewer service
        service = ReportViewerService(reports_dir="reports/html", port=8080)
        service.start_server(host="0.0.0.0")
        
    except KeyboardInterrupt:
        print("\n👋 Report viewer stopped")
    except Exception as e:
        print(f"❌ Error starting report viewer: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 