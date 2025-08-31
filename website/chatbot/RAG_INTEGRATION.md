# RAG Integration with Chatbot

This document explains how the chatbot has been integrated with the RAG (Retrieval-Augmented Generation) system to provide more intelligent and context-aware responses.

## Overview

The chatbot now uses a RAG system instead of hardcoded responses. This provides several benefits:

- **More intelligent responses**: Uses AI to generate contextually relevant answers
- **Knowledge base integration**: Can access and reference specific documents
- **Session-specific knowledge**: Different document sets for different session types
- **Fallback mechanism**: Falls back to basic responses if RAG system is unavailable

## Architecture

### Components

1. **RAG System** (`website/rag/`):
   - `rag.py`: Core RAG functionality
   - `services.py`: High-level service layer
   - `models.py`: Database models for dialogues and exchanges
   - `llm_providers.py`: LLM provider interface
   - `config.py`: Configuration settings

2. **Chatbot Integration** (`website/chatbot/views.py`):
   - `generate_bot_response()`: Main function that uses RAG system
   - `get_fallback_response()`: Fallback responses when RAG fails
   - `get_documents_path_for_session_type()`: Maps session types to document paths

3. **Knowledge Base** (`website/rag/test_docs/`):
   - Session-specific document directories
   - Text files containing relevant information

## Session Types and Documents

The system maps different session types to specific document directories:

- **ESG Sessions** (`test_docs/esg/`):
  - `esg_info.txt`: Basic ESG information
  - `compliance_frameworks.txt`: ESG frameworks and standards
  - `metrics_and_kpis.txt`: ESG metrics and KPIs

- **Technical Support** (`test_docs/technical/`):
  - `technical_support.txt`: Common technical issues and solutions

- **Billing Support** (`test_docs/billing/`):
  - `billing_support.txt`: Subscription plans and billing information

- **General** (`test_docs/`):
  - `general_platform_info.txt`: Platform overview and features

## Configuration

### Environment Variables

The system uses the following environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
```

### Dependencies

Additional dependencies have been added to `requirements.txt`:

```
langchain==0.2.0
langchain-openai==0.1.0
langchain-community==0.2.0
chromadb==0.4.22
openai==1.12.0
numpy==1.24.3
scikit-learn==1.3.0
faiss-cpu==1.7.4
```

## How It Works

1. **User sends a message** to the chatbot
2. **Session type is determined** (esg, technical, billing, general)
3. **RAG system is initialized** with appropriate documents
4. **Query is processed** through the RAG pipeline:
   - Document retrieval based on similarity
   - Context generation
   - LLM response generation
5. **Response is returned** to the user
6. **Fallback mechanism** provides basic responses if RAG fails

## Testing

Run the test script to verify the integration:

```bash
cd website/chatbot
python test_rag_integration.py
```

This will test:
- Document path resolution
- RAG response generation
- Fallback response generation
- Different session types

## Adding New Knowledge

To add new knowledge to the system:

1. **Add documents** to the appropriate directory in `test_docs/`
2. **Update session mapping** in `config.py` if needed
3. **Test the integration** with the test script

## Troubleshooting

### Common Issues

1. **RAG system fails to initialize**:
   - Check OpenAI API key is set
   - Verify dependencies are installed
   - Check document paths exist

2. **No response generated**:
   - Check fallback responses are working
   - Verify document content is relevant
   - Check LLM provider configuration

3. **Poor response quality**:
   - Improve document quality and relevance
   - Adjust chunk size and overlap settings
   - Fine-tune LLM parameters

### Logging

The system includes comprehensive logging. Check logs for:
- RAG system initialization
- Document processing
- Query processing
- Error messages

## Future Enhancements

Potential improvements:

1. **Dynamic document loading**: Load documents based on user context
2. **Multi-modal support**: Support for images, PDFs, etc.
3. **Conversation memory**: Maintain context across multiple exchanges
4. **Custom embeddings**: Domain-specific embedding models
5. **Hybrid search**: Combine semantic and keyword search
6. **Response caching**: Cache common responses for performance
