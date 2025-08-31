# Example usage of the neutral RAG system
# This file demonstrates how to use the RAG system with different LLM providers
import os
from rag import create_rag_system, RAGSystem
from .llm_providers import create_llm_provider

def example_openai_rag():
    """Example using OpenAI provider."""
    print("=== OpenAI RAG Example ===")
    
    # Configuration
    config = {
        "api_key": os.getenv("OPENAI_API_KEY", "openai-api-key"),
        "llm_model": "gpt-5-mini",
        "embedding_model": "text-embedding-ada-002",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        # Create RAG system with OpenAI
        rag = create_rag_system(
            provider_type="openai",
            documents_path="./test_docs",  # Path to your documents
            vector_store_type="chroma",
            **config
        )
        
        # Query the system
        question = "What is ESG compliance?"
        result = rag.query(question)
        
        print(f"Question: {question}")
        print(f"Answer: {result['answer']}")
        print(f"Provider: {result['provider_info']['provider']}")
        print(f"Usage Stats: {result['usage_stats']}")
        print(f"Processing Info: {result['processing_info']}")
        print(f"Intermediate Data: {result['intermediate_data']}")
        
    except Exception as e:
        print(f"Error with OpenAI RAG: {e}")

def example_huggingface_rag():
    """Example using HuggingFace provider."""
    print("\n=== HuggingFace RAG Example ===")
    
    # Configuration
    config = {
        "llm_model": "gpt2",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "temperature": 0.7,
        "max_tokens": 1000,
        "device": "cpu"
    }
    
    try:
        # Create RAG system with HuggingFace
        rag = create_rag_system(
            provider_type="huggingface",
            documents_path="./test_docs",
            vector_store_type="chroma",
            **config
        )
        
        # Query the system
        question = "What is ESG compliance?"
        result = rag.query(question)
        
        print(f"Question: {question}")
        print(f"Answer: {result['answer']}")
        print(f"Provider: {result['provider_info']['provider']}")
        print(f"Usage Stats: {result['usage_stats']}")
        
    except Exception as e:
        print(f"Error with HuggingFace RAG: {e}")

def example_local_rag():
    """Example using local Ollama provider."""
    print("\n=== Local Ollama RAG Example ===")
    
    # Configuration
    config = {
        "llm_model": "llama2",
        "embedding_model": "llama2",
        "base_url": "http://localhost:11434",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        # Create RAG system with local provider
        rag = create_rag_system(
            provider_type="local",
            documents_path="./test_docs",
            vector_store_type="chroma",
            **config
        )
        
        # Query the system
        question = "What is ESG compliance?"
        result = rag.query(question)
        
        print(f"Question: {question}")
        print(f"Answer: {result['answer']}")
        print(f"Provider: {result['provider_info']['provider']}")
        print(f"Usage Stats: {result['usage_stats']}")
        
    except Exception as e:
        print(f"Error with Local RAG: {e}")

def example_anthropic_rag():
    """Example using Anthropic provider."""
    print("\n=== Anthropic RAG Example ===")
    
    # Configuration
    config = {
        "api_key": os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key"),
        "llm_model": "claude-3-sonnet-20240229",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        # Create RAG system with Anthropic
        rag = create_rag_system(
            provider_type="anthropic",
            documents_path="./test_docs",
            vector_store_type="chroma",
            **config
        )
        
        # Query the system
        question = "What is ESG compliance?"
        result = rag.query(question)
        
        print(f"Question: {question}")
        print(f"Answer: {result['answer']}")
        print(f"Provider: {result['provider_info']['provider']}")
        print(f"Usage Stats: {result['usage_stats']}")
        
    except Exception as e:
        print(f"Error with Anthropic RAG: {e}")

def example_manual_provider_setup():
    """Example of manually creating a provider and RAG system."""
    print("\n=== Manual Provider Setup Example ===")
    
    try:
        # Create provider manually
        from .llm_providers import OpenAIProvider
        
        provider = OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key"),
            llm_model="gpt-3.5-turbo",
            embedding_model="text-embedding-ada-002"
        )
        
        # Create RAG system with the provider
        from rag import RAGSystem
        
        rag = RAGSystem(
            llm_provider=provider,
            vector_store_type="chroma"
        )
        
        # Load documents and create vector store
        documents = rag.load_directory("./test_docs")
        rag.create_vector_store(documents)
        
        # Query the system
        question = "What is ESG compliance?"
        result = rag.query(question)
        
        print(f"Question: {question}")
        print(f"Answer: {result['answer']}")
        print(f"Provider: {result['provider_info']['provider']}")
        
    except Exception as e:
        print(f"Error with manual setup: {e}")

def example_provider_switching():
    """Example of switching between different providers."""
    print("\n=== Provider Switching Example ===")
    
    # Create documents for testing
    test_docs = [
        "ESG stands for Environmental, Social, and Governance.",
        "ESG compliance helps companies manage risks and opportunities.",
        "Environmental factors include climate change and resource management.",
        "Social factors include labor practices and community relations.",
        "Governance factors include board diversity and transparency."
    ]
    
    # Save test documents
    os.makedirs("./test_docs", exist_ok=True)
    with open("./test_docs/esg_info.txt", "w") as f:
        f.write("\n".join(test_docs))
    
    providers = [
        ("openai", {"api_key": os.getenv("OPENAI_API_KEY", "your-key")}),
        ("huggingface", {"device": "cpu"}),
        ("local", {"base_url": "http://localhost:11434"}),
    ]
    
    question = "What does ESG stand for?"
    
    for provider_type, config in providers:
        try:
            print(f"\n--- Testing {provider_type.upper()} ---")
            
            rag = create_rag_system(
                provider_type=provider_type,
                documents_path="./test_docs",
                vector_store_type="chroma",
                **config
            )
            
            result = rag.query(question)
            print(f"Answer: {result['answer'][:100]}...")
            print(f"Provider: {result['provider_info']['provider']}")
            
        except Exception as e:
            print(f"Error with {provider_type}: {e}")

def main():
    """Run all examples."""
    print("RAG System Examples with Different LLM Providers")
    print("=" * 50)
    
    # Run examples
    example_openai_rag()
    # example_huggingface_rag()
    # example_local_rag()
    # example_anthropic_rag()
    # example_manual_provider_setup()
    # example_provider_switching()

if __name__ == "__main__":
    main()
