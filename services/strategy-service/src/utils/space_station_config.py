# Space Trading Station Configuration
# This file contains theme and AI assistant information for the Space Trading Station

# AI Assistant Configuration
AI_ASSISTANT_NAME = "ORION"
AI_ASSISTANT_ROLE = "Mission Control AI Navigator"
AI_ASSISTANT_DESCRIPTION = "AI co-pilot for Space Trading Station operations"

# Space Trading Station Theme
STATION_NAME = "Space Trading Station"
STATION_THEME = "space_trading_station"
STATION_MOTTO = "Navigating the markets from orbit"

# Mission Control Components
MISSION_CONTROL_COMPONENTS = {
    "gateway": "Mission Control Gateway",
    "trading": "Trading Service",
    "market_data": "Satellite Data Service", 
    "risk": "Risk Management Service",
    "portfolio": "Portfolio Service",
    "ai_strategies": "AI Navigation Systems",
    "order_management": "Order Management Service",
    "analytics": "Analytics Service",
    "user_management": "User Management Service"
}

# Space Station Operations
OPERATIONS = {
    "backtesting": "Orbital Backtesting",
    "deployment": "Space Station Deployment",
    "monitoring": "Mission Control Monitoring",
    "data_fetch": "Satellite Data Fetch",
    "strategy_testing": "AI Navigation System Testing"
}

# AI Navigation Systems
AI_NAVIGATION_SYSTEMS = [
    "RSI_AI_Enhanced",
    "BollingerBands_AI_Enhanced", 
    "MACD_AI_Enhanced",
    "SMACrossover_AI_Enhanced",
    "NewsEnhanced"
]

# Mission Control Commands
MISSION_COMMANDS = {
    "status": "Check Space Station Status",
    "deploy": "Deploy Space Station Modules",
    "backtest": "Launch Orbital Backtest",
    "monitor": "Access Mission Control Dashboard",
    "logs": "View Space Station Logs"
}

def get_ai_assistant_info():
    """Get AI assistant configuration"""
    return {
        "name": AI_ASSISTANT_NAME,
        "role": AI_ASSISTANT_ROLE,
        "description": AI_ASSISTANT_DESCRIPTION
    }

def get_station_info():
    """Get Space Trading Station information"""
    return {
        "name": STATION_NAME,
        "theme": STATION_THEME,
        "motto": STATION_MOTTO
    }

def get_mission_control_components():
    """Get Mission Control component mappings"""
    return MISSION_CONTROL_COMPONENTS

def get_operations():
    """Get Space Station operations"""
    return OPERATIONS

def get_ai_navigation_systems():
    """Get available AI Navigation Systems"""
    return AI_NAVIGATION_SYSTEMS

def get_mission_commands():
    """Get Mission Control commands"""
    return MISSION_COMMANDS 