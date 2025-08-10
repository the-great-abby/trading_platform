#!/usr/bin/env python3
"""
Service Status Checker
Checks the status of essential services and provides guidance for getting them running.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_kubernetes_status():
    """Check Kubernetes cluster status"""
    print("🔍 Checking Kubernetes cluster status...")
    
    # Check if kubectl is available
    success, stdout, stderr = run_command("kubectl version --client")
    if not success:
        print("❌ kubectl is not available")
        return False
    
    # Check cluster status
    success, stdout, stderr = run_command("kubectl cluster-info")
    if not success:
        print("❌ Kubernetes cluster is not accessible")
        return False
    
    print("✅ Kubernetes cluster is accessible")
    return True

def check_namespace_status():
    """Check trading-system namespace status"""
    print("\n🔍 Checking trading-system namespace...")
    
    success, stdout, stderr = run_command("kubectl get namespace trading-system")
    if not success:
        print("❌ trading-system namespace not found")
        return False
    
    print("✅ trading-system namespace exists")
    return True

def check_essential_services():
    """Check status of essential services"""
    print("\n🔍 Checking essential services...")
    
    services = [
        'backtest-api',
        'backtest-request-service', 
        'market-data-service',
        'timescaledb',
        'redis',
        'rabbitmq',
        'unified-analytics-dashboard',
        'unified-news-dashboard',
        'unified-trading-dashboard'
    ]
    
    service_status = {}
    
    for service in services:
        success, stdout, stderr = run_command(f"kubectl get pods -n trading-system -l app={service} --no-headers")
        if success and stdout.strip():
            lines = stdout.strip().split('\n')
            running = 0
            pending = 0
            failed = 0
            
            for line in lines:
                if 'Running' in line:
                    running += 1
                elif 'Pending' in line:
                    pending += 1
                elif 'Failed' in line or 'Error' in line:
                    failed += 1
            
            service_status[service] = {
                'running': running,
                'pending': pending,
                'failed': failed,
                'total': len(lines)
            }
        else:
            service_status[service] = {'running': 0, 'pending': 0, 'failed': 0, 'total': 0}
    
    return service_status

def check_resource_usage():
    """Check cluster resource usage"""
    print("\n🔍 Checking cluster resource usage...")
    
    success, stdout, stderr = run_command("kubectl describe nodes | grep -A 10 'Allocated resources'")
    if success:
        print("📊 Current resource allocation:")
        print(stdout)
    else:
        print("❌ Could not get resource usage information")

def print_service_status(service_status):
    """Print service status in a formatted way"""
    print("\n📊 Service Status:")
    print("-" * 80)
    print(f"{'Service':<30} {'Running':<8} {'Pending':<8} {'Failed':<8} {'Total':<8}")
    print("-" * 80)
    
    for service, status in service_status.items():
        print(f"{service:<30} {status['running']:<8} {status['pending']:<8} "
              f"{status['failed']:<8} {status['total']:<8}")
    
    print("-" * 80)

def provide_guidance(service_status):
    """Provide guidance based on service status"""
    print("\n💡 Guidance:")
    
    # Check if any services are running
    total_running = sum(status['running'] for status in service_status.values())
    total_pending = sum(status['pending'] for status in service_status.values())
    total_failed = sum(status['failed'] for status in service_status.values())
    
    if total_running == 0 and total_pending > 0:
        print("⚠️  All services are pending - this indicates resource constraints")
        print("   Recommendations:")
        print("   1. Scale down non-essential services")
        print("   2. Increase cluster resources")
        print("   3. Use local testing instead")
        
    elif total_running > 0:
        print("✅ Some services are running")
        print("   You can:")
        print("   1. Access running services via port forwarding")
        print("   2. Test the winning ensemble strategy locally")
        print("   3. Wait for pending services to start")
        
    elif total_failed > 0:
        print("❌ Some services have failed")
        print("   Check logs with:")
        print("   kubectl logs -n trading-system deployment/<service-name>")
    
    # Check specific essential services
    essential_services = ['backtest-api', 'timescaledb', 'redis']
    essential_running = all(service_status.get(s, {}).get('running', 0) > 0 for s in essential_services)
    
    if essential_running:
        print("\n✅ Essential services (backtest-api, timescaledb, redis) are running")
        print("   You can now:")
        print("   1. Run the winning ensemble strategy backtest")
        print("   2. Access the unified dashboards")
        print("   3. Test with real market data")
    else:
        print("\n❌ Essential services are not all running")
        print("   Consider using local testing instead")

def show_port_forwarding_commands():
    """Show port forwarding commands for running services"""
    print("\n🌐 Port Forwarding Commands:")
    print("If services are running, you can access them with:")
    print()
    print("# Backtest API")
    print("kubectl port-forward svc/backtest-api 10001:10001 -n trading-system")
    print()
    print("# Unified Dashboards")
    print("kubectl port-forward svc/unified-analytics-dashboard 11141:80 -n trading-system")
    print("kubectl port-forward svc/unified-news-dashboard 11142:80 -n trading-system")
    print("kubectl port-forward svc/unified-trading-dashboard 11143:80 -n trading-system")
    print()
    print("# Market Data Service")
    print("kubectl port-forward svc/market-data-service 11108:80 -n trading-system")

def show_local_testing_commands():
    """Show local testing commands"""
    print("\n🧪 Local Testing Commands:")
    print("Since services are not fully available, you can test locally:")
    print()
    print("# Test winning ensemble strategy locally")
    print("python scripts/test_winning_ensemble_local.py")
    print()
    print("# Run analysis")
    print("python scripts/analyze_winning_ensemble.py")
    print()
    print("# See usage example")
    print("python examples/winning_ensemble_usage.py")

def main():
    """Main function"""
    print("🚀 Trading System Service Status Checker")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check Kubernetes
    if not check_kubernetes_status():
        print("\n❌ Cannot proceed without Kubernetes access")
        return
    
    # Check namespace
    if not check_namespace_status():
        print("\n❌ Cannot proceed without trading-system namespace")
        return
    
    # Check resource usage
    check_resource_usage()
    
    # Check services
    service_status = check_essential_services()
    
    # Print status
    print_service_status(service_status)
    
    # Provide guidance
    provide_guidance(service_status)
    
    # Show commands
    show_port_forwarding_commands()
    show_local_testing_commands()
    
    print("\n" + "=" * 60)
    print("✅ Status check complete!")
    print("For more information, see docs/WINNING_ENSEMBLE_STRATEGY_GUIDE.md")

if __name__ == "__main__":
    main() 