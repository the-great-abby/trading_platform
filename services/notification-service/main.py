"""
Notification Service - Email notifications for backtest completion
"""

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import asyncio
from datetime import datetime
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service", version="1.0.0")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@trading-system.com")

# Backtest API configuration
BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:8000")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8081/dashboard")

class NotificationRequest(BaseModel):
    """Notification request model"""
    job_id: str
    user_email: str
    notification_type: str = "backtest_completion"
    custom_message: Optional[str] = None

class EmailNotification:
    """Email notification handler"""
    
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.sender_email = SENDER_EMAIL
        
    def send_backtest_completion_email(self, user_email: str, job_id: str, results: Dict[str, Any]) -> bool:
        """Send backtest completion email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = f"🚀 Backtest Complete - Job {job_id}"
            
            # Create HTML email content
            html_content = self._create_backtest_email_html(job_id, results)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=ssl.create_default_context())
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {user_email} for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {user_email}: {e}")
            return False
    
    def _create_backtest_email_html(self, job_id: str, results: Dict[str, Any]) -> str:
        """Create HTML email content for backtest results"""
        
        # Extract key metrics
        total_return = results.get('total_return_pct', 0)
        sharpe_ratio = results.get('sharpe_ratio', 0)
        max_drawdown = results.get('max_drawdown_pct', 0)
        total_trades = results.get('total_trades', 0)
        win_rate = results.get('win_rate', 0)
        
        # Determine performance color
        if total_return > 0:
            performance_color = "#28a745"
            performance_icon = "📈"
        else:
            performance_color = "#dc3545"
            performance_icon = "📉"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .performance-highlight {{
            background: {performance_color};
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            margin: 10px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #6c757d; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{performance_icon} Backtest Complete!</h1>
        <p>Your trading strategy backtest has finished processing</p>
    </div>
    
    <div class="performance-highlight">
        <h2>Overall Performance</h2>
        <div class="metric-value" style="color: white;">{total_return:.2f}%</div>
        <p>Total Return</p>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value {('positive' if sharpe_ratio > 0 else 'negative')}">{sharpe_ratio:.2f}</div>
            <div class="metric-label">Sharpe Ratio</div>
        </div>
        <div class="metric-card">
            <div class="metric-value negative">{max_drawdown:.2f}%</div>
            <div class="metric-label">Max Drawdown</div>
        </div>
        <div class="metric-card">
            <div class="metric-value neutral">{total_trades}</div>
            <div class="metric-label">Total Trades</div>
        </div>
        <div class="metric-card">
            <div class="metric-value {('positive' if win_rate > 0.5 else 'neutral')}">{win_rate:.1%}</div>
            <div class="metric-label">Win Rate</div>
        </div>
    </div>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{DASHBOARD_URL}" class="cta-button">📊 View Full Results</a>
        <a href="http://localhost:8082/" class="cta-button">🚀 Run New Backtest</a>
    </div>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3>📋 Job Details</h3>
        <p><strong>Job ID:</strong> {job_id}</p>
        <p><strong>Completed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Strategies:</strong> {', '.join(results.get('strategies', []))}</p>
        <p><strong>Symbols:</strong> {', '.join(results.get('symbols', []))}</p>
    </div>
    
    <div class="footer">
        <p>This is an automated notification from your Trading System</p>
        <p>Job ID: {job_id}</p>
    </div>
</body>
</html>
"""

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "notification-service"}

@app.post("/api/send-notification")
async def send_notification(request: NotificationRequest, background_tasks: BackgroundTasks):
    """Send notification for backtest completion"""
    try:
        logger.info(f"Sending notification for job {request.job_id} to {request.user_email}")
        
        # Get backtest results
        results = await get_backtest_results(request.job_id)
        
        # Send email notification
        email_notifier = EmailNotification()
        success = email_notifier.send_backtest_completion_email(
            request.user_email, 
            request.job_id, 
            results
        )
        
        if success:
            return {
                "success": True,
                "message": "Notification sent successfully",
                "job_id": request.job_id,
                "email": request.user_email
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")
            
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_backtest_results(job_id: str) -> Dict[str, Any]:
    """Get backtest results from API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKTEST_API_URL}/api/v1/runs/{job_id}")
            if response.status_code == 200:
                return response.json()
            else:
                # Return default results if API call fails
                return {
                    "total_return_pct": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown_pct": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "strategies": ["Unknown"],
                    "symbols": ["Unknown"]
                }
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        return {
            "total_return_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "strategies": ["Unknown"],
            "symbols": ["Unknown"]
        }

@app.post("/api/test-email")
async def test_email(user_email: str):
    """Test email functionality"""
    try:
        email_notifier = EmailNotification()
        test_results = {
            "total_return_pct": 15.5,
            "sharpe_ratio": 1.2,
            "max_drawdown_pct": -8.3,
            "total_trades": 45,
            "win_rate": 0.62,
            "strategies": ["BollingerBands", "RSI", "MACD"],
            "symbols": ["AAPL", "GOOGL", "MSFT"]
        }
        
        success = email_notifier.send_backtest_completion_email(
            user_email, 
            "test-job-123", 
            test_results
        )
        
        if success:
            return {"success": True, "message": "Test email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_page():
    """Test page for email notifications"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Email Notification Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .form { margin: 20px 0; }
        input, button { padding: 10px; margin: 5px; }
        .result { margin: 20px 0; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>📧 Email Notification Test</h1>
    <p>Test the email notification system by sending a test email.</p>
    
    <div class="form">
        <input type="email" id="test-email" placeholder="Enter your email address" style="width: 300px;">
        <button onclick="sendTestEmail()">Send Test Email</button>
    </div>
    
    <div id="result"></div>
    
    <script>
        async function sendTestEmail() {
            const email = document.getElementById('test-email').value;
            const resultDiv = document.getElementById('result');
            
            if (!email) {
                resultDiv.innerHTML = '<div class="result error">Please enter an email address</div>';
                return;
            }
            
            try {
                const response = await fetch('/api/test-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_email: email })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    resultDiv.innerHTML = '<div class="result success">✅ Test email sent successfully! Check your inbox.</div>';
                } else {
                    resultDiv.innerHTML = '<div class="result error">❌ Failed to send test email: ' + result.detail + '</div>';
                }
            } catch (error) {
                resultDiv.innerHTML = '<div class="result error">❌ Error: ' + error.message + '</div>';
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8083) 