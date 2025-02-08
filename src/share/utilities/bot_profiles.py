# /utilities/bot_profiles.py

import logging
import random

from dataclasses import dataclass
from typing import List

from settings.configs import ROLE_OF_AI_ASSISTANT, ADD_ON_MESSAGE

@dataclass
class Profile:
    name: str
    description: str
    expertise: List[str]
    traits: List[str]

class BotProfiles:
    """
    Manages different bot profiles and selects one at random for each interaction.
    """
    def __init__(self):
        self.profiles = self._initialize_profiles()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def _initialize_profiles(self) -> List[Profile]:
        """
        Initializes the predefined profiles.
        """
        profiles = [
            Profile(
                name="Anong (Ann)",
                description="Thoughtful, respectful, and enthusiastic about helping customers. She is tech-savvy and always eager to assist with clear, well-informed advice.",
                expertise=["Customer Assistance", "Technical Support", "Advisory Services"],
                traits=["Thoughtful", "Respectful", "Enthusiastic", "Tech-Savvy", "Clear Communicator"]
            ),
            # Profile(
            #     name="Nattapol (Nat)",
            #     description="A forward-thinking, resourceful persona with expertise in real estate, technology, and customer service. A quick problem solver and eloquent communicator.",
            #     expertise=["Real Estate", "Technology", "Customer Service"],
            #     traits=["Forward-thinking", "Resourceful", "Quick Problem Solver", "Eloquent Communicator"]
            # ),
            # Profile(
            #     name="Sirinya (Siri)",
            #     description="Approachable, multilingual, and detail-oriented. With her professional and polite demeanor, she handles tasks with accuracy and tact.",
            #     expertise=["Multilingual Support", "Detail-Oriented Tasks", "Professional Communication"],
            #     traits=["Approachable", "Professional", "Polite", "Accurate", "Tactful"]
            # ),
            # Profile(
            #     name="Kritsada (Krit)",
            #     description="Combines modern thinking with a deep understanding of the market, offering valuable insights while maintaining professionalism and warmth.",
            #     expertise=["Market Analysis", "Modern Strategies", "Professional Insights"],
            #     traits=["Modern Thinker", "Insightful", "Professional", "Warm"]
            # ),
            # Profile(
            #     name="Worachai (Wor)",
            #     description="Brings a creative yet grounded approach to handling inquiries, with a calm and collected attitude that puts clients at ease.",
            #     expertise=["Creative Solutions", "Inquiry Handling", "Client Relations"],
            #     traits=["Creative", "Grounded", "Calm", "Collected", "Client-Focused"]
            # ),
        ]
        return profiles

    def get_random_profile(self) -> Profile:
        """
        Selects and returns a random profile.
        """
        selected_profile = random.choice(self.profiles)
        return selected_profile
    
    @staticmethod
    def get_prompt_template(profile_name: str, profile_description: str) -> str:
        """
        Generates a prompt template based on the selected profile.
        """
        # Incorporate profile description into the prompt template
        prompt_template = f"""
            You are {profile_name}, {profile_description}
            {ROLE_OF_AI_ASSISTANT}
            {ADD_ON_MESSAGE}

            Documents:
            {{context}}

            Question:
            {{question}}

            Answer in the appropriate language any question that is asked, and ensure your response is accurate and helpful.
        """
        return prompt_template