# 🚀 Deployment Guide - Web Search Agent on Google Cloud Platform

This guide will walk you through deploying the Web Search Agent to Google Cloud Platform (GCP) using Cloud Run, a fully managed serverless platform.

## 📋 Prerequisites

Before starting, ensure you have:

1. **Google Cloud Platform Account** with billing enabled
2. **Google Cloud SDK (gcloud)** installed and configured
3. **Docker** installed (for local testing)
4. **OpenAI API Key** for the AI features
5. **Project ownership or Editor role** in your GCP project

## 🏗️ Architecture Overview

The application consists of two main components:

- **Backend**: Python FastAPI application with web scraping and AI capabilities
- **Frontend**: Next.js React application with a modern UI

Both services are deployed as separate Cloud Run services with automatic scaling.

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd WebSearchAgent

# Make scripts executable
chmod +x setup-gcp-secrets.sh deploy.sh
```

### 2. Initial GCP Setup

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Run the setup script
./setup-gcp-secrets.sh
```

This script will:
- ✅ Enable required GCP APIs
- 🔐 Create and store your OpenAI API key as a secret
- 🔑 Set up IAM permissions
- 📝 Create environment configuration files

### 3. Deploy to Cloud Run

```bash
# Deploy both frontend and backend
./deploy.sh
```

This will:
- 📦 Build Docker images for both services
- 🚀 Deploy to Cloud Run
- 🔗 Configure service URLs
- 🏥 Run health checks

### 4. Access Your Application

After deployment, you'll receive URLs for both services:
- **Frontend**: `https://web-search-agent-frontend-[hash]-uc.a.run.app`
- **Backend**: `https://web-search-agent-backend-[hash]-uc.a.run.app`

## 📁 Project Structure

```
WebSearchAgent/
├── backend/
│   ├── Dockerfile              # Backend container configuration
│   ├── cloudbuild.yaml         # Backend deployment configuration
│   └── src/                    # Python source code
├── frontend/
│   ├── Dockerfile              # Frontend container configuration
│   ├── cloudbuild.yaml         # Frontend deployment configuration
│   └── src/                    # Next.js source code
├── cloudbuild.yaml             # Combined deployment configuration
├── setup-gcp-secrets.sh        # Initial setup script
├── deploy.sh                   # Deployment script
└── DEPLOYMENT.md               # This file
```

## 🔧 Manual Deployment (Alternative)

If you prefer manual deployment or need more control:

### 1. Enable GCP APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  containerregistry.googleapis.com
```

### 2. Create Secrets

```bash
# Create OpenAI API key secret
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-
```

### 3. Deploy Backend

```bash
# Build and deploy backend
cd backend
gcloud builds submit --config cloudbuild.yaml
cd ..
```

### 4. Deploy Frontend

```bash
# Build and deploy frontend
cd frontend
gcloud builds submit --config cloudbuild.yaml
cd ..
```

### 5. Update Frontend with Backend URL

```bash
# Get backend URL
BACKEND_URL=$(gcloud run services describe web-search-agent-backend \
  --region=us-central1 \
  --format='value(status.url)')

# Update frontend with backend URL
gcloud run services update web-search-agent-frontend \
  --set-env-vars="BACKEND_URL=$BACKEND_URL" \
  --region=us-central1
```

## ⚙️ Configuration

### Environment Variables

#### Backend
- `PORT`: Server port (default: 8000)
- `OPENAI_API_KEY`: OpenAI API key (stored as secret)

#### Frontend
- `PORT`: Server port (default: 3000)
- `NODE_ENV`: Environment (production)
- `BACKEND_URL`: Backend service URL

### Resource Allocation

#### Backend Service
- **Memory**: 2GB
- **CPU**: 2 vCPUs
- **Timeout**: 300 seconds
- **Max Instances**: 10
- **Min Instances**: 0 (scales to zero)

#### Frontend Service
- **Memory**: 1GB
- **CPU**: 1 vCPU
- **Timeout**: 60 seconds
- **Max Instances**: 10
- **Min Instances**: 0 (scales to zero)

## 🔒 Security Considerations

1. **Secrets Management**: OpenAI API key is stored in Google Secret Manager
2. **IAM Permissions**: Least privilege access for service accounts
3. **HTTPS**: All traffic is encrypted with automatic SSL certificates
4. **Container Security**: Non-root users in containers
5. **Network Security**: Services communicate over private Google network

## 💰 Cost Optimization

1. **Serverless**: Services scale to zero when not in use
2. **Request-based Pricing**: Pay only for actual usage
3. **Automatic Scaling**: Scales based on demand
4. **Resource Limits**: Configured to prevent runaway costs

### Estimated Monthly Costs (Light Usage)
- **Cloud Run**: $5-20/month
- **Container Registry**: $1-5/month
- **Secret Manager**: $0.10/month
- **Cloud Build**: $0.003/build minute

## 🔍 Monitoring and Logging

### View Logs
```bash
# Backend logs
gcloud logs read --follow --service=web-search-agent-backend

# Frontend logs
gcloud logs read --follow --service=web-search-agent-frontend
```

### Service Status
```bash
# List all services
gcloud run services list

# Describe a specific service
gcloud run services describe web-search-agent-backend --region=us-central1
```

### Health Checks
- Backend: `https://your-backend-url/health`
- Frontend: `https://your-frontend-url/health`

## 🐛 Troubleshooting

### Common Issues

#### 1. Build Timeouts
```bash
# Increase build timeout
gcloud builds submit --timeout=3600s
```

#### 2. Memory Issues
```bash
# Increase memory allocation
gcloud run services update web-search-agent-backend \
  --memory=4Gi \
  --region=us-central1
```

#### 3. Cold Start Issues
```bash
# Set minimum instances
gcloud run services update web-search-agent-backend \
  --min-instances=1 \
  --region=us-central1
```

#### 4. Permission Denied
```bash
# Check IAM permissions
gcloud projects get-iam-policy $PROJECT_ID

# Add missing roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/run.admin"
```

### Debug Commands
```bash
# Check service configuration
gcloud run services describe web-search-agent-backend \
  --region=us-central1 \
  --format=yaml

# View build history
gcloud builds list --limit=10

# Check secret access
gcloud secrets versions access latest --secret=openai-api-key
```

## 🔄 Updates and Maintenance

### Update Application
```bash
# Update both services
./deploy.sh

# Update only backend
cd backend && gcloud builds submit --config cloudbuild.yaml

# Update only frontend
cd frontend && gcloud builds submit --config cloudbuild.yaml
```

### Rollback
```bash
# List revisions
gcloud run revisions list --service=web-search-agent-backend

# Rollback to specific revision
gcloud run services update-traffic web-search-agent-backend \
  --to-revisions=web-search-agent-backend-00001-abc=100 \
  --region=us-central1
```

## 🌐 Custom Domain (Optional)

### 1. Map Custom Domain
```bash
# Map domain to service
gcloud run domain-mappings create \
  --service=web-search-agent-frontend \
  --domain=your-domain.com \
  --region=us-central1
```

### 2. Configure DNS
Add the provided DNS records to your domain registrar.

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Container Registry Documentation](https://cloud.google.com/container-registry/docs)

## 🤝 Support

If you encounter issues:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review service logs
3. Verify IAM permissions
4. Check API quotas and limits

## 🎉 Success!

Your Web Search Agent is now deployed on Google Cloud Platform! 

The application provides:
- 🔍 Intelligent web search across multiple engines
- 🤖 AI-powered content summarization
- 📊 Real-time performance monitoring
- 🔄 Automatic scaling based on demand
- 🔒 Enterprise-grade security

Enjoy your fully deployed, production-ready Web Search Agent! 🚀 