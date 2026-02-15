# Testing Setup for Web Subscription Platform

This directory contains a comprehensive test suite for the Django web subscription platform.

## 📁 Directory Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Pytest configuration and shared fixtures
├── pytest.ini                 # Pytest settings
├── test_settings.py           # Django test-specific settings
├── requirements-test.txt      # Test-only dependencies
├── README.md                  # This file
│
├── factories/                 # Factory classes for creating test objects
│   ├── __init__.py
│   ├── accounts.py           # User, Profile, Membership factories
│   ├── chatbot.py            # ChatSession, ChatMessage factories
│   ├── guestbook.py          # Comment factory
│   └── rag.py                # RAG-related factories
│
├── fixtures/                  # JSON fixtures for loading test data
│   ├── __init__.py
│   ├── sample_users.json     # Sample users for testing
│   └── sample_memberships.json # Sample membership plans
│
├── unit/                      # Unit tests (isolated component testing)
│   ├── __init__.py
│   ├── test_accounts/        # Accounts app unit tests
│   │   ├── __init__.py
│   │   ├── test_models.py    # Model unit tests
│   │   └── test_views.py     # View unit tests
│   ├── test_chatbot/         # Chatbot app unit tests
│   ├── test_guestbook/       # Guestbook app unit tests
│   └── test_rag/             # RAG system unit tests
│
├── integration/              # Integration tests (multi-component testing)
│   ├── __init__.py
│   ├── test_user_registration_flow.py
│   └── test_chatbot_rag_flow.py
│
└── utils/                    # Test utilities and helpers
    ├── __init__.py
    └── test_helpers.py       # Helper classes and functions
```

## 🚀 Running Tests

### Prerequisites

1. Install test dependencies:
   ```bash
   pip install -r tests/requirements-test.txt
   ```

2. Make sure you're in the project root directory:
   ```bash
   cd /home/jesper/projects/websubscription
   ```

### Running All Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=website --cov-report=html

# Run tests in parallel (faster)
pytest -n auto
```

### Running Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests for specific app
pytest tests/unit/test_accounts/

# Run specific test file
pytest tests/unit/test_accounts/test_models.py

# Run specific test method
pytest tests/unit/test_accounts/test_models.py::TestUserModel::test_user_creation
```

### Running Tests with Markers

```bash
# Run only integration tests
pytest -m integration

# Run only unit tests
pytest -m unit

# Exclude slow tests
pytest -m "not slow"

# Run tests that don't require external APIs
pytest -m "not external_api"
```

### Debugging Tests

```bash
# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Show local variables in tracebacks
pytest -l

# Enter debugger on failures
pytest --pdb
```

## 🏗️ Test Configuration

### Test Settings ([test_settings.py](test_settings.py))

- Uses in-memory SQLite database for speed
- Disables migrations (uses schema from models)
- Fast password hasher for testing
- Memory-based email backend
- Temporary directories for media files
- Mock Stripe and OpenAI API keys

### Pytest Configuration ([pytest.ini](pytest.ini))

- Configured for Django testing
- Reuses database between tests (faster)
- Skips migrations
- Custom test markers defined
- Verbose output by default

## 🏭 Factories ([factories/](factories/))

Factory classes use `factory-boy` to create test objects with realistic data:

```python
# Create a user with confirmed email
user = UserFactory()
user.profile.email_confirmed = True
user.profile.save()

# Create a chat session with messages
session = ChatSessionFactory()
ChatMessageFactory.create_batch(5, session=session)

# Create membership plans
membership = MembershipFactory(name='Premium')
```

## 🎯 Test Organization Patterns

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (Stripe, OpenAI)
- Fast execution
- Focus on business logic

### Integration Tests
- Test complete user workflows
- Test interactions between components
- May use real database operations
- Slower but more comprehensive

### Test Naming Convention
```python
class TestModelName:
    def test_specific_behavior(self):
        """Test description of what is being tested."""
        # Arrange
        # Act  
        # Assert
```

## 📊 Coverage Reports

After running tests with coverage:

```bash
pytest --cov=website --cov-report=html
```

Open `htmlcov/index.html` to view detailed coverage report.

## 🔧 Adding New Tests

1. **Unit Tests**: Add to appropriate `tests/unit/test_<app>/` directory
2. **Integration Tests**: Add to `tests/integration/`
3. **Factories**: Add new factories to `tests/factories/`
4. **Fixtures**: Add JSON fixtures to `tests/fixtures/`
5. **Utilities**: Add helper functions to `tests/utils/`

## 🚧 Continuous Integration

For CI/CD pipelines, use:

```bash
# Fast test run for CI
pytest --tb=short --strict-markers -q

# With coverage for quality gates
pytest --cov=website --cov-fail-under=80
```

## 🔒 Test Data Security

- All test data uses fake/mock values
- No real API keys or sensitive data in tests
- Temporary directories cleaned up automatically
- Test database isolated from production data

## 📦 Excluding Tests from Deployment

To exclude the tests directory from production deployment, add to your deployment script or `.gitignore` (if desired):

```bash
# In deployment scripts, exclude tests/
rsync --exclude='tests/' --exclude='*.pyc' ...

# Or in .dockerignore
tests/
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from project root
2. **Database Errors**: Check that `DJANGO_SETTINGS_MODULE` is set correctly
3. **Factory Errors**: Verify all required fields are provided in factories
4. **Async Errors**: Use `pytest-asyncio` for async test functions

### Debug Commands

```bash
# Check test discovery
pytest --collect-only

# Show pytest configuration
pytest --help

# Validate test settings
python -c "import tests.test_settings; print('Settings loaded successfully')"
```