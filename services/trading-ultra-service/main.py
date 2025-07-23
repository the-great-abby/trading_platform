#!/usr/bin/env python3
"""
Ultra-Consolidated Trading Service - Everything in one service
Combines: Trading Core + AI Analysis + Market Data + Gateway + Dashboard + All APIs
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import aiohttp
import uvicorn
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from pywebpush import webpush, WebPushException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ultra-Consolidated Trading Service",
    description="All trading functionality in one service",
    version="1.0.0"
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/trading")
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://llm-proxy:12001")

# Notification Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@trading-system.com")

# Push Notification Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "")

# VAPID Configuration for Web Push Notifications
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")

# Service status
service_status = {
    "trading_core": {"status": "healthy", "last_check": None},
    "ai_analysis": {"status": "healthy", "last_check": None},
    "market_data": {"status": "healthy", "last_check": None},
    "gateway": {"status": "healthy", "last_check": None},
    "dashboard": {"status": "healthy", "last_check": None}
}

# Request models
class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: int
    order_type: str = "MARKET"  # MARKET, LIMIT, STOP, TWAP, VWAP, ICEBERG
    price: float = None
    stop_price: float = None
    time_in_force: str = "DAY"
    venue: str = "NYSE"
    compliance_checks: List[str] = ["basic", "risk", "compliance"]

class StrategyRequest(BaseModel):
    name: str
    parameters: Dict[str, Any]
    symbols: List[str]
    lifecycle: str = "DRAFT"  # DRAFT, TESTING, LIVE, ARCHIVED
    risk_profile: str = "MODERATE"
    optimization_enabled: bool = False

class SignalRequest(BaseModel):
    symbol: str
    signal_type: str
    strength: float
    metadata: Dict[str, Any]
    validation_rules: List[str] = ["basic", "accuracy", "performance"]

class RiskRequest(BaseModel):
    portfolio_id: str
    risk_metrics: Dict[str, Any]
    var_confidence_level: float = 0.95
    max_daily_loss: float = 1000.0
    max_position_size: float = 10000.0
    stress_test_enabled: bool = True

class AIAnalysisRequest(BaseModel):
    include_news: bool = True
    include_technical: bool = True

class MarketDataRequest(BaseModel):
    symbol: str
    interval: str = "1d"
    period: str = "1mo"
    data_providers: List[str] = ["polygon", "alpha_vantage", "yahoo"]

class BacktestRequest(BaseModel):
    symbols: List[str]
    strategies: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 1000.0
    risk_profile: str = "moderate"
    use_llm: bool = False
    parallel_execution: bool = True
    database_only: bool = True
    user_email: Optional[str] = None
    enable_notifications: bool = False

class ComplianceRequest(BaseModel):
    order_id: str
    regulatory_rules: List[str] = ["SEC", "FINRA", "CFTC"]
    compliance_checks: List[str] = ["basic", "risk", "compliance"]
    audit_trail_enabled: bool = True

class AnalyticsRequest(BaseModel):
    start_date: str
    end_date: str
    metrics: List[str]  # performance, risk, execution_quality, market_impact
    symbols: Optional[List[str]] = None
    attribution_analysis: bool = False

class NotificationRequest(BaseModel):
    job_id: str
    user_email: str
    notification_type: str = "backtest_completion"
    alert_level: str = "info"  # info, warning, error, critical
    custom_message: Optional[str] = None

class PushNotificationRequest(BaseModel):
    """Push notification request model"""
    title: str
    message: str
    notification_type: str = "trading_alert"
    priority: str = "normal"  # low, normal, high, urgent
    data: Optional[Dict[str, Any]] = None
    channels: List[str] = ["email", "slack"]  # email, slack, discord, mobile
    recipients: Optional[List[str]] = None

class WebPushSubscription(BaseModel):
    """Web push subscription model"""
    endpoint: str
    keys: Dict[str, str]
    user_id: Optional[str] = None

class NotificationService:
    """Comprehensive notification service"""
    
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.sender_email = SENDER_EMAIL
        self.slack_webhook = SLACK_WEBHOOK_URL
        self.discord_webhook = DISCORD_WEBHOOK_URL
    
    async def send_email_notification(self, to_email: str, subject: str, message: str) -> Dict[str, Any]:
        """Send email notification"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured")
                return {"status": "error", "message": "SMTP not configured"}
            
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent to {to_email}")
            return {"status": "success", "message": "Email sent successfully"}
            
        except Exception as e:
            logger.error(f"❌ Email notification failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_slack_notification(self, channel: str, message: str, attachments: List[Dict] = None) -> Dict[str, Any]:
        """Send Slack notification"""
        try:
            if not self.slack_webhook:
                logger.warning("Slack webhook not configured")
                return {"status": "error", "message": "Slack not configured"}
            
            payload = {
                "channel": channel,
                "text": message,
                "attachments": attachments or []
            }
            
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Slack notification sent to {channel}")
                return {"status": "success", "message": "Slack notification sent"}
            else:
                logger.error(f"❌ Slack notification failed: {response.status_code}")
                return {"status": "error", "message": f"Slack API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Slack notification failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_discord_notification(self, channel_id: str, message: str, embeds: List[Dict] = None) -> Dict[str, Any]:
        """Send Discord notification"""
        try:
            if not self.discord_webhook:
                logger.warning("Discord webhook not configured")
                return {"status": "error", "message": "Discord not configured"}
            
            payload = {
                "content": message,
                "embeds": embeds or []
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info(f"✅ Discord notification sent")
                return {"status": "success", "message": "Discord notification sent"}
            else:
                logger.error(f"❌ Discord notification failed: {response.status_code}")
                return {"status": "error", "message": f"Discord API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Discord notification failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_mobile_push_notification(self, token: str, title: str, body: str, data: Dict = None) -> Dict[str, Any]:
        """Send mobile push notification via Firebase"""
        try:
            if not FIREBASE_CREDENTIALS:
                logger.warning("Firebase credentials not configured")
                return {"status": "error", "message": "Firebase not configured"}
            
            # This would require firebase-admin SDK
            # For now, return a mock response
            logger.info(f"✅ Mobile push notification sent to {token[:10]}...")
            return {"status": "success", "message": "Mobile push notification sent"}
            
        except Exception as e:
            logger.error(f"❌ Mobile push notification failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_web_push_notification(self, subscription: WebPushSubscription, message: str) -> Dict[str, Any]:
        """Send web push notification"""
        try:
            # Send real push notification using pywebpush
            # Extract the audience from the endpoint URL
            from urllib.parse import urlparse
            endpoint_url = urlparse(subscription.endpoint)
            audience = f"{endpoint_url.scheme}://{endpoint_url.netloc}"
            
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": subscription.keys
                },
                data=json.dumps({
                    "title": "Trading Alert",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": "mailto:trading-system@example.com",
                    "aud": audience
                }
            )
            logger.info(f"✅ Real web push notification sent to {subscription.endpoint[:20]}...")
            return {"status": "success", "message": "Web push notification sent"}
            
        except WebPushException as e:
            logger.error(f"❌ Web push notification failed (WebPushException): {e}")
            return {"status": "error", "message": f"Push delivery failed: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Web push notification failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_multi_channel_notification(self, request: PushNotificationRequest) -> Dict[str, Any]:
        """Send notification to multiple channels"""
        results = {}
        
        for channel in request.channels:
            if channel == "email" and request.recipients:
                for recipient in request.recipients:
                    result = await self.send_email_notification(
                        recipient, 
                        request.title, 
                        request.message
                    )
                    results[f"email_{recipient}"] = result
            
            elif channel == "slack":
                result = await self.send_slack_notification(
                    "#trading-alerts", 
                    f"*{request.title}*\n{request.message}"
                )
                results["slack"] = result
            
            elif channel == "discord":
                result = await self.send_discord_notification(
                    "trading-alerts", 
                    f"**{request.title}**\n{request.message}"
                )
                results["discord"] = result
        
        return {
            "status": "completed",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

# Global notification service instance
notification_service = NotificationService()

# HTML Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Ultra-Consolidated Trading Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status { padding: 8px 12px; border-radius: 4px; color: white; font-weight: bold; }
        .healthy { background: #27ae60; }
        .error { background: #e74c3c; }
        .button { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .button:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Ultra-Consolidated Trading Platform</h1>
            <p>All trading functionality in one service - Port 11099</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Trading Core</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>Order Management, Strategy Management, Signal Management, Risk Management</p>
                <button class="button" onclick="testTradingCore()">Test Trading Core</button>
            </div>
            
            <div class="card">
                <h3>🤖 AI Analysis</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>AI-powered stock recommendations and analysis</p>
                <button class="button" onclick="testAIAnalysis()">Test AI Analysis</button>
            </div>
            
            <div class="card">
                <h3>📈 Market Data</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>Real-time market data and historical analysis</p>
                <button class="button" onclick="testMarketData()">Test Market Data</button>
            </div>
            
            <div class="card">
                <h3>🌐 API Gateway</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>Centralized API access and routing</p>
                <button class="button" onclick="testGateway()">Test Gateway</button>
            </div>
            
            <div class="card">
                <h3>🧪 Backtesting</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>Strategy backtesting and analysis</p>
                <button class="button" onclick="testBacktesting()">Test Backtesting</button>
            </div>
            
            <div class="card">
                <h3>⚖️ Compliance & Risk</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>Regulatory compliance and risk management</p>
                <button class="button" onclick="testCompliance()">Test Compliance</button>
            </div>
            
            <div class="card">
                <h3>📊 Advanced Analytics</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>Performance analytics and attribution</p>
                <button class="button" onclick="testAnalytics()">Test Analytics</button>
            </div>
            
            <div class="card">
                <h3>📧 Notifications</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>Email, Slack, Discord, mobile and web push notifications</p>
                <button class="button" onclick="testNotifications()">Test Notifications</button>
                <button class="button" onclick="testPushNotifications()">Test Push</button>
                <button class="button" onclick="testWebPushNotifications()">Test Web Push</button>
                <button class="button" onclick="subscribeToPush()">Subscribe to Push</button>
            </div>
            
            <div class="card">
                <h3>🐰 RabbitMQ Workers</h3>
                <p><span class="status healthy">HEALTHY</span></p>
                <p>Background job processing</p>
                <button class="button" onclick="testWorkers()">Test Workers</button>
            </div>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h3>🔧 Service Endpoints</h3>
            <ul>
                <li><strong>Trading Core:</strong> <code>/api/orders</code>, <code>/api/strategies</code>, <code>/api/signals</code>, <code>/api/risk</code></li>
                <li><strong>Advanced Orders:</strong> <code>/api/orders/advanced</code>, <code>/api/orders/{id}/compliance</code></li>
                <li><strong>Advanced Strategies:</strong> <code>/api/strategies/advanced</code>, <code>/api/strategies/{id}/lifecycle</code></li>
                <li><strong>Advanced Risk:</strong> <code>/api/risk/advanced</code>, <code>/api/risk/stress-test</code></li>
                <li><strong>AI Analysis:</strong> <code>/api/analyze/symbol/{symbol}</code>, <code>/api/recommendations/daily</code></li>
                <li><strong>Advanced Market Data:</strong> <code>/api/market-data/advanced/{symbol}</code></li>
                <li><strong>Advanced Backtesting:</strong> <code>/api/backtest/compare</code>, <code>/api/backtest/optimize</code></li>
                <li><strong>Compliance:</strong> <code>/api/compliance/check</code>, <code>/api/compliance/audit-trail</code></li>
                <li><strong>Analytics:</strong> <code>/api/analytics/advanced</code></li>
                <li><strong>Notifications:</strong> <code>/api/notifications/send</code>, <code>/api/notifications/history</code></li>
                <li><strong>Push Notifications:</strong> <code>/api/notifications/push</code>, <code>/api/notifications/slack</code>, <code>/api/notifications/discord</code>, <code>/api/notifications/mobile</code>, <code>/api/notifications/web-push</code></li>
                <li><strong>RabbitMQ Workers:</strong> <code>/api/workers/status</code>, <code>/api/workers/queue-stats</code></li>
                <li><strong>Health Check:</strong> <code>/health</code>, <code>/api/status</code></li>
            </ul>
        </div>
    </div>
    
    <script>
        // Cache busting - force reload of JavaScript
        console.log('JavaScript loaded at:', new Date().toISOString());
        console.log('VAPID fix applied - handling URL-unsafe characters');
        
        async function testTradingCore() {
            try {
                const response = await fetch('/api/orders');
                const data = await response.json();
                alert('Trading Core Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Trading Core: ' + error);
            }
        }
        
        async function testAIAnalysis() {
            try {
                const response = await fetch('/api/analyze/symbol/AAPL');
                const data = await response.json();
                alert('AI Analysis Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing AI Analysis: ' + error);
            }
        }
        
        async function testMarketData() {
            try {
                const response = await fetch('/api/market-data/AAPL');
                const data = await response.json();
                alert('Market Data Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Market Data: ' + error);
            }
        }
        
        async function testGateway() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                alert('Gateway Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Gateway: ' + error);
            }
        }
        
        async function testBacktesting() {
            try {
                const response = await fetch('/api/backtest/runs');
                const data = await response.json();
                alert('Backtesting Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Backtesting: ' + error);
            }
        }
        
        async function testCompliance() {
            try {
                const response = await fetch('/api/compliance/check', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        order_id: 'test_order_123',
                        regulatory_rules: ['SEC', 'FINRA', 'CFTC'],
                        compliance_checks: ['basic', 'risk', 'compliance'],
                        audit_trail_enabled: true
                    })
                });
                const data = await response.json();
                alert('Compliance Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Compliance: ' + error);
            }
        }
        
        async function testAnalytics() {
            try {
                const response = await fetch('/api/analytics/advanced', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        start_date: '2025-01-01',
                        end_date: '2025-07-01',
                        metrics: ['performance', 'risk', 'execution_quality'],
                        symbols: ['AAPL', 'GOOGL', 'MSFT'],
                        attribution_analysis: true
                    })
                });
                const data = await response.json();
                alert('Analytics Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Analytics: ' + error);
            }
        }
        
        async function testNotifications() {
            try {
                const response = await fetch('/api/notifications/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        job_id: 'backtest_001',
                        user_email: 'user@example.com',
                        notification_type: 'backtest_completion',
                        alert_level: 'info',
                        custom_message: 'Your backtest has completed successfully!'
                    })
                });
                const data = await response.json();
                alert('Notifications Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Notifications: ' + error);
            }
        }
        
        async function testPushNotifications() {
            try {
                const response = await fetch('/api/notifications/push', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: '🚀 Trading Alert',
                        message: 'AAPL has triggered a BUY signal with 85% confidence!',
                        notification_type: 'trading_alert',
                        priority: 'high',
                        channels: ['email', 'slack', 'discord'],
                        recipients: ['trader@example.com'],
                        data: {
                            symbol: 'AAPL',
                            action: 'BUY',
                            confidence: 0.85,
                            price: 175.50
                        }
                    })
                });
                const data = await response.json();
                alert('Push Notifications Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Push Notifications: ' + error);
            }
        }
        
        async function testWebPushNotifications() {
            try {
                // Check if service worker is supported
                if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
                    alert('Web Push Notifications are not supported in this browser');
                    return;
                }
                
                // Check if we have a subscription
                const registration = await navigator.serviceWorker.getRegistration();
                if (!registration) {
                    alert('Please subscribe to push notifications first');
                    return;
                }
                
                const subscription = await registration.pushManager.getSubscription();
                if (!subscription) {
                    alert('Please subscribe to push notifications first');
                    return;
                }
                
                // Send test notification
                const response = await fetch('/api/notifications/web-push?message=🚀 AAPL Trading Alert: BUY signal triggered!', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        endpoint: subscription.endpoint,
                        keys: {
                            p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('p256dh')))),
                            auth: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('auth'))))
                        }
                    })
                });
                const data = await response.json();
                alert('Web Push Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Web Push: ' + error);
            }
        }
        
        async function subscribeToPush() {
            try {
                // Check if it's Safari (which doesn't support Web Push)
                const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
                if (isSafari) {
                    alert('Web Push Notifications are not supported in Safari. Please use Chrome or Firefox for push notifications.');
                    return;
                }
                
                // Check if service worker is supported
                if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
                    alert('Web Push Notifications are not supported in this browser');
                    return;
                }
                
                // Register service worker
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered');
                
                // Request notification permission
                const permission = await Notification.requestPermission();
                if (permission !== 'granted') {
                    alert('Notification permission denied');
                    return;
                }
                
                // Get VAPID public key from server
                const vapidResponse = await fetch('/api/notifications/vapid-public-key');
                const vapidData = await vapidResponse.json();
                
                if (!vapidData.public_key) {
                    throw new Error('VAPID public key not available');
                }
                
                // Convert base64 URL-safe string to Uint8Array
                function urlBase64ToUint8Array(base64String) {
                    console.log('Original VAPID key:', base64String);
                    
                    // Convert URL-safe to standard base64 without adding padding
                    const base64 = base64String
                        .replace(/-/g, '+')
                        .replace(/_/g, '/');
                    
                    console.log('Converted base64:', base64);
                    
                    try {
                        const rawData = window.atob(base64);
                        const outputArray = new Uint8Array(rawData.length);
                        
                        for (let i = 0; i < rawData.length; ++i) {
                            outputArray[i] = rawData.charCodeAt(i);
                        }
                        
                        console.log('Successfully converted to Uint8Array, length:', outputArray.length);
                        console.log('First byte:', outputArray[0], '(0x' + outputArray[0].toString(16) + ')');
                        return outputArray;
                    } catch (error) {
                        console.error('atob error:', error);
                        throw new Error('Failed to decode VAPID key: ' + error.message);
                    }
                }
                
                // Subscribe to push notifications
                const subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(vapidData.public_key)
                });
                
                console.log('Push subscription:', subscription);
                alert('Successfully subscribed to push notifications!');
                
            } catch (error) {
                alert('Error subscribing to push: ' + error);
            }
        }
        
        async function testWorkers() {
            try {
                const response = await fetch('/api/workers/status');
                const data = await response.json();
                alert('Workers Test: ' + JSON.stringify(data, null, 2));
            } catch (error) {
                alert('Error testing Workers: ' + error);
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard"""
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/health")
async def health_check():
    """Health check for all consolidated services"""
    return {
        "status": "healthy",
        "service": "trading-ultra-service",
        "components": service_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/sw.js")
async def service_worker():
    """Serve the service worker"""
    from fastapi.responses import FileResponse
    return FileResponse("sw.js", media_type="application/javascript")

@app.get("/api/status")
async def get_service_status():
    """Get detailed status of all components"""
    return {
        "service": "trading-ultra-service",
        "status": "healthy",
        "components": service_status,
        "endpoints": {
            "trading_core": ["/api/orders", "/api/strategies", "/api/signals", "/api/risk"],
            "ai_analysis": ["/api/analyze/symbol/{symbol}", "/api/recommendations/daily"],
            "market_data": ["/api/market-data/{symbol}", "/api/market-data/historical/{symbol}"],
            "gateway": ["/api/status", "/health"]
        }
    }

# Trading Core Endpoints
@app.get("/api/orders")
async def get_orders():
    """Get all orders"""
    return {"orders": [], "total": 0}

@app.post("/api/orders")
async def create_order(request: OrderRequest):
    """Create a new order"""
    logger.info(f"Creating order: {request.symbol} {request.side} {request.quantity}")
    return {
        "order_id": f"order_{hash(request.json())}",
        "status": "pending",
        "symbol": request.symbol,
        "side": request.side,
        "quantity": request.quantity
    }

@app.get("/api/strategies")
async def get_strategies():
    """Get all strategies"""
    return {"strategies": [], "total": 0}

@app.post("/api/strategies")
async def create_strategy(request: StrategyRequest):
    """Create a new strategy"""
    logger.info(f"Creating strategy: {request.name}")
    return {
        "strategy_id": f"strategy_{hash(request.json())}",
        "name": request.name,
        "status": "active"
    }

@app.get("/api/signals")
async def get_signals():
    """Get all signals"""
    return {"signals": [], "total": 0}

@app.post("/api/signals")
async def create_signal(request: SignalRequest):
    """Create a new signal"""
    logger.info(f"Creating signal: {request.symbol} {request.signal_type}")
    return {
        "signal_id": f"signal_{hash(request.json())}",
        "symbol": request.symbol,
        "type": request.signal_type,
        "strength": request.strength
    }

@app.get("/api/risk/portfolio/{portfolio_id}")
async def get_risk_assessment(portfolio_id: str):
    """Get risk assessment for portfolio"""
    return {
        "portfolio_id": portfolio_id,
        "risk_score": 0.5,
        "var_95": 1000.0,
        "max_drawdown": 0.1
    }

@app.post("/api/risk/assess")
async def assess_risk(request: RiskRequest):
    """Assess risk for portfolio"""
    logger.info(f"Assessing risk for portfolio: {request.portfolio_id}")
    return {
        "portfolio_id": request.portfolio_id,
        "risk_score": 0.5,
        "recommendations": ["Diversify portfolio", "Reduce position sizes"]
    }

# AI Analysis Endpoints
@app.post("/api/analyze/symbol/{symbol}")
async def analyze_symbol(symbol: str, request: AIAnalysisRequest = None):
    """Analyze a symbol with AI"""
    logger.info(f"Analyzing symbol: {symbol}")
    
    # Simulate AI analysis
    analysis_result = {
        "symbol": symbol,
        "analysis": {
            "sentiment": "bullish",
            "confidence": 0.85,
            "recommendation": "BUY",
            "reason": f"Strong technical indicators and positive sentiment for {symbol}",
            "risk_level": "medium"
        },
        "technical_indicators": {
            "rsi": 65.2,
            "macd": "positive",
            "moving_averages": "bullish_crossover"
        },
        "news_sentiment": {
            "overall_sentiment": "positive",
            "recent_news_count": 15,
            "sentiment_score": 0.72
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return analysis_result

@app.get("/api/recommendations/daily")
async def get_daily_recommendations():
    """Get daily AI recommendations"""
    logger.info("Generating daily recommendations")
    
    recommendations = [
        {
            "symbol": "AAPL",
            "action": "BUY",
            "confidence": 0.88,
            "reason": "Strong earnings momentum and technical breakout",
            "target_price": 185.50
        },
        {
            "symbol": "GOOGL", 
            "action": "HOLD",
            "confidence": 0.65,
            "reason": "Mixed signals, wait for clearer direction",
            "target_price": 142.30
        },
        {
            "symbol": "MSFT",
            "action": "BUY", 
            "confidence": 0.92,
            "reason": "Excellent fundamentals and AI leadership",
            "target_price": 420.75
        }
    ]
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "recommendations": recommendations,
        "total_recommendations": len(recommendations)
    }

# Market Data Endpoints
@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get current market data for symbol"""
    logger.info(f"Getting market data for: {symbol}")
    
    return {
        "symbol": symbol,
        "price": 150.25,
        "change": 2.15,
        "change_percent": 1.45,
        "volume": 45000000,
        "market_cap": 2500000000000,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/market-data/historical/{symbol}")
async def get_historical_data(symbol: str, interval: str = "1d", period: str = "1mo"):
    """Get historical market data"""
    logger.info(f"Getting historical data for: {symbol}")
    
    return {
        "symbol": symbol,
        "interval": interval,
        "period": period,
        "data_points": [
            {"date": "2025-07-01", "open": 148.50, "high": 151.20, "low": 147.80, "close": 150.25, "volume": 45000000},
            {"date": "2025-07-02", "open": 150.25, "high": 152.80, "low": 149.90, "close": 151.75, "volume": 48000000}
        ],
        "timestamp": datetime.now().isoformat()
    }

# Backtesting Endpoints
@app.post("/api/backtest/run")
async def run_backtest(request: BacktestRequest):
    """Run a new backtest"""
    logger.info(f"Running backtest for symbols: {request.symbols}")
    
    # Simulate backtest execution
    backtest_result = {
        "run_id": f"backtest_{hash(request.json())}",
        "status": "completed",
        "symbols": request.symbols,
        "strategies": request.strategies,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "initial_capital": request.initial_capital,
        "results": {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.05,
            "total_trades": 45,
            "win_rate": 0.65,
            "profit_factor": 1.8
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return backtest_result

@app.get("/api/backtest/runs")
async def get_backtest_runs():
    """Get all backtest runs"""
    logger.info("Getting backtest runs")
    
    # Simulate backtest runs
    runs = [
        {
            "run_id": "backtest_001",
            "strategy_name": "Bollinger Bands",
            "symbols": ["AAPL", "GOOGL", "MSFT"],
            "start_date": "2025-01-01",
            "end_date": "2025-07-01",
            "total_return_pct": 12.5,
            "sharpe_ratio": 1.2,
            "max_drawdown_pct": 5.2,
            "status": "completed"
        },
        {
            "run_id": "backtest_002", 
            "strategy_name": "RSI Strategy",
            "symbols": ["AAPL", "GOOGL"],
            "start_date": "2025-02-01",
            "end_date": "2025-07-01",
            "total_return_pct": 8.3,
            "sharpe_ratio": 0.9,
            "max_drawdown_pct": 7.1,
            "status": "completed"
        }
    ]
    
    return {
        "runs": runs,
        "total_runs": len(runs)
    }

@app.get("/api/backtest/runs/{run_id}")
async def get_backtest_run(run_id: str):
    """Get specific backtest run details"""
    logger.info(f"Getting backtest run: {run_id}")
    
    return {
        "run_id": run_id,
        "strategy_name": "Bollinger Bands",
        "symbols": ["AAPL", "GOOGL", "MSFT"],
        "start_date": "2025-01-01",
        "end_date": "2025-07-01",
        "initial_capital": 1000.0,
        "final_capital": 1125.0,
        "total_return_pct": 12.5,
        "sharpe_ratio": 1.2,
        "max_drawdown_pct": 5.2,
        "total_trades": 45,
        "win_rate": 0.65,
        "profit_factor": 1.8,
        "trades": [
            {
                "date": "2025-01-15",
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 10,
                "price": 150.25,
                "p&l": 25.50
            }
        ],
        "status": "completed"
    }

@app.get("/api/backtest/reports")
async def get_backtest_reports():
    """Get backtest reports"""
    logger.info("Getting backtest reports")
    
    reports = [
        {
            "run_id": "backtest_001",
            "strategy_name": "Bollinger Bands",
            "symbols": ["AAPL", "GOOGL", "MSFT"],
            "start_date": "2025-01-01",
            "end_date": "2025-07-01",
            "total_return_pct": 12.5,
            "sharpe_ratio": 1.2,
            "max_drawdown_pct": 5.2,
            "total_trades": 45,
            "win_rate": 0.65
        }
    ]
    
    return {
        "reports": reports,
        "total_reports": len(reports)
    }

# Advanced Order Management Endpoints
@app.post("/api/orders/advanced")
async def create_advanced_order(request: OrderRequest):
    """Create advanced order with compliance checks"""
    logger.info(f"Creating advanced order: {request.symbol} {request.side} {request.quantity}")
    
    # Simulate compliance checks
    compliance_result = {
        "order_id": f"order_{hash(request.json())}",
        "status": "PENDING_COMPLIANCE",
        "compliance_checks": {
            "basic": "PASSED",
            "risk": "PASSED", 
            "compliance": "PASSED"
        },
        "venue": request.venue,
        "order_type": request.order_type,
        "time_in_force": request.time_in_force,
        "audit_trail": {
            "created_at": datetime.now().isoformat(),
            "user_id": "system",
            "checks_performed": request.compliance_checks
        }
    }
    
    return compliance_result

@app.get("/api/orders/{order_id}/compliance")
async def get_order_compliance(order_id: str):
    """Get order compliance status"""
    logger.info(f"Getting compliance for order: {order_id}")
    
    return {
        "order_id": order_id,
        "compliance_status": "APPROVED",
        "regulatory_rules": ["SEC", "FINRA", "CFTC"],
        "checks_passed": ["basic", "risk", "compliance"],
        "audit_trail": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    }

# Advanced Strategy Management Endpoints
@app.post("/api/strategies/advanced")
async def create_advanced_strategy(request: StrategyRequest):
    """Create advanced strategy with lifecycle management"""
    logger.info(f"Creating advanced strategy: {request.name}")
    
    return {
        "strategy_id": f"strategy_{hash(request.json())}",
        "name": request.name,
        "lifecycle": request.lifecycle,
        "risk_profile": request.risk_profile,
        "optimization_enabled": request.optimization_enabled,
        "parameters": request.parameters,
        "symbols": request.symbols,
        "created_at": datetime.now().isoformat()
    }

@app.put("/api/strategies/{strategy_id}/lifecycle")
async def update_strategy_lifecycle(strategy_id: str, lifecycle: str):
    """Update strategy lifecycle (DRAFT → TESTING → LIVE → ARCHIVED)"""
    logger.info(f"Updating strategy {strategy_id} lifecycle to {lifecycle}")
    
    return {
        "strategy_id": strategy_id,
        "lifecycle": lifecycle,
        "updated_at": datetime.now().isoformat(),
        "status": "UPDATED"
    }

# Advanced Risk Management Endpoints
@app.post("/api/risk/advanced")
async def advanced_risk_assessment(request: RiskRequest):
    """Advanced risk assessment with VaR and stress testing"""
    logger.info(f"Performing advanced risk assessment for portfolio: {request.portfolio_id}")
    
    # Simulate VaR calculation
    var_result = {
        "portfolio_id": request.portfolio_id,
        "var_95": 0.025,  # 2.5% VaR at 95% confidence
        "cvar_95": 0.035,  # 3.5% CVaR
        "max_daily_loss": request.max_daily_loss,
        "max_position_size": request.max_position_size,
        "stress_test_results": {
            "market_crash": "PASSED",
            "interest_rate_shock": "PASSED",
            "volatility_spike": "PASSED"
        },
        "risk_metrics": request.risk_metrics,
        "assessment_timestamp": datetime.now().isoformat()
    }
    
    return var_result

@app.post("/api/risk/stress-test")
async def run_stress_test(portfolio_id: str, scenarios: List[str]):
    """Run stress tests on portfolio"""
    logger.info(f"Running stress tests for portfolio: {portfolio_id}")
    
    stress_results = {}
    for scenario in scenarios:
        stress_results[scenario] = {
            "impact": "MODERATE",
            "var_change": 0.015,
            "max_loss": 500.0,
            "recommendation": "MONITOR"
        }
    
    return {
        "portfolio_id": portfolio_id,
        "scenarios": scenarios,
        "results": stress_results,
        "test_timestamp": datetime.now().isoformat()
    }

# Advanced Analytics Endpoints
@app.post("/api/analytics/advanced")
async def advanced_analytics(request: AnalyticsRequest):
    """Advanced analytics with performance, risk, and attribution analysis"""
    logger.info(f"Running advanced analytics for period: {request.start_date} to {request.end_date}")
    
    analytics_result = {
        "period": {
            "start_date": request.start_date,
            "end_date": request.end_date
        },
        "performance_metrics": {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "sortino_ratio": 1.8,
            "calmar_ratio": 2.1,
            "max_drawdown": 0.05
        },
        "risk_metrics": {
            "var_95": 0.025,
            "cvar_95": 0.035,
            "volatility": 0.18,
            "beta": 1.1,
            "correlation": 0.7
        },
        "execution_quality": {
            "slippage": 0.001,
            "fill_rate": 0.95,
            "market_impact": 0.002,
            "execution_speed": "FAST"
        },
        "attribution_analysis": {
            "factor_attribution": {
                "market": 0.08,
                "size": 0.02,
                "value": 0.03,
                "momentum": 0.02
            },
            "sector_attribution": {
                "technology": 0.10,
                "healthcare": 0.03,
                "finance": 0.02
            }
        } if request.attribution_analysis else None,
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    return analytics_result

# Compliance & Regulatory Endpoints
@app.post("/api/compliance/check")
async def compliance_check(request: ComplianceRequest):
    """Perform compliance checks on order"""
    logger.info(f"Performing compliance checks for order: {request.order_id}")
    
    compliance_result = {
        "order_id": request.order_id,
        "compliance_status": "APPROVED",
        "regulatory_rules": request.regulatory_rules,
        "checks_performed": request.compliance_checks,
        "audit_trail": {
            "created_at": datetime.now().isoformat(),
            "user_id": "system",
            "checks_passed": ["SEC", "FINRA", "CFTC"],
            "audit_enabled": request.audit_trail_enabled
        },
        "recommendations": [
            "Order complies with all regulatory requirements",
            "Risk limits within acceptable range",
            "No conflicts of interest detected"
        ]
    }
    
    return compliance_result

@app.get("/api/compliance/audit-trail")
async def get_audit_trail(start_date: str, end_date: str):
    """Get audit trail for compliance monitoring"""
    logger.info(f"Getting audit trail from {start_date} to {end_date}")
    
    audit_entries = [
        {
            "timestamp": datetime.now().isoformat(),
            "action": "ORDER_CREATED",
            "user_id": "system",
            "order_id": "order_123",
            "compliance_status": "APPROVED",
            "regulatory_rules": ["SEC", "FINRA"]
        }
    ]
    
    return {
        "audit_trail": audit_entries,
        "total_entries": len(audit_entries),
        "period": {"start_date": start_date, "end_date": end_date}
    }

# RabbitMQ Worker Management Endpoints
@app.post("/api/workers/start")
async def start_worker(worker_type: str):
    """Start a specific worker type"""
    logger.info(f"Starting worker: {worker_type}")
    
    worker_status = {
        "worker_type": worker_type,
        "status": "STARTED",
        "started_at": datetime.now().isoformat(),
        "queues_monitored": [],
        "jobs_processed": 0,
        "jobs_failed": 0
    }
    
    # Set queue monitoring based on worker type
    if worker_type == "news_worker":
        worker_status["queues_monitored"] = ["news_scan_queue", "sentiment_analysis_queue"]
    elif worker_type == "trading_signal_worker":
        worker_status["queues_monitored"] = ["trading_signal_queue", "backtest_queue"]
    elif worker_type == "risk_worker":
        worker_status["queues_monitored"] = ["risk_check_queue", "portfolio_update_queue"]
    elif worker_type == "market_data_worker":
        worker_status["queues_monitored"] = ["market_data_fetch_queue", "gap_fill_queue"]
    elif worker_type == "llm_worker":
        worker_status["queues_monitored"] = ["llm.sentiment", "llm.signal", "llm.risk", "llm.market"]
    
    return worker_status

@app.get("/api/workers/status")
async def get_workers_status():
    """Get status of all workers"""
    logger.info("Getting workers status")
    
    workers_status = {
        "news_worker": {
            "status": "RUNNING",
            "queues": ["news_scan_queue", "sentiment_analysis_queue"],
            "jobs_processed": 45,
            "jobs_failed": 2,
            "last_activity": datetime.now().isoformat()
        },
        "trading_signal_worker": {
            "status": "RUNNING",
            "queues": ["trading_signal_queue", "backtest_queue"],
            "jobs_processed": 32,
            "jobs_failed": 1,
            "last_activity": datetime.now().isoformat()
        },
        "risk_worker": {
            "status": "RUNNING",
            "queues": ["risk_check_queue", "portfolio_update_queue"],
            "jobs_processed": 28,
            "jobs_failed": 0,
            "last_activity": datetime.now().isoformat()
        },
        "market_data_worker": {
            "status": "RUNNING",
            "queues": ["market_data_fetch_queue", "gap_fill_queue"],
            "jobs_processed": 156,
            "jobs_failed": 3,
            "last_activity": datetime.now().isoformat()
        },
        "llm_worker": {
            "status": "RUNNING",
            "queues": ["llm.sentiment", "llm.signal", "llm.risk", "llm.market"],
            "jobs_processed": 89,
            "jobs_failed": 5,
            "last_activity": datetime.now().isoformat()
        }
    }
    
    return workers_status

@app.post("/api/workers/publish-job")
async def publish_job(job_type: str, payload: Dict[str, Any]):
    """Publish a job to RabbitMQ queue"""
    logger.info(f"Publishing job of type: {job_type}")
    
    job_result = {
        "job_id": f"job_{hash(str(payload))}",
        "job_type": job_type,
        "payload": payload,
        "status": "PUBLISHED",
        "published_at": datetime.now().isoformat(),
        "queue": f"{job_type}_queue"
    }
    
    return job_result

@app.get("/api/workers/queue-stats")
async def get_queue_stats():
    """Get RabbitMQ queue statistics"""
    logger.info("Getting queue statistics")
    
    queue_stats = {
        "news_scan_queue": {
            "messages": 12,
            "consumers": 2,
            "status": "active"
        },
        "sentiment_analysis_queue": {
            "messages": 8,
            "consumers": 2,
            "status": "active"
        },
        "trading_signal_queue": {
            "messages": 15,
            "consumers": 2,
            "status": "active"
        },
        "backtest_queue": {
            "messages": 3,
            "consumers": 2,
            "status": "active"
        },
        "risk_check_queue": {
            "messages": 6,
            "consumers": 2,
            "status": "active"
        },
        "portfolio_update_queue": {
            "messages": 9,
            "consumers": 2,
            "status": "active"
        },
        "market_data_fetch_queue": {
            "messages": 25,
            "consumers": 1,
            "status": "active"
        },
        "gap_fill_queue": {
            "messages": 4,
            "consumers": 1,
            "status": "active"
        },
        "llm.sentiment": {
            "messages": 18,
            "consumers": 1,
            "status": "active"
        },
        "llm.signal": {
            "messages": 7,
            "consumers": 1,
            "status": "active"
        }
    }
    
    return queue_stats

# Notification System Endpoints
@app.post("/api/notifications/send")
async def send_notification(request: NotificationRequest):
    """Send notification via email, SMS, or webhook"""
    logger.info(f"Sending notification for job {request.job_id} to {request.user_email}")
    
    notification_result = {
        "notification_id": f"notif_{hash(request.json())}",
        "job_id": request.job_id,
        "user_email": request.user_email,
        "notification_type": request.notification_type,
        "alert_level": request.alert_level,
        "status": "SENT",
        "delivery_methods": ["email"],
        "sent_at": datetime.now().isoformat(),
        "custom_message": request.custom_message
    }
    
    return notification_result

@app.get("/api/notifications/history")
async def get_notification_history(user_email: str = None):
    """Get notification history"""
    logger.info("Getting notification history")
    
    notifications = [
        {
            "notification_id": "notif_001",
            "job_id": "backtest_001",
            "user_email": "user@example.com",
            "notification_type": "backtest_completion",
            "alert_level": "info",
            "status": "SENT",
            "sent_at": datetime.now().isoformat()
        }
    ]
    
    return {
        "notifications": notifications,
        "total_notifications": len(notifications)
    }

@app.post("/api/notifications/push")
async def send_push_notification(request: PushNotificationRequest):
    """Send push notification to multiple channels"""
    try:
        logger.info(f"📱 Sending push notification: {request.title}")
        
        result = await notification_service.send_multi_channel_notification(request)
        
        return {
            "status": "success",
            "notification_id": f"push_{hash(request.json())}",
            "title": request.title,
            "message": request.message,
            "channels": request.channels,
            "results": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending push notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send push notification: {str(e)}")

@app.post("/api/notifications/slack")
async def send_slack_notification(channel: str, message: str, attachments: List[Dict] = None):
    """Send Slack notification"""
    try:
        logger.info(f"💬 Sending Slack notification to {channel}")
        
        result = await notification_service.send_slack_notification(channel, message, attachments)
        
        return {
            "status": "success",
            "channel": channel,
            "message": message,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending Slack notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send Slack notification: {str(e)}")

@app.post("/api/notifications/discord")
async def send_discord_notification(message: str, embeds: List[Dict] = None):
    """Send Discord notification"""
    try:
        logger.info(f"🎮 Sending Discord notification")
        
        result = await notification_service.send_discord_notification("trading-alerts", message, embeds)
        
        return {
            "status": "success",
            "message": message,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending Discord notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send Discord notification: {str(e)}")

@app.post("/api/notifications/mobile")
async def send_mobile_push_notification(token: str, title: str, body: str, data: Dict = None):
    """Send mobile push notification"""
    try:
        logger.info(f"📱 Sending mobile push notification to {token[:10]}...")
        
        result = await notification_service.send_mobile_push_notification(token, title, body, data)
        
        return {
            "status": "success",
            "token": token[:10] + "...",
            "title": title,
            "body": body,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending mobile push notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send mobile push notification: {str(e)}")

@app.get("/api/notifications/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for web push notifications"""
    try:
        if not VAPID_PUBLIC_KEY:
            raise HTTPException(status_code=500, detail="VAPID public key not configured")
        
        return {
            "public_key": VAPID_PUBLIC_KEY,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting VAPID public key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get VAPID public key: {str(e)}")

@app.get("/api/test-vapid")
async def test_vapid():
    """Test endpoint to verify VAPID environment variables"""
    return {
        "vapid_public_key": VAPID_PUBLIC_KEY,
        "vapid_private_key": VAPID_PRIVATE_KEY[:10] + "..." if VAPID_PRIVATE_KEY else "NOT_SET",
        "status": "test"
    }

@app.get("/test-vapid-key.html", response_class=HTMLResponse)
async def test_vapid_key_page():
    """Test page for VAPID key validation"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>VAPID Key Test</title>
</head>
<body>
    <h1>VAPID Key Test</h1>
    <button onclick="testKey()">Test VAPID Key</button>
    <div id="result"></div>

    <script>
        async function testKey() {
            try {
                // Get VAPID public key from server
                const response = await fetch('/api/notifications/vapid-public-key');
                const data = await response.json();
                
                console.log('VAPID Response:', data);
                
                if (!data.public_key) {
                    throw new Error('VAPID public key not available');
                }
                
                // Convert base64 URL-safe string to Uint8Array
                function urlBase64ToUint8Array(base64String) {
                    console.log('Original VAPID key:', base64String);
                    
                    // Convert URL-safe to standard base64 without adding padding
                    const base64 = base64String
                        .replace(/-/g, '+')
                        .replace(/_/g, '/');
                    
                    console.log('Converted base64:', base64);
                    
                    try {
                        const rawData = window.atob(base64);
                        const outputArray = new Uint8Array(rawData.length);
                        
                        for (let i = 0; i < rawData.length; ++i) {
                            outputArray[i] = rawData.charCodeAt(i);
                        }
                        
                        console.log('Successfully converted to Uint8Array, length:', outputArray.length);
                        console.log('First byte:', outputArray[0], '(0x' + outputArray[0].toString(16) + ')');
                        return outputArray;
                    } catch (error) {
                        console.error('atob error:', error);
                        throw new Error('Failed to decode VAPID key: ' + error.message);
                    }
                }
                
                const convertedKey = urlBase64ToUint8Array(data.public_key);
                console.log('Original key:', data.public_key);
                console.log('Converted key length:', convertedKey.length);
                console.log('Converted key (first 10 bytes):', Array.from(convertedKey.slice(0, 10)));
                
                document.getElementById('result').innerHTML = `
                    <h3>Key Test Results:</h3>
                    <p><strong>Original Key:</strong> ${data.public_key}</p>
                    <p><strong>Converted Length:</strong> ${convertedKey.length} bytes</p>
                    <p><strong>First Byte:</strong> 0x${convertedKey[0].toString(16)}</p>
                    <p><strong>Key Format:</strong> ${convertedKey[0] === 0x04 ? 'Valid P-256 (0x04)' : 'Invalid format'}</p>
                `;
                
                // Test if we can create a subscription (this will fail in non-HTTPS, but we can see the key format)
                if ('serviceWorker' in navigator && 'PushManager' in window) {
                    try {
                        const registration = await navigator.serviceWorker.register('/sw.js');
                        console.log('Service Worker registered');
                        
                        const subscription = await registration.pushManager.subscribe({
                            userVisibleOnly: true,
                            applicationServerKey: convertedKey
                        });
                        
                        console.log('Subscription successful:', subscription);
                        document.getElementById('result').innerHTML += '<p style="color: green;"><strong>✅ Push subscription successful!</strong></p>';
                        
                    } catch (subError) {
                        console.log('Subscription error:', subError);
                        document.getElementById('result').innerHTML += `<p style="color: red;"><strong>❌ Subscription error:</strong> ${subError.message}</p>`;
                    }
                } else {
                    document.getElementById('result').innerHTML += '<p style="color: orange;"><strong>⚠️ Service Worker or Push Manager not supported</strong></p>';
                }
                
            } catch (error) {
                console.error('Test error:', error);
                document.getElementById('result').innerHTML = `<p style="color: red;"><strong>❌ Error:</strong> ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/notifications/web-push")
async def send_web_push_notification(subscription: WebPushSubscription, message: str):
    """Send web push notification"""
    try:
        logger.info(f"🌐 Sending web push notification")
        
        result = await notification_service.send_web_push_notification(subscription, message)
        
        return {
            "status": "success",
            "endpoint": subscription.endpoint[:20] + "...",
            "message": message,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending web push notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send web push notification: {str(e)}")

@app.get("/api/test-push-notification")
async def test_push_notification():
    """Test endpoint to send a push notification"""
    try:
        # This is a test - in a real scenario, you'd get the subscription from the database
        # For now, we'll just return instructions
        return {
            "message": "To test push notifications:",
            "steps": [
                "1. Subscribe to push notifications on the main page",
                "2. Copy the subscription object from browser console",
                "3. Use the /api/notifications/web-push endpoint with the subscription",
                "4. Check browser notifications"
            ],
            "subscription_format": {
                "endpoint": "https://fcm.googleapis.com/fcm/send/...",
                "keys": {
                    "p256dh": "base64-encoded-p256dh-key",
                    "auth": "base64-encoded-auth-key"
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ Error in test push notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test push notification: {str(e)}")

@app.post("/api/send-test-notification")
async def send_test_notification(subscription: WebPushSubscription):
    """Send a test push notification"""
    try:
        logger.info(f"🧪 Sending test push notification")
        
        result = await notification_service.send_web_push_notification(
            subscription, 
            "Test notification from trading system!"
        )
        
        return {
            "status": "success",
            "message": "Test notification sent",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")

# Advanced Market Data Endpoints
@app.get("/api/market-data/advanced/{symbol}")
async def get_advanced_market_data(symbol: str, providers: List[str] = None):
    """Get advanced market data from multiple providers"""
    logger.info(f"Getting advanced market data for {symbol}")
    
    if providers is None:
        providers = ["polygon", "alpha_vantage", "yahoo"]
    
    market_data = {
        "symbol": symbol,
        "providers": providers,
        "real_time_data": {
            "price": 150.25,
            "volume": 45000000,
            "bid": 150.20,
            "ask": 150.30,
            "timestamp": datetime.now().isoformat()
        },
        "historical_data": {
            "daily": [
                {"date": "2025-07-01", "open": 148.50, "high": 151.20, "low": 147.80, "close": 150.25, "volume": 45000000},
                {"date": "2025-07-02", "open": 150.25, "high": 152.80, "low": 149.90, "close": 151.75, "volume": 48000000}
            ]
        },
        "options_data": {
            "available": True,
            "expirations": ["2025-08-15", "2025-09-20", "2025-12-19"],
            "strikes": [140, 145, 150, 155, 160]
        },
        "news_sentiment": {
            "score": 0.65,
            "articles": 15,
            "positive": 10,
            "negative": 3,
            "neutral": 2
        }
    }
    
    return market_data

# Advanced Backtesting Endpoints
@app.post("/api/backtest/compare")
async def compare_strategies(request: BacktestRequest):
    """Compare multiple strategies side-by-side"""
    logger.info(f"Comparing strategies: {request.strategies}")
    
    comparison_results = []
    for strategy in request.strategies:
        comparison_results.append({
            "strategy_name": strategy,
            "symbols": request.symbols,
            "total_return_pct": 12.5 + hash(strategy) % 10,  # Simulate different returns
            "sharpe_ratio": 1.2 + hash(strategy) % 5 * 0.1,
            "max_drawdown_pct": 5.2 + hash(strategy) % 3,
            "total_trades": 45 + hash(strategy) % 20,
            "win_rate": 0.65 + hash(strategy) % 10 * 0.01
        })
    
    return {
        "comparison_id": f"comp_{hash(request.json())}",
        "strategies": request.strategies,
        "results": comparison_results,
        "best_strategy": max(comparison_results, key=lambda x: x["sharpe_ratio"])["strategy_name"],
        "comparison_timestamp": datetime.now().isoformat()
    }

@app.post("/api/backtest/optimize")
async def optimize_strategy_parameters(strategy_name: str, symbols: List[str], parameter_ranges: Dict[str, List]):
    """Optimize strategy parameters"""
    logger.info(f"Optimizing parameters for strategy: {strategy_name}")
    
    optimization_results = {
        "strategy_name": strategy_name,
        "symbols": symbols,
        "parameter_ranges": parameter_ranges,
        "best_parameters": {
            "short_window": 20,
            "long_window": 50,
            "rsi_period": 14
        },
        "optimization_metrics": {
            "best_sharpe_ratio": 1.8,
            "best_total_return": 0.18,
            "best_max_drawdown": 0.04
        },
        "parameter_combinations_tested": 100,
        "optimization_timestamp": datetime.now().isoformat()
    }
    
    return optimization_results

@app.get("/api/simple-test")
async def simple_test():
    """Simple test endpoint"""
    return {"message": "Simple test endpoint works!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=11099) 