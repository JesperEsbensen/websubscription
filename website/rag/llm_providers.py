# LLM Provider Interface and Implementations
# This module provides a neutral interface for different LLM providers

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text."""
        pass
    
    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics (tokens, cost, etc.)."""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(
        self,
        api_key: str,
        llm_model: str = "gpt-3.5-turbo",
        embedding_model: str = "text-embedding-ada-002",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """Initialize OpenAI provider."""
        try:
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            from langchain_community.callbacks.manager import get_openai_callback
        except ImportError:
            raise ImportError("OpenAI provider requires langchain-openai to be installed")
        
        self.api_key = api_key
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize components
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            model=embedding_model
        )
        
        self._usage_stats = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0
        }
        
        logger.info(f"OpenAI provider initialized with model: {llm_model}")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI."""
        try:
            from langchain_community.callbacks.manager import get_openai_callback
            
            with get_openai_callback() as cb:
                response = self.llm.predict(prompt, **kwargs)
                
                # Update usage stats
                self._usage_stats["total_tokens"] += cb.total_tokens
                self._usage_stats["prompt_tokens"] += cb.prompt_tokens
                self._usage_stats["completion_tokens"] += cb.completion_tokens
                self._usage_stats["total_cost"] += cb.total_cost
                
                logger.info(f"OpenAI response generated. Tokens: {cb.total_tokens}, Cost: ${cb.total_cost:.4f}")
                return response
                
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using OpenAI."""
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error getting OpenAI embedding: {str(e)}")
            raise
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts using OpenAI."""
        try:
            embeddings = self.embeddings.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error getting OpenAI embeddings: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information."""
        return {
            "provider": "openai",
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get OpenAI usage statistics."""
        return self._usage_stats.copy()

class HuggingFaceProvider(LLMProvider):
    """HuggingFace LLM provider implementation."""
    
    def __init__(
        self,
        llm_model: str = "gpt2",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        device: str = "cpu"
    ):
        """Initialize HuggingFace provider."""
        try:
            from langchain_community.llms import HuggingFacePipeline
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        except ImportError:
            raise ImportError("HuggingFace provider requires transformers and torch to be installed")
        
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.device = device
        
        # Initialize LLM
        tokenizer = AutoTokenizer.from_pretrained(llm_model)
        model = AutoModelForCausalLM.from_pretrained(llm_model)
        
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=max_tokens,
            temperature=temperature,
            device=device,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        self.llm = HuggingFacePipeline(pipeline=pipe)
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': device}
        )
        
        self._usage_stats = {
            "total_tokens": 0,
            "generations": 0
        }
        
        logger.info(f"HuggingFace provider initialized with model: {llm_model}")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using HuggingFace."""
        try:
            response = self.llm.predict(prompt, **kwargs)
            self._usage_stats["generations"] += 1
            return response
        except Exception as e:
            logger.error(f"Error generating HuggingFace response: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using HuggingFace."""
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error getting HuggingFace embedding: {str(e)}")
            raise
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts using HuggingFace."""
        try:
            embeddings = self.embeddings.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error getting HuggingFace embeddings: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get HuggingFace model information."""
        return {
            "provider": "huggingface",
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "device": self.device
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get HuggingFace usage statistics."""
        return self._usage_stats.copy()

class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider implementation."""
    
    def __init__(
        self,
        api_key: str,
        llm_model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """Initialize Anthropic provider."""
        try:
            from langchain_anthropic import ChatAnthropic
            from langchain_openai import OpenAIEmbeddings  # Anthropic uses OpenAI embeddings
        except ImportError:
            raise ImportError("Anthropic provider requires langchain-anthropic to be installed")
        
        self.api_key = api_key
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM
        self.llm = ChatAnthropic(
            anthropic_api_key=api_key,
            model=llm_model,
            temperature=temperature,
            max_tokens_to_sample=max_tokens
        )
        
        # Note: Anthropic doesn't provide embeddings, so we'll use OpenAI embeddings
        # You might want to use a different embedding provider
        self.embeddings = None
        
        self._usage_stats = {
            "total_tokens": 0,
            "generations": 0
        }
        
        logger.info(f"Anthropic provider initialized with model: {llm_model}")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic Claude."""
        try:
            response = self.llm.predict(prompt, **kwargs)
            self._usage_stats["generations"] += 1
            return response
        except Exception as e:
            logger.error(f"Error generating Anthropic response: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding - requires separate embedding provider."""
        raise NotImplementedError("Anthropic doesn't provide embeddings. Use a separate embedding provider.")
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings - requires separate embedding provider."""
        raise NotImplementedError("Anthropic doesn't provide embeddings. Use a separate embedding provider.")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Anthropic model information."""
        return {
            "provider": "anthropic",
            "llm_model": self.llm_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get Anthropic usage statistics."""
        return self._usage_stats.copy()

class LocalProvider(LLMProvider):
    """Local LLM provider using Ollama or similar local models."""
    
    def __init__(
        self,
        llm_model: str = "llama2",
        embedding_model: str = "llama2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """Initialize Local provider (Ollama)."""
        try:
            from langchain_ollama import OllamaLLM, OllamaEmbeddings
        except ImportError:
            raise ImportError("Local provider requires langchain-ollama to be installed")
        
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM
        self.llm = OllamaLLM(
            model=llm_model,
            base_url=base_url,
            temperature=temperature
        )
        
        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=base_url
        )
        
        self._usage_stats = {
            "generations": 0
        }
        
        logger.info(f"Local provider initialized with model: {llm_model}")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using local LLM."""
        try:
            response = self.llm.predict(prompt, **kwargs)
            self._usage_stats["generations"] += 1
            return response
        except Exception as e:
            logger.error(f"Error generating local response: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using local model."""
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error getting local embedding: {str(e)}")
            raise
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts using local model."""
        try:
            embeddings = self.embeddings.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error getting local embeddings: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get local model information."""
        return {
            "provider": "local",
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get local usage statistics."""
        return self._usage_stats.copy()

# Factory function to create LLM providers
def create_llm_provider(
    provider_type: str,
    **kwargs
) -> LLMProvider:
    """
    Factory function to create LLM providers.
    
    Args:
        provider_type: Type of provider ("openai", "huggingface", "anthropic", "local")
        **kwargs: Provider-specific arguments
        
    Returns:
        LLMProvider instance
    """
    provider_type = provider_type.lower()
    
    if provider_type == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_type == "huggingface":
        return HuggingFaceProvider(**kwargs)
    elif provider_type == "anthropic":
        return AnthropicProvider(**kwargs)
    elif provider_type == "local":
        return LocalProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
