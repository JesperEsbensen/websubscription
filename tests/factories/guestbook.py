"""Factory classes for guestbook app models."""

import factory
from guestbook.models import Comment
from .accounts import UserFactory

class CommentFactory(factory.django.DjangoModelFactory):
    """Factory for Comment model."""
    class Meta:
        model = Comment
    
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('text', max_nb_chars=800)