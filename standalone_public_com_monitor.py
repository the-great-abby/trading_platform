#!/usr/bin/env python3
"""
Standalone Public.com Cost Optimization Monitor
Lightweight monitoring script that can run alongside existing services
"""

import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StandalonePublicComMonitor:
    """Standalone Public.com cost optimization monitor"""
    
    def __init__(self):
        self.monitoring_data = {
            "deployment_time": datetime.now().isoformat(),
            "expected_benefits": {
                "annual_cost_savings": 139.26,
                "annual_rebates": 10.18,
                "total_annual_benefit": 149.44,
                "return_improvement": 0.0317
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
        """Calculate daily cost benefits for Public.com optimization"""
        # OLD costs (what we would have paid)
        old_commission_per_trade = 0.65
        old_commission_per_contract = 0.50
        
        # NEW costs (Public.com)
        new_commission_per_trade = 0.0
        new_commission_per_contract = 0.0
        new_rebate_per_contract = 0.06
        
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
    
    def generate_status_report(self) -> str:
        """Generate current status report"""
        total_days = len(self.monitoring_data["daily_tracking"])
        total_savings = sum(day["benefits"]["net_savings"] for day in self.monitoring_data["daily_tracking"].values())
        
        report = f"""
🚀 PUBLIC.COM COST OPTIMIZATION STATUS
=====================================

📅 Deployment: {self.monitoring_data['deployment_time']}
📊 Days Active: {total_days}
💰 Total Savings: ${total_savings:.2f}
🎯 Expected Annual Benefit: ${self.monitoring_data['expected_benefits']['total_annual_benefit']:.2f}
📈 Status: {'✅ Healthy' if total_savings >= 0 else '⚠️ Needs Attention'}

📊 DAILY BREAKDOWN:
"""
        
        if total_days > 0:
            for date, data in sorted(self.monitoring_data["daily_tracking"].items()):
                report += f"   {date}: {data['trades_count']} trades, {data['contracts_count']} contracts, ${data['benefits']['net_savings']:.2f} savings\n"
        else:
            report += "   No trading data recorded yet\n"
        
        report += f"""
🎯 KEY INSIGHTS:
   • Cost optimization is {'working well' if total_savings > 0 else 'needs attention'}
   • {'On track' if total_savings >= 0 else 'Below target'} for expected benefits
   • {'Active' if total_days > 0 else 'Ready'} monitoring system

=====================================
"""
        
        return report
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary"""
        total_days = len(self.monitoring_data["daily_tracking"])
        total_savings = sum(day["benefits"]["net_savings"] for day in self.monitoring_data["daily_tracking"].values())
        
        return {
            "deployment_time": self.monitoring_data["deployment_time"],
            "days_active": total_days,
            "total_savings": total_savings,
            "expected_annual_benefit": self.monitoring_data["expected_benefits"]["total_annual_benefit"],
            "status": "healthy" if total_savings >= 0 else "needs_attention"
        }
    
    def simulate_daily_trading(self):
        """Simulate daily trading data for testing"""
        import random
        
        # Simulate realistic trading activity
        trades_count = random.randint(2, 8)  # 2-8 trades per day
        contracts_count = trades_count * random.randint(1, 3)  # 1-3 contracts per trade
        
        self.update_daily_tracking(trades_count, contracts_count)
        
        return {
            "trades_count": trades_count,
            "contracts_count": contracts_count,
            "benefits": self.calculate_daily_benefits(trades_count, contracts_count)
        }

def main():
    """Main monitoring function"""
    monitor = StandalonePublicComMonitor()
    
    print("🚀 Standalone Public.com Cost Optimization Monitor")
    print("=" * 60)
    
    # Get current status
    status = monitor.get_status_summary()
    
    print(f"Deployment Time: {status['deployment_time']}")
    print(f"Days Active: {status['days_active']}")
    print(f"Total Savings: ${status['total_savings']:.2f}")
    print(f"Expected Annual Benefit: ${status['expected_annual_benefit']:.2f}")
    print(f"Status: {status['status']}")
    
    # Generate detailed report
    print(monitor.generate_status_report())
    
    # Ask if user wants to simulate trading data
    try:
        response = input("\n🤔 Would you like to simulate today's trading data? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            result = monitor.simulate_daily_trading()
            print(f"\n✅ Simulated trading data:")
            print(f"   Trades: {result['trades_count']}")
            print(f"   Contracts: {result['contracts_count']}")
            print(f"   Daily Savings: ${result['benefits']['net_savings']:.2f}")
            print(f"   Rebates: ${result['benefits']['rebates']:.2f}")
    except KeyboardInterrupt:
        print("\n👋 Monitoring session ended")
    
    print("\n✅ Standalone monitoring system ready!")
    print("💡 Run this script daily to track your Public.com cost optimization benefits")

if __name__ == "__main__":
    main()









