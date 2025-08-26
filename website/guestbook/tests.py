from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Comment
from .forms import CommentForm

class GuestBookTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.comment_data = {
            'content': 'This is a test comment for the guest book.'
        }

    def test_guestbook_list_view(self):
        """Test that the guest book list view loads correctly"""
        response = self.client.get(reverse('guestbook:guestbook_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'guestbook/guestbook_list.html')

    def test_add_comment_authenticated(self):
        """Test adding a comment when user is authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('guestbook:guestbook_list'), self.comment_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful post
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, self.comment_data['content'])

    def test_add_comment_unauthenticated(self):
        """Test that unauthenticated users cannot add comments"""
        response = self.client.post(reverse('guestbook:guestbook_list'), self.comment_data)
        self.assertEqual(response.status_code, 200)  # Form is displayed but not processed
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_form_valid(self):
        """Test that the comment form validates correctly"""
        form = CommentForm(data=self.comment_data)
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid(self):
        """Test that the comment form rejects empty content"""
        form = CommentForm(data={'content': ''})
        self.assertFalse(form.is_valid())

    def test_comment_model_str(self):
        """Test the string representation of the Comment model"""
        comment = Comment.objects.create(
            author=self.user,
            content='Test comment'
        )
        self.assertIn(self.user.username, str(comment))
        # The string representation includes the username and timestamp, not the content
        self.assertIn('Comment by', str(comment))
