#!/bin/bash

# GCP Web Search Agent - Secrets Setup Script
# This script helps you set up required secrets and environment variables for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}

echo -e "${GREEN}🚀 Setting up GCP secrets for Web Search Agent${NC}"
echo -e "${YELLOW}Project ID: $PROJECT_ID${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo ""

# Function to check if gcloud is installed and authenticated
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
        echo "Visit: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}❌ gcloud is not authenticated. Please run 'gcloud auth login' first.${NC}"
        exit 1
    fi
}

# Function to enable required APIs
enable_apis() {
    echo -e "${GREEN}🔧 Enabling required GCP APIs...${NC}"
    
    gcloud services enable cloudbuild.googleapis.com \
        run.googleapis.com \
        secretmanager.googleapis.com \
        containerregistry.googleapis.com \
        --project=$PROJECT_ID
    
    echo -e "${GREEN}✅ APIs enabled successfully${NC}"
}

# Function to create secrets
create_secrets() {
    echo -e "${GREEN}🔐 Creating secrets...${NC}"
    
    # OpenAI API Key
    echo -e "${YELLOW}Please enter your OpenAI API Key:${NC}"
    read -s OPENAI_API_KEY
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}❌ OpenAI API Key is required${NC}"
        exit 1
    fi
    
    # Create or update the secret
    if gcloud secrets describe openai-api-key --project=$PROJECT_ID &> /dev/null; then
        echo -e "${YELLOW}⚠️  Secret 'openai-api-key' already exists. Updating...${NC}"
        echo -n "$OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=- --project=$PROJECT_ID
    else
        echo -e "${GREEN}Creating new secret 'openai-api-key'...${NC}"
        echo -n "$OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=- --project=$PROJECT_ID
    fi
    
    echo -e "${GREEN}✅ Secrets created successfully${NC}"
}

# Function to set IAM permissions
set_iam_permissions() {
    echo -e "${GREEN}🔑 Setting IAM permissions...${NC}"
    
    # Get the project number
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    
    # Grant Cloud Run service account access to secrets
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    # Grant Cloud Build service account permissions
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
        --role="roles/run.admin"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
        --role="roles/iam.serviceAccountUser"
    
    echo -e "${GREEN}✅ IAM permissions set successfully${NC}"
}

# Function to create environment file
create_env_file() {
    echo -e "${GREEN}📝 Creating environment configuration...${NC}"
    
    cat > .env.production << EOF
# GCP Configuration
PROJECT_ID=$PROJECT_ID
REGION=$REGION

# Service URLs (will be populated after deployment)
BACKEND_URL=https://web-search-agent-backend-[hash]-uc.a.run.app
FRONTEND_URL=https://web-search-agent-frontend-[hash]-uc.a.run.app

# Environment
NODE_ENV=production
PORT=3000
EOF
    
    echo -e "${GREEN}✅ Environment file created at .env.production${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}Starting GCP setup...${NC}"
    
    # Check if PROJECT_ID is provided
    if [ "$PROJECT_ID" = "your-project-id" ]; then
        echo -e "${RED}❌ Please set PROJECT_ID environment variable or update the script${NC}"
        echo "Example: export PROJECT_ID=your-actual-project-id"
        exit 1
    fi
    
    check_gcloud
    enable_apis
    create_secrets
    set_iam_permissions
    create_env_file
    
    echo ""
    echo -e "${GREEN}🎉 GCP setup completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Update PROJECT_ID in cloudbuild.yaml if needed"
    echo "2. Run: gcloud builds submit --config cloudbuild.yaml"
    echo "3. Check the deployment status in GCP Console"
    echo ""
    echo -e "${GREEN}Happy deploying! 🚀${NC}"
}

# Run main function
main "$@" 