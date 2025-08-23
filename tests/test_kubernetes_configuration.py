#!/usr/bin/env python3
"""
Kubernetes Configuration Test Suite
Tests the current Kubernetes configuration for the trading system
"""

import pytest
import yaml
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any

class KubernetesConfigTester:
    """Test suite for Kubernetes configuration validation"""
    
    def __init__(self):
        self.k8s_dir = Path("k8s")
        self.namespace = "trading-system"
        self.required_secrets = [
            "trading-secrets",
            "trading-config"
        ]
        self.required_configmaps = [
            "trading-config"
        ]
    
    def load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            pytest.fail(f"Failed to load {file_path}: {e}")
    
    def run_kubectl_command(self, command: str) -> Dict[str, Any]:
        """Run a kubectl command and return JSON output"""
        try:
            result = subprocess.run(
                f"kubectl {command} -n {self.namespace} -o json",
                shell=True, capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Kubectl command failed: {e}")
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse kubectl output: {e}")
    
    def get_deployments(self) -> List[Dict[str, Any]]:
        """Get all deployments in the namespace"""
        return self.run_kubectl_command("get deployments")["items"]
    
    def get_services(self) -> List[Dict[str, Any]]:
        """Get all services in the namespace"""
        return self.run_kubectl_command("get services")["items"]
    
    def get_configmaps(self) -> List[Dict[str, Any]]:
        """Get all configmaps in the namespace"""
        return self.run_kubectl_command("get configmaps")["items"]
    
    def get_secrets(self) -> List[Dict[str, Any]]:
        """Get all secrets in the namespace"""
        return self.run_kubectl_command("get secrets")["items"]

@pytest.fixture
def k8s_tester():
    """Fixture for Kubernetes configuration tester"""
    return KubernetesConfigTester()

class TestKubernetesNamespace:
    """Test namespace configuration"""
    
    def test_namespace_exists(self, k8s_tester):
        """Test that the trading-system namespace exists"""
        try:
            result = subprocess.run(
                f"kubectl get namespace {k8s_tester.namespace}",
                shell=True, capture_output=True, text=True, check=True
            )
            assert k8s_tester.namespace in result.stdout
        except subprocess.CalledProcessError:
            pytest.fail(f"Namespace {k8s_tester.namespace} does not exist")

class TestKubernetesSecrets:
    """Test required secrets exist and are properly configured"""
    
    def test_required_secrets_exist(self, k8s_tester):
        """Test that all required secrets exist"""
        secrets = k8s_tester.get_secrets()
        secret_names = [secret["metadata"]["name"] for secret in secrets]
        
        for required_secret in k8s_tester.required_secrets:
            assert required_secret in secret_names, f"Required secret {required_secret} not found"
    
    def test_trading_secrets_has_required_keys(self, k8s_tester):
        """Test that trading-secrets has required keys"""
        try:
            result = subprocess.run(
                f"kubectl get secret trading-secrets -n {k8s_tester.namespace} -o json",
                shell=True, capture_output=True, text=True, check=True
            )
            secret_data = json.loads(result.stdout)
            data_keys = list(secret_data["data"].keys())
            
            # Check for essential keys
            essential_keys = ["database-url", "polygon-api-key"]
            for key in essential_keys:
                assert key in data_keys, f"Essential secret key {key} not found in trading-secrets"
        except subprocess.CalledProcessError:
            pytest.skip("trading-secrets not accessible")

class TestKubernetesConfigMaps:
    """Test required configmaps exist and are properly configured"""
    
    def test_required_configmaps_exist(self, k8s_tester):
        """Test that all required configmaps exist"""
        configmaps = k8s_tester.get_configmaps()
        configmap_names = [cm["metadata"]["name"] for cm in configmaps]
        
        for required_cm in k8s_tester.required_configmaps:
            assert required_cm in configmap_names, f"Required configmap {required_cm} not found"

class TestKubernetesDeployments:
    """Test deployment configurations"""
    
    def test_deployments_have_required_labels(self, k8s_tester):
        """Test that all deployments have required labels"""
        deployments = k8s_tester.get_deployments()
        
        for deployment in deployments:
            metadata = deployment["metadata"]
            labels = metadata.get("labels", {})
            
            # Check for app label
            assert "app" in labels, f"Deployment {metadata['name']} missing 'app' label"
            
            # Check for namespace
            assert metadata["namespace"] == k8s_tester.namespace
    
    def test_deployments_have_resource_limits(self, k8s_tester):
        """Test that deployments have resource limits defined"""
        deployments = k8s_tester.get_deployments()
        
        for deployment in deployments:
            containers = deployment["spec"]["template"]["spec"]["containers"]
            
            for container in containers:
                resources = container.get("resources", {})
                
                # Check for resource requests
                assert "requests" in resources, f"Container {container['name']} missing resource requests"
                assert "limits" in resources, f"Container {container['name']} missing resource limits"
                
                # Check for memory and CPU
                requests = resources["requests"]
                limits = resources["limits"]
                
                assert "memory" in requests, f"Container {container['name']} missing memory requests"
                assert "cpu" in requests, f"Container {container['name']} missing CPU requests"
                assert "memory" in limits, f"Container {container['name']} missing memory limits"
                assert "cpu" in limits, f"Container {container['name']} missing CPU limits"
    
    def test_deployments_have_health_checks(self, k8s_tester):
        """Test that deployments have health checks configured"""
        deployments = k8s_tester.get_deployments()
        
        for deployment in deployments:
            containers = deployment["spec"]["template"]["spec"]["containers"]
            
            for container in containers:
                # Check for liveness probe
                assert "livenessProbe" in container, f"Container {container['name']} missing liveness probe"
                
                # Check for readiness probe
                assert "readinessProbe" in container, f"Container {container['name']} missing readiness probe"
                
                # Validate probe configuration
                liveness = container["livenessProbe"]
                readiness = container["readinessProbe"]
                
                assert "httpGet" in liveness, f"Container {container['name']} liveness probe should use httpGet"
                assert "httpGet" in readiness, f"Container {container['name']} readiness probe should use httpGet"
                
                # Check probe paths and ports
                assert "path" in liveness["httpGet"], f"Container {container['name']} liveness probe missing path"
                assert "port" in liveness["httpGet"], f"Container {container['name']} liveness probe missing port"
                assert "path" in readiness["httpGet"], f"Container {container['name']} readiness probe missing path"
                assert "port" in readiness["httpGet"], f"Container {container['name']} readiness probe missing port"

class TestKubernetesServices:
    """Test service configurations"""
    
    def test_services_have_selectors(self, k8s_tester):
        """Test that all services have proper selectors"""
        services = k8s_tester.get_services()
        
        for service in services:
            spec = service["spec"]
            assert "selector" in spec, f"Service {service['metadata']['name']} missing selector"
            assert "app" in spec["selector"], f"Service {service['metadata']['name']} selector missing 'app' key"
    
    def test_services_have_ports(self, k8s_tester):
        """Test that all services have ports configured"""
        services = k8s_tester.get_services()
        
        for service in services:
            spec = service["spec"]
            assert "ports" in spec, f"Service {service['metadata']['name']} missing ports"
            assert len(spec["ports"]) > 0, f"Service {service['metadata']['name']} has no ports defined"
            
            for port in spec["ports"]:
                assert "port" in port, f"Service {service['metadata']['name']} port missing 'port' field"
                assert "targetPort" in port, f"Service {service['metadata']['name']} port missing 'targetPort' field"
                assert "protocol" in port, f"Service {service['metadata']['name']} port missing 'protocol' field"

class TestKubernetesImageConfiguration:
    """Test image configuration and registry settings"""
    
    def test_deployments_use_local_registry(self, k8s_tester):
        """Test that deployments use the local registry"""
        deployments = k8s_tester.get_deployments()
        
        for deployment in deployments:
            containers = deployment["spec"]["template"]["spec"]["containers"]
            
            for container in containers:
                image = container["image"]
                
                # Check for localhost:32000 registry
                if "localhost:32000" in image:
                    # Check imagePullPolicy for local images
                    image_pull_policy = container.get("imagePullPolicy", "IfNotPresent")
                    assert image_pull_policy in ["Never", "IfNotPresent"], \
                        f"Local image {image} should have imagePullPolicy Never or IfNotPresent"
    
    def test_deployments_have_image_pull_policy(self, k8s_tester):
        """Test that all deployments have imagePullPolicy set"""
        deployments = k8s_tester.get_deployments()
        
        for deployment in deployments:
            containers = deployment["spec"]["template"]["spec"]["containers"]
            
            for container in containers:
                assert "imagePullPolicy" in container, f"Container {container['name']} missing imagePullPolicy"

class TestKubernetesEnvironmentVariables:
    """Test environment variable configuration"""
    
    def test_deployments_have_database_url(self, k8s_tester):
        """Test that deployments that need database access have DATABASE_URL"""
        deployments = k8s_tester.get_deployments()
        
        # Services that should have database access
        db_services = [
            "strategy-service", "market-data-service", "performance-dashboard",
            "postgres-vector-storage", "background-vectorization-service"
        ]
        
        for deployment in deployments:
            deployment_name = deployment["metadata"]["name"]
            if deployment_name in db_services:
                containers = deployment["spec"]["template"]["spec"]["containers"]
                
                for container in containers:
                    env_vars = container.get("env", [])
                    env_names = [env["name"] for env in env_vars]
                    
                    # Check for DATABASE_URL (either direct or from secret)
                    has_db_url = False
                    for env in env_vars:
                        if env["name"] == "DATABASE_URL":
                            has_db_url = True
                            break
                        elif env["name"] == "DATABASE_URL" and "valueFrom" in env:
                            has_db_url = True
                            break
                    
                    assert has_db_url, f"Service {deployment_name} missing DATABASE_URL environment variable"

class TestKubernetesResourceQuotas:
    """Test resource quota and limit configurations"""
    
    def test_deployments_have_reasonable_resource_limits(self, k8s_tester):
        """Test that deployments have reasonable resource limits"""
        deployments = k8s_tester.get_deployments()
        
        for deployment in deployments:
            containers = deployment["spec"]["template"]["spec"]["containers"]
            
            for container in containers:
                resources = container.get("resources", {})
                if "limits" in resources:
                    limits = resources["limits"]
                    
                    # Check memory limits are reasonable (not too high)
                    if "memory" in limits:
                        memory = limits["memory"]
                        # Convert to Mi for comparison
                        if "Gi" in memory:
                            memory_mi = int(memory.replace("Gi", "")) * 1024
                        elif "Mi" in memory:
                            memory_mi = int(memory.replace("Mi", ""))
                        else:
                            memory_mi = int(memory) // (1024 * 1024)
                        
                        assert memory_mi <= 2048, f"Container {container['name']} has excessive memory limit: {memory}"
                    
                    # Check CPU limits are reasonable
                    if "cpu" in limits:
                        cpu = limits["cpu"]
                        if "m" in cpu:
                            cpu_cores = int(cpu.replace("m", "")) / 1000
                        else:
                            cpu_cores = float(cpu)
                        
                        assert cpu_cores <= 2.0, f"Container {container['name']} has excessive CPU limit: {cpu}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


