"""
HTML Report Generator for Backtest Results
Generates MetaTrader-style HTML reports with comprehensive metrics and charts
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

from .backtest_engine import BacktestResult, BacktestTrade


class HTMLReportGenerator:
    """Generate comprehensive HTML reports for backtest results"""
    
    def __init__(self, output_dir: str = "backtest_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "html").mkdir(exist_ok=True)
        (self.output_dir / "charts").mkdir(exist_ok=True)
        (self.output_dir / "assets").mkdir(exist_ok=True)
        
        # CSS styles for MetaTrader-like appearance
        self.css_styles = """
        <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header .subtitle {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 40px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            overflow: hidden;
        }
        .section-header {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
            font-weight: 600;
            font-size: 1.2em;
            color: #2c3e50;
        }
        .section-content {
            padding: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
        .neutral { color: #3498db; }
        .table-container {
            overflow-x: auto;
            margin: 20px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .chart-container {
            margin: 20px 0;
            text-align: center;
        }
        .strategy-comparison {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .strategy-card {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            background: white;
        }
        .strategy-name {
            font-size: 1.3em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 15px;
            text-align: center;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }
        .tabs {
            display: flex;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            color: #666;
            font-weight: 500;
        }
        .tab.active {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        </style>
        """
        
        # JavaScript for interactivity
        self.js_script = """
        <script>
        function showTab(tabName) {
            // Hide all tab contents
            var tabContents = document.getElementsByClassName('tab-content');
            for (var i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove('active');
            }
            
            // Remove active class from all tabs
            var tabs = document.getElementsByClassName('tab');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            
            // Show the selected tab content and mark tab as active
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        // Initialize first tab as active
        document.addEventListener('DOMContentLoaded', function() {
            var firstTab = document.querySelector('.tab');
            if (firstTab) {
                firstTab.classList.add('active');
                var firstTabContent = document.querySelector('.tab-content');
                if (firstTabContent) {
                    firstTabContent.classList.add('active');
                }
            }
        });
        </script>
        """
    
    def generate_report(self, results: Dict[str, BacktestResult], 
                       symbols: List[str], 
                       start_date: str, 
                       end_date: str,
                       report_title: Optional[str] = None) -> str:
        """Generate a comprehensive HTML report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"backtest_report_{timestamp}.html"
        report_path = self.output_dir / "html" / report_filename
        
        if report_title is None:
            report_title = f"Algorithmic Trading Backtest Report"
        
        # Generate charts
        charts_html = self._generate_charts(results, symbols, start_date, end_date)
        
        # Generate HTML content
        html_content = self._generate_html_content(
            results, symbols, start_date, end_date, report_title, charts_html
        )
        
        # Write HTML file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {report_path}")
        return str(report_path)
    
    def _generate_html_content(self, results: Dict[str, BacktestResult], 
                              symbols: List[str], 
                              start_date: str, 
                              end_date: str,
                              report_title: str,
                              charts_html: str) -> str:
        """Generate the main HTML content"""
        
        # Calculate summary statistics
        total_strategies = len(results)
        best_strategy = max(results.items(), key=lambda x: x[1].total_return_pct)
        worst_strategy = min(results.items(), key=lambda x: x[1].total_return_pct)
        
        # Generate metrics cards
        metrics_html = self._generate_metrics_cards(results)
        
        # Generate strategy comparison table
        comparison_table = self._generate_comparison_table(results)
        
        # Generate trade details table
        trade_details = self._generate_trade_details(results)
        
        # Generate monthly analysis
        monthly_analysis = self._generate_monthly_analysis(results)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{report_title}</title>
            {self.css_styles}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{report_title}</h1>
                    <div class="subtitle">
                        Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                    </div>
                </div>
                
                <div class="content">
                    <!-- Summary Section -->
                    <div class="section">
                        <div class="section-header">Test Summary</div>
                        <div class="section-content">
                            <div class="metrics-grid">
                                <div class="metric-card">
                                    <div class="metric-value neutral">{total_strategies}</div>
                                    <div class="metric-label">Strategies Tested</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value neutral">{', '.join(symbols)}</div>
                                    <div class="metric-label">Symbols</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value neutral">{start_date} to {end_date}</div>
                                    <div class="metric-label">Test Period</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value positive">{best_strategy[1].total_return_pct:.2f}%</div>
                                    <div class="metric-label">Best Return</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Performance Metrics -->
                    <div class="section">
                        <div class="section-header">Performance Metrics</div>
                        <div class="section-content">
                            {metrics_html}
                        </div>
                    </div>
                    
                    <!-- Charts Section -->
                    <div class="section">
                        <div class="section-header">Performance Charts</div>
                        <div class="section-content">
                            {charts_html}
                        </div>
                    </div>
                    
                    <!-- Strategy Comparison -->
                    <div class="section">
                        <div class="section-header">Strategy Comparison</div>
                        <div class="section-content">
                            <div class="tabs">
                                <button class="tab" onclick="showTab('comparison-tab')">Summary</button>
                                <button class="tab" onclick="showTab('trades-tab')">Trade Details</button>
                                <button class="tab" onclick="showTab('monthly-tab')">Monthly Analysis</button>
                            </div>
                            
                            <div id="comparison-tab" class="tab-content">
                                {comparison_table}
                            </div>
                            
                            <div id="trades-tab" class="tab-content">
                                {trade_details}
                            </div>
                            
                            <div id="monthly-tab" class="tab-content">
                                {monthly_analysis}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Report generated by Algorithmic Trading System</p>
                    <p>This report is for informational purposes only. Past performance does not guarantee future results.</p>
                </div>
            </div>
            {self.js_script}
        </body>
        </html>
        """
        
        return html
    
    def _generate_metrics_cards(self, results: Dict[str, BacktestResult]) -> str:
        """Generate metrics cards for all strategies"""
        
        cards_html = '<div class="strategy-comparison">'
        
        for strategy_name, result in results.items():
            # Determine color classes
            return_class = "positive" if result.total_return_pct > 0 else "negative"
            drawdown_class = "negative" if result.max_drawdown_pct > 20 else "neutral"
            sharpe_class = "positive" if result.sharpe_ratio > 1 else "neutral"
            
            cards_html += f"""
            <div class="strategy-card">
                <div class="strategy-name">{strategy_name}</div>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value {return_class}">{result.total_return_pct:.2f}%</div>
                        <div class="metric-label">Total Return</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {drawdown_class}">{result.max_drawdown_pct:.2f}%</div>
                        <div class="metric-label">Max Drawdown</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {sharpe_class}">{result.sharpe_ratio:.3f}</div>
                        <div class="metric-label">Sharpe Ratio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{result.total_trades}</div>
                        <div class="metric-label">Total Trades</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{result.win_rate:.1%}</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{result.profit_factor:.2f}</div>
                        <div class="metric-label">Profit Factor</div>
                    </div>
                </div>
            </div>
            """
        
        cards_html += '</div>'
        return cards_html
    
    def _generate_comparison_table(self, results: Dict[str, BacktestResult]) -> str:
        """Generate strategy comparison table"""
        
        table_html = """
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Strategy</th>
                        <th>Total Return %</th>
                        <th>Max Drawdown %</th>
                        <th>Sharpe Ratio</th>
                        <th>Total Trades</th>
                        <th>Win Rate</th>
                        <th>Profit Factor</th>
                        <th>Avg Win</th>
                        <th>Avg Loss</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for strategy_name, result in results.items():
            return_class = "positive" if result.total_return_pct > 0 else "negative"
            table_html += f"""
                <tr>
                    <td><strong>{strategy_name}</strong></td>
                    <td class="{return_class}">{result.total_return_pct:.2f}%</td>
                    <td>{result.max_drawdown_pct:.2f}%</td>
                    <td>{result.sharpe_ratio:.3f}</td>
                    <td>{result.total_trades}</td>
                    <td>{result.win_rate:.1%}</td>
                    <td>{result.profit_factor:.2f}</td>
                    <td>${result.avg_win:.2f}</td>
                    <td>${result.avg_loss:.2f}</td>
                </tr>
            """
        
        table_html += """
                </tbody>
            </table>
        </div>
        """
        
        return table_html
    
    def _generate_trade_details(self, results: Dict[str, BacktestResult]) -> str:
        """Generate trade details table"""
        
        table_html = """
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Strategy</th>
                        <th>Date</th>
                        <th>Symbol</th>
                        <th>Action</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Value</th>
                        <th>P&L</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Show last 20 trades for each strategy
        for strategy_name, result in results.items():
            for trade in result.trades[-20:]:  # Last 20 trades
                pnl_class = "positive" if trade.pnl > 0 else "negative"
                table_html += f"""
                <tr>
                    <td><strong>{strategy_name}</strong></td>
                    <td>{trade.timestamp.strftime('%Y-%m-%d %H:%M')}</td>
                    <td>{trade.symbol}</td>
                    <td>{trade.action}</td>
                    <td>{trade.quantity}</td>
                    <td>${trade.price:.2f}</td>
                    <td>${trade.quantity * trade.price:.2f}</td>
                    <td class="{pnl_class}">${trade.pnl:.2f}</td>
                    <td>{trade.confidence:.2f}</td>
                </tr>
                """
        
        table_html += """
                </tbody>
            </table>
        </div>
        """
        
        return table_html
    
    def _generate_monthly_analysis(self, results: Dict[str, BacktestResult]) -> str:
        """Generate monthly performance analysis"""
        
        # This is a placeholder - you can implement monthly analysis logic here
        table_html = """
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Strategy</th>
                        <th>Best Month</th>
                        <th>Worst Month</th>
                        <th>Avg Monthly Return</th>
                        <th>Months Profitable</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for strategy_name, result in results.items():
            # Placeholder data - you can calculate actual monthly stats
            table_html += f"""
                <tr>
                    <td><strong>{strategy_name}</strong></td>
                    <td>N/A</td>
                    <td>N/A</td>
                    <td>{result.total_return_pct / 12:.2f}%</td>
                    <td>N/A</td>
                </tr>
            """
        
        table_html += """
                </tbody>
            </table>
        </div>
        """
        
        return table_html
    
    def _generate_charts(self, results: Dict[str, BacktestResult], 
                        symbols: List[str], 
                        start_date: str, 
                        end_date: str) -> str:
        """Generate interactive charts using Plotly"""
        
        charts_html = ""
        
        # 1. Equity Curve Chart
        if any(not result.equity_curve.empty for result in results.values()):
            fig = go.Figure()
            
            for strategy_name, result in results.items():
                if not result.equity_curve.empty:
                    fig.add_trace(go.Scatter(
                        x=result.equity_curve.index,
                        y=result.equity_curve['portfolio_value'],
                        mode='lines',
                        name=strategy_name,
                        line=dict(width=2)
                    ))
            
            fig.update_layout(
                title="Portfolio Value Over Time",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                height=400,
                showlegend=True
            )
            
            charts_html += f'<div class="chart-container">{fig.to_html(full_html=False)}</div>'
        
        # 2. Performance Comparison Chart
        strategies = list(results.keys())
        returns = [results[s].total_return_pct for s in strategies]
        drawdowns = [results[s].max_drawdown_pct for s in strategies]
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Total Return (%)', 'Max Drawdown (%)'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        fig.add_trace(
            go.Bar(x=strategies, y=returns, name="Return %", marker_color='green'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=strategies, y=drawdowns, name="Drawdown %", marker_color='red'),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=False)
        charts_html += f'<div class="chart-container">{fig.to_html(full_html=False)}</div>'
        
        # 3. Risk-Return Scatter Plot
        fig = go.Figure()
        
        for strategy_name, result in results.items():
            fig.add_trace(go.Scatter(
                x=[result.max_drawdown_pct],
                y=[result.total_return_pct],
                mode='markers+text',
                text=[strategy_name],
                textposition="top center",
                marker=dict(size=15, color='blue'),
                name=strategy_name
            ))
        
        fig.update_layout(
            title="Risk-Return Analysis",
            xaxis_title="Max Drawdown (%)",
            yaxis_title="Total Return (%)",
            height=400
        )
        
        charts_html += f'<div class="chart-container">{fig.to_html(full_html=False)}</div>'
        
        return charts_html
    
    def generate_single_strategy_report(self, strategy_name: str, 
                                      result: BacktestResult,
                                      symbols: List[str],
                                      start_date: str,
                                      end_date: str) -> str:
        """Generate a detailed report for a single strategy"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{strategy_name}_report_{timestamp}.html"
        report_path = self.output_dir / "html" / report_filename
        
        # Generate detailed charts for single strategy
        charts_html = self._generate_single_strategy_charts(strategy_name, result)
        
        # Generate detailed metrics
        metrics_html = self._generate_detailed_metrics(result)
        
        # Generate trade analysis
        trade_analysis = self._generate_trade_analysis(result)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{strategy_name} - Detailed Backtest Report</title>
            {self.css_styles}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{strategy_name} Strategy Report</h1>
                    <div class="subtitle">
                        Detailed Analysis | {start_date} to {end_date} | {', '.join(symbols)}
                    </div>
                </div>
                
                <div class="content">
                    {metrics_html}
                    {charts_html}
                    {trade_analysis}
                </div>
                
                <div class="footer">
                    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Single strategy report generated: {report_path}")
        return str(report_path)
    
    def _generate_detailed_metrics(self, result: BacktestResult) -> str:
        """Generate detailed metrics for a single strategy"""
        
        return f"""
        <div class="section">
            <div class="section-header">Detailed Performance Metrics</div>
            <div class="section-content">
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value neutral">${result.initial_capital:,.2f}</div>
                        <div class="metric-label">Initial Capital</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">${result.final_capital:,.2f}</div>
                        <div class="metric-label">Final Capital</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value positive">${result.total_return:,.2f}</div>
                        <div class="metric-label">Total Return</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value positive">{result.total_return_pct:.2f}%</div>
                        <div class="metric-label">Return %</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value negative">{result.max_drawdown_pct:.2f}%</div>
                        <div class="metric-label">Max Drawdown</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{result.sharpe_ratio:.3f}</div>
                        <div class="metric-label">Sharpe Ratio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card">
                            <div class="metric-value neutral">{result.total_trades}</div>
                            <div class="metric-label">Total Trades</div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{result.winning_trades}</div>
                        <div class="metric-label">Winning Trades</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{result.losing_trades}</div>
                        <div class="metric-label">Losing Trades</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{result.win_rate:.1%}</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{result.profit_factor:.2f}</div>
                        <div class="metric-label">Profit Factor</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value positive">${result.avg_win:.2f}</div>
                        <div class="metric-label">Average Win</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value negative">${result.avg_loss:.2f}</div>
                        <div class="metric-label">Average Loss</div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_single_strategy_charts(self, strategy_name: str, result: BacktestResult) -> str:
        """Generate charts for a single strategy"""
        
        charts_html = ""
        
        # Equity curve
        if not result.equity_curve.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=result.equity_curve.index,
                y=result.equity_curve['portfolio_value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='blue', width=2)
            ))
            
            fig.update_layout(
                title=f"{strategy_name} - Portfolio Value Over Time",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                height=400
            )
            
            charts_html += f'<div class="chart-container">{fig.to_html(full_html=False)}</div>'
        
        # Trade P&L distribution
        if result.trades:
            pnl_values = [trade.pnl for trade in result.trades]
            fig = go.Figure(data=[go.Histogram(x=pnl_values, nbinsx=20)])
            fig.update_layout(
                title=f"{strategy_name} - Trade P&L Distribution",
                xaxis_title="P&L ($)",
                yaxis_title="Frequency",
                height=400
            )
            charts_html += f'<div class="chart-container">{fig.to_html(full_html=False)}</div>'
        
        return charts_html
    
    def _generate_trade_analysis(self, result: BacktestResult) -> str:
        """Generate detailed trade analysis"""
        
        if not result.trades:
            return "<div class='section'><div class='section-content'>No trades found.</div></div>"
        
        # Calculate additional metrics
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        current_wins = 0
        current_losses = 0
        
        for trade in result.trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        return f"""
        <div class="section">
            <div class="section-header">Trade Analysis</div>
            <div class="section-content">
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value neutral">{max_consecutive_wins}</div>
                        <div class="metric-label">Max Consecutive Wins</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{max_consecutive_losses}</div>
                        <div class="metric-label">Max Consecutive Losses</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{len([t for t in result.trades if t.pnl > 0])}</div>
                        <div class="metric-label">Profitable Trades</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">{len([t for t in result.trades if t.pnl < 0])}</div>
                        <div class="metric-label">Losing Trades</div>
                    </div>
                </div>
            </div>
        </div>
        """ 