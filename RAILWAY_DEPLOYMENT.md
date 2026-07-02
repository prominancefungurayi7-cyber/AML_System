# Railway Deployment Guide

## Prerequisites
- Railway account (free tier available at https://railway.app)
- Git repository with your code

## Deployment Methods

### Method 1: Web Interface (Recommended - Easier)

#### Step 1: Push to GitHub
```bash
cd "c:\Users\PROMINENT\Desktop\AML System"
git init
git add .
git commit -m "Initial commit"
git branch -M main
# Create a new repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/aml-system.git
git push -u origin main
```

#### Step 2: Deploy via Railway Web
1. Go to https://railway.app and log in
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `aml-system` repository
4. Railway will automatically detect your Dockerfile
5. Click "Deploy"

#### Step 3: Configure Environment Variables
After deployment, in Railway dashboard:
1. Go to your project → Settings → Variables
2. Add these variables:
   - `SECRET_KEY`: Generate a strong random key (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `FLASK_ENV`: `production`
   - `DATABASE_URL`: `sqlite:////app/data/aml.db` (or use Railway PostgreSQL addon)
   - `PORT`: `5000`

#### Step 4: Add PostgreSQL (Recommended for Production)
1. In Railway dashboard, click "New Service"
2. Select "PostgreSQL"
3. Railway will provide a connection string
4. Update `DATABASE_URL` variable with the PostgreSQL connection string

### Method 2: Railway CLI

### 5. Configure Environment Variables
After deployment, set these environment variables in Railway dashboard:

**Required:**
- `SECRET_KEY` - Generate a strong random key
- `FLASK_ENV` - Set to `production`
- `DATABASE_URL` - Railway will automatically set this if using their PostgreSQL, or use: `sqlite:////app/data/aml.db`
- `PORT` - Railway automatically sets this

**Optional (for production):**
- `REDIS_URL` - If you want Redis caching
- `KAFKA_BOOTSTRAP_SERVERS` - If you want Kafka integration
- `SMTP_EMAIL` - For OTP emails
- `SMTP_PASSWORD` - For SMTP authentication

### 6. Access Your Application
After deployment, Railway will provide a public URL like:
`https://your-app-name.railway.app`

## Free Tier Limits
- $5/month free credit
- 512MB RAM
- Shared CPU
- 1GB storage (ephemeral - data resets on redeploy)

**Important:** SQLite database will be ephemeral on Railway. For production, consider:
1. Using Railway's PostgreSQL addon (free tier available)
2. Using Railway's volume for persistent storage

## Using Railway PostgreSQL (Recommended for Production)

1. Add PostgreSQL service in Railway dashboard
2. Set `DATABASE_URL` environment variable to Railway's PostgreSQL connection string
3. Update `.env.example` to use PostgreSQL format

## Monitoring
- Railway provides built-in logs and metrics
- Access logs via: `railway logs`
- Monitor health at: `https://your-app-name.railway.app/health`

## Troubleshooting
- If deployment fails, check: `railway logs`
- Ensure all dependencies are in requirements.txt
- Verify Dockerfile syntax
- Check environment variables are set correctly
