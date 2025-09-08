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
from .config import (
    DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL, DEFAULT_VECTOR_STORE_TYPE,
    SESSION_DOCS_MAPPING, LIBRARY_PATH
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
        Initialize RAG systems for all session types.
        This should be called once when the server starts.
        """
        if self._rag_systems:
            logger.info("RAG systems already initialized")
            return
        
        logger.info("Initializing RAG systems for all session types...")
        
        try:
            # Create LLM provider once
            llm_provider = create_llm_provider(
                DEFAULT_LLM_PROVIDER,
                llm_model=DEFAULT_LLM_MODEL
            )
            
            # Initialize RAG system for each session type
            for session_type, docs_path in SESSION_DOCS_MAPPING.items():
                if os.path.exists(docs_path):
                    logger.info(f"Initializing RAG system for {session_type} with docs at {docs_path}")
                    
                    # Create RAG system
                    rag_system = RAGSystem(
                        llm_provider=llm_provider,
                        vector_store_type=DEFAULT_VECTOR_STORE_TYPE
                    )
                    
                    # Load documents and create vector store
                    documents = rag_system.load_directory(docs_path)
                    if documents:
                        rag_system.create_vector_store(documents)
                        self._rag_systems[session_type] = rag_system
                        logger.info(f"✅ RAG system initialized for {session_type} with {len(documents)} documents")
                    else:
                        logger.warning(f"⚠️ No documents found for {session_type} at {docs_path}")
                else:
                    logger.warning(f"⚠️ Documents path does not exist for {session_type}: {docs_path}")
            
            # Initialize general RAG system as fallback (only if no other systems exist)
            if not self._rag_systems and os.path.exists(LIBRARY_PATH):
                logger.info(f"Initializing general RAG system with docs at {LIBRARY_PATH}")
                rag_system = RAGSystem(
                    llm_provider=llm_provider,
                    vector_store_type=DEFAULT_VECTOR_STORE_TYPE
                )
                documents = rag_system.load_directory(LIBRARY_PATH)
                if documents:
                    rag_system.create_vector_store(documents)
                    self._rag_systems['general'] = rag_system
                    logger.info(f"✅ General RAG system initialized with {len(documents)} documents")
            
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
    
    def reload_system(self, session_type: str):
        """
        Reload a specific RAG system (useful for development).
        
        Args:
            session_type: The session type to reload
        """
        if session_type in SESSION_DOCS_MAPPING:
            docs_path = SESSION_DOCS_MAPPING[session_type]
            if os.path.exists(docs_path):
                logger.info(f"Reloading RAG system for {session_type}")
                
                # Create new LLM provider
                llm_provider = create_llm_provider(
                    DEFAULT_LLM_PROVIDER,
                    llm_model=DEFAULT_LLM_MODEL
                )
                
                # Create new RAG system
                rag_system = RAGSystem(
                    llm_provider=llm_provider,
                    vector_store_type=DEFAULT_VECTOR_STORE_TYPE
                )
                
                # Load documents and create vector store
                documents = rag_system.load_directory(docs_path)
                if documents:
                    rag_system.create_vector_store(documents)
                    self._rag_systems[session_type] = rag_system
                    logger.info(f"✅ RAG system reloaded for {session_type} with {len(documents)} documents")
                else:
                    logger.warning(f"⚠️ No documents found when reloading {session_type}")

# Global instance
rag_manager = RAGSystemManager()
