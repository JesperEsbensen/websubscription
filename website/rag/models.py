from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class RAGDialogue(models.Model):
    """
    Represents a dialogue session between a user and the RAG system.
    Each dialogue has a title and contains multiple exchanges.
    """
    DIALOGUE_TYPES = [
        ('general', 'General Query'),
        ('esg', 'ESG Analysis'),
        ('compliance', 'Compliance Check'),
        ('research', 'Research Query'),
        ('analysis', 'Data Analysis'),
        ('custom', 'Custom Topic'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rag_dialogues')
    title = models.CharField(max_length=200, help_text="Title of the dialogue")
    dialogue_type = models.CharField(max_length=20, choices=DIALOGUE_TYPES, default='general')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # RAG System Configuration
    llm_provider = models.CharField(max_length=50, default='openai', help_text="LLM provider used")
    llm_model = models.CharField(max_length=100, default='gpt-3.5-turbo', help_text="LLM model used")
    vector_store_type = models.CharField(max_length=20, default='chroma', help_text="Vector store type")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    # Statistics
    total_exchanges = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.00)
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name = "RAG Dialogue"
        verbose_name_plural = "RAG Dialogues"
    
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.dialogue_type})"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def duration(self):
        """Calculate the duration of the dialogue"""
        return self.updated_at - self.created_at
    
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def get_summary(self):
        """Get a summary of the dialogue"""
        exchanges = self.exchanges.all()
        return {
            'total_exchanges': exchanges.count(),
            'first_query': exchanges.first().user_query if exchanges.exists() else None,
            'last_query': exchanges.last().user_query if exchanges.exists() else None,
            'duration': self.duration,
            'total_tokens': self.total_tokens_used,
            'total_cost': float(self.total_cost),
        }

class RAGExchange(models.Model):
    """
    Represents a single exchange (question-answer pair) within a dialogue.
    Contains detailed information about the RAG processing.
    """
    dialogue = models.ForeignKey(RAGDialogue, on_delete=models.CASCADE, related_name='exchanges')
    
    # User input and system response
    user_query = models.TextField(help_text="The user's question")
    system_response = models.TextField(help_text="The system's response")
    
    # Processing information
    processing_time = models.FloatField(default=0.0, help_text="Total processing time in seconds")
    tokens_used = models.PositiveIntegerField(default=0, help_text="Total tokens used")
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.00, help_text="Cost of this exchange")
    
    # RAG-specific data
    retrieved_documents = models.JSONField(default=list, help_text="List of retrieved documents")
    context_used = models.TextField(blank=True, help_text="Context provided to the LLM")
    similarity_scores = models.JSONField(default=list, help_text="Similarity scores for retrieved documents")
    
    # Processing steps timing
    retrieval_time = models.FloatField(default=0.0, help_text="Document retrieval time")
    context_prep_time = models.FloatField(default=0.0, help_text="Context preparation time")
    llm_processing_time = models.FloatField(default=0.0, help_text="LLM processing time")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    exchange_number = models.PositiveIntegerField(help_text="Order of this exchange in the dialogue")
    
    class Meta:
        ordering = ['exchange_number']
        verbose_name = "RAG Exchange"
        verbose_name_plural = "RAG Exchanges"
    
    def __str__(self):
        return f"Exchange {self.exchange_number} - {self.user_query[:50]}..."
    
    @property
    def is_efficient(self):
        """Check if the exchange was processed efficiently"""
        return self.processing_time < 5.0  # Less than 5 seconds
    
    @property
    def document_count(self):
        """Get the number of retrieved documents"""
        return len(self.retrieved_documents)
    
    @property
    def average_similarity_score(self):
        """Calculate average similarity score"""
        if self.similarity_scores:
            return sum(self.similarity_scores) / len(self.similarity_scores)
        return 0.0
    
    def get_processing_breakdown(self):
        """Get detailed processing time breakdown"""
        return {
            'retrieval': self.retrieval_time,
            'context_preparation': self.context_prep_time,
            'llm_processing': self.llm_processing_time,
            'total': self.processing_time,
        }

class RAGDocument(models.Model):
    """
    Represents documents that have been processed by the RAG system.
    Tracks document usage and performance.
    """
    DOCUMENT_TYPES = [
        ('text', 'Text Document'),
        ('pdf', 'PDF Document'),
        ('csv', 'CSV Document'),
        ('json', 'JSON Document'),
        ('other', 'Other'),
    ]
    
    # Document information
    title = models.CharField(max_length=200, help_text="Document title")
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES, default='text')
    source_path = models.CharField(max_length=500, help_text="Path to the original document")
    content_hash = models.CharField(max_length=64, unique=True, help_text="SHA-256 hash of document content")
    
    # Processing information
    chunk_count = models.PositiveIntegerField(default=0, help_text="Number of chunks created")
    embedding_model = models.CharField(max_length=100, help_text="Embedding model used")
    vector_store_id = models.CharField(max_length=100, help_text="ID in vector store")
    
    # Usage statistics
    retrieval_count = models.PositiveIntegerField(default=0, help_text="Number of times retrieved")
    average_similarity_score = models.FloatField(default=0.0, help_text="Average similarity score when retrieved")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    last_accessed = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, help_text="Additional document metadata")
    
    class Meta:
        ordering = ['-last_accessed']
        verbose_name = "RAG Document"
        verbose_name_plural = "RAG Documents"
    
    def __str__(self):
        return f"{self.title} ({self.document_type})"
    
    def update_usage_stats(self, similarity_score=None):
        """Update usage statistics"""
        self.retrieval_count += 1
        self.last_accessed = timezone.now()
        
        if similarity_score is not None:
            # Update average similarity score
            total_score = self.average_similarity_score * (self.retrieval_count - 1) + similarity_score
            self.average_similarity_score = total_score / self.retrieval_count
        
        self.save()

class RAGSystemLog(models.Model):
    """
    System-level logs for monitoring and debugging the RAG system.
    """
    LOG_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    LOG_TYPES = [
        ('system', 'System'),
        ('user_action', 'User Action'),
        ('processing', 'Processing'),
        ('error', 'Error'),
        ('performance', 'Performance'),
    ]
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='info')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES, default='system')
    
    # Log content
    message = models.TextField(help_text="Log message")
    details = models.JSONField(default=dict, help_text="Additional log details")
    
    # Context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rag_logs')
    dialogue = models.ForeignKey(RAGDialogue, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    exchange = models.ForeignKey(RAGExchange, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    
    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "RAG System Log"
        verbose_name_plural = "RAG System Logs"
    
    def __str__(self):
        return f"{self.level.upper()} - {self.message[:50]}..."
    
    @classmethod
    def log_system_event(cls, level, message, details=None, user=None, dialogue=None, exchange=None):
        """Convenience method to log system events"""
        return cls.objects.create(
            level=level,
            log_type='system',
            message=message,
            details=details or {},
            user=user,
            dialogue=dialogue,
            exchange=exchange,
        )

# Utility functions for the models
def create_rag_dialogue(user, title, dialogue_type='general', **kwargs):
    """Create a new RAG dialogue with proper initialization"""
    dialogue = RAGDialogue.objects.create(
        user=user,
        title=title,
        dialogue_type=dialogue_type,
        **kwargs
    )
    
    # Log the creation
    RAGSystemLog.log_system_event(
        level='info',
        message=f"Created new RAG dialogue: {title}",
        details={'dialogue_type': dialogue_type, 'user_id': user.id},
        user=user,
        dialogue=dialogue
    )
    
    return dialogue

def add_exchange_to_dialogue(dialogue, user_query, system_response, processing_info=None, **kwargs):
    """Add an exchange to a dialogue with proper tracking"""
    # Get the next exchange number
    next_number = dialogue.exchanges.count() + 1
    
    # Extract processing information
    processing_time = processing_info.get('total_duration', 0.0) if processing_info else 0.0
    retrieval_time = 0.0
    context_prep_time = 0.0
    llm_processing_time = 0.0
    
    if processing_info and 'steps' in processing_info:
        for step in processing_info['steps']:
            if step['step'] == 'document_retrieval':
                retrieval_time = step['duration']
            elif step['step'] == 'context_preparation':
                context_prep_time = step['duration']
            elif step['step'] == 'llm_processing':
                llm_processing_time = step['duration']
    
    # Create the exchange
    exchange = RAGExchange.objects.create(
        dialogue=dialogue,
        user_query=user_query,
        system_response=system_response,
        exchange_number=next_number,
        processing_time=processing_time,
        retrieval_time=retrieval_time,
        context_prep_time=context_prep_time,
        llm_processing_time=llm_processing_time,
        **kwargs
    )
    
    # Update dialogue statistics
    dialogue.total_exchanges += 1
    dialogue.total_tokens_used += exchange.tokens_used
    dialogue.total_cost += exchange.cost
    dialogue.update_activity()
    dialogue.save()
    
    return exchange
