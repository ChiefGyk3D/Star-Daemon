"""
Base connector class for all social platforms
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class Connector(ABC):
    """Base class for all platform connectors"""

    def __init__(self, name: str, enabled: bool):
        self.name = name
        self.enabled = enabled
        self._initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the connector. Returns True if successful."""
        pass

    @abstractmethod
    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Post a message to the platform.

        Args:
            message: The message to post
            metadata: Optional metadata about the repository

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the connection to the platform. Returns True if successful."""
        pass

    def is_ready(self) -> bool:
        """Check if connector is ready to post"""
        return self.enabled and self._initialized

    def safe_post(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Safely post a message with error handling

        Args:
            message: The message to post
            metadata: Optional metadata about the repository

        Returns:
            True if successful, False otherwise
        """
        if not self.is_ready():
            logger.warning(f"{self.name} connector is not ready")
            return False

        try:
            return self.post_message(message, metadata)
        except Exception as e:
            logger.error(f"Error posting to {self.name}: {e}", exc_info=True)
            return False
