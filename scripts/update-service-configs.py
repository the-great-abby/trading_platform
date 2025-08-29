#!/usr/bin/env python3
"""
Service Configuration Update Script
Updates Kubernetes ConfigMaps and service configurations to use new external databases
"""

import yaml
import os
import logging
import argparse
import sys
from typing import Dict, List, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/service-config-update_{os.getenv("USER", "unknown")}_{os.getenv("HOSTNAME", "unknown")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ServiceConfigUpdater:
    """Updates service configurations to use new external databases"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
                # New external database URLs (using port forwarding)
        self.new_database_urls = {
            "TIMESCALEDB_URL": "postgresql://postgres:postgres@localhost:11150/trading",
            "VECTOR_STORAGE_URL": "postgresql://postgres:postgres@localhost:11151/trading",
            "AGE_DATABASE_URL": "postgresql://postgres:postgres@localhost:11152/trading",
            "CONFIG_DATABASE_URL": "postgresql://postgres:postgres@localhost:11153/trading",

            # Service-specific database URLs
            "DATABASE_URL": "postgresql://postgres:postgres@localhost:11150/trading",
            "KUBERNETES_VECTOR_DB_URL": "postgresql://postgres:postgres@localhost:11151/trading",
            "FINANCIAL_VECTOR_DB_URL": "postgresql://postgres:postgres@localhost:11151/trading",
        }
        
        # Services that need database URL updates
        self.services_to_update = [
            "unified-analytics-dashboard",
            "unified-trading-dashboard", 
            "unified-news-dashboard",
            "earnings-data-service",
            "market-data-service",
            "rss-feed-service",
            "trading-engine",
            "strategy-service",
            "backtest-api",
            "ai-analysis-service",
            "background-vectorization-service"
        ]
        
        # ConfigMaps to update
        self.configmaps_to_update = [
            "trading-config",
            "trading-platform-config"
        ]
    
    def update_k8s_configmap(self, configmap_path: str) -> bool:
        """Update a Kubernetes ConfigMap file"""
        try:
            logger.info(f"🔧 Updating ConfigMap: {configmap_path}")
            
            if not os.path.exists(configmap_path):
                logger.warning(f"⚠️ ConfigMap not found: {configmap_path}")
                return False
            
            # Read existing ConfigMap
            with open(configmap_path, 'r') as f:
                configmap = yaml.safe_load(f)
            
            if not configmap or 'data' not in configmap:
                logger.warning(f"⚠️ Invalid ConfigMap structure: {configmap_path}")
                return False
            
            # Track changes
            changes_made = False
            
            # Update database URLs
            for old_url, new_url in self.new_database_urls.items():
                if old_url in configmap['data']:
                    old_value = configmap['data'][old_url]
                    if old_value != new_url:
                        if self.dry_run:
                            logger.info(f"🔍 DRY RUN: Would update {old_url} in {configmap_path}")
                            logger.info(f"   Old: {old_value}")
                            logger.info(f"   New: {new_url}")
                        else:
                            configmap['data'][old_url] = new_url
                            changes_made = True
                            logger.info(f"✅ Updated {old_url} in {configmap_path}")
            
            # Save updated ConfigMap
            if changes_made and not self.dry_run:
                with open(configmap_path, 'w') as f:
                    yaml.dump(configmap, f, default_flow_style=False, sort_keys=False)
                logger.info(f"💾 Saved updated ConfigMap: {configmap_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update ConfigMap {configmap_path}: {e}")
            return False
    
    def update_service_yaml(self, service_path: str) -> bool:
        """Update a service YAML file"""
        try:
            logger.info(f"🔧 Updating service: {service_path}")
            
            if not os.path.exists(service_path):
                logger.warning(f"⚠️ Service file not found: {service_path}")
                return False
            
            # Read existing service file
            with open(service_path, 'r') as f:
                service = yaml.safe_load(f)
            
            if not service:
                logger.warning(f"⚠️ Invalid service file: {service_path}")
                return False
            
            # Track changes
            changes_made = False
            
            # Update environment variables in containers
            if 'spec' in service and 'template' in service['spec']:
                containers = service['spec']['template']['spec'].get('containers', [])
                
                for container in containers:
                    if 'env' in container:
                        for env_var in container['env']:
                            if env_var.get('name') == 'DATABASE_URL':
                                old_value = env_var.get('value', '')
                                new_value = self.new_database_urls['DATABASE_URL']
                                
                                if old_value != new_value:
                                    if self.dry_run:
                                        logger.info(f"🔍 DRY RUN: Would update DATABASE_URL in {service_path}")
                                        logger.info(f"   Old: {old_value}")
                                        logger.info(f"   New: {new_value}")
                                    else:
                                        env_var['value'] = new_value
                                        changes_made = True
                                        logger.info(f"✅ Updated DATABASE_URL in {service_path}")
            
            # Save updated service file
            if changes_made and not self.dry_run:
                with open(service_path, 'w') as f:
                    yaml.dump(service, f, default_flow_style=False, sort_keys=False)
                logger.info(f"💾 Saved updated service: {service_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update service {service_path}: {e}")
            return False
    
    def update_service_python(self, service_path: str) -> bool:
        """Update a service Python file"""
        try:
            logger.info(f"🔧 Updating Python service: {service_path}")
            
            if not os.path.exists(service_path):
                logger.warning(f"⚠️ Service file not found: {service_path}")
                return False
            
            # Read existing service file
            with open(service_path, 'r') as f:
                content = f.read()
            
            # Track changes
            changes_made = False
            
            # Update database URLs
            for old_url, new_url in self.new_database_urls.items():
                if old_url in content:
                    old_value = None
                    
                    # Find the old value (look for assignment patterns)
                    import re
                    pattern = rf'{old_url}\s*=\s*os\.getenv\("{old_url}",\s*"([^"]+)"\)'
                    match = re.search(pattern, content)
                    if match:
                        old_value = match.group(1)
                    
                    if old_value and old_value != new_url:
                        if self.dry_run:
                            logger.info(f"🔍 DRY RUN: Would update {old_url} in {service_path}")
                            logger.info(f"   Old: {old_value}")
                            logger.info(f"   New: {new_url}")
                        else:
                            # Replace the old URL with new URL
                            content = content.replace(f'"{old_value}"', f'"{new_url}"')
                            changes_made = True
                            logger.info(f"✅ Updated {old_url} in {service_path}")
            
            # Save updated service file
            if changes_made and not self.dry_run:
                with open(service_path, 'w') as f:
                    f.write(content)
                logger.info(f"💾 Saved updated Python service: {service_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update Python service {service_path}: {e}")
            return False
    
    def update_all_configs(self) -> bool:
        """Update all configurations"""
        logger.info("🚀 Starting service configuration updates...")
        
        success_count = 0
        total_count = 0
        
        # Update ConfigMaps
        for configmap_name in self.configmaps_to_update:
            configmap_path = f"k8s/{configmap_name}.yaml"
            if os.path.exists(configmap_path):
                total_count += 1
                if self.update_k8s_configmap(configmap_path):
                    success_count += 1
            else:
                logger.warning(f"⚠️ ConfigMap not found: {configmap_path}")
        
        # Update service YAML files
        for service_name in self.services_to_update:
            service_path = f"k8s/services/{service_name}.yaml"
            if os.path.exists(service_path):
                total_count += 1
                if self.update_service_yaml(service_path):
                    success_count += 1
            else:
                logger.warning(f"⚠️ Service YAML not found: {service_path}")
        
        # Update service Python files
        for service_name in self.services_to_update:
            service_path = f"services/{service_name}/main.py"
            if os.path.exists(service_path):
                total_count += 1
                if self.update_service_python(service_path):
                    success_count += 1
            else:
                logger.warning(f"⚠️ Service Python not found: {service_path}")
        
        # Update specific files that might have database URLs
        specific_files = [
            "k8s/postgres-deployment.yaml",
            "k8s/setup-database.yaml",
            "k8s/secrets.yaml"
        ]
        
        for file_path in specific_files:
            if os.path.exists(file_path):
                total_count += 1
                if self.update_service_yaml(file_path):
                    success_count += 1
        
        logger.info(f"📊 Configuration update summary: {success_count}/{total_count} successful")
        return success_count == total_count
    
    def create_backup_configs(self) -> bool:
        """Create backup of current configurations"""
        try:
            backup_dir = f"backup/service-configs-{os.getenv('USER', 'unknown')}-{os.getenv('HOSTNAME', 'unknown')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            logger.info(f"💾 Creating backup in: {backup_dir}")
            
            # Backup ConfigMaps
            for configmap_name in self.configmaps_to_update:
                configmap_path = f"k8s/{configmap_name}.yaml"
                if os.path.exists(configmap_path):
                    backup_path = f"{backup_dir}/{configmap_name}.yaml.backup"
                    with open(configmap_path, 'r') as src, open(backup_path, 'w') as dst:
                        dst.write(src.read())
                    logger.info(f"✅ Backed up: {configmap_path}")
            
            # Backup service files
            for service_name in self.services_to_update:
                # YAML files
                service_path = f"k8s/services/{service_name}.yaml"
                if os.path.exists(service_path):
                    backup_path = f"{backup_dir}/{service_name}.yaml.backup"
                    with open(service_path, 'r') as src, open(backup_path, 'w') as dst:
                        dst.write(src.read())
                    logger.info(f"✅ Backed up: {service_path}")
                
                # Python files
                service_path = f"services/{service_name}/main.py"
                if os.path.exists(service_path):
                    backup_path = f"{backup_dir}/{service_name}_main.py.backup"
                    with open(service_path, 'r') as src, open(backup_path, 'w') as dst:
                        dst.write(src.read())
                    logger.info(f"✅ Backed up: {service_path}")
            
            logger.info(f"💾 Backup completed: {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def generate_kubectl_apply_commands(self) -> None:
        """Generate kubectl apply commands for updated configurations"""
        logger.info("📋 Generating kubectl apply commands...")
        
        commands = []
        
        # Apply updated ConfigMaps
        for configmap_name in self.configmaps_to_update:
            configmap_path = f"k8s/{configmap_name}.yaml"
            if os.path.exists(configmap_path):
                commands.append(f"kubectl apply -f {configmap_path}")
        
        # Apply updated service files
        for service_name in self.services_to_update:
            service_path = f"k8s/services/{service_name}.yaml"
            if os.path.exists(service_path):
                commands.append(f"kubectl apply -f {service_path}")
        
        # Restart services to pick up new configurations
        for service_name in self.services_to_update:
            commands.append(f"kubectl rollout restart deployment/{service_name} -n trading-system")
        
        # Print commands
        logger.info("📋 Run these commands to apply the updated configurations:")
        logger.info("=" * 60)
        for cmd in commands:
            logger.info(f"$ {cmd}")
        logger.info("=" * 60)
        
        # Save commands to file
        commands_file = f"logs/kubectl-apply-commands.sh"
        with open(commands_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Generated kubectl apply commands for external database migration\n")
            f.write("# Run this script to apply all updated configurations\n\n")
            for cmd in commands:
                f.write(f"{cmd}\n")
        
        os.chmod(commands_file, 0o755)
        logger.info(f"💾 Commands saved to: {commands_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Update service configurations for external databases")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without actually doing it")
    parser.add_argument("--backup-only", action="store_true", help="Only create backup of current configurations")
    parser.add_argument("--generate-commands", action="store_true", help="Generate kubectl apply commands")
    
    args = parser.parse_args()
    
    # Create updater
    updater = ServiceConfigUpdater(dry_run=args.dry_run)
    
    try:
        if args.backup_only:
            if updater.create_backup_configs():
                logger.info("✅ Backup completed successfully")
                return 0
            else:
                logger.error("❌ Backup failed")
                return 1
        
        if args.generate_commands:
            updater.generate_kubectl_apply_commands()
            return 0
        
        # Full update process
        logger.info("🚀 Starting service configuration update process...")
        
        # Create backup first
        if not updater.create_backup_configs():
            logger.error("❌ Failed to create backup")
            return 1
        
        # Update configurations
        if updater.update_all_configs():
            logger.info("✅ All configurations updated successfully")
            
            # Generate kubectl commands
            updater.generate_kubectl_apply_commands()
            
            logger.info("🎉 Service configuration update completed!")
            logger.info("📋 Next steps:")
            logger.info("   1. Review the changes in the backup directory")
            logger.info("   2. Run the generated kubectl commands")
            logger.info("   3. Test that services are working with new databases")
            
            return 0
        else:
            logger.error("❌ Some configuration updates failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("⏹️ Update interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
