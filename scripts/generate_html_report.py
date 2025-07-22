#!/usr/bin/env python3
"""
HTML Report Generator CLI
Generate MetaTrader-style HTML reports from backtest results
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.report_service import ReportService


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML reports from backtest results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for specific run ID
  python generate_html_report.py --run-id backtest_20250101_120000_momentum_strategy
  
  # Generate comparison report for multiple runs
  python generate_html_report.py --run-ids backtest_20250101_120000_momentum backtest_20250101_120000_mean_reversion
  
  # Generate reports for latest 5 runs
  python generate_html_report.py --latest 5
  
  # List available backtest runs
  python generate_html_report.py --list
  
  # Generate report with custom title
  python generate_html_report.py --run-id backtest_20250101_120000_momentum_strategy --title "My Custom Report"
        """
    )
    
    parser.add_argument(
        "--run-id",
        help="Generate report for specific backtest run ID"
    )
    
    parser.add_argument(
        "--run-ids",
        nargs="+",
        help="Generate comparison report for multiple backtest run IDs"
    )
    
    parser.add_argument(
        "--latest",
        type=int,
        help="Generate reports for latest N backtest runs"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available backtest runs"
    )
    
    parser.add_argument(
        "--title",
        help="Custom title for the report"
    )
    
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Output directory for reports (default: reports)"
    )
    
    parser.add_argument(
        "--cleanup",
        type=int,
        metavar="DAYS",
        help="Clean up reports older than N days"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize report service
        report_service = ReportService(output_dir=args.output_dir)
        
        if args.list:
            # List available reports
            reports = report_service.list_available_reports()
            
            if not reports:
                print("No backtest runs found in database.")
                return
            
            print(f"\nAvailable Backtest Runs ({len(reports)} total):")
            print("-" * 100)
            print(f"{'Run ID':<30} {'Strategy':<20} {'Start Date':<12} {'End Date':<12} {'Return %':<10} {'Trades':<8}")
            print("-" * 100)
            
            for report in reports:
                run_id = report.get('run_id', 'N/A')[:29]
                strategy = report.get('strategy_name', 'N/A')[:19]
                start_date = report.get('start_date', 'N/A')[:11]
                end_date = report.get('end_date', 'N/A')[:11]
                return_pct = f"{report.get('total_return_pct', 0):.2f}%"
                trades = report.get('total_trades', 0)
                
                print(f"{run_id:<30} {strategy:<20} {start_date:<12} {end_date:<12} {return_pct:<10} {trades:<8}")
            
            print("-" * 100)
            return
        
        if args.cleanup:
            # Clean up old reports
            print(f"Cleaning up reports older than {args.cleanup} days...")
            report_service.cleanup_old_reports(args.cleanup)
            print("Cleanup completed.")
            return
        
        if args.run_id:
            # Generate single report
            print(f"Generating report for run ID: {args.run_id}")
            report_path = report_service.generate_report_from_run_id(
                run_id=args.run_id,
                report_title=args.title
            )
            print(f"✅ Report generated: {report_path}")
            
        elif args.run_ids:
            # Generate comparison report
            print(f"Generating comparison report for {len(args.run_ids)} runs...")
            report_path = report_service.generate_comparison_report(
                run_ids=args.run_ids,
                report_title=args.title
            )
            print(f"✅ Comparison report generated: {report_path}")
            
        elif args.latest:
            # Generate reports for latest runs
            print(f"Generating reports for latest {args.latest} runs...")
            report_paths = report_service.generate_latest_reports(limit=args.latest)
            
            if report_paths:
                print(f"✅ Generated {len(report_paths)} reports:")
                for path in report_paths:
                    print(f"   - {path}")
            else:
                print("No reports generated.")
                
        else:
            # No action specified
            parser.print_help()
            return
        
        print(f"\n📁 Reports saved to: {args.output_dir}")
        print("💡 Open the HTML files in your web browser to view the reports")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 