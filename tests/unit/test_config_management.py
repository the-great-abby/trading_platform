"""
Unit Tests for Configuration Management

Tests the configuration management functionality that handles validation
settings, tolerances, and execution parameters.
"""

import pytest
from typing import Dict, Any
from datetime import datetime

# This will fail until implementation is complete
from src.validation.config.config_manager import ConfigManager
from src.validation.models.test_configuration import TestConfiguration


class TestConfigurationManagement:
    """Unit tests for configuration management"""
    
    @pytest.fixture
    def config_manager(self):
        """Create a configuration manager instance"""
        return ConfigManager()
    
    @pytest.fixture
    def default_config(self):
        """Create a default test configuration"""
        return TestConfiguration(
            id="default-config",
            name="Default Configuration",
            description="Default validation settings",
            tolerances={
                "returns_tolerance_pct": 0.1,
                "ratios_tolerance": 0.01,
                "drawdown_tolerance_pct": 0.05,
                "win_rate_tolerance_pct": 0.5
            },
            timeouts={
                "quick_test_seconds": 30,
                "standard_test_seconds": 300,
                "comprehensive_test_seconds": 1800,
                "options_test_seconds": 600
            },
            validation_rules={
                "require_exact_trade_counts": True,
                "allow_missing_metrics": [],
                "required_metrics": ["total_return_pct", "sharpe_ratio", "max_drawdown_pct"]
            },
            execution_settings={
                "parallel_execution": True,
                "max_parallel_jobs": 4,
                "retry_failed_tests": True,
                "max_retries": 2
            },
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_create_default_configuration(self, config_manager):
        """Test creating a default configuration"""
        # This test will FAIL until implementation is complete
        config = config_manager.create_default_configuration()
        
        # Verify default configuration structure
        assert isinstance(config, TestConfiguration)
        assert config.name == "Default Configuration"
        assert config.is_default is True
        assert config.tolerances is not None
        assert config.timeouts is not None
        assert config.validation_rules is not None
        assert config.execution_settings is not None
        
        # Verify default values
        assert config.tolerances["returns_tolerance_pct"] == 0.1
        assert config.tolerances["ratios_tolerance"] == 0.01
        assert config.tolerances["drawdown_tolerance_pct"] == 0.05
        assert config.tolerances["win_rate_tolerance_pct"] == 0.5
        
        assert config.timeouts["quick_test_seconds"] == 30
        assert config.timeouts["standard_test_seconds"] == 300
        assert config.timeouts["comprehensive_test_seconds"] == 1800
        assert config.timeouts["options_test_seconds"] == 600
        
        assert config.validation_rules["require_exact_trade_counts"] is True
        assert config.validation_rules["allow_missing_metrics"] == []
        assert "total_return_pct" in config.validation_rules["required_metrics"]
        
        assert config.execution_settings["parallel_execution"] is True
        assert config.execution_settings["max_parallel_jobs"] == 4
        assert config.execution_settings["retry_failed_tests"] is True
        assert config.execution_settings["max_retries"] == 2
    
    def test_save_and_load_configuration(self, config_manager, default_config):
        """Test saving and loading configurations"""
        # This test will FAIL until implementation is complete
        # Save configuration
        saved_config = config_manager.save_configuration(default_config)
        assert saved_config.id is not None
        
        # Load configuration
        loaded_config = config_manager.load_configuration(saved_config.id)
        assert loaded_config is not None
        assert loaded_config.id == saved_config.id
        assert loaded_config.name == default_config.name
        assert loaded_config.tolerances == default_config.tolerances
        assert loaded_config.timeouts == default_config.timeouts
        assert loaded_config.validation_rules == default_config.validation_rules
        assert loaded_config.execution_settings == default_config.execution_settings
    
    def test_list_configurations(self, config_manager, default_config):
        """Test listing all configurations"""
        # This test will FAIL until implementation is complete
        # Save a configuration
        config_manager.save_configuration(default_config)
        
        # List configurations
        configurations = config_manager.list_configurations()
        
        # Verify list contains our configuration
        assert len(configurations) >= 1
        config_names = [config.name for config in configurations]
        assert default_config.name in config_names
    
    def test_update_configuration(self, config_manager, default_config):
        """Test updating an existing configuration"""
        # This test will FAIL until implementation is complete
        # Save initial configuration
        saved_config = config_manager.save_configuration(default_config)
        
        # Update configuration
        saved_config.name = "Updated Configuration"
        saved_config.tolerances["returns_tolerance_pct"] = 0.05  # Stricter tolerance
        saved_config.execution_settings["max_parallel_jobs"] = 8  # More parallel jobs
        
        updated_config = config_manager.update_configuration(saved_config)
        
        # Verify updates
        assert updated_config.name == "Updated Configuration"
        assert updated_config.tolerances["returns_tolerance_pct"] == 0.05
        assert updated_config.execution_settings["max_parallel_jobs"] == 8
        assert updated_config.updated_at > saved_config.updated_at
    
    def test_delete_configuration(self, config_manager, default_config):
        """Test deleting a configuration"""
        # This test will FAIL until implementation is complete
        # Save configuration
        saved_config = config_manager.save_configuration(default_config)
        config_id = saved_config.id
        
        # Verify configuration exists
        loaded_config = config_manager.load_configuration(config_id)
        assert loaded_config is not None
        
        # Delete configuration
        config_manager.delete_configuration(config_id)
        
        # Verify configuration is deleted
        with pytest.raises(ValueError):
            config_manager.load_configuration(config_id)
    
    def test_get_default_configuration(self, config_manager, default_config):
        """Test getting the default configuration"""
        # This test will FAIL until implementation is complete
        # Save default configuration
        config_manager.save_configuration(default_config)
        
        # Get default configuration
        default = config_manager.get_default_configuration()
        
        # Verify default configuration
        assert default is not None
        assert default.is_default is True
        assert default.name == default_config.name
    
    def test_set_default_configuration(self, config_manager, default_config):
        """Test setting a configuration as default"""
        # This test will FAIL until implementation is complete
        # Create and save a new configuration
        new_config = TestConfiguration(
            id="new-config",
            name="New Configuration",
            description="New validation settings",
            tolerances=default_config.tolerances.copy(),
            timeouts=default_config.timeouts.copy(),
            validation_rules=default_config.validation_rules.copy(),
            execution_settings=default_config.execution_settings.copy(),
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        saved_new_config = config_manager.save_configuration(new_config)
        
        # Set as default
        config_manager.set_default_configuration(saved_new_config.id)
        
        # Verify it's now default
        updated_config = config_manager.load_configuration(saved_new_config.id)
        assert updated_config.is_default is True
        
        # Verify old default is no longer default
        old_default = config_manager.get_default_configuration()
        if old_default and old_default.id != saved_new_config.id:
            assert old_default.is_default is False
    
    def test_validate_configuration(self, config_manager):
        """Test configuration validation"""
        # This test will FAIL until implementation is complete
        # Test valid configuration
        valid_config = TestConfiguration(
            id="valid-config",
            name="Valid Configuration",
            description="Valid validation settings",
            tolerances={
                "returns_tolerance_pct": 0.1,
                "ratios_tolerance": 0.01,
                "drawdown_tolerance_pct": 0.05,
                "win_rate_tolerance_pct": 0.5
            },
            timeouts={
                "quick_test_seconds": 30,
                "standard_test_seconds": 300,
                "comprehensive_test_seconds": 1800,
                "options_test_seconds": 600
            },
            validation_rules={
                "require_exact_trade_counts": True,
                "allow_missing_metrics": [],
                "required_metrics": ["total_return_pct", "sharpe_ratio"]
            },
            execution_settings={
                "parallel_execution": True,
                "max_parallel_jobs": 4,
                "retry_failed_tests": True,
                "max_retries": 2
            },
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Should validate successfully
        assert config_manager.validate_configuration(valid_config) is True
        
        # Test invalid configuration (negative tolerance)
        invalid_config = TestConfiguration(
            id="invalid-config",
            name="Invalid Configuration",
            description="Invalid validation settings",
            tolerances={
                "returns_tolerance_pct": -0.1,  # Negative tolerance (invalid)
                "ratios_tolerance": 0.01,
                "drawdown_tolerance_pct": 0.05,
                "win_rate_tolerance_pct": 0.5
            },
            timeouts={
                "quick_test_seconds": 30,
                "standard_test_seconds": 300,
                "comprehensive_test_seconds": 1800,
                "options_test_seconds": 600
            },
            validation_rules={
                "require_exact_trade_counts": True,
                "allow_missing_metrics": [],
                "required_metrics": ["total_return_pct", "sharpe_ratio"]
            },
            execution_settings={
                "parallel_execution": True,
                "max_parallel_jobs": 4,
                "retry_failed_tests": True,
                "max_retries": 2
            },
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Should fail validation
        assert config_manager.validate_configuration(invalid_config) is False
    
    def test_configuration_error_handling(self, config_manager):
        """Test error handling in configuration management"""
        # This test will FAIL until implementation is complete
        # Test loading non-existent configuration
        with pytest.raises(ValueError):
            config_manager.load_configuration("non-existent-id")
        
        # Test deleting non-existent configuration
        with pytest.raises(ValueError):
            config_manager.delete_configuration("non-existent-id")
        
        # Test setting non-existent configuration as default
        with pytest.raises(ValueError):
            config_manager.set_default_configuration("non-existent-id")
        
        # Test updating non-existent configuration
        non_existent_config = TestConfiguration(
            id="non-existent",
            name="Non Existent",
            description="This config doesn't exist",
            tolerances={},
            timeouts={},
            validation_rules={},
            execution_settings={},
            is_default=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with pytest.raises(ValueError):
            config_manager.update_configuration(non_existent_config)
    
    def test_configuration_serialization(self, config_manager, default_config):
        """Test configuration serialization and deserialization"""
        # This test will FAIL until implementation is complete
        # Test JSON serialization
        json_data = config_manager.serialize_to_json(default_config)
        assert isinstance(json_data, str)
        
        # Test JSON deserialization
        deserialized_config = config_manager.deserialize_from_json(json_data)
        assert isinstance(deserialized_config, TestConfiguration)
        assert deserialized_config.name == default_config.name
        assert deserialized_config.tolerances == default_config.tolerances
        assert deserialized_config.timeouts == default_config.timeouts
    
    def test_configuration_export_import(self, config_manager, default_config):
        """Test configuration export and import"""
        # This test will FAIL until implementation is complete
        # Save configuration
        saved_config = config_manager.save_configuration(default_config)
        
        # Export configuration
        export_data = config_manager.export_configuration(saved_config.id)
        assert isinstance(export_data, dict)
        assert "id" in export_data
        assert "name" in export_data
        assert "tolerances" in export_data
        assert "timeouts" in export_data
        
        # Import configuration with new name
        imported_config = config_manager.import_configuration(export_data, "Imported Configuration")
        assert imported_config.name == "Imported Configuration"
        assert imported_config.tolerances == default_config.tolerances
        assert imported_config.timeouts == default_config.timeouts
    
    def test_configuration_search_and_filter(self, config_manager, default_config):
        """Test searching and filtering configurations"""
        # This test will FAIL until implementation is complete
        # Save configuration
        config_manager.save_configuration(default_config)
        
        # Test search by name
        search_results = config_manager.search_configurations("Default")
        assert len(search_results) >= 1
        assert any(config.name == default_config.name for config in search_results)
        
        # Test filter by default status
        default_configs = config_manager.filter_configurations(is_default=True)
        assert len(default_configs) >= 1
        assert all(config.is_default is True for config in default_configs)
        
        # Test filter by creation date
        recent_configs = config_manager.filter_configurations(
            created_after=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        assert len(recent_configs) >= 1
        assert any(config.id == default_config.id for config in recent_configs)


if __name__ == "__main__":
    pytest.main([__file__])













