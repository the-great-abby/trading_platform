#!/usr/bin/env python3
"""
AI Recommendations Report Generator
Generates HTML reports for AI-powered trading recommendations
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path

class AIRecommendationsReportGenerator:
    """Generates HTML reports for AI trading recommendations"""
    
    def __init__(self, output_dir: str = "reports/html"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_recommendations_report(self, analysis_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Generate HTML report for AI recommendations"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_recommendations_{timestamp}.html"
        
        filepath = self.output_dir / filename
        
        # Extract data
        recommendations = analysis_data.get("recommendations", [])
        summary = analysis_data.get("summary", {})
        timestamp = analysis_data.get("timestamp", datetime.now())
        
        # Create HTML content
        html_content = self._create_html_content(recommendations, summary, timestamp)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def _create_html_content(self, recommendations: List[Dict], summary: Dict, timestamp: datetime) -> str:
        """Create the HTML content for the report"""
        
        # Create DataFrame for easier manipulation
        df = pd.DataFrame(recommendations)
        
        # Generate summary statistics
        buy_signals = df[df['recommendation'] == 'BUY']
        sell_signals = df[df['recommendation'] == 'SELL']
        hold_signals = df[df['recommendation'] == 'HOLD']
        
        high_confidence = df[df['confidence'] >= 80]
        medium_confidence = df[(df['confidence'] >= 60) & (df['confidence'] < 80)]
        low_confidence = df[df['confidence'] < 60]
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Trading Recommendations Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 20px;
        }}
        
        .timestamp {{
            font-size: 0.9em;
            opacity: 0.7;
        }}
        
        .summary-section {{
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            text-align: center;
            border-left: 4px solid #3498db;
        }}
        
        .summary-card.buy {{
            border-left-color: #27ae60;
        }}
        
        .summary-card.sell {{
            border-left-color: #e74c3c;
        }}
        
        .summary-card.hold {{
            border-left-color: #f39c12;
        }}
        
        .summary-card.high-confidence {{
            border-left-color: #9b59b6;
        }}
        
        .summary-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .summary-label {{
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts-section {{
            padding: 30px;
        }}
        
        .chart-container {{
            margin-bottom: 40px;
        }}
        
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #2c3e50;
            font-weight: 600;
        }}
        
        .recommendations-section {{
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .recommendations-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        
        .recommendation-card {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border-left: 4px solid #3498db;
            transition: transform 0.2s ease;
        }}
        
        .recommendation-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }}
        
        .recommendation-card.buy {{
            border-left-color: #27ae60;
        }}
        
        .recommendation-card.sell {{
            border-left-color: #e74c3c;
        }}
        
        .recommendation-card.hold {{
            border-left-color: #f39c12;
        }}
        
        .recommendation-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .symbol {{
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .recommendation-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .recommendation-badge.buy {{
            background: #d5f4e6;
            color: #27ae60;
        }}
        
        .recommendation-badge.sell {{
            background: #fadbd8;
            color: #e74c3c;
        }}
        
        .recommendation-badge.hold {{
            background: #fdeaa7;
            color: #f39c12;
        }}
        
        .confidence-bar {{
            width: 100%;
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            margin: 15px 0;
            overflow: hidden;
        }}
        
        .confidence-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        
        .confidence-fill.high {{
            background: linear-gradient(90deg, #27ae60, #2ecc71);
        }}
        
        .confidence-fill.medium {{
            background: linear-gradient(90deg, #f39c12, #f1c40f);
        }}
        
        .confidence-fill.low {{
            background: linear-gradient(90deg, #e74c3c, #c0392b);
        }}
        
        .confidence-text {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        
        .price-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 15px 0;
        }}
        
        .price-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }}
        
        .price-label {{
            font-size: 0.8em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .price-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 5px;
        }}
        
        .reasoning {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
            font-size: 0.9em;
            line-height: 1.6;
            color: #34495e;
        }}
        
        .technical-signals {{
            margin-top: 15px;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 5px;
        }}
        
        .technical-title {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        
        .signal-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
        }}
        
        .signal-item {{
            text-align: center;
            padding: 8px;
            background: white;
            border-radius: 3px;
            font-size: 0.8em;
        }}
        
        .signal-value {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .signal-label {{
            color: #7f8c8d;
            font-size: 0.7em;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .recommendations-grid {{
                grid-template-columns: 1fr;
            }}
            
            .summary-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Trading Recommendations</h1>
            <div class="subtitle">AI-Powered Stock Analysis & Recommendations</div>
            <div class="timestamp">Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </div>
        
        <div class="summary-section">
            <div class="summary-grid">
                <div class="summary-card buy">
                    <div class="summary-number">{len(buy_signals)}</div>
                    <div class="summary-label">Buy Signals</div>
                </div>
                <div class="summary-card sell">
                    <div class="summary-number">{len(sell_signals)}</div>
                    <div class="summary-label">Sell Signals</div>
                </div>
                <div class="summary-card hold">
                    <div class="summary-number">{len(hold_signals)}</div>
                    <div class="summary-label">Hold Signals</div>
                </div>
                <div class="summary-card high-confidence">
                    <div class="summary-number">{len(high_confidence)}</div>
                    <div class="summary-label">High Confidence</div>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Recommendation Distribution</div>
                <div id="recommendationChart"></div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Confidence Distribution</div>
                <div id="confidenceChart"></div>
            </div>
        </div>
        
        <div class="recommendations-section">
            <h2 style="margin-bottom: 30px; color: #2c3e50;">Detailed Recommendations</h2>
            <div class="recommendations-grid">
"""
        
        # Add recommendation cards
        for rec in recommendations:
            confidence_class = "high" if rec.get('confidence', 0) >= 80 else "medium" if rec.get('confidence', 0) >= 60 else "low"
            recommendation_class = rec.get('recommendation', 'HOLD').lower()
            
            html += f"""
                <div class="recommendation-card {recommendation_class}">
                    <div class="recommendation-header">
                        <div class="symbol">{rec.get('symbol', 'N/A')}</div>
                        <div class="recommendation-badge {recommendation_class}">{rec.get('recommendation', 'HOLD')}</div>
                    </div>
                    
                    <div class="confidence-bar">
                        <div class="confidence-fill {confidence_class}" style="width: {rec.get('confidence', 0)}%"></div>
                    </div>
                    <div class="confidence-text">Confidence: {rec.get('confidence', 0):.1f}%</div>
                    
                    <div class="price-info">
                        <div class="price-item">
                            <div class="price-label">Current Price</div>
                            <div class="price-value">${rec.get('current_price', 0):.2f}</div>
                        </div>
                        <div class="price-item">
                            <div class="price-label">Target Price</div>
                            <div class="price-value">${rec.get('target_price', 0):.2f if rec.get('target_price') else 'N/A'}</div>
                        </div>
                        <div class="price-item">
                            <div class="price-label">Stop Loss</div>
                            <div class="price-value">${rec.get('stop_loss', 0):.2f if rec.get('stop_loss') else 'N/A'}</div>
                        </div>
                        <div class="price-item">
                            <div class="price-label">Position Size</div>
                            <div class="price-value">{rec.get('position_size', 'N/A')}</div>
                        </div>
                    </div>
                    
                    <div class="reasoning">
                        <strong>Analysis:</strong> {rec.get('reasoning', 'No reasoning provided')}
                    </div>
                    
                    <div class="technical-signals">
                        <div class="technical-title">Technical Signals</div>
                        <div class="signal-grid">
"""
            
            # Add technical signals
            technical_signals = rec.get('technical_signals', {})
            for signal_name, signal_value in technical_signals.items():
                if isinstance(signal_value, dict):
                    for sub_name, sub_value in signal_value.items():
                        html += f"""
                            <div class="signal-item">
                                <div class="signal-value">{sub_value:.2f if isinstance(sub_value, (int, float)) else sub_value}</div>
                                <div class="signal-label">{signal_name} {sub_name}</div>
                            </div>
"""
                else:
                    html += f"""
                        <div class="signal-item">
                            <div class="signal-value">{signal_value:.2f if isinstance(signal_value, (int, float)) else signal_value}</div>
                            <div class="signal-label">{signal_name}</div>
                        </div>
"""
            
            html += """
                        </div>
                    </div>
                </div>
"""
        
        html += """
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by AI Analysis Service | Trading Platform</p>
        </div>
    </div>
    
    <script>
        // Recommendation distribution chart
        const recommendationData = [
            {x: ['Buy', 'Sell', 'Hold'], y: ["""
        html += f"{len(buy_signals)}, {len(sell_signals)}, {len(hold_signals)}"
        html += """], type: 'bar', marker: {color: ['#27ae60', '#e74c3c', '#f39c12']}}
        ];
        
        const recommendationLayout = {
            title: 'Recommendation Distribution',
            xaxis: {title: 'Recommendation'},
            yaxis: {title: 'Count'},
            margin: {l: 50, r: 50, t: 50, b: 50}
        };
        
        Plotly.newPlot('recommendationChart', recommendationData, recommendationLayout);
        
        // Confidence distribution chart
        const confidenceData = [
            {x: ['High (80-100%)', 'Medium (60-79%)', 'Low (<60%)'], 
             y: ["""
        html += f"{len(high_confidence)}, {len(medium_confidence)}, {len(low_confidence)}"
        html += """], type: 'bar', marker: {color: ['#9b59b6', '#f39c12', '#e74c3c']}}
        ];
        
        const confidenceLayout = {
            title: 'Confidence Distribution',
            xaxis: {title: 'Confidence Level'},
            yaxis: {title: 'Count'},
            margin: {l: 50, r: 50, t: 50, b: 50}
        };
        
        Plotly.newPlot('confidenceChart', confidenceData, confidenceLayout);
    </script>
</body>
</html>
"""
        
        return html
    
    def generate_comparison_report(self, analyses: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Generate comparison report for multiple analyses"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_comparison_{timestamp}.html"
        
        filepath = self.output_dir / filename
        
        # Create comparison HTML
        html_content = self._create_comparison_html(analyses)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)

def main():
    """Example usage"""
    generator = AIRecommendationsReportGenerator()
    
    # Example analysis data
    sample_data = {
        "timestamp": datetime.now(),
        "recommendations": [
            {
                "symbol": "AAPL",
                "current_price": 150.25,
                "recommendation": "BUY",
                "confidence": 85.5,
                "reasoning": "Strong technical signals with positive sentiment",
                "target_price": 165.00,
                "stop_loss": 145.00,
                "position_size": "MEDIUM",
                "risk_level": "MEDIUM",
                "technical_signals": {
                    "rsi": 65.2,
                    "macd": {"value": 0.5, "signal": 0.3, "histogram": 0.2},
                    "sma_20": 148.50,
                    "sma_50": 145.75
                },
                "sentiment_score": 0.75,
                "market_context": {"volume": 50000000, "change_percent": 2.5}
            },
            {
                "symbol": "TSLA",
                "current_price": 250.00,
                "recommendation": "SELL",
                "confidence": 70.0,
                "reasoning": "Overbought conditions with negative sentiment",
                "target_price": 230.00,
                "stop_loss": 260.00,
                "position_size": "SMALL",
                "risk_level": "HIGH",
                "technical_signals": {
                    "rsi": 75.8,
                    "macd": {"value": -0.2, "signal": 0.1, "histogram": -0.3},
                    "sma_20": 245.00,
                    "sma_50": 240.00
                },
                "sentiment_score": -0.25,
                "market_context": {"volume": 30000000, "change_percent": -1.5}
            }
        ],
        "summary": {
            "total_analyzed": 2,
            "buy_recommendations": 1,
            "sell_recommendations": 1,
            "hold_recommendations": 0,
            "average_confidence": 77.75,
            "high_confidence_signals": 1,
            "medium_confidence_signals": 1,
            "low_confidence_signals": 0
        }
    }
    
    # Generate report
    report_path = generator.generate_recommendations_report(sample_data)
    print(f"Generated AI recommendations report: {report_path}")

if __name__ == "__main__":
    main() 