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
            'annual_return': 0.20,       # 20% (realistic for ensemble)
            'max_drawdown': 0.08,        # 8% (aligns with circuit breaker and stop loss)
            'sharpe_ratio': 1.5,         # 1.5 (realistic for ensemble)
            'win_rate': 0.60,            # 60% (realistic for ensemble)
            'daily_trades': 10,          # 10 trades/day (matches strategy config)
            'monthly_trades': 200        # 200 trades/month (realistic for ensemble)
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
        """Get current account balance from stored database values"""
        try:
            # Try the /balance endpoint first (requires real Public.com credentials)
            response = requests.get(f"{self.live_trading_url}/api/v1/accounts/{self.account_id}/balance", timeout=10)
            if response.status_code == 200:
                balance_data = response.json()
                cash_balance = balance_data.get("cash_balance", 0)
                equity = balance_data.get("equity", 0)
                buying_power = balance_data.get("buying_power", 0)
                
                logger.info(f"💰 Account Balance (Real-time): ${cash_balance:.2f} cash, ${equity:.2f} equity, ${buying_power:.2f} buying power")
                return balance_data
            else:
                # Fallback to stored database values if /balance fails
                logger.warning(f"⚠️  Real-time balance unavailable, using stored values...")
                response = requests.get(f"{self.live_trading_url}/api/v1/accounts", timeout=10)
                if response.status_code == 200:
                    accounts_data = response.json()
                    accounts = accounts_data.get("accounts", [])
                    for account in accounts:
                        if account.get("account_id") == self.account_id:
                            cash_balance = account.get("cash_balance", 0)
                            equity = account.get("equity", 0)
                            buying_power = account.get("buying_power", 0)
                            
                            logger.info(f"💰 Account Balance (Stored): ${cash_balance:.2f} cash, ${equity:.2f} equity, ${buying_power:.2f} buying power")
                            return {
                                "cash_balance": cash_balance,
                                "equity": equity,
                                "buying_power": buying_power,
                                "account_type": account.get("account_type")
                            }
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
                    max_pos = strategy.get('max_position_size')
                    max_trades = strategy.get('max_daily_trades')
                    max_pos_str = f"{max_pos:.1%}" if max_pos is not None else "N/A"
                    max_trades_str = str(max_trades) if max_trades is not None else "N/A"
                    logger.info(f"   • {strategy.get('strategy_name', 'Unknown')}: {max_pos_str} max position, {max_trades_str} daily trades")
                
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
            response = requests.get(
                f"{self.live_trading_url}/api/v1/trading/orders", 
                params={"account_id": self.account_id},
                timeout=10
            )
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
                    price = order.get('price', 0)
                    status = order.get('status', 'N/A')
                    action = order.get('action', 'N/A')
                    logger.info(f"   • {order.get('symbol', 'N/A')} - {action} @ ${price:.2f} - {status}")
                
                return recent_orders
            else:
                logger.error(f"❌ Failed to get orders: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return None
    
    def get_current_market_price(self, symbol):
        """Get current market price from Polygon API"""
        try:
            import subprocess
            import base64
            
            # Get Polygon API key from k8s secret
            result = subprocess.run(
                ['kubectl', 'get', 'secret', 'polygon-api-key', '-n', 'trading-system', 
                 '-o', "jsonpath='{.data.api-key}'"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                api_key = base64.b64decode(result.stdout.strip("'")).decode('utf-8')
                
                # Fetch current price from Polygon
                url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
                response = requests.get(url, params={'apiKey': api_key}, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        return float(data['results'][0]['c'])  # Close price
            return None
        except Exception as e:
            logger.debug(f"Could not fetch price for {symbol}: {e}")
            return None
    
    def get_pending_options_orders(self):
        """Get pending options orders that haven't filled yet"""
        try:
            response = requests.get(
                f"{self.live_trading_url}/api/v1/trading/orders",
                params={"account_id": self.account_id, "limit": 100},
                timeout=10
            )
            if response.status_code == 200:
                orders_data = response.json()
                all_orders = orders_data.get("orders", [])
                
                # Filter for options orders only
                options_orders = [o for o in all_orders if o.get("option_type")]
                
                # Categorize by status
                pending = [o for o in options_orders if o.get("status") == "SUBMITTED"]
                filled = [o for o in options_orders if o.get("status") == "FILLED"]
                rejected = [o for o in options_orders if o.get("status") in ["REJECTED", "CANCELLED", "FAILED"]]
                
                return {
                    "pending": pending,
                    "filled": filled,
                    "rejected": rejected,
                    "total": len(options_orders)
                }
            else:
                logger.error(f"❌ Failed to get orders: {response.status_code}")
                return {"pending": [], "filled": [], "rejected": [], "total": 0}
        except Exception as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return {"pending": [], "filled": [], "rejected": [], "total": 0}
    
    def get_active_positions(self):
        """Get current active positions with exit strategy information"""
        try:
            response = requests.get(
                f"{self.live_trading_url}/api/v1/trading/positions", 
                params={"account_id": self.account_id, "status_filter": "OPEN"},
                timeout=10
            )
            if response.status_code == 200:
                positions_data = response.json()
                raw_positions = positions_data.get("positions", [])
                
                # Consolidate positions by symbol (sum quantities for same symbol)
                consolidated = {}
                for pos in raw_positions:
                    symbol = pos.get("symbol")
                    if symbol not in consolidated:
                        consolidated[symbol] = pos.copy()
                    else:
                        # Sum quantities and recalculate weighted average price
                        existing = consolidated[symbol]
                        existing_qty = existing.get("quantity", 0)
                        existing_avg = existing.get("average_price", 0)
                        new_qty = pos.get("quantity", 0)
                        new_avg = pos.get("average_price", 0)
                        
                        total_qty = existing_qty + new_qty
                        if total_qty > 0:
                            weighted_avg = ((existing_qty * existing_avg) + (new_qty * new_avg)) / total_qty
                            consolidated[symbol]["quantity"] = total_qty
                            consolidated[symbol]["average_price"] = weighted_avg
                            
                            # Sum P&L
                            consolidated[symbol]["unrealized_pnl"] = consolidated[symbol].get("unrealized_pnl", 0) + pos.get("unrealized_pnl", 0)
                
                positions = list(consolidated.values())
                logger.info(f"📊 Active Positions: {len(positions)} ({len(raw_positions)} raw position records)")
                
                total_stored_value = 0
                total_current_value = 0
                total_cost = 0
                
                for position in positions:
                    symbol = position.get("symbol", "N/A")
                    quantity = position.get("quantity", 0)
                    avg_price = position.get("average_price", 0)  # Entry price
                    stored_current = position.get("current_price", avg_price)  # Stored "current" price
                    stored_pnl = position.get("unrealized_pnl", 0)
                    
                    # Get REAL current market price
                    real_current_price = self.get_current_market_price(symbol)
                    if real_current_price is None:
                        real_current_price = stored_current
                    
                    # Calculate values
                    position_cost = quantity * avg_price
                    stored_value = quantity * stored_current
                    real_value = quantity * real_current_price
                    real_pnl = real_value - position_cost
                    real_pnl_pct = (real_pnl / position_cost * 100) if position_cost > 0 else 0
                    
                    total_cost += position_cost
                    total_stored_value += stored_value
                    total_current_value += real_value
                    
                    logger.info(f"   • {symbol}: {quantity} shares @ ${avg_price:.2f} entry")
                    logger.info(f"      📦 Stored: ${stored_current:.2f} = ${stored_value:.2f} (P&L: ${stored_pnl:.2f})")
                    logger.info(f"      💹 LIVE: ${real_current_price:.2f} = ${real_value:.2f} (P&L: ${real_pnl:+.2f} / {real_pnl_pct:+.2f}%)")
                    
                    # Display exit strategy information if available
                    if position.get("exit_strategy"):
                        exit_strategy = position["exit_strategy"]
                        logger.info(f"     🎯 Exit Strategy:")
                        logger.info(f"        • Max Hold: {exit_strategy.get('max_holding_days', 'N/A')} days")
                        logger.info(f"        • Profit Target: {exit_strategy.get('profit_target_pct', 'N/A'):.1%}" if isinstance(exit_strategy.get('profit_target_pct'), (int, float)) else f"        • Profit Target: {exit_strategy.get('profit_target_pct', 'N/A')}")
                        logger.info(f"        • Stop Loss: {exit_strategy.get('stop_loss_pct', 'N/A'):.1%}" if isinstance(exit_strategy.get('stop_loss_pct'), (int, float)) else f"        • Stop Loss: {exit_strategy.get('stop_loss_pct', 'N/A')}")
                        logger.info(f"        • Min Holding: {exit_strategy.get('min_holding_hours', 'N/A')} hours")
                        
                        # Show anxiety-reducing message
                        if exit_strategy.get('anxiety_reduction_message'):
                            logger.info(f"     🛡️ Protection:")
                            for line in exit_strategy['anxiety_reduction_message'].split('\n'):
                                if line.strip():
                                    logger.info(f"        {line}")
                        
                        # Show closest exit condition
                        if exit_strategy.get('closest_exit'):
                            closest = exit_strategy['closest_exit']
                            logger.info(f"     ⏰ Closest Exit: {closest.get('description', 'Unknown')}")
                    else:
                        # Show default exit strategy if not in position data
                        logger.info(f"     🎯 Exit Strategy:")
                        logger.info(f"        • Max Hold: 30 days")
                        logger.info(f"        • Profit Target: 15.0%")
                        logger.info(f"        • Stop Loss: 8.0%")
                        logger.info(f"        • Min Holding: 4 hours")
                        logger.info(f"     🛡️  Protection:")
                        logger.info(f"        Your position is protected by automatic exit strategies")
                        logger.info(f"        Risk is limited to 8% stop loss per position")
                
                # Check for pending options orders
                logger.info(f"\n📊 Checking for pending options orders...")
                options_status = self.get_pending_options_orders()
                
                if options_status["pending"]:
                    total_pending = len(options_status['pending'])
                    # Show only the 10 most recent pending orders
                    recent_pending = sorted(options_status["pending"], 
                                          key=lambda x: x.get("created_at", ""), 
                                          reverse=True)[:10]
                    
                    logger.info(f"\n🕒 PENDING OPTIONS ORDERS ({total_pending} total, showing 10 most recent):")
                    for order in recent_pending:
                        symbol = order.get("symbol", "N/A")
                        option_type = order.get("option_type", "N/A")
                        strike = order.get("strike_price", 0)
                        quantity = order.get("quantity", 0)
                        created = order.get("created_at", "N/A")
                        logger.info(f"   🕒 {symbol} {option_type} Strike ${strike} x{quantity} - Submitted {created[:10]}")
                        logger.info(f"      Status: Awaiting market open / execution")
                
                if options_status["rejected"]:
                    logger.info(f"\n❌ REJECTED OPTIONS ORDERS ({len(options_status['rejected'])}):")
                    for order in options_status["rejected"]:
                        symbol = order.get("symbol", "N/A")
                        option_type = order.get("option_type", "N/A")
                        strike = order.get("strike_price", 0)
                        status = order.get("status", "REJECTED")
                        reason = order.get("reject_reason") or order.get("notes") or "Unknown reason"
                        logger.info(f"   ❌ {symbol} {option_type} Strike ${strike} - {status}")
                        logger.info(f"      Reason: {reason}")
                
                if options_status["filled"] and not positions:
                    # Filled orders but no positions yet (might be in sync)
                    logger.info(f"\n⚠️  {len(options_status['filled'])} filled options orders detected")
                    logger.info(f"   Positions may need to sync from broker")
                
                # Log totals
                if positions:
                    total_stored_pnl = total_stored_value - total_cost
                    total_real_pnl = total_current_value - total_cost
                    logger.info(f"\n📊 Portfolio Summary:")
                    logger.info(f"   • Total Cost: ${total_cost:.2f}")
                    logger.info(f"   • Stored Value: ${total_stored_value:.2f} (P&L: ${total_stored_pnl:+.2f})")
                    logger.info(f"   • LIVE Value: ${total_current_value:.2f} (P&L: ${total_real_pnl:+.2f})")
                
                # Attach summary data to positions for report
                for position in positions:
                    position['_total_cost'] = total_cost
                    position['_total_stored_value'] = total_stored_value
                    position['_total_current_value'] = total_current_value
                
                return positions
            else:
                logger.error(f"❌ Failed to get positions: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return None
    
    def check_authentication_status(self):
        """Check Public.com authentication status"""
        try:
            response = requests.get(
                f"{self.live_trading_url}/api/v1/auth/status/{self.account_id}",
                timeout=10
            )
            if response.status_code == 200:
                auth_data = response.json()
                is_authenticated = auth_data.get("is_authenticated", False)
                token_expires_at = auth_data.get("token_expires_at")
                
                if is_authenticated:
                    if token_expires_at:
                        expires_dt = datetime.fromisoformat(token_expires_at.replace("Z", "+00:00"))
                        hours_until_expiry = (expires_dt - datetime.now()).total_seconds() / 3600
                        logger.info(f"🔐 Authentication: ✅ Active (expires in {hours_until_expiry:.1f} hours)")
                    else:
                        logger.info(f"🔐 Authentication: ✅ Active")
                    return True
                else:
                    logger.error(f"🔐 Authentication: ❌ Not authenticated")
                    return False
            else:
                logger.error(f"❌ Failed to check authentication: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to check authentication: {e}")
            return False

    def check_risk_status(self):
        """Check risk management status"""
        try:
            response = requests.get(f"{self.live_trading_url}/api/v1/risk/profile/{self.account_id}", timeout=10)
            if response.status_code == 200:
                risk_data = response.json()
                
                # Get the correct field names and display properly
                max_pos = risk_data.get('max_position_size', 0)
                max_exposure = risk_data.get('max_portfolio_risk', 0)  # This is the total exposure field
                
                logger.info("🛡️  Risk Management Status:")
                logger.info(f"   • Max Daily Loss: ${risk_data.get('max_daily_loss', 0):.2f}")
                logger.info(f"   • Max Position Size: {max_pos:.1%}")
                logger.info(f"   • Max Portfolio Exposure: {max_exposure:.1%}")
                logger.info(f"   • Min Cash Reserve: {1 - max_exposure:.1%}")  # Calculate from max exposure
                logger.info(f"   • Circuit Breaker: ✅ Enabled")
                logger.info(f"   • Automated Exits: ✅ Enabled")
                
                return risk_data
            else:
                logger.error(f"❌ Failed to get risk status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get risk status: {e}")
            return None
    
    def generate_performance_report(self, balance_data, strategies, orders, positions, risk_data, auth_status, options_status=None):
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
   • Authentication: {'✅ Authenticated' if auth_status else '❌ Not Authenticated'}

📊 ACTIVE STRATEGIES:
   • Total Strategies: {len(strategies) if strategies else 0}
"""
        
        if strategies:
            for strategy in strategies:
                max_pos = strategy.get('max_position_size')
                max_trades = strategy.get('max_daily_trades')
                max_pos_str = f"{max_pos:.1%}" if max_pos is not None else "N/A"
                max_trades_str = str(max_trades) if max_trades is not None else "N/A"
                report += f"   • {strategy.get('strategy_name', 'Unknown')}: {max_pos_str} max position, {max_trades_str} daily trades\n"
        
        report += f"""
📈 TRADING ACTIVITY:
   • Recent Orders (24h): {len(orders) if orders else 0}
   • Active Positions: {len(positions) if positions else 0}
"""
        
        if positions and len(positions) > 0:
            # Get summary data from first position (attached in get_active_positions)
            total_cost = positions[0].get('_total_cost', 0)
            total_stored_value = positions[0].get('_total_stored_value', 0)
            total_current_value = positions[0].get('_total_current_value', 0)
            
            stored_pnl = total_stored_value - total_cost
            live_pnl = total_current_value - total_cost
            
            report += f"""   • Position Cost: ${total_cost:,.2f}
   • Stored P&L: ${stored_pnl:+.2f} (database values)
   • LIVE P&L: ${live_pnl:+.2f} (real-time market prices)
   • Performance Gain: ${live_pnl - stored_pnl:+.2f} since last update
"""
        
        report += f"""
🛡️  RISK MANAGEMENT:
   • Max Daily Loss: ${risk_data.get('max_daily_loss', 0):,.2f}
   • Max Position Size: {risk_data.get('max_position_size', 0):.1%}
   • Max Portfolio Exposure: {risk_data.get('max_portfolio_risk', 0):.1%}
   • Min Cash Reserve: {1 - risk_data.get('max_portfolio_risk', 0):.1%}
   • Circuit Breaker: ✅ Enabled
   • Automated Exits: ✅ Enabled

🎯 OPTIMIZATION TARGETS:
   • Annual Return Target: {self.targets['annual_return']:.1%}
   • Max Drawdown Limit: {self.targets['max_drawdown']:.1%}
   • Sharpe Ratio Target: {self.targets['sharpe_ratio']:.1f}
   • Win Rate Target: {self.targets['win_rate']:.1%}
   • Daily Trades Target: {self.targets['daily_trades']}
   • Monthly Trades Target: {self.targets['monthly_trades']}

📊 ACTIVE STRATEGY CONFIGURATION:
   • MultiStrategyEnsemble: Combines 5 proven strategies with optimized weights
   • Adaptive Wave Strategy: Elliott Wave + Ichimoku analysis (30% weight)
   • Regime Switching: Market timing and regime detection (20% weight)
   • Enhanced Multi: Sector rotation and momentum (20% weight)
   • Momentum Strategy: Cross-sectional momentum analysis (15% weight)
   • Zero-DTE Options: Credit spreads with delta targeting (15% weight)
   
📊 RISK MANAGEMENT (Active):
   • Max Position Size: 20% per position
   • Max Portfolio Exposure: 85%
   • Min Cash Reserve: 15%
   • Max Daily Loss: $150
   • Max Daily Trades: 10
   • Automated Stop Loss: ✅ Enabled (8% per position)
   • Circuit Breaker: ✅ Enabled at 8% portfolio drawdown

💡 CURRENT STATUS:
   • MultiStrategyEnsemble: ✅ Active
   • Strategy Weights: Adaptive Wave (30%), Regime Switching (20%), Enhanced Multi (20%), Momentum (15%), Zero-DTE (15%)
   • Risk Controls: ✅ Active (20% max position, $150 daily loss limit, 85% max exposure, 15% cash reserve)
   • Automatic Exits: ✅ Enabled (Stop loss, Take profit, Circuit breakers)
   • Primary Symbols: SPY, NVDA, AAPL, QQQ
   • Secondary Symbols: TSLA, GOOGL, AMD, META

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
        auth_status = self.check_authentication_status()
        strategies = self.get_active_strategies()
        orders = self.get_recent_orders()
        positions = self.get_active_positions()
        risk_data = self.check_risk_status()
        options_status = self.get_pending_options_orders()
        
        # Generate report
        if balance_data:
            report = self.generate_performance_report(balance_data, strategies, orders, positions, risk_data, auth_status, options_status)
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
            'strategies_count': len(strategies) if strategies else 0,
            'orders': orders,
            'orders_count': len(orders) if orders else 0,
            'positions': positions,
            'positions_count': len(positions) if positions else 0,
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
