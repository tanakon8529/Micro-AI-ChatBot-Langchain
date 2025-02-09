# apis/access/routes.py

from fastapi import APIRouter, Depends, Header, Request
from typing import Dict

from apis.access.mainmod import get_token
from core.auth import valid_access_token

router = APIRouter()

# Health check endpoint
@router.get("/v1/health/")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the OAuth service"""
    return {"status": "healthy", "service": "oauth"}

# Route to get access token
@router.post("/v1/token/")
async def generate_access_token(
    request: Request,
    client_id: str = Header(...),
    client_secret: str = Header(...)
) -> Dict[str, str]:
    return await get_token(client_id, client_secret, request)

# Protected route that requires authentication
@router.get("/v1/protected/")
async def protected_authen(
    auth: Dict[str, str] = Depends(valid_access_token)
) -> Dict[str, str]:
    return auth