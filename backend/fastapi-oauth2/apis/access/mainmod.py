# apis/access/mainmod.py

import logging

from fastapi import HTTPException, Request
from typing import Dict

from core.auth import authenticate_user, store_access_token

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def get_token(client_id: str, client_secret: str, request: Request) -> Dict[str, str]:
    try:
        access_token = await authenticate_user(client_id, client_secret)
        if not access_token:
            raise HTTPException(status_code=401, detail='Access Denied')
        
        result = await store_access_token(access_token, request)
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        return result
    except Exception as e:
        # Log the error with both `error` and `message`
        logger.error(error=str(e), message='Error in get_token')
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(status_code=500, detail=f'internal server error: {e}')