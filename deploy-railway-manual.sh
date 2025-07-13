#!/bin/bash

# Manual Railway Deployment - Simplified
# Use this if the main deployment script fails

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚂 Manual Railway Deployment${NC}"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found. Installing...${NC}"
    npm install -g @railway/cli
fi

# Login to Railway
echo -e "${YELLOW}Please log in to Railway...${NC}"
railway login

echo ""
echo -e "${GREEN}=== DEPLOYING BACKEND ===${NC}"
cd backend

# Initialize project
echo -e "${YELLOW}Initializing backend project...${NC}"
railway init

# Set environment variables
echo -e "${YELLOW}Please enter your OpenAI API Key:${NC}"
read -s OPENAI_API_KEY

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OpenAI API Key is required${NC}"
    exit 1
fi

echo -e "${YELLOW}Setting environment variables...${NC}"
railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
railway variables set PORT="8000"
railway variables set PYTHONPATH="/app"
railway variables set PYTHONUNBUFFERED="1"

# Deploy backend
echo -e "${YELLOW}Deploying backend...${NC}"
railway up

# Get backend URL
echo -e "${YELLOW}Getting backend URL...${NC}"
sleep 5
BACKEND_URL=$(railway status --json 2>/dev/null | jq -r '.deployments[0].url' 2>/dev/null || railway domain 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}❌ Could not get backend URL automatically.${NC}"
    echo -e "${YELLOW}Please get the URL from Railway dashboard and run:${NC}"
    echo "cd ../frontend"
    echo "railway init"
    echo "railway variables set BACKEND_URL=\"https://your-backend-url.railway.app\""
    echo "railway up"
    exit 1
fi

echo -e "${GREEN}✅ Backend deployed: $BACKEND_URL${NC}"

# Deploy frontend
echo ""
echo -e "${GREEN}=== DEPLOYING FRONTEND ===${NC}"
cd ../frontend

# Initialize frontend project
echo -e "${YELLOW}Initializing frontend project...${NC}"
railway init

# Set frontend environment variables
echo -e "${YELLOW}Setting frontend environment variables...${NC}"
railway variables set BACKEND_URL="$BACKEND_URL"
railway variables set PORT="3000"
railway variables set NODE_ENV="production"
railway variables set NEXT_TELEMETRY_DISABLED="1"

# Deploy frontend
echo -e "${YELLOW}Deploying frontend...${NC}"
railway up

# Get frontend URL
echo -e "${YELLOW}Getting frontend URL...${NC}"
sleep 5
FRONTEND_URL=$(railway status --json 2>/dev/null | jq -r '.deployments[0].url' 2>/dev/null || railway domain 2>/dev/null || echo "Check Railway Dashboard")

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${YELLOW}Backend:${NC} $BACKEND_URL"
echo -e "${YELLOW}Frontend:${NC} $FRONTEND_URL"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Test your backend: curl $BACKEND_URL/health"
echo "2. Open your app: $FRONTEND_URL"
echo "3. Check Railway dashboard for logs and monitoring" 