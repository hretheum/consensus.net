"""
Configuration loading system for ConsensusNet.

Supports loading configuration from YAML, JSON, and environment variables.
Provides a centralized way to manage application settings.
"""

import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from ..agents.agent_models import AgentConfig


@dataclass
class AppConfig:
    """
    Main application configuration.
    
    Contains all configuration settings for the ConsensusNet application,
    including agent settings, API configuration, and system parameters.
    """
    # Application settings
    app_name: str = "ConsensusNet"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api"
    cors_origins: list = field(default_factory=lambda: ["*"])
    
    # Agent settings
    default_agent_config: Optional[AgentConfig] = None
    agent_pool_size: int = 5
    max_verification_time: int = 30
    
    # Database settings (for future use)
    database_url: str = "postgresql://localhost/consensusnet"
    redis_url: str = "redis://localhost:6379"
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # External service settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AppConfig':
        """
        Create AppConfig from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            AppConfig instance with values from the dictionary
        """
        # Extract agent configuration if present
        agent_config_data = config_dict.get('agent', {})
        default_agent_config = None
        
        if agent_config_data:
            default_agent_config = AgentConfig(
                agent_id=agent_config_data.get('agent_id', 'default'),
                domain_expertise=agent_config_data.get('domain_expertise', []),
                primary_model=agent_config_data.get('primary_model', 'gpt-4o-mini'),
                secondary_model=agent_config_data.get('secondary_model', 'claude-3-haiku'),
                fallback_model=agent_config_data.get('fallback_model', 'ollama/llama3.2'),
                max_tokens=agent_config_data.get('max_tokens', 2000),
                temperature=agent_config_data.get('temperature', 0.1),
                confidence_threshold=agent_config_data.get('confidence_threshold', 0.7),
                evidence_sources=agent_config_data.get('evidence_sources', []),
                max_verification_time=agent_config_data.get('max_verification_time', 30),
                max_history_items=agent_config_data.get('max_history_items', 100),
                memory_decay_factor=agent_config_data.get('memory_decay_factor', 0.95),
                detailed_reasoning=agent_config_data.get('detailed_reasoning', True),
                include_uncertainty=agent_config_data.get('include_uncertainty', True),
                evidence_limit=agent_config_data.get('evidence_limit', 10)
            )
        
        # Create AppConfig with filtered dictionary (removing non-matching keys)
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
        
        return cls(
            default_agent_config=default_agent_config,
            **filtered_dict
        )


class ConfigLoader:
    """
    Configuration loader that supports multiple formats and sources.
    
    Can load configuration from:
    - YAML files
    - JSON files  
    - Environment variables
    - Default values
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory to search for configuration files.
                       Defaults to current working directory.
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd()
        self._config_cache: Optional[AppConfig] = None
    
    def load_from_file(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a file.
        
        Supports YAML and JSON formats based on file extension.
        
        Args:
            filepath: Path to the configuration file
            
        Returns:
            Dictionary containing configuration data
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the file format is not supported or invalid
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif filepath.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {filepath.suffix}")
                    
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid configuration file format: {e}")
    
    def load_from_env(self, prefix: str = "CONSENSUSNET_") -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variables
            
        Returns:
            Dictionary containing configuration from environment
        """
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix):].lower()
                
                # Try to parse as JSON, fall back to string
                try:
                    config[config_key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    config[config_key] = value
        
        return config
    
    def find_config_file(self, filename: Optional[str] = None) -> Optional[Path]:
        """
        Find a configuration file in the config directory.
        
        Args:
            filename: Specific filename to look for. If None, searches for
                     common configuration file names.
                     
        Returns:
            Path to the configuration file if found, None otherwise
        """
        if filename:
            candidate = self.config_dir / filename
            return candidate if candidate.exists() else None
        
        # Search for common configuration file names
        candidates = [
            "config.yaml",
            "config.yml", 
            "consensusnet.yaml",
            "consensusnet.yml",
            "config.json",
            "consensusnet.json"
        ]
        
        for candidate_name in candidates:
            candidate = self.config_dir / candidate_name
            if candidate.exists():
                return candidate
        
        return None
    
    def load_config(self, 
                   config_file: Optional[Union[str, Path]] = None,
                   use_env: bool = True) -> AppConfig:
        """
        Load complete application configuration.
        
        Loads configuration from multiple sources in order of precedence:
        1. Environment variables (highest precedence)
        2. Configuration file
        3. Default values (lowest precedence)
        
        Args:
            config_file: Path to configuration file. If None, searches for
                        common config file names in the config directory.
            use_env: Whether to load configuration from environment variables
            
        Returns:
            AppConfig instance with merged configuration
        """
        # Start with default configuration
        config_data = {}
        
        # Load from file if available
        if config_file:
            file_path = Path(config_file)
        else:
            file_path = self.find_config_file()
        
        if file_path and file_path.exists():
            try:
                file_config = self.load_from_file(file_path)
                config_data.update(file_config)
            except (FileNotFoundError, ValueError) as e:
                print(f"Warning: Could not load config file {file_path}: {e}")
        
        # Override with environment variables
        if use_env:
            env_config = self.load_from_env()
            config_data.update(env_config)
        
        # Special handling for API keys from environment
        config_data['openai_api_key'] = os.getenv('OPENAI_API_KEY')
        config_data['anthropic_api_key'] = os.getenv('ANTHROPIC_API_KEY')
        
        return AppConfig.from_dict(config_data)
    
    def get_config(self, reload: bool = False) -> AppConfig:
        """
        Get the application configuration, using cache if available.
        
        Args:
            reload: Whether to reload the configuration from sources
            
        Returns:
            AppConfig instance
        """
        if self._config_cache is None or reload:
            self._config_cache = self.load_config()
        
        return self._config_cache


# Global configuration loader instance
_config_loader = ConfigLoader()


def get_config() -> AppConfig:
    """
    Get the current application configuration.
    
    Returns:
        AppConfig instance with current configuration
    """
    return _config_loader.get_config()


def reload_config() -> AppConfig:
    """
    Reload the application configuration from sources.
    
    Returns:
        AppConfig instance with reloaded configuration
    """
    return _config_loader.get_config(reload=True)


def set_config_dir(config_dir: Union[str, Path]) -> None:
    """
    Set the directory to search for configuration files.
    
    Args:
        config_dir: Path to the configuration directory
    """
    global _config_loader
    _config_loader = ConfigLoader(config_dir)