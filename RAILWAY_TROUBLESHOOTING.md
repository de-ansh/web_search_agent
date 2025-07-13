# 🚂 Railway Deployment Troubleshooting

Having issues with Railway deployment? This guide covers common problems and solutions.

## 🔧 **Common Issues & Solutions**

### 1. **"No start command could be found" Error**

**Problem**: Railway can't detect how to start your application.

**Solutions**:

#### Option A: Use Procfile (Recommended)
```bash
# Backend: Create backend/Procfile
echo "web: python -m uvicorn src.api.main:app --host 0.0.0.0 --port \$PORT" > backend/Procfile

# Frontend: Create frontend/Procfile  
echo "web: npm start" > frontend/Procfile
```

#### Option B: Fix nixpacks.toml
Make sure your `nixpacks.toml` has the correct start command:

```toml
# backend/nixpacks.toml
[start]
cmd = "python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
```

#### Option C: Set Start Command in Railway Dashboard
1. Go to Railway dashboard
2. Select your service
3. Go to Settings → Deploy
4. Set Start Command: `python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

---

### 2. **Build Failures**

**Problem**: Dependency installation fails or build process errors.

**Solutions**:

#### For Backend Python Issues:
```bash
# Add to backend/Procfile or nixpacks.toml
PYTHONPATH="/app"
PYTHONUNBUFFERED="1"

# Use requirements.txt as fallback
pip install -r requirements.txt
```

#### For Frontend Node.js Issues:
```bash
# Clear npm cache
npm cache clean --force

# Use specific Node version in package.json
{
  "engines": {
    "node": "18.x",
    "npm": "9.x"
  }
}
```

---

### 3. **Playwright/Chromium Issues**

**Problem**: Browser automation fails on Railway.

**Solutions**:

#### Update your build process:
```bash
# In backend/build.sh
playwright install chromium --with-deps
export PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright
```

#### Environment variables to set:
```bash
PLAYWRIGHT_BROWSERS_PATH="/app/.cache/ms-playwright"
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD="false"
```

---

### 4. **Environment Variables Not Working**

**Problem**: API keys or config not available.

**Solutions**:

#### Set via Railway CLI:
```bash
cd backend
railway variables set OPENAI_API_KEY="your-key-here"
railway variables set PYTHONPATH="/app"
railway variables set PORT="8000"
```

#### Set via Railway Dashboard:
1. Go to your service
2. Variables tab
3. Add each variable

---

### 5. **Service Communication Issues**

**Problem**: Frontend can't reach backend.

**Solutions**:

#### Get backend URL and set in frontend:
```bash
# Get backend URL
railway domain

# Set in frontend
railway variables set BACKEND_URL="https://your-backend-url.railway.app"
```

---

## 🛠️ **Step-by-Step Fix Process**

### If deployment completely fails:

1. **Check Project Structure**:
   ```bash
   # Make sure you have these files:
   backend/Procfile          # or nixpacks.toml
   backend/requirements.txt  # Python dependencies
   frontend/Procfile         # or package.json scripts
   frontend/package.json     # Node.js dependencies
   ```

2. **Use Manual Deployment**:
   ```bash
   # Deploy backend manually
   cd backend
   railway login
   railway init
   railway deploy

   # Deploy frontend manually  
   cd ../frontend
   railway init
   railway deploy
   ```

3. **Check Logs**:
   ```bash
   railway logs
   ```

---

## 🔍 **Debugging Commands**

### Check Railway Status:
```bash
railway status
railway variables
railway logs --tail 100
```

### Test Locally First:
```bash
# Test backend
cd backend
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Test frontend
cd frontend
npm run build
npm start
```

---

## 🚨 **Emergency Fallback: Manual Setup**

If automated scripts fail, deploy manually:

### 1. Backend Manual Setup:
```bash
cd backend

# Login and create project
railway login
railway init

# Set environment variables
railway variables set OPENAI_API_KEY="your-key"
railway variables set PORT="8000"
railway variables set PYTHONPATH="/app"

# Create Procfile
echo "web: python -m uvicorn src.api.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
railway deploy
```

### 2. Frontend Manual Setup:
```bash
cd frontend

# Create project
railway init

# Get backend URL from Railway dashboard
# Set environment variable
railway variables set BACKEND_URL="https://your-backend.railway.app"
railway variables set PORT="3000"
railway variables set NODE_ENV="production"

# Create Procfile
echo "web: npm start" > Procfile

# Deploy
railway deploy
```

---

## 📋 **Pre-Deployment Checklist**

Before deploying to Railway:

- [ ] **Railway CLI installed**: `npm install -g @railway/cli`
- [ ] **Logged in**: `railway login`
- [ ] **OpenAI API key ready**
- [ ] **Both Procfiles exist** (backend/Procfile, frontend/Procfile)
- [ ] **requirements.txt exists** (backend/requirements.txt)
- [ ] **package.json scripts work** (npm run build, npm start)

---

## 🆘 **Still Having Issues?**

### Try Alternative Free Platforms:

1. **Render** (100% free with limitations):
   ```bash
   # Use render.yaml configuration
   git push origin main
   # Connect GitHub to Render
   ```

2. **Local Docker** (completely free):
   ```bash
   ./setup-local.sh
   ```

3. **Vercel + Railway** (hybrid approach):
   - Frontend on Vercel (free)
   - Backend on Railway (free)

---

## 💡 **Pro Tips**

1. **Always test locally first** with Docker
2. **Use Procfile instead of nixpacks.toml** for simpler deployments
3. **Check Railway logs** for specific error messages
4. **Start with backend only**, then add frontend
5. **Use Railway's Discord** for community support

---

## ✅ **Success Indicators**

Your deployment is working when:
- ✅ Backend returns 200 at `/health` endpoint
- ✅ Frontend loads without errors
- ✅ Frontend can communicate with backend
- ✅ Search functionality works end-to-end

---

## 🔗 **Useful Links**

- [Railway Docs](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Nixpacks Docs](https://nixpacks.com/)
- [Railway CLI Reference](https://docs.railway.app/develop/cli) 