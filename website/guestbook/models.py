from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guestbook_comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.created_at.strftime("%Y-%m-%d %H:%M")}'
