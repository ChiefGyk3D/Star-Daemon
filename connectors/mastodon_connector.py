"""
Mastodon connector for Star-Daemon
"""

from typing import Dict, Any, Optional
import logging
import os
import tempfile
import requests
from mastodon import Mastodon
from .base import Connector

logger = logging.getLogger(__name__)


class MastodonConnector(Connector):
    """Connector for Mastodon instances with threading and media support"""

    def __init__(
        self,
        api_base_url: str,
        client_id: str = None,
        client_secret: str = None,
        access_token: str = None,
    ):
        super().__init__("Mastodon", enabled=True)
        self.api_base_url = api_base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.client = None

    def initialize(self) -> bool:
        """Initialize Mastodon client"""
        try:
            if not all(
                [
                    self.client_id,
                    self.client_secret,
                    self.access_token,
                    self.api_base_url,
                ]
            ):
                logger.error("Missing required Mastodon credentials")
                return False

            self.client = Mastodon(
                client_id=self.client_id,
                client_secret=self.client_secret,
                access_token=self.access_token,
                api_base_url=self.api_base_url,
            )

            self._initialized = True
            logger.info(f"✓ Mastodon authenticated ({self.api_base_url})")
            return True
        except Exception as e:
            logger.error(f"✗ Mastodon authentication failed: {e}")
            return False

    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Post a status to Mastodon with optional threading and media support.

        Args:
            message: The message to post
            metadata: Optional dict containing:
                - reply_to_id: Post ID to reply to (for threading)
                - repo_data: Repository metadata (for rich formatting)
                - thumbnail_url: Direct thumbnail URL
                - viewer_count: Viewer count for media description
                - game_name: Game name for media description

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized or not self.client:
            logger.error("Mastodon connector not initialized")
            return False

        try:
            reply_to_id = metadata.get("reply_to_id") if metadata else None
            repo_data = metadata.get("repo_data") if metadata else None
            media_ids = []

            # Enhance message with repository metadata (like BlueSky does)
            enhanced_message = message
            if repo_data:
                repo_name = repo_data.get("full_name", repo_data.get("name", ""))
                description = repo_data.get("description", "")
                stars_count = repo_data.get("stargazers_count", 0)
                language = repo_data.get("language", "")

                # Build rich card-like text format
                card_parts = []
                if stars_count:
                    card_parts.append(f"⭐ {stars_count:,} stars")
                if language:
                    card_parts.append(language)

                card_info = " • ".join(card_parts) if card_parts else ""

                # Format similar to BlueSky's embed card
                if description and card_info:
                    enhanced_message = f"{message}\n\n{card_info}\n{description[:200]}"
                elif description:
                    enhanced_message = f"{message}\n\n{description[:200]}"
                elif card_info:
                    enhanced_message = f"{message}\n\n{card_info}"

            # Check if we should attach a thumbnail image
            if repo_data or (metadata and metadata.get("thumbnail_url")):
                thumbnail_url = metadata.get("thumbnail_url") if metadata else None
                if not thumbnail_url and repo_data:
                    # Try to get thumbnail from repo data (e.g., owner avatar or social preview)
                    thumbnail_url = repo_data.get("owner", {}).get("avatar_url")

                if thumbnail_url:
                    try:
                        # Download thumbnail
                        headers = {
                            "User-Agent": "Mozilla/5.0 (compatible; Star-Daemon/2.0)",
                        }
                        img_response = requests.get(
                            thumbnail_url, headers=headers, timeout=10
                        )

                        if img_response.status_code == 200:
                            # Determine file extension from content type or URL
                            content_type = img_response.headers.get("content-type", "")
                            if (
                                "jpeg" in content_type
                                or "jpg" in content_type
                                or thumbnail_url.endswith(".jpg")
                            ):
                                ext = ".jpg"
                            elif "png" in content_type or thumbnail_url.endswith(
                                ".png"
                            ):
                                ext = ".png"
                            elif "webp" in content_type or thumbnail_url.endswith(
                                ".webp"
                            ):
                                ext = ".webp"
                            else:
                                ext = ".jpg"  # Default fallback

                            # Save to temporary file
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=ext
                            ) as tmp_file:
                                tmp_file.write(img_response.content)
                                tmp_path = tmp_file.name

                            try:
                                # Upload to Mastodon
                                # Build description with metadata
                                description_parts = []
                                if repo_data:
                                    repo_name = repo_data.get(
                                        "full_name", repo_data.get("name", "")
                                    )
                                    if repo_name:
                                        description_parts.append(f"⭐ {repo_name}")
                                if metadata and metadata.get("viewer_count"):
                                    description_parts.append(
                                        f"👥 {metadata['viewer_count']:,} viewers"
                                    )
                                if metadata and metadata.get("game_name"):
                                    description_parts.append(
                                        f"🎮 {metadata['game_name']}"
                                    )

                                description = (
                                    " • ".join(description_parts)
                                    if description_parts
                                    else "Repository thumbnail"
                                )

                                media = self.client.media_post(
                                    tmp_path, description=description
                                )
                                media_ids.append(media["id"])
                                logger.info(
                                    f"✓ Uploaded thumbnail to Mastodon (media ID: {media['id']})"
                                )
                            finally:
                                # Clean up temp file
                                os.unlink(tmp_path)
                    except Exception as img_error:
                        logger.warning(
                            f"⚠ Could not upload thumbnail to Mastodon: {img_error}"
                        )

            # Post as a reply if reply_to_id is provided (threading)
            status = self.client.status_post(
                enhanced_message,  # Use enhanced message instead of plain message
                in_reply_to_id=reply_to_id,
                media_ids=media_ids if media_ids else None,
            )
            logger.info(f"✓ Posted to Mastodon (ID: {status['id']})")

            # Store the status ID in metadata for threading
            if metadata is not None:
                metadata["last_status_id"] = str(status["id"])

            return True
        except Exception as e:
            logger.error(f"✗ Mastodon post failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Mastodon connection"""
        if not self._initialized or not self.client:
            return False

        try:
            self.client.account_verify_credentials()
            logger.info("✓ Mastodon connection test successful")
            return True
        except Exception as e:
            logger.error(f"✗ Mastodon connection test failed: {e}")
            return False
