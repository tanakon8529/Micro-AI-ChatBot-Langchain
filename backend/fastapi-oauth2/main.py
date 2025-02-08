
import logging
import sys

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from settings.configs import API_VERSION, API_PATH_FASTAPI_OAUTH2, API_DOC
from endpoint import api_router

from middlewares.redis_middleware import RedisMiddleware

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
    title="FastAPI OAuth2",
    description="FastAPI OAuth2",
    version=API_VERSION,
    docs_url=f"{API_PATH_FASTAPI_OAUTH2}{API_DOC}",
    redoc_url=None,
    openapi_url=f"{API_PATH_FASTAPI_OAUTH2}{API_DOC}/openapi.json"
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
app.include_router(api_router, prefix=API_PATH_FASTAPI_OAUTH2)