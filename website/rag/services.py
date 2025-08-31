"""
Service layer for integrating RAG system with database models.
Provides high-level functions for managing dialogues and exchanges.
"""

from typing import Dict, Any, Optional, List
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import hashlib
import json

from .models import RAGDialogue, RAGExchange, RAGDocument, RAGSystemLog
from .rag import RAGSystem
from .llm_providers import create_llm_provider

class RAGDialogueService:
    """
    Service class for managing RAG dialogues and exchanges.
    Integrates the RAG system with database persistence.
    """
    
    def __init__(self, user: User):
        self.user = user
    
    def create_dialogue(
        self, 
        title: str, 
        dialogue_type: str = 'general',
        llm_provider: str = 'openai',
        llm_model: str = 'gpt-3.5-turbo',
        vector_store_type: str = 'chroma',
        **kwargs
    ) -> RAGDialogue:
        """
        Create a new RAG dialogue for the user.
        
        Args:
            title: Title of the dialogue
            dialogue_type: Type of dialogue (general, esg, compliance, etc.)
            llm_provider: LLM provider to use
            llm_model: LLM model to use
            vector_store_type: Vector store type
            **kwargs: Additional arguments for RAGDialogue creation
            
        Returns:
            Created RAGDialogue instance
        """
        with transaction.atomic():
            dialogue = RAGDialogue.objects.create(
                user=self.user,
                title=title,
                dialogue_type=dialogue_type,
                llm_provider=llm_provider,
                llm_model=llm_model,
                vector_store_type=vector_store_type,
                **kwargs
            )
            
            # Log the creation
            RAGSystemLog.log_system_event(
                level='info',
                message=f"Created new RAG dialogue: {title}",
                details={
                    'dialogue_type': dialogue_type,
                    'llm_provider': llm_provider,
                    'llm_model': llm_model,
                    'vector_store_type': vector_store_type
                },
                user=self.user,
                dialogue=dialogue
            )
            
            return dialogue
    
    def get_user_dialogues(
        self, 
        status: str = 'active',
        dialogue_type: Optional[str] = None
    ) -> List[RAGDialogue]:
        """
        Get all dialogues for the user.
        
        Args:
            status: Filter by status (active, archived, deleted)
            dialogue_type: Filter by dialogue type
            
        Returns:
            List of RAGDialogue instances
        """
        queryset = RAGDialogue.objects.filter(user=self.user, status=status)
        
        if dialogue_type:
            queryset = queryset.filter(dialogue_type=dialogue_type)
        
        return queryset.order_by('-last_activity')
    
    def get_dialogue(self, dialogue_id: int) -> Optional[RAGDialogue]:
        """
        Get a specific dialogue by ID.
        
        Args:
            dialogue_id: ID of the dialogue
            
        Returns:
            RAGDialogue instance or None if not found
        """
        try:
            return RAGDialogue.objects.get(id=dialogue_id, user=self.user)
        except RAGDialogue.DoesNotExist:
            return None
    
    def process_query(
        self, 
        dialogue: RAGDialogue, 
        user_query: str,
        documents_path: str = None,
        include_intermediate: bool = True,
        **rag_kwargs
    ) -> Dict[str, Any]:
        """
        Process a user query through the RAG system and persist the exchange.
        
        Args:
            dialogue: The dialogue to add the exchange to
            user_query: The user's question
            documents_path: Path to documents for the RAG system
            include_intermediate: Whether to include intermediate processing info
            **rag_kwargs: Additional arguments for RAG system
            
        Returns:
            Dictionary containing the response and exchange information
        """
        try:
            print(f"🔍 DEBUG: Services process_query - Creating LLM provider")
            print(f"   - Provider type: {dialogue.llm_provider}")
            print(f"   - LLM model: {dialogue.llm_model}")
            print(f"   - Additional kwargs: {rag_kwargs}")
            
            # Create RAG system instance
            llm_provider = create_llm_provider(
                dialogue.llm_provider,
                llm_model=dialogue.llm_model,
                **rag_kwargs
            )
            
            print(f"✅ DEBUG: LLM provider created successfully")
            
            print(f"🔍 DEBUG: Creating RAG system")
            print(f"   - Vector store type: {dialogue.vector_store_type}")
            
            rag_system = RAGSystem(
                llm_provider=llm_provider,
                vector_store_type=dialogue.vector_store_type
            )
            
            print(f"✅ DEBUG: RAG system created successfully")
            
            # Load documents if path provided
            if documents_path:
                print(f"🔍 DEBUG: Loading documents from: {documents_path}")
                documents = rag_system.load_directory(documents_path)
                print(f"📊 DEBUG: Loaded {len(documents)} documents")
                print(f"🔍 DEBUG: Creating vector store")
                rag_system.create_vector_store(documents)
                print(f"✅ DEBUG: Vector store created successfully")
            else:
                print(f"⚠️ DEBUG: No documents path provided, skipping document loading")
            
            # Process the query
            print(f"🔍 DEBUG: Processing query: {user_query}")
            result = rag_system.query(user_query, include_intermediate=include_intermediate)
            print(f"📊 DEBUG: Query result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if 'error' in result:
                # Log the error
                RAGSystemLog.log_system_event(
                    level='error',
                    message=f"Error processing query: {result['error']}",
                    details={'user_query': user_query},
                    user=self.user,
                    dialogue=dialogue
                )
                return result
            
            print(f"🔍 DEBUG: Query result: {result}")
            
            # Extract processing information
            processing_info = result.get('processing_info', {})
            usage_stats = result.get('usage_stats', {})
            intermediate_data = result.get('intermediate_data', {})
            
            # Convert any Decimal values in usage_stats to float for JSON serialization
            if usage_stats:
                usage_stats = {k: float(v) if isinstance(v, Decimal) else v for k, v in usage_stats.items()}
            
            # Ensure all Decimal values in the entire result are converted to float
            def convert_decimals_to_float(obj):
                """Recursively convert all Decimal values to float in a nested structure."""
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: convert_decimals_to_float(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals_to_float(item) for item in obj]
                else:
                    return obj
            
            # Convert all Decimal values in the result
            result = convert_decimals_to_float(result)
            
            # Calculate costs and tokens
            tokens_used = usage_stats.get('total_tokens', 0)
            cost_float = float(usage_stats.get('total_cost', 0.0))
            cost = Decimal(str(cost_float))
            
            # Create the exchange
            with transaction.atomic():
                exchange = RAGExchange.objects.create(
                    dialogue=dialogue,
                    user_query=user_query,
                    system_response=result['answer'],
                    exchange_number=dialogue.exchanges.count() + 1,
                    processing_time=processing_info.get('total_duration', 0.0),
                    tokens_used=tokens_used,
                    cost=cost,
                    retrieval_time=processing_info.get('steps', [{}])[0].get('duration', 0.0) if processing_info.get('steps') else 0.0,
                    context_prep_time=processing_info.get('steps', [{}])[1].get('duration', 0.0) if len(processing_info.get('steps', [])) > 1 else 0.0,
                    llm_processing_time=processing_info.get('steps', [{}])[2].get('duration', 0.0) if len(processing_info.get('steps', [])) > 2 else 0.0,
                    retrieved_documents=intermediate_data.get('retrieved_documents', []),
                    context_used=intermediate_data.get('context_used', ''),
                    similarity_scores=intermediate_data.get('retrieval_scores', [])
                )
                
                # Update dialogue statistics
                dialogue.total_exchanges += 1
                dialogue.total_tokens_used += tokens_used
                dialogue.total_cost += cost
                dialogue.update_activity()
                dialogue.save()
                
                # Log the successful exchange
                RAGSystemLog.log_system_event(
                    level='info',
                    message=f"Processed query: {user_query[:50]}...",
                    details={
                        'processing_time': processing_info.get('total_duration', 0.0),
                        'tokens_used': tokens_used,
                        'cost': cost_float,
                        'documents_retrieved': len(intermediate_data.get('retrieved_documents', []))
                    },
                    user=self.user,
                    dialogue=dialogue,
                    exchange=exchange
                )
            
            # Add exchange information to result
            result['exchange'] = {
                'id': exchange.id,
                'exchange_number': exchange.exchange_number,
                'processing_time': exchange.processing_time,
                'tokens_used': exchange.tokens_used,
                'cost': float(exchange.cost),
                'document_count': exchange.document_count,
                'average_similarity_score': exchange.average_similarity_score
            }
            
            return result
            
        except Exception as e:
            # Log the exception
            RAGSystemLog.log_system_event(
                level='error',
                message=f"Exception processing query: {str(e)}",
                details={'user_query': user_query, 'exception': str(e)},
                user=self.user,
                dialogue=dialogue
            )
            return {'error': str(e)}
    
    def get_dialogue_exchanges(self, dialogue: RAGDialogue) -> List[RAGExchange]:
        """
        Get all exchanges for a dialogue.
        
        Args:
            dialogue: The dialogue to get exchanges for
            
        Returns:
            List of RAGExchange instances
        """
        return dialogue.exchanges.all().order_by('exchange_number')
    
    def archive_dialogue(self, dialogue: RAGDialogue) -> bool:
        """
        Archive a dialogue.
        
        Args:
            dialogue: The dialogue to archive
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dialogue.status = 'archived'
            dialogue.save()
            
            RAGSystemLog.log_system_event(
                level='info',
                message=f"Archived dialogue: {dialogue.title}",
                user=self.user,
                dialogue=dialogue
            )
            
            return True
        except Exception as e:
            RAGSystemLog.log_system_event(
                level='error',
                message=f"Error archiving dialogue: {str(e)}",
                user=self.user,
                dialogue=dialogue
            )
            return False
    
    def delete_dialogue(self, dialogue: RAGDialogue) -> bool:
        """
        Mark a dialogue as deleted.
        
        Args:
            dialogue: The dialogue to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dialogue.status = 'deleted'
            dialogue.save()
            
            RAGSystemLog.log_system_event(
                level='info',
                message=f"Deleted dialogue: {dialogue.title}",
                user=self.user,
                dialogue=dialogue
            )
            
            return True
        except Exception as e:
            RAGSystemLog.log_system_event(
                level='error',
                message=f"Error deleting dialogue: {str(e)}",
                user=self.user,
                dialogue=dialogue
            )
            return False

class RAGDocumentService:
    """
    Service class for managing RAG documents.
    """
    
    @staticmethod
    def create_document(
        title: str,
        document_type: str,
        source_path: str,
        content: str,
        chunk_count: int = 0,
        embedding_model: str = 'text-embedding-ada-002',
        vector_store_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> RAGDocument:
        """
        Create a new RAG document.
        
        Args:
            title: Document title
            document_type: Type of document
            source_path: Path to the original document
            content: Document content
            chunk_count: Number of chunks created
            embedding_model: Embedding model used
            vector_store_id: ID in vector store
            metadata: Additional metadata
            
        Returns:
            Created RAGDocument instance
        """
        # Generate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Check if document already exists
        existing_doc = RAGDocument.objects.filter(content_hash=content_hash).first()
        if existing_doc:
            return existing_doc
        
        # Create new document
        document = RAGDocument.objects.create(
            title=title,
            document_type=document_type,
            source_path=source_path,
            content_hash=content_hash,
            chunk_count=chunk_count,
            embedding_model=embedding_model,
            vector_store_id=vector_store_id,
            metadata=metadata or {}
        )
        
        # Log document creation
        RAGSystemLog.log_system_event(
            level='info',
            message=f"Created RAG document: {title}",
            details={
                'document_type': document_type,
                'chunk_count': chunk_count,
                'embedding_model': embedding_model
            }
        )
        
        return document
    
    @staticmethod
    def update_document_usage(document: RAGDocument, similarity_score: float = None):
        """
        Update document usage statistics.
        
        Args:
            document: The document to update
            similarity_score: Similarity score from retrieval
        """
        document.update_usage_stats(similarity_score)
    
    @staticmethod
    def get_popular_documents(limit: int = 10) -> List[RAGDocument]:
        """
        Get the most frequently retrieved documents.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of popular RAGDocument instances
        """
        return RAGDocument.objects.filter(retrieval_count__gt=0).order_by('-retrieval_count')[:limit]
    
    @staticmethod
    def get_documents_by_type(document_type: str) -> List[RAGDocument]:
        """
        Get documents by type.
        
        Args:
            document_type: Type of documents to retrieve
            
        Returns:
            List of RAGDocument instances
        """
        return RAGDocument.objects.filter(document_type=document_type).order_by('-last_accessed')

class RAGAnalyticsService:
    """
    Service class for RAG system analytics and reporting.
    """
    
    @staticmethod
    def get_user_statistics(user: User) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a user.
        
        Args:
            user: The user to get statistics for
            
        Returns:
            Dictionary containing user statistics
        """
        dialogues = RAGDialogue.objects.filter(user=user, status='active')
        
        total_dialogues = dialogues.count()
        total_exchanges = sum(d.total_exchanges for d in dialogues)
        total_tokens = sum(d.total_tokens_used for d in dialogues)
        total_cost = sum(float(d.total_cost) for d in dialogues)
        
        # Get recent activity
        recent_dialogues = dialogues.order_by('-last_activity')[:5]
        
        # Get dialogue type distribution
        type_distribution = {}
        for dialogue in dialogues:
            dialogue_type = dialogue.dialogue_type
            type_distribution[dialogue_type] = type_distribution.get(dialogue_type, 0) + 1
        
        return {
            'total_dialogues': total_dialogues,
            'total_exchanges': total_exchanges,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'recent_dialogues': [
                {
                    'id': d.id,
                    'title': d.title,
                    'type': d.dialogue_type,
                    'last_activity': d.last_activity,
                    'exchanges': d.total_exchanges
                } for d in recent_dialogues
            ],
            'type_distribution': type_distribution
        }
    
    @staticmethod
    def get_system_statistics() -> Dict[str, Any]:
        """
        Get system-wide statistics.
        
        Args:
            None
            
        Returns:
            Dictionary containing system statistics
        """
        total_dialogues = RAGDialogue.objects.filter(status='active').count()
        total_exchanges = RAGExchange.objects.count()
        total_documents = RAGDocument.objects.count()
        total_logs = RAGSystemLog.objects.count()
        
        # Get recent activity
        recent_exchanges = RAGExchange.objects.select_related('dialogue', 'dialogue__user').order_by('-created_at')[:10]
        
        # Get error rate
        error_logs = RAGSystemLog.objects.filter(level='error').count()
        total_logs_recent = RAGSystemLog.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        error_rate = (error_logs / max(1, total_logs_recent)) * 100 if total_logs_recent > 0 else 0
        
        return {
            'total_dialogues': total_dialogues,
            'total_exchanges': total_exchanges,
            'total_documents': total_documents,
            'total_logs': total_logs,
            'error_rate': error_rate,
            'recent_exchanges': [
                {
                    'id': e.id,
                    'dialogue_title': e.dialogue.title,
                    'user': e.dialogue.user.username,
                    'query': e.user_query[:50] + '...' if len(e.user_query) > 50 else e.user_query,
                    'processing_time': e.processing_time,
                    'created_at': e.created_at
                } for e in recent_exchanges
            ]
        }
