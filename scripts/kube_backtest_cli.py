#!/usr/bin/env python3
"""
Kubernetes Backtest CLI Runner
This script runs backtest CLI commands in Kubernetes with proper network access.
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def run_kubectl_job(command_args):
    """Run a backtest CLI command in Kubernetes"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_name = f"backtest-cli-{timestamp}"
    
    # Create job YAML
    job_yaml = f"""
apiVersion: batch/v1
kind: Job
metadata:
  name: {job_name}
  namespace: trading-system
spec:
  template:
    spec:
      containers:
      - name: backtest-cli
        image: trading-bot:latest
        imagePullPolicy: IfNotPresent
        command: ["python"]
        args: {json.dumps(command_args)}
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: database-url
        - name: PYTHONPATH
          value: "/app/src"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      restartPolicy: Never
  backoffLimit: 3
"""
    
    # Write job YAML to temporary file
    job_file = f"/tmp/{job_name}.yaml"
    with open(job_file, 'w') as f:
        f.write(job_yaml)
    
    try:
        # Apply the job
        print(f"Creating job: {job_name}")
        subprocess.run(["kubectl", "apply", "-f", job_file], check=True)
        
        # Wait for completion
        print("Waiting for job completion...")
        subprocess.run(["kubectl", "wait", "--for=condition=complete", f"job/{job_name}", "--timeout=60s"], check=True)
        
        # Get logs
        print("Job completed. Getting logs...")
        result = subprocess.run(["kubectl", "logs", f"job/{job_name}"], capture_output=True, text=True, check=True)
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"Error running job: {e}")
        return False
    finally:
        # Clean up
        print(f"Cleaning up job: {job_name}")
        subprocess.run(["kubectl", "delete", "job", job_name], check=False)
        os.remove(job_file)
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python kube_backtest_cli.py <command> [args...]")
        print("Commands:")
        print("  list                    - List backtest runs")
        print("  list --details          - List with detailed information")
        print("  show <run_id>           - Show details for specific run")
        print("  trades <run_id>         - Show trades for specific run")
        print("  compare                 - Compare strategies")
        print("  stats                   - Show statistics")
        sys.exit(1)
    
    command = sys.argv[1]
    args = ["src/scripts/backtest_cli.py"] + sys.argv[1:]
    
    print(f"Running backtest CLI command in Kubernetes: {' '.join(args)}")
    success = run_kubectl_job(args)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 