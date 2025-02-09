import pytest
import httpx
import os
import pytest_asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
BASE_URL_OAUTH = os.getenv('BASE_URL_OAUTH', 'http://localhost:8001/oauth/v1')
BASE_URL_CHAT = os.getenv('BASE_URL_CHAT', 'http://localhost:8002/langgpt/v1')

@pytest_asyncio.fixture
async def client():
    client = httpx.AsyncClient()
    yield client
    await client.aclose()

@pytest_asyncio.fixture
async def auth_token(client):
    """Get authentication token"""
    response = await client.post(
        f"{BASE_URL_OAUTH}/token/",
        headers={
            "client-id": os.getenv("CLIENT_ID", "ai_develop_01"),
            "client-secret": os.getenv("CLIENT_SECRET", "abc123")
        }
    )
    if response.status_code != 200:
        logger.error(f"Failed to get auth token. Status: {response.status_code}, Response: {response.text}")
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_oauth_health_check(client):
    """Test OAuth service health check endpoint"""
    response = await client.get(f"{BASE_URL_OAUTH}/health/")
    if response.status_code != 200:
        logger.error(f"OAuth health check failed. Status: {response.status_code}, Response: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "oauth"

@pytest.mark.asyncio
async def test_chat_health_check(client):
    """Test AI Chat service health check endpoint"""
    response = await client.get(f"{BASE_URL_CHAT}/health/")
    if response.status_code != 200:
        logger.error(f"Chat health check failed. Status: {response.status_code}, Response: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-chat"

@pytest.mark.asyncio
async def test_oauth_protected_endpoint(client, auth_token):
    """Test protected endpoint with valid token"""
    response = await client.get(
        f"{BASE_URL_OAUTH}/protected/",
        headers={"token": f"Bearer {auth_token}"}
    )
    if response.status_code != 200:
        logger.error(f"Protected endpoint test failed. Status: {response.status_code}, Response: {response.text}")
    assert response.status_code == 200
    assert "detail" in response.json()
    assert response.json()["detail"] == "Valid access token!"

@pytest.mark.asyncio
async def test_chat_endpoint(client, auth_token):
    """Test chat endpoint"""
    payload = {
        "user_id": "dev_test007",
        "topic_id": "001",
        "question": "What is your name?",
        "model": "GPT"
    }
    logger.info(f"Sending chat request with payload: {payload}")
    response = await client.post(
        f"{BASE_URL_CHAT}/ask/",
        headers={"token": f"Bearer {auth_token}"},
        json=payload
    )
    if response.status_code != 200:
        logger.error(f"Chat endpoint test failed. Status: {response.status_code}, Response: {response.text}")
        logger.error(f"Request headers: {response.request.headers}")
        logger.error(f"Request body: {response.request.content}")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "answer" in data["data"]

@pytest.mark.asyncio
async def test_conversation_endpoint(client, auth_token):
    """Test conversation history endpoint"""
    # First, create a conversation by asking a question
    ask_payload = {
        "user_id": "dev_test007",
        "topic_id": "001",
        "question": "What is your name?",
        "model": "GPT"
    }
    logger.info(f"Creating conversation with payload: {ask_payload}")
    ask_response = await client.post(
        f"{BASE_URL_CHAT}/ask/",
        headers={"token": f"Bearer {auth_token}"},
        json=ask_payload
    )
    if ask_response.status_code != 200:
        logger.error(f"Failed to create conversation. Status: {ask_response.status_code}, Response: {ask_response.text}")
        logger.error(f"Request headers: {ask_response.request.headers}")
        logger.error(f"Request body: {ask_response.request.content}")
    
    # Then get the conversation history
    payload = {
        "user_id": "dev_test007",
        "topic_id": "001"
    }
    logger.info(f"Getting conversation history with payload: {payload}")
    response = await client.post(
        f"{BASE_URL_CHAT}/conversation/",
        headers={"token": f"Bearer {auth_token}"},
        json=payload
    )
    if response.status_code != 200:
        logger.error(f"Conversation history test failed. Status: {response.status_code}, Response: {response.text}")
        logger.error(f"Request headers: {response.request.headers}")
        logger.error(f"Request body: {response.request.content}")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
