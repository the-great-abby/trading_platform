#!/usr/bin/env python3
"""
Trading CLI - Command line interface for internal operations
Used for interacting with microservices from within the Docker network
"""

import argparse
import requests
import json
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

class TradingCLI:
    def __init__(self):
        self.api_gateway_url = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
        self.trading_service_url = os.getenv("TRADING_SERVICE_URL", "http://trading-service:8001")
        self.market_data_service_url = os.getenv("MARKET_DATA_SERVICE_URL", "http://market-data-service:8002")
        self.risk_service_url = os.getenv("RISK_SERVICE_URL", "http://risk-service:8003")
        self.portfolio_service_url = os.getenv("PORTFOLIO_SERVICE_URL", "http://portfolio-service:8004")
        self.strategy_service_url = os.getenv("STRATEGY_SERVICE_URL", "http://strategy-service:8005")
        self.order_service_url = os.getenv("ORDER_SERVICE_URL", "http://order-service:8006")
        self.analytics_service_url = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8007")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://user-service:8008")

    def make_request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to service"""
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return {"error": str(e)}

    def check_health(self, service: str = "all"):
        """Check health of services"""
        services = {
            "api-gateway": self.api_gateway_url,
            "trading": self.trading_service_url,
            "market-data": self.market_data_service_url,
            "risk": self.risk_service_url,
            "portfolio": self.portfolio_service_url,
            "strategy": self.strategy_service_url,
            "order": self.order_service_url,
            "analytics": self.analytics_service_url,
            "user": self.user_service_url
        }
        
        if service == "all":
            for name, url in services.items():
                status = self.make_request("GET", f"{url}/health")
                print(f"{name}: {status.get('status', 'unknown')}")
        else:
            if service in services:
                status = self.make_request("GET", f"{services[service]}/health")
                print(f"{service}: {status.get('status', 'unknown')}")
            else:
                print(f"Unknown service: {service}")

    def get_portfolio(self):
        """Get portfolio summary"""
        data = self.make_request("GET", f"{self.portfolio_service_url}/portfolio/summary")
        if "error" not in data:
            print("Portfolio Summary:")
            print(f"  Total Value: ${data.get('total_value', 0):,.2f}")
            print(f"  Cash: ${data.get('cash', 0):,.2f}")
            print(f"  Total P&L: ${data.get('total_pnl', 0):,.2f} ({data.get('total_pnl_percentage', 0):.2f}%)")
            print(f"  Daily P&L: ${data.get('daily_pnl', 0):,.2f}")
            print(f"  Max Drawdown: {data.get('max_drawdown', 0):.2%}")
            print(f"  Positions: {data.get('num_positions', 0)}")
        else:
            print(f"Error: {data['error']}")

    def get_strategies(self):
        """Get available strategies"""
        data = self.make_request("GET", f"{self.strategy_service_url}/strategies")
        if "error" not in data:
            print("Available Strategies:")
            for strategy in data.get('strategies', []):
                print(f"  {strategy['name']}: {strategy['display_name']} - {strategy['description']}")
                print(f"    Active: {strategy['is_active']}")
        else:
            print(f"Error: {data['error']}")

    def get_market_data(self, symbol: str):
        """Get market data for symbol"""
        data = self.make_request("GET", f"{self.market_data_service_url}/market-data/current/{symbol}")
        if "error" not in data:
            print(f"Market Data for {symbol}:")
            print(f"  Price: ${data.get('price', 0):.2f}")
            print(f"  Change: ${data.get('change', 0):.2f} ({data.get('change_percent', 0):.2f}%)")
            print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
        else:
            print(f"Error: {data['error']}")

    def get_risk_assessment(self):
        """Get portfolio risk assessment"""
        # Mock portfolio data for risk assessment
        portfolio_data = {
            "portfolio_value": 200000,
            "cash": 50000,
            "positions": [
                {"value": 75000},
                {"value": 75000}
            ]
        }
        
        data = self.make_request("POST", f"{self.risk_service_url}/risk/assess-portfolio", portfolio_data)
        if "error" not in data:
            print("Risk Assessment:")
            print(f"  Risk Score: {data.get('total_risk_score', 0):.1f}/100")
            print(f"  Max Position Size: ${data.get('max_position_size', 0):,.2f}")
            print(f"  Recommended Cash Reserve: ${data.get('recommended_cash_reserve', 0):,.2f}")
        else:
            print(f"Error: {data['error']}")

    def get_orders(self, status: Optional[str] = None):
        """Get orders"""
        url = f"{self.order_service_url}/orders"
        if status:
            url += f"?status={status}"
        
        data = self.make_request("GET", url)
        if "error" not in data:
            print("Orders:")
            for order in data.get('orders', []):
                print(f"  {order['order_id']}: {order['side']} {order['quantity']} {order['symbol']} @ {order.get('price', 'market')}")
                print(f"    Status: {order['status']}")
        else:
            print(f"Error: {data['error']}")

    def get_analytics(self, report_type: str = "performance"):
        """Get analytics reports"""
        if report_type == "performance":
            data = self.make_request("GET", f"{self.analytics_service_url}/analytics/performance")
        elif report_type == "risk":
            data = self.make_request("GET", f"{self.analytics_service_url}/analytics/risk")
        elif report_type == "trades":
            data = self.make_request("GET", f"{self.analytics_service_url}/analytics/trades")
        else:
            print(f"Unknown report type: {report_type}")
            return
        
        if "error" not in data:
            print(f"{report_type.title()} Analytics:")
            for key, value in data.items():
                if key not in ["period", "symbol"]:
                    if isinstance(value, float):
                        print(f"  {key}: {value:.4f}")
                    else:
                        print(f"  {key}: {value}")
        else:
            print(f"Error: {data['error']}")

    def execute_trade(self, symbol: str, side: str, quantity: float, price: Optional[float] = None):
        """Execute a trade"""
        trade_data = {
            "symbol": symbol,
            "action": side,
            "quantity": quantity,
            "price": price
        }
        
        data = self.make_request("POST", f"{self.trading_service_url}/trades/execute", trade_data)
        if "error" not in data:
            print(f"Trade executed: {data.get('message', 'Success')}")
            print(f"Trade ID: {data.get('trade_id', 'N/A')}")
        else:
            print(f"Error: {data['error']}")

    def generate_signal(self, strategy: str, symbol: str):
        """Generate trading signal"""
        signal_data = {
            "strategy_name": strategy,
            "symbol": symbol,
            "market_data": {
                "close": 150.0,
                "volume": 1000000,
                "high": 155.0,
                "low": 145.0
            }
        }
        
        data = self.make_request("POST", f"{self.strategy_service_url}/strategies/{strategy}/signal", signal_data)
        if "error" not in data:
            print(f"Signal generated for {symbol} using {strategy}:")
            print(f"  Signal: {data.get('signal', 'N/A')}")
            print(f"  Confidence: {data.get('confidence', 0):.2f}")
            print(f"  Reason: {data.get('reason', 'N/A')}")
        else:
            print(f"Error: {data['error']}")

def main():
    parser = argparse.ArgumentParser(description="Trading Bot CLI for internal operations")
    parser.add_argument("command", choices=[
        "health", "portfolio", "strategies", "market-data", "risk", 
        "orders", "analytics", "trade", "signal"
    ], help="Command to execute")
    
    parser.add_argument("--service", default="all", help="Service name for health check")
    parser.add_argument("--symbol", help="Symbol for market data or trading")
    parser.add_argument("--side", choices=["buy", "sell"], help="Trade side")
    parser.add_argument("--quantity", type=float, help="Trade quantity")
    parser.add_argument("--price", type=float, help="Trade price")
    parser.add_argument("--strategy", help="Strategy name for signal generation")
    parser.add_argument("--status", help="Order status filter")
    parser.add_argument("--report", default="performance", help="Analytics report type")
    
    args = parser.parse_args()
    
    cli = TradingCLI()
    
    if args.command == "health":
        cli.check_health(args.service)
    elif args.command == "portfolio":
        cli.get_portfolio()
    elif args.command == "strategies":
        cli.get_strategies()
    elif args.command == "market-data":
        if not args.symbol:
            print("Error: --symbol is required for market-data command")
            sys.exit(1)
        cli.get_market_data(args.symbol)
    elif args.command == "risk":
        cli.get_risk_assessment()
    elif args.command == "orders":
        cli.get_orders(args.status)
    elif args.command == "analytics":
        cli.get_analytics(args.report)
    elif args.command == "trade":
        if not all([args.symbol, args.side, args.quantity]):
            print("Error: --symbol, --side, and --quantity are required for trade command")
            sys.exit(1)
        cli.execute_trade(args.symbol, args.side, args.quantity, args.price)
    elif args.command == "signal":
        if not all([args.strategy, args.symbol]):
            print("Error: --strategy and --symbol are required for signal command")
            sys.exit(1)
        cli.generate_signal(args.strategy, args.symbol)

if __name__ == "__main__":
    main() 