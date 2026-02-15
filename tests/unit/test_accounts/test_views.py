"""Unit tests for accounts app views."""

import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock
from tests.factories.accounts import UserFactory, ProfileFactory

User = get_user_model()

@pytest.mark.django_db
class TestAccountViews:
    """Test accounts app views."""
    
    def test_home_view_anonymous(self):
        """Test home view for anonymous users."""
        client = Client()
        response = client.get(reverse('home'))
        assert response.status_code == 200
    
    def test_home_view_authenticated(self):
        """Test home view for authenticated users."""
        user = UserFactory()
        client = Client()
        client.force_login(user)
        response = client.get(reverse('home'))
        assert response.status_code == 200
    
    def test_register_view_get(self):
        """Test registration form display."""
        client = Client()
        response = client.get(reverse('register'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_register_view_post_valid(self):
        """Test user registration with valid data."""
        client = Client()
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        with patch('accounts.views.send_confirmation_email') as mock_send:
            response = client.post(reverse('register'), data)
            assert response.status_code == 302  # Redirect after successful registration
            mock_send.assert_called_once()
    
    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication."""
        client = Client()
        response = client.get(reverse('profile'))
        assert response.status_code == 302  # Redirect to login
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user."""
        user = UserFactory()
        user.profile.email_confirmed = True
        user.profile.save()
        
        client = Client()
        client.force_login(user)
        response = client.get(reverse('profile'))
        assert response.status_code == 200
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_stripe):
        """Test Stripe checkout session creation."""
        mock_stripe.return_value = Mock(url='https://checkout.stripe.com/session_123')
        
        user = UserFactory()
        user.profile.email_confirmed = True
        user.profile.save()
        
        client = Client()
        client.force_login(user)
        
        response = client.post(reverse('create_checkout_session', args=[1]))
        assert response.status_code == 302
        mock_stripe.assert_called_once()