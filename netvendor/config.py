"""
Configuration management for NetVendor.

Supports configuration from:
- Environment variables (NETVENDOR_*)
- Configuration file (netvendor.conf, netvendor.yaml, netvendor.toml)
- Default values

Configuration file locations (checked in order):
1. Current directory: ./netvendor.conf (or .yaml, .toml)
2. User config: ~/.config/netvendor/netvendor.conf
3. System config: /etc/netvendor/netvendor.conf
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from configparser import ConfigParser


class NetVendorConfig:
    """Configuration manager for NetVendor."""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Optional path to configuration file. If None, searches
                        default locations.
        """
        self.config_file = config_file
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment."""
        # Start with defaults
        self.config = {
            'offline': False,
            'history_dir': 'history',
            'analyze_drift': False,
            'site': None,
            'environment': None,
            'change_ticket': None,
            'siem_export': False,
            'output_dir': 'output',
        }
        
        # Load from config file
        config_path = self._find_config_file()
        if config_path:
            self._load_from_file(config_path)
        
        # Override with environment variables
        self._load_from_env()
    
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in standard locations."""
        if self.config_file:
            path = Path(self.config_file)
            if path.exists():
                return path
            return None
        
        # Check current directory
        for ext in ['.conf', '.ini', '.yaml', '.yml', '.toml']:
            path = Path(f'netvendor{ext}')
            if path.exists():
                return path
        
        # Check user config directory
        user_config_dir = Path.home() / '.config' / 'netvendor'
        for ext in ['.conf', '.ini', '.yaml', '.yml', '.toml']:
            path = user_config_dir / f'netvendor{ext}'
            if path.exists():
                return path
        
        # Check system config directory
        system_config_dir = Path('/etc') / 'netvendor'
        for ext in ['.conf', '.ini', '.yaml', '.yml', '.toml']:
            path = system_config_dir / f'netvendor{ext}'
            if path.exists():
                return path
        
        return None
    
    def _load_from_file(self, config_path: Path):
        """Load configuration from file."""
        ext = config_path.suffix.lower()
        
        if ext in ['.conf', '.ini']:
            self._load_ini(config_path)
        elif ext in ['.yaml', '.yml']:
            self._load_yaml(config_path)
        elif ext == '.toml':
            self._load_toml(config_path)
        else:
            # Try JSON as fallback
            try:
                with config_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._update_config(data)
            except (json.JSONDecodeError, ValueError):
                pass
    
    def _load_ini(self, config_path: Path):
        """Load INI/ConfigParser format."""
        parser = ConfigParser()
        parser.read(config_path, encoding='utf-8')
        
        if 'netvendor' in parser:
            section = parser['netvendor']
            config = {}
            for key in section:
                value = section[key]
                # Convert boolean strings
                if value.lower() in ('true', 'yes', '1', 'on'):
                    config[key] = True
                elif value.lower() in ('false', 'no', '0', 'off'):
                    config[key] = False
                elif value.lower() == 'none' or value == '':
                    config[key] = None
                else:
                    config[key] = value
            self._update_config(config)
    
    def _load_yaml(self, config_path: Path):
        """Load YAML format (requires PyYAML if available)."""
        try:
            import yaml
            with config_path.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    # Support both flat and nested config
                    if 'netvendor' in data:
                        self._update_config(data['netvendor'])
                    else:
                        self._update_config(data)
        except ImportError:
            # PyYAML not installed, skip YAML support
            pass
        except (yaml.YAMLError, ValueError):
            pass
    
    def _load_toml(self, config_path: Path):
        """Load TOML format (requires tomli/tomllib if available)."""
        try:
            # Python 3.11+ has tomllib in stdlib
            try:
                import tomllib
                with config_path.open('rb') as f:
                    data = tomllib.load(f)
            except ImportError:
                # Fall back to tomli for older Python
                import tomli
                with config_path.open('rb') as f:
                    data = tomli.load(f)
            
            if isinstance(data, dict):
                # Support both flat and nested config
                if 'netvendor' in data:
                    self._update_config(data['netvendor'])
                else:
                    self._update_config(data)
        except ImportError:
            # TOML library not installed, skip TOML support
            pass
        except (ValueError, KeyError):
            pass
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mapping = {
            'NETVENDOR_OFFLINE': ('offline', bool),
            'NETVENDOR_HISTORY_DIR': ('history_dir', str),
            'NETVENDOR_ANALYZE_DRIFT': ('analyze_drift', bool),
            'NETVENDOR_SITE': ('site', str),
            'NETVENDOR_ENVIRONMENT': ('environment', str),
            'NETVENDOR_CHANGE_TICKET': ('change_ticket', str),
            'NETVENDOR_SIEM_EXPORT': ('siem_export', bool),
            'NETVENDOR_OUTPUT_DIR': ('output_dir', str),
        }
        
        for env_var, (config_key, config_type) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                if config_type == bool:
                    self.config[config_key] = value.lower() in ('true', 'yes', '1', 'on')
                elif config_type == str:
                    self.config[config_key] = value if value else None
                else:
                    self.config[config_key] = config_type(value)
    
    def _update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        for key, value in updates.items():
            if key in self.config:
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return self.config.copy()


def load_config(config_file: Optional[Union[str, Path]] = None) -> NetVendorConfig:
    """
    Load NetVendor configuration.
    
    Args:
        config_file: Optional path to configuration file
    
    Returns:
        NetVendorConfig instance
    
    Example:
        >>> config = load_config()
        >>> offline = config.get('offline', False)
        >>> site = config.get('site')
    """
    return NetVendorConfig(config_file)

