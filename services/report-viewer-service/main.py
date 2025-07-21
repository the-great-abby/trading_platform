"""
Report Viewer Service - Browse and view backtest reports
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import json
import httpx
from datetime import datetime, timedelta
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Report Viewer Service", version="1.0.0")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot")

class ReportViewerService:
    """Service for retrieving backtest reports from database"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_recent_backtests(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent backtest runs"""
        try:
            with self.SessionLocal() as session:
                result = session.execute(text("""
                    SELECT 
                        run_id,
                        strategy_name,
                        backtest_name,
                        symbols,
                        start_date,
                        end_date,
                        initial_capital,
                        final_capital,
                        total_return_pct,
                        sharpe_ratio,
                        max_drawdown_pct,
                        total_trades,
                        win_rate,
                        created_at,
                        completed_at
                    FROM backtest_runs 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """), {"limit": limit})
                
                backtests = []
                for row in result:
                    backtests.append({
                        'run_id': row.run_id,
                        'strategy_name': row.strategy_name,
                        'backtest_name': row.backtest_name,
                        'symbols': json.loads(row.symbols) if row.symbols else [],
                        'start_date': row.start_date.isoformat() if row.start_date else None,
                        'end_date': row.end_date.isoformat() if row.end_date else None,
                        'initial_capital': row.initial_capital,
                        'final_capital': row.final_capital,
                        'total_return_pct': row.total_return_pct,
                        'sharpe_ratio': row.sharpe_ratio,
                        'max_drawdown_pct': row.max_drawdown_pct,
                        'total_trades': row.total_trades,
                        'win_rate': row.win_rate,
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'completed_at': row.completed_at.isoformat() if row.completed_at else None
                    })
                
                return backtests
                
        except Exception as e:
            logger.error(f"Error getting recent backtests: {e}")
            return []
    
    def get_backtest_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed backtest information"""
        try:
            with self.SessionLocal() as session:
                # Get backtest run details
                result = session.execute(text("""
                    SELECT 
                        run_id,
                        strategy_name,
                        backtest_name,
                        symbols,
                        start_date,
                        end_date,
                        initial_capital,
                        final_capital,
                        total_return,
                        total_return_pct,
                        max_drawdown_pct,
                        sharpe_ratio,
                        total_trades,
                        winning_trades,
                        losing_trades,
                        win_rate,
                        profit_factor,
                        avg_win,
                        avg_loss,
                        database_only,
                        data_provider,
                        created_at,
                        completed_at
                    FROM backtest_runs 
                    WHERE run_id = :run_id
                """), {"run_id": run_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                # Get trades for this run
                trades_result = session.execute(text("""
                    SELECT 
                        timestamp,
                        symbol,
                        action,
                        quantity,
                        price,
                        value,
                        pnl,
                        confidence,
                        portfolio_value,
                        cash,
                        position_value,
                        total_pnl,
                        trade_pnl
                    FROM backtest_trades 
                    WHERE run_id = :run_id
                    ORDER BY timestamp
                """), {"run_id": run_id})
                
                trades = []
                for trade_row in trades_result:
                    trades.append({
                        'timestamp': trade_row.timestamp.isoformat() if trade_row.timestamp else None,
                        'symbol': trade_row.symbol,
                        'action': trade_row.action,
                        'quantity': trade_row.quantity,
                        'price': trade_row.price,
                        'value': trade_row.value,
                        'pnl': trade_row.pnl,
                        'confidence': trade_row.confidence,
                        'portfolio_value': trade_row.portfolio_value,
                        'cash': trade_row.cash,
                        'position_value': trade_row.position_value,
                        'total_pnl': trade_row.total_pnl,
                        'trade_pnl': trade_row.trade_pnl
                    })
                
                # Get equity curve data
                equity_result = session.execute(text("""
                    SELECT 
                        date,
                        portfolio_value,
                        cash,
                        positions_value,
                        total_pnl
                    FROM backtest_equity_curves 
                    WHERE run_id = :run_id
                    ORDER BY date
                """), {"run_id": run_id})
                
                equity_curve = []
                for equity_row in equity_result:
                    equity_curve.append({
                        'date': equity_row.date.isoformat() if equity_row.date else None,
                        'portfolio_value': equity_row.portfolio_value,
                        'cash': equity_row.cash,
                        'positions_value': equity_row.positions_value,
                        'total_pnl': equity_row.total_pnl
                    })
                
                return {
                    'run_id': row.run_id,
                    'strategy_name': row.strategy_name,
                    'backtest_name': row.backtest_name,
                    'symbols': json.loads(row.symbols) if row.symbols else [],
                    'start_date': row.start_date.isoformat() if row.start_date else None,
                    'end_date': row.end_date.isoformat() if row.end_date else None,
                    'initial_capital': row.initial_capital,
                    'final_capital': row.final_capital,
                    'total_return': row.total_return,
                    'total_return_pct': row.total_return_pct,
                    'max_drawdown_pct': row.max_drawdown_pct,
                    'sharpe_ratio': row.sharpe_ratio,
                    'total_trades': row.total_trades,
                    'winning_trades': row.winning_trades,
                    'losing_trades': row.losing_trades,
                    'win_rate': row.win_rate,
                    'profit_factor': row.profit_factor,
                    'avg_win': row.avg_win,
                    'avg_loss': row.avg_loss,
                    'database_only': row.database_only == 'true',
                    'data_provider': row.data_provider,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'completed_at': row.completed_at.isoformat() if row.completed_at else None,
                    'trades': trades,
                    'equity_curve': equity_curve
                }
                
        except Exception as e:
            logger.error(f"Error getting backtest details: {e}")
            return None

# Initialize service
report_service = ReportViewerService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "report-viewer-service"}

@app.get("/", response_class=HTMLResponse)
async def report_dashboard():
    """Main report dashboard"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Backtest Reports Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: #667eea;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.8;
        }
        
        .nav-buttons {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .nav-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .nav-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .report-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .report-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .report-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .strategy-name {
            font-weight: 600;
            color: #667eea;
            font-size: 1.1em;
        }
        
        .performance-indicator {
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .positive {
            background: #d4edda;
            color: #155724;
        }
        
        .negative {
            background: #f8d7da;
            color: #721c24;
        }
        
        .neutral {
            background: #e2e3e5;
            color: #383d41;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .metric {
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 2px;
        }
        
        .metric-label {
            font-size: 0.8em;
            color: #666;
        }
        
        .report-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
            color: #666;
        }
        
        .view-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }
        
        .view-btn:hover {
            background: #5a6fd8;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .error {
            text-align: center;
            padding: 40px;
            color: #dc3545;
        }
        
        @media (max-width: 768px) {
            .reports-grid {
                grid-template-columns: 1fr;
            }
            
            .nav-buttons {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Backtest Reports</h1>
            <p>View and analyze your trading strategy backtest results</p>
        </div>
        
        <div class="nav-buttons">
            <a href="http://localhost:11031/" class="nav-btn">🚀 Run New Backtest</a>
            <a href="http://localhost:11000/dashboard" class="nav-btn">📈 Performance Dashboard</a>
            <a href="http://localhost:11002/dashboard" class="nav-btn">📧 Test Email Notifications</a>
        </div>
        
        <div id="reports-container">
            <div class="loading">Loading reports...</div>
        </div>
    </div>
    
    <script>
        async function loadReports() {
            try {
                const response = await fetch('/api/reports');
                const reports = await response.json();
                
                const container = document.getElementById('reports-container');
                
                if (reports.length === 0) {
                    container.innerHTML = '<div class="error">No backtest reports found. Run your first backtest to see results here!</div>';
                    return;
                }
                
                container.innerHTML = '<div class="reports-grid"></div>';
                const grid = container.querySelector('.reports-grid');
                
                reports.forEach(report => {
                    const card = createReportCard(report);
                    grid.appendChild(card);
                });
                
            } catch (error) {
                document.getElementById('reports-container').innerHTML = 
                    '<div class="error">Error loading reports: ' + error.message + '</div>';
            }
        }
        
        function createReportCard(report) {
            const card = document.createElement('div');
            card.className = 'report-card';
            
            const performanceClass = report.total_return_pct >= 0 ? 'positive' : 'negative';
            const performanceText = report.total_return_pct >= 0 ? '+' : '';
            
            card.innerHTML = `
                <div class="report-header">
                    <div class="strategy-name">${report.strategy_name}</div>
                    <div class="performance-indicator ${performanceClass}">
                        ${performanceText}${report.total_return_pct.toFixed(2)}%
                    </div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric">
                        <div class="metric-value">${report.sharpe_ratio.toFixed(2)}</div>
                        <div class="metric-label">Sharpe Ratio</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${report.max_drawdown_pct.toFixed(2)}%</div>
                        <div class="metric-label">Max Drawdown</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${report.total_trades}</div>
                        <div class="metric-label">Total Trades</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${(report.win_rate * 100).toFixed(1)}%</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                </div>
                
                <div class="report-footer">
                    <div>
                        <div>${report.symbols.join(', ')}</div>
                        <div>${report.start_date} to ${report.end_date}</div>
                    </div>
                    <button class="view-btn" onclick="viewReport('${report.run_id}')">View Details</button>
                </div>
            `;
            
            return card;
        }
        
        function viewReport(runId) {
            window.open(`/report/${runId}`, '_blank');
        }
        
        // Load reports when page loads
        loadReports();
    </script>
</body>
</html>
"""

@app.get("/api/reports")
async def get_reports():
    """Get recent backtest reports"""
    reports = report_service.get_recent_backtests(limit=50)
    return reports

@app.get("/report/{run_id}", response_class=HTMLResponse)
async def view_report(run_id: str):
    """View detailed backtest report"""
    report = report_service.get_backtest_details(run_id)
    
    if not report:
        return """
        <html>
        <head><title>Report Not Found</title></head>
        <body>
            <h1>Report Not Found</h1>
            <p>The requested backtest report could not be found.</p>
            <a href="/">← Back to Dashboard</a>
        </body>
        </html>
        """
    
    # Create detailed report HTML
    performance_class = "positive" if report['total_return_pct'] >= 0 else "negative"
    performance_sign = "+" if report['total_return_pct'] >= 0 else ""
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {report['strategy_name']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            color: #667eea;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .performance-summary {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .performance-indicator {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .trades-section {{
            margin-top: 30px;
        }}
        
        .trades-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .trades-table th,
        .trades-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        
        .trades-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        
        .back-btn {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            margin-bottom: 20px;
        }}
        
        .back-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-btn">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📊 {report['strategy_name']} Backtest Report</h1>
            <p>Run ID: {report['run_id']}</p>
        </div>
        
        <div class="performance-summary">
            <div class="performance-indicator {performance_class}">
                {performance_sign}{report['total_return_pct']:.2f}%
            </div>
            <p>Total Return</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">${report['initial_capital']:,.2f}</div>
                <div class="metric-label">Initial Capital</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${report['final_capital']:,.2f}</div>
                <div class="metric-label">Final Capital</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['sharpe_ratio']:.2f}</div>
                <div class="metric-label">Sharpe Ratio</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['max_drawdown_pct']:.2f}%</div>
                <div class="metric-label">Max Drawdown</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['total_trades']}</div>
                <div class="metric-label">Total Trades</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{(report['win_rate'] * 100):.1f}%</div>
                <div class="metric-label">Win Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['profit_factor']:.2f}</div>
                <div class="metric-label">Profit Factor</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${report['avg_win']:,.2f}</div>
                <div class="metric-label">Avg Win</div>
            </div>
        </div>
        
        <div class="trades-section">
            <h2>📈 Trade History</h2>
            <table class="trades-table">
                <thead>
                    <tr>
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
                    {''.join([f'''
                    <tr>
                        <td>{trade['timestamp'][:10] if trade['timestamp'] else 'N/A'}</td>
                        <td>{trade['symbol']}</td>
                        <td>{trade['action']}</td>
                        <td>{trade['quantity']}</td>
                        <td>${trade['price']:.2f}</td>
                        <td>${trade['value']:,.2f}</td>
                        <td style="color: {'green' if trade['pnl'] >= 0 else 'red'}">${trade['pnl']:,.2f}</td>
                        <td>{(trade['confidence'] * 100):.1f}%</td>
                    </tr>
                    ''' for trade in report['trades'][:50]])}
                </tbody>
            </table>
            {f'<p style="text-align: center; margin-top: 20px; color: #666;">Showing first 50 trades of {len(report["trades"])} total trades</p>' if len(report['trades']) > 50 else ''}
        </div>
    </div>
</body>
</html>
"""

@app.get("/api/report/{run_id}")
async def get_report_json(run_id: str):
    """Get backtest report as JSON"""
    report = report_service.get_backtest_details(run_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8084) 