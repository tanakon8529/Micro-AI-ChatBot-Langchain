#!/bin/bash

# Exit on error
set -e

# Get script directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)

# Parse environment argument
ENV="dev"
if [ "$1" = "-uat" ]; then
    ENV="uat"
elif [ "$1" = "-dev" ]; then
    ENV="dev"
fi

# Error handler
cleanup_and_exit() {
    local exit_code=$?
    printf "\n🧹 Starting cleanup...\n"
    
    if [ "$ENV" = "dev" ]; then
        printf "🧹 Stopping containers...\n"
        cd "$PROJECT_ROOT" && docker compose down --remove-orphans
    fi
    
    if [ $exit_code -ne 0 ]; then
        printf "❌ Tests failed with exit code: %d\n" "$exit_code"
        printf "📝 Check the logs above for details\n"
    fi
    
    exit $exit_code
}

# Set up trap for cleanup
trap cleanup_and_exit EXIT
trap 'exit 1' INT TERM

# Colors and emojis
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Helper functions
print_header() {
    printf "\n${BLUE}${BOLD}%s${NC}\n" "$1"
}

print_step() {
    printf "${BLUE}${BOLD}%s${NC} %s\n" "$1" "$2"
}

# Check service health
check_service_health() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    printf "Checking health of %s service...\n" "http://localhost:$port/$service/v1/health/"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/$service/v1/health/" | grep -q "healthy"; then
            printf "✅ %s is healthy!\n" "$service"
            return 0
        fi
        printf "⏳ Waiting for %s to be healthy... (Attempt %d/%d)\n" "$service" "$attempt" "$max_attempts"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    printf "❌ %s health check failed after %d attempts\n" "$service" "$max_attempts"
    return 1
}

# Setup test environment
print_header "Setting up test environment for ${ENV}"

# Setup Python virtual environment
VENV_DIR="src/tests/venv"
if [ ! -d "$VENV_DIR" ]; then
    print_step "📦" "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
. "$VENV_DIR/bin/activate"

# Copy requirements in share into tests requirements-test.txt
print_step "📦" "Copy and Install project dependencies..."
cp src/share/requirements.txt src/tests/requirements-test.txt
pip install -r src/tests/requirements-test.txt

if [ "$ENV" = "dev" ]; then
    # Copy .env files
    print_step "📝" "Copying environment files..."
    "$SCRIPT_DIR/copy-env.sh"
    
    # Load environment variables
    print_step "🔄" "Loading environment variables..."
    if [ -f "$SCRIPT_DIR/.env" ]; then
        set -a
        . "$SCRIPT_DIR/.env"
        set +a
    else
        printf "❌ Error: .env file not found in tests directory\n"
        exit 1
    fi
    
    # Start services
    print_step "🚀" "Starting services..."
    cd "$PROJECT_ROOT" && ./start.sh -test
    cd - > /dev/null
    
    # Check service health
    print_step "🏥" "Checking service health..."
    check_service_health "oauth" "${PORT_FASTAPI_OAUTH2}"
    check_service_health "langgpt" "${PORT_FASTAPI_AI_CHAT}"
fi

# Run tests
print_header "Running Tests"

# Set up Python path for tests
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Set environment variables for tests
if [ "$ENV" = "uat" ]; then
    export BASE_URL_OAUTH="${HOST_UAT}/oauth/v1"
    export BASE_URL_CHAT="${HOST_UAT}/langgpt/v1"
else
    export BASE_URL_OAUTH="http://localhost:${PORT_FASTAPI_OAUTH2}/oauth/v1"
    export BASE_URL_CHAT="http://localhost:${PORT_FASTAPI_AI_CHAT}/langgpt/v1"
fi

# 1. Unit Tests
print_step "🧪" "Running unit tests..."
python3 -m pytest src/share/utilities/test_*.py -v --cov=src/share/utilities --cov-report=term-missing

# 2. Integration Tests
print_step "🧪" "Running integration tests..."
python3 -m pytest src/tests/integration/ -v

# 3. Load Tests
print_step "🧪" "Running load tests..."
if [ "$ENV" = "uat" ]; then
    export BASE_URL_OAUTH="${HOST_UAT}/v1"
    export BASE_URL_CHAT="${HOST_UAT}/v1"
else
    export BASE_URL_OAUTH="http://localhost:${PORT_FASTAPI_OAUTH2}/oauth/v1"
    export BASE_URL_CHAT="http://localhost:${PORT_FASTAPI_AI_CHAT}/langgpt/v1"
fi

if command -v k6 >/dev/null 2>&1; then
    k6 run src/tests/load/chatbot_load_test.js
else
    printf "⚠️ k6 is not installed. Skipping load tests.\n"
    printf "To install k6, visit: https://k6.io/docs/getting-started/installation\n"
fi

# Cleanup
print_header "Tests completed"
deactivate
