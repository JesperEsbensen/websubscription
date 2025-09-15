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


class FormQuestion(models.Model):
    """Model for storing form questions that can be presented to users"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('email', 'Email'),
        ('number', 'Number'),
        ('select', 'Select Dropdown'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox'),
        ('date', 'Date'),
        ('datetime', 'Date and Time'),
        ('file', 'File Upload'),
    ]
    
    title = models.CharField(max_length=200, help_text="Question title or form name")
    description = models.TextField(blank=True, help_text="Optional description or instructions")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    field_name = models.CharField(max_length=100, help_text="Internal field name for JSON storage")
    field_label = models.CharField(max_length=200, help_text="Display label for the field")
    placeholder = models.CharField(max_length=200, blank=True, help_text="Placeholder text")
    required = models.BooleanField(default=True)
    options = models.JSONField(default=list, blank=True, help_text="Options for select/radio/checkbox fields")
    validation_rules = models.JSONField(default=dict, blank=True, help_text="Custom validation rules")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.title} ({self.field_type})"


class FormResponse(models.Model):
    """Model for storing form responses and managing JSON file storage"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='form_responses')
    form_title = models.CharField(max_length=200)
    response_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.form_title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    
    @classmethod
    def get_user_responses(cls, user, form_title=None):
        """Get all responses for a user, optionally filtered by form title"""
        queryset = cls.objects.filter(user=user)
        if form_title:
            queryset = queryset.filter(form_title=form_title)
        return queryset
    
