from __future__ import annotations

import logging

from fastapi import HTTPException

from apis.langgpt.submod import query_conversation_history, ask_langchain_models, test_chatbot_faiss

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def get_conversation_history(data):
    result = None
    try:
        if data is None:
            raise HTTPException(status_code=400, detail='data is required.')
        
        result = await query_conversation_history(data)
        if "error_server" in result or "error_code" in result:
            raise HTTPException(status_code=400, detail='{}'.format(result.get('msg')))
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail='{}'.format(result.get('msg')))

        return result
    except Exception as e:
        logger.error(str(e))
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(status_code=500, detail='internal server error: {0}'.format(e))

async def ai_langchain_ask(data):
    result = None
    try:
        if data is None:
            raise HTTPException(status_code=400, detail='data is required.')
        
        result = await ask_langchain_models(data)
        if "error_server" in result or "error_code" in result:
            raise HTTPException(status_code=400, detail='{}'.format(result.get('msg')))
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail='{}'.format(result.get('msg')))

        return result
    except Exception as e:
        logger.error(str(e))
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(status_code=500, detail='internal server error: {0}'.format(e))
        
async def ai_langchain_test(data):
    result = None
    try:
        result = await test_chatbot_faiss(data)
        if not result:
            raise HTTPException(status_code=500, detail='Failed to run tests.')
        
        return result
    except Exception as e:
        logger.error(str(e))
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(status_code=500, detail='internal server error: {0}'.format(e))
        