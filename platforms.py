"""
Social platform wiring for Star-Daemon, backed by hypeman-social.

Star-Daemon used to carry ~1,300 lines of its own connectors for Bluesky,
Mastodon, Discord, and Matrix. Their rendering (repository embeds and cards)
now lives inside hypeman-social's platforms, triggered by
``event_kind: EVENT_STAR`` — so this module shrinks to three jobs:

1. Translate Star-Daemon's historical env names (``MASTODON_ENABLED``,
   ``MATRIX_USER_ID``, ``DISCORD_ROLE_ID``) to the hypeman-social convention
   (``MASTODON_ENABLE_POSTING``, ``MATRIX_USERNAME``, ``DISCORD_ROLE``), so
   existing deployments keep working without touching their .env or Doppler.
2. Adapt the daemon's connector interface — ``safe_post(message, metadata)``
   returning a bool — onto hypeman's ``SocialPlatform.safe_post``.
3. Build one connector per enabled platform from hypeman's ``REGISTRY``,
   which also gets Star-Daemon every network hypeman grows (Threads landed
   this way) for free.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from hypeman_social.social import EVENT_STAR, REGISTRY, DiscordPlatform, SocialPlatform

logger = logging.getLogger(__name__)


class Connector(ABC):
    """
    Star-Daemon's connector interface, kept for the daemon and its tests.

    The real implementations are hypeman platforms behind PlatformConnector;
    this ABC survives so test doubles keep their historical shape.
    """

    def __init__(self, name: str, enabled: bool):
        self.name = name
        self.enabled = enabled
        self._initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the connector. Returns True if successful."""

    @abstractmethod
    def post_message(
        self, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Post a message. Returns True if successful."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the connection to the platform. Returns True if successful."""

    def is_ready(self) -> bool:
        """Check if connector is ready to post."""
        return self.enabled and self._initialized

    def safe_post(
        self, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Post with error handling; one bad platform never stops the rest."""
        if not self.is_ready():
            logger.warning(f"{self.name} connector is not ready")
            return False

        try:
            return self.post_message(message, metadata)
        except Exception as e:
            logger.error(f"Error posting to {self.name}: {e}", exc_info=True)
            return False


class PlatformConnector(Connector):
    """A hypeman-social platform wearing Star-Daemon's connector interface."""

    def __init__(self, platform: SocialPlatform):
        super().__init__(platform.name, enabled=True)
        self.platform = platform

    def initialize(self) -> bool:
        self._initialized = self.platform.authenticate()
        return self._initialized

    def test_connection(self) -> bool:
        return self.platform.test_connection()

    def post_message(
        self, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Map the daemon's metadata dict onto hypeman's stream_data payload.

        EVENT_STAR is what makes every platform render the repository —
        Discord's rich embed, Bluesky's API-metadata card, Mastodon's text
        card, Matrix's heading and paragraphs.
        """
        metadata = metadata or {}
        stream_data = {
            "event_kind": EVENT_STAR,
            "repo_data": metadata.get("repo_data"),
            "thumbnail_url": metadata.get("thumbnail_url"),
            "url": metadata.get("url"),
        }
        post_id = self.platform.safe_post(
            message,
            reply_to_id=metadata.get("reply_to_id"),
            stream_data=stream_data,
        )
        if post_id:
            # Preserved for callers that thread follow-ups.
            metadata["last_post_id"] = post_id
        return post_id is not None


def bridge_config_to_env(config) -> None:
    """
    Export the resolved Star-Daemon config under hypeman-social's env names.

    Renames: `*_ENABLED` becomes `*_ENABLE_POSTING`, `MATRIX_USER_ID` becomes
    `MATRIX_USERNAME`, `DISCORD_ROLE_ID` becomes `DISCORD_ROLE`. Same-named
    values (MASTODON_CLIENT_ID, BLUESKY_HANDLE, MATRIX_ROOM_ID, ...) need no
    translation — hypeman's `<PLATFORM>_<KEY>` fallback already finds them.

    setdefault everywhere: anything already set in the environment under the
    hypeman name (by an operator adopting the new convention directly) wins
    over the translation. Values resolved through Star-Daemon's own secrets
    manager (Doppler/AWS/Vault) are exported too, so hypeman's env-fallback
    lookup finds them without needing its own manager configuration.
    """

    def export(name: str, value) -> None:
        if value:
            os.environ.setdefault(name, str(value))

    export("MASTODON_ENABLE_POSTING", "true" if config.mastodon_enabled else "")
    export("MASTODON_API_BASE_URL", config.mastodon_api_base_url)
    export("MASTODON_CLIENT_ID", config.mastodon_client_id)
    export("MASTODON_CLIENT_SECRET", config.mastodon_client_secret)
    export("MASTODON_ACCESS_TOKEN", config.mastodon_access_token)

    export("BLUESKY_ENABLE_POSTING", "true" if config.bluesky_enabled else "")
    export("BLUESKY_HANDLE", config.bluesky_handle)
    export("BLUESKY_APP_PASSWORD", config.bluesky_app_password)

    export("DISCORD_ENABLE_POSTING", "true" if config.discord_enabled else "")
    export("DISCORD_WEBHOOK_URL", config.discord_webhook_url)
    export("DISCORD_ROLE", config.discord_role_id)

    export("MATRIX_ENABLE_POSTING", "true" if config.matrix_enabled else "")
    export("MATRIX_HOMESERVER", config.matrix_homeserver)
    export("MATRIX_ROOM_ID", config.matrix_room_id)
    export("MATRIX_USERNAME", config.matrix_user_id)
    export("MATRIX_PASSWORD", config.matrix_password)
    export("MATRIX_ACCESS_TOKEN", config.matrix_access_token)

    export("THREADS_ENABLE_POSTING", "true" if config.threads_enabled else "")
    export("THREADS_ACCESS_TOKEN", config.threads_access_token)
    export("THREADS_USER_ID", config.threads_user_id)


def build_connectors(config) -> List[Connector]:
    """
    Construct, authenticate, and probe a connector for every enabled platform.

    Platforms that are disabled, fail to authenticate, or fail their
    connection probe are skipped with a log line — the daemon runs with
    whatever works, same as before.
    """
    bridge_config_to_env(config)

    connectors: List[Connector] = []
    for name, platform_cls in REGISTRY.items():
        # Discord picks embed style from the event kind; announcements from
        # this daemon are always stars.
        if platform_cls is DiscordPlatform:
            platform = platform_cls(default_event_kind=EVENT_STAR)
        else:
            platform = platform_cls()

        connector = PlatformConnector(platform)
        if not connector.initialize():
            continue
        if not connector.test_connection():
            logger.warning(
                f"⚠ {connector.name} authenticated but failed its connection probe"
            )
            continue
        connectors.append(connector)

    logger.info(f"Initialized {len(connectors)} platform connector(s)")
    return connectors
