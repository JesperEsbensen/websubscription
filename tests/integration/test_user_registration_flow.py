"""Integration tests for complete user registration flow."""

import pytest
from django.test import Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from unittest.mock import patch
from tests.factories.accounts import MembershipFactory

User = get_user_model()

@pytest.mark.integration
@pytest.mark.django_db
class TestUserRegistrationFlow:
    """Test complete user registration and subscription flow."""
    
    def test_complete_registration_to_subscription_flow(self):
        """Test user can register, confirm email, and subscribe."""
        client = Client()
        
        # Step 1: Register user
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        response = client.post(reverse('register'), registration_data)
        assert response.status_code == 302
        
        # Check user was created but email not confirmed
        user = User.objects.get(username='newuser')
        assert not user.profile.email_confirmed
        
        # Check confirmation email was sent
        assert len(mail.outbox) == 1
        confirmation_email = mail.outbox[0]
        assert 'newuser@test.com' in confirmation_email.to
        
        # Step 2: Attempt to login before confirmation (should fail)
        login_response = client.post(reverse('login'), {
            'username': 'newuser',
            'password': 'complexpass123'
        })
        # Should redirect back to login with error
        assert login_response.status_code == 200  # Form with errors
        
        # Step 3: Confirm email (simulate clicking confirmation link)
        user.profile.email_confirmed = True
        user.profile.save()
        
        # Step 4: Login after confirmation (should succeed)
        login_response = client.post(reverse('login'), {
            'username': 'newuser', 
            'password': 'complexpass123'
        })
        assert login_response.status_code == 302  # Redirect after successful login
        
        # Step 5: Access profile page
        profile_response = client.get(reverse('profile'))
        assert profile_response.status_code == 200
        
        # Step 6: Create membership and attempt subscription
        membership = MembershipFactory(name='Premium', stripe_price_id='price_test123')
        
        with patch('stripe.checkout.Session.create') as mock_stripe:
            mock_stripe.return_value.url = 'https://checkout.stripe.com/session_123'
            
            subscription_response = client.post(
                reverse('create_checkout_session', args=[membership.id])
            )
            assert subscription_response.status_code == 302
            mock_stripe.assert_called_once()