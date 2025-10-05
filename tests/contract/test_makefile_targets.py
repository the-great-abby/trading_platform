#!/usr/bin/env python3
"""
Contract tests for Makefile targets API.
These tests validate the expected behavior of Makefile targets for secrets management.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path


class TestMakefileTargetsContract:
    """Contract tests for Makefile targets API."""
    
    def test_secrets_validate_target_exists(self):
        """Test that secrets-validate target exists in Makefile."""
        # This test will fail until T016 (Makefile targets) is implemented
        result = subprocess.run(
            ["make", "-n", "secrets-validate"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        assert result.returncode == 0, f"secrets-validate target not found: {result.stderr}"
        assert "secrets-validate" in result.stdout or "validate-env" in result.stdout
    
    def test_secrets_update_target_exists(self):
        """Test that secrets-update target exists in Makefile."""
        # This test will fail until T016 (Makefile targets) is implemented
        result = subprocess.run(
            ["make", "-n", "secrets-update"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        assert result.returncode == 0, f"secrets-update target not found: {result.stderr}"
        assert "secrets-update" in result.stdout or "update-secrets" in result.stdout
    
    def test_secrets_list_target_exists(self):
        """Test that secrets-list target exists in Makefile."""
        # This test will fail until T016 (Makefile targets) is implemented
        result = subprocess.run(
            ["make", "-n", "secrets-list"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        assert result.returncode == 0, f"secrets-list target not found: {result.stderr}"
        assert "secrets-list" in result.stdout or "list-secrets" in result.stdout
    
    def test_secrets_validate_script_exists(self):
        """Test that validate-env.sh script exists."""
        # This test will fail until T010 (validate-env.sh) is implemented
        script_path = Path(__file__).parent.parent.parent / "scripts" / "validate-env.sh"
        assert script_path.exists(), f"validate-env.sh script not found at {script_path}"
        assert script_path.is_file(), f"validate-env.sh is not a file"
        assert os.access(script_path, os.X_OK), f"validate-env.sh is not executable"
    
    def test_update_secrets_script_exists(self):
        """Test that update-secrets.sh script exists."""
        # This test will fail until T011 (update-secrets.sh) is implemented
        script_path = Path(__file__).parent.parent.parent / "scripts" / "update-secrets.sh"
        assert script_path.exists(), f"update-secrets.sh script not found at {script_path}"
        assert script_path.is_file(), f"update-secrets.sh is not a file"
        assert os.access(script_path, os.X_OK), f"update-secrets.sh is not executable"
    
    def test_list_secrets_script_exists(self):
        """Test that list-secrets.sh script exists."""
        # This test will fail until T012 (list-secrets.sh) is implemented
        script_path = Path(__file__).parent.parent.parent / "scripts" / "list-secrets.sh"
        assert script_path.exists(), f"list-secrets.sh script not found at {script_path}"
        assert script_path.is_file(), f"list-secrets.sh is not a file"
        assert os.access(script_path, os.X_OK), f"list-secrets.sh is not executable"
    
    def test_makefile_targets_follow_naming_convention(self):
        """Test that Makefile targets follow the secrets-* naming convention."""
        # This test will fail until T016 (Makefile targets) is implemented
        makefile_path = Path(__file__).parent.parent.parent / "Makefile"
        assert makefile_path.exists(), "Makefile not found"
        
        with open(makefile_path, 'r') as f:
            content = f.read()
        
        # Check for secrets-related targets
        secrets_targets = []
        for line in content.split('\n'):
            if line.strip().startswith('secrets-') and ':' in line:
                target_name = line.split(':')[0].strip()
                secrets_targets.append(target_name)
        
        expected_targets = ['secrets-validate', 'secrets-update', 'secrets-list']
        for target in expected_targets:
            assert target in secrets_targets, f"Expected target {target} not found in Makefile"
    
    def test_makefile_targets_have_descriptions(self):
        """Test that Makefile targets have descriptive comments."""
        # This test will fail until T016 (Makefile targets) is implemented
        makefile_path = Path(__file__).parent.parent.parent / "Makefile"
        assert makefile_path.exists(), "Makefile not found"
        
        with open(makefile_path, 'r') as f:
            content = f.read()
        
        # Check for descriptive comments before secrets targets
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('secrets-') and ':' in line:
                # Check if there's a comment line before this target
                has_comment = False
                for j in range(max(0, i-3), i):
                    if lines[j].strip().startswith('#'):
                        has_comment = True
                        break
                assert has_comment, f"Target {line.strip()} should have a descriptive comment"


if __name__ == "__main__":
    pytest.main([__file__])

