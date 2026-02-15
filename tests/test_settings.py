"""
Django settings for testing environment.
Inherits from main settings but optimized for testing.
"""

from website.settings import *
import tempfile
import os

# Test database - use in-memory SQLite for speed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster testing
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Password hashers - use fast hasher for testing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend - use memory backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Media files - use temporary directory
MEDIA_ROOT = tempfile.mkdtemp()

# Static files - disable for testing
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Logging - reduce verbosity during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Stripe - use test keys
STRIPE_PUBLISHABLE_KEY = 'pk_test_fake_key'
STRIPE_SECRET_KEY = 'sk_test_fake_key'
STRIPE_WEBHOOK_SECRET = 'whsec_fake_secret'

# OpenAI - use test configuration
OPENAI_API_KEY = 'test-key'
OPENAI_MODEL = 'gpt-3.5-turbo'

# ChromaDB - use temporary directory
CHROMA_DB_PATH = tempfile.mkdtemp()

# Cache - use dummy cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Security - disable for testing
SECRET_KEY = 'test-secret-key-not-for-production'
DEBUG = True
ALLOWED_HOSTS = ['*']