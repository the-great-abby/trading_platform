#!/usr/bin/env python3
"""
Generate Kubernetes Job YAML for backtest execution
"""

import sys
import yaml
import argparse
from datetime import datetime

def create_backtest_job(script_name, database_only=False, job_name=None, script_args=None):
    """Create a Kubernetes Job YAML for backtest execution"""
    
    if job_name is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        job_name = f"backtest-{timestamp}"
    
    # Build the args list for the container
    container_args = [script_name]
    if script_args:
        container_args.extend(script_args)
    
    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name,
            "namespace": "trading-system"
        },
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "backtest",
                            "image": "trading-bot:latest",
                            "imagePullPolicy": "Never",
                            "command": ["python"],
                            "args": container_args,
                            "env": [
                                {
                                    "name": "DATABASE_ONLY",
                                    "value": str(database_only).lower()
                                },
                                {
                                    "name": "DATABASE_URL",
                                    "value": "postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot"
                                }
                            ],
                            "volumeMounts": [
                                {
                                    "name": "results-volume",
                                    "mountPath": "/app/backtest_results"
                                }
                            ],
                            "resources": {
                                "requests": {
                                    "memory": "512Mi",
                                    "cpu": "250m"
                                },
                                "limits": {
                                    "memory": "1Gi",
                                    "cpu": "500m"
                                }
                            }
                        }
                    ],
                    "volumes": [
                        {
                            "name": "results-volume",
                            "hostPath": {
                                "path": "/tmp/backtest_results",
                                "type": "DirectoryOrCreate"
                            }
                        }
                    ],
                    "restartPolicy": "Never"
                }
            },
            "backoffLimit": 1
        }
    }
    
    return job

def main():
    parser = argparse.ArgumentParser(description="Generate Kubernetes Job YAML for backtest")
    parser.add_argument("script", help="Python script to run")
    parser.add_argument("--database-only", action="store_true", help="Set DATABASE_ONLY=true")
    parser.add_argument("--job-name", help="Custom job name")
    parser.add_argument("--output", help="Output file (default: stdout)")
    
    # Parse known args first to get our script arguments
    args, remaining = parser.parse_known_args()
    
    # Filter out the '--' separator and get the actual script arguments
    script_args = []
    if remaining:
        for arg in remaining:
            if arg != '--':
                script_args.append(arg)
    
    # Set to None if no arguments
    script_args = script_args if script_args else None
    
    job = create_backtest_job(
        script_name=args.script,
        database_only=args.database_only,
        job_name=args.job_name,
        script_args=script_args
    )
    
    yaml_content = yaml.dump(job, default_flow_style=False)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(yaml_content)
        print(f"Job YAML written to {args.output}")
    else:
        print(yaml_content)

if __name__ == "__main__":
    main() 