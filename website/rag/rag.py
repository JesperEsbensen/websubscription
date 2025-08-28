# RAG (Retrieval-Augmented Generation) System using LangChain
# This module provides document processing, vector storage, and retrieval capabilities

# Core LangChain imports
from langchain import hub
from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PDFMinerLoader,
    UnstructuredFileLoader,
    DirectoryLoader,
    CSVLoader,
    JSONLoader
)
from langchain_community.vectorstores import (
    Chroma,
    FAISS,
    Pinecone,
    Weaviate,
    Qdrant,
    Milvus
)
from langchain_community.retrievers import BM25Retriever
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.evaluation import load_evaluator
from langchain.schema.runnable import Runnable

# Import our neutral LLM provider interface
from llm_providers import LLMProvider, create_llm_provider

# For document processing
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# For vector operations
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    """
    A comprehensive RAG (Retrieval-Augmented Generation) system using LangChain.
    
    This class provides functionality for:
    - Document loading and processing
    - Text splitting and chunking
    - Vector storage and retrieval
    - Question answering with context
    - Conversation memory management
    
    The system is LLM-neutral and can work with any provider that implements the LLMProvider interface.
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        vector_store_type: str = "chroma",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Initialize the RAG system.
        
        Args:
            llm_provider: LLM provider instance (OpenAI, HuggingFace, Anthropic, Local, etc.)
            vector_store_type: Type of vector store ("chroma", "faiss", "pinecone", etc.)
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
            temperature: LLM temperature for response generation
            max_tokens: Maximum tokens for LLM responses
        """
        self.llm_provider = llm_provider
        self.vector_store_type = vector_store_type
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.vector_store = None
        self.retriever = None
        self.qa_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="result",
            return_messages=True
        )
        
        logger.info(f"RAG System initialized with {vector_store_type} vector store and {llm_provider.get_model_info()['provider']} provider")
    
    def load_documents(self, file_paths: List[str]) -> List[Document]:
        """
        Load documents from various file formats.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            List of LangChain Document objects
        """
        documents = []
        
        for file_path in file_paths:
            try:
                file_path = Path(file_path)
                
                if file_path.suffix.lower() == '.txt':
                    loader = TextLoader(str(file_path))
                elif file_path.suffix.lower() == '.pdf':
                    loader = PDFMinerLoader(str(file_path))
                elif file_path.suffix.lower() == '.csv':
                    loader = CSVLoader(str(file_path))
                elif file_path.suffix.lower() == '.json':
                    loader = JSONLoader(
                        file_path=str(file_path),
                        jq_schema='.',
                        text_content=False
                    )
                else:
                    # Try unstructured loader for other formats
                    loader = UnstructuredFileLoader(str(file_path))
                
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Loaded {len(docs)} documents from {file_path}")
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {str(e)}")
                continue
        
        return documents
    
    def load_directory(self, directory_path: str, glob_pattern: str = "**/*") -> List[Document]:
        """
        Load all documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            glob_pattern: Pattern to match files
            
        Returns:
            List of LangChain Document objects
        """
        loader = DirectoryLoader(
            directory_path,
            glob=glob_pattern,
            show_progress=True,
            use_multithreading=True
        )
        
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} documents from directory {directory_path}")
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for processing.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of split document chunks
        """
        split_docs = self.text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
        return split_docs
    
    def create_vector_store(self, documents: List[Document], persist_directory: str = None) -> None:
        """
        Create and initialize the vector store with documents.
        
        Args:
            documents: List of documents to add to vector store
            persist_directory: Directory to persist vector store (for Chroma)
        """
        if not documents:
            logger.warning("No documents provided for vector store creation")
            return
        
        try:
            if self.vector_store_type.lower() == "chroma":
                persist_dir = persist_directory or "./chroma_db"
                self.vector_store = Chroma.from_documents(
                    documents=documents,
                    embedding=self.llm_provider.embeddings,
                    persist_directory=persist_dir
                )
                # Chroma 0.4.x automatically persists, no need to call persist()
                
            elif self.vector_store_type.lower() == "faiss":
                self.vector_store = FAISS.from_documents(
                    documents=documents,
                    embedding=self.llm_provider.embeddings
                )
                
            elif self.vector_store_type.lower() == "pinecone":
                # Note: Requires Pinecone API key and index name
                # self.vector_store = Pinecone.from_documents(
                #     documents=documents,
                #     embedding=self.llm_provider.embeddings,
                #     index_name="your-index-name"
                # )
                logger.warning("Pinecone setup requires additional configuration")
                return
                
            else:
                logger.warning(f"Unsupported vector store type: {self.vector_store_type}")
                return
            
            # Initialize retriever
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            # Initialize QA chain with custom LLM wrapper
            self.qa_chain = self._create_qa_chain()
            
            logger.info(f"Vector store created with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    def _create_qa_chain(self):
        """Create a QA chain using the LLM provider."""
        # Create a custom LLM wrapper that implements Runnable interface
        class ProviderLLMWrapper(Runnable):
            def __init__(self, provider: LLMProvider):
                self.provider = provider
            
            def invoke(self, input_data, config=None, **kwargs):
                """Implement the Runnable interface."""
                if isinstance(input_data, dict):
                    prompt = input_data.get("query", "")
                else:
                    prompt = str(input_data)
                
                # Filter out unsupported kwargs
                supported_kwargs = {}
                for key, value in kwargs.items():
                    if key not in ['stop', 'callbacks', 'tags', 'metadata']:
                        supported_kwargs[key] = value
                
                response = self.provider.generate_response(prompt, **supported_kwargs)
                return response
            
            def predict(self, prompt: str, **kwargs) -> str:
                """Backward compatibility method."""
                return self.provider.generate_response(prompt, **kwargs)
        
        # Create the wrapper
        llm_wrapper = ProviderLLMWrapper(self.llm_provider)
        
        # Create the QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm_wrapper,
            chain_type="stuff",
            retriever=self.retriever,
            memory=self.memory,
            return_source_documents=True
        )
        
        return qa_chain
    
    def load_existing_vector_store(self, persist_directory: str = None) -> bool:
        """
        Load an existing vector store from disk.
        
        Args:
            persist_directory: Directory containing the persisted vector store
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if self.vector_store_type.lower() == "chroma":
                persist_dir = persist_directory or "./chroma_db"
                if os.path.exists(persist_dir):
                    self.vector_store = Chroma(
                        persist_directory=persist_dir,
                        embedding_function=self.llm_provider.embeddings
                    )
                    
                    self.retriever = self.vector_store.as_retriever(
                        search_type="similarity",
                        search_kwargs={"k": 5}
                    )
                    
                    self.qa_chain = self._create_qa_chain()
                    
                    logger.info("Existing vector store loaded successfully")
                    return True
                    
            elif self.vector_store_type.lower() == "faiss":
                # For FAISS, you would load the saved index
                # self.vector_store = FAISS.load_local("faiss_index", self.llm_provider.embeddings)
                logger.info("FAISS loading requires saved index file")
                
        except Exception as e:
            logger.error(f"Error loading existing vector store: {str(e)}")
        
        return False
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add new documents to the existing vector store.
        
        Args:
            documents: List of new documents to add
        """
        if not self.vector_store:
            logger.error("Vector store not initialized. Call create_vector_store first.")
            return
        
        try:
            split_docs = self.split_documents(documents)
            self.vector_store.add_documents(split_docs)
            
            if hasattr(self.vector_store, 'persist'):
                self.vector_store.persist()
            
            logger.info(f"Added {len(split_docs)} document chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
    
    def query(self, question: str, k: int = 5) -> Dict[str, Any]:
        """
        Query the RAG system with a question.
        
        Args:
            question: The question to ask
            k: Number of relevant documents to retrieve
            
        Returns:
            Dictionary containing answer and source documents
        """
        if not self.qa_chain:
            logger.error("QA chain not initialized. Call create_vector_store first.")
            return {"error": "QA chain not initialized"}
        
        try:
            result = self.qa_chain({"query": question})
            
            # Get usage stats from provider
            usage_stats = self.llm_provider.get_usage_stats()
            
            response = {
                "answer": result["result"],
                "source_documents": result.get("source_documents", []),
                "chat_history": self.memory.chat_memory.messages,
                "usage_stats": usage_stats,
                "provider_info": self.llm_provider.get_model_info()
            }
            
            logger.info(f"Query processed using {self.llm_provider.get_model_info()['provider']} provider")
            return response
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {"error": str(e)}
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Perform similarity search to find relevant documents.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Retrieved {len(docs)} documents for query: {query}")
            return docs
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    def get_vector_store_info(self) -> Dict[str, Any]:
        """
        Get information about the current vector store.
        
        Returns:
            Dictionary with vector store information
        """
        if not self.vector_store:
            return {"error": "Vector store not initialized"}
        
        try:
            info = {
                "type": self.vector_store_type,
                "provider_info": self.llm_provider.get_model_info(),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            }
            
            # Get document count if available
            if hasattr(self.vector_store, '_collection'):
                info["document_count"] = self.vector_store._collection.count()
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting vector store info: {str(e)}")
            return {"error": str(e)}
    
    def clear_memory(self) -> None:
        """Clear the conversation memory."""
        self.memory.clear()
        logger.info("Conversation memory cleared")
    
    def save_vector_store(self, path: str) -> bool:
        """
        Save the vector store to disk.
        
        Args:
            path: Path to save the vector store
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if self.vector_store_type.lower() == "chroma":
                # Chroma 0.4.x automatically persists
                pass
            elif self.vector_store_type.lower() == "faiss":
                self.vector_store.save_local(path)
            
            logger.info(f"Vector store saved to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            return False

# Example usage and utility functions
def create_rag_system(
    provider_type: str,
    documents_path: str,
    vector_store_type: str = "chroma",
    **provider_kwargs
) -> RAGSystem:
    """
    Create and initialize a complete RAG system.
    
    Args:
        provider_type: Type of LLM provider ("openai", "huggingface", "anthropic", "local")
        documents_path: Path to documents directory or file
        vector_store_type: Type of vector store to use
        **provider_kwargs: Provider-specific arguments
        
    Returns:
        Initialized RAGSystem instance
    """
    # Create LLM provider
    llm_provider = create_llm_provider(provider_type, **provider_kwargs)
    
    # Initialize RAG system
    rag = RAGSystem(llm_provider, vector_store_type)
    
    # Load documents
    if os.path.isdir(documents_path):
        documents = rag.load_directory(documents_path)
    else:
        documents = rag.load_documents([documents_path])
    
    # Create vector store
    rag.create_vector_store(documents)
    
    return rag

def query_rag_system(rag: RAGSystem, question: str) -> str:
    """
    Simple function to query a RAG system and return just the answer.
    
    Args:
        rag: RAGSystem instance
        question: Question to ask
        
    Returns:
        Answer string
    """
    result = rag.query(question)
    return result.get("answer", "No answer available")

# Example configurations for different providers
def get_provider_configs():
    """Get example configurations for different LLM providers."""
    return {
        "openai": {
            "api_key": "your-openai-api-key",
            "llm_model": "gpt-3.5-turbo",
            "embedding_model": "text-embedding-ada-002",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "huggingface": {
            "llm_model": "gpt2",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "temperature": 0.7,
            "max_tokens": 1000,
            "device": "cpu"
        },
        "anthropic": {
            "api_key": "your-anthropic-api-key",
            "llm_model": "claude-3-sonnet-20240229",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "local": {
            "llm_model": "llama2",
            "embedding_model": "llama2",
            "base_url": "http://localhost:11434",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }
