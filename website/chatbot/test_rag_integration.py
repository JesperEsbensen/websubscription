#!/usr/bin/env python3
"""
Test script to verify RAG system integration with chatbot
"""

import os
import sys
import django
from pathlib import Path

# Add the Django project to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.website.settings')
django.setup()

from django.contrib.auth.models import User
from chatbot.views import generate_bot_response, get_documents_path_for_session_type

def test_rag_integration():
    """Test the RAG integration with the chatbot"""
    print("🧪 Testing RAG Integration with Chatbot")
    print("=" * 50)
    
    # Create or get a test user
    user, created = User.objects.get_or_create(
        username='testuser_chatbot',
        defaults={
            'email': 'testuser_chatbot@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"✅ Using existing test user: {user.username}")
    
    # Test different session types and queries
    test_cases = [
        {
            'session_type': 'esg',
            'queries': [
                'What is ESG compliance?',
                'Tell me about ESG frameworks',
                'What are ESG metrics?'
            ]
        },
        {
            'session_type': 'technical',
            'queries': [
                'I have a login problem',
                'How do I reset my password?',
                'The platform is loading slowly'
            ]
        },
        {
            'session_type': 'billing',
            'queries': [
                'What are your subscription plans?',
                'How do I cancel my subscription?',
                'I have a payment issue'
            ]
        },
        {
            'session_type': 'general',
            'queries': [
                'What features does your platform offer?',
                'How do I get started?',
                'What is ESG?'
            ]
        }
    ]
    
    for test_case in test_cases:
        session_type = test_case['session_type']
        queries = test_case['queries']
        
        print(f"\n📋 Testing {session_type.upper()} session type:")
        print("-" * 30)
        
        # Test document path
        docs_path = get_documents_path_for_session_type(session_type)
        print(f"📁 Documents path: {docs_path}")
        print(f"📁 Path exists: {os.path.exists(docs_path)}")
        
        for i, query in enumerate(queries, 1):
            print(f"\n❓ Query {i}: {query}")
            
            try:
                # Test RAG response
                rag_response = generate_bot_response(query, session_type, user=user)
                print(f"🤖 RAG Response: {rag_response[:200]}...")
                
                # Test fallback response (without user)
                fallback_response = generate_bot_response(query, session_type, user=None)
                print(f"🔄 Fallback Response: {fallback_response[:200]}...")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    print("\n✅ RAG Integration Test Complete!")

if __name__ == "__main__":
    test_rag_integration()
