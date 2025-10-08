#!/usr/bin/env python3
"""
Integration tests for .env file validation.
These tests validate the .env file parsing and validation functionality.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path


class TestEnvValidationIntegration:
    """Integration tests for .env file validation."""
    
    def test_validate_env_script_exists(self):
        """Test that validate-env.sh script exists and is executable."""
        # This test will fail until T010 (validate-env.sh) is implemented
        script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
        assert script_path.exists(), f"validate-env.sh script not found at {script_path}"
        assert script_path.is_file(), f"validate-env.sh is not a file"
        assert os.access(script_path, os.X_OK), f"validate-env.sh is not executable"
    
    def test_validate_env_with_valid_file(self):
        """Test validation with a valid .env file."""
        # This test will fail until T010 (validate-env.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Valid .env file for testing
POLYGON_API_KEY=test_api_key_123
ALPHA_VANTAGE_API_KEY=test_alpha_key_456
DB_HOST=localhost
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_database
""")
            env_file = f.name
        
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run(
                [str(script_path), env_file],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Validation failed: {result.stderr}"
            assert "valid" in result.stdout.lower() or "success" in result.stdout.lower()
        finally:
            os.unlink(env_file)
    
    def test_validate_env_with_missing_file(self):
        """Test validation with a missing .env file."""
        # This test will fail until T010 (validate-env.sh) is implemented
        script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
        result = subprocess.run(
            [str(script_path), "/nonexistent/file.env"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, "Validation should fail for missing file"
        assert "not found" in result.stderr.lower() or "missing" in result.stderr.lower()
    
    def test_validate_env_with_empty_file(self):
        """Test validation with an empty .env file."""
        # This test will fail until T010 (validate-env.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("# Empty .env file\n")
            env_file = f.name
        
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run(
                [str(script_path), env_file],
                capture_output=True,
                text=True
            )
            assert result.returncode != 0, "Validation should fail for empty file"
            assert "empty" in result.stderr.lower() or "missing" in result.stderr.lower()
        finally:
            os.unlink(env_file)
    
    def test_validate_env_with_invalid_format(self):
        """Test validation with invalid .env file format."""
        # This test will fail until T010 (validate-env.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Invalid .env file format
INVALID_LINE_WITHOUT_EQUALS
POLYGON_API_KEY=test_key
ANOTHER_INVALID_LINE
""")
            env_file = f.name
        
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run(
                [str(script_path), env_file],
                capture_output=True,
                text=True
            )
            assert result.returncode != 0, "Validation should fail for invalid format"
            assert "invalid" in result.stderr.lower() or "format" in result.stderr.lower()
        finally:
            os.unlink(env_file)
    
    def test_validate_env_with_empty_values(self):
        """Test validation with empty values in .env file."""
        # This test will fail until T010 (validate-env.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# .env file with empty values
POLYGON_API_KEY=
ALPHA_VANTAGE_API_KEY=test_key
DB_HOST=localhost
DB_USERNAME=
DB_PASSWORD=test_password
DB_NAME=test_database
""")
            env_file = f.name
        
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run(
                [str(script_path), env_file],
                capture_output=True,
                text=True
            )
            assert result.returncode != 0, "Validation should fail for empty values"
            assert "empty" in result.stderr.lower() or "missing" in result.stderr.lower()
        finally:
            os.unlink(env_file)
    
    def test_validate_env_with_missing_required_variables(self):
        """Test validation with missing required variables."""
        # This test will fail until T010 (validate-env.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# .env file missing required variables
POLYGON_API_KEY=test_key
# Missing ALPHA_VANTAGE_API_KEY
DB_HOST=localhost
DB_USERNAME=test_user
# Missing DB_PASSWORD
DB_NAME=test_database
""")
            env_file = f.name
        
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run(
                [str(script_path), env_file],
                capture_output=True,
                text=True
            )
            assert result.returncode != 0, "Validation should fail for missing required variables"
            assert "missing" in result.stderr.lower() or "required" in result.stderr.lower()
        finally:
            os.unlink(env_file)
    
    def test_validate_env_file_permissions(self):
        """Test validation checks file permissions."""
        # This test will fail until T010 (validate-env.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# .env file with proper content
POLYGON_API_KEY=test_key
ALPHA_VANTAGE_API_KEY=test_key
DB_HOST=localhost
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_database
""")
            env_file = f.name
        
        try:
            # Set overly permissive permissions
            os.chmod(env_file, 0o644)
            
            script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run(
                [str(script_path), env_file],
                capture_output=True,
                text=True
            )
            assert result.returncode != 0, "Validation should fail for overly permissive file permissions"
            assert "permission" in result.stderr.lower() or "security" in result.stderr.lower()
        finally:
            os.unlink(env_file)
    
    def test_validate_env_output_format(self):
        """Test that validation output follows expected format."""
        # This test will fail until T010 (validate-env.sh) is implemented
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("""# Valid .env file for testing
POLYGON_API_KEY=test_api_key_123
ALPHA_VANTAGE_API_KEY=test_alpha_key_456
DB_HOST=localhost
DB_USERNAME=test_user
DB_PASSWORD=test_password
DB_NAME=test_database
""")
            env_file = f.name
        
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
            result = subprocess.run(
                [str(script_path), env_file],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Validation failed: {result.stderr}"
            
            # Check for expected output format
            output = result.stdout
            assert "validating" in output.lower() or "validation" in output.lower()
            assert "✅" in output or "success" in output.lower()
            
        finally:
            os.unlink(env_file)


if __name__ == "__main__":
    pytest.main([__file__])













