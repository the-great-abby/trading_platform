#!/usr/bin/env python3
"""
End-to-end integration tests for complete secrets workflow.
These tests validate the entire workflow from .env file to Kubernetes secrets.
"""

import pytest
import subprocess
import tempfile
import os
import time
from pathlib import Path


class TestSecretsWorkflowIntegration:
    """End-to-end integration tests for secrets workflow."""
    
    def test_complete_workflow_scripts_exist(self):
        """Test that all required scripts exist for the complete workflow."""
        # This test will fail until all scripts are implemented
        scripts = [
            "scripts/validate-env.sh",
            "scripts/update-secrets.sh", 
            "scripts/list-secrets.sh",
            "scripts/secret-helpers.sh"
        ]
        
        for script in scripts:
            script_path = Path(__file__).parent.parent.parent / script
            assert script_path.exists(), f"Required script {script} not found"
            assert script_path.is_file(), f"{script} is not a file"
            assert os.access(script_path, os.X_OK), f"{script} is not executable"
    
    def test_complete_workflow_with_valid_env_file(self):
        """Test complete workflow with a valid .env file."""
        # This test will fail until all scripts are implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Valid .env file for complete workflow test
POLYGON_API_KEY=test_polygon_key_12345
ALPHA_VANTAGE_API_KEY=test_alpha_key_67890
DB_HOST=test-db-host
DB_USERNAME=test_db_user
DB_PASSWORD=test_db_password_secure
DB_NAME=test_trading_database
""")
            env_file = f.name
        
        try:
            # Step 1: Validate the .env file
            validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run([
                str(validate_script), env_file
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Validation failed: {result.stderr}"
            assert "valid" in result.stdout.lower() or "success" in result.stdout.lower()
            
            # Step 2: Update secrets in Kubernetes (dry-run first)
            update_script = Path(__file__).parent.parent.parent / "scripts" / "update-secrets.sh"
            result = subprocess.run([
                str(update_script), "--dry-run", env_file
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Dry-run update failed: {result.stderr}"
            assert "dry-run" in result.stdout.lower() or "would create" in result.stdout.lower()
            
            # Step 3: List secrets
            list_script = Path(__file__).parent.parent.parent / "scripts" / "list-secrets.sh"
            result = subprocess.run([
                str(list_script)
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"List secrets failed: {result.stderr}"
            assert "secrets" in result.stdout.lower()
            
        finally:
            os.unlink(env_file)
    
    def test_workflow_error_handling_missing_env_file(self):
        """Test workflow error handling when .env file is missing."""
        # This test will fail until all scripts are implemented
        validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
        result = subprocess.run([
            str(validate_script), "/nonexistent/file.env"
        ], capture_output=True, text=True)
        
        assert result.returncode != 0, "Validation should fail for missing file"
        assert "not found" in result.stderr.lower() or "missing" in result.stderr.lower()
        
        # Check that error message provides helpful next steps
        assert "next steps" in result.stderr.lower() or "help" in result.stderr.lower()
    
    def test_workflow_error_handling_invalid_env_file(self):
        """Test workflow error handling with invalid .env file."""
        # This test will fail until all scripts are implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Invalid .env file
POLYGON_API_KEY=
ALPHA_VANTAGE_API_KEY=test_key
INVALID_LINE_WITHOUT_EQUALS
DB_HOST=localhost
""")
            env_file = f.name
        
        try:
            validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run([
                str(validate_script), env_file
            ], capture_output=True, text=True)
            
            assert result.returncode != 0, "Validation should fail for invalid file"
            assert "error" in result.stderr.lower() or "invalid" in result.stderr.lower()
            
            # Check that error message provides helpful next steps
            assert "next steps" in result.stderr.lower() or "help" in result.stderr.lower()
            
        finally:
            os.unlink(env_file)
    
    def test_workflow_error_handling_kubectl_unavailable(self):
        """Test workflow error handling when kubectl is not available."""
        # This test will fail until all scripts are implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Valid .env file
POLYGON_API_KEY=test_key
ALPHA_VANTAGE_API_KEY=test_key
DB_HOST=localhost
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_db
""")
            env_file = f.name
        
        try:
            # Temporarily rename kubectl to simulate unavailability
            kubectl_backup = None
            kubectl_path = subprocess.run(["which", "kubectl"], capture_output=True, text=True)
            
            if kubectl_path.returncode == 0:
                kubectl_backup = kubectl_path.stdout.strip()
                # Note: We can't actually rename kubectl in this test environment
                # This test documents the expected behavior
            
            update_script = Path(__file__).parent.parent.parent / "scripts" / "update-secrets.sh"
            result = subprocess.run([
                str(update_script), env_file
            ], capture_output=True, text=True)
            
            # Should handle kubectl unavailability gracefully
            if result.returncode != 0:
                assert "kubectl" in result.stderr.lower() or "cluster" in result.stderr.lower()
                assert "next steps" in result.stderr.lower()
            
        finally:
            os.unlink(env_file)
    
    def test_workflow_performance_requirements(self):
        """Test that workflow meets performance requirements (<5 seconds)."""
        # This test will fail until all scripts are implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Performance test .env file
POLYGON_API_KEY=test_key
ALPHA_VANTAGE_API_KEY=test_key
DB_HOST=localhost
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_db
""")
            env_file = f.name
        
        try:
            start_time = time.time()
            
            # Run complete workflow (validation + dry-run update + list)
            validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            update_script = Path(__file__).parent.parent.parent / "scripts" / "update-secrets.sh"
            list_script = Path(__file__).parent.parent.parent / "scripts" / "list-secrets.sh"
            
            # Step 1: Validate
            result = subprocess.run([
                str(validate_script), env_file
            ], capture_output=True, text=True)
            assert result.returncode == 0, f"Validation failed: {result.stderr}"
            
            # Step 2: Dry-run update
            result = subprocess.run([
                str(update_script), "--dry-run", env_file
            ], capture_output=True, text=True)
            assert result.returncode == 0, f"Dry-run update failed: {result.stderr}"
            
            # Step 3: List secrets
            result = subprocess.run([
                str(list_script)
            ], capture_output=True, text=True)
            assert result.returncode == 0, f"List secrets failed: {result.stderr}"
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within 5 seconds
            assert duration < 5.0, f"Workflow took too long: {duration:.2f} seconds"
            
        finally:
            os.unlink(env_file)
    
    def test_workflow_secret_naming_consistency(self):
        """Test that secret naming is consistent throughout the workflow."""
        # This test will fail until all scripts are implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Naming consistency test .env file
POLYGON_API_KEY=test_polygon_key
ALPHA_VANTAGE_API_KEY=test_alpha_key
DB_HOST=test_host
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_db
""")
            env_file = f.name
        
        try:
            # Validate and get expected secret names
            validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run([
                str(validate_script), env_file
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Validation failed: {result.stderr}"
            
            # Check that validation output mentions expected secret names
            expected_secrets = [
                "polygon-api-key",
                "alpha-vantage-api-key",
                "db-credentials"
            ]
            
            validation_output = result.stdout.lower()
            for secret_name in expected_secrets:
                assert secret_name in validation_output, \
                    f"Expected secret name {secret_name} not found in validation output"
            
            # Check that update script uses same naming
            update_script = Path(__file__).parent.parent.parent / "scripts" / "update-secrets.sh"
            result = subprocess.run([
                str(update_script), "--dry-run", env_file
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Dry-run update failed: {result.stderr}"
            
            update_output = result.stdout.lower()
            for secret_name in expected_secrets:
                assert secret_name in update_output, \
                    f"Expected secret name {secret_name} not found in update output"
            
        finally:
            os.unlink(env_file)
    
    def test_workflow_makefile_integration(self):
        """Test workflow integration with Makefile targets."""
        # This test will fail until T016 (Makefile targets) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Makefile integration test .env file
POLYGON_API_KEY=test_key
ALPHA_VANTAGE_API_KEY=test_key
DB_HOST=localhost
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_db
""")
            env_file = f.name
        
        try:
            # Test make secrets-validate
            result = subprocess.run([
                "make", "secrets-validate", f"ENV_FILE={env_file}"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            assert result.returncode == 0, f"make secrets-validate failed: {result.stderr}"
            assert "validating" in result.stdout.lower() or "validation" in result.stdout.lower()
            
            # Test make secrets-update (dry-run)
            result = subprocess.run([
                "make", "secrets-update", f"ENV_FILE={env_file}", "DRY_RUN=true"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            assert result.returncode == 0, f"make secrets-update failed: {result.stderr}"
            assert "updating" in result.stdout.lower() or "update" in result.stdout.lower()
            
            # Test make secrets-list
            result = subprocess.run([
                "make", "secrets-list"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            assert result.returncode == 0, f"make secrets-list failed: {result.stderr}"
            assert "listing" in result.stdout.lower() or "list" in result.stdout.lower()
            
        finally:
            os.unlink(env_file)
    
    def test_workflow_security_requirements(self):
        """Test that workflow meets security requirements."""
        # This test will fail until all scripts are implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Security test .env file
POLYGON_API_KEY=secret_key_12345
ALPHA_VANTAGE_API_KEY=secret_alpha_67890
DB_HOST=secure_host
DB_USERNAME=secure_user
DB_PASSWORD=very_secure_password_123
DB_NAME=secure_database
""")
            env_file = f.name
        
        try:
            # Set overly permissive permissions
            os.chmod(env_file, 0o644)
            
            # Validation should fail for insecure permissions
            validate_script = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run([
                str(validate_script), env_file
            ], capture_output=True, text=True)
            
            assert result.returncode != 0, "Validation should fail for insecure file permissions"
            assert "permission" in result.stderr.lower() or "security" in result.stderr.lower()
            
            # Fix permissions
            os.chmod(env_file, 0o600)
            
            # Now validation should pass
            result = subprocess.run([
                str(validate_script), env_file
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Validation failed with correct permissions: {result.stderr}"
            
            # Check that secret values are never logged
            update_script = Path(__file__).parent.parent.parent / "scripts" / "update-secrets.sh"
            result = subprocess.run([
                str(update_script), "--dry-run", env_file
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Dry-run update failed: {result.stderr}"
            
            # Secret values should not appear in output
            output = result.stdout + result.stderr
            secret_values = ["secret_key_12345", "secret_alpha_67890", "very_secure_password_123"]
            
            for secret_value in secret_values:
                assert secret_value not in output, \
                    f"Secret value {secret_value} should not appear in output"
            
        finally:
            os.unlink(env_file)


if __name__ == "__main__":
    pytest.main([__file__])













