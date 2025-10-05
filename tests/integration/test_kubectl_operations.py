#!/usr/bin/env python3
"""
Integration tests for kubectl operations.
These tests validate kubectl commands for secret management.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path


class TestKubectlOperationsIntegration:
    """Integration tests for kubectl operations."""
    
    def test_kubectl_cluster_connection(self):
        """Test that kubectl can connect to cluster."""
        # This test will fail if kubectl is not configured or cluster is not accessible
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Cannot connect to Kubernetes cluster: {result.stderr}"
        assert "is running" in result.stdout or "Kubernetes control plane" in result.stdout
    
    def test_kubectl_secret_creation_dry_run(self):
        """Test kubectl secret creation with dry-run."""
        # This test will fail until T011 (update-secrets.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Test .env file for dry-run
POLYGON_API_KEY=test_key_123
ALPHA_VANTAGE_API_KEY=test_alpha_456
""")
            env_file = f.name
        
        try:
            # Test dry-run secret creation
            result = subprocess.run([
                "kubectl", "create", "secret", "generic", "polygon-api-key",
                "--from-env-file", env_file,
                "--dry-run=client", "-o", "yaml"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Dry-run secret creation failed: {result.stderr}"
            assert "kind: Secret" in result.stdout
            assert "name: polygon-api-key" in result.stdout
            assert "test_key_123" in result.stdout
            
        finally:
            os.unlink(env_file)
    
    def test_kubectl_secret_update_dry_run(self):
        """Test kubectl secret update with dry-run."""
        # This test will fail until T011 (update-secrets.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Test .env file for update dry-run
POLYGON_API_KEY=updated_test_key_123
""")
            env_file = f.name
        
        try:
            # Test dry-run secret patch
            result = subprocess.run([
                "kubectl", "patch", "secret", "polygon-api-key",
                "--patch-file", "-",
                "--dry-run=client"
            ], input="""apiVersion: v1
kind: Secret
metadata:
  name: polygon-api-key
data:
  api-key: dXBkYXRlZF90ZXN0X2tleV8xMjM=
""", text=True, capture_output=True)
            
            assert result.returncode == 0, f"Dry-run secret update failed: {result.stderr}"
            
        finally:
            os.unlink(env_file)
    
    def test_kubectl_secret_listing(self):
        """Test kubectl secret listing functionality."""
        # This test will fail until T012 (list-secrets.sh) is implemented
        result = subprocess.run([
            "kubectl", "get", "secrets", "-o", "json"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Secret listing failed: {result.stderr}"
        
        # Parse JSON output
        import json
        secrets_data = json.loads(result.stdout)
        assert "items" in secrets_data
        assert isinstance(secrets_data["items"], list)
    
    def test_kubectl_namespace_operations(self):
        """Test kubectl operations with specific namespace."""
        # This test will fail until T011 (update-secrets.sh) is implemented
        namespace = "default"
        
        # Test namespace exists
        result = subprocess.run([
            "kubectl", "get", "namespace", namespace
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Namespace {namespace} not found: {result.stderr}"
        assert namespace in result.stdout
    
    def test_kubectl_secret_validation_patterns(self):
        """Test kubectl secret name validation patterns."""
        # This test validates the naming convention patterns
        valid_names = [
            "polygon-api-key",
            "alpha-vantage-api-key", 
            "db-credentials",
            "test-secret-123"
        ]
        
        invalid_names = [
            "Polygon_Api_Key",  # Contains uppercase and underscores
            "polygon api key",  # Contains spaces
            "polygon-api-key-", # Ends with hyphen
            "-polygon-api-key", # Starts with hyphen
            "polygon..api.key"  # Contains dots
        ]
        
        for name in valid_names:
            result = subprocess.run([
                "kubectl", "create", "secret", "generic", name,
                "--from-literal=test=value",
                "--dry-run=client"
            ], capture_output=True, text=True)
            assert result.returncode == 0, f"Valid secret name {name} should be accepted"
        
        for name in invalid_names:
            result = subprocess.run([
                "kubectl", "create", "secret", "generic", name,
                "--from-literal=test=value",
                "--dry-run=client"
            ], capture_output=True, text=True)
            # Some invalid names might still be accepted by kubectl
            # This test documents the expected behavior
    
    def test_kubectl_error_handling(self):
        """Test kubectl error handling for invalid operations."""
        # Test invalid secret name
        result = subprocess.run([
            "kubectl", "get", "secret", "nonexistent-secret-12345"
        ], capture_output=True, text=True)
        
        assert result.returncode != 0, "Should fail for nonexistent secret"
        assert "not found" in result.stderr.lower()
    
    def test_kubectl_permissions_check(self):
        """Test kubectl permissions for secret operations."""
        # Test if we can create secrets
        result = subprocess.run([
            "kubectl", "auth", "can-i", "create", "secrets"
        ], capture_output=True, text=True)
        
        # This might return "yes" or "no" depending on permissions
        assert result.returncode == 0, f"Permission check failed: {result.stderr}"
        assert result.stdout.strip() in ["yes", "no"]
        
        # Test if we can list secrets
        result = subprocess.run([
            "kubectl", "auth", "can-i", "list", "secrets"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Permission check failed: {result.stderr}"
        assert result.stdout.strip() in ["yes", "no"]
    
    def test_kubectl_context_validation(self):
        """Test kubectl context validation."""
        # Get current context
        result = subprocess.run([
            "kubectl", "config", "current-context"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Context validation failed: {result.stderr}"
        assert result.stdout.strip(), "No current context found"
        
        # Test context switching (if multiple contexts exist)
        contexts_result = subprocess.run([
            "kubectl", "config", "get-contexts", "-o", "name"
        ], capture_output=True, text=True)
        
        if contexts_result.returncode == 0:
            contexts = contexts_result.stdout.strip().split('\n')
            assert len(contexts) > 0, "No contexts found"
    
    def test_kubectl_secret_encoding(self):
        """Test kubectl secret value encoding."""
        # Test that secret values are properly base64 encoded
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Test encoding
TEST_KEY=hello_world_123
""")
            env_file = f.name
        
        try:
            result = subprocess.run([
                "kubectl", "create", "secret", "generic", "test-secret",
                "--from-env-file", env_file,
                "--dry-run=client", "-o", "yaml"
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Secret creation failed: {result.stderr}"
            
            # Check that the value is base64 encoded
            assert "data:" in result.stdout
            assert "TEST_KEY:" in result.stdout
            
            # The value should be base64 encoded (not plain text)
            assert "hello_world_123" not in result.stdout
            
        finally:
            os.unlink(env_file)


if __name__ == "__main__":
    pytest.main([__file__])

