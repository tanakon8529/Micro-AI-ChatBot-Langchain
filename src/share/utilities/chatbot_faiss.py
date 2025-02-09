# utilities/chatbot_faiss.py

import os
import time
import logging
import asyncio
import numpy as np
import faiss
import uuid
import random
import json
import openai

from typing import List
from datetime import datetime, timedelta
from redis.commands.search.query import Query
from redis.commands.search.field import TextField, NumericField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition

from difflib import SequenceMatcher
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from settings.configs import OPENAI_API_KEY, MODEL_ID_GPT, MODEL_ID_CLAUDE, PERSIST_DIRECTORY, \
                                PDF_DIRECTORY_PATH, TEMPERATURE, BUILD_VECTOR_STORE, \
                                CLEAR_CACHE, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, \
                                AWS_REGION_NAME

# Load Agents
from utilities.llm.openai_llm import OpenAIChatLLM
from utilities.llm.aws_bedrock_claude import AWSBedrockClaude
from utilities.bot_profiles import BotProfiles
from utilities.cache_controller import CacheAnswer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SimpleOpenAIEmbeddings(Embeddings):
    """Simple embeddings class that uses OpenAI API directly."""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "text-embedding-ada-002"
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        if not texts:
            return []
        try:
            batch_size = 100
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            embeddings = np.array(all_embeddings).astype("float32")
            faiss.normalize_L2(embeddings)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error in embed_documents: {str(e)}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Get embeddings for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            # Extract the embedding from the response
            embedding = response.data[0].embedding
            embedding = np.array(embedding).astype("float32")
            faiss.normalize_L2(embedding.reshape(1, -1))
            return embedding.flatten().tolist()
        except Exception as e:
            logger.error(f"Error in embed_query: {str(e)}")
            raise

class ChatbotFAISS:
    """
    ChatbotFAISS processes user queries using FAISS for vector similarity search and caching.
    Now handles conversations based on user_id and topic_id.
    Supports multiple AI models: GPT and Claude.
    """
    def __init__(self, redis_client):
        # Initialize variables that don't require async
        self.lock = asyncio.Lock()
        self.persist_directory = PERSIST_DIRECTORY
        self.pdf_directory_path = PDF_DIRECTORY_PATH
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.MODEL_ID_GPT = MODEL_ID_GPT
        self.MODEL_ID_CLAUDE = MODEL_ID_CLAUDE
        self.AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
        self.AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
        self.AWS_REGION_NAME = AWS_REGION_NAME
        self.TEMPERATURE = float(TEMPERATURE) if TEMPERATURE else 0.3
        if not all([self.persist_directory, self.pdf_directory_path, self.OPENAI_API_KEY, self.MODEL_ID_GPT, self.MODEL_ID_CLAUDE,
                    self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY, self.AWS_REGION_NAME]):
            logger.error("Required environment variables are not set.")
            raise ValueError("Required environment variables are not set.")
        
        # Initialize Redis client and cache controller
        self.redis_client = redis_client
        self.cache_controller = CacheAnswer(redis_client)
        self.bot_profiles = BotProfiles()
        self.profile = self.bot_profiles.get_random_profile()

        try:
            logger.info("STEP 1 : Initializing ChatbotFAISS... | 0%/100%")
            # Initialize embeddings
            self.embeddings = self.initialize_embeddings()
            logger.info("STEP 2 : OpenAI Embeddings Initialized... | 20%/100%")
            # Initialize vector store
            self.vector_store = self.initialize_vector_store()
            logger.info("STEP 3 : FAISS Vector Store Initialized... | 60%/100%")
            # Initialize QA chains
            self.qa_chains = self.initialize_qa_chains()
            logger.info("STEP 4 : QA Chains Initialized... | 80%/100%")

            logger.info("STEP 5 : ChatbotFAISS Initialization Complete... | 100%/100%")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    @classmethod
    async def create(cls, redis_client):
        """
        Factory method to initialize ChatbotFAISS with necessary async resources.
        """
        try:
            # Initialize ChatbotFAISS
            chatbot = cls(redis_client=redis_client)
            if BUILD_VECTOR_STORE == "True":
                chatbot.rebuild_vector_store()
                await chatbot.clear_cache()
            if CLEAR_CACHE == "True":
                await chatbot.clear_cache()

            return chatbot
        except Exception as e:
            logger.error(f"Error during ChatbotFAISS creation: {e}")
            raise

    def log_time(self, topic, description, start_time, end_time):
        """Logs the time used for a particular operation."""
        time_used = end_time - start_time
        logger.info(f"{topic} | {description} | Time Used: {time_used:.2f} seconds")

    def initialize_redis_index(self):
        try:
            # Check if RediSearch module is available
            try:
                self.redisearch_client.info()
                logger.info("Redis index 'cache_index' already exists.")
                return
            except Exception as e:
                if "unknown command" in str(e).lower():
                    logger.warning("RediSearch module not available. Cache functionality will be limited.")
                    return
                logger.info("Creating Redis index 'cache_index'.")

            # Create index only if RediSearch is available
            embedding_field = VectorField("embedding",
                                        "FLAT", {
                                            "TYPE": "FLOAT32",
                                            "DIM": self.embedding_dimension,
                                            "DISTANCE_METRIC": "COSINE"
                                        })

            question_field = TextField("question")
            answers_field = TextField("answers")
            timestamp_field = NumericField("timestamp", sortable=True)

            try:
                self.redisearch_client.create_index(
                    fields=[embedding_field, question_field, answers_field, timestamp_field],
                    definition=IndexDefinition(prefix=['cache:'])
                )
            except Exception as e:
                logger.warning(f"Failed to create Redis index: {e}")

        except Exception as e:
            logger.error(f"Error in initialize_redis_index: {e}")

    def initialize_embeddings(self):
        """Initialize the embeddings model."""
        topic = "Embeddings Initialization"
        description = "Initializing OpenAI embeddings"
        start_time = time.time()

        try:
            embeddings = SimpleOpenAIEmbeddings(api_key=self.OPENAI_API_KEY)
            # Test embeddings
            test_embedding = embeddings.embed_query("test")
            if not isinstance(test_embedding, list) or len(test_embedding) == 0:
                raise ValueError("Failed to generate test embedding")
            return embeddings
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
        finally:
            end_time = time.time()
            self.log_time(topic, description, start_time, end_time)

    def load_and_split_pdfs(self):
        topic = "PDF Processing"
        description = "Loading and splitting multiple PDFs into chunks"
        start_time = time.time()

        try:
            logger.info(f"Loading and splitting PDFs from directory: {self.pdf_directory_path}")
            full_directory_path = os.path.abspath(self.pdf_directory_path)
            logger.info(f"Full Directory Path: {full_directory_path}")

            if not os.path.isdir(full_directory_path):
                logger.error(f"PDF directory does not exist at path: {full_directory_path}")
                raise NotADirectoryError(f"PDF directory does not exist at path: {full_directory_path}")

            pdf_files = [file for file in os.listdir(full_directory_path) if file.lower().endswith('.pdf')]
            if not pdf_files:
                logger.error(f"No PDF files found in directory: {full_directory_path}")
                raise FileNotFoundError(f"No PDF files found in directory: {full_directory_path}")

            all_chunks = []
            for pdf_file in pdf_files:
                pdf_path = os.path.join(full_directory_path, pdf_file)
                logger.info(f"Loading PDF: {pdf_path}")
                loader = PyPDFLoader(pdf_path)
                documents = loader.load()

                if not documents:
                    logger.error(f"No documents loaded from PDF: {pdf_path}")
                    continue  # Skip this PDF and continue with others

                text_splitter = CharacterTextSplitter(
                    separator="\n",
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                chunks = text_splitter.split_documents(documents)
                all_chunks.extend(chunks)
                logger.info(f"Loaded and split PDF '{pdf_file}' into {len(chunks)} chunks.")

            if not all_chunks:
                logger.error("No chunks were created from any PDF files.")
                raise ValueError("No chunks were created from any PDF files.")

            logger.info(f"Total chunks created from all PDFs: {len(all_chunks)}")

        except Exception as e:
            logger.error(f"Error loading and splitting PDFs: {e}")
            raise  # Re-raise the exception to prevent proceeding with invalid chunks

        end_time = time.time()
        self.log_time(topic, description, start_time, end_time)
        return all_chunks

    def initialize_vector_store(self):
        topic = "FAISS Vector Store"
        description = "Creating or loading FAISS vector store"
        start_time = time.time()

        index_file = os.path.join(self.persist_directory, "index.faiss")

        try:
            if os.path.exists(index_file):
                logger.info("Loading existing FAISS vector store.")
                vector_store = FAISS.load_local(
                    folder_path=self.persist_directory,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Loaded existing FAISS vector store.")
            else:
                logger.info("Creating new FAISS vector store.")
                document_chunks = self.load_and_split_pdfs()
                vector_store = FAISS.from_documents(
                    documents=document_chunks,
                    embedding=self.embeddings
                )
                vector_store.save_local(self.persist_directory)
                logger.info(f"Created new FAISS vector store | Persisted at: {self.persist_directory}")
                
            return vector_store
        except Exception as e:
            logger.error(f"Error initializing FAISS vector store: {e}")
            raise  # Re-raise to prevent proceeding with invalid vector_store
        finally:
            end_time = time.time()
            self.log_time(topic, description, start_time, end_time)

    def initialize_qa_chains(self):
        """
        Initializes QA chains for both GPT and Claude models.
        """
        qa_chains = {}
        topic = "QA Chain Initialization"
        description = "Initializing RetrievalQA chain with AI Assistant role"
        start_time = time.time()

        # Incorporate profile description into the prompt template
        prompt_template = self.bot_profiles.get_prompt_template(self.profile.name, self.profile.description)
        if not prompt_template:
            logger.error(f"Prompt template not set : {prompt_template}")
            raise ValueError("Prompt template not set.")

        # Initialize GPT QA Chain
        try:
            PROMPT = PromptTemplate(
                input_variables=["context", "question"],
                template=prompt_template
            )

            llm_gpt = OpenAIChatLLM(
                openai_api_key=self.OPENAI_API_KEY,
                model_name=self.MODEL_ID_GPT,
                temperature=self.TEMPERATURE
            )

            qa_chain_gpt = RetrievalQA.from_chain_type(
                llm=llm_gpt,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
            qa_chains["GPT"] = qa_chain_gpt
            logger.info("Initialized GPT RetrievalQA chain.")
        except Exception as e:
            logger.error(f"Error initializing GPT QA chain: {e}")
            raise  # Ensures that initialization fails if GPT chain isn't set up correctly

        # Initialize Claude QA Chain
        try:
            PROMPT = PromptTemplate(
                input_variables=["context", "question"],
                template=prompt_template
            )

            llm_claude = AWSBedrockClaude(
                aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                region_name=self.AWS_REGION_NAME,
                model_id=self.MODEL_ID_CLAUDE
            )

            qa_chain_claude = RetrievalQA.from_chain_type(
                llm=llm_claude,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
            qa_chains["CLAUDE"] = qa_chain_claude
            logger.info("Initialized Claude RetrievalQA chain.")
        except Exception as e:
            logger.error(f"Error initializing Claude QA chain: {e}")
            raise  # Re-raise to prevent proceeding with invalid qa_chain
        finally:
            end_time = time.time()
            self.log_time(topic, description, start_time, end_time)
        return qa_chains

    def are_questions_similar(self, question1: str, question2: str, percent_similar: float = 0.8) -> bool:
        """
        Determines if two questions are similar based on a specified threshold.
        """
        ratio = SequenceMatcher(None, question1.strip(), question2.strip()).ratio()
        return ratio > percent_similar  # Threshold set to 80%

    async def check_cache(self, question: str):
        try:
            percent_similar = 0.8  # Set similarity threshold to 80%

            # Skip cache check if RediSearch is not available
            try:
                return await self.cache_controller.check_cache(question)
            except Exception as e:
                logger.error(f"Error checking cache: {e}", "check_cache")
                return None, None

        except Exception as e:
            logger.error(f"Error checking cache: {e}", "check_cache")
            return None, None

    async def add_to_cache(self, question: str, answer: str):
        try:
            await self.cache_controller.add_to_cache(question, answer)
        except Exception as e:
            logger.error(f"Error adding to cache: {e}", "add_to_cache")

    def remove_cache_entry(self, doc_id):
        try:
            self.cache_controller.remove_cache_entry(doc_id)
        except Exception as e:
            logger.error(f"Error removing cache entry {doc_id}: {e}")

    async def clear_cache(self):
        try:
            await self.cache_controller.clear_cache()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def rebuild_vector_store(self):
        # Delete existing index file if exists
        index_file = os.path.join(self.persist_directory, "index.faiss")
        index_pkl_file = os.path.join(self.persist_directory, "index.pkl")
        try:
            if os.path.exists(index_file):
                os.remove(index_file)
                logger.info(f"Deleted existing FAISS index file: {index_file}")
            if os.path.exists(index_pkl_file):
                os.remove(index_pkl_file)
                logger.info(f"Deleted existing FAISS index pickle file: {index_pkl_file}")
        except Exception as e:
            logger.error(f"Error deleting existing FAISS index file: {e}")
        
        # Re-initialize vector store
        self.vector_store = self.initialize_vector_store()
        logger.info("Rebuilt FAISS vector store.")

    async def process_single_question(self, question: str, qa_chain: RetrievalQA) -> dict:
        """
        Processes a single question using the specified QA chain.
        """
        try:
            # Check cache first
            cached_answers, cache_status = await self.check_cache(question)
            if cache_status == "cache" and cached_answers:
                return {
                    "answer": cached_answers[0],  # Return the random answer from cache
                    "type_res": "cache"
                }
            
            # If cache needs more answers or cache miss, generate a new answer
            response = await asyncio.to_thread(qa_chain.invoke, question)
            response_data = response.get("result", None)

            if not isinstance(response_data, str):
                logger.error(f"Unexpected response format: {response}")
                return {"error_code": "03", "msg": "Unexpected response format from QA chain."}

            answer = response_data.strip()

            # Add the new Q&A to cache
            await self.add_to_cache(question, answer)

            return {
                "answer": answer,
                "type_res": "generate"
            }
        except Exception as e:
            logger.error(f"Error processing single question: {e}")
            return {"error_code": "04", "msg": f"Error processing question: {str(e)}"}

    def test_similarity_search(self, query: str):
        """Test similarity search functionality."""
        try:
            # Get embedding for the query using embed_query method
            embedding = self.embeddings.embed_query(query)
            embedding = np.array(embedding).astype('float32')
            faiss.normalize_L2(embedding.reshape(1, -1))
            D, I = self.vector_store.index.search(embedding.reshape(1, -1), k=5)
            return D, I
        except Exception as e:
            logger.error(f"Error in test_similarity_search: {str(e)}")
            raise

    def get_vector_store_info(self) -> str:
        """Get information about the contents of the vector store"""
        try:
            if not hasattr(self, 'vector_store') or not self.vector_store:
                return "Vector store is not initialized."
            
            # Get the document store from FAISS
            docstore = self.vector_store.docstore
            if not docstore:
                return "Vector store is empty."
            
            # Count total documents
            total_docs = len(docstore._dict)
            
            # Sample some documents to show content
            sample_size = min(5, total_docs)
            sample_docs = list(docstore._dict.values())[:sample_size]
            
            # Build information string
            info = f"Vector store contains {total_docs} total documents.\n\n"
            info += "Sample of document contents:\n"
            for i, doc in enumerate(sample_docs, 1):
                content = doc.page_content[:200].replace('\n', ' ').strip()
                info += f"\n{i}. Content: {content}...\n"
                if hasattr(doc.metadata, 'source') and doc.metadata.get('source'):
                    info += f"   Source: {doc.metadata['source']}\n"
                info += "---\n"
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting vector store info: {e}")
            return f"Error inspecting vector store: {str(e)}"

    async def process_query(self, user_id: str, topic_id: str, user_query: str, **kwargs) -> dict:
        """Processes the user query using the selected AI model (GPT or Claude)."""
        async with self.lock:
            model_choice = kwargs.get("model_choice", "GPT")
            topic = "User Query Processing"
            description = f"Processing user query for user_id: {user_id} and topic_id: {topic_id}"
            start_time = time.time()

            try:
                # Clean the query
                cleaned_query = user_query.strip().lower()

                # Check if this is a special command to inspect vector store
                if any(cmd in cleaned_query for cmd in ["vector store", "data in store", "check store"]):
                    store_info = self.get_vector_store_info()
                    return {
                        "msg": "success",
                        "data": {
                            "answer": store_info,
                            "type_res": "vector_store_info"
                        }
                    }

                # Treat the entire user_query as a single question
                question = user_query.strip()
                if not question:
                    return {
                        "msg": "No valid question found in the input.",
                        "data": {
                            "answer": "",
                            "type_res": "no_valid_question"
                        }
                    }

                # Select the appropriate QA chain based on model_choice
                model_choice_upper = model_choice.upper()
                if model_choice_upper not in self.qa_chains:
                    logger.error(f"Invalid model choice: {model_choice}")
                    return {
                        "msg": f"Invalid model choice: {model_choice}. Choose either 'GPT' or 'CLAUDE'.",
                        "data": {
                            "answer": "",
                            "type_res": "invalid_model_choice"
                        }
                    }
                
                qa_chain = self.qa_chains[model_choice_upper]

                # Process the single question
                response = await self.process_single_question(question, qa_chain)

                if "error_code" in response:
                    return response

                answer = response.get('answer', '')
                type_res = response.get('type_res', 'generate')

                return {
                    "msg": "success",
                    "data": {
                        "answer": answer,
                        "type_res": type_res
                    }
                }
            except Exception as e:
                logger.error(f"{topic} | Error processing request: {str(e)}")
                return {"error_code": "02", "msg": f"Error processing request: {str(e)}"}

            finally:
                end_time = time.time()
                self.log_time(f"{topic}", description, start_time, end_time)