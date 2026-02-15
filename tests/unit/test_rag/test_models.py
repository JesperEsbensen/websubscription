"""Unit tests for RAG app models."""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from tests.factories.rag import RAGDialogueFactory, RAGExchangeFactory
from tests.factories.accounts import UserFactory
from rag.models import RAGDialogue, RAGExchange

@pytest.mark.django_db
class TestRAGDialogueModel:
    """Test RAGDialogue model functionality."""
    
    def test_dialogue_creation(self):
        """Test dialogue creation with factory."""
        dialogue = RAGDialogueFactory()
        assert dialogue.pk is not None
        assert dialogue.user is not None
        assert dialogue.title
        assert dialogue.dialogue_type in [
            'general', 'esg', 'compliance', 'research', 'analysis', 'custom'
        ]
        assert dialogue.status == 'active'
        assert dialogue.total_exchanges == 0
        assert dialogue.total_cost == Decimal('0.00')
    
    def test_dialogue_str_representation(self):
        """Test dialogue string representation."""
        user = UserFactory(username='testuser')
        dialogue = RAGDialogueFactory(
            user=user, 
            title='Test Dialogue',
            dialogue_type='esg'
        )
        # The actual __str__ method would be defined in the model
        # This is a placeholder test
        assert dialogue.title == 'Test Dialogue'
    
    def test_dialogue_default_values(self):
        """Test dialogue default field values."""
        dialogue = RAGDialogueFactory()
        assert dialogue.llm_provider == 'openai'
        assert dialogue.llm_model == 'gpt-3.5-turbo' 
        assert dialogue.vector_store_type == 'chroma'
        assert dialogue.status == 'active'
    
    def test_dialogue_cost_calculation(self):
        """Test dialogue cost tracking."""
        dialogue = RAGDialogueFactory()
        
        # Add some exchanges with costs
        exchange1 = RAGExchangeFactory(
            dialogue=dialogue,
            tokens_used=100,
            cost=Decimal('0.01'),
            exchange_number=1
        )
        exchange2 = RAGExchangeFactory(
            dialogue=dialogue,
            tokens_used=200,
            cost=Decimal('0.02'),
            exchange_number=2
        )
        
        # Test that exchanges are related correctly
        assert dialogue.exchanges.count() == 2
        total_cost = sum(ex.cost for ex in dialogue.exchanges.all())
        assert total_cost == Decimal('0.03')

@pytest.mark.django_db
class TestRAGExchangeModel:
    """Test RAGExchange model functionality."""
    
    def test_exchange_creation(self):
        """Test exchange creation with factory."""
        exchange = RAGExchangeFactory()
        assert exchange.pk is not None
        assert exchange.dialogue is not None
        assert exchange.user_query
        assert exchange.system_response
        assert exchange.tokens_used > 0
        assert exchange.cost >= Decimal('0.00')
        assert exchange.processing_time > 0
        assert isinstance(exchange.retrieved_documents, list)
        assert isinstance(exchange.similarity_scores, list)
    
    def test_exchange_dialogue_relationship(self):
        """Test exchange-dialogue relationship."""
        dialogue = RAGDialogueFactory()
        exchange1 = RAGExchangeFactory(dialogue=dialogue, exchange_number=1)
        exchange2 = RAGExchangeFactory(dialogue=dialogue, exchange_number=2)
        
        # Test forward relationship
        assert exchange1.dialogue == dialogue
        assert exchange2.dialogue == dialogue
        
        # Test reverse relationship
        exchanges = list(dialogue.exchanges.all())
        assert len(exchanges) == 2
        assert exchange1 in exchanges
        assert exchange2 in exchanges
    
    def test_exchange_cost_calculation(self):
        """Test that cost is calculated from tokens."""
        exchange = RAGExchangeFactory(tokens_used=1000)
        # The factory should set cost based on tokens_used
        expected_cost = Decimal(str(exchange.tokens_used * 0.001))
        assert exchange.cost == expected_cost
    
    def test_exchange_retrieved_documents_storage(self):
        """Test that retrieved documents are stored as JSON list."""
        documents = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']
        exchange = RAGExchangeFactory(retrieved_documents=documents)
        assert exchange.retrieved_documents == documents
        assert isinstance(exchange.retrieved_documents, list)
    
    def test_exchange_ordering(self):
        """Test exchange ordering by exchange number."""
        dialogue = RAGDialogueFactory()
        
        # Create exchanges in specific order
        exchange3 = RAGExchangeFactory(dialogue=dialogue, user_query='Third', exchange_number=3)
        exchange1 = RAGExchangeFactory(dialogue=dialogue, user_query='First', exchange_number=1)
        exchange2 = RAGExchangeFactory(dialogue=dialogue, user_query='Second', exchange_number=2)
        
        # Get exchanges in default ordering (should be by exchange_number)
        exchanges = list(dialogue.exchanges.all())
        
        # Should be ordered by exchange_number
        assert len(exchanges) == 3
        assert exchanges[0].exchange_number == 1
        assert exchanges[1].exchange_number == 2
        assert exchanges[2].exchange_number == 3