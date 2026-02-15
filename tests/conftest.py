"""
pytest configuration and shared fixtures.
"""

import os
import sys
import tempfile
from pathlib import Path

# Configure Django before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')

# Add paths to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
WEBSITE_DIR = BASE_DIR / 'website'
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(WEBSITE_DIR))

# Setup Django
import django
django.setup()

import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from tests.factories.accounts import UserFactory, ProfileFactory

User = get_user_model()

@pytest.fixture
def api_client():
    """Returns a Django test client."""
    return Client()

@pytest.fixture
def authenticated_client(db):
    """Returns a Django test client with an authenticated user."""
    user = UserFactory()
    client = Client()
    client.force_login(user)
    return client, user

@pytest.fixture
def confirmed_user(db):
    """Returns a user with confirmed email."""
    user = UserFactory()
    user.profile.email_confirmed = True
    user.profile.save()
    return user

@pytest.fixture
def temp_media_root():
    """Provides a temporary directory for media files during testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup happens automatically when temp_dir goes out of scope

@pytest.fixture
def mock_stripe_customer():
    """Mock Stripe customer data."""
    return {
        'id': 'cus_test123',
        'email': 'test@example.com',
        'created': 1234567890,
        'default_source': None
    }

@pytest.fixture
def mock_stripe_subscription():
    """Mock Stripe subscription data."""
    return {
        'id': 'sub_test123',
        'customer': 'cus_test123',
        'status': 'active',
        'current_period_start': 1234567890,
        'current_period_end': 1234567890 + 2592000  # +30 days
    }