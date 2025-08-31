#!/usr/bin/env python3
"""
Simple test script to verify RAG system integration with chatbot
"""

import os
import sys
from pathlib import Path

# Add the Django project to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.website.settings')

# Import Django components
import django
django.setup()

from django.contrib.auth.models import User
from rag.services import RAGDialogueService
from rag.config import SESSION_DOCS_MAPPING

def test_rag_system():
    """Test the RAG system components"""
    print("🧪 Testing RAG System Components")
    print("=" * 50)
    
    # Test document paths
    print("\n📁 Testing Document Paths:")
    for session_type, docs_path in SESSION_DOCS_MAPPING.items():
        exists = os.path.exists(docs_path)
        print(f"  {session_type}: {docs_path} - {'✅' if exists else '❌'}")
    
    # Test RAG service creation
    print("\n🔧 Testing RAG Service:")
    try:
        # Create a test user
        user, created = User.objects.get_or_create(
            username='testuser_rag_simple',
            defaults={
                'email': 'testuser_rag_simple@example.com',
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
        
        # Initialize RAG service
        rag_service = RAGDialogueService(user)
        print("✅ RAG service initialized successfully")
        
        # Test dialogue creation
        dialogue = rag_service.create_dialogue(
            title="Test ESG Dialogue",
            dialogue_type="esg",
            llm_provider="openai",
            llm_model="gpt-3.5-turbo",
            vector_store_type="chroma"
        )
        print(f"✅ Created dialogue: {dialogue.title} (ID: {dialogue.id})")
        
        # Test query processing
        test_query = "What is ESG compliance?"
        print(f"\n❓ Testing query: {test_query}")
        
        result = rag_service.process_query(
            dialogue=dialogue,
            user_query=test_query,
            documents_path=SESSION_DOCS_MAPPING['esg'],
            include_intermediate=False
        )
        
        if 'error' in result:
            print(f"❌ Error processing query: {result['error']}")
        else:
            print(f"✅ Query processed successfully")
            print(f"🤖 Response: {result.get('answer', 'No answer')[:200]}...")
        
        # Clean up
        dialogue.status = 'deleted'
        dialogue.save()
        print("✅ Test dialogue cleaned up")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ RAG System Test Complete!")

if __name__ == "__main__":
    test_rag_system()
