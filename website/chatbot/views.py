from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
import json
from .models import ChatSession, ChatMessage

# Import RAG system components
from rag.services import RAGDialogueService
from rag.models import RAGDialogue
from rag.config import SESSION_DOCS_MAPPING
from rag.rag_manager import rag_manager
import os

@login_required
def chatbot_main(request):
    """Main chatbot page with sessions and messages"""
    # Get user's chat sessions
    sessions = ChatSession.objects.filter(user=request.user, is_active=True)
    
    # Get or create default session
    default_session, created = ChatSession.objects.get_or_create(
        user=request.user,
        session_type='general',
        is_active=True,
        defaults={'title': 'General Support'}
    )
    
    # Get messages for default session
    messages = default_session.messages.all()
    
    context = {
        'sessions': sessions,
        'current_session': default_session,
        'messages': messages,
    }
    return render(request, 'chatbot/main.html', context)

@login_required
def get_sessions(request):
    """Get all chat sessions for the user"""
    sessions = ChatSession.objects.filter(user=request.user, is_active=True)
    
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            'id': session.id,
            'type': session.session_type,
            'title': session.title or session.get_session_type_display(),
            'last_message_time': session.last_message_time.strftime('%Y-%m-%d %H:%M'),
            'message_count': session.message_count,
            'is_active': session.is_active,
        })
    
    return JsonResponse({'sessions': sessions_data})

@login_required
def get_messages(request, session_id):
    """Get messages for a specific session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = session.messages.all()
    
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'type': message.message_type,
            'content': message.content,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_user': message.is_user_message,
        })
    
    return JsonResponse({
        'session': {
            'id': session.id,
            'type': session.session_type,
            'title': session.title or session.get_session_type_display(),
        },
        'messages': messages_data
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Send a message and get bot response"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Get or create session
        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            session, created = ChatSession.objects.get_or_create(
                user=request.user,
                session_type='general',
                is_active=True,
                defaults={'title': 'General Support'}
            )
        
        # Save user message
        user_message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=message_content
        )
        
        # Generate bot response using RAG system
        bot_response = generate_bot_response(message_content, session.session_type, user=request.user)
        
        # Save bot message
        bot_message = ChatMessage.objects.create(
            session=session,
            message_type='bot',
            content=bot_response
        )
        
        # Update session timestamp
        session.save()  # This updates the updated_at field
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'created_at': user_message.created_at.strftime('%Y-%m-%d %H:%M'),
            },
            'bot_message': {
                'id': bot_message.id,
                'content': bot_message.content,
                'created_at': bot_message.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_session(request):
    """Create a new chat session"""
    try:
        data = json.loads(request.body)
        session_type = data.get('session_type', 'general')
        title = data.get('title', '')
        
        # Deactivate other sessions of the same type
        ChatSession.objects.filter(
            user=request.user, 
            session_type=session_type, 
            is_active=True
        ).update(is_active=False)
        
        # Create new session
        session = ChatSession.objects.create(
            user=request.user,
            session_type=session_type,
            title=title
        )
        
        # Add welcome message
        welcome_message = get_welcome_message(session_type)
        ChatMessage.objects.create(
            session=session,
            message_type='bot',
            content=welcome_message
        )
        
        return JsonResponse({
            'success': True,
            'session': {
                'id': session.id,
                'type': session.session_type,
                'title': session.title or session.get_session_type_display(),
                'created_at': session.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def clear_session(request, session_id):
    """Clear all messages from a session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.messages.all().delete()
    
    # Add welcome message back
    welcome_message = get_welcome_message(session.session_type)
    ChatMessage.objects.create(
        session=session,
        message_type='bot',
        content=welcome_message
    )
    
    return JsonResponse({'success': True})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def delete_session(request, session_id):
    """Delete a chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.is_active = False
    session.save()
    
    return JsonResponse({'success': True})

def generate_bot_response(user_message, session_type, user=None):
    """Generate bot response using RAG system based on user message and session type"""
    print(f"🔍 DEBUG: Starting RAG response generation")
    print(f"   - User message: {user_message}")
    print(f"   - Session type: {session_type}")
    print(f"   - User: {user.username if user else 'None'}")
    
    try:
        if not user:
            print(f"❌ DEBUG: No user provided, falling back to basic response")
            return get_fallback_response(user_message, session_type)
        
        print(f"✅ DEBUG: User authenticated, initializing RAG service")
        
        # Initialize RAG service
        rag_service = RAGDialogueService(user)
        print(f"✅ DEBUG: RAG service initialized successfully")
        
        # Map session types to RAG dialogue types
        dialogue_type_mapping = {
            'esg': 'esg',
            'technical': 'general',  # Technical support can use general knowledge
            'billing': 'general',    # Billing can use general knowledge
            'general': 'general'
        }
        
        rag_dialogue_type = dialogue_type_mapping.get(session_type, 'general')
        print(f"📋 DEBUG: Mapped session type '{session_type}' to RAG dialogue type '{rag_dialogue_type}'")
        
        # Get or create RAG dialogue for this session type
        print(f"🔍 DEBUG: Looking for existing dialogues...")
        existing_dialogues = rag_service.get_user_dialogues(
            status='active', 
            dialogue_type=rag_dialogue_type
        )
        print(f"📊 DEBUG: Found {len(existing_dialogues)} existing dialogues")
        
        if existing_dialogues:
            dialogue = existing_dialogues[0]  # Use the most recent active dialogue
            print(f"✅ DEBUG: Using existing dialogue: {dialogue.title} (ID: {dialogue.id})")
        else:
            print(f"🆕 DEBUG: No existing dialogue found, creating new one...")
            # Create new dialogue
            dialogue_title = f"{session_type.title()} Support Session"
            dialogue = rag_service.create_dialogue(
                title=dialogue_title,
                dialogue_type=rag_dialogue_type
            )
            print(f"✅ DEBUG: Created new dialogue: {dialogue.title} (ID: {dialogue.id})")
        
        # Check if RAG systems are initialized
        print(f"🔍 DEBUG: Checking RAG manager status...")
        print(f"   - RAG manager initialized: {rag_manager.is_initialized()}")
        print(f"   - Available systems: {rag_manager.get_available_systems()}")
        
        if not rag_manager.is_initialized():
            print(f"❌ DEBUG: RAG systems not initialized, falling back to basic response")
            return get_fallback_response(user_message, session_type)
        
        print(f"🤖 DEBUG: Processing query through RAG system...")
        result = rag_service.process_query(
            dialogue=dialogue,
            user_query=user_message,
            include_intermediate=False  # Don't include intermediate data for chatbot responses
        )
        
        print(f"📊 DEBUG: RAG result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if 'error' in result:
            print(f"❌ DEBUG: RAG returned error: {result['error']}")
            print(f"🔄 DEBUG: Falling back to basic response due to RAG error")
            return get_fallback_response(user_message, session_type)
        
        answer = result.get('answer')
        if answer:
            print(f"✅ DEBUG: RAG generated answer: {answer[:100]}...")
            return answer
        else:
            print(f"⚠️ DEBUG: RAG result has no 'answer' key, falling back")
            return get_fallback_response(user_message, session_type)
        
    except Exception as e:
        # Log the error and fall back to basic response
        print(f"❌ DEBUG: Exception in RAG system: {str(e)}")
        print(f"📋 DEBUG: Exception type: {type(e).__name__}")
        import traceback
        print(f"📋 DEBUG: Full traceback:")
        traceback.print_exc()
        print(f"🔄 DEBUG: Falling back to basic response due to exception")
        return get_fallback_response(user_message, session_type)

def get_fallback_response(user_message, session_type):
    """Fallback response when RAG system is unavailable"""
    message = user_message.lower()
    
    # Session-specific fallback responses
    if session_type == 'esg':
        if any(word in message for word in ['esg', 'environmental', 'social', 'governance']):
            return "ESG (Environmental, Social, and Governance) factors are crucial for modern businesses. Our platform provides comprehensive ESG tracking and reporting tools. Would you like to know more about specific ESG metrics, reporting frameworks, or compliance requirements?"
        else:
            return "I'm here to help with ESG guidance! I can assist with compliance questions, reporting frameworks, best practices, and ESG strategy development. What specific ESG topic would you like to discuss?"
    
    elif session_type == 'technical':
        if any(word in message for word in ['error', 'bug', 'issue', 'problem']):
            return "I can help you troubleshoot technical issues. Could you please provide more details about the problem you're experiencing? Include any error messages, steps to reproduce, and your browser/device information."
        else:
            return "I'm here to help with technical support! Please describe the issue you're experiencing, and I'll guide you through the solution."
    
    elif session_type == 'billing':
        if any(word in message for word in ['payment', 'billing', 'subscription', 'charge']):
            return "For billing and subscription questions, you can check your payment history in your profile, update payment methods, or contact our billing support team. What specific billing issue are you experiencing?"
        else:
            return "I can help with billing and subscription questions! This includes payment issues, subscription management, invoices, and account billing. What do you need assistance with?"
    
    else:  # general
        if any(word in message for word in ['esg', 'environmental', 'social', 'governance']):
            return "ESG (Environmental, Social, and Governance) factors are increasingly important for businesses. Our platform helps you track and report on these key areas. Would you like to know more about specific ESG metrics or reporting frameworks?"
        elif any(word in message for word in ['help', 'support']):
            return "I'm here to help! I can assist with ESG compliance, technical issues, billing questions, or general platform guidance. What specific area do you need help with?"
        else:
            return "Thank you for your message! I'm here to help with ESG support, technical issues, billing questions, or general guidance. How can I assist you further?"

def get_documents_path_for_session_type(session_type):
    """Get the appropriate documents path for the session type"""
    docs_path = SESSION_DOCS_MAPPING.get(session_type, SESSION_DOCS_MAPPING['general'])
    
    # Check if the path exists, otherwise use general path
    if os.path.exists(docs_path):
        return docs_path
    else:
        return SESSION_DOCS_MAPPING['general']

def get_welcome_message(session_type):
    """Get welcome message based on session type"""
    welcome_messages = {
        'general': "Hello! I'm your ESG support assistant. I'm here to help you with ESG compliance questions, technical support, billing and subscription help, and general platform guidance. How can I assist you today?",
        'esg': "Welcome to ESG Guidance! I can help you with ESG compliance, reporting frameworks, best practices, metrics tracking, and strategy development. What ESG topic would you like to discuss?",
        'technical': "Welcome to Technical Support! I'm here to help you resolve technical issues, troubleshoot problems, and get the most out of our platform. Please describe the issue you're experiencing.",
        'billing': "Welcome to Billing & Subscriptions! I can help you with payment questions, subscription management, invoices, and account billing. What billing-related assistance do you need?"
    }
    return welcome_messages.get(session_type, welcome_messages['general'])
