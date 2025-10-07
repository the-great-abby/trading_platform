"""
Configuration management API endpoints

This module provides REST API endpoints for managing test configurations
and validation settings in the validation framework.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from ..config.config_manager import ConfigManager
from ..models.test_configuration import TestConfiguration
from ..integration import get_validation_logger

logger = get_validation_logger(__name__)

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])


class ConfigurationRequest(BaseModel):
    """Request model for configuration operations"""
    config_name: str
    config_data: Dict[str, Any]
    description: Optional[str] = None


class ConfigurationResponse(BaseModel):
    """Response model for configuration operations"""
    success: bool
    message: str
    configuration: Optional[TestConfiguration] = None


class ConfigAPI:
    """
    API endpoints for configuration management operations.
    """
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    @router.post("/", response_model=ConfigurationResponse)
    async def create_configuration(self, request: ConfigurationRequest):
        """
        Create a new test configuration.
        
        Args:
            request: Configuration creation parameters
            
        Returns:
            Configuration creation response
        """
        try:
            logger.info(f"Creating configuration - Name: {request.config_name}")
            
            # Create configuration
            config = TestConfiguration(
                config_name=request.config_name,
                description=request.description,
                timeout_seconds=request.config_data.get("timeout_seconds", 300),
                expected_metrics=request.config_data.get("expected_metrics", {}),
                tolerance_levels=request.config_data.get("tolerance_levels", {}),
                validation_rules=request.config_data.get("validation_rules", []),
                environment_variables=request.config_data.get("environment_variables", {}),
                resource_limits=request.config_data.get("resource_limits", {})
            )
            
            # Save configuration
            await self.config_manager.save_configuration(config)
            
            logger.info(f"Configuration created - Name: {request.config_name}")
            
            return ConfigurationResponse(
                success=True,
                message=f"Configuration '{request.config_name}' created successfully",
                configuration=config
            )
            
        except Exception as e:
            logger.error(f"Failed to create configuration {request.config_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create configuration: {str(e)}")
    
    @router.get("/", response_model=List[TestConfiguration])
    async def list_configurations(
        self,
        limit: int = Query(20, description="Maximum number of configurations to return"),
        offset: int = Query(0, description="Number of configurations to skip")
    ):
        """
        List all available test configurations.
        
        Args:
            limit: Maximum number of configurations to return
            offset: Number of configurations to skip for pagination
            
        Returns:
            List of configurations
        """
        try:
            logger.info("Listing configurations")
            
            configurations = await self.config_manager.list_configurations()
            
            # Apply pagination
            total_count = len(configurations)
            paginated_configs = configurations[offset:offset + limit]
            
            logger.info(f"Configurations listed - Total: {total_count}, Returned: {len(paginated_configs)}")
            
            return paginated_configs
            
        except Exception as e:
            logger.error(f"Failed to list configurations: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list configurations: {str(e)}")
    
    @router.get("/{config_id}", response_model=ConfigurationResponse)
    async def get_configuration(
        self,
        config_id: str = Path(..., description="Configuration identifier")
    ):
        """
        Get a specific test configuration.
        
        Args:
            config_id: Unique identifier for the configuration
            
        Returns:
            Configuration details
        """
        try:
            logger.info(f"Getting configuration - ID: {config_id}")
            
            configuration = await self.config_manager.get_configuration(config_id)
            
            if not configuration:
                raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
            
            logger.info(f"Configuration retrieved - ID: {config_id}")
            
            return ConfigurationResponse(
                success=True,
                message="Configuration retrieved successfully",
                configuration=configuration
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get configuration {config_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")
    
    @router.put("/{config_id}", response_model=ConfigurationResponse)
    async def update_configuration(
        self,
        config_id: str = Path(..., description="Configuration identifier"),
        request: ConfigurationRequest = None
    ):
        """
        Update an existing test configuration.
        
        Args:
            config_id: Unique identifier for the configuration
            request: Configuration update parameters
            
        Returns:
            Configuration update response
        """
        try:
            logger.info(f"Updating configuration - ID: {config_id}")
            
            # Get existing configuration
            existing_config = await self.config_manager.get_configuration(config_id)
            if not existing_config:
                raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
            
            # Update configuration
            updated_config = TestConfiguration(
                config_id=config_id,
                config_name=request.config_name,
                description=request.description,
                timeout_seconds=request.config_data.get("timeout_seconds", existing_config.timeout_seconds),
                expected_metrics=request.config_data.get("expected_metrics", existing_config.expected_metrics),
                tolerance_levels=request.config_data.get("tolerance_levels", existing_config.tolerance_levels),
                validation_rules=request.config_data.get("validation_rules", existing_config.validation_rules),
                environment_variables=request.config_data.get("environment_variables", existing_config.environment_variables),
                resource_limits=request.config_data.get("resource_limits", existing_config.resource_limits)
            )
            
            # Save updated configuration
            await self.config_manager.save_configuration(updated_config)
            
            logger.info(f"Configuration updated - ID: {config_id}")
            
            return ConfigurationResponse(
                success=True,
                message=f"Configuration '{config_id}' updated successfully",
                configuration=updated_config
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update configuration {config_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
    
    @router.delete("/{config_id}")
    async def delete_configuration(
        self,
        config_id: str = Path(..., description="Configuration identifier")
    ):
        """
        Delete a test configuration.
        
        Args:
            config_id: Unique identifier for the configuration
            
        Returns:
            Deletion confirmation
        """
        try:
            logger.info(f"Deleting configuration - ID: {config_id}")
            
            # Check if configuration exists
            existing_config = await self.config_manager.get_configuration(config_id)
            if not existing_config:
                raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
            
            # Delete configuration
            await self.config_manager.delete_configuration(config_id)
            
            logger.info(f"Configuration deleted - ID: {config_id}")
            
            return {
                "success": True,
                "message": f"Configuration '{config_id}' deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete configuration {config_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {str(e)}")
    
    @router.post("/{config_id}/validate")
    async def validate_configuration(
        self,
        config_id: str = Path(..., description="Configuration identifier")
    ):
        """
        Validate a test configuration.
        
        Args:
            config_id: Unique identifier for the configuration
            
        Returns:
            Validation results
        """
        try:
            logger.info(f"Validating configuration - ID: {config_id}")
            
            # Get configuration
            configuration = await self.config_manager.get_configuration(config_id)
            if not configuration:
                raise HTTPException(status_code=404, detail=f"Configuration {config_id} not found")
            
            # Validate configuration
            validation_results = await self.config_manager.validate_configuration(configuration)
            
            logger.info(f"Configuration validated - ID: {config_id}")
            
            return {
                "success": True,
                "validation_results": validation_results,
                "message": "Configuration validation completed"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to validate configuration {config_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to validate configuration: {str(e)}")
    
    @router.get("/templates/available")
    async def get_available_templates(self):
        """
        Get list of available configuration templates.
        
        Returns:
            Available configuration templates
        """
        try:
            logger.info("Getting available configuration templates")
            
            templates = [
                {
                    "template_id": "basic",
                    "name": "Basic Configuration",
                    "description": "Basic validation configuration with standard timeouts and tolerances",
                    "config_data": {
                        "timeout_seconds": 300,
                        "tolerance_levels": {
                            "total_return_pct": 0.01,
                            "sharpe_ratio": 0.1,
                            "max_drawdown_pct": 0.05
                        }
                    }
                },
                {
                    "template_id": "strict",
                    "name": "Strict Configuration",
                    "description": "Strict validation with tight tolerances",
                    "config_data": {
                        "timeout_seconds": 600,
                        "tolerance_levels": {
                            "total_return_pct": 0.001,
                            "sharpe_ratio": 0.01,
                            "max_drawdown_pct": 0.01
                        }
                    }
                },
                {
                    "template_id": "performance",
                    "name": "Performance Configuration",
                    "description": "Configuration optimized for performance testing",
                    "config_data": {
                        "timeout_seconds": 120,
                        "resource_limits": {
                            "max_memory_mb": 1024,
                            "max_cpu_percent": 80
                        }
                    }
                }
            ]
            
            logger.info(f"Configuration templates retrieved - Count: {len(templates)}")
            
            return {
                "success": True,
                "templates": templates,
                "message": "Configuration templates retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get configuration templates: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get configuration templates: {str(e)}")
    
    @router.post("/templates/{template_id}/create")
    async def create_from_template(
        self,
        template_id: str = Path(..., description="Template identifier"),
        config_name: str = Query(..., description="Name for the new configuration"),
        description: Optional[str] = Query(None, description="Description for the new configuration")
    ):
        """
        Create a configuration from a template.
        
        Args:
            template_id: Template identifier
            config_name: Name for the new configuration
            description: Optional description
            
        Returns:
            Configuration creation response
        """
        try:
            logger.info(f"Creating configuration from template - Template: {template_id}, Name: {config_name}")
            
            # Get available templates
            templates_response = await self.get_available_templates()
            templates = templates_response["templates"]
            
            # Find template
            template = next((t for t in templates if t["template_id"] == template_id), None)
            if not template:
                raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
            
            # Create configuration from template
            config_request = ConfigurationRequest(
                config_name=config_name,
                config_data=template["config_data"],
                description=description or template["description"]
            )
            
            response = await self.create_configuration(config_request)
            
            logger.info(f"Configuration created from template - Template: {template_id}, Name: {config_name}")
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create configuration from template {template_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create configuration from template: {str(e)}")


# Create router instance
config_api = ConfigAPI()











