"""Configuration manager with profile support."""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger('cterasdk.config')


class Profile:
    """Configuration profile."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value


class ConfigManager:
    """
    Manages SDK configuration with multiple profiles.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        :param Path config_dir: Configuration directory
        """
        self.config_dir = config_dir or Path.home() / '.ctera'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.profiles: Dict[str, Profile] = {}
        self.active_profile: Optional[Profile] = None
        
        self._load_profiles()
    
    def _load_profiles(self):
        """Load all configuration profiles."""
        config_file = self.config_dir / 'config.json'
        
        if config_file.exists():
            import json
            with open(config_file, 'r') as f:
                data = json.load(f)
                for name, config in data.get('profiles', {}).items():
                    self.profiles[name] = Profile(name, config)
        
        # Create default profile if none exist
        if not self.profiles:
            self.profiles['default'] = Profile('default', self._default_config())
            self._save_profiles()
    
    def _save_profiles(self):
        """Save all profiles to disk."""
        config_file = self.config_dir / 'config.json'
        import json
        
        data = {
            'profiles': {
                name: profile.config
                for name, profile in self.profiles.items()
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_profile(self, name: str) -> Optional[Profile]:
        """Get a profile by name."""
        return self.profiles.get(name)
    
    def create_profile(self, name: str, config: Optional[Dict[str, Any]] = None) -> Profile:
        """Create a new profile."""
        if name in self.profiles:
            raise ValueError(f"Profile '{name}' already exists")
        
        profile = Profile(name, config or self._default_config())
        self.profiles[name] = profile
        self._save_profiles()
        
        logger.info("Created profile: %s", name)
        return profile
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile."""
        if name == 'default':
            raise ValueError("Cannot delete default profile")
        
        if name in self.profiles:
            del self.profiles[name]
            self._save_profiles()
            logger.info("Deleted profile: %s", name)
            return True
        return False
    
    def set_active_profile(self, name: str):
        """Set the active profile."""
        if name not in self.profiles:
            raise ValueError(f"Profile '{name}' not found")
        
        self.active_profile = self.profiles[name]
        logger.info("Active profile set to: %s", name)
    
    def get_active_profile(self) -> Profile:
        """Get the active profile."""
        if not self.active_profile:
            self.active_profile = self.profiles.get('default')
        return self.active_profile
    
    def list_profiles(self) -> list:
        """List all profile names."""
        return list(self.profiles.keys())
    
    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'portal': {
                'host': '',
                'port': 443,
                'ssl': True,
                'timeout': 60
            },
            'edge': {
                'timeout': 60,
                'ssl': True
            },
            'logging': {
                'level': 'INFO',
                'file': None
            },
            'rate_limit': {
                'enabled': True,
                'max_requests': 100,
                'window_seconds': 60
            }
        }
    
    def get_env_override(self, key: str) -> Optional[str]:
        """Get environment variable override."""
        env_key = f"CTERA_{key.upper().replace('.', '_')}"
        return os.environ.get(env_key)
    
    def resolve_value(self, key: str, profile: Optional[Profile] = None) -> Any:
        """Resolve configuration value with environment override."""
        # Check environment variable first
        env_value = self.get_env_override(key)
        if env_value is not None:
            return env_value
        
        # Get from profile
        profile = profile or self.get_active_profile()
        return profile.get(key)

