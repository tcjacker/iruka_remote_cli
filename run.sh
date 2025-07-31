#!/bin/bash

# Gemini CLI Docker Integration - Quick Run Script
# This script provides convenient commands to run the system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "🚀 Gemini CLI Docker Integration - Run Script"
    echo "=============================================="
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [--debug] [--port PORT]  Start the main service"
    echo "  demo [DEMO_NAME]               Run a demo script"
    echo "  test                           Run tests"
    echo "  build                          Build Docker image"
    echo "  clean                          Clean up containers and processes"
    echo "  setup                          Run initial setup"
    echo "  help                           Show this help message"
    echo ""
    echo "Demo options:"
    echo "  showcase                       Run the comprehensive demo (default)"
    echo "  git                           Run basic Git integration demo"
    echo "  git-improved                  Run enhanced Git integration demo"
    echo "  gemini                        Run original Gemini system demo"
    echo ""
    echo "Examples:"
    echo "  $0 start                      # Start service on default port 8081"
    echo "  $0 start --debug --port 8082  # Start with debug mode on port 8082"
    echo "  $0 demo showcase              # Run comprehensive demo"
    echo "  $0 demo git                   # Run Git integration demo"
    echo "  $0 build                      # Build Docker image"
    echo "  $0 clean                      # Clean up everything"
}

check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
        echo "   Run: source venv/bin/activate"
        echo "   Or use: ./setup.sh to create one"
        exit 1
    fi
    echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
}

check_env_file() {
    if [[ ! -f ".env" ]]; then
        echo -e "${YELLOW}⚠️  .env file not found${NC}"
        echo "   Run: cp .env.example .env"
        echo "   Then edit .env and add your Gemini API key"
        exit 1
    fi
}

check_docker_image() {
    if ! docker images | grep -q "agent-service.*latest"; then
        echo -e "${YELLOW}⚠️  Docker image 'agent-service:latest' not found${NC}"
        echo "   Run: $0 build"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker image found${NC}"
}

build_image() {
    echo -e "${BLUE}🐳 Building Docker image...${NC}"
    cd core/agent
    docker build -t agent-service:latest .
    cd ../..
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
}

start_service() {
    local debug_flag=""
    local port_flag=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --debug|-d)
                debug_flag="--debug"
                shift
                ;;
            --port|-p)
                port_flag="--port $2"
                shift 2
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                exit 1
                ;;
        esac
    done
    
    check_venv
    check_env_file
    check_docker_image
    
    echo -e "${BLUE}🚀 Starting main service...${NC}"
    python main.py $debug_flag $port_flag
}

run_demo() {
    local demo_name="${1:-showcase}"
    
    check_venv
    check_env_file
    check_docker_image
    
    case $demo_name in
        showcase|final)
            echo -e "${BLUE}🎪 Running comprehensive demo...${NC}"
            python demos/demo_final_showcase.py
            ;;
        git|git-basic)
            echo -e "${BLUE}🎪 Running Git integration demo...${NC}"
            python demos/demo_git_integration.py
            ;;
        git-improved|git-enhanced)
            echo -e "${BLUE}🎪 Running enhanced Git integration demo...${NC}"
            python demos/demo_git_integration_improved.py
            ;;
        gemini|gemini-system)
            echo -e "${BLUE}🎪 Running Gemini system demo...${NC}"
            python demos/demo_gemini_system.py
            ;;
        *)
            echo -e "${RED}❌ Unknown demo: $demo_name${NC}"
            echo "Available demos: showcase, git, git-improved, gemini"
            exit 1
            ;;
    esac
}

run_tests() {
    check_venv
    check_env_file
    
    echo -e "${BLUE}🧪 Running tests...${NC}"
    if [[ -f "tests/quick_test.py" ]]; then
        python tests/quick_test.py
    else
        echo -e "${YELLOW}⚠️  No tests found in tests/ directory${NC}"
    fi
}

clean_up() {
    echo -e "${BLUE}🧹 Cleaning up...${NC}"
    ./cleanup.sh
}

setup_project() {
    echo -e "${BLUE}⚙️ Running project setup...${NC}"
    ./setup.sh
}

# Main command processing
case "${1:-help}" in
    start)
        shift
        start_service "$@"
        ;;
    demo)
        shift
        run_demo "$@"
        ;;
    test|tests)
        run_tests
        ;;
    build)
        build_image
        ;;
    clean|cleanup)
        clean_up
        ;;
    setup)
        setup_project
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac
