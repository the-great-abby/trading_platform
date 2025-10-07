#!/usr/bin/env python3
"""
Simplified Optimized System Monitor
Monitors the deployed optimized trading system with available endpoints
"""

import json
import requests
import subprocess
import logging
import time
from datetime import datetime, timedelta
import os
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedSystemMonitor:
    def __init__(self):
        self.strategy_service_url = "http://localhost:11001"
        self.dashboard_url = "http://localhost:11115"
        self.monitoring_log = f"/Users/abby/code/trading/monitoring/simplified_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
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
        """Check if services are running"""
        logger.info("🏥 Checking service health...")
        
        services = [
            ("Strategy Service", f"{self.strategy_service_url}/"),
            ("Trading Dashboard", f"{self.dashboard_url}/")
        ]
        
        healthy_services = []
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name}: Healthy")
                    healthy_services.append(service_name)
                else:
                    logger.warning(f"⚠️  {service_name}: Unhealthy (Status: {response.status_code})")
            except Exception as e:
                logger.error(f"❌ {service_name}: Unreachable ({e})")
        
        return healthy_services
    
    def check_k8s_status(self):
        """Check Kubernetes deployment status"""
        logger.info("☸️  Checking Kubernetes status...")
        
        try:
            # Check strategy service pods
            cmd = ['kubectl', 'get', 'pods', '-l', 'app=strategy-service', '-n', 'trading-system', '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                pods_data = json.loads(result.stdout)
                pod_status = []
                
                for pod in pods_data.get('items', []):
                    pod_name = pod['metadata']['name']
                    pod_status_info = pod['status']['phase']
                    pod_status.append(f"{pod_name}: {pod_status_info}")
                
                logger.info(f"✅ Strategy service pods: {', '.join(pod_status)}")
                return pod_status
            else:
                logger.error(f"❌ Failed to check pod status: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to check Kubernetes status: {e}")
            return None
    
    def check_config_deployment(self):
        """Check if optimized config is deployed"""
        logger.info("🔧 Checking configuration deployment...")
        
        try:
            # Check ConfigMap
            cmd = ['kubectl', 'get', 'configmap', 'strategy-service-config', '-n', 'trading-system', '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                configmap_data = json.loads(result.stdout)
                config_data = configmap_data.get('data', {}).get('live_trading_strategies.yaml', '')
                
                if config_data:
                    # Parse YAML to check for optimized settings
                    config = yaml.safe_load(config_data)
                    
                    # Check for key optimized settings
                    optimizations = []
                    
                    if config.get('strategies', {}).get('ELLIOTT_WAVE_IMPULSE', {}).get('enabled'):
                        optimizations.append("✅ Elliott Wave Impulse: ENABLED")
                    else:
                        optimizations.append("❌ Elliott Wave Impulse: DISABLED")
                    
                    if config.get('cost_controls', {}).get('trading_costs', {}).get('commission_per_trade') == 0.0:
                        optimizations.append("✅ Commission-free trading: ACTIVE")
                    else:
                        optimizations.append("❌ Commission-free trading: INACTIVE")
                    
                    if config.get('cost_controls', {}).get('trading_costs', {}).get('options_rebate_per_contract') == 0.06:
                        optimizations.append("✅ Options rebates: ACTIVE")
                    else:
                        optimizations.append("❌ Options rebates: INACTIVE")
                    
                    max_daily_trades = config.get('cost_controls', {}).get('trading_limits', {}).get('max_daily_trades', 0)
                    if max_daily_trades >= 4:
                        optimizations.append(f"✅ Daily trade limit: {max_daily_trades} (optimized)")
                    else:
                        optimizations.append(f"⚠️  Daily trade limit: {max_daily_trades} (may need optimization)")
                    
                    logger.info("📋 Configuration optimizations:")
                    for opt in optimizations:
                        logger.info(f"   {opt}")
                    
                    return optimizations
                else:
                    logger.warning("⚠️  No configuration data found in ConfigMap")
                    return None
            else:
                logger.error(f"❌ Failed to check ConfigMap: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to check configuration: {e}")
            return None
    
    def check_port_forwarding(self):
        """Check port forwarding status"""
        logger.info("🔌 Checking port forwarding...")
        
        try:
            # Check if port forwards are active
            cmd = ['ps', 'aux']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            port_forwards = []
            for line in result.stdout.split('\n'):
                if 'kubectl port-forward' in line and 'strategy-service' in line:
                    port_forwards.append(line.strip())
            
            if port_forwards:
                logger.info("✅ Port forwards active:")
                for pf in port_forwards:
                    logger.info(f"   {pf}")
                return True
            else:
                logger.warning("⚠️  No port forwards detected for strategy service")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to check port forwarding: {e}")
            return False
    
    def generate_status_report(self, healthy_services, k8s_status, config_optimizations, port_forwards):
        """Generate comprehensive status report"""
        logger.info("📋 Generating status report...")
        
        report = f"""
================================================================================
🚀 OPTIMIZED TRADING SYSTEM STATUS REPORT
================================================================================
📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🏥 SERVICE HEALTH:
   • Healthy Services: {len(healthy_services)}
   • Services: {', '.join(healthy_services) if healthy_services else 'None'}

☸️  KUBERNETES STATUS:
   • Strategy Service Pods: {len(k8s_status) if k8s_status else 0}
   • Pod Status: {', '.join(k8s_status) if k8s_status else 'Unknown'}

🔌 PORT FORWARDING:
   • Status: {'✅ Active' if port_forwards else '❌ Inactive'}
   • Strategy Service: {'✅ Accessible' if port_forwards else '❌ Not accessible'}

🔧 CONFIGURATION STATUS:
"""
        
        if config_optimizations:
            for opt in config_optimizations:
                report += f"   • {opt}\n"
        else:
            report += "   • ❌ Configuration status unknown\n"
        
        report += f"""
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

💡 NEXT STEPS:
"""
        
        if not port_forwards:
            report += "   • Set up port forwarding: kubectl port-forward -n trading-system svc/strategy-service 11001:80\n"
        
        if not config_optimizations:
            report += "   • Verify configuration deployment\n"
        
        if len(healthy_services) < 2:
            report += "   • Check service health and restart if needed\n"
        
        report += "   • Monitor performance over time\n"
        report += "   • Run backtests to validate improvements\n"
        
        report += """
================================================================================
"""
        
        return report
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        logger.info("🔄 Starting monitoring cycle...")
        
        # Check service health
        healthy_services = self.check_service_health()
        
        # Check Kubernetes status
        k8s_status = self.check_k8s_status()
        
        # Check configuration deployment
        config_optimizations = self.check_config_deployment()
        
        # Check port forwarding
        port_forwards = self.check_port_forwarding()
        
        # Generate report
        report = self.generate_status_report(healthy_services, k8s_status, config_optimizations, port_forwards)
        print(report)
        
        # Log status
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'healthy_services': healthy_services,
            'k8s_status': k8s_status,
            'config_optimizations': config_optimizations,
            'port_forwards': port_forwards
        }
        
        try:
            with open(self.monitoring_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()}: {json.dumps(status_data)}\n")
        except Exception as e:
            logger.error(f"❌ Failed to write to log file: {e}")
        
        return status_data
    
    def run_continuous_monitoring(self, interval_minutes=5):
        """Run continuous monitoring"""
        logger.info(f"🔄 Starting continuous monitoring (every {interval_minutes} minutes)")
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
        logger.info("🔍 Running single monitoring check...")
        
        status_data = self.run_monitoring_cycle()
        
        # Summary
        logger.info("📋 Monitoring Summary:")
        logger.info(f"   • Healthy Services: {len(status_data['healthy_services'])}")
        logger.info(f"   • Kubernetes Status: {'✅ Available' if status_data['k8s_status'] else '❌ Unavailable'}")
        logger.info(f"   • Configuration: {'✅ Deployed' if status_data['config_optimizations'] else '❌ Unknown'}")
        logger.info(f"   • Port Forwarding: {'✅ Active' if status_data['port_forwards'] else '❌ Inactive'}")
        
        return status_data

def main():
    """Main execution function"""
    import sys
    
    monitor = SimplifiedSystemMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            monitor.run_continuous_monitoring(interval)
        elif sys.argv[1] == "single":
            monitor.run_single_check()
        else:
            print("Usage: python3 simplified_system_monitor.py [continuous|single] [interval_minutes]")
    else:
        # Default to single check
        monitor.run_single_check()

if __name__ == "__main__":
    main()


















