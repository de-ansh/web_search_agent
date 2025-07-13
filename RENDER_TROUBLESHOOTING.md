# 🔧 Render Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. **Build Failures**

#### Heavy Dependencies Issue
**Problem**: Build fails with memory/time limits due to heavy dependencies (torch, transformers, playwright)

**Solution**: Use lightweight requirements
```bash
# Use requirements-render.txt instead of requirements.txt
pip install -r requirements-render.txt
```

**Fixed Dependencies**:
- ✅ Removed: `torch`, `transformers`, `sentence-transformers`, `playwright`
- ✅ Added: `httpx`, `lxml`, `scikit-learn` for lightweight functionality
- ✅ Kept: `fastapi`, `openai`, `beautifulsoup4`
- ✅ Created lightweight versions: `main_render.py`, `lightweight_scraper.py`, `lightweight_summarizer.py`, `lightweight_similarity.py`

#### Build Timeout Issue
**Problem**: Build process exceeds Render's free tier limits

**Solution**: Optimized build commands
```yaml
buildCommand: "pip install --upgrade pip && pip install -r requirements-render.txt"
```

### 2. **Start Command Issues**

#### Module Not Found
**Problem**: `ModuleNotFoundError: No module named 'src.api.main'` or `ModuleNotFoundError: No module named 'sklearn'`

**Solution**: Use the lightweight main file with all dependencies
```yaml
startCommand: "python -m uvicorn src.api.main_render:app --host 0.0.0.0 --port $PORT"
```

**Fixed Import Issues**:
- ✅ `sklearn` - Added to requirements-render.txt
- ✅ `transformers` - Created lightweight_summarizer.py without transformers
- ✅ `sentence_transformers` - Created lightweight_similarity.py without embeddings
- ✅ `playwright` - Created lightweight_scraper.py with requests only

#### Port Configuration
**Problem**: Service not accessible on the correct port

**Solution**: Ensure PORT environment variable is set
```yaml
envVars:
  - key: PORT
    value: 10000
  - key: PYTHONPATH
    value: /opt/render/project/src
```

### 3. **Environment Variables**

#### Missing PYTHONPATH
**Problem**: Import errors in Python modules

**Solution**: Set PYTHONPATH in render.yaml
```yaml
envVars:
  - key: PYTHONPATH
    value: /opt/render/project/src
```

#### OpenAI API Key
**Problem**: AI summarization fails

**Solution**: Set in Render Dashboard
1. Go to your service dashboard
2. Navigate to "Environment"
3. Add `OPENAI_API_KEY` with your key
4. Deploy again

### 4. **Frontend Issues**

#### Backend URL Not Set
**Problem**: Frontend can't connect to backend

**Solution**: Check environment variables
```yaml
envVars:
  - key: BACKEND_URL
    fromService:
      type: web
      name: web-search-agent-backend
      property: host
  - key: NEXT_PUBLIC_BACKEND_URL
    fromService:
      type: web
      name: web-search-agent-backend
      property: host
```

#### Build Process Issues
**Problem**: Frontend build fails

**Solution**: Use npm ci instead of npm install
```yaml
buildCommand: "npm ci --legacy-peer-deps && npm run build"
```

#### CSS Dependencies Not Found
**Problem**: "Cannot find module 'tailwindcss'" during build

**Solution**: Move CSS build dependencies to main `dependencies` section
```json
{
  "dependencies": {
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16"
  }
}
```
**Note**: Render only installs `dependencies` in production, not `devDependencies`

#### ESLint Required During Build
**Problem**: "ESLint must be installed in order to run during builds"

**Solution**: Move ESLint dependencies to main `dependencies` section
```json
{
  "dependencies": {
    "eslint": "^9",
    "eslint-config-next": "15.3.5",
    "@eslint/eslintrc": "^3",
    "typescript": "^5"
  }
}
```
**Note**: Next.js requires ESLint during the build process, not just development

### 5. **Resource Limits**

#### Memory Limits
**Problem**: Service crashes due to memory usage

**Solution**: Optimize memory usage
- Use lightweight scraper instead of Playwright
- Reduce concurrent requests
- Implement better caching

#### CPU Limits
**Problem**: Slow response times

**Solution**: Optimize processing
- Use simpler AI models
- Implement request queuing
- Cache frequently accessed results

### 6. **Deployment Process**

#### Using Render.yaml
1. **Connect Repository**:
   ```bash
   # Push your code to GitHub
   git add .
   git commit -m "Add Render configuration"
   git push origin main
   ```

2. **Deploy on Render**:
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Deploy both backend and frontend

3. **Manual Configuration**:
   If render.yaml doesn't work:
   - Create services manually
   - Backend: Python web service
   - Frontend: Node.js web service
   - Set environment variables manually

### 7. **Debugging Steps**

#### Check Build Logs
1. Go to your service dashboard
2. Click on "Logs"
3. Look for build errors

#### Common Log Errors:
```bash
# Memory limit exceeded
ERROR: Could not install packages due to an EnvironmentError: [Errno 28] No space left on device

# Solution: Use requirements-render.txt

# Module import error
ModuleNotFoundError: No module named 'playwright'

# Solution: Use main_render.py

# Port binding error
uvicorn.error: [Errno 98] Address already in use

# Solution: Check PORT environment variable
```

### 8. **Performance Optimization**

#### Reduce Dependencies
```bash
# Original (heavy)
pip install torch transformers playwright

# Optimized (light)
pip install requests beautifulsoup4 httpx
```

#### Cache Strategy
- Enable similarity detection caching
- Use in-memory caching for frequent queries
- Implement request deduplication

### 9. **Alternative Deployment Steps**

#### If Render.yaml Fails:

1. **Backend Manual Setup**:
   ```
   Service Type: Web Service
   Environment: Python 3.11
   Build Command: pip install -r requirements-render.txt
   Start Command: python -m uvicorn src.api.main_render:app --host 0.0.0.0 --port $PORT
   ```

2. **Frontend Manual Setup**:
   ```
   Service Type: Web Service
   Environment: Node.js
   Build Command: npm ci && npm run build
   Start Command: npm start
   ```

### 10. **Success Checklist**

#### Backend Health Check:
- [ ] Service starts without errors
- [ ] Health endpoint responds: `GET /health`
- [ ] Search endpoint works: `POST /search`
- [ ] No import errors in logs
- [ ] OpenAI API key is set

#### Frontend Health Check:
- [ ] Frontend builds successfully
- [ ] Pages load without errors
- [ ] API calls work
- [ ] Environment variables are set
- [ ] CORS is configured

### 11. **Common Error Messages**

#### "Build failed with exit code 1"
```bash
# Check: requirements-render.txt exists
# Check: Python version compatibility
# Check: Build command syntax
```

#### "Service failed to start"
```bash
# Check: Start command syntax
# Check: Port configuration
# Check: PYTHONPATH setting
```

#### "Service is not responding"
```bash
# Check: Backend URL configuration
# Check: CORS settings
# Check: Environment variables
```

### 12. **Getting Help**

#### Render Support:
- [Render Documentation](https://render.com/docs)
- [Render Community Discord](https://discord.gg/render)
- [Render Status Page](https://status.render.com/)

#### Debug Commands:
```bash
# Test locally first
python -m uvicorn src.api.main_render:app --host 0.0.0.0 --port 8000

# Check dependencies
pip list | grep -E "(fastapi|openai|beautifulsoup4)"

# Test endpoints
curl http://localhost:8000/health
```

### 13. **Success Example**

Once working, you should see:
```json
{
  "status": "healthy",
  "message": "All systems operational (Render mode)",
  "version": "2.0.0-render",
  "features": {
    "lightweight_scraper": true,
    "ai_summarization": true,
    "query_validation": true,
    "similarity_detection": true,
    "playwright": false
  }
}
```

## Quick Fix Summary

1. **Use lightweight requirements**: `requirements-render.txt`
2. **Use simplified main file**: `main_render.py`
3. **Set PYTHONPATH**: `/opt/render/project/src`
4. **Set OpenAI API key** in Render dashboard
5. **Use correct build commands** in `render.yaml`
6. **Check logs** for specific error messages

This should resolve most Render deployment issues! 🚀 