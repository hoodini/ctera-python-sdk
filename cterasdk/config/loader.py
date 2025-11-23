"""Configuration loader with multiple format support."""
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger('cterasdk.config')


class ConfigLoader:
    """Loads configuration from various formats."""
    
    @staticmethod
    def load_json(path: Path) -> Dict[str, Any]:
        """Load JSON configuration."""
        with open(path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def load_yaml(path: Path) -> Dict[str, Any]:
        """Load YAML configuration."""
        try:
            import yaml
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except ImportError:
            logger.error("PyYAML not installed, cannot load YAML files")
            return {}
    
    @staticmethod
    def load_env() -> Dict[str, Any]:
        """Load configuration from environment variables."""
        import os
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith('CTERA_'):
                config_key = key[6:].lower().replace('_', '.')
                config[config_key] = value
        
        return config
    
    @staticmethod
    def auto_load(path: Path) -> Dict[str, Any]:
        """Auto-detect format and load."""
        if path.suffix == '.json':
            return ConfigLoader.load_json(path)
        elif path.suffix in ['.yml', '.yaml']:
            return ConfigLoader.load_yaml(path)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")

