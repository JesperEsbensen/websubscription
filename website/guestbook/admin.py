from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'content', 'created_at', 'updated_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
