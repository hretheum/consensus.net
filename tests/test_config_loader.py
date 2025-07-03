"""
Tests for the configuration loading system.
"""

import json
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.config_loader import (
    AppConfig,
    ConfigLoader,
    get_config,
    reload_config,
    set_config_dir
)
from src.agents.agent_models import AgentConfig


class TestAppConfig:
    """Test cases for AppConfig class."""
    
    def test_default_app_config(self):
        """Test default AppConfig creation."""
        config = AppConfig()
        
        assert config.app_name == "ConsensusNet"
        assert config.version == "0.1.0"
        assert config.environment == "development"
        assert config.debug is False
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.api_prefix == "/api"
        assert config.cors_origins == ["*"]
        assert config.default_agent_config is None
    
    def test_app_config_from_dict_basic(self):
        """Test creating AppConfig from basic dictionary."""
        config_data = {
            "app_name": "TestApp",
            "version": "1.0.0",
            "environment": "test",
            "debug": True,
            "api_port": 9000
        }
        
        config = AppConfig.from_dict(config_data)
        
        assert config.app_name == "TestApp"
        assert config.version == "1.0.0"
        assert config.environment == "test"
        assert config.debug is True
        assert config.api_port == 9000
        # Defaults should remain
        assert config.api_host == "0.0.0.0"
        assert config.api_prefix == "/api"
    
    def test_app_config_from_dict_with_agent(self):
        """Test creating AppConfig with agent configuration."""
        config_data = {
            "app_name": "TestApp",
            "agent": {
                "agent_id": "test_agent",
                "domain_expertise": ["science", "technology"],
                "primary_model": "gpt-4",
                "temperature": 0.2,
                "confidence_threshold": 0.8
            }
        }
        
        config = AppConfig.from_dict(config_data)
        
        assert config.app_name == "TestApp"
        assert config.default_agent_config is not None
        assert config.default_agent_config.agent_id == "test_agent"
        assert config.default_agent_config.domain_expertise == ["science", "technology"]
        assert config.default_agent_config.primary_model == "gpt-4"
        assert config.default_agent_config.temperature == 0.2
        assert config.default_agent_config.confidence_threshold == 0.8
    
    def test_app_config_filters_invalid_keys(self):
        """Test that AppConfig filters out invalid keys."""
        config_data = {
            "app_name": "TestApp",
            "invalid_key": "should_be_ignored",
            "another_invalid": 123,
            "api_port": 9000
        }
        
        config = AppConfig.from_dict(config_data)
        
        assert config.app_name == "TestApp"
        assert config.api_port == 9000
        # Invalid keys should not cause errors
        assert not hasattr(config, 'invalid_key')
        assert not hasattr(config, 'another_invalid')


class TestConfigLoader:
    """Test cases for ConfigLoader class."""
    
    def test_config_loader_initialization(self):
        """Test ConfigLoader initialization."""
        loader = ConfigLoader()
        assert loader.config_dir == Path.cwd()
        
        test_dir = Path("/tmp")
        loader = ConfigLoader(test_dir)
        assert loader.config_dir == test_dir
    
    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        yaml_content = {
            "app_name": "YamlApp",
            "version": "1.0.0",
            "debug": True,
            "agent": {
                "agent_id": "yaml_agent",
                "temperature": 0.3
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader()
            config_data = loader.load_from_file(temp_path)
            
            assert config_data["app_name"] == "YamlApp"
            assert config_data["version"] == "1.0.0"
            assert config_data["debug"] is True
            assert config_data["agent"]["agent_id"] == "yaml_agent"
            assert config_data["agent"]["temperature"] == 0.3
        finally:
            os.unlink(temp_path)
    
    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        json_content = {
            "app_name": "JsonApp",
            "version": "2.0.0",
            "debug": False,
            "api_port": 9000
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader()
            config_data = loader.load_from_file(temp_path)
            
            assert config_data["app_name"] == "JsonApp"
            assert config_data["version"] == "2.0.0"
            assert config_data["debug"] is False
            assert config_data["api_port"] == 9000
        finally:
            os.unlink(temp_path)
    
    def test_load_from_file_not_found(self):
        """Test loading from non-existent file."""
        loader = ConfigLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_from_file("/non/existent/file.yaml")
    
    def test_load_from_file_unsupported_format(self):
        """Test loading from unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            temp_path = f.name
        
        try:
            loader = ConfigLoader()
            with pytest.raises(ValueError, match="Unsupported file format"):
                loader.load_from_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_from_file_invalid_yaml(self):
        """Test loading from invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [\n")
            temp_path = f.name
        
        try:
            loader = ConfigLoader()
            with pytest.raises(ValueError, match="Invalid configuration file format"):
                loader.load_from_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_from_file_invalid_json(self):
        """Test loading from invalid JSON file.""" 
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json,}')
            temp_path = f.name
        
        try:
            loader = ConfigLoader()
            with pytest.raises(ValueError, match="Invalid configuration file format"):
                loader.load_from_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "CONSENSUSNET_APP_NAME": "EnvApp",
            "CONSENSUSNET_API_PORT": "9999",
            "CONSENSUSNET_DEBUG": "true",
            "CONSENSUSNET_CORS_ORIGINS": '["http://localhost"]',
            "OTHER_VAR": "should_be_ignored"
        }
        
        with patch.dict(os.environ, env_vars):
            loader = ConfigLoader()
            config_data = loader.load_from_env()
            
            assert config_data["app_name"] == "EnvApp"
            assert config_data["api_port"] == 9999  # JSON parsed as int
            assert config_data["debug"] is True  # JSON parsed as boolean
            assert config_data["cors_origins"] == ["http://localhost"]
            assert "other_var" not in config_data
    
    def test_load_from_env_custom_prefix(self):
        """Test loading from environment with custom prefix."""
        env_vars = {
            "MYAPP_APP_NAME": "CustomApp",
            "MYAPP_VERSION": "3.0.0",
            "CONSENSUSNET_IGNORED": "should_be_ignored"
        }
        
        with patch.dict(os.environ, env_vars):
            loader = ConfigLoader()
            config_data = loader.load_from_env("MYAPP_")
            
            assert config_data["app_name"] == "CustomApp"
            assert config_data["version"] == "3.0.0"
            assert "ignored" not in config_data
    
    def test_find_config_file_specific(self):
        """Test finding a specific configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "myconfig.yaml"
            config_path.write_text("app_name: test")
            
            loader = ConfigLoader(temp_dir)
            found_path = loader.find_config_file("myconfig.yaml")
            
            assert found_path == config_path
    
    def test_find_config_file_common_names(self):
        """Test finding configuration files with common names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text("app_name: test")
            
            loader = ConfigLoader(temp_dir)
            found_path = loader.find_config_file()
            
            assert found_path == config_path
    
    def test_find_config_file_not_found(self):
        """Test finding configuration file when none exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = ConfigLoader(temp_dir)
            found_path = loader.find_config_file("nonexistent.yaml")
            
            assert found_path is None
            
            found_path = loader.find_config_file()
            assert found_path is None
    
    def test_load_config_integration(self):
        """Test full configuration loading integration."""
        yaml_content = {
            "app_name": "IntegrationTest",
            "version": "1.0.0",
            "debug": False,
            "agent": {
                "agent_id": "integration_agent",
                "confidence_threshold": 0.9
            }
        }
        
        env_vars = {
            "CONSENSUSNET_DEBUG": "true",
            "CONSENSUSNET_API_PORT": "9999",
            "OPENAI_API_KEY": "test_key_123"
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(yaml_content, f)
            
            with patch.dict(os.environ, env_vars):
                loader = ConfigLoader(temp_dir)
                config = loader.load_config()
                
                # File values
                assert config.app_name == "IntegrationTest"
                assert config.version == "1.0.0"
                
                # Environment override
                assert config.debug is True  # Overridden by env
                assert config.api_port == 9999  # From env (parsed as int)
                
                # API key from env
                assert config.openai_api_key == "test_key_123"
                
                # Agent config from file
                assert config.default_agent_config is not None
                assert config.default_agent_config.agent_id == "integration_agent"
                assert config.default_agent_config.confidence_threshold == 0.9
    
    def test_config_caching(self):
        """Test that configuration is cached."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text("app_name: CacheTest")
            
            loader = ConfigLoader(temp_dir)
            config1 = loader.get_config()
            config2 = loader.get_config()
            
            # Should be the same instance (cached)
            assert config1 is config2
            
            # Force reload should give new instance
            config3 = loader.get_config(reload=True)
            assert config3 is not config1


class TestGlobalFunctions:
    """Test global configuration functions."""
    
    def test_get_config_function(self):
        """Test global get_config function."""
        config = get_config()
        assert isinstance(config, AppConfig)
    
    def test_reload_config_function(self):
        """Test global reload_config function."""
        config = reload_config()
        assert isinstance(config, AppConfig)
    
    def test_set_config_dir_function(self):
        """Test global set_config_dir function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            set_config_dir(temp_dir)
            # This should not raise an error
            config = get_config()
            assert isinstance(config, AppConfig)


class TestConfigWithRealFiles:
    """Test configuration loading with the actual config files in the repo."""
    
    def test_load_sample_yaml_config(self):
        """Test loading the sample YAML configuration file."""
        # Assume we're running from the repo root
        config_path = Path("config.yaml")
        
        if config_path.exists():
            loader = ConfigLoader()
            config = loader.load_config(config_path)
            
            assert config.app_name == "ConsensusNet"
            assert config.version == "0.1.0"
            assert config.environment == "development"
            assert config.debug is True
            assert config.default_agent_config is not None
            assert config.default_agent_config.agent_id == "default_agent"
    
    def test_load_sample_json_config(self):
        """Test loading the sample JSON configuration file."""
        # Assume we're running from the repo root
        config_path = Path("config.production.json")
        
        if config_path.exists():
            loader = ConfigLoader()
            config = loader.load_config(config_path)
            
            assert config.app_name == "ConsensusNet"
            assert config.version == "0.1.0"
            assert config.environment == "production"
            assert config.debug is False
            assert config.default_agent_config is not None
            assert config.default_agent_config.agent_id == "production_agent"