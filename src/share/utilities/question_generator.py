# /utilities/question_generator.py

import logging

from typing import List
from langchain.prompts import PromptTemplate
from settings.configs import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME, MODEL_ID_CLAUDE
from utilities.llm.aws_bedrock_claude import AWSBedrockClaude  # Updated import

class QuestionGenerator:
    def __init__(self):
        self.aws_access_key_id = AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = AWS_SECRET_ACCESS_KEY
        self.region_name = AWS_REGION_NAME
        self.model_id_claude = MODEL_ID_CLAUDE
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize AWSBedrockClaude
        try:
            self.llm = AWSBedrockClaude(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
                model_id=self.model_id_claude
            )
            self.logger.info("Initialized AWSBedrockClaude successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize AWSBedrockClaude: {e}")
            raise

        # Define a prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["number_of_questions", "topic"],
            template=(
                "Generate {number_of_questions} insightful and diverse questions on the topic of {topic}. "
                "Ensure that the questions are clear, concise, and cover various subtopics within the main topic."
            )
        )

    def generate(self, number_of_questions: int, topic: str = "general") -> List[str]:
        """
        Generates a specified number of questions based on the given topic using AWSBedrockClaude.

        Args:
            number_of_questions (int): The number of questions to generate.
            topic (str): The topic or category for question generation.

        Returns:
            List[str]: A list of generated questions.
        """
        try:
            self.logger.info(f"Generating {number_of_questions} questions on topic: '{topic}'")
            
            # Format the prompt with the given parameters
            prompt = self.prompt_template.format(number_of_questions=number_of_questions, topic=topic)
            
            # Call the LLM to generate the questions
            response = self.llm(prompt, temperature=0.7)  # Adjust temperature as needed
            
            # Extract and process the response
            questions_text = response.strip()
            # Split the questions assuming they are separated by newlines or numbered
            questions = self._parse_questions(questions_text, number_of_questions)
            
            self.logger.info(f"Generated {len(questions)} questions successfully.")
            return questions
        except Exception as e:
            self.logger.error(f"Error generating questions with AWSBedrockClaude: {e}")
            return []

    def _parse_questions(self, text: str, expected_count: int) -> List[str]:
        """
        Parses the generated text into individual questions.

        Args:
            text (str): The raw text output from the LLM.
            expected_count (int): The expected number of questions.

        Returns:
            List[str]: A list of cleaned questions.
        """
        import re

        # Attempt to split by lines
        lines = text.split('\n')
        questions = []
        for line in lines:
            # Remove numbering if present (e.g., "1. What is...")
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
            if cleaned.endswith('?'):
                questions.append(cleaned)
            if len(questions) >= expected_count:
                break
        
        # If not enough questions, attempt splitting by other delimiters
        if len(questions) < expected_count:
            # Split by question marks and re-add them
            split_questions = re.split(r'\?+', text)
            questions = [q.strip() + '?' for q in split_questions if q.strip()]
            questions = questions[:expected_count]
        
        return questions