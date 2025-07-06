"""
Backtest Results Exporter - Generate CSV and Markdown reports
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List
from pathlib import Path

from .backtest_engine import BacktestResult, BacktestTrade


class BacktestResultsExporter:
    """Export backtest results to CSV and Markdown formats"""
    
    def __init__(self, output_dir: str = "backtest_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "csv").mkdir(exist_ok=True)
        (self.output_dir / "markdown").mkdir(exist_ok=True)
        (self.output_dir / "charts").mkdir(exist_ok=True)
    
    def export_results(self, results: Dict[str, BacktestResult], 
                      symbols: List[str], 
                      start_date: str, 
                      end_date: str):
        """Export all backtest results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export summary
        self._export_summary_table(results, timestamp)
        
        # Export detailed results for each strategy
        for strategy_name, result in results.items():
            self._export_strategy_results(strategy_name, result, timestamp)
        
        # Export combined comparison
        self._export_comparison_table(results, symbols, start_date, end_date, timestamp)
        
        # Export trade details
        self._export_trade_details(results, timestamp)
        
        print(f"Results exported to: {self.output_dir}")
    
    def _export_summary_table(self, results: Dict[str, BacktestResult], timestamp: str):
        """Export summary table of all strategies"""
        
        summary_data = []
        
        for strategy_name, result in results.items():
            summary_data.append({
                'Strategy': strategy_name,
                'Initial Capital': f"${result.initial_capital:,.2f}",
                'Final Capital': f"${result.final_capital:,.2f}",
                'Total Return': f"${result.total_return:,.2f}",
                'Total Return %': f"{result.total_return_pct:.2f}%",
                'Max Drawdown': f"{result.max_drawdown_pct:.2f}%",
                'Sharpe Ratio': f"{result.sharpe_ratio:.3f}",
                'Total Trades': result.total_trades,
                'Win Rate': f"{result.win_rate:.1%}",
                'Profit Factor': f"{result.profit_factor:.2f}",
                'Avg Win': f"${result.avg_win:.2f}",
                'Avg Loss': f"${result.avg_loss:.2f}"
            })
        
        # Export to CSV
        summary_df = pd.DataFrame(summary_data)
        csv_path = self.output_dir / "csv" / f"summary_{timestamp}.csv"
        summary_df.to_csv(csv_path, index=False)
        
        # Export to Markdown
        markdown_path = self.output_dir / "markdown" / f"summary_{timestamp}.md"
        self._dataframe_to_markdown(summary_df, markdown_path, "Backtest Summary Results")
        
        print(f"Summary exported: {csv_path}")
    
    def _export_strategy_results(self, strategy_name: str, result: BacktestResult, timestamp: str):
        """Export detailed results for a single strategy"""
        
        # Strategy performance summary
        performance_data = [{
            'Metric': 'Initial Capital',
            'Value': f"${result.initial_capital:,.2f}"
        }, {
            'Metric': 'Final Capital',
            'Value': f"${result.final_capital:,.2f}"
        }, {
            'Metric': 'Total Return',
            'Value': f"${result.total_return:,.2f}"
        }, {
            'Metric': 'Total Return %',
            'Value': f"{result.total_return_pct:.2f}%"
        }, {
            'Metric': 'Max Drawdown',
            'Value': f"{result.max_drawdown_pct:.2f}%"
        }, {
            'Metric': 'Sharpe Ratio',
            'Value': f"{result.sharpe_ratio:.3f}"
        }, {
            'Metric': 'Total Trades',
            'Value': result.total_trades
        }, {
            'Metric': 'Winning Trades',
            'Value': result.winning_trades
        }, {
            'Metric': 'Losing Trades',
            'Value': result.losing_trades
        }, {
            'Metric': 'Win Rate',
            'Value': f"{result.win_rate:.1%}"
        }, {
            'Metric': 'Profit Factor',
            'Value': f"{result.profit_factor:.2f}"
        }, {
            'Metric': 'Average Win',
            'Value': f"${result.avg_win:.2f}"
        }, {
            'Metric': 'Average Loss',
            'Value': f"${result.avg_loss:.2f}"
        }]
        
        # Export performance summary
        perf_df = pd.DataFrame(performance_data)
        csv_path = self.output_dir / "csv" / f"{strategy_name}_performance_{timestamp}.csv"
        perf_df.to_csv(csv_path, index=False)
        
        markdown_path = self.output_dir / "markdown" / f"{strategy_name}_performance_{timestamp}.md"
        self._dataframe_to_markdown(perf_df, markdown_path, f"{strategy_name.title()} Strategy Performance")
        
        # Export equity curve
        if not result.equity_curve.empty:
            equity_df = result.equity_curve.reset_index()
            equity_df.columns = ['Date', 'Portfolio Value']
            equity_csv_path = self.output_dir / "csv" / f"{strategy_name}_equity_curve_{timestamp}.csv"
            equity_df.to_csv(equity_csv_path, index=False)
        
        print(f"Strategy results exported: {csv_path}")
    
    def _export_comparison_table(self, results: Dict[str, BacktestResult], 
                                symbols: List[str], 
                                start_date: str, 
                                end_date: str, 
                                timestamp: str):
        """Export comparison table of all strategies"""
        
        comparison_data = []
        
        for strategy_name, result in results.items():
            comparison_data.append({
                'Strategy': strategy_name,
                'Start Date': result.start_date.strftime('%Y-%m-%d'),
                'End Date': result.end_date.strftime('%Y-%m-%d'),
                'Symbols': ', '.join(symbols),
                'Initial Capital': result.initial_capital,
                'Final Capital': result.final_capital,
                'Total Return': result.total_return,
                'Total Return %': result.total_return_pct,
                'Max Drawdown %': result.max_drawdown_pct,
                'Sharpe Ratio': result.sharpe_ratio,
                'Total Trades': result.total_trades,
                'Win Rate %': result.win_rate * 100,
                'Profit Factor': result.profit_factor,
                'Avg Win': result.avg_win,
                'Avg Loss': result.avg_loss
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Export to CSV
        csv_path = self.output_dir / "csv" / f"comparison_{timestamp}.csv"
        comparison_df.to_csv(csv_path, index=False)
        
        # Export to Markdown
        markdown_path = self.output_dir / "markdown" / f"comparison_{timestamp}.md"
        self._dataframe_to_markdown(comparison_df, markdown_path, "Strategy Comparison Results")
        
        print(f"Comparison exported: {csv_path}")
    
    def _export_trade_details(self, results: Dict[str, BacktestResult], timestamp: str):
        """Export detailed trade information for each strategy"""
        
        for strategy_name, result in results.items():
            if not result.trades:
                continue
            
            # Convert trades to DataFrame
            trades_data = []
            for trade in result.trades:
                trades_data.append({
                    'Date': trade.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'Symbol': trade.symbol,
                    'Action': trade.action,
                    'Quantity': trade.quantity,
                    'Price': trade.price,
                    'Value': trade.quantity * trade.price,
                    'Strategy': trade.strategy,
                    'Confidence': trade.confidence,
                    'Portfolio Value': trade.portfolio_value,
                    'Cash': trade.cash,
                    'Position Value': trade.position_value,
                    'Total P&L': trade.total_pnl,
                    'Trade P&L': trade.trade_pnl
                })
            
            trades_df = pd.DataFrame(trades_data)
            
            # Export to CSV
            csv_path = self.output_dir / "csv" / f"{strategy_name}_trades_{timestamp}.csv"
            trades_df.to_csv(csv_path, index=False)
            
            # Export to Markdown (first 50 trades for readability)
            markdown_path = self.output_dir / "markdown" / f"{strategy_name}_trades_{timestamp}.md"
            self._dataframe_to_markdown(
                trades_df.head(50), 
                markdown_path, 
                f"{strategy_name.title()} Strategy - Recent Trades (First 50)"
            )
            
            print(f"Trade details exported: {csv_path}")
    
    def _dataframe_to_markdown(self, df: pd.DataFrame, filepath: Path, title: str):
        """Convert DataFrame to Markdown table and save to file"""
        
        with open(filepath, 'w') as f:
            f.write(f"# {title}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Convert DataFrame to markdown table
            markdown_table = df.to_markdown(index=False, tablefmt="grid")
            f.write(markdown_table)
            
            f.write(f"\n\n*Total rows: {len(df)}*")
    
    def generate_summary_report(self, results: Dict[str, BacktestResult], 
                               symbols: List[str], 
                               start_date: str, 
                               end_date: str) -> str:
        """Generate a comprehensive summary report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / "markdown" / f"backtest_report_{timestamp}.md"
        
        with open(report_path, 'w') as f:
            f.write("# Algorithmic Trading Backtest Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Test Period:** {start_date} to {end_date}\n\n")
            f.write(f"**Symbols Tested:** {', '.join(symbols)}\n\n")
            f.write(f"**Strategies Tested:** {', '.join(results.keys())}\n\n")
            
            f.write("## Executive Summary\n\n")
            
            # Find best performing strategy
            best_strategy = max(results.items(), key=lambda x: x[1].total_return_pct)
            worst_strategy = min(results.items(), key=lambda x: x[1].total_return_pct)
            
            f.write(f"- **Best Strategy:** {best_strategy[0]} ({best_strategy[1].total_return_pct:.2f}% return)\n")
            f.write(f"- **Worst Strategy:** {worst_strategy[0]} ({worst_strategy[1].total_return_pct:.2f}% return)\n")
            f.write(f"- **Total Strategies Tested:** {len(results)}\n\n")
            
            f.write("## Strategy Performance Comparison\n\n")
            
            # Create performance comparison table
            perf_data = []
            for strategy_name, result in results.items():
                perf_data.append({
                    'Strategy': strategy_name,
                    'Return %': f"{result.total_return_pct:.2f}%",
                    'Max DD %': f"{result.max_drawdown_pct:.2f}%",
                    'Sharpe': f"{result.sharpe_ratio:.3f}",
                    'Trades': result.total_trades,
                    'Win Rate': f"{result.win_rate:.1%}",
                    'Profit Factor': f"{result.profit_factor:.2f}"
                })
            
            perf_df = pd.DataFrame(perf_data)
            f.write(perf_df.to_markdown(index=False, tablefmt="grid"))
            f.write("\n\n")
            
            f.write("## Detailed Analysis\n\n")
            
            for strategy_name, result in results.items():
                f.write(f"### {strategy_name.title()} Strategy\n\n")
                f.write(f"- **Total Return:** {result.total_return_pct:.2f}% (${result.total_return:,.2f})\n")
                f.write(f"- **Max Drawdown:** {result.max_drawdown_pct:.2f}%\n")
                f.write(f"- **Sharpe Ratio:** {result.sharpe_ratio:.3f}\n")
                f.write(f"- **Total Trades:** {result.total_trades}\n")
                f.write(f"- **Win Rate:** {result.win_rate:.1%}\n")
                f.write(f"- **Profit Factor:** {result.profit_factor:.2f}\n\n")
            
            f.write("## Recommendations\n\n")
            
            # Generate recommendations based on results
            profitable_strategies = [name for name, result in results.items() if result.total_return_pct > 0]
            
            if profitable_strategies:
                f.write(f"- **Profitable Strategies:** {', '.join(profitable_strategies)}\n")
                f.write("- Consider implementing these strategies in live trading\n")
            else:
                f.write("- No strategies showed positive returns in this period\n")
                f.write("- Consider adjusting strategy parameters or testing different time periods\n")
            
            f.write(f"\n- **Best Risk-Adjusted Return:** {best_strategy[0]} (Sharpe: {best_strategy[1].sharpe_ratio:.3f})\n")
            f.write(f"- **Most Active:** {max(results.items(), key=lambda x: x[1].total_trades)[0]} ({max(results.items(), key=lambda x: x[1].total_trades)[1].total_trades} trades)\n")
        
        print(f"Summary report generated: {report_path}")
        return str(report_path) 