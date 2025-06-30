from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from unittest.mock import patch, MagicMock
from .models import Profile, Membership

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
        self.assertContains(response, 'successfully confirmed')

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

    def test_unauthenticated_users_cannot_access_protected_pages(self):
        """Test that unauthenticated users are redirected when accessing protected pages"""
        # Ensure we're logged out
        self.client.logout()
        
        # Test logged_in_page (should redirect to login)
        response = self.client.get(reverse('logged_in_page'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test subscribing_page (should redirect to login)
        response = self.client.get(reverse('subscribing_page'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test profile page (should redirect to login)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test subscription_details page (should redirect to login)
        response = self.client.get(reverse('subscription_details'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test cancel_subscription (should redirect to login)
        response = self.client.post(reverse('cancel_subscription'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test reactivate_subscription (should redirect to login)
        response = self.client.post(reverse('reactivate_subscription'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test cancel_subscription_immediately (should redirect to login)
        response = self.client.post(reverse('cancel_subscription_immediately'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_logged_in_user_can_access_logged_in_page_but_not_subscription_page(self):
        """Test that a logged-in user can access the logged-in page but not the subscription page without an active subscription."""
        # Ensure the user is logged in
        self.client.login(username=self.username, password=self.password)

        # The user should be able to access the logged-in page
        response = self.client.get(reverse('logged_in_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subscription')  # Or some text unique to the page

        # The user should NOT be able to access the subscription page (should redirect to subscribe)
        response = self.client.get(reverse('subscribing_page'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/subscribe/', response.url)

    def test_subscribing_user_can_access_both_logged_in_and_subscription_pages(self):
        """Test that a user with an active subscription can access both the logged-in page and the subscription page."""
        # Set up the user as subscribed
        self.user.profile.stripe_subscription_id = 'sub_test123'
        self.user.profile.subscription_status = 'active'
        self.user.profile.save()
        self.client.login(username=self.username, password=self.password)

        # The user should be able to access the logged-in page
        response = self.client.get(reverse('logged_in_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subscription')  # Or some text unique to the page

        # The user should be able to access the subscription page
        response = self.client.get(reverse('subscribing_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subscription')  # Or some text unique to the page


class SubscriptionCancellationTests(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.user.profile.email_confirmed = True
        self.user.profile.stripe_customer_id = 'cus_test123'
        self.user.profile.stripe_subscription_id = 'sub_test123'
        self.user.profile.subscription_status = 'active'
        self.user.profile.save()
        self.client.login(username=self.username, password=self.password)

    @patch('accounts.views.stripe')
    def test_cancel_subscription_at_period_end(self, mock_stripe):
        # Mock the Stripe subscription modification
        mock_subscription = MagicMock()
        mock_stripe.Subscription.modify.return_value = mock_subscription
        
        response = self.client.post(reverse('cancel_subscription'))
        
        # Check that Stripe was called correctly
        mock_stripe.Subscription.modify.assert_called_once_with(
            'sub_test123',
            cancel_at_period_end=True
        )
        
        # Check that the user was redirected
        self.assertRedirects(response, reverse('profile'))
        
        # Check that the subscription status was updated
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.subscription_status, 'canceled')

    @patch('accounts.views.stripe')
    def test_cancel_subscription_immediately(self, mock_stripe):
        # Mock the Stripe subscription deletion
        mock_subscription = MagicMock()
        mock_stripe.Subscription.delete.return_value = mock_subscription
        
        response = self.client.post(reverse('cancel_subscription_immediately'))
        
        # Check that Stripe was called correctly
        mock_stripe.Subscription.delete.assert_called_once_with('sub_test123')
        
        # Check that the user was redirected
        self.assertRedirects(response, reverse('profile'))
        
        # Check that the subscription status was updated
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.subscription_status, 'canceled')

    @patch('accounts.views.stripe')
    def test_reactivate_subscription(self, mock_stripe):
        # Set subscription as canceled
        self.user.profile.subscription_status = 'canceled'
        self.user.profile.save()
        
        # Mock the Stripe subscription modification
        mock_subscription = MagicMock()
        mock_stripe.Subscription.modify.return_value = mock_subscription
        
        response = self.client.post(reverse('reactivate_subscription'))
        
        # Check that Stripe was called correctly
        mock_stripe.Subscription.modify.assert_called_once_with(
            'sub_test123',
            cancel_at_period_end=False
        )
        
        # Check that the user was redirected
        self.assertRedirects(response, reverse('profile'))
        
        # Check that the subscription status was updated
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.subscription_status, 'active')

    def test_cancel_subscription_no_subscription(self):
        # Remove subscription ID
        self.user.profile.stripe_subscription_id = None
        self.user.profile.save()
        
        response = self.client.post(reverse('cancel_subscription'))
        
        # Should redirect to profile with error message
        self.assertRedirects(response, reverse('profile'))

    @patch('accounts.views.stripe')
    def test_subscription_details_view(self, mock_stripe):
        # Mock Stripe responses with proper nested objects and real values
        class Recurring:
            interval = 'month'
        class Price:
            recurring = Recurring()
            unit_amount = 2000  # Real numeric value
        class Item:
            price = Price()
        mock_item = Item()
        mock_subscription = MagicMock()
        mock_subscription.status = 'active'
        mock_subscription.created = 1640995200  # Unix timestamp
        mock_subscription.current_period_start = 1640995200
        mock_subscription.current_period_end = 1643673600
        mock_subscription.cancel_at_period_end = False
        mock_subscription.items.data = [mock_item]
        mock_subscription.id = 'sub_test123'
        
        mock_customer = MagicMock()
        mock_customer.name = 'Test User'
        mock_customer.email = 'test@example.com'
        mock_customer.id = 'cus_test123'
        
        # Mock Stripe API calls
        mock_stripe.Subscription.retrieve.return_value = mock_subscription
        mock_stripe.Customer.retrieve.return_value = mock_customer
        
        # Mock the upcoming invoice to return None to avoid template issues
        mock_stripe.Invoice.upcoming.side_effect = Exception("No upcoming invoice")
        
        # Mock stripe.error.StripeError for exception handling
        class MockStripeError(Exception):
            pass
        mock_stripe.error.StripeError = MockStripeError
        
        response = self.client.get(reverse('subscription_details'))
        
        # Check that the view returns 200
        self.assertEqual(response.status_code, 200)
        
        # Check that the template is used
        self.assertTemplateUsed(response, 'accounts/subscription_details.html')
        
        # Check that Stripe was called
        mock_stripe.Subscription.retrieve.assert_called_once_with('sub_test123')

class UserDeletionTests(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.email = 'test@example.com'
        self.password = 'testpass123'
        self.user = User.objects.create_user(username=self.username, email=self.email, password=self.password)
        self.user.profile.email_confirmed = True
        self.user.profile.stripe_customer_id = 'cus_test123'
        self.user.profile.stripe_subscription_id = 'sub_test123'
        self.user.profile.subscription_status = 'active'
        self.user.profile.save()
        self.client.login(username=self.username, password=self.password)

    @patch('accounts.views.stripe')
    def test_delete_user_with_correct_email(self, mock_stripe):
        """Test that user can be deleted with correct email confirmation"""
        # Mock Stripe API calls to prevent real API calls
        mock_subscription = MagicMock()
        mock_subscription.status = 'active'
        mock_subscription['items'] = {'data': [{'price': {'product': 'prod_test'}}]}
        mock_stripe.Subscription.retrieve.return_value = mock_subscription
        
        response = self.client.post(reverse('delete_user'), {'email': self.email})
        
        # Should redirect to home
        self.assertRedirects(response, reverse('home'))
        
        # User should be deleted from database
        self.assertFalse(User.objects.filter(username=self.username).exists())
        self.assertFalse(Profile.objects.filter(user__username=self.username).exists())

    @patch('accounts.views.stripe')
    def test_delete_user_with_incorrect_email(self, mock_stripe):
        """Test that user is not deleted with incorrect email"""
        # Mock Stripe API calls to prevent real API calls
        mock_subscription = MagicMock()
        mock_subscription.status = 'active'
        mock_subscription['items'] = {'data': [{'price': {'product': 'prod_test'}}]}
        mock_stripe.Subscription.retrieve.return_value = mock_subscription
        
        response = self.client.post(reverse('delete_user'), {'email': 'wrong@email.com'})
        
        # Should redirect to subscription_details
        self.assertRedirects(response, reverse('subscription_details'))
        
        # User should still exist in database
        self.assertTrue(User.objects.filter(username=self.username).exists())
        self.assertTrue(Profile.objects.filter(user__username=self.username).exists())

    @patch('accounts.views.stripe')
    def test_delete_user_with_empty_email(self, mock_stripe):
        """Test that user is not deleted with empty email"""
        # Mock Stripe API calls to prevent real API calls
        mock_subscription = MagicMock()
        mock_subscription.status = 'active'
        mock_subscription['items'] = {'data': [{'price': {'product': 'prod_test'}}]}
        mock_stripe.Subscription.retrieve.return_value = mock_subscription
        
        response = self.client.post(reverse('delete_user'), {'email': ''})
        
        # Should redirect to subscription_details
        self.assertRedirects(response, reverse('subscription_details'))
        
        # User should still exist in database
        self.assertTrue(User.objects.filter(username=self.username).exists())
        self.assertTrue(Profile.objects.filter(user__username=self.username).exists())

    @patch('accounts.views.stripe')
    def test_delete_user_without_email(self, mock_stripe):
        """Test that user is not deleted without email parameter"""
        # Mock Stripe API calls to prevent real API calls
        mock_subscription = MagicMock()
        mock_subscription.status = 'active'
        mock_subscription['items'] = {'data': [{'price': {'product': 'prod_test'}}]}
        mock_stripe.Subscription.retrieve.return_value = mock_subscription
        
        response = self.client.post(reverse('delete_user'), {})
        
        # Should redirect to subscription_details
        self.assertRedirects(response, reverse('subscription_details'))
        
        # User should still exist in database
        self.assertTrue(User.objects.filter(username=self.username).exists())
        self.assertTrue(Profile.objects.filter(user__username=self.username).exists())

    @patch('accounts.views.stripe')
    def test_delete_user_case_insensitive_email(self, mock_stripe):
        """Test that email comparison is case insensitive"""
        # Mock Stripe API calls to prevent real API calls
        mock_subscription = MagicMock()
        mock_subscription.status = 'active'
        mock_subscription['items'] = {'data': [{'price': {'product': 'prod_test'}}]}
        mock_stripe.Subscription.retrieve.return_value = mock_subscription
        
        response = self.client.post(reverse('delete_user'), {'email': self.email.upper()})
        
        # Should redirect to home (successful deletion)
        self.assertRedirects(response, reverse('home'))
        
        # User should be deleted from database
        self.assertFalse(User.objects.filter(username=self.username).exists())
        self.assertFalse(Profile.objects.filter(user__username=self.username).exists())

    def test_delete_user_requires_login(self):
        """Test that delete_user requires authentication"""
        self.client.logout()
        response = self.client.post(reverse('delete_user'), {'email': self.email})
        
        # Should redirect to login
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('delete_user')}")
        
        # User should still exist in database
        self.assertTrue(User.objects.filter(username=self.username).exists())

    def test_delete_user_requires_post(self):
        """Test that delete_user only accepts POST requests"""
        response = self.client.get(reverse('delete_user'))
        
        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
        
        # User should still exist in database
        self.assertTrue(User.objects.filter(username=self.username).exists())
