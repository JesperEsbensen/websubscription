"""Factory classes for RAG app models."""

import factory
from decimal import Decimal
from rag.models import RAGDialogue, RAGExchange, DocumentChunk, RAGConfiguration
from .accounts import UserFactory

class RAGDialogueFactory(factory.django.DjangoModelFactory):
    """Factory for RAGDialogue model."""
    class Meta:
        model = RAGDialogue
    
    user = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=4)
    dialogue_type = factory.Faker('random_element', elements=[
        'general', 'esg', 'compliance', 'research', 'analysis', 'custom'
    ])
    status = 'active'
    llm_provider = 'openai'
    llm_model = 'gpt-3.5-turbo'
    vector_store_type = 'chroma'
    total_exchanges = 0
    total_tokens_used = 0
    total_cost = Decimal('0.00')

class RAGExchangeFactory(factory.django.DjangoModelFactory):
    """Factory for RAGExchange model."""
    class Meta:
        model = RAGExchange
    
    dialogue = factory.SubFactory(RAGDialogueFactory)
    user_query = factory.Faker('question')
    bot_response = factory.Faker('text', max_nb_chars=1000)
    tokens_used = factory.Faker('random_int', min=50, max=500)
    cost = factory.LazyAttribute(lambda obj: Decimal(str(obj.tokens_used * 0.001)))
    response_time_ms = factory.Faker('random_int', min=500, max=3000)
    confidence_score = factory.Faker('pyfloat', left_digits=0, right_digits=2, min_value=0.0, max_value=1.0)
    sources_used = factory.List([
        factory.Faker('file_name', extension='pdf') for _ in range(3)
    ])

class DocumentChunkFactory(factory.django.DjangoModelFactory):
    """Factory for DocumentChunk model."""
    class Meta:
        model = DocumentChunk
    
    document_name = factory.Faker('file_name', extension='pdf')
    chunk_text = factory.Faker('text', max_nb_chars=1000)
    chunk_index = factory.Sequence(int)
    metadata = factory.Dict({
        'page_number': factory.Faker('random_int', min=1, max=100),
        'source': factory.Faker('file_name', extension='pdf')
    })
    vector_id = factory.Faker('uuid4')
    collection_name = factory.Faker('random_element', elements=['esg', 'system', 'general'])

class RAGConfigurationFactory(factory.django.DjangoModelFactory):
    """Factory for RAGConfiguration model."""
    class Meta:
        model = RAGConfiguration
    
    user = factory.SubFactory(UserFactory)
    collection_name = factory.Faker('random_element', elements=['esg', 'system', 'general'])
    chunk_size = 1000
    chunk_overlap = 200
    temperature = 0.7
    max_tokens = 1000
    top_k = 5
    similarity_threshold = 0.7