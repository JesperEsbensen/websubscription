from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your thoughts...',
            'maxlength': 1000
        }),
        max_length=1000,
        help_text='Maximum 1000 characters'
    )
    
    class Meta:
        model = Comment
        fields = ['content']
