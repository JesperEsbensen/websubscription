#!/bin/bash

# Test runner script for Web Subscription Platform
# Usage: ./run_tests.sh [options]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Web Subscription Platform Test Runner${NC}"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ] && [ ! -f "website/manage.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ Error: pytest is not installed. Please run:${NC}"
    echo "pip install -r tests/requirements-test.txt"
    exit 1
fi

# Default options
FAST=false
COVERAGE=false
UNIT_ONLY=false
INTEGRATION_ONLY=false
VERBOSE=false
PARALLEL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            FAST=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --unit)
            UNIT_ONLY=true
            shift
            ;;
        --integration)
            INTEGRATION_ONLY=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --parallel|-n)
            PARALLEL=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --fast          Skip slow tests and use faster settings"
            echo "  --coverage      Generate coverage report"
            echo "  --unit          Run only unit tests"
            echo "  --integration   Run only integration tests"
            echo "  --verbose, -v   Verbose output"
            echo "  --parallel, -n  Run tests in parallel"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Run all tests"
            echo "  $0 --fast --coverage # Fast run with coverage"
            echo "  $0 --unit --verbose  # Unit tests with verbose output"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

# Add test directory selection
if [ "$UNIT_ONLY" = true ]; then
    PYTEST_CMD="$PYTEST_CMD tests/unit/"
    echo -e "${YELLOW}📋 Running unit tests only${NC}"
elif [ "$INTEGRATION_ONLY" = true ]; then
    PYTEST_CMD="$PYTEST_CMD tests/integration/"
    echo -e "${YELLOW}📋 Running integration tests only${NC}"
else
    PYTEST_CMD="$PYTEST_CMD tests/"
    echo -e "${YELLOW}📋 Running all tests${NC}"
fi

# Add options based on flags
if [ "$FAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --tb=short -q -m 'not slow'"
    echo -e "${YELLOW}⚡ Fast mode: skipping slow tests${NC}"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=website --cov-report=html --cov-report=term"
    echo -e "${YELLOW}📊 Coverage reporting enabled${NC}"
fi

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
    echo -e "${YELLOW}🔍 Verbose output enabled${NC}"
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
    echo -e "${YELLOW}🚀 Parallel execution enabled${NC}"
fi

echo ""
echo -e "${GREEN}▶️  Executing: $PYTEST_CMD${NC}"
echo ""

# Run the tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo -e "${GREEN}📊 Coverage report generated in htmlcov/index.html${NC}"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi