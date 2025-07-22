#!/usr/bin/env python3
"""
Job Generator from Template
Generates Kubernetes jobs from the job template with proper substitutions
"""

import yaml
import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

def load_template(template_path: str) -> Dict[str, Any]:
    """Load the job template YAML file"""
    try:
        with open(template_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading template {template_path}: {e}")
        sys.exit(1)

def substitute_placeholders(template: Dict[str, Any], substitutions: Dict[str, str]) -> Dict[str, Any]:
    """Replace placeholders in the template with actual values"""
    template_str = yaml.dump(template)
    
    for placeholder, value in substitutions.items():
        template_str = template_str.replace(f"{placeholder}_PLACEHOLDER", value)
    
    return yaml.safe_load(template_str)

def generate_job_name(job_type: str, strategy_name: str, symbols: str) -> str:
    """Generate a unique job name"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    symbols_clean = symbols.replace(",", "-").replace(" ", "").lower()
    return f"{job_type}-{strategy_name}-{symbols_clean}-{timestamp}"

def main():
    parser = argparse.ArgumentParser(description="Generate Kubernetes jobs from template")
    parser.add_argument("--job-type", required=True, help="Type of job (backtest, analysis, etc.)")
    parser.add_argument("--strategy-name", required=True, help="Name of the trading strategy")
    parser.add_argument("--symbols", required=True, help="Comma-separated list of symbols")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--image", default="trading-system", help="Docker image to use")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--template", default="k8s/templates/job-template.yaml", help="Template file path")
    
    args = parser.parse_args()
    
    # Load template
    template = load_template(args.template)
    
    # Generate job name
    job_name = generate_job_name(args.job_type, args.strategy_name, args.symbols)
    
    # Prepare substitutions
    substitutions = {
        "JOB_NAME": job_name,
        "JOB_APP": f"{args.job_type}-{args.strategy_name}",
        "IMAGE": args.image,
        "JOB_TYPE": args.job_type,
        "STRATEGY_NAME": args.strategy_name,
        "SYMBOLS": args.symbols,
        "START_DATE": args.start_date,
        "END_DATE": args.end_date
    }
    
    # Generate job
    job = substitute_placeholders(template, substitutions)
    
    # Output
    output_yaml = yaml.dump(job, default_flow_style=False, sort_keys=False)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_yaml)
        print(f"✅ Job generated: {args.output}")
    else:
        print(output_yaml)

if __name__ == "__main__":
    main() 