"""
Report Service - Generates HTML reports from backtest results
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.services.database.backtest_results_service import BacktestResultsService
from src.backtesting.results.html_report_generator import HTMLReportGenerator

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating HTML reports from backtest results"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.results_service = BacktestResultsService()
        self.html_generator = HTMLReportGenerator(output_dir=str(self.output_dir / "html"))
        
        logger.info("Report service initialized")
    
    def generate_report_from_run_id(self, run_id: str, 
                                  report_title: Optional[str] = None) -> str:
        """Generate HTML report from a specific backtest run ID"""
        
        try:
            # Get backtest run data
            run_data = self.results_service.get_backtest_run(run_id)
            if not run_data:
                raise ValueError(f"Backtest run {run_id} not found")
            
            # Get trades for this run
            trades_data = self.results_service.get_trades_for_run(run_id)
            
            # Get equity curve data
            equity_data = self.results_service.get_equity_curve_for_run(run_id)
            
            # Convert to BacktestResult format
            result = self._convert_to_backtest_result(run_data, trades_data, equity_data)
            
            # Generate report
            symbols = run_data.get('symbols', [])
            start_date = run_data.get('start_date', '')
            end_date = run_data.get('end_date', '')
            
            if report_title is None:
                report_title = f"Backtest Report - {run_data.get('strategy_name', 'Unknown Strategy')}"
            
            report_path = self.html_generator.generate_single_strategy_report(
                strategy_name=run_data.get('strategy_name', 'Unknown'),
                result=result,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"Generated HTML report for run {run_id}: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating report for run {run_id}: {str(e)}")
            raise
    
    def generate_comparison_report(self, run_ids: List[str], 
                                 report_title: Optional[str] = None) -> str:
        """Generate comparison report for multiple backtest runs"""
        
        try:
            results = {}
            
            for run_id in run_ids:
                # Get backtest run data
                run_data = self.results_service.get_backtest_run(run_id)
                if not run_data:
                    logger.warning(f"Backtest run {run_id} not found, skipping")
                    continue
                
                # Get trades for this run
                trades_data = self.results_service.get_trades_for_run(run_id)
                
                # Get equity curve data
                equity_data = self.results_service.get_equity_curve_for_run(run_id)
                
                # Convert to BacktestResult format
                result = self._convert_to_backtest_result(run_data, trades_data, equity_data)
                
                strategy_name = run_data.get('strategy_name', f'Strategy_{run_id}')
                results[strategy_name] = result
            
            if not results:
                raise ValueError("No valid backtest runs found")
            
            # Use data from first run for common parameters
            first_run = self.results_service.get_backtest_run(run_ids[0])
            symbols = first_run.get('symbols', [])
            start_date = first_run.get('start_date', '')
            end_date = first_run.get('end_date', '')
            
            if report_title is None:
                report_title = "Backtest Comparison Report"
            
            report_path = self.html_generator.generate_report(
                results=results,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                report_title=report_title
            )
            
            logger.info(f"Generated comparison report for {len(results)} strategies: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating comparison report: {str(e)}")
            raise
    
    def generate_latest_reports(self, limit: int = 10) -> List[str]:
        """Generate reports for the latest backtest runs"""
        
        try:
            # Get latest backtest runs
            latest_runs = self.results_service.get_latest_backtest_runs(limit)
            
            if not latest_runs:
                logger.warning("No backtest runs found")
                return []
            
            report_paths = []
            
            # Generate individual reports for each run
            for run in latest_runs:
                run_id = run.get('run_id')
                if run_id:
                    try:
                        report_path = self.generate_report_from_run_id(run_id)
                        report_paths.append(report_path)
                    except Exception as e:
                        logger.error(f"Error generating report for run {run_id}: {str(e)}")
            
            # Generate comparison report if multiple runs
            if len(latest_runs) > 1:
                try:
                    run_ids = [run.get('run_id') for run in latest_runs if run.get('run_id')]
                    comparison_path = self.generate_comparison_report(run_ids)
                    report_paths.append(comparison_path)
                except Exception as e:
                    logger.error(f"Error generating comparison report: {str(e)}")
            
            logger.info(f"Generated {len(report_paths)} reports")
            return report_paths
            
        except Exception as e:
            logger.error(f"Error generating latest reports: {str(e)}")
            raise
    
    def _convert_to_backtest_result(self, run_data: Dict, 
                                   trades_data: List[Dict], 
                                   equity_data: List[Dict]) -> Any:
        """Convert database data to BacktestResult format"""
        
        # Import here to avoid circular imports
        from src.backtesting.engine.backtest_engine import BacktestResult, BacktestTrade
        import pandas as pd
        
        # Convert trades
        trades = []
        for trade_data in trades_data:
            trade = BacktestTrade(
                timestamp=datetime.fromisoformat(trade_data['timestamp']),
                symbol=trade_data['symbol'],
                action=trade_data['action'],
                quantity=trade_data['quantity'],
                price=trade_data['price'],
                pnl=trade_data['pnl'],
                confidence=trade_data['confidence'],
                portfolio_value=trade_data['portfolio_value'],
                cash=trade_data['cash'],
                position_value=trade_data['position_value'],
                total_pnl=trade_data['total_pnl'],
                trade_pnl=trade_data['trade_pnl'],
                strategy=run_data.get('strategy_name', 'Unknown')
            )
            trades.append(trade)
        
        # Convert equity curve
        equity_df = pd.DataFrame()
        if equity_data:
            equity_data_sorted = sorted(equity_data, key=lambda x: x['date'])
            dates = [datetime.fromisoformat(item['date']).date() for item in equity_data_sorted]
            portfolio_values = [item['portfolio_value'] for item in equity_data_sorted]
            
            equity_df = pd.DataFrame({
                'portfolio_value': portfolio_values
            }, index=pd.to_datetime(dates))
        
        # Create BacktestResult
        result = BacktestResult(
            strategy=run_data.get('strategy_name', 'Unknown'),
            initial_capital=run_data.get('initial_capital', 0.0),
            final_capital=run_data.get('final_capital', 0.0),
            total_return=run_data.get('total_return', 0.0),
            total_return_pct=run_data.get('total_return_pct', 0.0),
            max_drawdown_pct=run_data.get('max_drawdown_pct', 0.0),
            sharpe_ratio=run_data.get('sharpe_ratio', 0.0),
            total_trades=run_data.get('total_trades', 0),
            winning_trades=run_data.get('winning_trades', 0),
            losing_trades=run_data.get('losing_trades', 0),
            win_rate=run_data.get('win_rate', 0.0),
            profit_factor=run_data.get('profit_factor', 0.0),
            avg_win=run_data.get('avg_win', 0.0),
            avg_loss=run_data.get('avg_loss', 0.0),
            trades=trades,
            equity_curve=equity_df,
            start_date=datetime.fromisoformat(run_data.get('start_date', '2020-01-01')),
            end_date=datetime.fromisoformat(run_data.get('end_date', '2020-12-31'))
        )
        
        return result
    
    def list_available_reports(self) -> List[Dict]:
        """List all available backtest runs that can be used for reports"""
        
        try:
            runs = self.results_service.get_all_backtest_runs()
            
            report_list = []
            for run in runs:
                report_list.append({
                    'run_id': run.get('run_id'),
                    'strategy_name': run.get('strategy_name'),
                    'backtest_name': run.get('backtest_name'),
                    'start_date': run.get('start_date'),
                    'end_date': run.get('end_date'),
                    'total_return_pct': run.get('total_return_pct'),
                    'total_trades': run.get('total_trades'),
                    'created_at': run.get('created_at')
                })
            
            return report_list
            
        except Exception as e:
            logger.error(f"Error listing available reports: {str(e)}")
            return []
    
    def cleanup_old_reports(self, days_to_keep: int = 30):
        """Clean up old report files"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            html_dir = self.output_dir / "html"
            if html_dir.exists():
                for file_path in html_dir.glob("*.html"):
                    if file_path.stat().st_mtime < cutoff_date.timestamp():
                        file_path.unlink()
                        logger.info(f"Deleted old report: {file_path}")
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}") 