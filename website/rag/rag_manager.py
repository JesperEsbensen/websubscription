"""
RAG System Manager - Singleton for managing RAG system initialization
"""
import os
import logging
import warnings
from typing import Dict, Optional
from django.conf import settings
from pathlib import Path

# Suppress warnings and verbose logging
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

from .rag import RAGSystem
from .llm_providers import create_llm_provider
from .docling_chroma_db import DoclingChromaDB
from .config import (
    DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL, DEFAULT_VECTOR_STORE_TYPE,
    SESSION_DOCS_MAPPING, LIBRARY_PATH, DOCLING_DB_PATH
)

logger = logging.getLogger(__name__)

class RAGSystemManager:
    """
    Singleton manager for RAG system instances.
    Initializes RAG systems once and reuses them across requests.
    """
    
    _instance = None
    _rag_systems = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGSystemManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._rag_systems = {}
            self._initialized = True
            logger.info("RAG System Manager initialized")
    
    def initialize_rag_systems(self):
        """
        Initialize RAG systems using DoclingChromaDB for all session types.
        This should be called once when the server starts.
        """
        if self._rag_systems:
            logger.info("RAG systems already initialized")
            return
        
        logger.info("Initializing RAG systems with DoclingChromaDB for all session types...")
        
        try:
            # Create LLM provider once
            llm_provider = create_llm_provider(
                DEFAULT_LLM_PROVIDER,
                llm_model=DEFAULT_LLM_MODEL
            )
            
            # Initialize DoclingChromaDB systems for each session type
            for session_type, docs_path in SESSION_DOCS_MAPPING.items():
                if os.path.exists(docs_path):
                    logger.info(f"Initializing DoclingChromaDB system for {session_type} with docs at {docs_path}")
                    
                    try:
                        # Create DoclingChromaDB instance
                        docling_db = DoclingChromaDB(
                            persist_dir=os.path.join(DOCLING_DB_PATH, session_type),
                            collection_name=f"docling_chunks_{session_type}"
                        )
                        
                        # Initialize the database
                        docling_db.init_db()
                        
                        # Add documents to the database
                        docling_db.add_paths([docs_path])
                        
                        # Create a wrapper RAG system that uses DoclingChromaDB
                        rag_system = RAGSystem(
                            llm_provider=llm_provider,
                            vector_store_type=DEFAULT_VECTOR_STORE_TYPE
                        )
                        
                        # Store the DoclingChromaDB instance in the RAG system for later use
                        rag_system.docling_db = docling_db
                        
                        # Initialize the QA chain by creating a vector store
                        # We'll create a minimal vector store to initialize the QA chain
                        # The actual document retrieval will be handled by DoclingChromaDB
                        rag_system.create_vector_store([])  # Empty list to just initialize the chain
                        
                        self._rag_systems[session_type] = rag_system
                        logger.info(f"✅ DoclingChromaDB system initialized for {session_type}")
                        
                    except RuntimeError as e:
                        logger.warning(f"⚠️ DoclingChromaDB not available for {session_type}: {e}")

                else:
                    logger.warning(f"⚠️ Documents path does not exist for {session_type}: {docs_path}")
            
            
            logger.info(f"✅ RAG System Manager initialization complete. Systems ready: {list(self._rag_systems.keys())}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing RAG systems: {str(e)}")
            raise


    def get_rag_system(self, session_type: str) -> Optional[RAGSystem]:
        """
        Get the RAG system for a specific session type.
        
        Args:
            session_type: The session type (esg, technical, billing, general)
            
        Returns:
            RAGSystem instance or None if not available
        """
        # Try to get the specific session type
        if session_type in self._rag_systems:
            return self._rag_systems[session_type]
        
        # Fallback to general
        if 'general' in self._rag_systems:
            logger.info(f"Using general RAG system for session type: {session_type}")
            return self._rag_systems['general']
        
        logger.error(f"No RAG system available for session type: {session_type}")
        return None
    
    def is_initialized(self) -> bool:
        """Check if RAG systems are initialized."""
        return len(self._rag_systems) > 0
    
    def get_available_systems(self) -> list:
        """Get list of available RAG system types."""
        return list(self._rag_systems.keys())

# Global instance
rag_manager = RAGSystemManager()
