#!/usr/bin/env python3
"""
Public.com Cost Optimization Monitor
Track and report on cost savings and rebate earnings
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PublicComCostMonitor:
    """Monitor Public.com cost optimization benefits"""
    
    def __init__(self):
        self.monitoring_data = {
            "deployment_time": datetime.now().isoformat(),
            "expected_benefits": {
                "annual_cost_savings": 139.26,
                "annual_rebates": 10.18,
                "total_annual_benefit": 149.44,
                "return_improvement": 0.0317  # 3.17%
            },
            "daily_tracking": {},
            "monthly_summary": {},
            "alerts": []
        }
        
        # Load existing data if available
        self.load_monitoring_data()
    
    def load_monitoring_data(self):
        """Load existing monitoring data"""
        try:
            with open('public_com_monitoring.json', 'r') as f:
                self.monitoring_data = json.load(f)
            logger.info("Loaded existing monitoring data")
        except FileNotFoundError:
            logger.info("Starting fresh monitoring data")
    
    def save_monitoring_data(self):
        """Save monitoring data to file"""
        with open('public_com_monitoring.json', 'w') as f:
            json.dump(self.monitoring_data, f, indent=2)
    
    def calculate_daily_benefits(self, trades_count: int, contracts_count: int) -> Dict[str, float]:
        """Calculate daily cost benefits"""
        # OLD costs (what we would have paid)
        old_commission_per_trade = 0.65
        old_commission_per_contract = 0.50
        old_spread_cost = 0.002  # 0.2%
        old_slippage = 0.0005    # 0.05%
        
        # NEW costs (Public.com)
        new_commission_per_trade = 0.0
        new_commission_per_contract = 0.0
        new_rebate_per_contract = 0.06
        new_spread_cost = 0.001  # 0.1%
        new_slippage = 0.0003    # 0.03%
        
        # Calculate costs
        old_daily_costs = (trades_count * old_commission_per_trade + 
                          contracts_count * old_commission_per_contract)
        
        new_daily_costs = (trades_count * new_commission_per_trade + 
                          contracts_count * new_commission_per_contract)
        
        daily_rebates = contracts_count * new_rebate_per_contract
        
        return {
            "old_costs": old_daily_costs,
            "new_costs": new_daily_costs,
            "rebates": daily_rebates,
            "net_savings": old_daily_costs - new_daily_costs + daily_rebates
        }
    
    def update_daily_tracking(self, trades_count: int, contracts_count: int):
        """Update daily tracking data"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        benefits = self.calculate_daily_benefits(trades_count, contracts_count)
        
        self.monitoring_data["daily_tracking"][today] = {
            "trades_count": trades_count,
            "contracts_count": contracts_count,
            "benefits": benefits,
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate running totals
        total_old_costs = sum(day["benefits"]["old_costs"] for day in self.monitoring_data["daily_tracking"].values())
        total_new_costs = sum(day["benefits"]["new_costs"] for day in self.monitoring_data["daily_tracking"].values())
        total_rebates = sum(day["benefits"]["rebates"] for day in self.monitoring_data["daily_tracking"].values())
        total_savings = total_old_costs - total_new_costs + total_rebates
        
        logger.info(f"📊 Daily Update - {today}")
        logger.info(f"   Trades: {trades_count}, Contracts: {contracts_count}")
        logger.info(f"   Daily Savings: ${benefits['net_savings']:.2f}")
        logger.info(f"   Total Savings: ${total_savings:.2f}")
        
        self.save_monitoring_data()
    
    def generate_monthly_report(self) -> str:
        """Generate monthly cost optimization report"""
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Filter data for current month
        monthly_data = {
            date: data for date, data in self.monitoring_data["daily_tracking"].items()
            if datetime.fromisoformat(date) >= month_start
        }
        
        if not monthly_data:
            return "No data available for current month"
        
        # Calculate monthly totals
        total_trades = sum(day["trades_count"] for day in monthly_data.values())
        total_contracts = sum(day["contracts_count"] for day in monthly_data.values())
        total_old_costs = sum(day["benefits"]["old_costs"] for day in monthly_data.values())
        total_new_costs = sum(day["benefits"]["new_costs"] for day in monthly_data.values())
        total_rebates = sum(day["benefits"]["rebates"] for day in monthly_data.values())
        total_savings = total_old_costs - total_new_costs + total_rebates
        
        # Calculate projections
        days_in_month = now.day
        projected_monthly_savings = total_savings * (30 / days_in_month)
        projected_annual_savings = projected_monthly_savings * 12
        
        report = f"""
📊 PUBLIC.COM COST OPTIMIZATION MONTHLY REPORT
==============================================

📅 Period: {month_start.strftime('%B %Y')} (through {now.strftime('%B %d, %Y')})
📈 Trading Activity:
   • Total Trades: {total_trades}
   • Total Contracts: {total_contracts}
   • Average Daily Trades: {total_trades / days_in_month:.1f}
   • Average Daily Contracts: {total_contracts / days_in_month:.1f}

💰 Cost Optimization Results:
   • OLD Configuration Costs: ${total_old_costs:.2f}
   • NEW Configuration Costs: ${total_new_costs:.2f}
   • Rebates Earned: ${total_rebates:.2f}
   • Net Monthly Savings: ${total_savings:.2f}

📊 Projections:
   • Projected Monthly Savings: ${projected_monthly_savings:.2f}
   • Projected Annual Savings: ${projected_annual_savings:.2f}
   • Expected Annual Benefit: ${self.monitoring_data['expected_benefits']['total_annual_benefit']:.2f}
   • Performance vs Expected: {(projected_annual_savings / self.monitoring_data['expected_benefits']['total_annual_benefit']) * 100:.1f}%

🎯 Key Insights:
   • {'✅ On Track' if projected_annual_savings >= self.monitoring_data['expected_benefits']['total_annual_benefit'] * 0.8 else '⚠️ Below Target'}
   • Cost optimization is {'working well' if total_savings > 0 else 'needs attention'}
   • Rebate program is {'active' if total_rebates > 0 else 'inactive'}

==============================================
"""
        
        return report
    
    def check_alerts(self):
        """Check for any alerts or issues"""
        alerts = []
        
        # Check if we're on track for annual benefits
        now = datetime.now()
        days_since_deployment = (now - datetime.fromisoformat(self.monitoring_data["deployment_time"])).days
        
        if days_since_deployment > 0:
            expected_daily_benefit = self.monitoring_data["expected_benefits"]["total_annual_benefit"] / 252
            actual_daily_benefit = sum(day["benefits"]["net_savings"] for day in self.monitoring_data["daily_tracking"].values()) / days_since_deployment
            
            if actual_daily_benefit < expected_daily_benefit * 0.5:
                alerts.append({
                    "type": "warning",
                    "message": f"Daily benefits below 50% of expected ({actual_daily_benefit:.2f} vs {expected_daily_benefit:.2f})",
                    "timestamp": now.isoformat()
                })
        
        # Check for missing data
        if not self.monitoring_data["daily_tracking"]:
            alerts.append({
                "type": "info",
                "message": "No trading data recorded yet",
                "timestamp": now.isoformat()
            })
        
        self.monitoring_data["alerts"] = alerts
        return alerts
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary"""
        alerts = self.check_alerts()
        
        total_days = len(self.monitoring_data["daily_tracking"])
        total_savings = sum(day["benefits"]["net_savings"] for day in self.monitoring_data["daily_tracking"].values())
        
        return {
            "deployment_time": self.monitoring_data["deployment_time"],
            "days_active": total_days,
            "total_savings": total_savings,
            "expected_annual_benefit": self.monitoring_data["expected_benefits"]["total_annual_benefit"],
            "alerts": alerts,
            "status": "healthy" if not alerts else "needs_attention"
        }

def main():
    """Main monitoring function"""
    monitor = PublicComCostMonitor()
    
    # Get current status
    status = monitor.get_status_summary()
    
    print("🚀 Public.com Cost Optimization Monitor")
    print("=" * 50)
    print(f"Deployment Time: {status['deployment_time']}")
    print(f"Days Active: {status['days_active']}")
    print(f"Total Savings: ${status['total_savings']:.2f}")
    print(f"Expected Annual Benefit: ${status['expected_annual_benefit']:.2f}")
    print(f"Status: {status['status']}")
    
    if status['alerts']:
        print("\n⚠️ Alerts:")
        for alert in status['alerts']:
            print(f"   • {alert['message']}")
    
    # Generate monthly report if we have data
    if status['days_active'] > 0:
        print("\n" + monitor.generate_monthly_report())
    
    print("\n✅ Monitoring system active and ready!")

if __name__ == "__main__":
    main()





















