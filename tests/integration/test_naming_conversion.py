#!/usr/bin/env python3
"""
Integration tests for secret naming conversion.
These tests validate the underscore-to-hyphen conversion functionality.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path


class TestNamingConversionIntegration:
    """Integration tests for secret naming conversion."""
    
    def test_naming_conversion_script_exists(self):
        """Test that naming conversion functionality exists."""
        # This test will fail until T013 (secret-helpers.sh) is implemented
        script_path = Path(__file__).parent.parent.parent / "scripts" / "secret-helpers.sh"
        assert script_path.exists(), f"secret-helpers.sh script not found at {script_path}"
        assert script_path.is_file(), f"secret-helpers.sh is not a file"
        assert os.access(script_path, os.X_OK), f"secret-helpers.sh is not executable"
    
    def test_underscore_to_hyphen_conversion(self):
        """Test conversion of underscore-separated names to hyphen-separated."""
        # This test will fail until T013 (secret-helpers.sh) is implemented
        test_cases = [
            ("POLYGON_API_KEY", "polygon-api-key"),
            ("ALPHA_VANTAGE_API_KEY", "alpha-vantage-api-key"),
            ("DB_HOST", "db-host"),
            ("DB_USERNAME", "db-username"),
            ("DB_PASSWORD", "db-password"),
            ("DB_NAME", "db-name"),
            ("TWILIO_API_KEY", "twilio-api-key"),
            ("SENDGRID_API_KEY", "sendgrid-api-key"),
        ]
        
        for env_var, expected_k8s_name in test_cases:
            # Test the conversion function
            script_path = Path(__file__).parent.parent.parent / "scripts" / "secret-helpers.sh"
            result = subprocess.run([
                str(script_path), "convert-name", env_var
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Conversion failed for {env_var}: {result.stderr}"
            assert result.stdout.strip() == expected_k8s_name, \
                f"Expected {expected_k8s_name}, got {result.stdout.strip()}"
    
    def test_naming_conversion_with_complex_names(self):
        """Test conversion with complex naming patterns."""
        # This test will fail until T013 (secret-helpers.sh) is implemented
        test_cases = [
            ("API_KEY_123", "api-key-123"),
            ("TEST_VAR_WITH_MULTIPLE_UNDERSCORES", "test-var-with-multiple-underscores"),
            ("SINGLE", "single"),
            ("A_B_C_D_E", "a-b-c-d-e"),
        ]
        
        for env_var, expected_k8s_name in test_cases:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "secret-helpers.sh"
            result = subprocess.run([
                str(script_path), "convert-name", env_var
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Conversion failed for {env_var}: {result.stderr}"
            assert result.stdout.strip() == expected_k8s_name, \
                f"Expected {expected_k8s_name}, got {result.stdout.strip()}"
    
    def test_naming_conversion_validation(self):
        """Test that converted names meet Kubernetes naming requirements."""
        # This test will fail until T013 (secret-helpers.sh) is implemented
        # Kubernetes secret names must:
        # - Start and end with alphanumeric characters
        # - Contain only lowercase letters, numbers, and hyphens
        # - Be no longer than 253 characters
        
        valid_env_vars = [
            "POLYGON_API_KEY",
            "DB_HOST",
            "ALPHA_VANTAGE_API_KEY",
            "TEST_VAR_123"
        ]
        
        for env_var in valid_env_vars:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "secret-helpers.sh"
            result = subprocess.run([
                str(script_path), "convert-name", env_var
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Conversion failed for {env_var}: {result.stderr}"
            
            k8s_name = result.stdout.strip()
            
            # Validate Kubernetes naming requirements
            assert k8s_name[0].isalnum(), f"K8s name {k8s_name} must start with alphanumeric"
            assert k8s_name[-1].isalnum(), f"K8s name {k8s_name} must end with alphanumeric"
            assert k8s_name.islower(), f"K8s name {k8s_name} must be lowercase"
            assert all(c.isalnum() or c == '-' for c in k8s_name), \
                f"K8s name {k8s_name} can only contain lowercase letters, numbers, and hyphens"
            assert len(k8s_name) <= 253, f"K8s name {k8s_name} must be <= 253 characters"
    
    def test_naming_conversion_error_handling(self):
        """Test error handling for invalid input names."""
        # This test will fail until T013 (secret-helpers.sh) is implemented
        invalid_inputs = [
            "",  # Empty string
            "123_START_WITH_NUMBER",  # Starts with number
            "_START_WITH_UNDERSCORE",  # Starts with underscore
            "END_WITH_UNDERSCORE_",  # Ends with underscore
            "CONTAINS_SPACES",  # Contains spaces (though this should be handled)
        ]
        
        for invalid_input in invalid_inputs:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "secret-helpers.sh"
            result = subprocess.run([
                str(script_path), "convert-name", invalid_input
            ], capture_output=True, text=True)
            
            # Should either fail gracefully or handle the input appropriately
            if result.returncode != 0:
                assert "invalid" in result.stderr.lower() or "error" in result.stderr.lower()
    
    def test_naming_conversion_batch_processing(self):
        """Test batch processing of multiple environment variables."""
        # This test will fail until T013 (secret-helpers.sh) is implemented
        env_vars = [
            "POLYGON_API_KEY",
            "ALPHA_VANTAGE_API_KEY", 
            "DB_HOST",
            "DB_USERNAME",
            "DB_PASSWORD",
            "DB_NAME"
        ]
        
        expected_mappings = {
            "POLYGON_API_KEY": "polygon-api-key",
            "ALPHA_VANTAGE_API_KEY": "alpha-vantage-api-key",
            "DB_HOST": "db-host",
            "DB_USERNAME": "db-username", 
            "DB_PASSWORD": "db-password",
            "DB_NAME": "db-name"
        }
        
        # Test batch conversion
        script_path = Path(__file__).parent.parent.parent / "scripts" / "secret-helpers.sh"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('\n'.join(env_vars))
            input_file = f.name
        
        try:
            result = subprocess.run([
                str(script_path), "convert-names", input_file
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Batch conversion failed: {result.stderr}"
            
            # Parse output and verify mappings
            output_lines = result.stdout.strip().split('\n')
            assert len(output_lines) == len(env_vars), "Output should have same number of lines as input"
            
            for line in output_lines:
                parts = line.split(' -> ')
                assert len(parts) == 2, f"Invalid output format: {line}"
                env_var, k8s_name = parts
                assert expected_mappings[env_var] == k8s_name, \
                    f"Expected {expected_mappings[env_var]}, got {k8s_name}"
                    
        finally:
            os.unlink(input_file)
    
    def test_naming_conversion_integration_with_env_file(self):
        """Test naming conversion integrated with .env file processing."""
        # This test will fail until T010 (validate-env.sh) and T013 (secret-helpers.sh) are implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Test .env file for naming conversion
POLYGON_API_KEY=test_key_123
ALPHA_VANTAGE_API_KEY=test_alpha_456
DB_HOST=localhost
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_database
""")
            env_file = f.name
        
        try:
            # Test that the validation script can process the file and convert names
            script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run([
                str(script_path), env_file
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Validation failed: {result.stderr}"
            
            # Check that the output mentions the converted secret names
            output = result.stdout.lower()
            expected_secrets = [
                "polygon-api-key",
                "alpha-vantage-api-key", 
                "db-credentials"  # Database vars are combined
            ]
            
            for secret_name in expected_secrets:
                assert secret_name in output, f"Expected secret name {secret_name} not found in output"
                
        finally:
            os.unlink(env_file)
    
    def test_naming_conversion_performance(self):
        """Test naming conversion performance with many variables."""
        # This test will fail until T013 (secret-helpers.sh) is implemented
        import time
        
        # Generate many environment variables
        env_vars = [f"TEST_VAR_{i:03d}" for i in range(100)]
        
        start_time = time.time()
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "secret-helpers.sh"
        for env_var in env_vars:
            result = subprocess.run([
                str(script_path), "convert-name", env_var
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Conversion failed for {env_var}: {result.stderr}"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (< 1 second for 100 conversions)
        assert duration < 1.0, f"Conversion took too long: {duration:.2f} seconds"
    
    def test_naming_conversion_consistency(self):
        """Test that naming conversion is consistent across multiple runs."""
        # This test will fail until T013 (secret-helpers.sh) is implemented
        test_var = "POLYGON_API_KEY"
        expected_result = "polygon-api-key"
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "secret-helpers.sh"
        
        # Run conversion multiple times
        for i in range(10):
            result = subprocess.run([
                str(script_path), "convert-name", test_var
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Conversion failed on run {i}: {result.stderr}"
            assert result.stdout.strip() == expected_result, \
                f"Result inconsistent on run {i}: expected {expected_result}, got {result.stdout.strip()}"


if __name__ == "__main__":
    pytest.main([__file__])













