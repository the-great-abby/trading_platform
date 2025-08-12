#!/usr/bin/env python3
"""
Focused Port Watcher - Monitors only essential services that actually exist
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
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('port_watcher_focused.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FocusedPortWatcher:
    def __init__(self):
        # Only monitor services that actually exist and are important
        self.watched_ports = {
            # Core Monitoring Services
            'grafana': {'local_port': 11044, 'target_port': 3000, 'service': 'grafana'},
            'prometheus': {'local_port': 11190, 'target_port': 11190, 'service': 'prometheus'},
            
            # Essential Dashboard Services
            'unified-analytics-dashboard': {'local_port': 11114, 'target_port': 80, 'service': 'unified-analytics-dashboard'},
            'unified-trading-dashboard': {'local_port': 11115, 'target_port': 80, 'service': 'unified-trading-dashboard'},
            'unified-news-dashboard': {'local_port': 11113, 'target_port': 80, 'service': 'unified-news-dashboard'},
            
            # Core Trading Services
            'trading-core-service': {'local_port': 11090, 'target_port': 11090, 'service': 'trading-core-service'},
            'strategy-service': {'local_port': 11103, 'target_port': 80, 'service': 'strategy-service'},
            'market-data-service': {'local_port': 11084, 'target_port': 11084, 'service': 'market-data-service'},
            
            # AI Services
            'ai-analysis-service': {'local_port': 11085, 'target_port': 11085, 'service': 'ai-analysis-service'},
            'kubernetes-rag-chat': {'local_port': 11117, 'target_port': 8000, 'service': 'kubernetes-rag-chat'},
            
            # Infrastructure Services
            'background-vectorization-service': {'local_port': 11116, 'target_port': 8080, 'service': 'background-vectorization-service'},
            'postgres-vector-storage': {'local_port': 11106, 'target_port': 80, 'service': 'postgres-vector-storage'},
            
            # Database Services
            'timescaledb': {'local_port': 11140, 'target_port': 5432, 'service': 'timescaledb'},
            'redis': {'local_port': 11142, 'target_port': 6379, 'service': 'redis'},
            'rabbitmq': {'local_port': 11144, 'target_port': 5672, 'service': 'rabbitmq'},
        }
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True
        self.log_dir = "port_watcher_focused_logs"
        
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
    
    def capture_connectivity_failure_logs(self, name: str, config: Dict, failure_reason: str):
        """Capture logs when connectivity tests fail but port forwarding is still running"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        connectivity_log_file = os.path.join(self.log_dir, f"{name}_connectivity_failure_{timestamp}.log")
        
        logger.warning(f"Connectivity test failed for {name}: {failure_reason}. Capturing diagnostic information...")
        
        with open(connectivity_log_file, 'w') as f:
            f.write(f"=== CONNECTIVITY FAILURE REPORT ===\n")
            f.write(f"Service: {name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Failure Reason: {failure_reason}\n")
            f.write(f"Local Port: {config['local_port']}\n")
            f.write(f"Target Port: {config['target_port']}\n")
            f.write(f"Target Service: {config['service']}\n\n")
            
            # Get container logs from the service
            f.write(f"=== CONTAINER LOGS ===\n")
            try:
                # Get the specific pod name for this service
                cmd = [
                    'kubectl', 'get', 'pods', '-n', 'trading-system',
                    '-l', f'app={config["service"]}', '--no-headers', '-o', 'custom-columns=NAME:.metadata.name'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    pod_name = result.stdout.strip().split('\n')[0]  # Get first pod
                    f.write(f"Pod: {pod_name}\n")
                    
                    # Get recent container logs (last 30 lines)
                    cmd = [
                        'kubectl', 'logs', pod_name, '-n', 'trading-system', '--tail=30'
                    ]
                    log_result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    if log_result.returncode == 0:
                        f.write(f"Container Logs (last 30 lines):\n{log_result.stdout}\n")
                    else:
                        f.write(f"Failed to get container logs: {log_result.stderr}\n")
                        
                else:
                    f.write("No pods found for this service\n")
            except Exception as e:
                f.write(f"Error getting container logs: {str(e)}\n")
            f.write("\n\n")
            
            # Get service health check details
            f.write(f"=== SERVICE HEALTH STATUS ===\n")
            try:
                # Check if the service is actually responding
                if name == 'grafana':
                    cmd = ['curl', '-s', '-u', 'admin:admin', f'http://localhost:{config["local_port"]}/api/health', '--max-time', '5']
                elif 'dashboard' in name.lower():
                    cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/health', '--max-time', '5']
                else:
                    cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/', '--max-time', '5']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                f.write(f"Health Check Command: {' '.join(cmd)}\n")
                f.write(f"Health Check Exit Code: {result.returncode}\n")
                f.write(f"Health Check Response: {result.stdout[:500]}...\n")  # First 500 chars
                f.write(f"Health Check Errors: {result.stderr}\n")
            except Exception as e:
                f.write(f"Error performing health check: {str(e)}\n")
            f.write("\n\n")
            
            # Get port usage information
            f.write(f"=== PORT USAGE ANALYSIS ===\n")
            try:
                cmd = ['lsof', '-i', f':{config["local_port"]}']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    f.write(f"Port {config['local_port']} Usage:\n{result.stdout}\n")
                else:
                    f.write(f"Port {config['local_port']} not in use\n")
            except Exception as e:
                f.write(f"Error checking port usage: {str(e)}\n")
            f.write("\n\n")
        
        logger.info(f"Connectivity failure report saved to: {connectivity_log_file}")

    def capture_healthy_service_logs(self, name: str, config: Dict):
        """Capture logs from healthy services for baseline comparison"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        healthy_log_file = os.path.join(self.log_dir, f"{name}_healthy_baseline_{timestamp}.log")
        
        logger.debug(f"Capturing baseline logs for healthy service: {name}")
        
        with open(healthy_log_file, 'w') as f:
            f.write(f"=== HEALTHY SERVICE BASELINE ===\n")
            f.write(f"Service: {name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Local Port: {config['local_port']}\n")
            f.write(f"Target Port: {config['target_port']}\n")
            f.write(f"Target Service: {config['service']}\n\n")
            
            # Get container logs from the healthy service
            f.write(f"=== CONTAINER LOGS (BASELINE) ===\n")
            try:
                # Get the specific pod name for this service
                cmd = [
                    'kubectl', 'get', 'pods', '-n', 'trading-system',
                    '-l', f'app={config["service"]}', '--no-headers', '-o', 'custom-columns=NAME:.metadata.name'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    pod_name = result.stdout.strip().split('\n')[0]  # Get first pod
                    f.write(f"Pod: {pod_name}\n")
                    
                    # Get recent container logs (last 20 lines)
                    cmd = [
                        'kubectl', 'logs', pod_name, '-n', 'trading-system', '--tail=20'
                    ]
                    log_result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    if log_result.returncode == 0:
                        f.write(f"Container Logs (last 20 lines):\n{log_result.stdout}\n")
                    else:
                        f.write(f"Failed to get container logs: {log_result.stderr}\n")
                        
                else:
                    f.write("No pods found for this service\n")
            except Exception as e:
                f.write(f"Error getting container logs: {str(e)}\n")
            f.write("\n\n")
            
            # Get service health response
            f.write(f"=== HEALTH CHECK RESPONSE ===\n")
            try:
                if name == 'grafana':
                    cmd = ['curl', '-s', '-u', 'admin:admin', f'http://localhost:{config["local_port"]}/api/health']
                elif 'dashboard' in name.lower():
                    cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/health']
                else:
                    cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                f.write(f"Health Check Command: {' '.join(cmd)}\n")
                f.write(f"Health Check Exit Code: {result.returncode}\n")
                f.write(f"Health Check Response: {result.stdout[:200]}...\n")  # First 200 chars
            except Exception as e:
                f.write(f"Error performing health check: {str(e)}\n")
            f.write("\n\n")
        
        # Clean up old baseline logs (keep only last 5)
        self.cleanup_old_logs(name, "healthy_baseline", 5)

    def cleanup_old_logs(self, service_name: str, log_type: str, keep_count: int):
        """Clean up old log files to prevent disk space issues"""
        try:
            pattern = os.path.join(self.log_dir, f"{service_name}_{log_type}_*.log")
            log_files = glob.glob(pattern)
            if len(log_files) > keep_count:
                # Sort by modification time and remove oldest
                log_files.sort(key=os.path.getmtime)
                for old_file in log_files[:-keep_count]:
                    os.remove(old_file)
                    logger.debug(f"Cleaned up old log file: {old_file}")
        except Exception as e:
            logger.debug(f"Error cleaning up old logs: {str(e)}")

    def test_service_connectivity(self, name: str, config: Dict) -> bool:
        """Test if a service is actually accessible"""
        try:
            if name == 'grafana':
                cmd = ['curl', '-s', '-u', 'admin:admin', f'http://localhost:{config["local_port"]}/api/health']
            elif name == 'prometheus':
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/-/healthy']
            elif 'dashboard' in name.lower():
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/health']
            elif 'service' in name.lower():
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/health']
            else:
                cmd = ['curl', '-s', f'http://localhost:{config["local_port"]}/']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and len(result.stdout) > 0:
                return True
            else:
                # Capture detailed logs when connectivity test fails
                failure_reason = f"HTTP {result.returncode}, Response: {result.stdout[:100]}..."
                self.capture_connectivity_failure_logs(name, config, failure_reason)
                return False
                
        except subprocess.TimeoutExpired:
            # Capture detailed logs when connectivity test times out
            self.capture_connectivity_failure_logs(name, config, "Timeout after 15 seconds")
            return False
        except Exception as e:
            # Capture detailed logs when connectivity test has other errors
            self.capture_connectivity_failure_logs(name, config, f"Error: {str(e)}")
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
        """Monitor a port forwarding process and handle failures"""
        logger.info(f"Starting monitor for {name}")
        
        # Capture initial baseline logs for healthy service
        self.capture_healthy_service_logs(name, config)
        
        last_baseline_capture = time.time()
        baseline_interval = 3600  # Capture baseline every hour
        
        while self.running and process.poll() is None:
            time.sleep(10)
            
            # Test connectivity every 30 seconds for critical services
            if name in ['grafana', 'unified-analytics-dashboard', 'unified-trading-dashboard', 'unified-news-dashboard']:
                if self.test_service_connectivity(name, config):
                    logger.debug(f"{name} connectivity test passed")
                    
                    # Periodically capture baseline logs from healthy services
                    current_time = time.time()
                    if current_time - last_baseline_capture > baseline_interval:
                        self.capture_healthy_service_logs(name, config)
                        last_baseline_capture = current_time
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
            
            # Get pod status and details
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
            
            # Get container logs from the failing pod
            f.write(f"=== CONTAINER LOGS ===\n")
            try:
                # Get the specific pod name for this service
                cmd = [
                    'kubectl', 'get', 'pods', '-n', 'trading-system',
                    '-l', f'app={config["service"]}', '--no-headers', '-o', 'custom-columns=NAME:.metadata.name'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    pod_name = result.stdout.strip().split('\n')[0]  # Get first pod
                    f.write(f"Pod: {pod_name}\n")
                    
                    # Get recent container logs (last 50 lines)
                    cmd = [
                        'kubectl', 'logs', pod_name, '-n', 'trading-system', '--tail=50'
                    ]
                    log_result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    if log_result.returncode == 0:
                        f.write(f"Container Logs (last 50 lines):\n{log_result.stdout}\n")
                    else:
                        f.write(f"Failed to get container logs: {log_result.stderr}\n")
                    
                    # Get container events
                    cmd = [
                        'kubectl', 'describe', 'pod', pod_name, '-n', 'trading-system'
                    ]
                    events_result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    if events_result.returncode == 0:
                        # Extract just the Events section
                        events_output = events_result.stdout
                        if 'Events:' in events_output:
                            events_start = events_output.find('Events:')
                            events_section = events_output[events_start:]
                            f.write(f"Pod Events:\n{events_section}\n")
                        else:
                            f.write("No events found in pod description\n")
                    else:
                        f.write(f"Failed to get pod description: {events_result.stderr}\n")
                        
                else:
                    f.write("No pods found for this service\n")
            except Exception as e:
                f.write(f"Error getting container logs: {str(e)}\n")
            f.write("\n\n")
            
            # Get service details
            f.write(f"=== SERVICE DETAILS ===\n")
            try:
                cmd = [
                    'kubectl', 'describe', 'service', config['service'], '-n', 'trading-system'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    f.write(result.stdout)
                else:
                    f.write(f"Failed to get service details: {result.stderr}")
            except Exception as e:
                f.write(f"Error getting service details: {str(e)}")
            f.write("\n\n")
            
            # Get recent cluster events that might be related
            f.write(f"=== RECENT CLUSTER EVENTS ===\n")
            try:
                cmd = [
                    'kubectl', 'get', 'events', '-n', 'trading-system', '--sort-by=.metadata.creationTimestamp', '--no-headers'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Get last 20 events
                    events = result.stdout.strip().split('\n')[-20:] if result.stdout.strip() else []
                    for event in events:
                        f.write(f"{event}\n")
                else:
                    f.write(f"Failed to get cluster events: {result.stderr}")
            except Exception as e:
                f.write(f"Error getting cluster events: {str(e)}")
            f.write("\n\n")
        
        logger.info(f"Failure report saved to: {failure_log_file}")
        
        # Clean up old failure logs (keep only last 10)
        self.cleanup_old_logs(name, "failure", 10)
        
        # Remove from processes dict
        if name in self.processes:
            del self.processes[name]
        
        # Auto-restart critical services
        if name in ['grafana', 'unified-analytics-dashboard', 'unified-trading-dashboard', 'unified-news-dashboard']:
            logger.info(f"Auto-restarting critical service: {name}")
            self.restart_port_forward(name, config)
    
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
        logger.info("Starting Focused Port Watcher...")
        logger.info(f"Monitoring {len(self.watched_ports)} essential services")
        
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
            
            # Check if any critical services are down
            for name, config in self.watched_ports.items():
                if name in ['grafana', 'unified-analytics-dashboard', 'unified-trading-dashboard', 'unified-news-dashboard']:
                    if name not in self.processes or (self.processes[name] and self.processes[name].poll() is not None):
                        logger.warning(f"Critical service {name} is down, restarting...")
                        self.restart_port_forward(name, config)
        
        logger.info("Focused Port Watcher stopped")

if __name__ == "__main__":
    watcher = FocusedPortWatcher()
    watcher.run()
