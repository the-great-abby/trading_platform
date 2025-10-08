"""
Configuration management service for validation settings

This service manages validation configurations including tolerances,
timeouts, and execution settings.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..models.test_configuration import TestConfiguration

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Service for managing validation configurations.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".validation_framework" / "configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.configurations: Dict[str, TestConfiguration] = {}
        self.default_config_id: Optional[str] = None
        
        # Load existing configurations
        self._load_configurations()
    
    def create_default_configuration(self) -> TestConfiguration:
        """
        Create a default validation configuration.
        
        Returns:
            TestConfiguration with default settings
        """
        default_config = TestConfiguration(
            name="Default Configuration",
            description="Default validation settings for backtest scripts",
            is_default=True
        )
        
        # Save the default configuration
        saved_config = self.save_configuration(default_config)
        self.default_config_id = saved_config.id
        
        logger.info("Created default validation configuration")
        return saved_config
    
    def save_configuration(self, configuration: TestConfiguration) -> TestConfiguration:
        """
        Save a configuration to storage.
        
        Args:
            configuration: TestConfiguration to save
            
        Returns:
            Saved TestConfiguration with assigned ID
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.validate_configuration(configuration):
            raise ValueError("Configuration validation failed")
        
        # If this is the first configuration or it's marked as default, set it as default
        if not self.configurations or configuration.is_default:
            # Clear default flag from existing configurations
            for config in self.configurations.values():
                config.is_default = False
            
            configuration.is_default = True
            self.default_config_id = configuration.id
        
        # Save to storage
        config_file = self.config_dir / f"{configuration.id}.json"
        config_data = configuration.to_dict()
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Update in-memory cache
        self.configurations[configuration.id] = configuration
        
        logger.info(f"Saved configuration: {configuration.name}")
        return configuration
    
    def load_configuration(self, config_id: str) -> TestConfiguration:
        """
        Load a configuration by ID.
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            TestConfiguration object
            
        Raises:
            ValueError: If configuration not found
        """
        if config_id in self.configurations:
            return self.configurations[config_id]
        
        # Try to load from file
        config_file = self.config_dir / f"{config_id}.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            configuration = TestConfiguration.from_dict(config_data)
            self.configurations[config_id] = configuration
            return configuration
        
        raise ValueError(f"Configuration not found: {config_id}")
    
    def list_configurations(self) -> List[TestConfiguration]:
        """
        List all available configurations.
        
        Returns:
            List of TestConfiguration objects
        """
        return list(self.configurations.values())
    
    def update_configuration(self, configuration: TestConfiguration) -> TestConfiguration:
        """
        Update an existing configuration.
        
        Args:
            configuration: Updated TestConfiguration
            
        Returns:
            Updated TestConfiguration
            
        Raises:
            ValueError: If configuration not found or invalid
        """
        if configuration.id not in self.configurations:
            raise ValueError(f"Configuration not found: {configuration.id}")
        
        if not self.validate_configuration(configuration):
            raise ValueError("Configuration validation failed")
        
        # Update timestamp
        configuration.updated_at = datetime.now()
        
        # Save updated configuration
        return self.save_configuration(configuration)
    
    def delete_configuration(self, config_id: str) -> None:
        """
        Delete a configuration.
        
        Args:
            config_id: Configuration identifier to delete
            
        Raises:
            ValueError: If configuration not found
        """
        if config_id not in self.configurations:
            raise ValueError(f"Configuration not found: {config_id}")
        
        # Don't allow deletion of default configuration
        if self.configurations[config_id].is_default:
            raise ValueError("Cannot delete default configuration")
        
        # Remove from storage
        config_file = self.config_dir / f"{config_id}.json"
        if config_file.exists():
            config_file.unlink()
        
        # Remove from in-memory cache
        del self.configurations[config_id]
        
        logger.info(f"Deleted configuration: {config_id}")
    
    def get_default_configuration(self) -> Optional[TestConfiguration]:
        """
        Get the default configuration.
        
        Returns:
            Default TestConfiguration or None if not set
        """
        if self.default_config_id and self.default_config_id in self.configurations:
            return self.configurations[self.default_config_id]
        
        # Try to find a default configuration
        for config in self.configurations.values():
            if config.is_default:
                self.default_config_id = config.id
                return config
        
        return None
    
    def set_default_configuration(self, config_id: str) -> None:
        """
        Set a configuration as the default.
        
        Args:
            config_id: Configuration identifier to set as default
            
        Raises:
            ValueError: If configuration not found
        """
        if config_id not in self.configurations:
            raise ValueError(f"Configuration not found: {config_id}")
        
        # Clear default flag from existing configurations
        for config in self.configurations.values():
            config.is_default = False
        
        # Set new default
        self.configurations[config_id].is_default = True
        self.default_config_id = config_id
        
        # Save the change
        self.save_configuration(self.configurations[config_id])
        
        logger.info(f"Set default configuration: {config_id}")
    
    def validate_configuration(self, configuration: TestConfiguration) -> bool:
        """
        Validate a configuration.
        
        Args:
            configuration: TestConfiguration to validate
            
        Returns:
            True if configuration is valid
        """
        try:
            # Validate basic fields
            if not configuration.name or not configuration.name.strip():
                logger.error("Configuration name is empty")
                return False
            
            # Validate tolerances
            tolerances = configuration.tolerances
            if tolerances.returns_tolerance_pct < 0:
                logger.error("Returns tolerance must be non-negative")
                return False
            
            if tolerances.ratios_tolerance < 0:
                logger.error("Ratios tolerance must be non-negative")
                return False
            
            if tolerances.drawdown_tolerance_pct < 0:
                logger.error("Drawdown tolerance must be non-negative")
                return False
            
            if tolerances.win_rate_tolerance_pct < 0:
                logger.error("Win rate tolerance must be non-negative")
                return False
            
            # Validate timeouts
            timeouts = configuration.timeouts
            if timeouts.quick_test_seconds <= 0:
                logger.error("Quick test timeout must be positive")
                return False
            
            if timeouts.standard_test_seconds <= 0:
                logger.error("Standard test timeout must be positive")
                return False
            
            if timeouts.comprehensive_test_seconds <= 0:
                logger.error("Comprehensive test timeout must be positive")
                return False
            
            if timeouts.options_test_seconds <= 0:
                logger.error("Options test timeout must be positive")
                return False
            
            # Validate execution settings
            execution = configuration.execution_settings
            if execution.max_parallel_jobs <= 0:
                logger.error("Max parallel jobs must be positive")
                return False
            
            if execution.max_retries < 0:
                logger.error("Max retries must be non-negative")
                return False
            
            # Validate validation rules
            rules = configuration.validation_rules
            if not rules.required_metrics:
                logger.error("Required metrics list cannot be empty")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
    
    def search_configurations(self, query: str) -> List[TestConfiguration]:
        """
        Search configurations by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching TestConfiguration objects
        """
        query_lower = query.lower()
        matching_configs = []
        
        for config in self.configurations.values():
            if (query_lower in config.name.lower() or 
                query_lower in config.description.lower()):
                matching_configs.append(config)
        
        return matching_configs
    
    def filter_configurations(self, is_default: Optional[bool] = None,
                            created_after: Optional[datetime] = None) -> List[TestConfiguration]:
        """
        Filter configurations by criteria.
        
        Args:
            is_default: Filter by default status
            created_after: Filter by creation date
            
        Returns:
            List of filtered TestConfiguration objects
        """
        filtered_configs = list(self.configurations.values())
        
        if is_default is not None:
            filtered_configs = [c for c in filtered_configs if c.is_default == is_default]
        
        if created_after is not None:
            filtered_configs = [c for c in filtered_configs if c.created_at >= created_after]
        
        return filtered_configs
    
    def serialize_to_json(self, configuration: TestConfiguration) -> str:
        """
        Serialize configuration to JSON string.
        
        Args:
            configuration: TestConfiguration to serialize
            
        Returns:
            JSON string representation
        """
        return json.dumps(configuration.to_dict(), indent=2)
    
    def deserialize_from_json(self, json_data: str) -> TestConfiguration:
        """
        Deserialize configuration from JSON string.
        
        Args:
            json_data: JSON string representation
            
        Returns:
            TestConfiguration object
            
        Raises:
            ValueError: If JSON data is invalid
        """
        try:
            config_data = json.loads(json_data)
            return TestConfiguration.from_dict(config_data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid JSON data: {e}")
    
    def export_configuration(self, config_id: str) -> Dict[str, Any]:
        """
        Export configuration data.
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            Dictionary with configuration data
            
        Raises:
            ValueError: If configuration not found
        """
        if config_id not in self.configurations:
            raise ValueError(f"Configuration not found: {config_id}")
        
        config = self.configurations[config_id]
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "tolerances": config.tolerances.dict(),
            "timeouts": config.timeouts.dict(),
            "validation_rules": config.validation_rules.dict(),
            "execution_settings": config.execution_settings.dict(),
            "is_default": config.is_default,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
    
    def import_configuration(self, config_data: Dict[str, Any], 
                           new_name: Optional[str] = None) -> TestConfiguration:
        """
        Import configuration data.
        
        Args:
            config_data: Configuration data dictionary
            new_name: Optional new name for imported configuration
            
        Returns:
            Imported TestConfiguration object
            
        Raises:
            ValueError: If configuration data is invalid
        """
        try:
            # Create new configuration from data
            configuration = TestConfiguration.from_dict(config_data)
            
            # Override name if provided
            if new_name:
                configuration.name = new_name
            
            # Generate new ID and timestamps
            configuration.id = None  # Will be generated
            configuration.created_at = datetime.now()
            configuration.updated_at = datetime.now()
            configuration.is_default = False  # Imported configs are not default
            
            return self.save_configuration(configuration)
            
        except Exception as e:
            raise ValueError(f"Failed to import configuration: {e}")
    
    def _load_configurations(self) -> None:
        """Load all configurations from storage."""
        if not self.config_dir.exists():
            return
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                configuration = TestConfiguration.from_dict(config_data)
                self.configurations[configuration.id] = configuration
                
                if configuration.is_default:
                    self.default_config_id = configuration.id
                
                logger.debug(f"Loaded configuration: {configuration.name}")
                
            except Exception as e:
                logger.warning(f"Failed to load configuration from {config_file}: {e}")
    
    def get_configuration_by_name(self, name: str) -> Optional[TestConfiguration]:
        """
        Get configuration by name.
        
        Args:
            name: Configuration name
            
        Returns:
            TestConfiguration object or None if not found
        """
        for config in self.configurations.values():
            if config.name == name:
                return config
        return None
    
    def clone_configuration(self, config_id: str, new_name: str, 
                          new_description: str = "") -> TestConfiguration:
        """
        Clone an existing configuration.
        
        Args:
            config_id: Configuration identifier to clone
            new_name: Name for the cloned configuration
            new_description: Description for the cloned configuration
            
        Returns:
            Cloned TestConfiguration object
            
        Raises:
            ValueError: If source configuration not found
        """
        if config_id not in self.configurations:
            raise ValueError(f"Configuration not found: {config_id}")
        
        source_config = self.configurations[config_id]
        cloned_config = source_config.clone(new_name, new_description)
        
        return self.save_configuration(cloned_config)













