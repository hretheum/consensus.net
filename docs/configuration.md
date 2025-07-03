# Configuration System Documentation

The ConsensusNet application uses a flexible configuration system that supports loading settings from multiple sources.

## Configuration Sources

The configuration system loads settings in the following order of precedence (highest to lowest):

1. **Environment Variables** (highest precedence)
2. **Configuration Files** (YAML or JSON)  
3. **Default Values** (lowest precedence)

## Configuration Files

### Supported Formats

- **YAML** (.yaml, .yml)
- **JSON** (.json)

### File Discovery

The system automatically searches for configuration files in the following order:

1. `config.yaml`
2. `config.yml`
3. `consensusnet.yaml`
4. `consensusnet.yml`
5. `config.json`
6. `consensusnet.json`

You can also specify a specific configuration file when loading.

### Sample Configuration Files

#### YAML Configuration (config.yaml)
```yaml
# Application settings
app_name: "ConsensusNet"
version: "0.1.0"
environment: "development"
debug: true

# API settings
api_host: "0.0.0.0"
api_port: 8000
api_prefix: "/api"
cors_origins:
  - "*"

# Agent configuration
agent:
  agent_id: "default_agent"
  domain_expertise:
    - "general"
    - "science"
  primary_model: "gpt-4o-mini"
  secondary_model: "claude-3-haiku"
  fallback_model: "ollama/llama3.2"
  max_tokens: 2000
  temperature: 0.1
  confidence_threshold: 0.7
  evidence_sources:
    - "wikipedia"
    - "scientific_journals"
  max_verification_time: 30
```

#### JSON Configuration (config.json)
```json
{
  "app_name": "ConsensusNet",
  "version": "0.1.0",
  "environment": "production",
  "debug": false,
  "api_host": "0.0.0.0",
  "api_port": 8000,
  "agent": {
    "agent_id": "production_agent",
    "confidence_threshold": 0.8,
    "primary_model": "gpt-4o-mini"
  }
}
```

## Environment Variables

Environment variables can override any configuration setting. Use the prefix `CONSENSUSNET_` followed by the setting name in uppercase.

### Examples

```bash
# Override the environment setting
export CONSENSUSNET_ENVIRONMENT=production

# Override API port
export CONSENSUSNET_API_PORT=9000

# Override debug mode
export CONSENSUSNET_DEBUG=false

# Override CORS origins (JSON format)
export CONSENSUSNET_CORS_ORIGINS='["https://myapp.com"]'

# API keys (special handling)
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key
```

## Configuration Settings

### Application Settings

- `app_name`: Application name (default: "ConsensusNet")
- `version`: Application version (default: "0.1.0")
- `environment`: Environment name (default: "development")
- `debug`: Debug mode (default: false)

### API Settings

- `api_host`: Host to bind to (default: "0.0.0.0")
- `api_port`: Port to bind to (default: 8000)
- `api_prefix`: API prefix (default: "/api")
- `cors_origins`: Allowed CORS origins (default: ["*"])

### Agent Settings

- `agent_pool_size`: Number of agents in pool (default: 5)
- `max_verification_time`: Max verification time in seconds (default: 30)

### Agent Configuration

The `agent` section configures the default agent behavior:

- `agent_id`: Agent identifier
- `domain_expertise`: List of expertise domains
- `primary_model`: Primary LLM model
- `secondary_model`: Secondary LLM model  
- `fallback_model`: Fallback LLM model
- `max_tokens`: Maximum tokens per request
- `temperature`: LLM temperature setting
- `confidence_threshold`: Minimum confidence for verification
- `evidence_sources`: List of evidence sources
- `max_verification_time`: Maximum time for verification
- `detailed_reasoning`: Include detailed reasoning in output
- `include_uncertainty`: Include uncertainty information

### Database Settings (Future Use)

- `database_url`: Database connection URL
- `redis_url`: Redis connection URL

### Logging Settings

- `log_level`: Logging level (default: "INFO")
- `log_format`: Log message format

## Usage Examples

### Loading Configuration in Code

```python
from src.config import get_config

# Get current configuration
config = get_config()

# Access configuration values
print(f"App: {config.app_name}")
print(f"Environment: {config.environment}")
print(f"Agent ID: {config.default_agent_config.agent_id}")

# Reload configuration from sources
from src.config import reload_config
config = reload_config()
```

### Setting Custom Configuration Directory

```python
from src.config import set_config_dir

# Set custom config directory
set_config_dir("/path/to/config")

# Configuration will now be loaded from the specified directory
config = get_config()
```

### Using Different Configuration Files

```python
from src.config import ConfigLoader

loader = ConfigLoader("/path/to/config")
config = loader.load_config("custom-config.yaml")
```

## API Endpoints

The application provides endpoints to inspect the current configuration:

- `GET /api/config` - Get current configuration information (non-sensitive)
- `GET /api/health` - Health check including configuration status

## Security Notes

- API keys are loaded from environment variables only
- Sensitive configuration values are not exposed via API endpoints
- Configuration files should not contain API keys or secrets
- Use environment variables for sensitive configuration in production