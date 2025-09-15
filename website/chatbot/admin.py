from django.contrib import admin
from .models import ChatSession, ChatMessage, FormQuestion, FormResponse

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


@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'field_type', 'field_label', 'required', 'order', 'is_active', 'created_at')
    list_filter = ('field_type', 'required', 'is_active', 'created_at')
    search_fields = ('title', 'field_label', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('order', 'created_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'is_active')
        }),
        ('Field Configuration', {
            'fields': ('field_type', 'field_name', 'field_label', 'placeholder', 'required', 'order')
        }),
        ('Field Options', {
            'fields': ('options', 'validation_rules'),
            'description': 'Options are used for select, radio, and checkbox fields. Validation rules are stored as JSON.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'form_title', 'response_preview', 'created_at')
    list_filter = ('form_title', 'created_at')
    search_fields = ('user__username', 'user__email', 'form_title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def response_preview(self, obj):
        import json
        try:
            data = json.dumps(obj.response_data, indent=2)
            return data[:100] + '...' if len(data) > 100 else data
        except:
            return str(obj.response_data)[:100] + '...' if len(str(obj.response_data)) > 100 else str(obj.response_data)
    response_preview.short_description = 'Response Data Preview'
