"""Factory classes for RAG app models."""

import factory
from decimal import Decimal
from rag.models import RAGDialogue, RAGExchange, RAGDocument, RAGSystemLog
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
    user_query = factory.Faker('sentence', nb_words=8)  # Use sentence instead of 'question'
    system_response = factory.Faker('text', max_nb_chars=1000)
    tokens_used = factory.Faker('random_int', min=50, max=500)
    cost = factory.LazyAttribute(lambda obj: Decimal(str(obj.tokens_used * 0.001)))
    processing_time = factory.Faker('pyfloat', left_digits=1, right_digits=3, min_value=0.1, max_value=5.0)
    retrieved_documents = factory.List([
        factory.Faker('file_name', extension='pdf') for _ in range(3)
    ])
    similarity_scores = factory.List([
        factory.Faker('pyfloat', left_digits=0, right_digits=2, min_value=0.0, max_value=0.99) for _ in range(3)
    ])
    exchange_number = factory.Sequence(int)
    context_used = factory.Faker('text', max_nb_chars=500)
    retrieval_time = factory.Faker('pyfloat', left_digits=0, right_digits=3, min_value=0.001, max_value=0.999)
    context_prep_time = factory.Faker('pyfloat', left_digits=0, right_digits=3, min_value=0.001, max_value=0.499)
    llm_processing_time = factory.Faker('pyfloat', left_digits=1, right_digits=3, min_value=0.1, max_value=3.0)

class RAGDocumentFactory(factory.django.DjangoModelFactory):
    """Factory for RAGDocument model."""
    class Meta:
        model = RAGDocument
    
    user = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=3)
    file_name = factory.Faker('file_name', extension='pdf')
    file_path = factory.Faker('file_path', depth=3)
    file_size = factory.Faker('random_int', min=1024, max=1048576)  # 1KB to 1MB
    file_type = 'pdf'
    collection_name = factory.Faker('random_element', elements=['esg', 'system', 'general'])
    processing_status = 'completed'
    total_chunks = factory.Faker('random_int', min=1, max=50)
    metadata = factory.Dict({
        'pages': factory.Faker('random_int', min=1, max=100),
        'language': 'en'
    })

class RAGSystemLogFactory(factory.django.DjangoModelFactory):
    """Factory for RAGSystemLog model."""
    class Meta:
        model = RAGSystemLog
    
    level = factory.Faker('random_element', elements=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    category = factory.Faker('random_element', elements=[
        'document_processing', 'query_processing', 'system', 'external_api'
    ])
    message = factory.Faker('sentence')
    user = factory.SubFactory(UserFactory)
    metadata = factory.Dict({
        'operation': factory.Faker('word'),
        'duration_ms': factory.Faker('random_int', min=10, max=5000)
    })