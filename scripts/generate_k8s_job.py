#!/usr/bin/env python3
"""
Kubernetes Job Generator
Generates Kubernetes job YAML files from templates with customizable parameters.
"""

import os
import sys
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class K8sJobGenerator:
    def __init__(self, templates_dir: str = "k8s/job-templates"):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path("k8s/generated")
        self.output_dir.mkdir(exist_ok=True)
    
    def load_template(self, template_name: str) -> str:
        """Load a template file"""
        template_path = self.templates_dir / f"{template_name}.yaml"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r') as f:
            return f.read()
    
    def replace_placeholders(self, template: str, params: Dict[str, Any]) -> str:
        """Replace placeholders in template with actual values"""
        result = template
        
        for key, value in params.items():
            placeholder = f"{{{{{key}}}}}"
            
            if isinstance(value, list):
                # Handle list values (like args, command)
                if key in ['ARGS', 'COMMAND']:
                    yaml_list = yaml.dump(value, default_flow_style=True).strip()
                    result = result.replace(placeholder, yaml_list)
                else:
                    # Handle custom env vars list
                    env_vars = []
                    for item in value:
                        if isinstance(item, dict):
                            env_vars.append(f"- name: {item['name']}\n          value: \"{item['value']}\"")
                        else:
                            env_vars.append(f"- name: {item}")
                    result = result.replace(placeholder, '\n        '.join(env_vars))
            elif isinstance(value, dict):
                # Handle dict values (like volume mounts)
                yaml_dict = yaml.dump(value, default_flow_style=True).strip()
                result = result.replace(placeholder, yaml_dict)
            else:
                result = result.replace(placeholder, str(value))
        
        return result
    
    def generate_backtest_job(self, 
                             script_name: str,
                             job_name: Optional[str] = None,
                             symbols: Optional[str] = None,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             use_llm: bool = False,
                             memory_request: str = "512Mi",
                             memory_limit: str = "1Gi",
                             cpu_request: str = "250m",
                             cpu_limit: str = "500m") -> str:
        """Generate a backtest job"""
        
        if not job_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            job_name = f"backtest-{script_name.replace('.py', '')}-{timestamp}"
        
        # Custom environment variables
        custom_env_vars = []
        if symbols:
            custom_env_vars.append({"name": "BACKTEST_SYMBOLS", "value": symbols})
        if start_date:
            custom_env_vars.append({"name": "BACKTEST_START_DATE", "value": start_date})
        if end_date:
            custom_env_vars.append({"name": "BACKTEST_END_DATE", "value": end_date})
        if use_llm:
            custom_env_vars.extend([
                {"name": "USE_LLM_EVALUATION", "value": "true"},
                {"name": "OLLAMA_MODEL", "value": "granite3.3:2b"},
                {"name": "OLLAMA_TIMEOUT", "value": "60"},
                {"name": "OLLAMA_RETRIES", "value": "3"}
            ])
        
        params = {
            "JOB_NAME": job_name,
            "APP_NAME": "backtest",
            "COMPONENT": "data-analysis",
            "JOB_TYPE": "backtest",
            "CONTAINER_NAME": "backtest",
            "IMAGE": "localhost:32000/trading-system:latest",
            "IMAGE_PULL_POLICY": "Always",
            "COMMAND": ["python"],
            "ARGS": [script_name],
            "LOG_LEVEL": "INFO",
            "MEMORY_REQUEST": memory_request,
            "MEMORY_LIMIT": memory_limit,
            "CPU_REQUEST": cpu_request,
            "CPU_LIMIT": cpu_limit,
            "BACKOFF_LIMIT": 3,
            "CUSTOM_ENV_VARS": self._format_env_vars(custom_env_vars),
            "CUSTOM_VOLUME_MOUNTS": "",
            "CUSTOM_VOLUMES": ""
        }
        
        template = self.load_template("base-job-template")
        return self.replace_placeholders(template, params)
    
    def generate_analysis_job(self,
                             script_name: str,
                             job_name: Optional[str] = None,
                             **kwargs) -> str:
        """Generate an analysis job"""
        
        if not job_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            job_name = f"analyze-{script_name.replace('.py', '')}-{timestamp}"
        
        params = {
            "JOB_NAME": job_name,
            "APP_NAME": "analysis",
            "COMPONENT": "data-analysis",
            "JOB_TYPE": "analysis",
            "CONTAINER_NAME": "analysis",
            "IMAGE": "localhost:32000/trading-system:latest",
            "IMAGE_PULL_POLICY": "Always",
            "COMMAND": ["python"],
            "ARGS": [script_name],
            "LOG_LEVEL": "INFO",
            "MEMORY_REQUEST": kwargs.get("memory_request", "512Mi"),
            "MEMORY_LIMIT": kwargs.get("memory_limit", "1Gi"),
            "CPU_REQUEST": kwargs.get("cpu_request", "250m"),
            "CPU_LIMIT": kwargs.get("cpu_limit", "500m"),
            "BACKOFF_LIMIT": 2,
            "CUSTOM_ENV_VARS": self._format_env_vars(kwargs.get("custom_env_vars", [])),
            "CUSTOM_VOLUME_MOUNTS": "",
            "CUSTOM_VOLUMES": ""
        }
        
        template = self.load_template("base-job-template")
        return self.replace_placeholders(template, params)
    
    def generate_data_job(self,
                          script_name: str,
                          job_name: Optional[str] = None,
                          **kwargs) -> str:
        """Generate a data processing job"""
        
        if not job_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            job_name = f"data-{script_name.replace('.py', '')}-{timestamp}"
        
        params = {
            "JOB_NAME": job_name,
            "APP_NAME": "data-processing",
            "COMPONENT": "data-ingestion",
            "JOB_TYPE": "data",
            "CONTAINER_NAME": "data-processor",
            "IMAGE": "localhost:32000/trading-system:latest",
            "IMAGE_PULL_POLICY": "Always",
            "COMMAND": ["python"],
            "ARGS": [script_name],
            "LOG_LEVEL": "INFO",
            "MEMORY_REQUEST": kwargs.get("memory_request", "256Mi"),
            "MEMORY_LIMIT": kwargs.get("memory_limit", "512Mi"),
            "CPU_REQUEST": kwargs.get("cpu_request", "100m"),
            "CPU_LIMIT": kwargs.get("cpu_limit", "200m"),
            "BACKOFF_LIMIT": 3,
            "CUSTOM_ENV_VARS": self._format_env_vars(kwargs.get("custom_env_vars", [])),
            "CUSTOM_VOLUME_MOUNTS": "",
            "CUSTOM_VOLUMES": ""
        }
        
        template = self.load_template("base-job-template")
        return self.replace_placeholders(template, params)
    
    def _format_env_vars(self, env_vars: list) -> str:
        """Format environment variables for template"""
        if not env_vars:
            return ""
        
        formatted = []
        for var in env_vars:
            if isinstance(var, dict):
                formatted.append(f"- name: {var['name']}\n          value: \"{var['value']}\"")
            else:
                formatted.append(f"- name: {var}")
        
        return '\n        '.join(formatted)
    
    def save_job(self, job_yaml: str, filename: str) -> str:
        """Save job YAML to file"""
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            f.write(job_yaml)
        return str(output_path)
    
    def apply_job(self, job_yaml: str, filename: str) -> str:
        """Save and apply job to Kubernetes"""
        output_path = self.save_job(job_yaml, filename)
        
        # Apply to Kubernetes
        os.system(f"kubectl apply -f {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Generate Kubernetes jobs from templates")
    parser.add_argument("--type", choices=["backtest", "analysis", "data"], required=True,
                       help="Type of job to generate")
    parser.add_argument("--script", required=True, help="Python script to run")
    parser.add_argument("--name", help="Custom job name")
    parser.add_argument("--symbols", help="Comma-separated symbols for backtest")
    parser.add_argument("--start-date", help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--use-llm", action="store_true", help="Enable LLM evaluation")
    parser.add_argument("--memory-request", default="512Mi", help="Memory request")
    parser.add_argument("--memory-limit", default="1Gi", help="Memory limit")
    parser.add_argument("--cpu-request", default="250m", help="CPU request")
    parser.add_argument("--cpu-limit", default="500m", help="CPU limit")
    parser.add_argument("--apply", action="store_true", help="Apply job to Kubernetes")
    parser.add_argument("--output", help="Output filename")
    
    args = parser.parse_args()
    
    generator = K8sJobGenerator()
    
    # Generate job based on type
    if args.type == "backtest":
        job_yaml = generator.generate_backtest_job(
            script_name=args.script,
            job_name=args.name,
            symbols=args.symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            use_llm=args.use_llm,
            memory_request=args.memory_request,
            memory_limit=args.memory_limit,
            cpu_request=args.cpu_request,
            cpu_limit=args.cpu_limit
        )
    elif args.type == "analysis":
        job_yaml = generator.generate_analysis_job(
            script_name=args.script,
            job_name=args.name,
            memory_request=args.memory_request,
            memory_limit=args.memory_limit,
            cpu_request=args.cpu_request,
            cpu_limit=args.cpu_limit
        )
    elif args.type == "data":
        job_yaml = generator.generate_data_job(
            script_name=args.script,
            job_name=args.name,
            memory_request=args.memory_request,
            memory_limit=args.memory_limit,
            cpu_request=args.cpu_request,
            cpu_limit=args.cpu_limit
        )
    
    # Determine output filename
    if args.output:
        filename = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{args.type}-{args.script.replace('.py', '')}-{timestamp}.yaml"
    
    # Save or apply job
    if args.apply:
        output_path = generator.apply_job(job_yaml, filename)
        print(f"✅ Job applied to Kubernetes: {output_path}")
    else:
        output_path = generator.save_job(job_yaml, filename)
        print(f"✅ Job saved to: {output_path}")
        print(f"To apply: kubectl apply -f {output_path}")

if __name__ == "__main__":
    main() 