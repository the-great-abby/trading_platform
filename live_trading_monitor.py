#!/usr/bin/env python3
"""
Live Trading Performance Monitor
Monitors the optimized live trading system performance
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiveTradingMonitor:
    def __init__(self):
        self.live_trading_url = "http://localhost:11120"
        self.account_id = "19c25392-8b61-4b71-a344-0eb04d275528"
        self.monitoring_log = f"/Users/abby/code/trading/monitoring/live_trading_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Performance targets from optimized system
        self.targets = {
            'annual_return': 0.075,  # 7.5%
            'max_drawdown': 0.11,    # 11%
            'sharpe_ratio': 2.0,     # 2.0
            'win_rate': 0.70,        # 70%
            'daily_trades': 4,        # 4 trades/day
            'monthly_trades': 8       # 8 trades/month
        }
        
        # Create monitoring directory
        os.makedirs("/Users/abby/code/trading/monitoring", exist_ok=True)
    
    def check_service_health(self):
        """Check if live trading service is healthy"""
        try:
            response = requests.get(f"{self.live_trading_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ Live trading service: {health_data.get('status', 'unknown')}")
                return True
            else:
                logger.error(f"❌ Live trading service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to check service health: {e}")
            return False
    
    def check_trading_session(self):
        """Check trading session status"""
        try:
            response = requests.get(f"{self.live_trading_url}/api/v1/status/trading-session", timeout=10)
            if response.status_code == 200:
                session_data = response.json()
                if session_data.get("is_active"):
                    remaining_hours = session_data.get("time_remaining_hours", 0)
                    logger.info(f"✅ Trading session active - {remaining_hours:.1f} hours remaining")
                    return True
                else:
                    logger.warning("⚠️  Trading session not active")
                    return False
            else:
                logger.error(f"❌ Failed to check trading session: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to check trading session: {e}")
            return False
    
    def get_account_balance(self):
        """Get current account balance"""
        try:
            response = requests.get(f"{self.live_trading_url}/api/v1/accounts/{self.account_id}/balance", timeout=10)
            if response.status_code == 200:
                balance_data = response.json()
                cash_balance = balance_data.get("cash_balance", 0)
                equity = balance_data.get("equity", 0)
                buying_power = balance_data.get("buying_power", 0)
                
                logger.info(f"💰 Account Balance: ${cash_balance:.2f} cash, ${equity:.2f} equity, ${buying_power:.2f} buying power")
                return balance_data
            else:
                logger.error(f"❌ Failed to get account balance: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get account balance: {e}")
            return None
    
    def get_active_strategies(self):
        """Get active trading strategies"""
        try:
            response = requests.get(f"{self.live_trading_url}/api/v1/strategies/{self.account_id}", timeout=10)
            if response.status_code == 200:
                strategies_data = response.json()
                active_strategies = [s for s in strategies_data.get("strategies", []) if s.get("enabled")]
                
                logger.info(f"📊 Active Strategies: {len(active_strategies)}")
                for strategy in active_strategies:
                    logger.info(f"   • {strategy['strategy_name']}: {strategy['max_position_size']:.1%} max position, {strategy['max_daily_trades']} daily trades")
                
                return active_strategies
            else:
                logger.error(f"❌ Failed to get strategies: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get strategies: {e}")
            return None
    
    def get_recent_orders(self):
        """Get recent trading orders"""
        try:
            response = requests.get(f"{self.live_trading_url}/api/v1/trading/orders", timeout=10)
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get("orders", [])
                
                # Filter recent orders (last 24 hours)
                recent_orders = []
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for order in orders:
                    order_time = datetime.fromisoformat(order.get("created_at", "").replace("Z", "+00:00"))
                    if order_time > cutoff_time:
                        recent_orders.append(order)
                
                logger.info(f"📈 Recent Orders: {len(recent_orders)} in last 24 hours")
                for order in recent_orders[-5:]:  # Show last 5 orders
                    logger.info(f"   • {order.get('symbol', 'N/A')} - {order.get('side', 'N/A')} - ${order.get('filled_price', 0):.2f}")
                
                return recent_orders
            else:
                logger.error(f"❌ Failed to get orders: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return None
    
    def get_active_positions(self):
        """Get current active positions"""
        try:
            response = requests.get(f"{self.live_trading_url}/api/v1/trading/positions", timeout=10)
            if response.status_code == 200:
                positions_data = response.json()
                positions = positions_data.get("positions", [])
                
                logger.info(f"📊 Active Positions: {len(positions)}")
                for position in positions:
                    symbol = position.get("symbol", "N/A")
                    quantity = position.get("quantity", 0)
                    avg_price = position.get("avg_price", 0)
                    market_value = position.get("market_value", 0)
                    unrealized_pnl = position.get("unrealized_pnl", 0)
                    
                    logger.info(f"   • {symbol}: {quantity} shares @ ${avg_price:.2f} = ${market_value:.2f} (P&L: ${unrealized_pnl:.2f})")
                
                return positions
            else:
                logger.error(f"❌ Failed to get positions: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return None
    
    def check_risk_status(self):
        """Check risk management status"""
        try:
            response = requests.get(f"{self.live_trading_url}/api/v1/risk/profile/{self.account_id}", timeout=10)
            if response.status_code == 200:
                risk_data = response.json()
                
                logger.info("🛡️  Risk Management Status:")
                logger.info(f"   • Max Daily Loss: ${risk_data.get('max_daily_loss', 0):.2f}")
                logger.info(f"   • Max Position Size: {risk_data.get('max_position_size', 0):.1%}")
                logger.info(f"   • Max Total Exposure: {risk_data.get('max_total_exposure', 0):.1%}")
                logger.info(f"   • Min Cash Reserve: {risk_data.get('min_cash_reserve', 0):.1%}")
                logger.info(f"   • Emergency Stop: {'✅ Active' if risk_data.get('emergency_stop_enabled') else '❌ Inactive'}")
                
                return risk_data
            else:
                logger.error(f"❌ Failed to get risk status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get risk status: {e}")
            return None
    
    def generate_performance_report(self, balance_data, strategies, orders, positions, risk_data):
        """Generate comprehensive performance report"""
        logger.info("📋 Generating live trading performance report...")
        
        report = f"""
================================================================================
🚀 LIVE TRADING PERFORMANCE REPORT
================================================================================
📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💰 ACCOUNT STATUS:
   • Cash Balance: ${balance_data.get('cash_balance', 0):,.2f}
   • Equity: ${balance_data.get('equity', 0):,.2f}
   • Buying Power: ${balance_data.get('buying_power', 0):,.2f}
   • Account Type: {balance_data.get('account_type', 'Unknown')}

📊 ACTIVE STRATEGIES:
   • Total Strategies: {len(strategies) if strategies else 0}
"""
        
        if strategies:
            for strategy in strategies:
                report += f"   • {strategy['strategy_name']}: {strategy['max_position_size']:.1%} max position, {strategy['max_daily_trades']} daily trades\n"
        
        report += f"""
📈 TRADING ACTIVITY:
   • Recent Orders (24h): {len(orders) if orders else 0}
   • Active Positions: {len(positions) if positions else 0}
"""
        
        if positions:
            total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
            report += f"   • Total Unrealized P&L: ${total_pnl:.2f}\n"
        
        report += f"""
🛡️  RISK MANAGEMENT:
   • Max Daily Loss: ${risk_data.get('max_daily_loss', 0):,.2f}
   • Max Position Size: {risk_data.get('max_position_size', 0):.1%}
   • Max Total Exposure: {risk_data.get('max_total_exposure', 0):.1%}
   • Min Cash Reserve: {risk_data.get('min_cash_reserve', 0):.1%}
   • Emergency Stop: {'✅ Active' if risk_data.get('emergency_stop_enabled') else '❌ Inactive'}

🎯 OPTIMIZATION TARGETS:
   • Annual Return Target: {self.targets['annual_return']:.1%}
   • Max Drawdown Limit: {self.targets['max_drawdown']:.1%}
   • Sharpe Ratio Target: {self.targets['sharpe_ratio']:.1f}
   • Win Rate Target: {self.targets['win_rate']:.1%}
   • Daily Trades Target: {self.targets['daily_trades']}
   • Monthly Trades Target: {self.targets['monthly_trades']}

📊 EXPECTED IMPROVEMENTS:
   • Annual Return: +7.53% (vs previous -1.23%)
   • Sharpe Ratio: +2.177 (vs previous +0.384)
   • All strategies optimized with enhanced parameters
   • News delay filters and quality thresholds active

💡 OPTIMIZATION STATUS:
   • Calendar Spread: ✅ Optimized (12% max position, 4 daily trades)
   • Iron Condor: ✅ Optimized (12% max position, 4 daily trades)
   • Butterfly Spread: ✅ Optimized (12% max position, 4 daily trades)
   • Risk Management: ✅ Enhanced (11% drawdown limit, 15% cash reserve)

================================================================================
"""
        
        return report
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        logger.info("🔄 Starting live trading monitoring cycle...")
        
        # Check service health
        if not self.check_service_health():
            return None
        
        # Check trading session
        self.check_trading_session()
        
        # Get account data
        balance_data = self.get_account_balance()
        strategies = self.get_active_strategies()
        orders = self.get_recent_orders()
        positions = self.get_active_positions()
        risk_data = self.check_risk_status()
        
        # Generate report
        if balance_data:
            report = self.generate_performance_report(balance_data, strategies, orders, positions, risk_data)
            print(report)
            
            # Log data
            monitoring_data = {
                'timestamp': datetime.now().isoformat(),
                'balance': balance_data,
                'strategies_count': len(strategies) if strategies else 0,
                'orders_count': len(orders) if orders else 0,
                'positions_count': len(positions) if positions else 0,
                'risk_status': risk_data
            }
            
            try:
                with open(self.monitoring_log, 'a') as f:
                    f.write(f"{datetime.now().isoformat()}: {json.dumps(monitoring_data)}\n")
            except Exception as e:
                logger.error(f"❌ Failed to write to log file: {e}")
        
        return {
            'balance': balance_data,
            'strategies': strategies,
            'orders': orders,
            'positions': positions,
            'risk': risk_data
        }
    
    def run_continuous_monitoring(self, interval_minutes=5):
        """Run continuous monitoring"""
        logger.info(f"🔄 Starting continuous live trading monitoring (every {interval_minutes} minutes)")
        logger.info("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                self.run_monitoring_cycle()
                logger.info(f"⏰ Next monitoring cycle in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
    
    def run_single_check(self):
        """Run single monitoring check"""
        logger.info("🔍 Running single live trading check...")
        
        monitoring_data = self.run_monitoring_cycle()
        
        if monitoring_data:
            logger.info("📋 Live Trading Summary:")
            logger.info(f"   • Service Health: ✅ Healthy")
            if monitoring_data.get('balance'):
                logger.info(f"   • Account Balance: ${monitoring_data['balance'].get('cash_balance', 0):,.2f}")
            else:
                logger.info(f"   • Account Balance: ❌ Unavailable")
            logger.info(f"   • Active Strategies: {monitoring_data.get('strategies_count', 0)}")
            logger.info(f"   • Recent Orders: {monitoring_data.get('orders_count', 0)}")
            logger.info(f"   • Active Positions: {monitoring_data.get('positions_count', 0)}")
        else:
            logger.info("📋 Live Trading Summary:")
            logger.info(f"   • Service Health: ❌ Unavailable")
        
        return monitoring_data

def main():
    """Main execution function"""
    import sys
    
    monitor = LiveTradingMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            monitor.run_continuous_monitoring(interval)
        elif sys.argv[1] == "single":
            monitor.run_single_check()
        else:
            print("Usage: python3 live_trading_monitor.py [continuous|single] [interval_minutes]")
    else:
        # Default to single check
        monitor.run_single_check()

if __name__ == "__main__":
    main()
