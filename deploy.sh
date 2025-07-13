#!/bin/bash

# GCP Web Search Agent - Deployment Script
# This script deploys the Web Search Agent to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
BUILD_CONFIG=${BUILD_CONFIG:-"cloudbuild.yaml"}

echo -e "${GREEN}🚀 Deploying Web Search Agent to Google Cloud Run${NC}"
echo -e "${YELLOW}Project ID: $PROJECT_ID${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo -e "${YELLOW}Build Config: $BUILD_CONFIG${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
        echo "Visit: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}❌ gcloud is not authenticated. Please run 'gcloud auth login' first.${NC}"
        exit 1
    fi
    
    # Check if project exists
    if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
        echo -e "${RED}❌ Project $PROJECT_ID does not exist or you don't have access.${NC}"
        exit 1
    fi
    
    # Check if Docker files exist
    if [ ! -f "backend/Dockerfile" ] || [ ! -f "frontend/Dockerfile" ]; then
        echo -e "${RED}❌ Docker files not found. Please make sure both backend/Dockerfile and frontend/Dockerfile exist.${NC}"
        exit 1
    fi
    
    # Check if build config exists
    if [ ! -f "$BUILD_CONFIG" ]; then
        echo -e "${RED}❌ Build configuration file $BUILD_CONFIG not found.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to set the project
set_project() {
    echo -e "${BLUE}🔧 Setting GCP project...${NC}"
    gcloud config set project $PROJECT_ID
    echo -e "${GREEN}✅ Project set to $PROJECT_ID${NC}"
}

# Function to check required APIs
check_apis() {
    echo -e "${BLUE}🔍 Checking required APIs...${NC}"
    
    required_apis=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "secretmanager.googleapis.com"
        "containerregistry.googleapis.com"
    )
    
    for api in "${required_apis[@]}"; do
        if ! gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
            echo -e "${YELLOW}⚠️  API $api is not enabled. Please run the setup script first.${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ Required APIs are enabled${NC}"
}

# Function to check secrets
check_secrets() {
    echo -e "${BLUE}🔍 Checking secrets...${NC}"
    
    if ! gcloud secrets describe openai-api-key --project=$PROJECT_ID &> /dev/null; then
        echo -e "${YELLOW}⚠️  Secret 'openai-api-key' not found. Please run the setup script first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Required secrets are available${NC}"
}

# Function to start deployment
start_deployment() {
    echo -e "${BLUE}🚀 Starting deployment...${NC}"
    
    # Update PROJECT_ID in build configuration
    if [ -f "$BUILD_CONFIG" ]; then
        # Create a temporary build config with the correct PROJECT_ID
        cp "$BUILD_CONFIG" "${BUILD_CONFIG}.tmp"
        
        # If you want to substitute PROJECT_ID in the build config, uncomment the next line
        # sed -i "s/your-project-id/$PROJECT_ID/g" "${BUILD_CONFIG}.tmp"
        
        BUILD_CONFIG="${BUILD_CONFIG}.tmp"
    fi
    
    # Start the build
    echo -e "${BLUE}📦 Starting Cloud Build...${NC}"
    
    gcloud builds submit \
        --config="$BUILD_CONFIG" \
        --project="$PROJECT_ID" \
        --substitutions="_PROJECT_ID=$PROJECT_ID"
    
    # Clean up temporary file
    if [ -f "${BUILD_CONFIG}" ] && [[ "$BUILD_CONFIG" == *.tmp ]]; then
        rm "${BUILD_CONFIG}"
    fi
    
    echo -e "${GREEN}✅ Deployment completed successfully${NC}"
}

# Function to get service URLs
get_service_urls() {
    echo -e "${BLUE}🔗 Getting service URLs...${NC}"
    
    # Get backend URL
    BACKEND_URL=$(gcloud run services describe web-search-agent-backend \
        --region=$REGION \
        --format='value(status.url)' 2>/dev/null || echo "Not deployed")
    
    # Get frontend URL
    FRONTEND_URL=$(gcloud run services describe web-search-agent-frontend \
        --region=$REGION \
        --format='value(status.url)' 2>/dev/null || echo "Not deployed")
    
    echo ""
    echo -e "${GREEN}🎉 Deployment Summary:${NC}"
    echo -e "${YELLOW}Backend URL:${NC} $BACKEND_URL"
    echo -e "${YELLOW}Frontend URL:${NC} $FRONTEND_URL"
    echo ""
    
    # Create or update environment file
    cat > .env.production << EOF
# GCP Configuration
PROJECT_ID=$PROJECT_ID
REGION=$REGION

# Service URLs
BACKEND_URL=$BACKEND_URL
FRONTEND_URL=$FRONTEND_URL

# Environment
NODE_ENV=production
PORT=3000
EOF
    
    echo -e "${GREEN}✅ Environment file updated: .env.production${NC}"
}

# Function to run health checks
run_health_checks() {
    echo -e "${BLUE}🏥 Running health checks...${NC}"
    
    # Check backend health
    if [ "$BACKEND_URL" != "Not deployed" ]; then
        echo -e "${YELLOW}Checking backend health...${NC}"
        if curl -s -f "$BACKEND_URL/health" > /dev/null; then
            echo -e "${GREEN}✅ Backend is healthy${NC}"
        else
            echo -e "${RED}❌ Backend health check failed${NC}"
        fi
    fi
    
    # Check frontend health
    if [ "$FRONTEND_URL" != "Not deployed" ]; then
        echo -e "${YELLOW}Checking frontend health...${NC}"
        if curl -s -f "$FRONTEND_URL/health" > /dev/null; then
            echo -e "${GREEN}✅ Frontend is healthy${NC}"
        else
            echo -e "${RED}❌ Frontend health check failed${NC}"
        fi
    fi
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Visit the frontend URL to test the application"
    echo "2. Check Cloud Run logs if you encounter any issues:"
    echo "   gcloud logs read --follow --service=web-search-agent-backend"
    echo "   gcloud logs read --follow --service=web-search-agent-frontend"
    echo "3. Monitor the application in the GCP Console"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo "• View services: gcloud run services list"
    echo "• Update backend: gcloud builds submit --config backend/cloudbuild.yaml"
    echo "• Update frontend: gcloud builds submit --config frontend/cloudbuild.yaml"
    echo ""
    echo -e "${GREEN}Happy searching! 🔍✨${NC}"
}

# Main execution
main() {
    # Check if PROJECT_ID is provided
    if [ "$PROJECT_ID" = "your-project-id" ]; then
        echo -e "${RED}❌ Please set PROJECT_ID environment variable${NC}"
        echo "Example: export PROJECT_ID=your-actual-project-id"
        echo "         ./deploy.sh"
        exit 1
    fi
    
    check_prerequisites
    set_project
    check_apis
    check_secrets
    start_deployment
    get_service_urls
    run_health_checks
    show_next_steps
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo ""
        echo "Environment variables:"
        echo "  PROJECT_ID     GCP project ID (required)"
        echo "  REGION         GCP region (default: us-central1)"
        echo "  BUILD_CONFIG   Build configuration file (default: cloudbuild.yaml)"
        echo ""
        echo "Examples:"
        echo "  export PROJECT_ID=my-project && ./deploy.sh"
        echo "  PROJECT_ID=my-project ./deploy.sh"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 