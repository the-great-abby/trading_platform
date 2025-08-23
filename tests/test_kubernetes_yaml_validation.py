#!/usr/bin/env python3
"""
Kubernetes YAML Configuration Validation Test Suite
Tests Kubernetes YAML files for syntax, best practices, and consistency
"""

import pytest
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Set
import re

class KubernetesYAMLValidator:
    """Validator for Kubernetes YAML configuration files"""
    
    def __init__(self):
        self.k8s_dir = Path("k8s")
        self.namespace = "trading-system"
        self.required_labels = {"app", "namespace"}
        self.required_annotations = set()
        self.resource_patterns = {
            "memory": r"^\d+[KMG]i?$",
            "cpu": r"^\d+m?$|^\d+\.\d+$"
        }
        self.port_range = (1, 65535)
        self.container_port_range = (8000, 9000)  # Your project's preferred range
    
    def load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"YAML syntax error in {file_path}: {e}")
        except Exception as e:
            pytest.fail(f"Failed to load {file_path}: {e}")
    
    def get_all_yaml_files(self) -> List[Path]:
        """Get all YAML files in the k8s directory"""
        yaml_files = []
        for file_path in self.k8s_dir.rglob("*.yaml"):
            if not file_path.name.startswith("."):  # Skip hidden files
                yaml_files.append(file_path)
        return yaml_files
    
    def validate_resource_definition(self, resource: Dict[str, Any], file_path: Path) -> List[str]:
        """Validate a single Kubernetes resource definition"""
        errors = []
        
        # Check required fields
        if "apiVersion" not in resource:
            errors.append("Missing apiVersion")
        if "kind" not in resource:
            errors.append("Missing kind")
        if "metadata" not in resource:
            errors.append("Missing metadata")
        
        # Validate metadata
        if "metadata" in resource:
            metadata = resource["metadata"]
            if "name" not in metadata:
                errors.append("Missing metadata.name")
            
            # Check namespace consistency
            if "namespace" in metadata:
                if metadata["namespace"] != self.namespace:
                    errors.append(f"Namespace mismatch: expected {self.namespace}, got {metadata['namespace']}")
            else:
                # For resources that should have namespace
                if resource["kind"] in ["Deployment", "Service", "ConfigMap", "Secret"]:
                    errors.append(f"Resource {resource['kind']} should specify namespace")
        
        # Validate labels
        if "metadata" in resource and "labels" in resource["metadata"]:
            labels = resource["metadata"]["labels"]
            if "app" not in labels:
                errors.append("Missing 'app' label")
        
        # Resource-specific validation
        if resource["kind"] == "Deployment":
            errors.extend(self.validate_deployment(resource))
        elif resource["kind"] == "Service":
            errors.extend(self.validate_service(resource))
        elif resource["kind"] == "ConfigMap":
            errors.extend(self.validate_configmap(resource))
        elif resource["kind"] == "Secret":
            errors.extend(self.validate_secret(resource))
        
        return errors
    
    def validate_deployment(self, deployment: Dict[str, Any]) -> List[str]:
        """Validate Deployment resource"""
        errors = []
        
        spec = deployment.get("spec", {})
        if "template" not in spec:
            errors.append("Deployment missing spec.template")
            return errors
        
        template = spec["template"]
        if "spec" not in template:
            errors.append("Deployment missing spec.template.spec")
            return errors
        
        pod_spec = template["spec"]
        if "containers" not in pod_spec:
            errors.append("Deployment missing containers")
            return errors
        
        containers = pod_spec["containers"]
        if not containers:
            errors.append("Deployment has no containers")
            return errors
        
        for i, container in enumerate(containers):
            container_errors = self.validate_container(container, f"container[{i}]")
            errors.extend(container_errors)
        
        return errors
    
    def validate_service(self, service: Dict[str, Any]) -> List[str]:
        """Validate Service resource"""
        errors = []
        
        spec = service.get("spec", {})
        if "selector" not in spec:
            errors.append("Service missing selector")
        
        if "ports" not in spec:
            errors.append("Service missing ports")
        else:
            ports = spec["ports"]
            if not isinstance(ports, list):
                errors.append("Service ports must be a list")
            else:
                for i, port in enumerate(ports):
                    port_errors = self.validate_service_port(port, f"port[{i}]")
                    errors.extend(port_errors)
        
        return errors
    
    def validate_configmap(self, configmap: Dict[str, Any]) -> List[str]:
        """Validate ConfigMap resource"""
        errors = []
        
        if "data" not in configmap:
            errors.append("ConfigMap missing data")
        
        return errors
    
    def validate_secret(self, secret: Dict[str, Any]) -> List[str]:
        """Validate Secret resource"""
        errors = []
        
        if "data" not in secret and "stringData" not in secret:
            errors.append("Secret missing data or stringData")
        
        return errors
    
    def validate_container(self, container: Dict[str, Any], container_name: str) -> List[str]:
        """Validate container configuration"""
        errors = []
        
        # Check required fields
        if "name" not in container:
            errors.append(f"{container_name} missing name")
        if "image" not in container:
            errors.append(f"{container_name} missing image")
        
        # Validate image
        if "image" in container:
            image = container["image"]
            if "localhost:32000" in image:
                # Local images should have appropriate imagePullPolicy
                image_pull_policy = container.get("imagePullPolicy", "IfNotPresent")
                if image_pull_policy not in ["Never", "IfNotPresent"]:
                    errors.append(f"{container_name} local image should have imagePullPolicy Never or IfNotPresent")
        
        # Validate ports
        if "ports" in container:
            ports = container["ports"]
            if not isinstance(ports, list):
                errors.append(f"{container_name} ports must be a list")
            else:
                for i, port in enumerate(ports):
                    port_errors = self.validate_container_port(port, f"{container_name}.port[{i}]")
                    errors.extend(port_errors)
        
        # Validate resources
        if "resources" in container:
            resource_errors = self.validate_resources(container["resources"], container_name)
            errors.extend(resource_errors)
        
        # Validate probes
        if "livenessProbe" in container:
            probe_errors = self.validate_probe(container["livenessProbe"], f"{container_name}.livenessProbe")
            errors.extend(probe_errors)
        
        if "readinessProbe" in container:
            probe_errors = self.validate_probe(container["readinessProbe"], f"{container_name}.readinessProbe")
            errors.extend(probe_errors)
        
        # Validate environment variables
        if "env" in container:
            env_errors = self.validate_environment_variables(container["env"], container_name)
            errors.extend(env_errors)
        
        return errors
    
    def validate_container_port(self, port: Dict[str, Any], port_name: str) -> List[str]:
        """Validate container port configuration"""
        errors = []
        
        if "containerPort" not in port:
            errors.append(f"{port_name} missing containerPort")
        else:
            container_port = port["containerPort"]
            if not isinstance(container_port, int):
                errors.append(f"{port_name} containerPort must be an integer")
            elif container_port < 1 or container_port > 65535:
                errors.append(f"{port_name} containerPort must be between 1 and 65535")
            elif container_port < self.container_port_range[0] or container_port > self.container_port_range[1]:
                errors.append(f"{port_name} containerPort {container_port} should be in range {self.container_port_range[0]}-{self.container_port_range[1]}")
        
        return errors
    
    def validate_service_port(self, port: Dict[str, Any], port_name: str) -> List[str]:
        """Validate service port configuration"""
        errors = []
        
        if "port" not in port:
            errors.append(f"{port_name} missing port")
        else:
            service_port = port["port"]
            if not isinstance(service_port, int):
                errors.append(f"{port_name} port must be an integer")
            elif service_port < 1 or service_port > 65535:
                errors.append(f"{port_name} port must be between 1 and 65535")
        
        if "targetPort" not in port:
            errors.append(f"{port_name} missing targetPort")
        else:
            target_port = port["targetPort"]
            if not isinstance(target_port, int):
                errors.append(f"{port_name} targetPort must be an integer")
            elif target_port < 1 or target_port > 65535:
                errors.append(f"{port_name} targetPort must be between 1 and 65535")
        
        if "protocol" not in port:
            errors.append(f"{port_name} missing protocol")
        else:
            protocol = port["protocol"]
            if protocol not in ["TCP", "UDP", "SCTP"]:
                errors.append(f"{port_name} protocol must be TCP, UDP, or SCTP")
        
        return errors
    
    def validate_resources(self, resources: Dict[str, Any], container_name: str) -> List[str]:
        """Validate resource configuration"""
        errors = []
        
        if "requests" in resources:
            request_errors = self.validate_resource_limits(resources["requests"], f"{container_name}.requests")
            errors.extend(request_errors)
        
        if "limits" in resources:
            limit_errors = self.validate_resource_limits(resources["limits"], f"{container_name}.limits")
            errors.extend(limit_errors)
        
        # Check that requests don't exceed limits
        if "requests" in resources and "limits" in resources:
            requests = resources["requests"]
            limits = resources["limits"]
            
            if "memory" in requests and "memory" in limits:
                req_memory = self.parse_memory(requests["memory"])
                lim_memory = self.parse_memory(limits["memory"])
                if req_memory > lim_memory:
                    errors.append(f"{container_name} memory request ({requests['memory']}) exceeds limit ({limits['memory']})")
            
            if "cpu" in requests and "cpu" in limits:
                req_cpu = self.parse_cpu(requests["cpu"])
                lim_cpu = self.parse_cpu(limits["cpu"])
                if req_cpu > lim_cpu:
                    errors.append(f"{container_name} CPU request ({requests['cpu']}) exceeds limit ({limits['cpu']})")
        
        return errors
    
    def validate_resource_limits(self, resource_dict: Dict[str, Any], resource_name: str) -> List[str]:
        """Validate resource limits/requests"""
        errors = []
        
        for resource_type, value in resource_dict.items():
            if resource_type == "memory":
                if not re.match(self.resource_patterns["memory"], str(value)):
                    errors.append(f"{resource_name}.{resource_type} has invalid format: {value}")
            elif resource_type == "cpu":
                if not re.match(self.resource_patterns["cpu"], str(value)):
                    errors.append(f"{resource_name}.{resource_type} has invalid format: {value}")
        
        return errors
    
    def parse_memory(self, memory_str: str) -> int:
        """Parse memory string to bytes"""
        memory_str = str(memory_str)
        if memory_str.endswith("Ki"):
            return int(memory_str[:-2]) * 1024
        elif memory_str.endswith("Mi"):
            return int(memory_str[:-2]) * 1024 * 1024
        elif memory_str.endswith("Gi"):
            return int(memory_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(memory_str)
    
    def parse_cpu(self, cpu_str: str) -> float:
        """Parse CPU string to cores"""
        cpu_str = str(cpu_str)
        if cpu_str.endswith("m"):
            return int(cpu_str[:-1]) / 1000
        else:
            return float(cpu_str)
    
    def validate_probe(self, probe: Dict[str, Any], probe_name: str) -> List[str]:
        """Validate probe configuration"""
        errors = []
        
        if "httpGet" in probe:
            http_get = probe["httpGet"]
            if "path" not in http_get:
                errors.append(f"{probe_name} httpGet missing path")
            if "port" not in http_get:
                errors.append(f"{probe_name} httpGet missing port")
        elif "tcpSocket" in probe:
            tcp_socket = probe["tcpSocket"]
            if "port" not in tcp_socket:
                errors.append(f"{probe_name} tcpSocket missing port")
        elif "exec" in probe:
            exec_cmd = probe["exec"]
            if "command" not in exec_cmd:
                errors.append(f"{probe_name} exec missing command")
        else:
            errors.append(f"{probe_name} must have httpGet, tcpSocket, or exec")
        
        # Validate timing parameters
        if "initialDelaySeconds" in probe:
            if not isinstance(probe["initialDelaySeconds"], int) or probe["initialDelaySeconds"] < 0:
                errors.append(f"{probe_name} initialDelaySeconds must be a non-negative integer")
        
        if "periodSeconds" in probe:
            if not isinstance(probe["periodSeconds"], int) or probe["periodSeconds"] < 1:
                errors.append(f"{probe_name} periodSeconds must be a positive integer")
        
        if "timeoutSeconds" in probe:
            if not isinstance(probe["timeoutSeconds"], int) or probe["timeoutSeconds"] < 1:
                errors.append(f"{probe_name} timeoutSeconds must be a positive integer")
        
        if "failureThreshold" in probe:
            if not isinstance(probe["failureThreshold"], int) or probe["failureThreshold"] < 1:
                errors.append(f"{probe_name} failureThreshold must be a positive integer")
        
        return errors
    
    def validate_environment_variables(self, env_vars: List[Dict[str, Any]], container_name: str) -> List[str]:
        """Validate environment variable configuration"""
        errors = []
        
        for i, env_var in enumerate(env_vars):
            if "name" not in env_var:
                errors.append(f"{container_name}.env[{i}] missing name")
            
            # Check for value or valueFrom
            if "value" not in env_var and "valueFrom" not in env_var:
                errors.append(f"{container_name}.env[{i}] must have value or valueFrom")
            
            # Validate valueFrom references
            if "valueFrom" in env_var:
                value_from = env_var["valueFrom"]
                if "secretKeyRef" in value_from:
                    secret_ref = value_from["secretKeyRef"]
                    if "name" not in secret_ref:
                        errors.append(f"{container_name}.env[{i}] secretKeyRef missing name")
                    if "key" not in secret_ref:
                        errors.append(f"{container_name}.env[{i}] secretKeyRef missing key")
                elif "configMapKeyRef" in value_from:
                    configmap_ref = value_from["configMapKeyRef"]
                    if "name" not in configmap_ref:
                        errors.append(f"{container_name}.env[{i}] configMapKeyRef missing name")
                    if "key" not in configmap_ref:
                        errors.append(f"{container_name}.env[{i}] configMapKeyRef missing key")
        
        return errors

@pytest.fixture
def yaml_validator():
    """Fixture for YAML validator"""
    return KubernetesYAMLValidator()

class TestKubernetesYAMLSyntax:
    """Test YAML syntax and basic structure"""
    
    def test_all_yaml_files_are_valid(self, yaml_validator):
        """Test that all YAML files can be parsed without syntax errors"""
        yaml_files = yaml_validator.get_all_yaml_files()
        
        for yaml_file in yaml_files:
            try:
                yaml_validator.load_yaml_file(yaml_file)
            except Exception as e:
                pytest.fail(f"YAML file {yaml_file} has syntax errors: {e}")
    
    def test_yaml_files_have_valid_resources(self, yaml_validator):
        """Test that YAML files contain valid Kubernetes resources"""
        yaml_files = yaml_validator.get_all_yaml_files()
        
        for yaml_file in yaml_files:
            content = yaml_validator.load_yaml_file(yaml_file)
            
            # Handle both single resources and lists of resources
            if isinstance(content, dict):
                resources = [content]
            elif isinstance(content, list):
                resources = content
            else:
                pytest.fail(f"YAML file {yaml_file} contains invalid content type")
            
            for resource in resources:
                if resource is None:
                    continue  # Skip empty documents
                
                errors = yaml_validator.validate_resource_definition(resource, yaml_file)
                if errors:
                    pytest.fail(f"Resource in {yaml_file} has validation errors: {errors}")

class TestKubernetesYAMLBestPractices:
    """Test YAML files follow Kubernetes best practices"""
    
    def test_deployments_have_resource_limits(self, yaml_validator):
        """Test that deployments have resource limits defined"""
        yaml_files = yaml_validator.get_all_yaml_files()
        
        for yaml_file in yaml_files:
            content = yaml_validator.load_yaml_file(yaml_file)
            
            if isinstance(content, dict):
                resources = [content]
            elif isinstance(content, list):
                resources = content
            else:
                continue
            
            for resource in resources:
                if resource is None or resource.get("kind") != "Deployment":
                    continue
                
                spec = resource.get("spec", {})
                template = spec.get("template", {})
                pod_spec = template.get("spec", {})
                containers = pod_spec.get("containers", [])
                
                for container in containers:
                    if "resources" not in container:
                        pytest.fail(f"Container {container.get('name', 'unnamed')} in {yaml_file} missing resources")
                    
                    resources = container["resources"]
                    if "limits" not in resources:
                        pytest.fail(f"Container {container.get('name', 'unnamed')} in {yaml_file} missing resource limits")
                    if "requests" not in resources:
                        pytest.fail(f"Container {container.get('name', 'unnamed')} in {yaml_file} missing resource requests")
    
    def test_deployments_have_health_checks(self, yaml_validator):
        """Test that deployments have health checks configured"""
        yaml_files = yaml_validator.get_all_yaml_files()
        
        for yaml_file in yaml_files:
            content = yaml_validator.load_yaml_file(yaml_file)
            
            if isinstance(content, dict):
                resources = [content]
            elif isinstance(content, list):
                resources = content
            else:
                continue
            
            for resource in resources:
                if resource is None or resource.get("kind") != "Deployment":
                    continue
                
                spec = resource.get("spec", {})
                template = spec.get("template", {})
                pod_spec = template.get("spec", {})
                containers = pod_spec.get("containers", [])
                
                for container in containers:
                    if "livenessProbe" not in container:
                        pytest.fail(f"Container {container.get('name', 'unnamed')} in {yaml_file} missing livenessProbe")
                    if "readinessProbe" not in container:
                        pytest.fail(f"Container {container.get('name', 'unnamed')} in {yaml_file} missing readinessProbe")
    
    def test_services_have_proper_selectors(self, yaml_validator):
        """Test that services have proper selectors"""
        yaml_files = yaml_validator.get_all_yaml_files()
        
        for yaml_file in yaml_validator.get_all_yaml_files():
            content = yaml_validator.load_yaml_file(yaml_file)
            
            if isinstance(content, dict):
                resources = [content]
            elif isinstance(content, list):
                resources = content
            else:
                continue
            
            for resource in resources:
                if resource is None or resource.get("kind") != "Service":
                    continue
                
                spec = resource.get("spec", {})
                if "selector" not in spec:
                    pytest.fail(f"Service in {yaml_file} missing selector")
                
                selector = spec["selector"]
                if "app" not in selector:
                    pytest.fail(f"Service in {yaml_file} selector missing 'app' key")

class TestKubernetesYAMLConsistency:
    """Test YAML files for consistency across the project"""
    
    def test_namespace_consistency(self, yaml_validator):
        """Test that all resources use the same namespace"""
        yaml_files = yaml_validator.get_all_yaml_files()
        
        for yaml_file in yaml_files:
            content = yaml_validator.load_yaml_file(yaml_file)
            
            if isinstance(content, dict):
                resources = [content]
            elif isinstance(content, list):
                resources = content
            else:
                continue
            
            for resource in resources:
                if resource is None:
                    continue
                
                metadata = resource.get("metadata", {})
                if "namespace" in metadata:
                    namespace = metadata["namespace"]
                    assert namespace == yaml_validator.namespace, \
                        f"Resource in {yaml_file} uses wrong namespace: {namespace} (expected {yaml_validator.namespace})"
    
    def test_label_consistency(self, yaml_validator):
        """Test that resources have consistent labels"""
        yaml_files = yaml_validator.get_all_yaml_files()
        
        for yaml_file in yaml_files:
            content = yaml_validator.load_yaml_file(yaml_file)
            
            if isinstance(content, dict):
                resources = [content]
            elif isinstance(content, list):
                resources = content
            else:
                continue
            
            for resource in resources:
                if resource is None:
                    continue
                
                metadata = resource.get("metadata", {})
                labels = metadata.get("labels", {})
                
                # All resources should have an 'app' label
                if "app" not in labels:
                    pytest.fail(f"Resource in {yaml_file} missing 'app' label")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


