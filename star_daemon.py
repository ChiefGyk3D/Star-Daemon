"""
Star-Daemon - Multi-platform GitHub starring notification daemon

Monitors GitHub starred repositories and posts to multiple social platforms
including Mastodon, BlueSky, Discord, and Matrix.

This module holds the daemon logic; ``star-daemon.py`` is the entry-point shim
(the hyphenated filename cannot be imported, which kept this untestable).
"""

import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Set

from config import config
from connectors import (
    BlueSkyConnector,
    DiscordConnector,
    MastodonConnector,
    MatrixConnector,
)
from github_stars import RateLimitError, StarWatcher

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = Path.home() / ".star-daemon-state.json"


class StarDaemon:
    """Main daemon class for monitoring GitHub stars"""

    def __init__(self, state_file: Optional[Path] = None):
        self.watcher: Optional[StarWatcher] = None
        self.starred_repos: Set[str] = set()
        self.connectors = []
        self.running = True
        self.state_file = Path(state_file or config.state_file or DEFAULT_STATE_FILE)
        self._last_resync = time.time()

    def initialize(self) -> bool:
        """Initialize GitHub polling and connectors"""
        try:
            # Validate configuration
            if not config.validate():
                logger.error("Configuration validation failed")
                return False

            logger.info("Initializing GitHub client...")
            self.watcher = StarWatcher(
                config.github_token,
                username=config.github_username or None,
                api_base=config.github_api_url,
                rate_limit_floor=config.rate_limit_floor,
            )

            if config.github_username:
                login = config.github_username
            else:
                login = self.watcher.viewer_login()
            logger.info(f"Monitoring GitHub stars for user: {login}")

            # Load previously tracked repos from state file
            self._load_state()

            if not self.starred_repos:
                # First run: seed with the current stars (full paginated walk,
                # once) and don't post any of them.
                self.starred_repos = self.watcher.fetch_all_starred()
                self._save_state()
                logger.info(
                    f"Initial run: tracking {len(self.starred_repos)} starred repositories (won't post existing stars)"
                )
            else:
                # State exists: no need to enumerate anything at startup.
                logger.info(
                    f"Loaded {len(self.starred_repos)} previously tracked repositories from state file"
                )

            # Initialize connectors
            self._initialize_connectors()

            return True
        except RateLimitError as e:
            logger.error(f"GitHub API rate limit is exhausted; cannot initialize: {e}")
            return False
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def _initialize_connectors(self):
        """Initialize all enabled platform connectors"""
        # Mastodon
        if config.mastodon_enabled:
            connector = MastodonConnector(
                api_base_url=config.mastodon_api_base_url,
                client_id=config.mastodon_client_id,
                client_secret=config.mastodon_client_secret,
                access_token=config.mastodon_access_token,
            )
            if connector.initialize() and connector.test_connection():
                self.connectors.append(connector)

        # BlueSky
        if config.bluesky_enabled:
            connector = BlueSkyConnector(
                handle=config.bluesky_handle, app_password=config.bluesky_app_password
            )
            if connector.initialize() and connector.test_connection():
                self.connectors.append(connector)

        # Discord
        if config.discord_enabled:
            connector = DiscordConnector(
                webhook_url=config.discord_webhook_url,
                role_id=getattr(
                    config, "discord_role_id", None
                ),  # Optional role mention
            )
            if connector.initialize() and connector.test_connection():
                self.connectors.append(connector)

        # Matrix
        if config.matrix_enabled:
            connector = MatrixConnector(
                homeserver=config.matrix_homeserver,
                room_id=config.matrix_room_id,
                user_id=config.matrix_user_id,
                password=config.matrix_password,
                access_token=config.matrix_access_token,
            )
            if connector.initialize() and connector.test_connection():
                self.connectors.append(connector)

        logger.info(f"Initialized {len(self.connectors)} platform connector(s)")

    def check_new_stars(self):
        """Check for newly starred repositories (one API request, usually free)"""
        try:
            new_repos = self.watcher.fetch_new_starred(self.starred_repos)
        except RateLimitError as e:
            logger.warning(
                f"GitHub API rate limit exhausted; skipping check and backing off: {e}"
            )
            return
        except Exception as e:
            logger.error(f"Error checking for new stars: {e}", exc_info=True)
            return

        if not new_repos:
            return

        logger.info(f"Found {len(new_repos)} new starred repository(ies)")
        for repo in new_repos:
            self._handle_new_star(repo)

        self.starred_repos |= {
            repo["full_name"] for repo in new_repos if repo.get("full_name")
        }
        self._save_state()

    def maybe_resync(self):
        """
        Periodically re-enumerate all starred repos (default: daily).

        This prunes unstarred repositories from state (so a later re-star is
        announced again) and heals any drift from missed checks. Costs
        ``ceil(N / 100)`` API requests per resync.
        """
        if config.resync_interval <= 0:
            return
        if time.time() - self._last_resync < config.resync_interval:
            return

        try:
            current = self.watcher.fetch_all_starred()
        except RateLimitError as e:
            logger.warning(f"Skipping periodic resync, rate limit exhausted: {e}")
            return
        except Exception as e:
            logger.error(f"Periodic resync failed: {e}", exc_info=True)
            return

        removed = self.starred_repos - current
        if removed:
            logger.info(
                f"Resync: pruning {len(removed)} unstarred repository(ies) from state"
            )
        self.starred_repos = current
        self._save_state()
        self._last_resync = time.time()

    def _handle_new_star(self, repo: Dict[str, Any]):
        """Handle a newly starred repository (REST API JSON dict)"""
        try:
            owner = repo.get("owner") or {}
            description = repo.get("description")

            # Build message
            message = config.message_template.format(
                url=repo.get("html_url"),
                name=repo.get("full_name"),
                description=description or "No description",
            )

            # Prepare repository data for rich embeds
            repo_data = {
                "full_name": repo.get("full_name"),
                "name": repo.get("name"),
                "description": description,
                "language": repo.get("language"),
                "stargazers_count": repo.get("stargazers_count"),
                "forks_count": repo.get("forks_count"),
                "owner": {"avatar_url": owner.get("avatar_url")},
            }

            # Prepare metadata with repo_data for connectors
            metadata = {
                "url": repo.get("html_url"),
                "repo_data": repo_data,
                "thumbnail_url": owner.get("avatar_url"),
                # Legacy fields for backwards compatibility
                "name": repo.get("full_name"),
                "description": description,
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count"),
                "forks": repo.get("forks_count"),
            }

            logger.info(f"New star detected: {repo.get('full_name')}")

            # Post to all connectors
            for connector in self.connectors:
                try:
                    success = connector.safe_post(message, metadata)
                    if success:
                        logger.info(f"Successfully posted to {connector.name}")
                    else:
                        logger.warning(f"Failed to post to {connector.name}")
                except Exception as e:
                    logger.error(f"Error posting to {connector.name}: {e}")

        except Exception as e:
            logger.error(f"Error handling new star: {e}", exc_info=True)

    def _load_state(self):
        """Load tracked repositories from state file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self.starred_repos = set(state.get("starred_repos", []))
                logger.info(f"Loaded state from {self.state_file}")
        except Exception as e:
            logger.warning(f"Could not load state file: {e}")
            self.starred_repos = set()

    def _save_state(self):
        """Save tracked repositories to state file (atomically)"""
        try:
            state = {
                "starred_repos": sorted(self.starred_repos),
                "last_updated": time.time(),
            }
            tmp_file = self.state_file.with_suffix(".json.tmp")
            with open(tmp_file, "w") as f:
                json.dump(state, f, indent=2)
            os.replace(tmp_file, self.state_file)
            logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.warning(f"Could not save state file: {e}")

    def _next_delay(self) -> float:
        """Delay before the next check, backing off when quota is low."""
        if self.watcher is not None and self.watcher.quota_low():
            wait = max(config.check_interval, self.watcher.seconds_until_reset())
            logger.warning(
                f"GitHub rate limit low "
                f"({self.watcher.rate_limit_remaining} remaining); "
                f"backing off for {wait} seconds until the window resets"
            )
            return wait
        return config.check_interval

    def run(self):
        """Main daemon loop"""
        logger.info(
            f"Star-Daemon started. Checking every {config.check_interval} seconds."
        )
        logger.info("Press Ctrl+C to stop.")

        while self.running:
            try:
                self.check_new_stars()
                self.maybe_resync()
                time.sleep(self._next_delay())
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.running = False
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(config.check_interval)

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Star-Daemon...")
        self.running = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and initialize daemon
    daemon = StarDaemon()

    if not daemon.initialize():
        logger.error("Failed to initialize Star-Daemon")
        sys.exit(1)

    # Run daemon
    try:
        daemon.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        daemon.shutdown()


if __name__ == "__main__":
    main()
