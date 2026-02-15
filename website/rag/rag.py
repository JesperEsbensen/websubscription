# RAG (Retrieval-Augmented Generation) System using LangChain
# This module provides document processing, vector storage, and retrieval capabilities

# Core LangChain imports
from langchain import hub
from langchain.chains import RetrievalQA
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
from .llm_providers import LLMProvider, create_llm_provider

# Import configuration
try:
    from .config import (
        DEFAULT_VECTOR_STORE, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP,
        DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DOCLING_DB_PATH, LIBRARY_PATH
    )
except ImportError:
    # Fallback values if config is not available
    DEFAULT_VECTOR_STORE = "chroma"
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 1000
    DOCLING_DB_PATH = "docling_db"
    LIBRARY_PATH = "library"


# Import docling_chroma_db directly
from .docling_chroma_db import DoclingChromaDB

# For document processing
import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# For vector operations
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set root logger to WARNING to reduce noise from all libraries
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)

# Set our specific loggers back to INFO for important messages
logging.getLogger(__name__).setLevel(logging.INFO)

# Additional aggressive logging suppression
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress verbose LangChain logging
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("langchain_community").setLevel(logging.WARNING)
logging.getLogger("langchain_openai").setLevel(logging.WARNING)
logging.getLogger("langchain_core").setLevel(logging.WARNING)
logging.getLogger("langchain_text_splitters").setLevel(logging.WARNING)
logging.getLogger("langchain_community.document_loaders").setLevel(logging.WARNING)
logging.getLogger("langchain_community.vectorstores").setLevel(logging.WARNING)
logging.getLogger("langchain_community.embeddings").setLevel(logging.WARNING)
logging.getLogger("langchain_community.llms").setLevel(logging.WARNING)
logging.getLogger("langchain_community.chat_models").setLevel(logging.WARNING)
logging.getLogger("langchain_community.callbacks").setLevel(logging.WARNING)
logging.getLogger("langchain_community.callbacks.manager").setLevel(logging.WARNING)
logging.getLogger("langchain_community.callbacks.streaming_stdout").setLevel(logging.WARNING)
logging.getLogger("langchain_community.callbacks.streaming_aiter").setLevel(logging.WARNING)
logging.getLogger("langchain_community.callbacks.streaming_stdout_final_only").setLevel(logging.WARNING)
logging.getLogger("langchain_community.callbacks.streaming_aiter_final_only").setLevel(logging.WARNING)

# Suppress other verbose libraries
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("chromadb.api").setLevel(logging.WARNING)
logging.getLogger("chromadb.db").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("torch").setLevel(logging.WARNING)
logging.getLogger("tqdm").setLevel(logging.WARNING)

# Suppress PDF processing libraries
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfinterp").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfpage").setLevel(logging.WARNING)
logging.getLogger("pdfminer.converter").setLevel(logging.WARNING)
logging.getLogger("pdfminer.layout").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfparser").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfdocument").setLevel(logging.WARNING)
logging.getLogger("pdfminer.psparser").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfinterp").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfpage").setLevel(logging.WARNING)
logging.getLogger("pdfminer.converter").setLevel(logging.WARNING)
logging.getLogger("pdfminer.layout").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfparser").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfdocument").setLevel(logging.WARNING)
logging.getLogger("pdfminer.psparser").setLevel(logging.WARNING)

# Suppress unstructured library logging
logging.getLogger("unstructured").setLevel(logging.WARNING)
logging.getLogger("unstructured.partition").setLevel(logging.WARNING)
logging.getLogger("unstructured.chunking").setLevel(logging.WARNING)

# Suppress other document processing libraries
logging.getLogger("pypdf").setLevel(logging.WARNING)
logging.getLogger("pymupdf").setLevel(logging.WARNING)
logging.getLogger("fitz").setLevel(logging.WARNING)
logging.getLogger("docx").setLevel(logging.WARNING)
logging.getLogger("python-docx").setLevel(logging.WARNING)

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
        vector_store_type: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        temperature: float = None,
        max_tokens: int = None
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
        logger.debug(f"Initializing RAG system with LLM provider: {llm_provider.get_model_info()['provider']}")
        self.llm_provider = llm_provider
        self.vector_store_type = vector_store_type or DEFAULT_VECTOR_STORE
        self.chunk_size = chunk_size if chunk_size is not None else DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else DEFAULT_CHUNK_OVERLAP
        self.temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS
        logger.debug(f"RAG system initialized with chunk size: {self.chunk_size}, chunk overlap: {self.chunk_overlap}, temperature: {self.temperature}, max_tokens: {self.max_tokens}")
        
        # Initialize text splitter
        logger.debug(f"Creating text splitter with:")
        logger.debug(f"   - chunk_size: {self.chunk_size}")
        logger.debug(f"   - chunk_overlap: {self.chunk_overlap}")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        logger.debug("Text splitter initialized successfully")
        
        self.vector_store = None
        self.retriever = None
        self.qa_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="result",
            input_key="query",
            return_messages=True
        )
        
        logger.info(f"RAG System initialized with {vector_store_type} vector store and {llm_provider.get_model_info()['provider']} provider")
    
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for processing.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of split document chunks
        """
        split_docs = self.text_splitter.split_documents(documents)
        logger.info(f"✂️ Split {len(documents)} documents into {len(split_docs)} chunks")
        return split_docs
    
    def _create_minimal_vector_store(self) -> None:
        """
        Create a minimal vector store and QA chain even when no documents are available.
        This ensures the QA chain is initialized for basic queries.
        """
        try:
            logger.info("Creating minimal vector store for empty document set...")
            
            if self.vector_store_type.lower() == "chroma":
                # Create an empty Chroma vector store
                self.vector_store = Chroma(
                    embedding_function=self.llm_provider.embeddings,
                    persist_directory="./chroma_db"
                )
                
                # Create a simple retriever
                self.retriever = self.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}
                )
                
                # Initialize QA chain
                self.qa_chain = self._create_qa_chain()
                
                logger.info("✅ Minimal vector store and QA chain created successfully")
                
            else:
                logger.warning(f"Minimal vector store not implemented for {self.vector_store_type}")
                
        except Exception as e:
            logger.error(f"Error creating minimal vector store: {str(e)}")
            # Still try to create a basic QA chain without vector store
            self._create_basic_qa_chain()
    
    def _create_basic_qa_chain(self) -> None:
        """
        Create a basic QA chain without vector store for simple queries.
        """
        try:
            logger.info("Creating basic QA chain without vector store...")
            
            # Create a simple LLM wrapper
            llm_wrapper = ProviderLLMWrapper(self.llm_provider)
            
            # Create a basic QA chain that just uses the LLM directly
            self.qa_chain = llm_wrapper
            
            logger.info("✅ Basic QA chain created successfully")
            
        except Exception as e:
            logger.error(f"Error creating basic QA chain: {str(e)}")
    
    def create_vector_store(self, documents: List[Document], persist_directory: str = None) -> None:
        """
        Create and initialize the vector store with documents.
        
        Args:
            documents: List of documents to add to vector store
            persist_directory: Directory to persist vector store (for Chroma)
        """
        if not documents:
            logger.warning("No documents provided for vector store creation")
            # Still create a minimal vector store and QA chain for empty queries
            self._create_minimal_vector_store()
            return
        
        try:
            # Split documents into chunks first
            logger.info(f"🔄 Processing {len(documents)} documents for vector store...")
            split_docs = self.split_documents(documents)
            
            if self.vector_store_type.lower() == "chroma":
                persist_dir = persist_directory or "./chroma_db"
                logger.info(f"🗄️ Creating Chroma vector store with {len(split_docs)} chunks...")
                self.vector_store = Chroma.from_documents(
                    documents=split_docs,
                    embedding=self.llm_provider.embeddings,
                    persist_directory=persist_dir
                )
                # Chroma 0.4.x automatically persists, no need to call persist()
                
            elif self.vector_store_type.lower() == "faiss":
                logger.info(f"🗄️ Creating FAISS vector store with {len(split_docs)} chunks...")
                self.vector_store = FAISS.from_documents(
                    documents=split_docs,
                    embedding=self.llm_provider.embeddings
                )
                
            elif self.vector_store_type.lower() == "pinecone":
                # Note: Requires Pinecone API key and index name
                # self.vector_store = Pinecone.from_documents(
                #     documents=split_docs,
                #     embedding=self.llm_provider.embeddings,
                #     index_name="your-index-name"
                # )
                logger.warning("Pinecone setup requires additional configuration")
                return
                
            else:
                logger.warning(f"Unsupported vector store type: {self.vector_store_type}")
                return
            
            # Use retriever from docling_chroma_db
            db = DoclingChromaDB(
                persist_dir=os.path.join(DOCLING_DB_PATH, 'esg'),
                collection_name="esg"
            )
            db.add_paths([os.path.join(LIBRARY_PATH, 'esg')])
            self.retriever =lc_retriever = db.as_retriever(k=4, strategy="hybrid")  # or "vector"/"bm25"
            
            # Initialize QA chain with custom LLM wrapper
            self.qa_chain = self._create_qa_chain()
            
            logger.info(f"✅ Vector store created successfully with {len(split_docs)} chunks")
            
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
    
    def query(self, question: str, k: int = 5, include_intermediate: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system with a question.
        
        Args:
            question: The question to ask
            k: Number of relevant documents to retrieve
            include_intermediate: Whether to include intermediate processing information
            
        Returns:
            Dictionary containing answer and source documents
        """
        if not self.qa_chain:
            logger.error("QA chain not initialized. Call create_vector_store first.")
            return {"error": "QA chain not initialized"}
        
        try:
            # Track processing steps
            processing_info = {
                "query": question,
                "timestamp": time.time(),
                "steps": []
            }
            
            # Step 1: Document retrieval
            logger.info(f"🔍 Query: {question}")
            start_time = time.time()
            relevant_docs = self.similarity_search(question, k=k)
            retrieval_time = time.time() - start_time
            
            # Log retrieved documents in a clean format
            if relevant_docs:
                logger.info(f"📚 Retrieved {len(relevant_docs)} relevant documents:")
                for i, doc in enumerate(relevant_docs, 1):
                    score = doc.metadata.get('similarity_score', None)
                    first_line = doc.page_content.split('\n')[0][:80] + "..." if len(doc.page_content.split('\n')[0]) > 80 else doc.page_content.split('\n')[0]
                    source = doc.metadata.get('source', 'Unknown')
                    source_name = Path(source).name if source != 'Unknown' else 'Unknown'
                    logger.info(f"  {i}. [{score:.3f}] {source_name}: {first_line}")
            else:
                logger.warning("No relevant documents found for query")
            
            processing_info["steps"].append({
                "step": "document_retrieval",
                "duration": retrieval_time,
                "documents_found": len(relevant_docs),
                "documents": [
                    {
                        "first_line": doc.page_content.split('\n')[0][:100] + "..." if len(doc.page_content.split('\n')[0]) > 100 else doc.page_content.split('\n')[0],
                        "source": doc.metadata.get('source', 'Unknown'),
                        "score": doc.metadata.get('similarity_score', None)
                    } for doc in relevant_docs
                ]
            })
            
            # Step 2: Context preparation
            start_time = time.time()
            context_text = self._prepare_context(relevant_docs)
            context_time = time.time() - start_time
            
            processing_info["steps"].append({
                "step": "context_preparation",
                "duration": context_time,
                "context_length": len(context_text),
                "context_preview": context_text[:500] + "..." if len(context_text) > 500 else context_text
            })
            
            # Step 3: LLM processing
            start_time = time.time()
            
            # Handle different types of QA chains
            if hasattr(self.qa_chain, 'invoke'):
                # Full RetrievalQA chain
                result = self.qa_chain.invoke({"query": question})
            else:
                # Direct LLM wrapper - create a simple response
                if relevant_docs:
                    context = "\n\n".join([doc.page_content for doc in relevant_docs])
                    prompt = f"Based on the following context, please answer the question: {question}\n\nContext:\n{context}"
                else:
                    prompt = f"Please answer the following question: {question}"
                
                result = self.qa_chain.invoke(prompt)
                # Wrap the result in the expected format
                result = {"result": result}
            
            llm_time = time.time() - start_time
            
            processing_info["steps"].append({
                "step": "llm_processing",
                "duration": llm_time,
                "provider": self.llm_provider.get_model_info()["provider"]
            })
            
            # Get usage stats from provider
            usage_stats = self.llm_provider.get_usage_stats()
            
            # Calculate total processing time
            total_time = time.time() - processing_info["timestamp"]
            processing_info["total_duration"] = total_time
            
            response = {
                "answer": result["result"],
                "source_documents": result.get("source_documents", []),
                "chat_history": self.memory.chat_memory.messages,
                "usage_stats": usage_stats,
                "provider_info": self.llm_provider.get_model_info()
            }
            logger.debug(f"Result: {result['result']}")
            
            # Add intermediate information if requested
            if include_intermediate:
                response["processing_info"] = processing_info
                response["intermediate_data"] = {
                    "retrieved_documents": relevant_docs,
                    "context_used": context_text,
                    "retrieval_scores": [doc.metadata.get('similarity_score', None) for doc in relevant_docs]
                }
            
            logger.debug(f"Query processed in {total_time:.2f}s using {self.llm_provider.get_model_info()['provider']} provider")
            return response
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {"error": str(e)}
    
    def similarity_search(self, query: str, k: int = 5, include_scores: bool = True) -> List[Document]:
        """
        Perform similarity search to find relevant documents.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            include_scores: Whether to include similarity scores
            
        Returns:
            List of relevant documents with optional scores
        """
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return []
        
        try:
            if include_scores:
                # Get documents with scores
                docs_and_scores = self.vector_store.similarity_search_with_score(query, k=k)
                docs = []
                for doc, score in docs_and_scores:
                    # Create a copy of the document and add score as metadata
                    doc_copy = Document(
                        page_content=doc.page_content,
                        metadata={**doc.metadata, 'similarity_score': score}
                    )
                    docs.append(doc_copy)
            else:
                docs = self.vector_store.similarity_search(query, k=k)
            
            logger.debug(f"Retrieved {len(docs)} documents for query: {query}")
            if include_scores and docs:
                # Log a clean summary of retrieved documents
                for i, doc in enumerate(docs, 1):
                    score = doc.metadata.get('similarity_score', None)
                    first_line = doc.page_content.split('\n')[0][:80] + "..." if len(doc.page_content.split('\n')[0]) > 80 else doc.page_content.split('\n')[0]
                    source = doc.metadata.get('source', 'Unknown')
                    source_name = Path(source).name if source != 'Unknown' else 'Unknown'
                    logger.debug(f"  {i}. [{score:.3f}] {source_name}: {first_line}")
            
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
                "chunk_overlap": self.chunk_overlap,
                "memory_info": {
                    "chat_history_length": len(self.memory.chat_memory.messages),
                    "memory_type": type(self.memory).__name__
                }
            }
            
            # Get document count if available
            if hasattr(self.vector_store, '_collection'):
                info["document_count"] = self.vector_store._collection.count()
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting vector store info: {str(e)}")
            return {"error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status and statistics.
        
        Returns:
            Dictionary with system status information
        """
        try:
            status = {
                "system_info": {
                    "rag_system_initialized": self.qa_chain is not None,
                    "vector_store_initialized": self.vector_store is not None,
                    "retriever_initialized": self.retriever is not None,
                    "memory_initialized": self.memory is not None
                },
                "vector_store_info": self.get_vector_store_info(),
                "provider_stats": self.llm_provider.get_usage_stats(),
                "configuration": {
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {"error": str(e)}
    
    def _prepare_context(self, documents: List[Document]) -> str:
        """
        Prepare context from retrieved documents.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.page_content.strip()
            metadata = doc.metadata
            source = metadata.get('source', 'Unknown')
            
            context_parts.append(f"Document {i} (Source: {source}):\n{content}\n")
        
        return "\n".join(context_parts)
    
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
