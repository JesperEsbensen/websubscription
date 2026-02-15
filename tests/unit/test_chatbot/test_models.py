"""Unit tests for chatbot app models."""

import pytest
from django.utils import timezone
from tests.factories.chatbot import ChatSessionFactory, ChatMessageFactory
from tests.factories.accounts import UserFactory
from chatbot.models import ChatSession, ChatMessage

@pytest.mark.django_db
class TestChatSessionModel:
    """Test ChatSession model functionality."""
    
    def test_chat_session_creation(self):
        """Test chat session creation."""
        session = ChatSessionFactory()
        assert session.pk is not None
        assert session.user is not None
        assert session.session_type in ['general', 'esg', 'technical', 'billing']
        assert session.is_active
    
    def test_chat_session_str_representation(self):
        """Test chat session string representation."""
        user = UserFactory(username='testuser')
        session = ChatSessionFactory(user=user, session_type='general')
        str_repr = str(session)
        assert 'testuser' in str_repr
        assert 'General Support' in str_repr
    
    def test_last_message_time_property(self):
        """Test last_message_time property."""
        session = ChatSessionFactory()
        
        # No messages - should return session creation time
        assert session.last_message_time == session.created_at
        
        # Add a message
        message = ChatMessageFactory(session=session)
        assert session.last_message_time == message.created_at
    
    def test_message_count_property(self):
        """Test message_count property."""
        session = ChatSessionFactory()
        assert session.message_count == 0
        
        # Add messages
        ChatMessageFactory.create_batch(3, session=session)
        assert session.message_count == 3

@pytest.mark.django_db
class TestChatMessageModel:
    """Test ChatMessage model functionality."""
    
    def test_chat_message_creation(self):
        """Test chat message creation."""
        message = ChatMessageFactory()
        assert message.pk is not None
        assert message.session is not None
        assert message.message_type in ['user', 'bot']
        assert message.content
    
    def test_message_ordering(self):
        """Test that messages are ordered by creation time."""
        session = ChatSessionFactory()
        
        # Create messages in specific order
        msg1 = ChatMessageFactory(session=session, content='First')
        msg2 = ChatMessageFactory(session=session, content='Second') 
        msg3 = ChatMessageFactory(session=session, content='Third')
        
        messages = list(session.messages.all())
        assert messages[0].content == 'First'
        assert messages[1].content == 'Second'
        assert messages[2].content == 'Third'