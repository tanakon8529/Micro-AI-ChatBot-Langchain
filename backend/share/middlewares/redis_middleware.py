# middlewares/redis_middleware.py

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from utilities.redis_connector import get_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class RedisMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            request.state.redis = await get_client()
        except Exception as e:
            logger.error(f"Error initializing Redis client: {e}")
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
        response = await call_next(request)
        await request.state.redis.close()
        return response