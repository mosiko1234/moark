"""S3 Settings Manager - Store and retrieve S3 configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


class S3Settings:
    """Manager for S3 settings storage."""
    
    def __init__(self, settings_file: Path):
        """Initialize S3 settings manager.
        
        Args:
            settings_file: Path to settings JSON file
        """
        self.settings_file = settings_file
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """Load S3 settings from file.
        
        Returns:
            Dictionary with S3 settings
        """
        if not self.settings_file.exists():
            return {}
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    def save(self, settings: Dict[str, Any]) -> None:
        """Save S3 settings to file.
        
        Args:
            settings: Dictionary with S3 settings
        """
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    
    def get_endpoint_url(self) -> str | None:
        """Get S3 endpoint URL."""
        return self.load().get('endpoint_url')
    
    def get_bucket_name(self) -> str | None:
        """Get S3 bucket name."""
        return self.load().get('bucket_name')
    
    def get_access_key(self) -> str | None:
        """Get S3 access key."""
        return self.load().get('access_key')
    
    def get_secret_key(self) -> str | None:
        """Get S3 secret key."""
        return self.load().get('secret_key')
    
    def get_region(self) -> str:
        """Get S3 region."""
        return self.load().get('region', 'us-east-1')
    
    def get_verify_ssl(self) -> bool:
        """Get SSL verification setting."""
        return self.load().get('verify_ssl', True)
    
    def is_configured(self) -> bool:
        """Check if S3 is configured.
        
        Returns:
            True if endpoint_url and bucket_name are set
        """
        settings = self.load()
        return bool(settings.get('endpoint_url') and settings.get('bucket_name'))
    
    def set_settings(
        self,
        endpoint_url: str,
        bucket_name: str,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str = 'us-east-1',
        verify_ssl: bool = True
    ) -> None:
        """Set S3 settings.
        
        Args:
            endpoint_url: S3 endpoint URL
            bucket_name: S3 bucket name
            access_key: AWS access key (optional)
            secret_key: AWS secret key (optional)
            region: AWS region
            verify_ssl: Whether to verify SSL
        """
        settings = {
            'endpoint_url': endpoint_url,
            'bucket_name': bucket_name,
            'region': region,
            'verify_ssl': verify_ssl
        }
        
        if access_key:
            settings['access_key'] = access_key
        if secret_key:
            settings['secret_key'] = secret_key
        
        self.save(settings)
    
    def clear(self) -> None:
        """Clear S3 settings."""
        if self.settings_file.exists():
            self.settings_file.unlink()

