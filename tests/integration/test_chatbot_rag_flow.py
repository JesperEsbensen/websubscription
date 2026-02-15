"""Integration tests for chatbot and RAG system interaction."""

import pytest
from django.test import Client
from django.urls import reverse
from unittest.mock import patch, Mock
from tests.factories.accounts import UserFactory
from tests.factories.chatbot import ChatSessionFactory

@pytest.mark.integration
@pytest.mark.django_db
class TestChatbotRAGIntegration:
    """Test integration between chatbot and RAG system."""
    
    def test_create_session_and_send_message(self):
        """Test creating a chat session and sending messages."""
        user = UserFactory()
        user.profile.email_confirmed = True
        user.profile.save()
        
        client = Client()
        client.force_login(user)
        
        # Step 1: Create chat session
        session_data = {
            'session_type': 'esg',
            'title': 'Test ESG Session'
        }
        
        response = client.post(
            reverse('chatbot:create_session'), 
            session_data,
            content_type='application/json'
        )
        assert response.status_code == 201
        session_data = response.json()
        session_id = session_data['session']['id']
        
        # Step 2: Send message to session
        with patch('chatbot.views.get_rag_response') as mock_rag:
            mock_rag.return_value = {
                'response': 'This is a test RAG response about ESG.',
                'sources': ['document1.pdf', 'document2.pdf'],
                'confidence': 0.95
            }
            
            message_data = {
                'session_id': session_id,
                'message': 'What are the ESG requirements?'
            }
            
            response = client.post(
                reverse('chatbot:send_message'),
                message_data,
                content_type='application/json'
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert 'response' in response_data
            mock_rag.assert_called_once()
        
        # Step 3: Retrieve session messages
        messages_response = client.get(
            reverse('chatbot:get_messages', args=[session_id])
        )
        assert messages_response.status_code == 200
        messages_data = messages_response.json()
        assert len(messages_data['messages']) == 2  # User + Bot message