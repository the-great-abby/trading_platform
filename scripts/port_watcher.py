#!/usr/bin/env python3
"""
Port Watcher - Monitors kubectl port-forward connections and captures logs on failure
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
        logging.FileHandler('port_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PortWatcher:
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
            'market-data-service': {'local_port': 11109, 'target_port': 80, 'service': 'market-data-service'},
            
            # AI and Analytics Services
            'ai-analysis-service': {'local_port': 11110, 'target_port': 11085, 'service': 'ai-analysis-service'},
            'ai-stock-dashboard': {'local_port': 11111, 'target_port': 80, 'service': 'ai-stock-dashboard'},
            'llm-service': {'local_port': 11112, 'target_port': 11109, 'service': 'llm-service'},
            'analytics-service': {'local_port': 11113, 'target_port': 80, 'service': 'analytics-service'},
            
            # Dashboard Services
            'health-dashboard': {'local_port': 11114, 'target_port': 80, 'service': 'health-dashboard'},
            'performance-dashboard': {'local_port': 11115, 'target_port': 80, 'service': 'performance-dashboard'},
            'central-hub-dashboard': {'local_port': 11116, 'target_port': 80, 'service': 'central-hub-dashboard'},
            'rss-dashboard': {'local_port': 11117, 'target_port': 80, 'service': 'rss-dashboard'},
            'trading-dashboard': {'local_port': 11118, 'target_port': 8080, 'service': 'trading-dashboard'},
            
            # Backtesting Services
            'backtest-api': {'local_port': 11119, 'target_port': 11101, 'service': 'backtest-api'},
            'backtest-request-service': {'local_port': 11120, 'target_port': 80, 'service': 'backtest-request-service'},
            
            # Data and Processing Services
            'data-processing-service': {'local_port': 11121, 'target_port': 11095, 'service': 'data-processing-service'},
            'market-data-worker': {'local_port': 11122, 'target_port': 11108, 'service': 'market-data-worker'},
            'postgres-vector-storage': {'local_port': 11123, 'target_port': 80, 'service': 'postgres-vector-storage'},
            
            # Management Services
            'strategy-management-service': {'local_port': 11124, 'target_port': 8000, 'service': 'strategy-management-service'},
            'order-management-service': {'local_port': 11125, 'target_port': 8000, 'service': 'order-management-service'},
            'signal-management-service': {'local_port': 11126, 'target_port': 8002, 'service': 'signal-management-service'},
            'risk-management-service': {'local_port': 11127, 'target_port': 8003, 'service': 'risk-management-service'},
            
            # Additional Services
            'notification-service': {'local_port': 11128, 'target_port': 80, 'service': 'notification-service'},
            'public-api': {'local_port': 11129, 'target_port': 80, 'service': 'public-api'},
            'report-viewer-service': {'local_port': 11130, 'target_port': 80, 'service': 'report-viewer-service'},
            'rss-feed-service': {'local_port': 11131, 'target_port': 11004, 'service': 'rss-feed-service'},
            'trading-core-service': {'local_port': 11132, 'target_port': 11090, 'service': 'trading-core-service'},
            'trading-ultra-service': {'local_port': 11133, 'target_port': 80, 'service': 'trading-ultra-service'},
            
            # Test Services
            'metrics-test-service': {'local_port': 11134, 'target_port': 11100, 'service': 'metrics-test-service'},
        }
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True
        self.log_dir = "port_watcher_logs"
        
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
    
    def get_pod_logs(self, service_name: str, lines: int = 50) -> str:
        """Get logs from the most recent pod for a service"""
        try:
            # Get the most recent pod for the service
            cmd = [
                'kubectl', 'get', 'pods', '-n', 'trading-system',
                '-l', f'app={service_name}', '--sort-by=.metadata.creationTimestamp',
                '-o', 'jsonpath={.items[-1].metadata.name}'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0 or not result.stdout.strip():
                return f"Could not find pod for service {service_name}"
            
            pod_name = result.stdout.strip()
            logger.info(f"Getting logs for pod: {pod_name}")
            
            # Get logs from the pod
            cmd = ['kubectl', 'logs', '-n', 'trading-system', pod_name, f'--tail={lines}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Failed to get logs: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Timeout getting pod logs"
        except Exception as e:
            return f"Error getting pod logs: {str(e)}"
    
    def get_pod_status(self, service_name: str) -> str:
        """Get current pod status for a service"""
        try:
            cmd = [
                'kubectl', 'get', 'pods', '-n', 'trading-system',
                '-l', f'app={service_name}', '-o', 'wide'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Failed to get pod status: {result.stderr}"
                
        except Exception as e:
            return f"Error getting pod status: {str(e)}"
    
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
            time.sleep(2)
            
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
            time.sleep(1)
        
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
            pod_status = self.get_pod_status(config['service'])
            f.write(pod_status)
            f.write("\n\n")
            
            # Get pod logs
            f.write(f"=== POD LOGS ===\n")
            pod_logs = self.get_pod_logs(config['service'])
            f.write(pod_logs)
            f.write("\n\n")
            
            # Get recent events
            f.write(f"=== RECENT EVENTS ===\n")
            try:
                cmd = ['kubectl', 'get', 'events', '-n', 'trading-system', '--sort-by=.lastTimestamp', '--tail=20']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    f.write(result.stdout)
                else:
                    f.write(f"Failed to get events: {result.stderr}")
            except Exception as e:
                f.write(f"Error getting events: {str(e)}")
        
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
        logger.info("Starting Port Watcher...")
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
            time.sleep(10)
            
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

def main():
    watcher = PortWatcher()
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        watcher.cleanup()

if __name__ == "__main__":
    main() 