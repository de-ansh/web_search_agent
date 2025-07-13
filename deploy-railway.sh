#!/bin/bash

# Railway Deployment Script for Web Search Agent
# This script helps deploy your Web Search Agent to Railway for FREE

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚂 Deploying Web Search Agent to Railway (FREE)${NC}"
echo ""

# Check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        echo -e "${YELLOW}⚠️  Railway CLI not installed. Installing...${NC}"
        
        # Install Railway CLI
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install railway
        elif [[ "$OSTYPE" == "linux"* ]]; then
            # Linux
            bash <(curl -fsSL https://railway.app/install.sh)
        else
            echo -e "${RED}❌ Please install Railway CLI manually:${NC}"
            echo "Visit: https://docs.railway.app/develop/cli"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ Railway CLI is installed${NC}"
}

# Login to Railway
login_railway() {
    echo -e "${BLUE}🔐 Logging into Railway...${NC}"
    
    if ! railway whoami &> /dev/null; then
        echo -e "${YELLOW}Please log in to Railway...${NC}"
        railway login
    fi
    
    echo -e "${GREEN}✅ Logged into Railway${NC}"
}

# Create or link project
setup_project() {
    echo -e "${BLUE}📁 Setting up Railway project...${NC}"
    
    # Check if already linked
    if [ ! -f ".railway/project.json" ]; then
        echo -e "${YELLOW}Creating new Railway project...${NC}"
        railway init
    else
        echo -e "${GREEN}✅ Railway project already linked${NC}"
    fi
}

# Deploy backend
deploy_backend() {
    echo -e "${BLUE}🚀 Deploying backend...${NC}"
    
    cd backend
    
    # Create railway service for backend
    railway service create web-search-agent-backend || true
    
    # Set environment variables
    echo -e "${YELLOW}Setting up environment variables...${NC}"
    
    # Prompt for OpenAI API key
    echo -e "${YELLOW}Please enter your OpenAI API Key:${NC}"
    read -s OPENAI_API_KEY
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}❌ OpenAI API Key is required${NC}"
        exit 1
    fi
    
    # Set the API key
    railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
    railway variables set PORT=8000
    railway variables set PYTHONUNBUFFERED=1
    
    # Deploy
    railway deploy
    
    # Get the backend URL
    BACKEND_URL=$(railway status --json | jq -r '.deployments[0].url')
    echo -e "${GREEN}✅ Backend deployed at: $BACKEND_URL${NC}"
    
    cd ..
    
    # Save backend URL for frontend
    echo "$BACKEND_URL" > .backend_url
}

# Deploy frontend
deploy_frontend() {
    echo -e "${BLUE}🚀 Deploying frontend...${NC}"
    
    cd frontend
    
    # Create railway service for frontend
    railway service create web-search-agent-frontend || true
    
    # Set environment variables
    BACKEND_URL=$(cat ../.backend_url)
    railway variables set BACKEND_URL="$BACKEND_URL"
    railway variables set PORT=3000
    railway variables set NODE_ENV=production
    
    # Deploy
    railway deploy
    
    # Get the frontend URL
    FRONTEND_URL=$(railway status --json | jq -r '.deployments[0].url')
    echo -e "${GREEN}✅ Frontend deployed at: $FRONTEND_URL${NC}"
    
    cd ..
    
    # Clean up
    rm -f .backend_url
}

# Show deployment info
show_deployment_info() {
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Your Web Search Agent is now live:${NC}"
    echo -e "${BLUE}Frontend:${NC} Visit the frontend URL above"
    echo -e "${BLUE}Backend:${NC} API available at backend URL"
    echo ""
    echo -e "${GREEN}Railway Free Tier Benefits:${NC}"
    echo "• ✅ $5/month in credits (enough for light usage)"
    echo "• ✅ Automatic HTTPS"
    echo "• ✅ Custom domains"
    echo "• ✅ Auto-scaling"
    echo "• ✅ Built-in monitoring"
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo "• View logs: railway logs"
    echo "• Check status: railway status"
    echo "• Open dashboard: railway open"
    echo "• Redeploy: railway deploy"
    echo ""
    echo -e "${GREEN}Happy searching! 🔍✨${NC}"
}

# Main execution
main() {
    check_railway_cli
    login_railway
    setup_project
    deploy_backend
    deploy_frontend
    show_deployment_info
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo ""
        echo "This script deploys the Web Search Agent to Railway for FREE"
        echo "Railway provides $5/month in credits, perfect for personal projects"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 