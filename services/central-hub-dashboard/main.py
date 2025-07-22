#!/usr/bin/env python3
"""
Central Hub Dashboard - Space Trading Station
Single entry point for all trading system services and dashboards
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Space Trading Station - Central Hub",
    description="Central navigation hub for all trading system services",
    version="1.0.0"
)

# Configuration
class HubConfig:
    """Central hub configuration"""
    # Service URLs (these would be environment variables in production)
    TRADING_DASHBOARD_URL = os.getenv("TRADING_DASHBOARD_URL", "http://trading-dashboard-service:80")
    HEALTH_DASHBOARD_URL = os.getenv("HEALTH_DASHBOARD_URL", "http://health-dashboard:80")
    PERFORMANCE_DASHBOARD_URL = os.getenv("PERFORMANCE_DASHBOARD_URL", "http://performance-dashboard:80")
    RSS_DASHBOARD_URL = os.getenv("RSS_DASHBOARD_URL", "http://rss-dashboard:80")
    GATEWAY_URL = os.getenv("GATEWAY_URL", "http://trading-gateway:80")
    BACKTEST_API_URL = os.getenv("BACKTEST_API_URL", "http://backtest-api:8000")
    ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000")
    AI_ANALYSIS_URL = os.getenv("AI_ANALYSIS_URL", "http://ai-analysis-service:11085")
    
    # Service status check timeout
    STATUS_CHECK_TIMEOUT = 5.0

config = HubConfig()

# Service definitions
SERVICES = {
    "trading": {
        "name": "📊 Trading Dashboard",
        "description": "Main trading interface with portfolio, trades, and positions",
        "url": config.TRADING_DASHBOARD_URL,
        "category": "Core Trading",
        "icon": "📈",
        "color": "#2E86AB"
    },
    "health": {
        "name": "🏥 Health Dashboard", 
        "description": "System health monitoring and service status",
        "url": config.HEALTH_DASHBOARD_URL,
        "category": "Monitoring",
        "icon": "🔍",
        "color": "#A23B72"
    },
    "performance": {
        "name": "📈 Performance Dashboard",
        "description": "Trading performance metrics and analytics",
        "url": config.PERFORMANCE_DASHBOARD_URL,
        "category": "Analytics",
        "icon": "📊",
        "color": "#F18F01"
    },
    "rss": {
        "name": "📡 RSS Feed Dashboard",
        "description": "Real-time RSS feed monitoring and alerts",
        "url": config.RSS_DASHBOARD_URL,
        "category": "Monitoring",
        "icon": "📡",
        "color": "#C73E1D"
    },
    "ai_analysis": {
        "name": "🤖 AI Analysis Service",
        "description": "AI-powered stock recommendations and analysis",
        "url": config.AI_ANALYSIS_URL,
        "category": "AI & Analytics",
        "icon": "🤖",
        "color": "#6C5CE7"
    },
    "reports": {
        "name": "📋 Backtest Reports",
        "description": "HTML reports and analysis from backtest runs",
        "url": f"{config.GATEWAY_URL}/reports",
        "category": "Analytics",
        "icon": "📋",
        "color": "#11998e"
    },
    "gateway": {
        "name": "🌐 API Gateway",
        "description": "Central API gateway and service documentation",
        "url": config.GATEWAY_URL,
        "category": "API",
        "icon": "🌐",
        "color": "#6C5CE7"
    },
    "backtest": {
        "name": "🧪 Backtest API",
        "description": "Backtest request form and results",
        "url": config.BACKTEST_API_URL,
        "category": "Trading",
        "icon": "🧪",
        "color": "#00B894"
    },
    "analytics": {
        "name": "📊 Analytics Service",
        "description": "Advanced analytics and data processing",
        "url": config.ANALYTICS_SERVICE_URL,
        "category": "Analytics",
        "icon": "📊",
        "color": "#FD79A8"
    }
}

async def check_service_status(service_id: str, service_info: Dict) -> Dict:
    """Check if a service is available"""
    try:
        async with httpx.AsyncClient(timeout=config.STATUS_CHECK_TIMEOUT) as client:
            response = await client.get(f"{service_info['url']}/health")
            return {
                "id": service_id,
                "status": "online" if response.status_code == 200 else "offline",
                "response_time": response.elapsed.total_seconds(),
                "last_check": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.warning(f"Service {service_id} check failed: {e}")
        return {
            "id": service_id,
            "status": "offline",
            "response_time": None,
            "last_check": datetime.utcnow().isoformat()
        }

@app.get("/", response_class=HTMLResponse)
async def hub_dashboard():
    """Main hub dashboard page"""
    
    # Check service statuses
    statuses = {}
    for service_id, service_info in SERVICES.items():
        status = await check_service_status(service_id, service_info)
        statuses[service_id] = status
    
    # Group services by category
    categories = {}
    for service_id, service_info in SERVICES.items():
        category = service_info["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append({
            "id": service_id,
            **service_info,
            "status": statuses.get(service_id, {}).get("status", "unknown")
        })
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Space Trading Station - Central Hub</title>
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
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}

            .header {{
                background: linear-gradient(135deg, #2c3e50, #34495e);
                color: white;
                padding: 40px;
                text-align: center;
            }}

            .header h1 {{
                font-size: 3rem;
                margin-bottom: 10px;
                font-weight: 300;
            }}

            .header .subtitle {{
                font-size: 1.2rem;
                opacity: 0.9;
                margin-bottom: 20px;
            }}

            .status-summary {{
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 20px;
            }}

            .status-item {{
                background: rgba(255,255,255,0.1);
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 0.9rem;
            }}

            .content {{
                padding: 40px;
            }}

            .category-section {{
                margin-bottom: 40px;
            }}

            .category-title {{
                font-size: 1.8rem;
                color: #2c3e50;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #ecf0f1;
            }}

            .services-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
            }}

            .service-card {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                border-left: 5px solid;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                position: relative;
                overflow: hidden;
            }}

            .service-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            }}

            .service-card.online {{
                border-left-color: #27ae60;
            }}

            .service-card.offline {{
                border-left-color: #e74c3c;
                opacity: 0.7;
            }}

            .service-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}

            .service-title {{
                font-size: 1.3rem;
                font-weight: 600;
                color: #2c3e50;
            }}

            .service-icon {{
                font-size: 2rem;
            }}

            .service-description {{
                color: #7f8c8d;
                margin-bottom: 15px;
                line-height: 1.5;
            }}

            .service-status {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                margin-bottom: 15px;
            }}

            .status-online {{
                background: #d5f4e6;
                color: #27ae60;
            }}

            .status-offline {{
                background: #fadbd8;
                color: #e74c3c;
            }}

            .service-link {{
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 500;
                transition: background 0.3s ease;
            }}

            .service-link:hover {{
                background: #2980b9;
            }}

            .service-link.offline {{
                background: #95a5a6;
                cursor: not-allowed;
            }}

            .service-link.offline:hover {{
                background: #7f8c8d;
            }}

            .footer {{
                background: #ecf0f1;
                padding: 30px;
                text-align: center;
                color: #7f8c8d;
            }}

            .quick-actions {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 12px;
                margin-bottom: 30px;
            }}

            .quick-actions h3 {{
                color: #2c3e50;
                margin-bottom: 20px;
                font-size: 1.5rem;
            }}

            .action-buttons {{
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
            }}

            .action-btn {{
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                transition: background 0.3s ease;
                text-decoration: none;
                display: inline-block;
            }}

            .action-btn:hover {{
                background: #2980b9;
            }}

            .action-btn.secondary {{
                background: #95a5a6;
            }}

            .action-btn.secondary:hover {{
                background: #7f8c8d;
            }}

            @media (max-width: 768px) {{
                .services-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .header h1 {{
                    font-size: 2rem;
                }}
                
                .action-buttons {{
                    flex-direction: column;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Space Trading Station</h1>
                <div class="subtitle">Central Hub Dashboard</div>
                <div class="status-summary">
                    <div class="status-item">
                        📊 {len([s for s in statuses.values() if s.get('status') == 'online'])} Services Online
                    </div>
                    <div class="status-item">
                        ⚠️ {len([s for s in statuses.values() if s.get('status') == 'offline'])} Services Offline
                    </div>
                    <div class="status-item">
                        🕒 Last Updated: {datetime.now().strftime('%H:%M:%S')}
                    </div>
                </div>
            </div>

            <div class="content">
                <div class="quick-actions">
                    <h3>⚡ Quick Actions</h3>
                    <div class="action-buttons">
                        <a href="{SERVICES['trading']['url']}" class="action-btn" target="_blank">
                            📊 Open Trading Dashboard
                        </a>
                        <a href="{SERVICES['reports']['url']}" class="action-btn" target="_blank">
                            📋 View Reports
                        </a>
                        <a href="{SERVICES['backtest']['url']}" class="action-btn" target="_blank">
                            🧪 Run Backtest
                        </a>
                        <a href="{SERVICES['health']['url']}" class="action-btn secondary" target="_blank">
                            🏥 System Health
                        </a>
                    </div>
                </div>

                {_generate_category_sections(categories)}
            </div>

            <div class="footer">
                <p>Space Trading Station Central Hub • Built for Algorithmic Trading Excellence</p>
                <p style="margin-top: 10px; font-size: 0.9rem;">
                    Auto-refresh every 30 seconds • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </div>

        <script>
            // Auto-refresh every 30 seconds
            setTimeout(() => {{
                window.location.reload();
            }}, 30000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

def _generate_category_sections(categories: Dict) -> str:
    """Generate HTML for category sections"""
    html = ""
    
    for category, services in categories.items():
        html += f"""
        <div class="category-section">
            <h2 class="category-title">{category}</h2>
            <div class="services-grid">
        """
        
        for service in services:
            status_class = "online" if service["status"] == "online" else "offline"
            status_text = "Online" if service["status"] == "online" else "Offline"
            
            html += f"""
            <div class="service-card {status_class}">
                <div class="service-header">
                    <div class="service-title">{service['name']}</div>
                    <div class="service-icon">{service['icon']}</div>
                </div>
                <div class="service-description">{service['description']}</div>
                <div class="service-status status-{status_class}">{status_text}</div>
                <a href="{service['url']}" class="service-link {status_class}" target="_blank">
                    {'Open Service' if service['status'] == 'online' else 'Service Offline'}
                </a>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
    
    return html

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "central-hub-dashboard",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/services")
async def get_services():
    """Get all services with their status"""
    statuses = {}
    for service_id, service_info in SERVICES.items():
        status = await check_service_status(service_id, service_info)
        statuses[service_id] = {
            **service_info,
            "status": status
        }
    
    return {
        "services": statuses,
        "total": len(SERVICES),
        "online": len([s for s in statuses.values() if s["status"]["status"] == "online"]),
        "offline": len([s for s in statuses.values() if s["status"]["status"] == "offline"])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 