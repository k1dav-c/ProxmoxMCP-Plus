"""
Configuration loading utilities for the Proxmox MCP server.

This module handles loading and validation of server configuration:
- Environment variable based configuration
- JSON configuration file fallback
- Configuration validation using Pydantic models
- Error handling for invalid configurations

The module ensures that all required configuration is present
and valid before the server starts operation.
"""
import json
import os
from typing import Optional
from .models import Config, ProxmoxConfig, AuthConfig, LoggingConfig, MCPConfig


def _load_from_env() -> Config:
    """Load configuration from environment variables.

    Environment Variables:
        PROXMOX_HOST: Proxmox host address (required)
        PROXMOX_PORT: API port (default: 8006)
        PROXMOX_VERIFY_SSL: SSL verification (default: false)
        PROXMOX_SERVICE: Service type (default: PVE)
        PROXMOX_USER: Username with realm (required)
        PROXMOX_TOKEN_NAME: API token name (required)
        PROXMOX_TOKEN_VALUE: API token value (required)
        LOG_LEVEL: Log level (default: INFO)
        LOG_FILE: Log file path (optional)

    Returns:
        Config object

    Raises:
        ValueError: If required environment variables are missing
    """
    host = os.getenv("PROXMOX_HOST")
    user = os.getenv("PROXMOX_USER")
    token_name = os.getenv("PROXMOX_TOKEN_NAME")
    token_value = os.getenv("PROXMOX_TOKEN_VALUE")

    missing = []
    if not host:
        missing.append("PROXMOX_HOST")
    if not user:
        missing.append("PROXMOX_USER")
    if not token_name:
        missing.append("PROXMOX_TOKEN_NAME")
    if not token_value:
        missing.append("PROXMOX_TOKEN_VALUE")
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    verify_ssl_str = os.getenv("PROXMOX_VERIFY_SSL", "false").lower()
    verify_ssl = verify_ssl_str in ("true", "1", "yes")

    return Config(
        proxmox=ProxmoxConfig(
            host=host,
            port=int(os.getenv("PROXMOX_PORT", "8006")),
            verify_ssl=verify_ssl,
            service=os.getenv("PROXMOX_SERVICE", "PVE"),
        ),
        auth=AuthConfig(
            user=user,
            token_name=token_name,
            token_value=token_value,
        ),
        logging=LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=os.getenv("LOG_FILE"),
        ),
        mcp=MCPConfig(
            transport="SSE",
        ),
    )


def load_config(config_path: Optional[str] = None) -> Config:
    """Load and validate configuration.

    If config_path is provided, loads from JSON file (backward compatible).
    Otherwise, loads from environment variables.

    Args:
        config_path: Optional path to a JSON configuration file

    Returns:
        Config object containing validated configuration

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    if config_path:
        try:
            with open(config_path) as f:
                config_data = json.load(f)
                if not config_data.get('proxmox', {}).get('host'):
                    raise ValueError("Proxmox host cannot be empty")
                return Config(**config_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load config: {e}")

    return _load_from_env()
