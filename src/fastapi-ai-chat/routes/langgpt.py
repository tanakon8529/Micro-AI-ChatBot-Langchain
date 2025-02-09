from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from typing import Optional, Dict

from core.auth import valid_access_token
from core.models import DynamicBaseModel

from utilities.dependencies import limit_concurrency

from apis.langgpt.mainmod import get_conversation_history, ai_langchain_ask, ai_langchain_test

router = APIRouter()

# Health check endpoint
@router.get("/v1/health/")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the AI Chat service"""
    return {"status": "healthy", "service": "ai-chat"}

@router.post("/v1/conversation/")
async def conversation_history(
    data: Optional[DynamicBaseModel] = None,
    _: Dict[str, str] = Depends(valid_access_token)
):
    return await get_conversation_history(data)

@router.post("/v1/ask/")
async def ask_ai_langchain(
    data: Optional[DynamicBaseModel] = None,
    _: Dict[str, str] = Depends(valid_access_token),
    semaphore: asyncio.Semaphore = Depends(limit_concurrency)
):
    try:
        return await ai_langchain_ask(data)
    finally:
        semaphore.release()

@router.get("/v1/test/")
async def test_ai_langchain(
    data: Optional[DynamicBaseModel] = None,
    _: Dict[str, str] = Depends(valid_access_token)
):
    return await ai_langchain_test(data)