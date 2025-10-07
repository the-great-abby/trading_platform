#!/usr/bin/env python3
"""
Migration Script: Enhanced Portfolio Management Services
Migrates from existing portfolio-service and risk-service to enhanced versions
"""

import subprocess
import sys
import time
import json
import requests
from typing import Dict, List, Any

class EnhancedServicesMigration:
    """Handles migration to enhanced portfolio management services"""
    
    def __init__(self):
        self.namespace = "trading-system"
        self.old_services = [
            "portfolio-service",
            "risk-service"
        ]
        self.new_services = [
            "enhanced-portfolio-service",
            "enhanced-risk-management-service"
        ]
    
    def check_prerequisites(self) -> bool:
        """Check if migration prerequisites are met"""
        print("🔍 Checking migration prerequisites...")
        
        # Check if kubectl is available
        try:
            result = subprocess.run(["kubectl", "version", "--client"], 
                                  capture_output=True, text=True, check=True)
            print("✅ kubectl is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ kubectl is not available or not working")
            return False
        
        # Check if namespace exists
        try:
            result = subprocess.run([
                "kubectl", "get", "namespace", self.namespace
            ], capture_output=True, text=True, check=True)
            print(f"✅ Namespace {self.namespace} exists")
        except subprocess.CalledProcessError:
            print(f"❌ Namespace {self.namespace} does not exist")
            return False
        
        # Check if old services are running
        for service in self.old_services:
            try:
                result = subprocess.run([
                    "kubectl", "get", "deployment", service, "-n", self.namespace
                ], capture_output=True, text=True, check=True)
                print(f"✅ Old service {service} is running")
            except subprocess.CalledProcessError:
                print(f"⚠️  Old service {service} is not running (this is OK)")
        
        return True
    
    def backup_existing_services(self) -> bool:
        """Backup existing service configurations"""
        print("💾 Backing up existing service configurations...")
        
        for service in self.old_services:
            try:
                # Export deployment
                result = subprocess.run([
                    "kubectl", "get", "deployment", service, "-n", self.namespace, "-o", "yaml"
                ], capture_output=True, text=True, check=True)
                
                with open(f"backup/{service}-deployment.yaml", "w") as f:
                    f.write(result.stdout)
                
                # Export service
                result = subprocess.run([
                    "kubectl", "get", "service", service, "-n", self.namespace, "-o", "yaml"
                ], capture_output=True, text=True, check=True)
                
                with open(f"backup/{service}-service.yaml", "w") as f:
                    f.write(result.stdout)
                
                print(f"✅ Backed up {service}")
                
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not backup {service} (may not exist)")
        
        return True
    
    def deploy_enhanced_services(self) -> bool:
        """Deploy enhanced services"""
        print("🚀 Deploying enhanced services...")
        
        try:
            # Apply enhanced services configuration
            result = subprocess.run([
                "kubectl", "apply", "-f", "k8s/enhanced-portfolio-services.yaml"
            ], capture_output=True, text=True, check=True)
            
            print("✅ Enhanced services configuration applied")
            
            # Wait for deployments to be ready
            for service in self.new_services:
                print(f"⏳ Waiting for {service} to be ready...")
                
                result = subprocess.run([
                    "kubectl", "wait", "--for=condition=available", 
                    f"deployment/{service}", "-n", self.namespace, "--timeout=300s"
                ], capture_output=True, text=True, check=True)
                
                print(f"✅ {service} is ready")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to deploy enhanced services: {e}")
            return False
    
    def verify_services(self) -> bool:
        """Verify enhanced services are working"""
        print("🔍 Verifying enhanced services...")
        
        # Get service endpoints
        try:
            result = subprocess.run([
                "kubectl", "get", "services", "-n", self.namespace, "-o", "json"
            ], capture_output=True, text=True, check=True)
            
            services = json.loads(result.stdout)
            
            for service in self.new_services:
                service_info = next(
                    (s for s in services["items"] if s["metadata"]["name"] == service), 
                    None
                )
                
                if service_info:
                    cluster_ip = service_info["spec"]["clusterIP"]
                    port = service_info["spec"]["ports"][0]["port"]
                    print(f"✅ {service} is available at {cluster_ip}:{port}")
                else:
                    print(f"❌ {service} service not found")
                    return False
            
            return True
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"❌ Failed to verify services: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints of enhanced services"""
        print("🧪 Testing API endpoints...")
        
        # Test enhanced portfolio service
        try:
            result = subprocess.run([
                "kubectl", "port-forward", "-n", self.namespace, 
                "service/enhanced-portfolio-service", "8080:80"
            ], capture_output=True, text=True, check=True, timeout=10)
            
            # Test health endpoint
            response = requests.get("http://localhost:8080/health", timeout=5)
            if response.status_code == 200:
                print("✅ Enhanced Portfolio Service health check passed")
            else:
                print(f"❌ Enhanced Portfolio Service health check failed: {response.status_code}")
                return False
                
        except (subprocess.CalledProcessError, requests.RequestException) as e:
            print(f"❌ Failed to test Enhanced Portfolio Service: {e}")
            return False
        
        # Test enhanced risk management service
        try:
            result = subprocess.run([
                "kubectl", "port-forward", "-n", self.namespace", 
                "service/enhanced-risk-management-service", "8081:80"
            ], capture_output=True, text=True, check=True, timeout=10)
            
            # Test health endpoint
            response = requests.get("http://localhost:8081/health", timeout=5)
            if response.status_code == 200:
                print("✅ Enhanced Risk Management Service health check passed")
            else:
                print(f"❌ Enhanced Risk Management Service health check failed: {response.status_code}")
                return False
                
        except (subprocess.CalledProcessError, requests.RequestException) as e:
            print(f"❌ Failed to test Enhanced Risk Management Service: {e}")
            return False
        
        return True
    
    def update_service_references(self) -> bool:
        """Update service references in other deployments"""
        print("🔄 Updating service references...")
        
        # List of deployments that might reference old services
        referencing_deployments = [
            "strategy-service",
            "unified-trading-dashboard",
            "unified-analytics-dashboard"
        ]
        
        for deployment in referencing_deployments:
            try:
                # Check if deployment exists
                result = subprocess.run([
                    "kubectl", "get", "deployment", deployment, "-n", self.namespace
                ], capture_output=True, text=True, check=True)
                
                print(f"⚠️  {deployment} may need configuration updates to use enhanced services")
                print(f"   Consider updating environment variables and service URLs")
                
            except subprocess.CalledProcessError:
                print(f"ℹ️  {deployment} not found (this is OK)")
        
        return True
    
    def cleanup_old_services(self) -> bool:
        """Clean up old services (optional)"""
        print("🧹 Cleaning up old services...")
        
        response = input("Do you want to remove old services? (y/N): ")
        if response.lower() != 'y':
            print("ℹ️  Keeping old services for now")
            return True
        
        for service in self.old_services:
            try:
                # Delete deployment
                subprocess.run([
                    "kubectl", "delete", "deployment", service, "-n", self.namespace
                ], capture_output=True, text=True, check=True)
                
                # Delete service
                subprocess.run([
                    "kubectl", "delete", "service", service, "-n", self.namespace
                ], capture_output=True, text=True, check=True)
                
                print(f"✅ Removed old service {service}")
                
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not remove {service} (may not exist)")
        
        return True
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        print("🚀 Starting Enhanced Portfolio Management Services Migration")
        print("=" * 60)
        
        steps = [
            ("Check Prerequisites", self.check_prerequisites),
            ("Backup Existing Services", self.backup_existing_services),
            ("Deploy Enhanced Services", self.deploy_enhanced_services),
            ("Verify Services", self.verify_services),
            ("Test API Endpoints", self.test_api_endpoints),
            ("Update Service References", self.update_service_references),
            ("Cleanup Old Services", self.cleanup_old_services)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}")
            print("-" * 40)
            
            if not step_func():
                print(f"❌ Migration failed at step: {step_name}")
                return False
            
            print(f"✅ {step_name} completed")
        
        print("\n🎉 Migration completed successfully!")
        print("=" * 60)
        print("Enhanced Portfolio Management Services are now running:")
        print("• Enhanced Portfolio Service: http://localhost:8080")
        print("• Enhanced Risk Management Service: http://localhost:8081")
        print("\nNext steps:")
        print("1. Update dashboard configurations to use new endpoints")
        print("2. Test portfolio optimization features")
        print("3. Verify risk management capabilities")
        print("4. Update documentation and monitoring")
        
        return True

def main():
    """Main migration function"""
    migration = EnhancedServicesMigration()
    
    if not migration.run_migration():
        sys.exit(1)

if __name__ == "__main__":
    main()





















