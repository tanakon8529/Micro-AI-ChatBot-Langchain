# /utilities/chatbot_faiss_test.py

import logging
import asyncio

from typing import List, Dict, Any
from utilities.chatbot_faiss import ChatbotFAISS
from utilities.question_generator import QuestionGenerator


class ChatbotFAISSTest:
    """
    ChatbotFAISSTest is designed to test the ChatbotFAISS class by generating questions,
    processing them with both GPT and Claude agents, and returning structured responses.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.chatbot = ChatbotFAISS()
        self.qa_chains = self.chatbot.initialize_qa_chains()
        self.question_generator = QuestionGenerator()

    async def run_tests(self, number_of_questions: int, topic: str) -> tuple[bool, List[Dict[str, Any]]]:
        """
        Generates questions and processes them with both GPT and Claude agents.

        Args:
            number_of_questions (int): The number of questions to generate and test.
            topic (str): The topic for which questions are generated.

        Returns:
            tuple[bool, List[Dict[str, Any]]]: A tuple containing a success flag and the results or error details.
        """
        results = []

        try:
            # Step 1: Generate Questions
            self.logger.info(f"Generating {number_of_questions} questions on topic: '{topic}'")
            questions = self.question_generator.generate(number_of_questions, topic)
            if not questions:
                self.logger.error("No questions were generated.")
                return False, [{"msg": "failure", "data": {"result": {"error": "No questions were generated."}}}]
            
            self.logger.info(f"Generated {len(questions)} questions successfully.")
            
            # Step 2: Process Questions with Both Agents
            tasks = [self.process_question(idx + 1, question) for idx, question in enumerate(questions)]
            
            # Execute all tasks concurrently and append results
            results.extend(await asyncio.gather(*tasks))
            
            # Check for any failures
            for result in results:
                if "error" in result:
                    self.logger.error(f"Error in question {result['question_id']}: {result['error']}")
            
            return results
        
        except Exception as e:
            self.logger.error(f"Exception during run_tests: {e}")
            # In case of any unexpected failure, return failure with details
            response_error = {
                "topic": topic,
                "result": results,
                "error": str(e),
            }
            return [response_error]

    async def process_question(self, question_id: int, question: str) -> Dict[str, Any]:
        """
        Processes a single question using both GPT and Claude agents.

        Args:
            question_id (int): The identifier for the question (e.g., 1, 2).
            question (str): The question text.

        Returns:
            Dict[str, Any]: A dictionary with the processed results for the question.
        """
        result = {"question_id": question_id, "question": question, "responses": {}}

        try:
            # Process with GPT
            agent = "GPT"
            qa_chain = self.qa_chains[agent]
            self.logger.info(f"Processing question {question_id} with GPT.")
            gpt_response = await self.chatbot.process_single_question(question, qa_chain)
            result["responses"][agent] = gpt_response

            # Process with Claude
            agent = "CLAUDE"
            qa_chain = self.qa_chains[agent]
            self.logger.info(f"Processing question {question_id} with CLAUDE.")
            claude_response = await self.chatbot.process_single_question(question, qa_chain)
            result["responses"][agent] = claude_response

            self.logger.info(f"Received responses for question {question_id}.")

        except Exception as e:
            # In case of any exception, log the error and store it in the result
            self.logger.error(f"Error processing question {question_id}: {e}")
            result["error"] = str(e)

        return result
