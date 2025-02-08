import logging

from typing import Dict, Any, List
from fastapi import HTTPException
from datetime import datetime

from core.models import DynamicBaseModel

from utilities.validation_manager import validate_user
from utilities.chatbot_faiss_test import ChatbotFAISSTest

from instances import app_state

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def query_conversation_history(data: DynamicBaseModel) -> Dict[str, Any]:
    conversation_manager = app_state.conversation_manager
    key_required = ['user_id', 'topic_id']
    if not all(key in data.dict() for key in key_required):
        logger.error("Missing required field(s).")
        raise HTTPException(status_code=400, detail="Missing required field(s).")
    
    user_id = data.user_id
    topic_id = data.topic_id
    if not user_id:
        logger.error("Received empty user_id.")
        raise HTTPException(status_code=400, detail="User ID cannot be empty.")
    if not topic_id:
        logger.error("Received empty topic_id.")
        raise HTTPException(status_code=400, detail="Topic ID cannot be empty.")
    
    # Validate user_id and topic_id
    if not validate_user(user_id):
        log_controller.log_error(f"Invalid user_id: {user_id}", 'query_conversation_history')
        raise HTTPException(status_code=400, detail="Invalid user_id or topic_id.")
    
    conversation_history = await conversation_manager.get_conversation_history(user_id, topic_id)
    
    return {
        "msg": "success",
        "data": {
            "conversation_history": conversation_history
        }
    }

async def ask_langchain_models(data: DynamicBaseModel) -> Dict[str, Any]:
    # Retrieve instances from AppState
    conversation_manager = app_state.conversation_manager
    chat_bot = app_state.chat_bot

    key_required = ['user_id', 'topic_id', 'question', 'model']
    if not all(key in data.dict() for key in key_required):
        logger.error("Missing required field(s).")
        raise HTTPException(status_code=400, detail="Missing required field(s).")
    
    user_id = data.user_id
    topic_id = data.topic_id
    question = data.question.strip() if data.question else None
    model_choice = data.model  # "GPT" or "CLAUDE"
    models = ["GPT", "CLAUDE"]
    
    # Validation
    if not user_id:
        logger.error("Received empty user_id.")
        raise HTTPException(status_code=400, detail="User ID cannot be empty.")
    if not topic_id:
        logger.error("Received empty topic_id.")
        raise HTTPException(status_code=400, detail="Topic ID cannot be empty.")
    if not question:
        logger.error("Received empty question.")
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if model_choice not in models:
        logger.error(f"Invalid model: {model_choice}.")
        raise HTTPException(status_code=400, detail="Invalid model. Must be 'GPT' or 'CLAUDE'.")
    
    # Validate user_id
    if not validate_user(user_id):
        logger.error(f"Invalid user_id: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user_id or topic_id.")

    # Retrieve conversation history
    conversation_history = await conversation_manager.get_conversation_history(user_id, topic_id)

    # Construct prompt with conversation history
    user_query = construct_prompt(conversation_history, question)
    
    # Process the query with the AI model using the constructed prompt
    answer_response = await chat_bot.process_query(user_id, topic_id, user_query, model_choice=model_choice)
    if "error_code" in answer_response:
        logger.error(f"Error from chat_bot: {answer_response.get('msg')}")
        raise HTTPException(status_code=400, detail=answer_response.get('msg', 'Bad request.'))

    data_field = answer_response.get("data", {})
    answer = data_field.get("answer")
    type_res = data_field.get("type_res")

    if not answer:
        logger.error("No answer returned from chat_bot.")
        raise HTTPException(status_code=500, detail="Failed to retrieve answer.")

    # Store user question and bot answer in Redis
    await conversation_manager.add_message(user_id, topic_id, 'user', question)
    await conversation_manager.add_message(user_id, topic_id, 'bot', answer)

    # Update session metadata (e.g., last active time)
    current_timestamp = datetime.utcnow().isoformat()
    await conversation_manager.update_session_metadata(user_id, topic_id, 'last_active', current_timestamp)

    result = {
        "msg": "success",
        "data": {
            "answer": answer,
            "type_res": type_res
        }
    }
    return result

def construct_prompt(conversation_history: List[Dict], new_question: str) -> str:
    """
    Constructs a prompt including the conversation history and the new question.
    Ensures that the format is clear and avoids redundancy.
    """
    formatted_history = []
    for message in conversation_history:
        sender = message.get('sender')
        content = message.get('message')
        if sender and content:
            if sender.lower() == 'user':
                formatted_history.append(f"User: {content}")
            elif sender.lower() == 'bot':
                formatted_history.append(f"Bot: {content}")
    # Join the conversation history with newline characters
    prompt = "\n".join(formatted_history)
    # Append the new user question
    prompt += f"\nUser: {new_question}\nBot:"
    return prompt

async def test_chatbot_faiss(data: DynamicBaseModel) -> Dict[str, Any]:
    try:
        chat_bot = app_state.chat_bot
        tester = ChatbotFAISSTest(chatbot=chat_bot)
        number_of_questions = 2
        if data and hasattr(data, "input_number_qa"):
            number_of_questions = data.input_number_qa
        topic = "AP Thailand, บริษัท เอพี (ไทยแลนด์) จำกัด"
        test_results = await tester.run_tests(number_of_questions, topic)
        
        return {
            "msg": "success",
            "data": {
                "result": test_results
            }
        }
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail='Internal server error: {}'.format(e))