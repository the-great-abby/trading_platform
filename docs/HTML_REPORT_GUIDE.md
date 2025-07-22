# HTML Report Generator Guide

Generate professional MetaTrader-style HTML reports from your backtest results with interactive charts, comprehensive metrics, and beautiful styling.

## Features

- **MetaTrader-style Design**: Professional appearance similar to MetaTrader reports
- **Interactive Charts**: Built with Plotly for zoom, pan, and hover interactions
- **Comprehensive Metrics**: All key performance indicators displayed
- **Strategy Comparison**: Compare multiple strategies side-by-side
- **Trade Analysis**: Detailed trade-by-trade breakdown
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices
- **Export Ready**: Self-contained HTML files that can be shared or printed

## Quick Start

### 1. Generate Sample Reports

First, try the sample report generator to see the HTML reports in action:

```bash
cd examples
python generate_sample_report.py
```

This will create sample reports in the `sample_reports/html/` directory.

### 2. Generate Reports from Your Backtest Data

#### List Available Backtest Runs

```bash
python scripts/generate_html_report.py --list
```

This shows all backtest runs in your database with their performance metrics.

#### Generate Single Strategy Report

```bash
python scripts/generate_html_report.py --run-id backtest_20250101_120000_momentum_strategy
```

#### Generate Comparison Report

```bash
python scripts/generate_html_report.py --run-ids backtest_20250101_120000_momentum backtest_20250101_120000_mean_reversion
```

#### Generate Reports for Latest Runs

```bash
python scripts/generate_html_report.py --latest 5
```

#### Custom Report Title

```bash
python scripts/generate_html_report.py --run-id backtest_20250101_120000_momentum_strategy --title "My Custom Strategy Report"
```

### 3. View Reports via Web Server

#### Option A: Simple HTTP Server (Quick)

```bash
# Navigate to reports directory
cd reports/html

# Start simple HTTP server
python -m http.server 8080

# Open in browser
open http://localhost:8080
```

#### Option B: Dedicated Report Viewer (Recommended)

```bash
# Start the report viewer server
make report-viewer

# Or directly
python scripts/start_report_viewer.py
```

Then open http://localhost:8080 in your browser.

#### Option C: Generate and View in One Command

```bash
# Generate reports and start viewer
make reports
make report-viewer
```

## Report Features

### 1. Executive Summary
- Test period and symbols
- Best and worst performing strategies
- Key performance highlights

### 2. Performance Metrics
- **Return Metrics**: Total return, return percentage, annualized return
- **Risk Metrics**: Maximum drawdown, Sharpe ratio, volatility
- **Trade Metrics**: Total trades, win rate, profit factor
- **Average Metrics**: Average win/loss, largest win/loss

### 3. Interactive Charts
- **Equity Curve**: Portfolio value over time
- **Performance Comparison**: Bar charts comparing strategies
- **Risk-Return Scatter**: Visual risk-return analysis
- **Trade Distribution**: Histogram of trade P&L

### 4. Strategy Comparison
- Side-by-side performance metrics
- Strategy ranking tables
- Detailed trade analysis
- Monthly performance breakdown

### 5. Trade Details
- Complete trade history
- Entry/exit prices and times
- P&L per trade
- Confidence scores

## Report Types

### Single Strategy Report
Detailed analysis of one strategy including:
- Performance metrics cards
- Equity curve chart
- Trade P&L distribution
- Detailed trade analysis
- Risk metrics breakdown

### Comparison Report
Compare multiple strategies with:
- Strategy comparison table
- Performance charts
- Risk-return scatter plot
- Trade analysis by strategy

## Usage Examples

### Python API

```python
from src.services.report_service import ReportService

# Initialize report service
report_service = ReportService(output_dir="my_reports")

# Generate single strategy report
report_path = report_service.generate_report_from_run_id(
    run_id="backtest_20250101_120000_momentum_strategy",
    report_title="My Momentum Strategy Report"
)

# Generate comparison report
comparison_path = report_service.generate_comparison_report(
    run_ids=["backtest_1", "backtest_2", "backtest_3"],
    report_title="Strategy Comparison Report"
)

# Generate reports for latest runs
report_paths = report_service.generate_latest_reports(limit=10)
```

### Direct HTML Generator

```python
from src.backtesting.results.html_report_generator import HTMLReportGenerator

# Initialize generator
generator = HTMLReportGenerator(output_dir="reports")

# Generate report from BacktestResult objects
report_path = generator.generate_report(
    results=my_backtest_results,
    symbols=['AAPL', 'GOOGL', 'MSFT'],
    start_date='2024-01-01',
    end_date='2024-12-31',
    report_title="My Backtest Report"
)
```

## Report Structure

```
reports/
├── html/
│   ├── backtest_report_20250101_120000.html
│   ├── momentum_strategy_report_20250101_120000.html
│   └── comparison_report_20250101_120000.html
└── charts/
    └── (generated chart files)
```

## Web Server Options

### Option 1: Direct File Opening (Simplest)
- Open HTML files directly in any web browser
- No server required
- Works offline
- Perfect for local viewing

### Option 2: Simple HTTP Server (Quick)
```bash
cd reports/html
python -m http.server 8080
# Then open http://localhost:8080
```

### Option 3: Dedicated Report Viewer (Recommended)
```bash
make report-viewer
# Or: python scripts/start_report_viewer.py
```
Features:
- **Web Interface**: Browse and select reports
- **API Endpoints**: Programmatic access to report list
- **Auto-refresh**: Automatically detects new reports
- **Better UX**: Professional interface with report metadata
- **CORS Support**: Can be embedded in other applications

### Option 4: Integration with Existing Services
The report viewer can be integrated into your existing Kubernetes services:

```yaml
# Add to your k8s deployment
- name: report-viewer
  image: your-registry/report-viewer:latest
  ports:
  - containerPort: 8080
  volumeMounts:
  - name: reports-volume
    mountPath: /app/reports
```

## Customization

### Custom CSS Styling

The HTML reports use embedded CSS for styling. You can modify the `css_styles` in `HTMLReportGenerator` to customize:

- Color scheme
- Fonts and typography
- Layout and spacing
- Chart styling
- Mobile responsiveness

### Custom Metrics

Add custom metrics by extending the `BacktestResult` class:

```python
@dataclass
class CustomBacktestResult(BacktestResult):
    custom_metric: float = 0.0
    additional_analysis: Dict = field(default_factory=dict)
```

### Custom Charts

Add custom charts by modifying the `_generate_charts` method:

```python
def _generate_custom_chart(self, results):
    # Create custom chart with Plotly
    fig = go.Figure()
    # ... chart configuration
    return fig.to_html(full_html=False)
```

## Integration with Backtest Engine

The HTML report generator integrates seamlessly with your existing backtest system:

1. **Automatic Storage**: Backtest results are automatically stored in the database
2. **Report Generation**: Generate reports from any stored backtest run
3. **Comparison Analysis**: Compare multiple strategies easily
4. **Historical Analysis**: Access and report on historical backtest data

## Best Practices

### 1. Regular Report Generation
```bash
# Generate reports for latest runs weekly
python scripts/generate_html_report.py --latest 10
```

### 2. Cleanup Old Reports
```bash
# Clean up reports older than 30 days
python scripts/generate_html_report.py --cleanup 30
```

### 3. Custom Report Titles
Use descriptive titles for easy identification:
```bash
python scripts/generate_html_report.py --run-id backtest_123 --title "Momentum Strategy Q1 2024"
```

### 4. Strategy Comparison
Regularly compare strategies to identify the best performers:
```bash
python scripts/generate_html_report.py --run-ids strategy1 strategy2 strategy3
```

## Troubleshooting

### Common Issues

1. **No backtest runs found**
   - Ensure backtests have been run and results stored
   - Check database connection
   - Verify run IDs exist

2. **Charts not displaying**
   - Ensure Plotly is installed: `pip install plotly`
   - Check browser compatibility
   - Verify HTML file opens in web browser

3. **Missing data**
   - Ensure equity curve data is available
   - Check trade data completeness
   - Verify date ranges are correct

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.services.report_service import ReportService
report_service = ReportService()
```

## Advanced Features

### 1. Automated Report Scheduling
Set up cron jobs to generate reports automatically:

```bash
# Generate daily reports
0 9 * * * cd /path/to/project && python scripts/generate_html_report.py --latest 5
```

### 2. Email Integration
Send reports via email:

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_report_email(report_path, recipient):
    # Email configuration and sending logic
    pass
```

### 3. Web Dashboard Integration
Embed reports in web dashboards:

```html
<iframe src="reports/html/backtest_report.html" width="100%" height="800px"></iframe>
```

## Performance Considerations

- **Large Datasets**: Reports with thousands of trades may take longer to generate
- **Memory Usage**: Multiple large reports can consume significant memory
- **File Size**: HTML files with embedded charts can be several MB
- **Cleanup**: Regular cleanup prevents disk space issues

## Future Enhancements

Planned features for future releases:

- PDF export capability
- More chart types (drawdown charts, rolling metrics)
- Custom metric calculations
- Report templates
- Email scheduling
- Web-based report viewer
- Real-time report updates

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the example scripts
3. Examine the generated sample reports
4. Check the database for backtest data availability

The HTML report generator provides professional-quality reports that rival commercial trading platforms while being fully integrated with your algorithmic trading system. 