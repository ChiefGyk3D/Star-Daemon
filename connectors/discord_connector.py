"""
Discord connector for Star-Daemon with rich embeds and message updating
"""

from typing import Dict, Any, Optional
import logging
import re
import time
from urllib.parse import urlparse
import requests
from .base import Connector

logger = logging.getLogger(__name__)


def _is_url_for_domain(url: str, domain: str) -> bool:
    """
    Safely check if a URL is for a specific domain.

    Args:
        url: The URL to check
        domain: The domain to match (e.g., 'github.com', 'gitlab.com')

    Returns:
        True if the URL's hostname matches or is a subdomain of the domain
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        # Check exact match or subdomain
        return hostname == domain or hostname.endswith("." + domain)
    except Exception:
        return False


class DiscordConnector(Connector):
    """Connector for Discord webhooks with rich embed and role mention support"""

    def __init__(self, webhook_url: str, role_id: str = None):
        super().__init__("Discord", enabled=True)
        self.webhook_url = webhook_url
        self.role_id = role_id  # Optional role ID for mentions
        self.active_messages = {}  # Track messages for updating

    def initialize(self) -> bool:
        """Initialize Discord connector"""
        try:
            # Validate webhook URL format
            if not self.webhook_url or not self.webhook_url.startswith(
                "https://discord.com/api/webhooks/"
            ):
                raise ValueError("Invalid Discord webhook URL")

            self._initialized = True
            if self.role_id:
                logger.info(f"✓ Discord webhook configured (with role mention)")
            else:
                logger.info(f"✓ Discord webhook configured")
            return True
        except Exception as e:
            logger.error(f"✗ Discord authentication failed: {e}")
            return False

    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Post to Discord via webhook with rich embeds.

        Args:
            message: The message to post
            metadata: Optional dict containing:
                - repo_data: Repository metadata (for embeds)
                - thumbnail_url: Direct thumbnail URL
                - url: Repository URL

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Discord connector not initialized")
            return False

        try:
            # Extract URL from message for embed
            url_pattern = r"https?://[^\s]+"
            url_match = re.search(url_pattern, message)
            first_url = url_match.group() if url_match else None

            # If no URL in message, try metadata
            if not first_url and metadata:
                first_url = metadata.get("url")

            # Build Discord embed with rich card
            embed = None
            repo_data = metadata.get("repo_data") if metadata else None

            if first_url:
                # Determine color and title based on platform
                color = 0xFFD700  # Default gold
                platform_title = "⭐ New Starred Repository"

                if _is_url_for_domain(first_url, "github.com"):
                    color = 0x6E5494  # GitHub purple
                    platform_title = "⭐ Starred on GitHub"
                elif _is_url_for_domain(first_url, "gitlab.com"):
                    color = 0xFC6D26  # GitLab orange
                    platform_title = "⭐ Starred on GitLab"

                # Create embed
                embed = {
                    "title": platform_title,
                    "description": message if message else "New repository starred!",
                    "url": first_url,
                    "color": color,
                }

                # Add fields for repository metadata
                fields = []
                if repo_data:
                    repo_name = repo_data.get("full_name", repo_data.get("name", ""))
                    if repo_name:
                        fields.append(
                            {
                                "name": "📦 Repository",
                                "value": repo_name,
                                "inline": False,
                            }
                        )

                    description = repo_data.get("description", "")
                    if description:
                        fields.append(
                            {
                                "name": "📝 Description",
                                "value": description[:1024],  # Field value limit
                                "inline": False,
                            }
                        )

                    language = repo_data.get("language", "")
                    stars_count = repo_data.get("stargazers_count")

                    if language:
                        fields.append(
                            {"name": "💻 Language", "value": language, "inline": True}
                        )

                    if stars_count is not None:
                        fields.append(
                            {
                                "name": "⭐ Stars",
                                "value": f"{stars_count:,}",
                                "inline": True,
                            }
                        )

                    forks = repo_data.get("forks_count")
                    if forks is not None:
                        fields.append(
                            {"name": "🔀 Forks", "value": f"{forks:,}", "inline": True}
                        )

                if fields:
                    embed["fields"] = fields

                # Add thumbnail if available
                thumbnail_url = metadata.get("thumbnail_url") if metadata else None
                if not thumbnail_url and repo_data and repo_data.get("owner"):
                    thumbnail_url = repo_data["owner"].get("avatar_url")

                if thumbnail_url:
                    embed["thumbnail"] = {"url": thumbnail_url}

                embed["footer"] = {"text": "Click to view repository"}

            # Build content: message + role mention
            content = ""
            if self.role_id:
                content = f"<@&{self.role_id}>"

            # Build webhook payload
            data = {}
            if content:
                data["content"] = content
            if embed:
                data["embeds"] = [embed]
            elif message:
                # Fallback to simple message if no embed
                data["content"] = content + " " + message if content else message

            # Add ?wait=true to get the message ID back
            webhook_url_with_wait = (
                self.webhook_url + "?wait=true"
                if "?" not in self.webhook_url
                else self.webhook_url + "&wait=true"
            )

            response = requests.post(webhook_url_with_wait, json=data, timeout=10)

            if response.status_code == 200:
                message_data = response.json()
                message_id = message_data.get("id")
                if message_id and first_url:
                    # Store message info for potential future updates
                    self.active_messages[first_url] = {
                        "message_id": message_id,
                        "last_update": time.time(),
                        "original_content": content,
                    }
                logger.info(f"✓ Discord embed posted (ID: {message_id})")
                return True
            else:
                logger.warning(
                    f"⚠ Discord post failed with status {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"✗ Discord post failed: {e}")
            return False

    def update_message(self, repo_url: str, repo_data: dict) -> bool:
        """Update an existing Discord embed with fresh repository data."""
        if not self._initialized or not repo_url:
            return False

        if repo_url not in self.active_messages:
            logger.debug(f"No active Discord message for {repo_url} to update")
            return False

        msg_info = self.active_messages[repo_url]
        message_id = msg_info["message_id"]

        try:
            # Determine color and platform info
            color = 0xFFD700  # Default gold
            platform_title = "⭐ Starred Repository"

            if _is_url_for_domain(repo_url, "github.com"):
                color = 0x6E5494
                platform_title = "⭐ Starred on GitHub"
            elif _is_url_for_domain(repo_url, "gitlab.com"):
                color = 0xFC6D26
                platform_title = "⭐ Starred on GitLab"

            # Build updated embed
            embed = {
                "title": platform_title,
                "url": repo_url,
                "color": color,
            }

            # Add repository metadata fields
            fields = []
            repo_name = repo_data.get("full_name", repo_data.get("name", ""))
            if repo_name:
                fields.append(
                    {"name": "📦 Repository", "value": repo_name, "inline": False}
                )

            description = repo_data.get("description", "")
            if description:
                fields.append(
                    {
                        "name": "📝 Description",
                        "value": description[:1024],
                        "inline": False,
                    }
                )

            language = repo_data.get("language", "")
            stars_count = repo_data.get("stargazers_count")

            if language:
                fields.append(
                    {"name": "💻 Language", "value": language, "inline": True}
                )

            if stars_count is not None:
                fields.append(
                    {"name": "⭐ Stars", "value": f"{stars_count:,}", "inline": True}
                )

            if fields:
                embed["fields"] = fields

            # Add thumbnail
            if repo_data.get("owner"):
                embed["thumbnail"] = {"url": repo_data["owner"].get("avatar_url")}

            # Add last updated timestamp in footer
            embed["footer"] = {"text": f"Last updated: {time.strftime('%H:%M:%S')}"}

            # Keep original content (role mention) from initial post
            content = msg_info.get("original_content", "")

            # Build update payload
            data = {}
            if content:
                data["content"] = content
            data["embeds"] = [embed]

            # PATCH the message via webhook
            edit_url = f"{self.webhook_url}/messages/{message_id}"
            response = requests.patch(edit_url, json=data, timeout=10)

            if response.status_code == 200:
                msg_info["last_update"] = time.time()
                logger.info(f"✓ Discord embed updated for {repo_name}")
                return True
            else:
                logger.warning(
                    f"⚠ Discord update failed with status {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"✗ Discord update failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Discord webhook without posting a visible message"""
        if not self._initialized:
            return False

        try:
            # Validate webhook URL format - Discord webhooks follow a specific pattern
            # Format: https://discord.com/api/webhooks/{webhook.id}/{webhook.token}
            if not self.webhook_url or not self.webhook_url.startswith(
                "https://discord.com/api/webhooks/"
            ):
                logger.error("✗ Discord webhook URL validation failed: invalid format")
                return False

            # Webhook URL is valid - we'll trust it works until first actual post
            # (Discord doesn't provide a GET endpoint to validate webhooks without posting)
            logger.info("✓ Discord webhook URL validated")
            return True
        except Exception as e:
            logger.error(f"✗ Discord connection test failed: {e}")
            return False
