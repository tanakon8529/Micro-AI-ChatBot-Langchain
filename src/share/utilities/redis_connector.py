import logging
import redis.asyncio as redis

from settings.configs import REDIS_PORT, REDIS_HOST

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def get_client():
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=False,  # Set to False to handle binary data
        )
        # Test the connection
        await redis_client.ping()
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")
        raise Exception('Redis not Connected')
    return redis_client