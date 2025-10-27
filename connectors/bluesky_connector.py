"""
BlueSky connector for Star-Daemon
"""

from typing import Dict, Any
import logging
from atproto import Client
from .base import Connector

logger = logging.getLogger(__name__)


class BlueSkyConnector(Connector):
    """Connector for BlueSky (AT Protocol)"""
    
    def __init__(self, handle: str, app_password: str):
        super().__init__("BlueSky", enabled=True)
        self.handle = handle
        self.app_password = app_password
        self.client = None
    
    def initialize(self) -> bool:
        """Initialize BlueSky client"""
        try:
            self.client = Client()
            self.client.login(self.handle, self.app_password)
            self._initialized = True
            logger.info(f"BlueSky connector initialized for {self.handle}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize BlueSky connector: {e}")
            return False
    
    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """Post to BlueSky"""
        try:
            # BlueSky character limit is 300
            if len(message) > 300:
                message = message[:297] + "..."
            
            post = self.client.send_post(text=message)
            logger.info(f"Posted to BlueSky: {post.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to post to BlueSky: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to BlueSky"""
        try:
            profile = self.client.get_profile(self.handle)
            logger.info(f"BlueSky connection test successful. Logged in as: @{profile.handle}")
            return True
        except Exception as e:
            logger.error(f"BlueSky connection test failed: {e}")
            return False
