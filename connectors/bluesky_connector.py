"""
BlueSky connector for Star-Daemon with threading and rich embed support
"""

import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from atproto import Client, client_utils, models
from bs4 import BeautifulSoup

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


class BlueSkyConnector(Connector):
    """Connector for BlueSky (AT Protocol) with threading and rich embeds"""

    def __init__(self, handle: str, app_password: str):
        super().__init__("BlueSky", enabled=True)
        self.handle = handle
        self.app_password = app_password
        self.client = None

    def initialize(self) -> bool:
        """Initialize BlueSky client"""
        try:
            if not all([self.handle, self.app_password]):
                logger.error("Missing required BlueSky credentials")
                return False

            self.client = Client()
            self.client.login(self.handle, self.app_password)
            self._initialized = True
            logger.info(f"✓ Bluesky authenticated (@{self.handle})")
            return True
        except Exception as e:
            logger.error(f"✗ Bluesky authentication failed: {e}")
            return False

    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Post to BlueSky with rich text, embeds, and threading support.

        Args:
            message: The message to post
            metadata: Optional dict containing:
                - reply_to_id: Post URI to reply to (for threading)
                - repo_data: Repository metadata (for embeds)
                - thumbnail_url: Direct thumbnail URL

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized or not self.client:
            logger.error("BlueSky connector not initialized")
            return False

        try:
            reply_to_id = metadata.get("reply_to_id") if metadata else None
            repo_data = metadata.get("repo_data") if metadata else None

            # Use TextBuilder to create rich text with explicit links
            text_builder = client_utils.TextBuilder()

            # Parse message to find URLs and convert them to clickable links
            url_pattern = r"https?://[^\s]+"
            last_pos = 0
            first_url = None  # Track first URL for embed card

            for match in re.finditer(url_pattern, message):
                # Add text before URL
                if match.start() > last_pos:
                    text_builder.text(message[last_pos : match.start()])

                # Add URL as clickable link
                url = match.group()
                text_builder.link(url, url)

                # Capture first URL for embed card
                if first_url is None:
                    first_url = url

                last_pos = match.end()

            # Add any remaining text after last URL
            if last_pos < len(message):
                text_builder.text(message[last_pos:])

            # Create embed card for the first URL if found
            embed = None
            if first_url:
                try:
                    # Use provided metadata if available
                    if repo_data and (
                        _is_url_for_domain(first_url, "github.com")
                        or _is_url_for_domain(first_url, "gitlab.com")
                    ):
                        logger.info(f"ℹ Using repository metadata for embed")

                        title = repo_data.get(
                            "full_name", repo_data.get("name", "Repository")
                        )
                        description = repo_data.get("description", "")[:1000]

                        # Try to get avatar/thumbnail
                        thumbnail_url = (
                            metadata.get("thumbnail_url") if metadata else None
                        )
                        if not thumbnail_url and repo_data.get("owner"):
                            thumbnail_url = repo_data["owner"].get("avatar_url")

                        # Upload thumbnail to Bluesky if available
                        thumb_blob = None
                        if thumbnail_url:
                            try:
                                headers = {
                                    "User-Agent": "Mozilla/5.0 (compatible; Star-Daemon/2.0)",
                                }
                                img_response = requests.get(
                                    thumbnail_url, headers=headers, timeout=10
                                )
                                if img_response.status_code == 200:
                                    upload_response = self.client.upload_blob(
                                        img_response.content
                                    )
                                    thumb_blob = (
                                        upload_response.blob
                                        if hasattr(upload_response, "blob")
                                        else None
                                    )
                            except Exception as img_error:
                                logger.warning(
                                    f"⚠ Could not upload thumbnail: {img_error}"
                                )

                        # Create external embed with repository metadata
                        stars_count = repo_data.get("stargazers_count", 0)
                        language = repo_data.get("language", "")
                        embed_desc = f"⭐ {stars_count:,} stars"
                        if language:
                            embed_desc += f" • {language}"
                        if description:
                            embed_desc += f"\n\n{description}"

                        embed = models.AppBskyEmbedExternal.Main(
                            external=models.AppBskyEmbedExternal.External(
                                uri=first_url,
                                title=title[:300] if title else "Repository",
                                description=embed_desc[:1000],
                                thumb=thumb_blob if thumb_blob else None,
                            )
                        )
                    else:
                        # For other URLs, scrape Open Graph metadata
                        headers = {
                            "User-Agent": "Mozilla/5.0 (compatible; Star-Daemon/2.0)",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.5",
                        }

                        response = requests.get(first_url, headers=headers, timeout=10)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, "html.parser")

                        # Try Open Graph metadata first
                        og_title = soup.find("meta", property="og:title")
                        og_description = soup.find("meta", property="og:description")
                        og_image = soup.find("meta", property="og:image")

                        # Fallback to Twitter Card metadata
                        if not og_title:
                            og_title = soup.find(
                                "meta", attrs={"name": "twitter:title"}
                            )
                        if not og_description:
                            og_description = soup.find(
                                "meta", attrs={"name": "twitter:description"}
                            )
                        if not og_image:
                            og_image = soup.find(
                                "meta", attrs={"name": "twitter:image"}
                            )

                        title = (
                            og_title["content"]
                            if og_title and og_title.get("content")
                            else first_url
                        )
                        description = (
                            og_description["content"]
                            if og_description and og_description.get("content")
                            else ""
                        )
                        image_url = (
                            og_image["content"]
                            if og_image and og_image.get("content")
                            else None
                        )

                        # Upload image to Bluesky if available
                        thumb_blob = None
                        if image_url:
                            try:
                                # Handle relative URLs
                                if image_url.startswith("//"):
                                    image_url = "https:" + image_url
                                elif image_url.startswith("/"):
                                    parsed = urlparse(first_url)
                                    image_url = (
                                        f"{parsed.scheme}://{parsed.netloc}{image_url}"
                                    )

                                img_response = requests.get(
                                    image_url, headers=headers, timeout=10
                                )
                                if img_response.status_code == 200:
                                    upload_response = self.client.upload_blob(
                                        img_response.content
                                    )
                                    thumb_blob = (
                                        upload_response.blob
                                        if hasattr(upload_response, "blob")
                                        else None
                                    )
                            except Exception as img_error:
                                logger.warning(
                                    f"⚠ Could not upload thumbnail: {img_error}"
                                )

                        # Create external embed with metadata
                        embed = models.AppBskyEmbedExternal.Main(
                            external=models.AppBskyEmbedExternal.External(
                                uri=first_url,
                                title=title[:300] if title else first_url,
                                description=description[:1000] if description else "",
                                thumb=thumb_blob if thumb_blob else None,
                            )
                        )
                except Exception as embed_error:
                    logger.warning(f"⚠ Could not create embed card: {embed_error}")
                    embed = None

            # Handle threading
            if reply_to_id:
                try:
                    # Get the parent post details
                    parent_response = self.client.app.bsky.feed.get_posts(
                        {"uris": [reply_to_id]}
                    )

                    if (
                        not parent_response
                        or not hasattr(parent_response, "posts")
                        or not parent_response.posts
                    ):
                        logger.warning(
                            f"⚠ Could not fetch parent post, posting without thread"
                        )
                        response = self.client.send_post(text_builder, embed=embed)
                        post_uri = response.uri if hasattr(response, "uri") else None
                    else:
                        parent_post = parent_response.posts[0]

                        # Determine root: if parent has a reply, use its root, otherwise parent is root
                        if (
                            hasattr(parent_post.record, "reply")
                            and parent_post.record.reply
                        ):
                            root_ref = parent_post.record.reply.root
                        else:
                            # Parent is the root - create strong ref
                            root_ref = models.create_strong_ref(parent_post)

                        # Create parent reference
                        parent_ref = models.create_strong_ref(parent_post)

                        # Create reply reference
                        reply_ref = models.AppBskyFeedPost.ReplyRef(
                            parent=parent_ref, root=root_ref
                        )

                        # Send threaded post with rich text and embed
                        response = self.client.send_post(
                            text_builder, reply_to=reply_ref, embed=embed
                        )
                        post_uri = response.uri if hasattr(response, "uri") else None

                except Exception as thread_error:
                    logger.warning(
                        f"⚠ Bluesky threading failed, posting without thread: {thread_error}"
                    )
                    response = self.client.send_post(text_builder, embed=embed)
                    post_uri = response.uri if hasattr(response, "uri") else None
            else:
                # Simple post without threading, with rich text and embed card
                response = self.client.send_post(text_builder, embed=embed)
                post_uri = response.uri if hasattr(response, "uri") else None

            logger.info(f"✓ Posted to Bluesky (URI: {post_uri})")

            # Store the post URI in metadata for threading
            if metadata is not None and post_uri:
                metadata["last_post_uri"] = post_uri

            return True

        except Exception as e:
            logger.error(f"✗ Bluesky post failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test connection to BlueSky"""
        if not self._initialized or not self.client:
            return False

        try:
            profile = self.client.get_profile(self.handle)
            logger.info(f"✓ BlueSky connection test successful (@{profile.handle})")
            return True
        except Exception as e:
            logger.error(f"✗ BlueSky connection test failed: {e}")
            return False
