import pytest
import redis.asyncio as redis
import pytest_asyncio
import numpy as np
from scipy.sparse import csr_matrix

from unittest.mock import AsyncMock, patch, MagicMock
from cache_controller import CacheAnswer

@pytest_asyncio.fixture
async def cache_answer():
    redis_client = AsyncMock(spec=redis.Redis)
    return CacheAnswer(redis_client)

@pytest.mark.asyncio
async def test_check_cache_with_similar_question(cache_answer):
    # Mock data
    test_question = "What is the capital of France?"
    cached_question = "What's the capital of France?"
    cached_answer = "The capital of France is Paris."
    
    # Mock redis client methods
    cache_answer.redis_client.hgetall = AsyncMock(return_value={cached_question: cached_answer})
    cache_answer.redis_client.hget = AsyncMock(return_value=cached_answer)
    
    # Mock vectorizer
    cache_answer.vectorizer = MagicMock()
    cache_answer.vectorizer.fit_transform = MagicMock(return_value=csr_matrix([[1, 0, 0]]))
    cache_answer.vectorizer.transform = MagicMock(return_value=csr_matrix([[1, 0, 0]]))
    
    # Set up cached questions and vectors
    cache_answer.cached_questions = [cached_question]
    cache_answer.cached_vectors = csr_matrix([[1, 0, 0]])
    
    # Test the cache check
    result = await cache_answer.check_cache(test_question)
    assert result[0] == [cached_answer]
    assert result[1] == "cache"

@pytest.mark.asyncio
async def test_check_cache_with_different_question(cache_answer):
    # Mock data
    test_question = "What is the capital of Spain?"
    cached_question = "What is the capital of France?"
    cached_answer = "The capital of France is Paris."
    
    # Mock redis client methods
    cache_answer.redis_client.hgetall = AsyncMock(return_value={cached_question: cached_answer})
    
    # Mock vectorizer
    cache_answer.vectorizer = MagicMock()
    cache_answer.vectorizer.fit_transform = MagicMock(return_value=csr_matrix([[1, 0, 0]]))
    cache_answer.vectorizer.transform = MagicMock(return_value=csr_matrix([[0, 1, 0]]))
    
    # Set up cached questions and vectors
    cache_answer.cached_questions = [cached_question]
    cache_answer.cached_vectors = csr_matrix([[1, 0, 0]])
    
    # Test the cache check
    result = await cache_answer.check_cache(test_question)
    assert result == (None, None)

@pytest.mark.asyncio
async def test_add_to_cache(cache_answer):
    # Test data
    question = "What is the capital of Italy?"
    answer = "The capital of Italy is Rome."
    
    # Mock redis client methods
    cache_answer.redis_client.hset = AsyncMock()
    cache_answer.redis_client.hgetall = AsyncMock(return_value={})
    
    # Test adding to cache
    await cache_answer.add_to_cache(question, answer)
    cache_answer.redis_client.hset.assert_called_once_with('cache_questions', question, answer)
