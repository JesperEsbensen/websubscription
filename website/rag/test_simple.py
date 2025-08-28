#!/usr/bin/env python3
"""
Simple test script to demonstrate the RAG system working without API keys.
This creates a mock LLM provider for testing purposes.
"""

import os
import logging
from typing import List, Dict, Any
from llm_providers import LLMProvider
from rag import RAGSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockEmbeddings:
    """Mock embeddings class for testing."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single text."""
        import numpy as np
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % 10000)
        return list(np.random.rand(self.dimension))
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        return [self.embed_query(text) for text in texts]

class MockProvider(LLMProvider):
    """Mock LLM provider for testing without API keys."""
    
    def __init__(self, name: str = "mock"):
        self.name = name
        self._usage_stats = {"generations": 0}
        
        # Create mock embeddings
        self.embeddings = MockEmbeddings(384)
        
        logger.info(f"Mock provider '{name}' initialized")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a mock response based on the prompt."""
        self._usage_stats["generations"] += 1
        
        # Simple mock responses based on keywords
        prompt_lower = prompt.lower()
        
        if "esg" in prompt_lower:
            return "ESG stands for Environmental, Social, and Governance. It's a framework for evaluating how a company manages risks and opportunities related to sustainability and responsible business practices."
        elif "environmental" in prompt_lower:
            return "Environmental factors in ESG include climate change, resource management, waste reduction, and energy efficiency."
        elif "social" in prompt_lower:
            return "Social factors in ESG include labor practices, human rights, community relations, and diversity and inclusion."
        elif "governance" in prompt_lower:
            return "Governance factors in ESG include board diversity, transparency, ethical business practices, and regulatory compliance."
        else:
            return f"This is a mock response to: {prompt}. The mock provider processed this request successfully."
    
    def get_embedding(self, text: str) -> List[float]:
        """Get a mock embedding for text."""
        return self.embeddings.embed_query(text)
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get mock embeddings for multiple texts."""
        return self.embeddings.embed_documents(texts)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information."""
        return {
            "provider": f"mock-{self.name}",
            "model": "mock-model-v1",
            "embedding_model": "mock-embeddings-v1",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get mock usage statistics."""
        return self._usage_stats.copy()

def test_rag_system():
    """Test the RAG system with a mock provider."""
    print("🧪 Testing RAG System with Mock Provider")
    print("=" * 50)
    
    try:
        # Create mock provider
        mock_provider = MockProvider("test-provider")
        
        # Create RAG system
        rag = RAGSystem(
            llm_provider=mock_provider,
            vector_store_type="chroma",
            chunk_size=500,
            chunk_overlap=50
        )
        
        print("✅ RAG System initialized successfully")
        
        # Load test documents
        documents = rag.load_directory("./test_docs")
        print(f"✅ Loaded {len(documents)} documents")
        
        # Create vector store
        rag.create_vector_store(documents)
        print("✅ Vector store created successfully")
        
        # Test queries
        test_questions = [
            "What is ESG?",
            "What are environmental factors?",
            "What are social factors?",
            "What are governance factors?",
            "How does ESG help companies?"
        ]
        
        print("\n🔍 Testing Queries:")
        print("-" * 30)
        
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            result = rag.query(question)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Answer: {result['answer']}")
                print(f"📊 Provider: {result['provider_info']['provider']}")
                print(f"📈 Usage: {result['usage_stats']}")
        
        # Test similarity search
        print("\n🔍 Testing Similarity Search:")
        print("-" * 30)
        
        search_results = rag.similarity_search("ESG compliance", k=3)
        print(f"✅ Found {len(search_results)} similar documents")
        
        for i, doc in enumerate(search_results, 1):
            print(f"📄 Document {i}: {doc.page_content[:100]}...")
        
        # Test vector store info
        print("\n📊 Vector Store Information:")
        print("-" * 30)
        
        info = rag.get_vector_store_info()
        print(f"✅ Type: {info['type']}")
        print(f"✅ Provider: {info['provider_info']['provider']}")
        print(f"✅ Chunk Size: {info['chunk_size']}")
        print(f"✅ Chunk Overlap: {info['chunk_overlap']}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_provider_interface():
    """Test the LLM provider interface."""
    print("\n🧪 Testing LLM Provider Interface")
    print("=" * 50)
    
    try:
        # Create mock provider
        provider = MockProvider("interface-test")
        
        # Test basic functionality
        print("✅ Provider created successfully")
        
        # Test response generation
        response = provider.generate_response("What is ESG?")
        print(f"✅ Response generated: {response[:50]}...")
        
        # Test embedding
        embedding = provider.get_embedding("test text")
        print(f"✅ Embedding generated: {len(embedding)} dimensions")
        
        # Test model info
        info = provider.get_model_info()
        print(f"✅ Model info: {info}")
        
        # Test usage stats
        stats = provider.get_usage_stats()
        print(f"✅ Usage stats: {stats}")
        
        print("🎉 Provider interface tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Provider interface test failed: {e}")

if __name__ == "__main__":
    test_provider_interface()
    test_rag_system()
