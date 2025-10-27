"""
Matrix connector for Star-Daemon
"""

from typing import Dict, Any
import logging
from nio import AsyncClient, LoginResponse, RoomSendResponse
import asyncio
from .base import Connector

logger = logging.getLogger(__name__)


class MatrixConnector(Connector):
    """Connector for Matrix protocol"""
    
    def __init__(self, homeserver: str, user_id: str, password: str = None, 
                 access_token: str = None, room_id: str = None):
        super().__init__("Matrix", enabled=True)
        self.homeserver = homeserver
        self.user_id = user_id
        self.password = password
        self.access_token = access_token
        self.room_id = room_id
        self.client = None
    
    def initialize(self) -> bool:
        """Initialize Matrix client"""
        try:
            self.client = AsyncClient(self.homeserver, self.user_id)
            
            # Login if we have credentials
            if self.password and not self.access_token:
                async def do_login():
                    response = await self.client.login(self.password)
                    if isinstance(response, LoginResponse):
                        self.access_token = response.access_token
                        logger.info(f"Matrix logged in successfully as {self.user_id}")
                        return True
                    else:
                        logger.error(f"Matrix login failed: {response}")
                        return False
                
                success = asyncio.run(do_login())
                if not success:
                    return False
            elif self.access_token:
                self.client.access_token = self.access_token
            
            self._initialized = True
            logger.info(f"Matrix connector initialized for {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Matrix connector: {e}")
            return False
    
    def post_message(self, message: str, metadata: Dict[str, Any] = None) -> bool:
        """Post to Matrix room"""
        try:
            async def send_message():
                # Format message with metadata if available
                if metadata:
                    formatted_message = f"⭐ **Starred Repository**\n\n{message}"
                    if metadata.get('description'):
                        formatted_message += f"\n\n_{metadata['description']}_"
                else:
                    formatted_message = message
                
                # Send message
                response = await self.client.room_send(
                    room_id=self.room_id,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.text",
                        "body": formatted_message,
                        "format": "org.matrix.custom.html",
                        "formatted_body": formatted_message.replace('\n', '<br>')
                    }
                )
                
                if isinstance(response, RoomSendResponse):
                    logger.info(f"Posted to Matrix room {self.room_id}")
                    return True
                else:
                    logger.error(f"Failed to post to Matrix: {response}")
                    return False
            
            return asyncio.run(send_message())
        except Exception as e:
            logger.error(f"Failed to post to Matrix: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test Matrix connection"""
        try:
            async def test():
                # Sync once to verify connection
                await self.client.sync(timeout=10000, full_state=False)
                logger.info(f"Matrix connection test successful for {self.user_id}")
                return True
            
            return asyncio.run(test())
        except Exception as e:
            logger.error(f"Matrix connection test failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup Matrix client"""
        if self.client:
            try:
                async def cleanup():
                    await self.client.close()
                asyncio.run(cleanup())
            except:
                pass
