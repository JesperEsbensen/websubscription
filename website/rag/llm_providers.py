# LLM Provider Interface and Implementations
# This module provides a neutral interface for different LLM providers

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import os

# Import configuration
try:
    from .config import (
        OPENAI_API_KEY, OPENAI_MODEL, OPENAI_EMBEDDING_MODEL,
        DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
    )
    print(f"✅ DEBUG: Successfully imported config values:")
    print(f"   - OPENAI_MODEL: {OPENAI_MODEL}")
    print(f"   - OPENAI_EMBEDDING_MODEL: {OPENAI_EMBEDDING_MODEL}")
except ImportError as e:
    # Fallback values if config is not available
    print(f"⚠️ DEBUG: Failed to import config, using fallback values: {e}")
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = 'gpt-3.5-turbo'
    OPENAI_EMBEDDING_MODEL = 'text-embedding-ada-002'
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 1000

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
        api_key: str = None,
        llm_model: str = None,
        embedding_model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        """Initialize OpenAI provider."""
        try:
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            from langchain_community.callbacks.manager import get_openai_callback
        except ImportError:
            raise ImportError("OpenAI provider requires langchain-openai to be installed")
        
        # Debug: Print configuration values
        print(f"🔧 DEBUG: OpenAIProvider configuration:")
        print(f"   - Provided api_key: {'***' + api_key[-4:] if api_key else 'None'}")
        print(f"   - Config OPENAI_API_KEY: {'***' + OPENAI_API_KEY[-4:] if OPENAI_API_KEY else 'None'}")
        print(f"   - Provided llm_model: {llm_model}")
        print(f"   - Config OPENAI_MODEL: {OPENAI_MODEL}")
        print(f"   - Provided embedding_model: {embedding_model}")
        print(f"   - Config OPENAI_EMBEDDING_MODEL: {OPENAI_EMBEDDING_MODEL}")
        print(f"   - Provided temperature: {temperature}")
        print(f"   - Config DEFAULT_TEMPERATURE: {DEFAULT_TEMPERATURE}")
        print(f"   - Provided max_tokens: {max_tokens}")
        print(f"   - Config DEFAULT_MAX_TOKENS: {DEFAULT_MAX_TOKENS}")
        
        # Use provided values or fall back to config defaults
        self.api_key = api_key or OPENAI_API_KEY
        self.llm_model = llm_model or OPENAI_MODEL
        self.embedding_model = embedding_model or OPENAI_EMBEDDING_MODEL
        self.temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS
        
        # Ensure embedding_model is never None
        if not self.embedding_model:
            self.embedding_model = "text-embedding-ada-002"
            print(f"⚠️ DEBUG: embedding_model was None, using default: {self.embedding_model}")
        
        # Debug: Print final values
        print(f"🔧 DEBUG: Final OpenAIProvider values:")
        print(f"   - Final api_key: {'***' + self.api_key[-4:] if self.api_key else 'None'}")
        print(f"   - Final llm_model: {self.llm_model}")
        print(f"   - Final embedding_model: {self.embedding_model}")
        print(f"   - Final temperature: {self.temperature}")
        print(f"   - Final max_tokens: {self.max_tokens}")
        
        # Validate API key
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize components
        print(f"🔧 DEBUG: Initializing ChatOpenAI with:")
        print(f"   - api_key: {'***' + self.api_key[-4:] if self.api_key else 'None'}")
        print(f"   - model: {self.llm_model}")
        print(f"   - temperature: {self.temperature}")
        print(f"   - max_tokens: {self.max_tokens}")
        
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model=self.llm_model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        print(f"🔧 DEBUG: Initializing OpenAIEmbeddings with:")
        print(f"   - api_key: {'***' + self.api_key[-4:] if self.api_key else 'None'}")
        print(f"   - model: {self.embedding_model}")
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.api_key,
            model=self.embedding_model
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
                response = self.llm.invoke(prompt, **kwargs)
                
                # Update usage stats
                self._usage_stats["total_tokens"] += cb.total_tokens
                self._usage_stats["prompt_tokens"] += cb.prompt_tokens
                self._usage_stats["completion_tokens"] += cb.completion_tokens
                self._usage_stats["total_cost"] += float(cb.total_cost)
                
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
        stats = self._usage_stats.copy()
        # Ensure all values are JSON serializable
        stats["total_cost"] = float(stats["total_cost"])
        return stats

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
            response = self.llm.invoke(prompt, **kwargs)
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
            response = self.llm.invoke(prompt, **kwargs)
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
            response = self.llm.invoke(prompt, **kwargs)
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
        # For OpenAI, if no api_key is provided, use the one from config
        if 'api_key' not in kwargs:
            kwargs['api_key'] = OPENAI_API_KEY
        return OpenAIProvider(**kwargs)
    elif provider_type == "huggingface":
        return HuggingFaceProvider(**kwargs)
    elif provider_type == "anthropic":
        return AnthropicProvider(**kwargs)
    elif provider_type == "local":
        return LocalProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
