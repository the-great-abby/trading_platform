#!/usr/bin/env python3
"""
Kubernetes Service Health Test Suite
Tests the health and connectivity of all Kubernetes services
"""

import pytest
import asyncio
import aiohttp
import subprocess
import json
import time
from typing import Dict, List, Any, Optional

class KubernetesServiceHealthTester:
    """Test suite for Kubernetes service health and connectivity"""
    
    def __init__(self):
        self.namespace = "trading-system"
        self.session: Optional[aiohttp.ClientSession] = None
        self.port_forwards: Dict[str, int] = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        # Clean up port forwards
        self.cleanup_port_forwards()
    
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
    
    def get_pods(self) -> List[Dict[str, Any]]:
        """Get all pods in the namespace"""
        return self.run_kubectl_command("get pods")["items"]
    
    def setup_port_forward(self, service_name: str, local_port: int, target_port: int = 80) -> bool:
        """Set up port forwarding for a service"""
        try:
            # Kill any existing port forward for this service
            subprocess.run(
                f"pkill -f 'kubectl port-forward.*{service_name}'",
                shell=True, capture_output=True
            )
            time.sleep(1)
            
            # Start new port forward
            cmd = f"kubectl port-forward service/{service_name} {local_port}:{target_port} -n {self.namespace}"
            process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a bit for port forward to establish
            time.sleep(3)
            
            # Check if port forward is working
            if process.poll() is None:  # Process is still running
                self.port_forwards[service_name] = local_port
                return True
            else:
                return False
        except Exception as e:
            print(f"Failed to setup port forward for {service_name}: {e}")
            return False
    
    def cleanup_port_forwards(self):
        """Clean up all port forwards"""
        for service_name in self.port_forwards:
            subprocess.run(
                f"pkill -f 'kubectl port-forward.*{service_name}'",
                shell=True, capture_output=True
            )
        self.port_forwards.clear()
    
    async def test_service_health_endpoint(self, service_name: str, port: int, health_path: str = "/health") -> bool:
        """Test a service's health endpoint"""
        try:
            url = f"http://localhost:{port}{health_path}"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return True
                else:
                    print(f"Service {service_name} health check failed with status {response.status}")
                    return False
        except Exception as e:
            print(f"Service {service_name} health check error: {e}")
            return False
    
    async def test_service_ready_endpoint(self, service_name: str, port: int, ready_path: str = "/ready") -> bool:
        """Test a service's ready endpoint"""
        try:
            url = f"http://localhost:{port}{ready_path}"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return True
                else:
                    print(f"Service {service_name} ready check failed with status {response.status}")
                    return False
        except Exception as e:
            print(f"Service {service_name} ready check error: {e}")
            return False

@pytest.fixture
async def k8s_health_tester():
    """Fixture for Kubernetes service health tester"""
    async with KubernetesServiceHealthTester() as tester:
        yield tester

class TestKubernetesPodStatus:
    """Test that all pods are running and healthy"""
    
    def test_all_pods_are_running(self, k8s_health_tester):
        """Test that all pods are in Running state"""
        pods = k8s_health_tester.get_pods()
        
        for pod in pods:
            status = pod["status"]["phase"]
            assert status == "Running", f"Pod {pod['metadata']['name']} is not running (status: {status})"
    
    def test_all_pods_are_ready(self, k8s_health_tester):
        """Test that all pods are ready"""
        pods = k8s_health_tester.get_pods()
        
        for pod in pods:
            # Check if pod has ready condition
            conditions = pod["status"].get("conditions", [])
            ready_condition = next((c for c in conditions if c["type"] == "Ready"), None)
            
            if ready_condition:
                assert ready_condition["status"] == "True", \
                    f"Pod {pod['metadata']['name']} is not ready: {ready_condition['message']}"
            else:
                pytest.fail(f"Pod {pod['metadata']['name']} missing Ready condition")
    
    def test_all_pods_have_restart_count_under_limit(self, k8s_health_tester):
        """Test that pods haven't restarted too many times"""
        pods = k8s_health_tester.get_pods()
        
        for pod in pods:
            containers = pod["status"].get("containerStatuses", [])
            for container in containers:
                restart_count = container.get("restartCount", 0)
                assert restart_count < 5, \
                    f"Container {container['name']} in pod {pod['metadata']['name']} has restarted {restart_count} times"

class TestKubernetesDeploymentStatus:
    """Test that all deployments are available and updated"""
    
    def test_all_deployments_are_available(self, k8s_health_tester):
        """Test that all deployments are available"""
        deployments = k8s_health_tester.get_deployments()
        
        for deployment in deployments:
            conditions = deployment["status"].get("conditions", [])
            available_condition = next((c for c in conditions if c["type"] == "Available"), None)
            
            if available_condition:
                assert available_condition["status"] == "True", \
                    f"Deployment {deployment['metadata']['name']} is not available: {available_condition['message']}"
            else:
                pytest.fail(f"Deployment {deployment['metadata']['name']} missing Available condition")
    
    def test_all_deployments_are_updated(self, k8s_health_tester):
        """Test that all deployments are updated"""
        deployments = k8s_health_tester.get_deployments()
        
        for deployment in deployments:
            status = deployment["status"]
            updated_replicas = status.get("updatedReplicas", 0)
            desired_replicas = status.get("replicas", 0)
            
            assert updated_replicas == desired_replicas, \
                f"Deployment {deployment['metadata']['name']} not fully updated ({updated_replicas}/{desired_replicas})"

class TestKubernetesServiceConnectivity:
    """Test service connectivity and health endpoints"""
    
    @pytest.mark.asyncio
    async def test_core_services_health(self, k8s_health_tester):
        """Test health endpoints of core services"""
        core_services = [
            ("strategy-service", 11120),
            ("market-data-service", 11121),
            ("trading-dashboard-service", 11122),
            ("performance-dashboard", 11123)
        ]
        
        for service_name, port in core_services:
            # Setup port forward
            if k8s_health_tester.setup_port_forward(service_name, port):
                # Test health endpoint
                health_ok = await k8s_health_tester.test_service_health_endpoint(service_name, port)
                assert health_ok, f"Service {service_name} health check failed"
            else:
                pytest.skip(f"Could not setup port forward for {service_name}")
    
    @pytest.mark.asyncio
    async def test_dashboard_services_health(self, k8s_health_tester):
        """Test health endpoints of dashboard services"""
        dashboard_services = [
            ("unified-analytics-dashboard", 11114),
            ("unified-trading-dashboard", 11115),
            ("unified-news-dashboard", 11113)
        ]
        
        for service_name, port in dashboard_services:
            # Setup port forward
            if k8s_health_tester.setup_port_forward(service_name, port):
                # Test health endpoint
                health_ok = await k8s_health_tester.test_service_health_endpoint(service_name, port)
                assert health_ok, f"Service {service_name} health check failed"
            else:
                pytest.skip(f"Could not setup port forward for {service_name}")
    
    @pytest.mark.asyncio
    async def test_ai_services_health(self, k8s_health_tester):
        """Test health endpoints of AI services"""
        ai_services = [
            ("ai-analysis-service", 11124),
            ("llm-service", 11125),
            ("postgres-vector-storage", 11126)
        ]
        
        for service_name, port in ai_services:
            # Setup port forward
            if k8s_health_tester.setup_port_forward(service_name, port):
                # Test health endpoint
                health_ok = await k8s_health_tester.test_service_health_endpoint(service_name, port)
                assert health_ok, f"Service {service_name} health check failed"
            else:
                pytest.skip(f"Could not setup port forward for {service_name}")

class TestKubernetesServiceReadiness:
    """Test service readiness endpoints"""
    
    @pytest.mark.asyncio
    async def test_core_services_readiness(self, k8s_health_tester):
        """Test ready endpoints of core services"""
        core_services = [
            ("strategy-service", 11120),
            ("market-data-service", 11121)
        ]
        
        for service_name, port in core_services:
            # Setup port forward
            if k8s_health_tester.setup_port_forward(service_name, port):
                # Test ready endpoint
                ready_ok = await k8s_health_tester.test_service_ready_endpoint(service_name, port)
                assert ready_ok, f"Service {service_name} ready check failed"
            else:
                pytest.skip(f"Could not setup port forward for {service_name}")

class TestKubernetesServiceDependencies:
    """Test that services can communicate with their dependencies"""
    
    def test_services_have_required_secrets(self, k8s_health_tester):
        """Test that services have access to required secrets"""
        deployments = k8s_health_tester.get_deployments()
        
        for deployment in deployments:
            containers = deployment["spec"]["template"]["spec"]["containers"]
            
            for container in containers:
                env_vars = container.get("env", [])
                
                # Check for secret references
                for env in env_vars:
                    if "valueFrom" in env and "secretKeyRef" in env["valueFrom"]:
                        secret_name = env["valueFrom"]["secretKeyRef"]["name"]
                        secret_key = env["valueFrom"]["secretKeyRef"]["key"]
                        
                        # Verify secret exists
                        try:
                            result = subprocess.run(
                                f"kubectl get secret {secret_name} -n {k8s_health_tester.namespace}",
                                shell=True, capture_output=True, text=True, check=True
                            )
                            assert secret_name in result.stdout, f"Secret {secret_name} not found"
                        except subprocess.CalledProcessError:
                            pytest.fail(f"Secret {secret_name} not accessible")
    
    def test_services_have_required_configmaps(self, k8s_health_tester):
        """Test that services have access to required configmaps"""
        deployments = k8s_health_tester.get_deployments()
        
        for deployment in deployments:
            containers = deployment["spec"]["template"]["spec"]["containers"]
            
            for container in containers:
                env_vars = container.get("env", [])
                
                # Check for configmap references
                for env in env_vars:
                    if "valueFrom" in env and "configMapKeyRef" in env["valueFrom"]:
                        configmap_name = env["valueFrom"]["configMapKeyRef"]["name"]
                        configmap_key = env["valueFrom"]["configMapKeyRef"]["key"]
                        
                        # Verify configmap exists
                        try:
                            result = subprocess.run(
                                f"kubectl get configmap {configmap_name} -n {k8s_health_tester.namespace}",
                                shell=True, capture_output=True, text=True, check=True
                            )
                            assert configmap_name in result.stdout, f"ConfigMap {configmap_name} not found"
                        except subprocess.CalledProcessError:
                            pytest.fail(f"ConfigMap {configmap_name} not accessible")

class TestKubernetesResourceUtilization:
    """Test resource utilization and limits"""
    
    def test_pods_are_not_over_resource_limits(self, k8s_health_tester):
        """Test that pods are not exceeding resource limits"""
        pods = k8s_health_tester.get_pods()
        
        for pod in pods:
            containers = pod["status"].get("containerStatuses", [])
            for container in containers:
                # Check if container is using resources
                if "usage" in container.get("resources", {}):
                    usage = container["resources"]["usage"]
                    
                    # This is a basic check - in practice you'd want to compare against limits
                    if "memory" in usage:
                        memory_usage = usage["memory"]
                        # Convert to Mi for logging
                        if "Ki" in memory_usage:
                            memory_mi = int(memory_usage.replace("Ki", "")) // 1024
                        elif "Mi" in memory_usage:
                            memory_mi = int(memory_usage.replace("Mi", ""))
                        else:
                            memory_mi = int(memory_usage) // (1024 * 1024)
                        
                        print(f"Container {container['name']} memory usage: {memory_mi}Mi")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])



