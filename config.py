"""
Configuration management for Star-Daemon
Supports both .env files and Doppler secrets management
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager with Doppler support"""
    
    def __init__(self):
        # Try to load from Doppler first, then fall back to .env
        doppler_token = os.getenv('DOPPLER_TOKEN')
        
        if doppler_token:
            logger.info("Using Doppler for secrets management")
            # Doppler CLI automatically injects environment variables
        else:
            logger.info("Loading configuration from .env file")
            load_dotenv()
        
        # Core settings
        self.check_interval = int(self._get_env('CHECK_INTERVAL', '60'))
        self.log_level = self._get_env('LOG_LEVEL', 'INFO')
        
        # GitHub
        self.github_token = self._get_env('GITHUB_ACCESS_TOKEN', required=True)
        self.github_username = self._get_env('GITHUB_USERNAME', '')
        
        # Mastodon
        self.mastodon_enabled = self._get_bool('MASTODON_ENABLED', False)
        self.mastodon_api_base_url = self._get_env('MASTODON_API_BASE_URL', '')
        self.mastodon_client_id = self._get_env('MASTODON_CLIENT_ID', '')
        self.mastodon_client_secret = self._get_env('MASTODON_CLIENT_SECRET', '')
        self.mastodon_access_token = self._get_env('MASTODON_ACCESS_TOKEN', '')
        
        # BlueSky
        self.bluesky_enabled = self._get_bool('BLUESKY_ENABLED', False)
        self.bluesky_handle = self._get_env('BLUESKY_HANDLE', '')
        self.bluesky_app_password = self._get_env('BLUESKY_APP_PASSWORD', '')
        
        # Discord
        self.discord_enabled = self._get_bool('DISCORD_ENABLED', False)
        self.discord_webhook_url = self._get_env('DISCORD_WEBHOOK_URL', '')
        self.discord_bot_token = self._get_env('DISCORD_BOT_TOKEN', '')
        self.discord_channel_id = self._get_env('DISCORD_CHANNEL_ID', '')
        
        # Matrix
        self.matrix_enabled = self._get_bool('MATRIX_ENABLED', False)
        self.matrix_homeserver = self._get_env('MATRIX_HOMESERVER', '')
        self.matrix_user_id = self._get_env('MATRIX_USER_ID', '')
        self.matrix_password = self._get_env('MATRIX_PASSWORD', '')
        self.matrix_access_token = self._get_env('MATRIX_ACCESS_TOKEN', '')
        self.matrix_room_id = self._get_env('MATRIX_ROOM_ID', '')
        
        # Message customization
        self.message_template = self._get_env(
            'MESSAGE_TEMPLATE',
            'I just starred a new repository on GitHub: {url}'
        )
        self.include_description = self._get_bool('INCLUDE_DESCRIPTION', False)
        self.max_message_length = int(self._get_env('MAX_MESSAGE_LENGTH', '500'))
    
    def _get_env(self, key: str, default: str = '', required: bool = False) -> str:
        """Get environment variable with optional default and required check"""
        value = os.getenv(key, default)
        
        if required and not value:
            raise ValueError(f"Required environment variable {key} is not set")
        
        return value
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check if at least one platform is enabled
        platforms_enabled = any([
            self.mastodon_enabled,
            self.bluesky_enabled,
            self.discord_enabled,
            self.matrix_enabled
        ])
        
        if not platforms_enabled:
            errors.append("No platforms enabled. Enable at least one platform (Mastodon, BlueSky, Discord, Matrix, or Twitter)")
        
        # Validate platform-specific configuration
        if self.mastodon_enabled:
            if not all([self.mastodon_api_base_url, self.mastodon_access_token]):
                errors.append("Mastodon enabled but missing required configuration")
        
        if self.bluesky_enabled:
            if not all([self.bluesky_handle, self.bluesky_app_password]):
                errors.append("BlueSky enabled but missing required configuration")
        
        if self.discord_enabled:
            if not self.discord_webhook_url and not (self.discord_bot_token and self.discord_channel_id):
                errors.append("Discord enabled but missing webhook URL or bot configuration")
        
        if self.matrix_enabled:
            if not all([self.matrix_homeserver, self.matrix_user_id, self.matrix_room_id]):
                errors.append("Matrix enabled but missing required configuration")
            if not self.matrix_password and not self.matrix_access_token:
                errors.append("Matrix enabled but missing password or access token")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
        
        return True


# Global config instance
config = Config()
