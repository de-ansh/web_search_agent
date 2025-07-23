# 🔧 Render Deployment Troubleshooting Guide

## Common Issues and Solutions

### 0. **Running Without OpenAI API (Recommended)**

**✅ This is the default and recommended setup!**

**What you'll see**:
```
⚠️  No OpenAI API key found, using extractive summarization
```

**Features without OpenAI**:
- ✅ **Extractive summarization** (smart sentence scoring)
- ✅ **Query-aware content extraction** 
- ✅ **Fast and reliable** (no external API calls)
- ✅ **Privacy-friendly** (no data sent to external services)
- ✅ **No API costs or rate limits**

**How it works**:
- Scores sentences based on length, position, and query relevance
- Extracts most important sentences for summaries
- Provides method="extractive" in API responses

**Optional**: To add OpenAI later, just set `OPENAI_API_KEY` in Render dashboard.

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

#### Backend 502 Error
**Problem**: Backend service returns 502 error (service not starting)

**Solution**: Check these common issues:

1. **PYTHONPATH Configuration**:
```yaml
envVars:
  - key: PYTHONPATH
    value: .
```
**Note**: Don't set custom PORT variable, Render provides $PORT automatically

2. **Import Issues**: Use relative imports in main_render.py
3. **Missing Dependencies**: Ensure all imports are in requirements-render.txt

#### Service Timeout During Startup
**Problem**: Backend starts but then "Timed Out" error

**Solution**: Add health check configuration:
```yaml
services:
  - type: web
    name: web-search-agent-backend
    healthCheckPath: "/health"
```

**Alternative**: The service works without OpenAI (uses extractive summarization):
```
⚠️  No OpenAI API key found, using extractive summarization
```
**This is normal and expected behavior!**

#### AttributeError: 'QueryValidationResult' object has no attribute 'to_dict'
**Problem**: `❌ Search failed: 'QueryValidationResult' object has no attribute 'to_dict'`

**Root Cause**: Pydantic models use `.dict()` method, not `.to_dict()`

**Solution**: Fixed in main_render.py:
```python
# Before (broken):
validation_info=validation_result.to_dict()

# After (fixed):
validation_info=validation_result.dict()
```

**Files Updated**:
- `src/api/main_render.py`: All `.to_dict()` calls changed to `.dict()`
- Also fixed `validation_result.message` → `validation_result.reason`

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

**Solution**: Use Render's provided PORT variable
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

#### API Connection Problems
**Problem**: Frontend shows "Backend: Disconnected" or API calls fail

**Debug Steps**:
1. Check build logs for backend URL construction:
   ```
   🔍 Debug - Original BACKEND_URL: your-backend-service.render.com
   🔍 Debug - Final backend URL: https://your-backend-service.render.com
   ```

2. Test API endpoints directly:
   ```bash
   curl https://your-backend-service.render.com/health
   curl https://your-frontend-service.render.com/api/health
   ```

3. Check Next.js rewrite mapping:
   - `/api/health` → `https://backend-service/health`
   - `/api/search` → `https://backend-service/search`

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

**Common Issues**:
- Backend service name mismatch
- Backend service not deployed yet
- Service discovery delays (wait 2-3 minutes after deployment)

#### DNS Resolution Error (ENOTFOUND)
**Problem**: `Failed to proxy https://web-search-agent-backend/health [Error: getaddrinfo ENOTFOUND web-search-agent-backend]`

**Root Cause**: `fromService.property: host` returns incomplete hostname (missing `.render.com`)

**Solution**: Updated render.yaml to use `hostNoPort` and added hostname fix:
```yaml
envVars:
  - key: BACKEND_URL
    fromService:
      type: web
      name: web-search-agent-backend
      property: hostNoPort  # Changed from 'host'
```

**Next.js Config Fix**: Automatically adds `.render.com` suffix:
```javascript
// Detects incomplete hostnames and fixes them
if (hostname && !hostname.includes('.') && hostname.includes('-')) {
  backendUrl = `${protocol}://${hostname}.render.com`;
}
```

**Expected Result**: 
- Before: `https://web-search-agent-backend/health`
- After: `https://web-search-agent-backend.render.com/health`

**Manual Override** (if `fromService` doesn't work):
```yaml
envVars:
  - key: BACKEND_URL
    value: https://web-search-agent-backend.render.com
  - key: NEXT_PUBLIC_BACKEND_URL
    value: https://web-search-agent-backend.render.com
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

#### TypeScript Dependencies Missing
**Problem**: "TypeScript but do not have the required package(s) installed"

**Solution**: Move TypeScript and type definitions to main `dependencies` section
```json
{
  "dependencies": {
    "typescript": "^5.8.3",
    "@types/node": "^20.19.7",
    "@types/react": "^18.3.23",
    "@types/react-dom": "^18"
  }
}
```
**Note**: TypeScript compiler and type definitions are needed during Next.js build process

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