#!/bin/bash

# Enhanced Web Scraping with uv runner script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed"
        echo "Please install uv first:"
        echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "or visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    print_status "uv is installed: $(uv --version)"
}

# Setup environment
setup() {
    print_info "Setting up Enhanced Web Scraping Environment"
    echo "=================================================="
    
    check_uv
    
    print_info "Installing dependencies with uv..."
    uv sync
    
    print_info "Installing Playwright browsers..."
    uv run playwright install chromium
    
    print_status "Environment setup completed!"
}

# Setup API keys
setup_keys() {
    print_info "Setting up API Keys"
    echo "==================="
    
    uv run python setup_gemini_api.py
}

# Run tests
test() {
    print_info "Running Enhanced Research Tests"
    echo "==============================="
    
    uv run python test_runner.py
}

# Start server
server() {
    print_info "Starting Enhanced Web Scraping Server"
    echo "====================================="
    
    echo "Server will be available at:"
    echo "   🌐 http://localhost:8000"
    echo "   📚 API Docs: http://localhost:8000/docs"
    echo "   🔍 Enhanced Research: http://localhost:8000/research/enhanced"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "--------------------------------"
    
    # Try lightweight mode first for faster startup
    if uv run python start_lightweight.py 2>/dev/null; then
        echo "✅ Started in lightweight mode"
    else
        echo "⚠️  Falling back to full mode"
        uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
    fi
}

# Run example
example() {
    print_info "Running Usage Examples"
    echo "======================"
    
    uv run python example_usage.py
}

# Show help
show_help() {
    echo "Enhanced Web Scraping with uv"
    echo "============================="
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Set up environment and install dependencies"
    echo "  keys      - Set up API keys (Gemini, OpenAI)"
    echo "  test      - Run enhanced research tests"
    echo "  server    - Start the FastAPI server"
    echo "  example   - Run usage examples"
    echo "  all       - Do everything (setup + keys + test + server)"
    echo ""
    echo "Direct uv commands:"
    echo "  uv run uvicorn src.api.main:app --reload"
    echo "  uv run python test_enhanced_research.py"
    echo "  uv run python setup_gemini_api.py"
    echo "  uv run python example_usage.py"
    echo ""
    echo "Examples:"
    echo "  ./run.sh setup     # Set up everything"
    echo "  ./run.sh server    # Start the server"
    echo "  ./run.sh all       # Complete setup and run"
}

# Main logic
case "${1:-help}" in
    setup)
        setup
        ;;
    keys)
        setup_keys
        ;;
    test)
        test
        ;;
    server)
        server
        ;;
    example)
        example
        ;;
    all)
        print_info "Complete Setup and Run"
        echo "======================"
        setup
        setup_keys
        test
        print_status "All tests passed! Starting server..."
        sleep 2
        server
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac