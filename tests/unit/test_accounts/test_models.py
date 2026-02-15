"""Unit tests for accounts app models."""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from tests.factories.accounts import UserFactory, ProfileFactory, MembershipFactory
from accounts.models import Profile, Membership

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self):
        """Test user can be created with factory."""
        user = UserFactory()
        assert user.pk is not None
        assert user.username
        assert user.email
        assert user.check_password('testpass123')
    
    def test_user_profile_created_automatically(self):
        """Test that profile is created when user is created."""
        user = UserFactory()
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, Profile)
    
    def test_user_str_representation(self):
        """Test user string representation."""
        user = UserFactory(username='testuser')
        assert str(user) == 'testuser'

@pytest.mark.django_db
class TestProfileModel:
    """Test Profile model functionality."""
    
    def test_profile_creation(self):
        """Test profile creation with factory."""
        profile = ProfileFactory()
        assert profile.pk is not None
        assert profile.user is not None
        assert not profile.email_confirmed  # Default value
    
    def test_profile_str_representation(self):
        """Test profile string representation."""
        user = UserFactory(username='testuser')
        profile = user.profile
        assert str(profile) == 'testuser Profile'
    
    def test_profile_with_confirmed_email(self):
        """Test profile with confirmed email."""
        profile = ProfileFactory(email_confirmed=True)
        assert profile.email_confirmed
    
    def test_profile_stripe_fields(self):
        """Test stripe-related fields."""
        profile = ProfileFactory(
            stripe_customer_id='cus_123',
            stripe_subscription_id='sub_123',
            subscription_status='active'
        )
        assert profile.stripe_customer_id == 'cus_123'
        assert profile.stripe_subscription_id == 'sub_123'
        assert profile.subscription_status == 'active'

@pytest.mark.django_db
class TestMembershipModel:
    """Test Membership model functionality."""
    
    def test_membership_creation(self):
        """Test membership creation."""
        membership = MembershipFactory(name='Premium')
        assert membership.name == 'Premium'
        assert membership.stripe_price_id
    
    def test_membership_str_representation(self):
        """Test membership string representation."""
        membership = MembershipFactory(name='Basic Plan')
        assert str(membership) == 'Basic Plan'