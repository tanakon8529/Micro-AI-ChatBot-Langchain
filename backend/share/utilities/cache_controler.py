import logging
import redis.asyncio as redis
import numpy as np

from typing import Dict, List, Optional, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CacheAnswer:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.vectorizer = TfidfVectorizer()
        self.cached_questions = []
        self.cached_vectors = None
        
    async def _update_vectorizer(self):
        """Update the TF-IDF vectorizer with current questions"""
        try:
            # Get all questions from Redis
            all_questions = await self.redis_client.hgetall('cache_questions')
            if all_questions:
                # Convert binary keys to strings if decode_responses is False
                self.cached_questions = [k.decode('utf-8') if isinstance(k, bytes) else k 
                                      for k in all_questions.keys()]
                self.cached_vectors = self.vectorizer.fit_transform(self.cached_questions)
                self.logger.info(f"Updated vectorizer with {len(self.cached_questions)} questions")
            else:
                self.cached_questions = []
                self.cached_vectors = None
                self.logger.info("No questions in cache to update vectorizer")
        except Exception as e:
            self.logger.error(f"Error updating vectorizer: {str(e)}")
            self.cached_questions = []
            self.cached_vectors = None

    def _calculate_similarity(self, query_vector: np.ndarray, cached_vectors: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between query and cached vectors"""
        return cosine_similarity(query_vector.reshape(1, -1), cached_vectors)[0]

    def _preprocess_question(self, question: str) -> str:
        """Preprocess question by removing common prefixes and normalizing"""
        # Remove common prefixes
        prefixes = ["User:", "Bot:", "User: ", "Bot: "]
        cleaned = question
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        return cleaned.strip()

    async def check_cache(self, question: str) -> Tuple[Optional[List[str]], Optional[str]]:
        """Check cache for similar questions and return answers with status"""
        try:
            # Preprocess the question
            cleaned_question = self._preprocess_question(question)
            self.logger.info(f"check_cache | Searching for question: {cleaned_question}")
            
            # Update vectorizer with current cache
            await self._update_vectorizer()
            
            # If no cached questions, return None, None
            if not self.cached_questions:
                self.logger.info("check_cache | No cached questions available")
                return None, None
            
            # Calculate similarity with existing questions
            query_vector = self.vectorizer.transform([cleaned_question])
            similarities = self._calculate_similarity(query_vector.toarray()[0], self.cached_vectors.toarray())
            max_similarity = np.max(similarities)
            best_match_idx = np.argmax(similarities)
            best_match_question = self.cached_questions[best_match_idx]
            
            self.logger.info(f"check_cache | Max similarity: {max_similarity}")
            self.logger.info(f"check_cache | Best match question: {best_match_question}")
            self.logger.info(f"check_cache | Current question: {cleaned_question}")
            
            # If exact match or very high similarity (>=0.98), return the cached answer
            if max_similarity >= 0.98 or cleaned_question.lower() == self._preprocess_question(best_match_question).lower():
                answer = await self.redis_client.hget('cache_questions', best_match_question)
                if answer:
                    # Decode answer if it's bytes
                    if isinstance(answer, bytes):
                        answer = answer.decode('utf-8')
                    self.logger.info("check_cache | Found matching cached answer")
                    return [answer], "cache"
            
            self.logger.info("check_cache | No matching answer found")
            return None, None

        except Exception as e:
            self.logger.error(f"Error checking cache: {str(e)}")
            return None, None

    async def add_to_cache(self, question: str, answer: str):
        """Add question and answer to cache"""
        try:
            # Preprocess the question
            cleaned_question = self._preprocess_question(question)
            self.logger.info(f"add_to_cache | Adding new Q&A pair. Question length: {len(cleaned_question)}, Answer length: {len(answer)}")
            
            # Update vectorizer to get current cache state
            await self._update_vectorizer()
            
            # Check similarity with existing questions
            if self.cached_vectors is not None and self.cached_questions:
                query_vector = self.vectorizer.transform([cleaned_question])
                similarities = self._calculate_similarity(query_vector.toarray()[0], self.cached_vectors.toarray())
                max_similarity = np.max(similarities)
                
                if max_similarity >= 0.98:
                    self.logger.info("add_to_cache | Similar question already exists in cache")
                    return
            
            # Add new question-answer pair to cache
            await self.redis_client.hset('cache_questions', cleaned_question, answer)
            self.logger.info("add_to_cache | Added new question-answer pair to cache")
            
        except Exception as e:
            self.logger.error(f"Error adding to cache: {str(e)}")

    def remove_cache_entry(self, doc_id: str):
        """Remove a specific cache entry"""
        try:
            self.redis_client.hdel('cache_questions', doc_id)
            self.logger.info(f"Removed cache entry with doc_id: {doc_id}")
        except Exception as e:
            self.logger.error(f"Error removing cache entry {doc_id}: {e}")

    async def clear_cache(self):
        """Clear all cache entries"""
        try:
            await self.redis_client.delete('cache_questions')
            self.logger.info("Cleared Redis cache.")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")