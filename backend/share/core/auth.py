# core/auth.py

import logging

from uuid import uuid4
from typing import Dict
from datetime import timedelta

from fastapi import HTTPException, Request, Header

from settings.configs import USERNAME_ADMIN, PASSWORD_ADMIN

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

username_pack = [USERNAME_ADMIN]
password_pack = [PASSWORD_ADMIN]

# Define token expiration time (in minutes)
token_expire_minutes = 60

# Validate access token
async def valid_access_token(token: str = Header(...), request: Request = None) -> Dict[str, str]:
    if "Bearer" in token:
        token = token.replace("Bearer", "").replace(" ", "")
    else:
        raise HTTPException(status_code=401, detail='Invalid access token')

    # Check if access token is valid
    redis = request.state.redis
    token_key = f'token:{token}'
    token_value = await redis.get(token_key)
    if not token_value:
        raise HTTPException(status_code=401, detail='Invalid access token')

    return {'detail': 'Valid access token!'}

# Authenticate user and return access token
async def authenticate_user(username: str, password: str) -> str:
    # Replace this with your own authentication logic
    access_token = None
    if username in username_pack and password in password_pack:
        access_token = str(uuid4())
    return access_token

# Store access token in Redis and return token info
async def store_access_token(access_token: str, request: Request) -> Dict[str, str]:
    try:
        # Generate token key
        token_key = f'token:{access_token}'
        # Store access token with expiration time
        await request.state.redis.setex(token_key, timedelta(minutes=token_expire_minutes), access_token)
        # Return token info
        result = {'access_token': access_token, 'token_type': 'Bearer'}
    except Exception as e:
        logger.error(str(e))
        result = {'error': str(e)}

    return result