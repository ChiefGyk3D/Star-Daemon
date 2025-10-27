"""
Discord connector for Star-Daemon
"""

from typing import Dict, Any
import logging
import requests
from .base import Connector

logger = logging.getLogger(__name__)


class DiscordConnector(Connector):
    """Connector for Discord webhooks"""
    
    def __init__(self, webhook_url: str):
        super().__init__("Discord", enabled=True)
        self.webhook_url = webhook_url
    
    def initialize(self) -> bool:
        """Initialize Discord connector"""
        try:
            # Validate webhook URL format
            if not self.webhook_url.startswith("https://discord.com/api/webhooks/"):
                raise ValueError("Invalid Discord webhook URL")
            
            self._initialized = True
            logger.info("Discord connector initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Discord connector: {e}")
            return False
    
    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """Post to Discord via webhook"""
        try:
            # Discord message limit is 2000 characters
            if len(message) > 2000:
                message = message[:1997] + "..."
            
            # Create embed if metadata is provided
            data = {}
            
            if metadata:
                embed = {
                    "title": f"⭐ Starred: {metadata.get('name', 'Repository')}",
                    "description": message,
                    "color": 0xFFD700,  # Gold color
                    "url": metadata.get('url', ''),
                    "fields": []
                }
                
                if metadata.get('description'):
                    embed["fields"].append({
                        "name": "Description",
                        "value": metadata['description'][:1024],  # Field value limit
                        "inline": False
                    })
                
                if metadata.get('language'):
                    embed["fields"].append({
                        "name": "Language",
                        "value": metadata['language'],
                        "inline": True
                    })
                
                if metadata.get('stars') is not None:
                    embed["fields"].append({
                        "name": "Stars",
                        "value": str(metadata['stars']),
                        "inline": True
                    })
                
                data = {"embeds": [embed]}
            else:
                data = {"content": message}
            
            response = requests.post(self.webhook_url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info("Posted to Discord via webhook")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Discord: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test Discord webhook"""
        try:
            # Send a test message
            data = {"content": "🤖 Star-Daemon connection test successful!"}
            response = requests.post(self.webhook_url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info("Discord connection test successful")
            return True
        except Exception as e:
            logger.error(f"Discord connection test failed: {e}")
            return False
