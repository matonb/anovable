"""Configuration management for Anovable."""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .exceptions import AnovaError


class AnovaConfig:
    """Configuration manager for Anova library."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file. If None, looks for default locations.
        """
        self.config_path = self._find_config_file(config_path)
        self._config: Dict[str, Any] = {}
        self.load_config()

    def _find_config_file(self, config_path: Optional[str] = None) -> Optional[str]:
        """Find configuration file in default locations."""
        if config_path:
            return config_path

        # Check default locations
        possible_paths = [
            "anovable.yaml",
            "~/.config/anovable/config.yaml",
            "~/.anovable.yaml",
            "/etc/anovable/config.yaml",
        ]

        for path in possible_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                return str(expanded_path)

        return None

    def load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_path:
            # No config file found, use defaults
            self._config = self._get_default_config()
            return

        try:
            with open(self.config_path) as f:
                self._config = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError) as e:
            raise AnovaError(
                f"Failed to load configuration from {self.config_path}: {e}"
            ) from e

        # Merge with defaults
        default_config = self._get_default_config()
        self._config = self._merge_configs(default_config, self._config)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "anova": {
                "mac_address": None,
                "connection": {
                    "timeout": 5.0,
                    "retry_attempts": 3,
                },
                "temperature": {
                    "default_unit": "celsius",
                },
                "logging": {
                    "level": "INFO",
                },
            }
        }

    def _merge_configs(
        self, default: Dict[str, Any], user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge user config with defaults."""
        result = default.copy()
        for key, value in user.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    @property
    def mac_address(self) -> Optional[str]:
        """Get MAC address from configuration."""
        result = self._config.get("anova", {}).get("mac_address")
        return result if isinstance(result, (str, type(None))) else None

    @property
    def timeout(self) -> float:
        """Get connection timeout."""
        result = self._config.get("anova", {}).get("connection", {}).get("timeout", 5.0)
        return float(result) if result is not None else 5.0

    @property
    def retry_attempts(self) -> int:
        """Get retry attempts."""
        result = (
            self._config.get("anova", {}).get("connection", {}).get("retry_attempts", 3)
        )
        return int(result) if result is not None else 3

    @property
    def default_unit(self) -> str:
        """Get default temperature unit."""
        result = (
            self._config.get("anova", {})
            .get("temperature", {})
            .get("default_unit", "celsius")
        )
        return str(result) if result is not None else "celsius"

    @property
    def log_level(self) -> str:
        """Get logging level."""
        result = self._config.get("anova", {}).get("logging", {}).get("level", "INFO")
        return str(result) if result is not None else "INFO"

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
