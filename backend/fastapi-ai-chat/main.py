# main.py

import logging
import sys

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from settings.configs import API_VERSION, API_PATH_FASTAPI_AI_CHAT, API_DOC
from endpoint import api_router

from utilities.conversation_manager import ConversationManager
from utilities.chatbot_faiss import ChatbotFAISS

from middlewares.redis_middleware import RedisMiddleware
from instances import app_state  # Import AppState

# Configure logging StreamHandler Log to console, only log [error, info]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(stream=sys.stdout)  # Log to console
    ]
)

# Disable all loggers by default
logging.getLogger().setLevel(logging.WARNING)

# Only enable logging for your application
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.INFO)

app = FastAPI(
    title="FastAPI Ai-Chat",
    description="FastAPI Ai-Chat",
    version=API_VERSION,
    docs_url=f"{API_PATH_FASTAPI_AI_CHAT}{API_DOC}",
    redoc_url=None,
    openapi_url=f"{API_PATH_FASTAPI_AI_CHAT}{API_DOC}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add Redis Middleware
app.add_middleware(RedisMiddleware)
app.include_router(api_router, prefix=API_PATH_FASTAPI_AI_CHAT)

# Initialize global instances via AppState
app_state.conversation_manager = ConversationManager()
app_state.chat_bot = None  # Will be initialized asynchronously

@app.on_event("startup")
async def startup_event():
    # Initialize Redis client, ConversationManager
    await app_state.conversation_manager.init_redis()
    # Clear cache
    await app_state.conversation_manager.clear_cache()

    # Initialize ChatbotFAISS
    app_state.chat_bot = await ChatbotFAISS.create(redis_client=app_state.conversation_manager.redis_client)

@app.on_event("shutdown")
async def shutdown_event():
    await app_state.conversation_manager.redis_client.close()
    await app_state.chat_bot.redis_client.close()