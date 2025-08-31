#!/usr/bin/env python3
"""
Example usage of the RAG dialogue database structure.
This script demonstrates how to create dialogues, process queries, and manage exchanges.
"""

import os
import sys
import django
from pathlib import Path

# Add the Django project to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
django.setup()

from django.contrib.auth.models import User
from rag.services import RAGDialogueService, RAGDocumentService, RAGAnalyticsService
from rag.models import RAGDialogue, RAGExchange

def create_test_user():
    """Create a test user if it doesn't exist."""
    username = 'testuser_rag'
    email = 'testuser_rag@example.com'
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {username}")
    else:
        print(f"✅ Using existing test user: {username}")
    
    return user

def example_dialogue_management():
    """Example of creating and managing RAG dialogues."""
    print("\n🎭 RAG Dialogue Management Example")
    print("=" * 50)
    
    # Create test user
    user = create_test_user()
    
    # Initialize service
    service = RAGDialogueService(user)
    
    # Create a new dialogue
    print("\n📝 Creating new RAG dialogue...")
    dialogue = service.create_dialogue(
        title="ESG Compliance Analysis",
        dialogue_type="esg",
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        vector_store_type="chroma"
    )
    print(f"✅ Created dialogue: {dialogue.title} (ID: {dialogue.id})")
    
    # Get user's dialogues
    print("\n📋 Getting user dialogues...")
    dialogues = service.get_user_dialogues(status='active')
    print(f"✅ Found {len(dialogues)} active dialogues:")
    for d in dialogues:
        print(f"  - {d.title} ({d.dialogue_type}) - {d.total_exchanges} exchanges")
    
    return dialogue, service

def example_query_processing(dialogue, service):
    """Example of processing queries through the RAG system."""
    print("\n🤖 RAG Query Processing Example")
    print("=" * 50)
    
    # Example queries
    queries = [
        "What is ESG compliance?",
        "How do environmental factors affect business?",
        "What are the social responsibilities of companies?",
        "How can governance improve corporate performance?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n❓ Processing Query {i}: {query}")
        
        # Process the query
        result = service.process_query(
            dialogue=dialogue,
            user_query=query,
            documents_path="./test_docs",  # Use test documents
            include_intermediate=True
        )
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Response: {result['answer'][:100]}...")
            
            # Display exchange information
            if 'exchange' in result:
                exchange_info = result['exchange']
                print(f"📊 Exchange #{exchange_info['exchange_number']}")
                print(f"   ⏱️  Processing time: {exchange_info['processing_time']:.3f}s")
                print(f"   🧠 Tokens used: {exchange_info['tokens_used']}")
                print(f"   💰 Cost: ${exchange_info['cost']:.6f}")
                print(f"   📄 Documents retrieved: {exchange_info['document_count']}")
                print(f"   🎯 Avg similarity score: {exchange_info['average_similarity_score']:.3f}")
            
            # Display processing steps if available
            if 'processing_info' in result:
                processing = result['processing_info']
                print(f"   📋 Total time: {processing['total_duration']:.3f}s")
                for step in processing['steps']:
                    step_name = step['step'].replace('_', ' ').title()
                    print(f"     - {step_name}: {step['duration']:.3f}s")

def example_dialogue_analytics(dialogue, service):
    """Example of dialogue analytics and reporting."""
    print("\n📈 Dialogue Analytics Example")
    print("=" * 50)
    
    # Get dialogue exchanges
    exchanges = service.get_dialogue_exchanges(dialogue)
    print(f"📊 Dialogue has {len(exchanges)} exchanges")
    
    # Display exchange details
    for exchange in exchanges:
        print(f"\n📝 Exchange #{exchange.exchange_number}")
        print(f"   Query: {exchange.user_query[:50]}...")
        print(f"   Response: {exchange.system_response[:50]}...")
        print(f"   Processing: {exchange.processing_time:.3f}s")
        print(f"   Tokens: {exchange.tokens_used}")
        print(f"   Cost: ${float(exchange.cost):.6f}")
        print(f"   Documents: {exchange.document_count}")
        print(f"   Efficiency: {'✅' if exchange.is_efficient else '⚠️'}")
    
    # Get dialogue summary
    summary = dialogue.get_summary()
    print(f"\n📋 Dialogue Summary:")
    print(f"   Total exchanges: {summary['total_exchanges']}")
    print(f"   Duration: {summary['duration']}")
    print(f"   Total tokens: {summary['total_tokens']}")
    print(f"   Total cost: ${summary['total_cost']:.6f}")
    
    # Get user statistics
    user_stats = RAGAnalyticsService.get_user_statistics(dialogue.user)
    print(f"\n👤 User Statistics:")
    print(f"   Total dialogues: {user_stats['total_dialogues']}")
    print(f"   Total exchanges: {user_stats['total_exchanges']}")
    print(f"   Total tokens: {user_stats['total_tokens']}")
    print(f"   Total cost: ${user_stats['total_cost']:.6f}")
    print(f"   Dialogue types: {user_stats['type_distribution']}")

def example_dialogue_management_operations(dialogue, service):
    """Example of dialogue management operations."""
    print("\n🔧 Dialogue Management Operations")
    print("=" * 50)
    
    # Archive dialogue
    print("\n📦 Archiving dialogue...")
    success = service.archive_dialogue(dialogue)
    if success:
        print("✅ Dialogue archived successfully")
        
        # Check archived dialogues
        archived_dialogues = service.get_user_dialogues(status='archived')
        print(f"📋 Found {len(archived_dialogues)} archived dialogues")
        
        # Reactivate dialogue (change status back to active)
        dialogue.status = 'active'
        dialogue.save()
        print("✅ Dialogue reactivated")
    else:
        print("❌ Failed to archive dialogue")

def example_system_analytics():
    """Example of system-wide analytics."""
    print("\n🌐 System Analytics Example")
    print("=" * 50)
    
    # Get system statistics
    system_stats = RAGAnalyticsService.get_system_statistics()
    
    print(f"📊 System Statistics:")
    print(f"   Total dialogues: {system_stats['total_dialogues']}")
    print(f"   Total exchanges: {system_stats['total_exchanges']}")
    print(f"   Total documents: {system_stats['total_documents']}")
    print(f"   Total logs: {system_stats['total_logs']}")
    print(f"   Error rate: {system_stats['error_rate']:.2f}%")
    
    print(f"\n🕒 Recent Activity:")
    for exchange in system_stats['recent_exchanges']:
        print(f"   - {exchange['user']}: {exchange['query']} ({exchange['processing_time']:.3f}s)")

def main():
    """Main function to run all examples."""
    print("🚀 RAG Dialogue Database Structure Examples")
    print("=" * 60)
    
    try:
        # Example 1: Dialogue Management
        dialogue, service = example_dialogue_management()
        
        # Example 2: Query Processing
        example_query_processing(dialogue, service)
        
        # Example 3: Dialogue Analytics
        example_dialogue_analytics(dialogue, service)
        
        # Example 4: Management Operations
        example_dialogue_management_operations(dialogue, service)
        
        # Example 5: System Analytics
        example_system_analytics()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
