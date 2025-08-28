from django.contrib import admin
from .models import ChatSession, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('message_type', 'content', 'created_at')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_type', 'title', 'created_at', 'updated_at', 'message_count', 'is_active')
    list_filter = ('session_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChatMessageInline]
    ordering = ('-updated_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'message_type', 'content_preview', 'created_at')
    list_filter = ('message_type', 'created_at', 'session__session_type')
    search_fields = ('content', 'session__user__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
