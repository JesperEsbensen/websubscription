from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

# Create your tests here.

class AuthTests(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.user.profile.email_confirmed = True
        self.user.profile.save()

    def test_login(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password
        })
        self.assertRedirects(response, reverse('profile'))

    def test_logout(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, '/')

    def test_user_registration_and_email_confirmation(self):
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpass1234',
            'password2': 'newpass1234',
        }
        response = self.client.post(reverse('register'), registration_data)
        if response.context and 'form' in response.context:
            self.assertFalse(response.context['form'].errors, msg=response.context['form'].errors)
        self.assertTemplateUsed(response, 'accounts/registration_pending.html')
        user = User.objects.get(username='newuser')
        self.assertFalse(user.profile.email_confirmed)
        # Simulate email confirmation
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_url = reverse('confirm_email', args=[uid, token])
        response = self.client.get(confirm_url)
        user.refresh_from_db()
        self.assertTrue(user.profile.email_confirmed)
        self.assertContains(response, 'Email confirmed')

    def test_login_requires_email_confirmation(self):
        # Create a user with unconfirmed email for this specific test
        unconfirmed_user = User.objects.create_user(
            username='unconfirmeduser',
            email='unconfirmed@example.com',
            password='unconfirmedpass123'
        )
        unconfirmed_user.profile.email_confirmed = False
        unconfirmed_user.profile.save()
        
        # Try to log in before confirmation
        response = self.client.post(reverse('login'), {
            'username': 'unconfirmeduser',
            'password': 'unconfirmedpass123',
        })
        self.assertContains(response, 'Please confirm your email before logging in.')
        
        # Confirm email
        uid = urlsafe_base64_encode(force_bytes(unconfirmed_user.pk))
        token = default_token_generator.make_token(unconfirmed_user)
        confirm_url = reverse('confirm_email', args=[uid, token])
        self.client.get(confirm_url)
        
        # Try to log in after confirmation
        response = self.client.post(reverse('login'), {
            'username': 'unconfirmeduser',
            'password': 'unconfirmedpass123',
        })
        self.assertRedirects(response, reverse('profile'))
