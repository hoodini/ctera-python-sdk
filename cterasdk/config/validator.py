"""Configuration validator."""
import logging
from typing import Dict, Any, List

logger = logging.getLogger('cterasdk.config')


class ValidationError(Exception):
    """Configuration validation error."""
    pass


class ConfigValidator:
    """Validates configuration against schema."""
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration.
        
        :param dict config: Configuration to validate
        :return: List of validation errors
        """
        errors = []
        
        # Validate portal config
        if 'portal' in config:
            portal = config['portal']
            if 'host' in portal and not portal['host']:
                errors.append("Portal host cannot be empty")
            if 'port' in portal:
                port = portal['port']
                if not isinstance(port, int) or port < 1 or port > 65535:
                    errors.append(f"Invalid portal port: {port}")
            if 'timeout' in portal:
                timeout = portal['timeout']
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    errors.append(f"Invalid portal timeout: {timeout}")
        
        # Validate rate limit config
        if 'rate_limit' in config:
            rl = config['rate_limit']
            if 'max_requests' in rl:
                if not isinstance(rl['max_requests'], int) or rl['max_requests'] < 1:
                    errors.append(f"Invalid max_requests: {rl['max_requests']}")
            if 'window_seconds' in rl:
                if not isinstance(rl['window_seconds'], (int, float)) or rl['window_seconds'] <= 0:
                    errors.append(f"Invalid window_seconds: {rl['window_seconds']}")
        
        return errors
    
    @staticmethod
    def validate_and_raise(config: Dict[str, Any]):
        """Validate and raise exception if invalid."""
        errors = ConfigValidator.validate(config)
        if errors:
            raise ValidationError(f"Configuration validation failed: {', '.join(errors)}")

