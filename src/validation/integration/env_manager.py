"""
Environment variable management for external database access

This service manages environment variables and configuration for connecting
to external databases in separate Kubernetes namespaces.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration from environment variables"""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    connection_timeout: int = 30
    pool_size: int = 10
    max_overflow: int = 20


class EnvironmentManager:
    """
    Manages environment variables and configuration for external database access.
    """
    
    def __init__(self):
        self.required_vars = [
            'VALIDATION_DB_HOST',
            'VALIDATION_DB_PORT',
            'VALIDATION_DB_NAME',
            'VALIDATION_DB_USER',
            'VALIDATION_DB_PASSWORD'
        ]
        
        self.optional_vars = {
            'VALIDATION_DB_SSL_MODE': 'prefer',
            'VALIDATION_DB_CONNECTION_TIMEOUT': '30',
            'VALIDATION_DB_POOL_SIZE': '10',
            'VALIDATION_DB_MAX_OVERFLOW': '20'
        }
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate that all required environment variables are set.
        
        Returns:
            Dictionary with validation results
        """
        missing_vars = []
        invalid_vars = []
        
        # Check required variables
        for var in self.required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        # Check optional variables with validation
        if os.getenv('VALIDATION_DB_PORT'):
            try:
                port = int(os.getenv('VALIDATION_DB_PORT'))
                if not (1 <= port <= 65535):
                    invalid_vars.append(f"VALIDATION_DB_PORT: {port} (must be 1-65535)")
            except ValueError:
                invalid_vars.append(f"VALIDATION_DB_PORT: {os.getenv('VALIDATION_DB_PORT')} (must be integer)")
        
        if os.getenv('VALIDATION_DB_CONNECTION_TIMEOUT'):
            try:
                timeout = int(os.getenv('VALIDATION_DB_CONNECTION_TIMEOUT'))
                if timeout <= 0:
                    invalid_vars.append(f"VALIDATION_DB_CONNECTION_TIMEOUT: {timeout} (must be positive)")
            except ValueError:
                invalid_vars.append(f"VALIDATION_DB_CONNECTION_TIMEOUT: {os.getenv('VALIDATION_DB_CONNECTION_TIMEOUT')} (must be integer)")
        
        if os.getenv('VALIDATION_DB_POOL_SIZE'):
            try:
                pool_size = int(os.getenv('VALIDATION_DB_POOL_SIZE'))
                if pool_size <= 0:
                    invalid_vars.append(f"VALIDATION_DB_POOL_SIZE: {pool_size} (must be positive)")
            except ValueError:
                invalid_vars.append(f"VALIDATION_DB_POOL_SIZE: {os.getenv('VALIDATION_DB_POOL_SIZE')} (must be integer)")
        
        if os.getenv('VALIDATION_DB_MAX_OVERFLOW'):
            try:
                max_overflow = int(os.getenv('VALIDATION_DB_MAX_OVERFLOW'))
                if max_overflow < 0:
                    invalid_vars.append(f"VALIDATION_DB_MAX_OVERFLOW: {max_overflow} (must be non-negative)")
            except ValueError:
                invalid_vars.append(f"VALIDATION_DB_MAX_OVERFLOW: {os.getenv('VALIDATION_DB_MAX_OVERFLOW')} (must be integer)")
        
        is_valid = len(missing_vars) == 0 and len(invalid_vars) == 0
        
        return {
            "valid": is_valid,
            "missing_variables": missing_vars,
            "invalid_variables": invalid_vars,
            "environment_ready": is_valid
        }
    
    def get_database_config(self) -> DatabaseConfig:
        """
        Get database configuration from environment variables.
        
        Returns:
            DatabaseConfig object
            
        Raises:
            ValueError: If required environment variables are missing
        """
        validation = self.validate_environment()
        
        if not validation["valid"]:
            error_msg = "Invalid environment configuration:\n"
            if validation["missing_variables"]:
                error_msg += f"Missing variables: {', '.join(validation['missing_variables'])}\n"
            if validation["invalid_variables"]:
                error_msg += f"Invalid variables: {'; '.join(validation['invalid_variables'])}"
            raise ValueError(error_msg)
        
        return DatabaseConfig(
            host=os.getenv('VALIDATION_DB_HOST'),
            port=int(os.getenv('VALIDATION_DB_PORT')),
            database=os.getenv('VALIDATION_DB_NAME'),
            username=os.getenv('VALIDATION_DB_USER'),
            password=os.getenv('VALIDATION_DB_PASSWORD'),
            ssl_mode=os.getenv('VALIDATION_DB_SSL_MODE', 'prefer'),
            connection_timeout=int(os.getenv('VALIDATION_DB_CONNECTION_TIMEOUT', '30')),
            pool_size=int(os.getenv('VALIDATION_DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('VALIDATION_DB_MAX_OVERFLOW', '20'))
        )
    
    def get_connection_string(self) -> str:
        """
        Get database connection string from environment variables.
        
        Returns:
            Connection string for database
        
        Raises:
            ValueError: If required environment variables are missing
        """
        config = self.get_database_config()
        
        # Build connection string
        connection_string = (
            f"postgresql+asyncpg://{config.username}:{config.password}"
            f"@{config.host}:{config.port}/{config.database}"
        )
        
        # Add SSL mode if specified
        if config.ssl_mode and config.ssl_mode != 'prefer':
            connection_string += f"?sslmode={config.ssl_mode}"
        
        return connection_string
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """
        Get summary of environment configuration.
        
        Returns:
            Dictionary with environment summary
        """
        validation = self.validate_environment()
        
        # Get all environment variables (mask sensitive ones)
        env_vars = {}
        for var in self.required_vars + list(self.optional_vars.keys()):
            value = os.getenv(var)
            if value:
                # Mask password
                if 'PASSWORD' in var:
                    env_vars[var] = '*' * len(value)
                else:
                    env_vars[var] = value
            else:
                env_vars[var] = None
        
        return {
            "valid": validation["valid"],
            "environment_variables": env_vars,
            "missing_variables": validation["missing_variables"],
            "invalid_variables": validation["invalid_variables"],
            "ready_for_database_connection": validation["valid"]
        }
    
    def set_default_values(self) -> None:
        """
        Set default values for optional environment variables if not already set.
        """
        for var, default_value in self.optional_vars.items():
            if not os.getenv(var):
                os.environ[var] = default_value
                logger.info(f"Set default value for {var}: {default_value}")
    
    def load_from_file(self, file_path: str) -> None:
        """
        Load environment variables from a file.
        
        Args:
            file_path: Path to environment file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        import os.path
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Environment file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value format
                    if '=' not in line:
                        raise ValueError(f"Invalid format at line {line_num}: {line}")
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    os.environ[key] = value
                    logger.debug(f"Loaded environment variable: {key}")
            
            logger.info(f"Loaded environment variables from {file_path}")
            
        except Exception as e:
            raise ValueError(f"Failed to load environment file {file_path}: {e}")
    
    def export_to_file(self, file_path: str, include_sensitive: bool = False) -> None:
        """
        Export current environment variables to a file.
        
        Args:
            file_path: Path to output file
            include_sensitive: Whether to include sensitive variables (passwords)
        """
        try:
            with open(file_path, 'w') as f:
                f.write("# Validation Framework Environment Variables\n")
                f.write(f"# Generated at: {os.getenv('TZ', 'UTC')}\n\n")
                
                # Write required variables
                f.write("# Required Variables\n")
                for var in self.required_vars:
                    value = os.getenv(var)
                    if value and ('PASSWORD' not in var or include_sensitive):
                        if 'PASSWORD' in var and not include_sensitive:
                            f.write(f"{var}=<hidden>\n")
                        else:
                            f.write(f"{var}={value}\n")
                    else:
                        f.write(f"{var}=\n")
                
                # Write optional variables
                f.write("\n# Optional Variables\n")
                for var in self.optional_vars.keys():
                    value = os.getenv(var)
                    if value:
                        f.write(f"{var}={value}\n")
                    else:
                        f.write(f"# {var}=<default>\n")
            
            logger.info(f"Exported environment variables to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export environment variables: {e}")
            raise

