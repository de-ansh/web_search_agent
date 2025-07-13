#!/bin/bash

# Local Deployment Setup Script for Web Search Agent
# This script helps you set up and run the Web Search Agent locally using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏠 Setting up Web Search Agent locally${NC}"
echo ""

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
        echo "Visit: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    if ! docker --version &> /dev/null; then
        echo -e "${RED}❌ Docker is not running. Please start Docker.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker is installed and running${NC}"
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not available. Please install Docker Compose.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker Compose is available${NC}"
}

# Create .env file
create_env_file() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}🔐 Setting up environment variables...${NC}"
        
        # Prompt for OpenAI API key
        echo -e "${YELLOW}Please enter your OpenAI API Key:${NC}"
        read -s OPENAI_API_KEY
        
        if [ -z "$OPENAI_API_KEY" ]; then
            echo -e "${RED}❌ OpenAI API Key is required${NC}"
            exit 1
        fi
        
        # Create .env file
        cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=$OPENAI_API_KEY

# Application Configuration
PORT=8000
NODE_ENV=development
PYTHONUNBUFFERED=1
EOF
        
        echo -e "${GREEN}✅ Environment file created${NC}"
    else
        echo -e "${GREEN}✅ Environment file already exists${NC}"
    fi
}

# Build and start services
start_services() {
    echo -e "${BLUE}🚀 Building and starting services...${NC}"
    
    # Build images
    echo -e "${YELLOW}Building Docker images...${NC}"
    if command -v docker-compose &> /dev/null; then
        docker-compose build
    else
        docker compose build
    fi
    
    # Start services
    echo -e "${YELLOW}Starting services...${NC}"
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    echo -e "${GREEN}✅ Services started successfully${NC}"
}

# Wait for services to be ready
wait_for_services() {
    echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
    
    # Wait for backend
    echo -e "${YELLOW}Checking backend health...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend is healthy${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Backend health check failed${NC}"
            exit 1
        fi
        sleep 2
    done
    
    # Wait for frontend
    echo -e "${YELLOW}Checking frontend health...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:3000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend is healthy${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Frontend health check failed${NC}"
            exit 1
        fi
        sleep 2
    done
}

# Show success message
show_success() {
    echo ""
    echo -e "${GREEN}🎉 Web Search Agent is running locally!${NC}"
    echo ""
    echo -e "${YELLOW}Access your application:${NC}"
    echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
    echo -e "${BLUE}Backend API:${NC} http://localhost:8000"
    echo -e "${BLUE}Backend Health:${NC} http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo "• View logs: docker-compose logs -f"
    echo "• Stop services: docker-compose down"
    echo "• Restart services: docker-compose restart"
    echo "• Update and rebuild: docker-compose up -d --build"
    echo ""
    echo -e "${GREEN}Happy searching! 🔍✨${NC}"
}

# Clean up function
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up...${NC}"
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
}

# Main execution
main() {
    check_docker
    check_docker_compose
    create_env_file
    start_services
    wait_for_services
    show_success
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --stop         Stop all services"
        echo "  --restart      Restart all services"
        echo "  --logs         Show service logs"
        echo "  --clean        Clean up and remove containers"
        echo ""
        echo "This script sets up and runs the Web Search Agent locally using Docker"
        exit 0
        ;;
    --stop)
        echo -e "${YELLOW}Stopping services...${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose down
        else
            docker compose down
        fi
        echo -e "${GREEN}✅ Services stopped${NC}"
        exit 0
        ;;
    --restart)
        echo -e "${YELLOW}Restarting services...${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose restart
        else
            docker compose restart
        fi
        echo -e "${GREEN}✅ Services restarted${NC}"
        exit 0
        ;;
    --logs)
        if command -v docker-compose &> /dev/null; then
            docker-compose logs -f
        else
            docker compose logs -f
        fi
        exit 0
        ;;
    --clean)
        echo -e "${YELLOW}Cleaning up containers and images...${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose down --volumes --remove-orphans
        else
            docker compose down --volumes --remove-orphans
        fi
        echo -e "${GREEN}✅ Cleanup completed${NC}"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 