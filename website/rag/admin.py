from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import RAGDialogue, RAGExchange, RAGDocument, RAGSystemLog

class RAGExchangeInline(admin.TabularInline):
    """Inline admin for RAG exchanges within dialogues"""
    model = RAGExchange
    extra = 0
    readonly_fields = ('created_at', 'exchange_number', 'processing_time', 'tokens_used', 'cost')
    fields = ('exchange_number', 'user_query', 'system_response', 'processing_time', 'tokens_used', 'cost', 'created_at')
    ordering = ('exchange_number',)
    
    def has_add_permission(self, request, obj=None):
        return False  # Exchanges should be created through the RAG system

class RAGSystemLogInline(admin.TabularInline):
    """Inline admin for system logs"""
    model = RAGSystemLog
    extra = 0
    readonly_fields = ('timestamp', 'level', 'log_type', 'message')
    fields = ('timestamp', 'level', 'log_type', 'message')
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request, obj=None):
        return False  # Logs should be created automatically

@admin.register(RAGDialogue)
class RAGDialogueAdmin(admin.ModelAdmin):
    """Admin interface for RAG dialogues"""
    list_display = (
        'title', 'user', 'dialogue_type', 'status', 'total_exchanges', 
        'total_tokens_used', 'total_cost', 'last_activity', 'created_at'
    )
    list_filter = ('dialogue_type', 'status', 'llm_provider', 'vector_store_type', 'created_at')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'last_activity', 'total_exchanges', 'total_tokens_used', 'total_cost')
    inlines = [RAGExchangeInline, RAGSystemLogInline]
    ordering = ('-last_activity',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'dialogue_type', 'status')
        }),
        ('RAG Configuration', {
            'fields': ('llm_provider', 'llm_model', 'vector_store_type')
        }),
        ('Statistics', {
            'fields': ('total_exchanges', 'total_tokens_used', 'total_cost')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('user')
    
    def dialogue_summary(self, obj):
        """Display a summary of the dialogue"""
        summary = obj.get_summary()
        return format_html(
            '<div style="font-size: 12px;">'
            '<strong>Duration:</strong> {}<br>'
            '<strong>First Query:</strong> {}<br>'
            '<strong>Last Query:</strong> {}'
            '</div>',
            summary['duration'],
            summary['first_query'][:50] + '...' if summary['first_query'] else 'N/A',
            summary['last_query'][:50] + '...' if summary['last_query'] else 'N/A'
        )
    dialogue_summary.short_description = 'Summary'

@admin.register(RAGExchange)
class RAGExchangeAdmin(admin.ModelAdmin):
    """Admin interface for RAG exchanges"""
    list_display = (
        'dialogue', 'exchange_number', 'user_query_preview', 'processing_time', 
        'tokens_used', 'cost', 'document_count', 'average_similarity_score', 'created_at'
    )
    list_filter = ('dialogue__dialogue_type', 'created_at', 'dialogue__llm_provider')
    search_fields = ('user_query', 'system_response', 'dialogue__title', 'dialogue__user__username')
    readonly_fields = ('created_at', 'exchange_number', 'processing_time', 'tokens_used', 'cost')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Exchange Information', {
            'fields': ('dialogue', 'exchange_number', 'user_query', 'system_response')
        }),
        ('Processing Details', {
            'fields': ('processing_time', 'retrieval_time', 'context_prep_time', 'llm_processing_time')
        }),
        ('Usage Statistics', {
            'fields': ('tokens_used', 'cost', 'document_count', 'average_similarity_score')
        }),
        ('RAG Data', {
            'fields': ('retrieved_documents', 'context_used', 'similarity_scores'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_query_preview(self, obj):
        """Display a preview of the user query"""
        return obj.user_query[:50] + '...' if len(obj.user_query) > 50 else obj.user_query
    user_query_preview.short_description = 'User Query'
    
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('dialogue', 'dialogue__user')
    
    def has_add_permission(self, request):
        return False  # Exchanges should be created through the RAG system

@admin.register(RAGDocument)
class RAGDocumentAdmin(admin.ModelAdmin):
    """Admin interface for RAG documents"""
    list_display = (
        'title', 'document_type', 'chunk_count', 'retrieval_count', 
        'average_similarity_score', 'last_accessed', 'created_at'
    )
    list_filter = ('document_type', 'embedding_model', 'created_at', 'last_accessed')
    search_fields = ('title', 'source_path', 'content_hash')
    readonly_fields = ('created_at', 'last_accessed', 'retrieval_count', 'average_similarity_score')
    ordering = ('-last_accessed',)
    
    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'document_type', 'source_path', 'content_hash')
        }),
        ('Processing Information', {
            'fields': ('chunk_count', 'embedding_model', 'vector_store_id')
        }),
        ('Usage Statistics', {
            'fields': ('retrieval_count', 'average_similarity_score', 'last_accessed')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_performance(self, obj):
        """Display document performance metrics"""
        if obj.retrieval_count > 0:
            return format_html(
                '<div style="font-size: 12px;">'
                '<strong>Retrieval Rate:</strong> {:.2f}%<br>'
                '<strong>Avg Score:</strong> {:.3f}'
                '</div>',
                (obj.retrieval_count / max(1, obj.chunk_count)) * 100,
                obj.average_similarity_score
            )
        return 'No retrievals'
    document_performance.short_description = 'Performance'

@admin.register(RAGSystemLog)
class RAGSystemLogAdmin(admin.ModelAdmin):
    """Admin interface for RAG system logs"""
    list_display = ('timestamp', 'level', 'log_type', 'message_preview', 'user', 'dialogue_link')
    list_filter = ('level', 'log_type', 'timestamp')
    search_fields = ('message', 'user__username', 'dialogue__title')
    readonly_fields = ('timestamp', 'level', 'log_type', 'message', 'details', 'user', 'dialogue', 'exchange')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Log Information', {
            'fields': ('timestamp', 'level', 'log_type', 'message')
        }),
        ('Context', {
            'fields': ('user', 'dialogue', 'exchange')
        }),
        ('Details', {
            'fields': ('details', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        """Display a preview of the log message"""
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'
    
    def dialogue_link(self, obj):
        """Create a link to the dialogue if available"""
        if obj.dialogue:
            url = reverse('admin:rag_ragdialogue_change', args=[obj.dialogue.id])
            return format_html('<a href="{}">{}</a>', url, obj.dialogue.title)
        return '-'
    dialogue_link.short_description = 'Dialogue'
    
    def has_add_permission(self, request):
        return False  # Logs should be created automatically
    
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('user', 'dialogue')

# Custom admin actions
@admin.action(description="Archive selected dialogues")
def archive_dialogues(modeladmin, request, queryset):
    """Archive selected dialogues"""
    updated = queryset.update(status='archived')
    modeladmin.message_user(request, f'{updated} dialogues have been archived.')

@admin.action(description="Delete selected dialogues")
def delete_dialogues(modeladmin, request, queryset):
    """Delete selected dialogues"""
    updated = queryset.update(status='deleted')
    modeladmin.message_user(request, f'{updated} dialogues have been marked as deleted.')

# Add actions to RAGDialogueAdmin
RAGDialogueAdmin.actions = [archive_dialogues, delete_dialogues]
