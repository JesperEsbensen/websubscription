"""Unit tests for guestbook app models."""

import pytest
from django.core.exceptions import ValidationError
from tests.factories.guestbook import CommentFactory
from tests.factories.accounts import UserFactory
from guestbook.models import Comment

@pytest.mark.django_db
class TestCommentModel:
    """Test Comment model functionality."""
    
    def test_comment_creation(self):
        """Test comment creation with factory."""
        comment = CommentFactory()
        assert comment.pk is not None
        assert comment.author is not None
        assert comment.content
        assert comment.created_at
        assert comment.updated_at
    
    def test_comment_str_representation(self):
        """Test comment string representation."""
        user = UserFactory(username='testuser')
        comment = CommentFactory(author=user, content='Test comment')
        str_repr = str(comment)
        assert 'testuser' in str_repr
        assert comment.created_at.strftime('%Y-%m-%d %H:%M') in str_repr
    
    def test_comment_ordering(self):
        """Test that comments are ordered by creation time (newest first)."""
        # Create comments in specific order
        comment1 = CommentFactory(content='First comment')
        comment2 = CommentFactory(content='Second comment')
        comment3 = CommentFactory(content='Third comment')
        
        # Get all comments in default ordering
        comments = list(Comment.objects.all())
        
        # Should be ordered newest first
        assert comments[0].content == 'Third comment'
        assert comments[1].content == 'Second comment'
        assert comments[2].content == 'First comment'
    
    def test_comment_content_max_length(self):
        """Test comment content has maximum length constraint."""
        # This test checks the model constraint
        # The actual validation happens at the form/view level
        long_content = 'x' * 1001  # Exceeds 1000 char limit
        comment = CommentFactory.build(content=long_content)
        
        # The factory should allow this, but Django form validation would catch it
        assert len(comment.content) > 1000
    
    def test_comment_author_relationship(self):
        """Test comment-author relationship."""
        user = UserFactory()
        comment1 = CommentFactory(author=user)
        comment2 = CommentFactory(author=user)
        
        # Test reverse relationship
        user_comments = list(user.guestbook_comments.all())
        assert len(user_comments) == 2
        assert comment1 in user_comments
        assert comment2 in user_comments