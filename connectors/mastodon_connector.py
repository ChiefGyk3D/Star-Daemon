"""
Mastodon connector for Star-Daemon
"""

from typing import Dict, Any
import logging
from mastodon import Mastodon
from .base import Connector

logger = logging.getLogger(__name__)


class MastodonConnector(Connector):
    """Connector for Mastodon instances"""
    
    def __init__(self, api_base_url: str, client_id: str = None, 
                 client_secret: str = None, access_token: str = None):
        super().__init__("Mastodon", enabled=True)
        self.api_base_url = api_base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.client = None
    
    def initialize(self) -> bool:
        """Initialize Mastodon client"""
        try:
            if self.client_id and self.client_secret:
                self.client = Mastodon(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    access_token=self.access_token,
                    api_base_url=self.api_base_url
                )
            else:
                # Use access token only
                self.client = Mastodon(
                    access_token=self.access_token,
                    api_base_url=self.api_base_url
                )
            
            self._initialized = True
            logger.info(f"Mastodon connector initialized for {self.api_base_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Mastodon connector: {e}")
            return False
    
    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """Post a status to Mastodon"""
        try:
            # Mastodon character limit is 500 by default (can be higher on some instances)
            if len(message) > 500:
                message = message[:497] + "..."
            
            status = self.client.status_post(message)
            logger.info(f"Posted to Mastodon: {status['url']}")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Mastodon: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to Mastodon"""
        try:
            account = self.client.account_verify_credentials()
            logger.info(f"Mastodon connection test successful. Logged in as: @{account['username']}")
            return True
        except Exception as e:
            logger.error(f"Mastodon connection test failed: {e}")
            return False
