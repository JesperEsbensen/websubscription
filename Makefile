# Makefile for Web Subscription Platform
# Provides convenient commands for development and testing

.PHONY: help install test test-unit test-integration test-fast test-coverage clean lint format run migrate

# Default target
help:
	@echo "📚 Web Subscription Platform - Available Commands:"
	@echo ""
	@echo "  🛠️  Development:"
	@echo "    install           Install all dependencies"
	@echo "    install-test      Install test dependencies"
	@echo "    run               Start development server"
	@echo "    migrate          Run database migrations"
	@echo "    makemigrations   Create new migrations"
	@echo "    shell            Start Django shell"
	@echo ""
	@echo "  🧪 Testing:"
	@echo "    test             Run all tests"
	@echo "    test-unit        Run only unit tests"
	@echo "    test-integration Run only integration tests"
	@echo "    test-fast        Run tests quickly (skip slow tests)"
	@echo "    test-coverage    Run tests with coverage report"
	@echo "    test-parallel    Run tests in parallel"
	@echo ""
	@echo "  🧙 Code Quality:"
	@echo "    lint             Run linting checks"
	@echo "    format           Format code with black"
	@echo "    clean            Clean up temporary files"
	@echo ""
	@echo "  🚀 Production:"
	@echo "    collectstatic    Collect static files"
	@echo "    check            Run Django system checks"
	@echo ""

# Installation
install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

install-test: install
	@echo "📦 Installing test dependencies..."
	pip install -r tests/requirements-test.txt

# Development
run:
	@echo "🚀 Starting development server..."
	cd website && python manage.py runserver

migrate:
	@echo "📋 Running database migrations..."
	cd website && python manage.py migrate

makemigrations:
	@echo "📋 Creating new migrations..."
	cd website && python manage.py makemigrations

shell:
	@echo "🐍 Starting Django shell..."
	cd website && python manage.py shell

collectstatic:
	@echo "📎 Collecting static files..."
	cd website && python manage.py collectstatic --noinput

check:
	@echo "✅ Running Django system checks..."
	cd website && python manage.py check

# Testing
test: install-test
	@echo "🧪 Running all tests..."
	./run_tests.sh

test-unit: install-test
	@echo "🧪 Running unit tests..."
	./run_tests.sh --unit

test-integration: install-test
	@echo "🧪 Running integration tests..."
	./run_tests.sh --integration

test-fast: install-test
	@echo "⚡ Running tests (fast mode)..."
	./run_tests.sh --fast

test-coverage: install-test
	@echo "📊 Running tests with coverage..."
	./run_tests.sh --coverage
	@echo "📊 Coverage report available at htmlcov/index.html"

test-parallel: install-test
	@echo "🚀 Running tests in parallel..."
	./run_tests.sh --parallel

# Code Quality
lint:
	@echo "🔍 Running linting checks..."
	@command -v flake8 >/dev/null 2>&1 || { echo "Installing flake8..."; pip install flake8; }
	flake8 website/ --max-line-length=88 --extend-ignore=E203,W503

format:
	@echo "🎨 Formatting code with black..."
	@command -v black >/dev/null 2>&1 || { echo "Installing black..."; pip install black; }
	black website/ tests/

# Cleanup
clean:
	@echo "🧹 Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	@echo "✨ Cleanup complete!"

# Docker commands (if using Docker)
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t websubscription .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 websubscription

# Help for specific test commands
test-help:
	@echo "🧪 Test Command Examples:"
	@echo ""
	@echo "  Basic Testing:"
	@echo "    make test                    # Run all tests"
	@echo "    make test-unit              # Run only unit tests"
	@echo "    make test-integration       # Run only integration tests"
	@echo ""
	@echo "  Advanced Testing:"
	@echo "    make test-fast              # Skip slow tests"
	@echo "    make test-coverage          # Generate coverage report"
	@echo "    make test-parallel          # Run tests in parallel"
	@echo ""
	@echo "  Direct pytest commands:"
	@echo "    pytest tests/unit/test_accounts/test_models.py::TestUserModel::test_user_creation"
	@echo "    pytest -m integration      # Run integration tests only" 
	@echo "    pytest -v --tb=short       # Verbose with short tracebacks"
	@echo ""

info:
	@echo "📊 Project Information:"
	@echo "    Python version: $$(python --version 2>&1)"
	@echo "    Django version: $$(cd website && python -c 'import django; print(django.get_version())' 2>/dev/null || echo 'Not installed')"
	@echo "    Pytest version: $$(pytest --version 2>/dev/null | head -n1 || echo 'Not installed')"
	@echo "    Working directory: $$(pwd)"
	@echo "    Virtual env: $$(echo $$VIRTUAL_ENV || echo 'None active')"
	@echo ""
	@echo "  Test Structure:"
	@echo "    Unit tests: $$(find tests/unit -name '*.py' | wc -l) files" 2>/dev/null || echo "    Unit tests: Not found"
	@echo "    Integration tests: $$(find tests/integration -name '*.py' | wc -l) files" 2>/dev/null || echo "    Integration tests: Not found"
	@echo "    Factories: $$(find tests/factories -name '*.py' | wc -l) files" 2>/dev/null || echo "    Factories: Not found"