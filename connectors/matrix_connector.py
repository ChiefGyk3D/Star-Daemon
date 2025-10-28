"""
Matrix connector for Star-Daemon with rich message support

NOTE: Matrix does NOT support editing messages like Discord.
Messages are posted once and cannot be updated.
"""

import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import quote, urlparse

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

        # Normalize to lowercase for comparison
        hostname = hostname.lower()
        domain = domain.lower()

        # Check exact match
        if hostname == domain:
            return True

        # Check if it's a proper subdomain
        if hostname.endswith("." + domain):
            return True

        return False
    except Exception:
        return False


class MatrixConnector(Connector):
    """
    Connector for Matrix protocol with rich message support.

    NOTE: Matrix does NOT support editing messages like Discord.
    Messages are posted once and cannot be updated.
    """

    def __init__(
        self,
        homeserver: str,
        room_id: str,
        user_id: str = None,
        password: str = None,
        access_token: str = None,
    ):
        super().__init__("Matrix", enabled=True)
        self.homeserver = homeserver
        self.room_id = room_id
        self.username = user_id
        self.password = password
        self.access_token = access_token

    def initialize(self) -> bool:
        """Initialize Matrix connector"""
        try:
            if not self.homeserver or not self.room_id:
                logger.error(
                    "Missing required Matrix credentials (homeserver or room_id)"
                )
                return False

            # Ensure homeserver has proper format
            if not self.homeserver.startswith("http"):
                self.homeserver = f"https://{self.homeserver}"

            # Priority: Username/Password > Access Token
            if self.username and self.password:
                # Login to get fresh access token
                logger.info(
                    "Using username/password authentication (auto-rotation enabled)"
                )
                self.access_token = self._login_and_get_token()
                if not self.access_token:
                    logger.error("✗ Matrix login failed - check username/password")
                    return False
                logger.info(f"✓ Matrix logged in and obtained access token")
            elif self.access_token:
                # Use static access token
                logger.info("Using static access token authentication")
            else:
                logger.error(
                    "✗ Matrix authentication failed - need either access_token OR username+password"
                )
                return False

            self._initialized = True
            logger.info(f"✓ Matrix authenticated ({self.room_id})")
            return True
        except Exception as e:
            logger.error(f"✗ Matrix authentication failed: {e}")
            return False

    def _login_and_get_token(self):
        """Login with username/password to get access token."""
        try:
            # Extract just the username part from full MXID (@username:domain)
            username_local = self.username
            if username_local.startswith("@"):
                # Remove @ prefix and :domain suffix
                username_local = username_local[1:].split(":")[0]

            login_url = f"{self.homeserver}/_matrix/client/r0/login"
            login_data = {
                "type": "m.login.password",
                "identifier": {"type": "m.id.user", "user": username_local},
                "password": self.password,
            }

            response = requests.post(login_url, json=login_data, timeout=10)

            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                if access_token:
                    logger.info(f"✓ Obtained Matrix access token")
                    return access_token
                else:
                    logger.error(
                        f"✗ Matrix login succeeded but no access_token in response"
                    )
            else:
                logger.error(f"✗ Matrix login failed: {response.status_code}")

            return None
        except Exception as e:
            logger.error(f"✗ Matrix login error: {e}")
            return None

    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Post to Matrix room with rich HTML formatting.

        Args:
            message: The message to post
            metadata: Optional dict containing:
                - reply_to_id: Event ID to reply to (for threading)
                - repo_data: Repository metadata (for rich formatting)
                - url: Repository URL

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            logger.error("Matrix connector not initialized")
            return False

        if not all([self.homeserver, self.access_token, self.room_id]):
            logger.warning(f"⚠ Matrix post skipped: missing credentials")
            return False

        try:
            reply_to_id = metadata.get("reply_to_id") if metadata else None
            repo_data = metadata.get("repo_data") if metadata else None

            # Extract URL from message for rich formatting
            url_pattern = r"https?://[^\s]+"
            url_match = re.search(url_pattern, message)
            first_url = url_match.group() if url_match else None

            # If no URL in message, try metadata
            if not first_url and metadata:
                first_url = metadata.get("url")

            # Create rich HTML message with link preview
            html_body = message
            plain_body = message

            if first_url:
                # Make URL clickable in HTML
                html_body = re.sub(
                    url_pattern, f'<a href="{first_url}">{first_url}</a>', message
                )

                # Add platform-specific styling
                if _is_url_for_domain(first_url, "github.com"):
                    html_body = f"<p><strong>⭐ Starred on GitHub</strong></p><p>{html_body}</p>"
                elif _is_url_for_domain(first_url, "gitlab.com"):
                    html_body = f"<p><strong>⭐ Starred on GitLab</strong></p><p>{html_body}</p>"
                else:
                    html_body = f"<p><strong>⭐ New Star</strong></p><p>{html_body}</p>"

                # Add repository metadata if available
                if repo_data:
                    repo_name = repo_data.get("full_name", repo_data.get("name", ""))
                    description = repo_data.get("description", "")
                    language = repo_data.get("language", "")
                    stars_count = repo_data.get("stargazers_count")

                    if repo_name:
                        html_body += f"<p><strong>📦 {repo_name}</strong></p>"
                    if description:
                        html_body += f"<p><em>{description}</em></p>"

                    info_parts = []
                    if language:
                        info_parts.append(f"💻 {language}")
                    if stars_count is not None:
                        info_parts.append(f"⭐ {stars_count:,} stars")

                    if info_parts:
                        html_body += f'<p>{" • ".join(info_parts)}</p>'

            # Build Matrix message event
            event_data = {
                "msgtype": "m.text",
                "body": plain_body,
                "format": "org.matrix.custom.html",
                "formatted_body": html_body,
            }

            # Add reply reference if provided
            if reply_to_id:
                event_data["m.relates_to"] = {
                    "m.in_reply_to": {"event_id": reply_to_id}
                }

            # Send message via Matrix Client-Server API
            url = f"{self.homeserver}/_matrix/client/r0/rooms/{quote(self.room_id)}/send/m.room.message"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            response = requests.post(url, json=event_data, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                event_id = data.get("event_id")
                logger.info(f"✓ Matrix message posted (ID: {event_id})")

                # Store the event ID in metadata for threading
                if metadata is not None and event_id:
                    metadata["last_event_id"] = event_id

                return True
            else:
                logger.warning(
                    f"⚠ Matrix post failed with status {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"✗ Matrix post failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Matrix connection"""
        if not self._initialized:
            return False

        try:
            # Try to get room info to verify connection
            url = (
                f"{self.homeserver}/_matrix/client/r0/rooms/{quote(self.room_id)}/state"
            )
            headers = {
                "Authorization": f"Bearer {self.access_token}",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(f"✓ Matrix connection test successful")
                return True
            else:
                logger.error(f"✗ Matrix connection test failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"✗ Matrix connection test failed: {e}")
            return False
