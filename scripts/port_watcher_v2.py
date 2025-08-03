#!/usr/bin/env python3
"""
Port Watcher V2 - Improved monitoring for all services
"""

import subprocess
import time
import json
import os
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('port_watcher_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PortWatcherV2:
    def __init__(self):
        # Comprehensive list of all important services to monitor
        self.watched_ports = {
            # Core Monitoring Services
            'grafana': {'local_port': 11102, 'target_port': 3000, 'service': 'grafana'},
            'prometheus': {'local_port': 11101, 'target_port': 9090, 'service': 'prometheus'},
            'infrastructure-metrics': {'local_port': 11103, 'target_port': 11103, 'service': 'infrastructure-metrics-collector'},
            
            # Core Trading Services
            'strategy-service': {'local_port': 11104, 'target_port': 80, 'service': 'strategy-service'},
            'trading-service': {'local_port': 11105, 'target_port': 80, 'service': 'trading-service'},
            'order-service': {'local_port': 11106, 'target_port': 80, 'service': 'order-service'},
            'portfolio-service': {'local_port': 11107, 'target_port': 80, 'service': 'portfolio-service'},
            'risk-service': {'local_port': 11108, 'target_port': 80, 'service': 'risk-service'},
            'market-data-service': {'local_port': 11109, 'target_port': 11084, 'service': 'market-data-service'},
            
            # AI and Analytics Services
            'ai-analysis-service': {'local_port': 11110, 'target_port': 11085, 'service': 'ai-analysis-service'},
            'llm-service': {'local_port': 11112, 'target_port': 11109, 'service': 'llm-service'},
            'analytics-service': {'local_port': 11113, 'target_port': 8006, 'service': 'analytics-service'},
            
            # Unified Dashboard Services (Phase 1 Consolidation)
            'unified-trading-dashboard': {'local_port': 11114, 'target_port': 80, 'service': 'unified-trading-dashboard'},
            'unified-analytics-dashboard': {'local_port': 11115, 'target_port': 80, 'service': 'unified-analytics-dashboard'},
            'unified-news-dashboard': {'local_port': 11116, 'target_port': 80, 'service': 'unified-news-dashboard'},
            
            # Backtesting Services
            'backtest-api': {'local_port': 11119, 'target_port': 10001, 'service': 'backtest-api'},
            'backtest-request-service': {'local_port': 11120, 'target_port': 80, 'service': 'backtest-request-service'},
            
            # Data and Processing Services
            'data-processing-service': {'local_port': 11121, 'target_port': 11095, 'service': 'data-processing-service'},
            'data-analysis-service': {'local_port': 11135, 'target_port': 11136, 'service': 'data-analysis-service'},
            'data-transformation-pipeline': {'local_port': 11138, 'target_port': 11135, 'service': 'data-transformation-pipeline'},
            'market-data-worker': {'local_port': 11122, 'target_port': 11108, 'service': 'market-data-worker'},
            'postgres-vector-storage': {'local_port': 11123, 'target_port': 80, 'service': 'postgres-vector-storage'},
            
            # Database Services
            'postgres': {'local_port': 11139, 'target_port': 5432, 'service': 'postgres'},
            'postgres-dev': {'local_port': 11140, 'target_port': 5432, 'service': 'postgres-dev'},
            'timescaledb': {'local_port': 11141, 'target_port': 5432, 'service': 'timescaledb'},
            
            # Message Queue and Cache Services
            'rabbitmq': {'local_port': 11142, 'target_port': 5672, 'service': 'rabbitmq'},
            'redis': {'local_port': 11143, 'target_port': 6379, 'service': 'redis'},
            'redis-dev': {'local_port': 11144, 'target_port': 11304, 'service': 'redis-dev'},
            
            # Management Services
            'strategy-management-service': {'local_port': 11124, 'target_port': 11126, 'service': 'strategy-management-service'},
            'order-management-service': {'local_port': 11125, 'target_port': 11123, 'service': 'order-management-service'},
            'signal-management-service': {'local_port': 11126, 'target_port': 11125, 'service': 'signal-management-service'},
            'risk-management-service': {'local_port': 11127, 'target_port': 11124, 'service': 'risk-management-service'},
            
            # Additional Services
            'notification-service': {'local_port': 11128, 'target_port': 8007, 'service': 'notification-service'},
            'public-api': {'local_port': 11145, 'target_port': 80, 'service': 'public-api'},
            'report-viewer-service': {'local_port': 11130, 'target_port': 80, 'service': 'report-viewer-service'},
            'trading-core-service': {'local_port': 11132, 'target_port': 11090, 'service': 'trading-core-service'},
            'trading-ultra-service': {'local_port': 11133, 'target_port': 80, 'service': 'trading-ultra-service'},
            
            # Test Services
            'metrics-test-service': {'local_port': 11134, 'target_port': 11100, 'service': 'metrics-test-service'},
        }
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True
        self.log_dir = "port_watcher_v2_logs"
        
        # Create log directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up all port forwarding processes"""
        logger.info("Cleaning up port forwarding processes...")
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"Terminating {name} process (PID: {process.pid})")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    
    def test_service_connectivity(self, name: str, config: Dict) -> bool:
        """Test if a service is actually accessible"""
        try:
            # Test the service endpoint based on service type
            if name == 'grafana':
                cmd = ['curl', '-s', '-u', 'admin:admin', f'http://localhost:{config["local_port"]}/api/datasources']
            elif name == 'prometheus':
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/api/v1/targets']
            elif name == 'infrastructure-metrics':
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/metrics']
            elif name == 'metrics-test-service':
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/metrics']
            elif 'dashboard' in name.lower():
                # Dashboard services typically have a health endpoint
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/health']
            elif 'service' in name.lower():
                # Regular services typically have a health endpoint
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/health']
            else:
                # For other services, just test basic connectivity
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return result.returncode == 0 and len(result.stdout) > 0
            
        except Exception as e:
            logger.error(f"Error testing connectivity for {name}: {str(e)}")
            return False
    
    def start_port_forward(self, name: str, config: Dict) -> Optional[subprocess.Popen]:
        """Start port forwarding for a service"""
        try:
            cmd = [
                'kubectl', 'port-forward',
                f'service/{config["service"]}',
                f'{config["local_port"]}:{config["target_port"]}',
                '-n', 'trading-system'
            ]
            
            logger.info(f"Starting port forward for {name}: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            time.sleep(3)
            
            if process.poll() is None:
                logger.info(f"Successfully started port forward for {name} (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Failed to start port forward for {name}: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting port forward for {name}: {str(e)}")
            return None
    
    def monitor_process(self, name: str, process: subprocess.Popen, config: Dict):
        """Monitor a port forwarding process and capture logs on failure"""
        logger.info(f"Starting monitor for {name}")
        
        while self.running and process.poll() is None:
            time.sleep(10)
            
            # Test connectivity every 30 seconds for critical services
            if name in ['grafana', 'prometheus', 'infrastructure-metrics', 'metrics-test-service']:
                if self.test_service_connectivity(name, config):
                    logger.debug(f"{name} connectivity test passed")
                else:
                    logger.warning(f"{name} connectivity test failed")
        
        if not self.running:
            return
        
        # Process has terminated, capture failure information
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failure_log_file = os.path.join(self.log_dir, f"{name}_failure_{timestamp}.log")
        
        logger.warning(f"Port forward for {name} has terminated, capturing failure information...")
        
        with open(failure_log_file, 'w') as f:
            f.write(f"=== PORT FORWARD FAILURE REPORT ===\n")
            f.write(f"Service: {name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Local Port: {config['local_port']}\n")
            f.write(f"Target Port: {config['target_port']}\n")
            f.write(f"Target Service: {config['service']}\n")
            f.write(f"Process Exit Code: {process.returncode}\n\n")
            
            # Get process output
            try:
                stdout, stderr = process.communicate(timeout=5)
                f.write(f"=== PROCESS OUTPUT ===\n")
                f.write(f"STDOUT:\n{stdout}\n")
                f.write(f"STDERR:\n{stderr}\n\n")
            except subprocess.TimeoutExpired:
                f.write("=== PROCESS OUTPUT ===\n")
                f.write("Timeout getting process output\n\n")
            
            # Get pod status
            f.write(f"=== POD STATUS ===\n")
            try:
                cmd = [
                    'kubectl', 'get', 'pods', '-n', 'trading-system',
                    '-l', f'app={config["service"]}', '-o', 'wide'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    f.write(result.stdout)
                else:
                    f.write(f"Failed to get pod status: {result.stderr}")
            except Exception as e:
                f.write(f"Error getting pod status: {str(e)}")
            f.write("\n\n")
            
            # Get pod logs
            f.write(f"=== POD LOGS ===\n")
            try:
                cmd = [
                    'kubectl', 'logs', '-n', 'trading-system',
                    f'deployment/{config["service"]}', '--tail=50'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    f.write(result.stdout)
                else:
                    f.write(f"Failed to get pod logs: {result.stderr}")
            except Exception as e:
                f.write(f"Error getting pod logs: {str(e)}")
            f.write("\n\n")
        
        logger.info(f"Failure report saved to: {failure_log_file}")
        
        # Remove from processes dict
        if name in self.processes:
            del self.processes[name]
    
    def restart_port_forward(self, name: str, config: Dict):
        """Restart port forwarding for a service"""
        logger.info(f"Restarting port forward for {name}")
        
        # Start new process
        process = self.start_port_forward(name, config)
        if process:
            self.processes[name] = process
            
            # Start monitoring in a separate thread
            monitor_thread = threading.Thread(
                target=self.monitor_process,
                args=(name, process, config),
                daemon=True
            )
            monitor_thread.start()
        else:
            logger.error(f"Failed to restart port forward for {name}")
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting Port Watcher V2...")
        logger.info(f"Monitoring {len(self.watched_ports)} services")
        
        # Start initial port forwarding for all services
        for name, config in self.watched_ports.items():
            process = self.start_port_forward(name, config)
            if process:
                self.processes[name] = process
                
                # Start monitoring in a separate thread
                monitor_thread = threading.Thread(
                    target=self.monitor_process,
                    args=(name, process, config),
                    daemon=True
                )
                monitor_thread.start()
            else:
                logger.error(f"Failed to start initial port forward for {name}")
        
        # Main monitoring loop
        while self.running:
            time.sleep(30)
            
            # Check if any processes need restarting
            for name, config in self.watched_ports.items():
                if name not in self.processes or self.processes[name].poll() is not None:
                    logger.info(f"Port forward for {name} is not running, restarting...")
                    self.restart_port_forward(name, config)
            
            # Log status
            active_ports = [name for name, process in self.processes.items() if process.poll() is None]
            logger.info(f"Active port forwards: {len(active_ports)}/{len(self.watched_ports)}")
            if len(active_ports) < len(self.watched_ports):
                inactive = [name for name in self.watched_ports.keys() if name not in active_ports]
                logger.warning(f"Inactive services: {inactive}")
            
            # Test connectivity for critical services only
            critical_services = ['grafana', 'prometheus', 'infrastructure-metrics', 'metrics-test-service']
            for name in critical_services:
                if name in self.processes and self.processes[name].poll() is None:
                    if not self.test_service_connectivity(name, self.watched_ports[name]):
                        logger.warning(f"Connectivity test failed for {name}, but process is running")

def main():
    watcher = PortWatcherV2()
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        watcher.cleanup()

if __name__ == "__main__":
    main() 