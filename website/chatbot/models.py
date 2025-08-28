from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ChatSession(models.Model):
    SESSION_TYPES = [
        ('general', 'General Support'),
        ('esg', 'ESG Guidance'),
        ('technical', 'Technical Support'),
        ('billing', 'Billing & Subscriptions'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='general')
    title = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_session_type_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def last_message_time(self):
        """Get the time of the last message in this session"""
        last_message = self.messages.order_by('-created_at').first()
        return last_message.created_at if last_message else self.created_at
    
    @property
    def message_count(self):
        """Get the number of messages in this session"""
        return self.messages.count()

class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('bot', 'Bot Message'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.get_message_type_display()} - {self.content[:50]}..."
    
    @property
    def is_user_message(self):
        return self.message_type == 'user'
    
    @property
    def is_bot_message(self):
        return self.message_type == 'bot'
