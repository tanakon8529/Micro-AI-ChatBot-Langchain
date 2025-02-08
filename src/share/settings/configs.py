
import os
from dotenv import load_dotenv

from settings.role_of_ai_assistant import settings_ai

load_dotenv("./.env")

#### MICROSERVICE ####
MICROSERVICE_NAME_FASTAPI_OAUTH2 = "fastapi-oauth2"
MICROSERVICE_NAME_FASTAPI_AI_CHAT = "fastapi-ai-chat"

def set_microservice_name_by_api_path(api_path):
    if api_path == API_PATH_FASTAPI_OAUTH2:
        return MICROSERVICE_NAME_FASTAPI_OAUTH2
    elif api_path == API_PATH_FASTAPI_AI_CHAT:
        return MICROSERVICE_NAME_FASTAPI_AI_CHAT
    else:
        return "Unknown"
    
API_VERSION = os.environ["API_VERSION"]
API_PATH_FASTAPI_OAUTH2 = os.environ["API_PATH_FASTAPI_OAUTH2"]
API_PATH_FASTAPI_AI_CHAT = os.environ["API_PATH_FASTAPI_AI_CHAT"]
API_DOC = os.environ["API_DOC"]
REQUEST_QUEUE_SIZE = int(os.environ["REQUEST_QUEUE_SIZE"]) or 10 # if not set, default to 10
HOST = os.environ["HOST"]

PORT_FASTAPI_OAUTH2 = os.environ["PORT_FASTAPI_OAUTH2"]
PORT_FASTAPI_AI_CHAT = os.environ["PORT_FASTAPI_AI_CHAT"]

#### AUTHENTICATION ####
USERNAME_ADMIN = os.environ["USERNAME_ADMIN"]
PASSWORD_ADMIN = os.environ["PASSWORD_ADMIN"]

#### REDIS ####
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]

#### AI Settings ####
MAX_TOKENS = 10000
TEMPERATURE = os.environ["TEMPERATURE"]
BUILD_VECTOR_STORE = os.environ["BUILD_VECTOR_STORE"]
CLEAR_CACHE = os.environ["CLEAR_CACHE"]
USER_IDS = ["dev_test007", "dev_test006"]

#### AI Chat ####
ROLE_OF_AI_ASSISTANT = settings_ai.get("role_of_ai_assistant", "You are an AI Assistant.")
ADD_ON_MESSAGE = settings_ai.get("add_on_message", "Use the following documents to answer the question.")

#### OpenAI ####
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL_ID_GPT = os.environ["MODEL_ID_GPT"]
PERSIST_DIRECTORY = os.environ["PERSIST_DIRECTORY"]
PDF_DIRECTORY_PATH = os.environ["PDF_DIRECTORY_PATH"]

#### AWS ####
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_REGION_NAME = os.environ["AWS_REGION_NAME"]
MODEL_ID_CLAUDE = os.environ["MODEL_ID_CLAUDE"]