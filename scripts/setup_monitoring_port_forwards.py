#!/usr/bin/env python3
"""
Setup Live Trading Monitoring Port Forwards
Sets up port forwarding for the new live trading monitoring services
"""

import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_monitoring_port_forwards():
    """Setup port forwarding for live trading monitoring services"""
    logger.info("🚀 Setting up Live Trading Monitoring port forwards...")
    
    # Port forwarding commands
    port_forwards = [
        {
            'name': 'Live Trading Monitoring Dashboard',
            'command': 'kubectl port-forward svc/live-trading-monitoring-dashboard 11180:8080 -n trading-system',
            'port': 11180,
            'url': 'http://localhost:11180/'
        },
        {
            'name': 'Live Trading Monitoring API', 
            'command': 'kubectl port-forward svc/live-trading-monitoring-api 11181:8081 -n trading-system',
            'port': 11181,
            'url': 'http://localhost:11181/'
        }
    ]
    
    # Start port forwards
    for pf in port_forwards:
        try:
            logger.info(f"🔧 Starting port forward for {pf['name']}...")
            
            # Start the port forward in background
            process = subprocess.Popen(
                pf['command'].split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment to check if it started successfully
            time.sleep(2)
            
            if process.poll() is None:
                logger.info(f"✅ {pf['name']} port forward started successfully")
                logger.info(f"   📱 Dashboard: {pf['url']}")
                logger.info(f"   🔌 Port: {pf['port']}")
            else:
                logger.warning(f"⚠️ {pf['name']} port forward may have failed")
                
        except Exception as e:
            logger.error(f"❌ Error starting port forward for {pf['name']}: {e}")
    
    logger.info("🎉 Live Trading Monitoring port forwards setup complete!")
    logger.info("📊 Access the monitoring dashboard at: http://localhost:11180/")
    logger.info("🔌 Access the monitoring API at: http://localhost:11181/")

if __name__ == "__main__":
    setup_monitoring_port_forwards()




