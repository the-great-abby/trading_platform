#!/usr/bin/env python3
"""
Generate and Deploy Reports to Kubernetes
Generates HTML reports and copies them to the Kubernetes volume
"""

import sys
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.report_service import ReportService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_reports():
    """Generate latest backtest reports"""
    try:
        logger.info("📊 Generating latest backtest reports...")
        
        # Initialize report service
        report_service = ReportService(output_dir="reports")
        
        # Generate reports for latest runs
        report_paths = report_service.generate_latest_reports(limit=10)
        
        if report_paths:
            logger.info(f"✅ Generated {len(report_paths)} reports:")
            for path in report_paths:
                logger.info(f"   - {path}")
        else:
            logger.warning("⚠️  No reports generated")
        
        return report_paths
        
    except Exception as e:
        logger.error(f"❌ Error generating reports: {e}")
        return []


def copy_reports_to_k8s():
    """Copy reports to Kubernetes volume"""
    try:
        logger.info("📁 Copying reports to Kubernetes volume...")
        
        # Create a temporary pod to copy files
        pod_name = f"reports-copy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create a pod with the reports volume mounted
        pod_yaml = f"""
apiVersion: v1
kind: Pod
metadata:
  name: {pod_name}
  namespace: trading-system
spec:
  containers:
  - name: copy-reports
    image: busybox
    command: ['sleep', '3600']
    volumeMounts:
    - name: reports-volume
      mountPath: /reports
  volumes:
  - name: reports-volume
    persistentVolumeClaim:
      claimName: reports-pvc
  restartPolicy: Never
"""
        
        # Apply the pod
        with open("/tmp/copy-pod.yaml", "w") as f:
            f.write(pod_yaml)
        
        subprocess.run(["kubectl", "apply", "-f", "/tmp/copy-pod.yaml"], check=True)
        
        # Wait for pod to be ready
        subprocess.run(["kubectl", "wait", "--for=condition=Ready", f"pod/{pod_name}", "-n", "trading-system"], check=True)
        
        # Copy reports to the pod
        reports_dir = Path("reports/html")
        if reports_dir.exists():
            for html_file in reports_dir.glob("*.html"):
                logger.info(f"📋 Copying {html_file.name} to Kubernetes...")
                subprocess.run([
                    "kubectl", "cp", 
                    str(html_file), 
                    f"trading-system/{pod_name}:/reports/html/{html_file.name}"
                ], check=True)
        
        # Delete the temporary pod
        subprocess.run(["kubectl", "delete", "pod", pod_name, "-n", "trading-system"], check=True)
        
        logger.info("✅ Reports copied to Kubernetes volume")
        
    except Exception as e:
        logger.error(f"❌ Error copying reports to Kubernetes: {e}")
        # Clean up pod if it exists
        try:
            subprocess.run(["kubectl", "delete", "pod", pod_name, "-n", "trading-system"], check=False)
        except:
            pass


def restart_gateway():
    """Restart the gateway to pick up new reports"""
    try:
        logger.info("🔄 Restarting gateway to pick up new reports...")
        
        # Restart the gateway deployment
        subprocess.run([
            "kubectl", "rollout", "restart", "deployment/trading-gateway", "-n", "trading-system"
        ], check=True)
        
        # Wait for rollout to complete
        subprocess.run([
            "kubectl", "rollout", "status", "deployment/trading-gateway", "-n", "trading-system"
        ], check=True)
        
        logger.info("✅ Gateway restarted successfully")
        
    except Exception as e:
        logger.error(f"❌ Error restarting gateway: {e}")


def get_gateway_url():
    """Get the gateway URL"""
    try:
        # Get the gateway service URL
        result = subprocess.run([
            "kubectl", "get", "service", "trading-gateway", "-n", "trading-system", "-o", "jsonpath={.status.loadBalancer.ingress[0].ip}"
        ], capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            return f"http://{result.stdout.strip()}"
        else:
            # Try to get the port-forward URL
            return "http://localhost:8080"
            
    except Exception as e:
        logger.warning(f"⚠️  Could not get gateway URL: {e}")
        return "http://localhost:8080"


def main():
    """Main function"""
    print("🚀 Generating and Deploying Reports to Kubernetes")
    print("=" * 50)
    
    # Step 1: Generate reports
    report_paths = generate_reports()
    
    if not report_paths:
        print("❌ No reports generated. Exiting.")
        return
    
    # Step 2: Copy reports to Kubernetes
    copy_reports_to_k8s()
    
    # Step 3: Restart gateway
    restart_gateway()
    
    # Step 4: Get gateway URL
    gateway_url = get_gateway_url()
    
    print("\n🎉 Reports deployed successfully!")
    print(f"📊 View reports at: {gateway_url}/reports")
    print(f"📋 API endpoint: {gateway_url}/api/v1/reports")
    print("\n💡 You can now:")
    print("   • Click 'Reports' in your trading dashboard")
    print("   • Access reports via the gateway API")
    print("   • View reports directly in your browser")


if __name__ == "__main__":
    main() 