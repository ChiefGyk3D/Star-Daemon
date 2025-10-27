#!/usr/bin/env python3
"""
Star-Daemon - Multi-platform GitHub starring notification daemon

Monitors GitHub starred repositories and posts to multiple social platforms
including Mastodon, BlueSky, Discord, and Matrix.
"""

import time
import logging
import sys
import signal
from typing import List, Set
from github import Github
from github.Repository import Repository

from config import config
from connectors import (
    MastodonConnector, 
    BlueSkyConnector, 
    DiscordConnector, 
    MatrixConnector
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class StarDaemon:
    """Main daemon class for monitoring GitHub stars"""
    
    def __init__(self):
        self.github = None
        self.user = None
        self.starred_repos: Set[str] = set()
        self.connectors = []
        self.running = True
    
    def initialize(self) -> bool:
        """Initialize GitHub client and connectors"""
        try:
            # Validate configuration
            if not config.validate():
                logger.error("Configuration validation failed")
                return False
            
            # Initialize GitHub client
            logger.info("Initializing GitHub client...")
            self.github = Github(config.github_token)
            
            if config.github_username:
                self.user = self.github.get_user(config.github_username)
            else:
                self.user = self.github.get_user()
            
            logger.info(f"Monitoring GitHub stars for user: {self.user.login}")
            
            # Get initial starred repos
            self.starred_repos = {repo.full_name for repo in self.user.get_starred()}
            logger.info(f"Currently tracking {len(self.starred_repos)} starred repositories")
            
            # Initialize connectors
            self._initialize_connectors()
            
            return True
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
                access_token=config.mastodon_access_token
            )
            if connector.initialize() and connector.test_connection():
                self.connectors.append(connector)
        
        # BlueSky
        if config.bluesky_enabled:
            connector = BlueSkyConnector(
                handle=config.bluesky_handle,
                app_password=config.bluesky_app_password
            )
            if connector.initialize() and connector.test_connection():
                self.connectors.append(connector)
        
        # Discord
        if config.discord_enabled:
            connector = DiscordConnector(
                webhook_url=config.discord_webhook_url
            )
            if connector.initialize() and connector.test_connection():
                self.connectors.append(connector)
        
        # Matrix
        if config.matrix_enabled:
            connector = MatrixConnector(
                homeserver=config.matrix_homeserver,
                user_id=config.matrix_user_id,
                password=config.matrix_password,
                access_token=config.matrix_access_token,
                room_id=config.matrix_room_id
            )
            if connector.initialize() and connector.test_connection():
                self.connectors.append(connector)
        
        logger.info(f"Initialized {len(self.connectors)} platform connector(s)")
    
    def check_new_stars(self):
        """Check for newly starred repositories"""
        try:
            current_starred = {repo.full_name: repo for repo in self.user.get_starred()}
            new_stars = set(current_starred.keys()) - self.starred_repos
            
            if new_stars:
                logger.info(f"Found {len(new_stars)} new starred repository(ies)")
                
                for repo_name in new_stars:
                    repo = current_starred[repo_name]
                    self._handle_new_star(repo)
                
                # Update tracked repos
                self.starred_repos = set(current_starred.keys())
            
        except Exception as e:
            logger.error(f"Error checking for new stars: {e}", exc_info=True)
    
    def _handle_new_star(self, repo: Repository):
        """Handle a newly starred repository"""
        try:
            # Build message
            message = config.message_template.format(
                url=repo.html_url,
                name=repo.full_name,
                description=repo.description or "No description"
            )
            
            # Prepare metadata
            metadata = {
                'url': repo.html_url,
                'name': repo.full_name,
                'description': repo.description,
                'language': repo.language,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count
            }
            
            logger.info(f"New star detected: {repo.full_name}")
            
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
    
    def run(self):
        """Main daemon loop"""
        logger.info(f"Star-Daemon started. Checking every {config.check_interval} seconds.")
        logger.info("Press Ctrl+C to stop.")
        
        while self.running:
            try:
                self.check_new_stars()
                time.sleep(config.check_interval)
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
