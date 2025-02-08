# /utilities/conversation_manager.py

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict

from utilities.redis_connector import get_client
from settings.configs import CLEAR_CACHE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ConversationManager:
    """
    Manages conversation histories and session metadata using Redis.
    Now using user_id and topic_id to manage conversations.
    """

    def __init__(self):
        self.redis_client = None  # Will be initialized asynchronously

    async def init_redis(self):
        """
        Initializes the Redis client asynchronously.
        """
        self.redis_client = await get_client()
    
    async def clear_cache(self):
        """
        Clears all conversation history and session metadata.
        """
        if CLEAR_CACHE == "True":
            try:
                keys = await self.redis_client.keys("chatbot:user:*:topic:*")
                if keys:
                    await self.redis_client.delete(*keys)
                    logger.info("Cleared all conversation history and session metadata")
                else:
                    logger.info("No conversation history or session metadata to clear")
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                raise

    def _get_conversation_key(self, user_id: str, topic_id: str) -> str:
        return f"chatbot:user:{user_id}:topic:{topic_id}:conversation"

    def _get_metadata_key(self, user_id: str, topic_id: str) -> str:
        return f"chatbot:user:{user_id}:topic:{topic_id}:metadata"

    async def add_message(self, user_id: str, topic_id: str, sender: str, message: str, max_messages: int = 50):
        """
        Adds a message to the conversation history.
        """
        conversation_key = self._get_conversation_key(user_id, topic_id)
        timestamp = datetime.utcnow().isoformat()
        message_entry = json.dumps({
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        })
        try:
            await self.redis_client.lpush(conversation_key, message_entry)
            await self.redis_client.ltrim(conversation_key, 0, max_messages - 1)  # Keep only latest N messages
            await self.set_session_ttl(user_id, topic_id)
        except Exception as e:
            logger.error(f"Error adding message to Redis: {e}")
            raise

    async def get_conversation_history(self, user_id: str, topic_id: str, limit: int = 50) -> List[Dict]:
        """
        Retrieves the conversation history in chronological order.
        """
        conversation_key = self._get_conversation_key(user_id, topic_id)
        try:
            messages = await self.redis_client.lrange(conversation_key, 0, limit - 1)
            # Reverse to chronological order
            messages = [json.loads(msg) for msg in reversed(messages)]
            logger.info(f"Retrieved conversation history for user {user_id}, topic {topic_id}")
            return messages
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            raise  # Re-raise the exception to be handled upstream

    async def set_session_ttl(self, user_id: str, topic_id: str, ttl_seconds: int = 86400):
        """
        Sets the Time-To-Live for the session keys.
        """
        conversation_key = self._get_conversation_key(user_id, topic_id)
        metadata_key = self._get_metadata_key(user_id, topic_id)
        try:
            await self.redis_client.expire(conversation_key, ttl_seconds)
            await self.redis_client.expire(metadata_key, ttl_seconds)
        except Exception as e:
            logger.error(f"Error setting TTL: {e}")
            raise

    async def get_session_metadata(self, user_id: str, topic_id: str) -> Optional[Dict]:
        """
        Retrieves session metadata.
        """
        metadata_key = self._get_metadata_key(user_id, topic_id)
        try:
            metadata = await self.redis_client.hgetall(metadata_key)
            return metadata if metadata else None
        except Exception as e:
            logger.error(f"Error retrieving session metadata: {e}")
            raise  # Re-raise the exception to be handled upstream

    async def update_session_metadata(self, user_id: str, topic_id: str, field: str, value: str):
        """
        Updates a specific field in session metadata.
        """
        metadata_key = self._get_metadata_key(user_id, topic_id)
        try:
            await self.redis_client.hset(metadata_key, field, value)
            await self.set_session_ttl(user_id, topic_id)
        except Exception as e:
            logger.error(f"Error updating session metadata: {e}")
            raise  # Re-raise the exception to be handled upstream