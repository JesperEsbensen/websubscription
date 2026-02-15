"""Factory classes for chatbot app models."""

import factory
from chatbot.models import ChatSession, ChatMessage
from .accounts import UserFactory

class ChatSessionFactory(factory.django.DjangoModelFactory):
    """Factory for ChatSession model."""
    class Meta:
        model = ChatSession
    
    user = factory.SubFactory(UserFactory)
    session_type = factory.Faker('random_element', elements=[
        'general', 'esg', 'technical', 'billing'
    ])
    title = factory.Faker('sentence', nb_words=4)
    is_active = True

class ChatMessageFactory(factory.django.DjangoModelFactory):
    """Factory for ChatMessage model."""
    class Meta:
        model = ChatMessage
    
    session = factory.SubFactory(ChatSessionFactory)
    message_type = factory.Faker('random_element', elements=['user', 'bot'])
    content = factory.Faker('text', max_nb_chars=500)