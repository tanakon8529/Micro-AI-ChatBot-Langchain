# utilities/validation_manager.py

from settings.configs import USER_IDS

def validate_user(user_id: str) -> bool:
    """
    Validates the user_id and topic_id.
    Add your custom validation logic here.
    For example, check if they are non-empty and conform to expected formats.
    """
    if not user_id or user_id not in USER_IDS:
        return False
    # Add more validation rules as needed
    return True