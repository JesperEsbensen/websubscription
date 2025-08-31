"""
Configuration file for RAG system
"""
import os
from pathlib import Path

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'openai-api-key')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5-mini')
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')

# RAG System Configuration
DEFAULT_VECTOR_STORE = 'chroma'
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000

# Document paths
TEST_DOCS_PATH = os.path.join(BASE_DIR, 'rag', 'test_docs')
CHROMA_DB_PATH = os.path.join(BASE_DIR, 'rag', 'chroma_db')

# Session type to document mapping
SESSION_DOCS_MAPPING = {
    'esg': os.path.join(TEST_DOCS_PATH, 'esg'),
    'technical': os.path.join(TEST_DOCS_PATH, 'technical'),
    'billing': os.path.join(TEST_DOCS_PATH, 'billing'),
    'general': TEST_DOCS_PATH
}

# LLM Provider Configuration
DEFAULT_LLM_PROVIDER = 'openai'
DEFAULT_LLM_MODEL = 'gpt-5-mini'

# RAG Dialogue Configuration
DEFAULT_DIALOGUE_TYPE = 'general'
DEFAULT_VECTOR_STORE_TYPE = 'chroma'

# Logging Configuration
RAG_LOG_LEVEL = os.getenv('RAG_LOG_LEVEL', 'INFO')
