# Production Deployment Guide

This guide covers deploying TubeQuery to production with proper Firebase authentication setup.

## Table of Contents
1. [Firebase Service Account Setup](#firebase-service-account-setup)
2. [Backend Deployment (Render)](#backend-deployment-render)
3. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
4. [Testing the Deployment](#testing-the-deployment)
5. [Troubleshooting](#troubleshooting)

---

## Firebase Service Account Setup

### Why Firebase Authentication is Required

TubeQuery uses Firebase Authentication for:
- User authentication and session management
- JWT token verification on every API request
- Secure user identification across frontend and backend

**This is NOT optional** - the application will not work without proper Firebase configuration.

### Getting Your Firebase Service Account

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (or create one)
3. Go to **Project Settings** (gear icon) → **Service Accounts**
4. Click **Generate New Private Key**
5. Download the JSON file - this is your `firebase-service-account.json`

### Important Security Notes

⚠️ **NEVER commit the service account JSON to Git!**
- The `.gitignore` already excludes `firebase-service-account.json`
- This file contains private keys that grant admin access to your Firebase project
- If accidentally committed, immediately revoke the key and generate a new one

---

## Backend Deployment (Render)

### Step 1: Push Code to GitHub

```bash
git add .
git commit -m "Production deployment setup"
git push origin main
```

### Step 2: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `tubequery-backend` (or your choice)
   - **Region**: Choose closest to your users (e.g., Singapore for India)
   - **Branch**: `main`
   - **Root Directory**: `tubequery`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python startup.py`

### Step 3: Configure Environment Variables

Add these environment variables in Render dashboard:

#### Required Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Redis (Upstash)
REDIS_URL=your-upstash-redis-url

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# YouTube API
YOUTUBE_API_KEY=your-youtube-api-key

# Firebase - METHOD 1 (Recommended)
FIREBASE_SERVICE_ACCOUNT_PATH=/etc/secrets/firebase-service-account.json
```

#### Firebase Configuration - Choose ONE Method

**Method 1: Secret Files (Recommended for Render)**

1. In Render dashboard, go to your service
2. Navigate to **Environment** → **Secret Files**
3. Click **Add Secret File**
4. Set **Filename**: `firebase-service-account.json`
5. Set **Contents**: Paste the entire contents of your Firebase service account JSON
6. Render will mount this at `/etc/secrets/firebase-service-account.json`
7. Set environment variable: `FIREBASE_SERVICE_ACCOUNT_PATH=/etc/secrets/firebase-service-account.json`

**Method 2: Environment Variable (Alternative)**

If Secret Files don't work, you can try passing the JSON as a string:
1. Open your `firebase-service-account.json`
2. Minify it to a single line (remove all newlines and extra spaces)
3. Set environment variable: `FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}`

⚠️ **Note**: Method 2 often fails due to newlines in the private key. Use Method 1 if possible.

**Method 3: Commit to Private Repo (Last Resort)**

If your repository is **private**, you can commit the file:
1. Ensure repo is private on GitHub
2. Place `firebase-service-account.json` in `tubequery/` directory
3. The app will auto-detect it (no env var needed)
4. **NEVER do this with a public repo!**

### Step 4: Deploy

1. Click **Create Web Service**
2. Render will automatically deploy
3. Wait for build to complete (5-10 minutes)
4. Check logs for: `Firebase Admin SDK initialised from file`
5. Your backend URL: `https://your-service.onrender.com`

### Step 5: Verify Backend is Running

Test the health endpoint:
```bash
curl https://your-service.onrender.com/health
```

Should return: `{"status":"ok"}`

---

## Frontend Deployment (Vercel)

### Step 1: Prepare Environment Variables

Create a `.env.production` file locally (don't commit it):

```bash
# Backend API
NEXT_PUBLIC_API_URL=https://your-service.onrender.com

# Firebase Client Config (from Firebase Console → Project Settings → General)
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
```

### Step 2: Deploy to Vercel

#### Option A: Vercel CLI (Recommended)

```bash
cd tubequery-ui
npm install -g vercel
vercel login
vercel --prod
```

When prompted:
- **Set up and deploy**: Yes
- **Which scope**: Your account
- **Link to existing project**: No
- **Project name**: `tubequery`
- **Directory**: `./` (current directory)
- **Override settings**: No

#### Option B: Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `tubequery-ui`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Step 3: Add Environment Variables in Vercel

1. Go to your project in Vercel dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add all variables from `.env.production` above
4. Make sure to select **Production** environment
5. Click **Save**

### Step 4: Redeploy

If you added env vars after initial deployment:
1. Go to **Deployments** tab
2. Click **...** on latest deployment
3. Click **Redeploy**

Your frontend URL: `https://your-project.vercel.app`

---

## Testing the Deployment

### 1. Test Backend Health

```bash
curl https://your-backend.onrender.com/health
```

Expected: `{"status":"ok"}`

### 2. Test Firebase Authentication

1. Open your frontend URL
2. Click **Sign In**
3. Sign in with Google/Email
4. Check browser console for errors
5. Try adding a video

### 3. Test Full Flow

1. Sign in to the app
2. Add a YouTube video URL
3. Wait for processing
4. Ask a question about the video
5. Verify you get a response with citations

### 4. Check Logs

**Backend logs (Render):**
- Go to Render dashboard → Your service → Logs
- Look for: `Firebase Admin SDK initialised from file`
- Check for any errors

**Frontend logs (Vercel):**
- Go to Vercel dashboard → Your project → Deployments → View Function Logs
- Check for any errors

---

## Troubleshooting

### Backend Issues

#### Error: "FIREBASE_SERVICE_ACCOUNT_PATH is set but file not found"

**Solution**: 
- Verify Secret File is created in Render dashboard
- Check the path matches: `/etc/secrets/firebase-service-account.json`
- Redeploy the service

#### Error: "Invalid FIREBASE_SERVICE_ACCOUNT JSON"

**Solution**:
- Don't use environment variable method for JSON with newlines
- Use Secret Files method instead
- Or minify the JSON to a single line (not recommended)

#### Error: "Token verification failed"

**Solution**:
- Verify Firebase project ID matches between frontend and backend
- Check that service account has correct permissions
- Regenerate service account key if needed

### Frontend Issues

#### Error: "Failed to fetch" or "Network Error"

**Solution**:
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend is running: `curl https://your-backend.onrender.com/health`
- Check CORS settings in backend (should allow your Vercel domain)

#### Error: "Firebase: Error (auth/invalid-api-key)"

**Solution**:
- Verify all Firebase client config variables are set in Vercel
- Check for typos in environment variable names
- Ensure variables start with `NEXT_PUBLIC_`

#### 404 Error on Vercel

**Solution**:
- Verify Root Directory is set to `tubequery-ui`
- Check Build Command is `npm run build`
- Ensure `package.json` exists in `tubequery-ui/`

### Performance Issues

#### Backend Cold Starts (Render Free Tier)

**Issue**: First request after 15 minutes takes 30-60 seconds

**Solutions**:
- Upgrade to paid plan ($7/month) for always-on instances
- Use a cron job to ping your backend every 10 minutes
- Accept cold starts for free tier

#### Rate Limiting

**Issue**: Users hitting rate limits

**Solution**:
- Check Redis connection is working
- Adjust rate limits in `tubequery/middleware/redis_rate_limit.py`
- Monitor usage in Upstash dashboard

---

## Production Checklist

Before going live:

- [ ] Firebase service account configured correctly
- [ ] All environment variables set in Render
- [ ] All environment variables set in Vercel
- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] User can sign in successfully
- [ ] Video ingestion works
- [ ] Chat functionality works
- [ ] Rate limiting is working
- [ ] Error messages are user-friendly
- [ ] Logs are being captured
- [ ] Domain configured (optional)
- [ ] SSL/HTTPS enabled (automatic on Render/Vercel)

---

## Monitoring

### Backend Monitoring (Render)

- Check logs regularly for errors
- Monitor response times in Render dashboard
- Set up alerts for downtime

### Frontend Monitoring (Vercel)

- Check deployment logs for build errors
- Monitor function execution times
- Use Vercel Analytics (optional)

### Database Monitoring (Supabase)

- Monitor database size
- Check query performance
- Review API usage

### Redis Monitoring (Upstash)

- Check connection count
- Monitor memory usage
- Review command statistics

---

## Scaling Considerations

### When to Upgrade

**Backend (Render)**:
- Free tier: Good for 0-100 users
- Starter ($7/month): Good for 100-1000 users
- Standard ($25/month): Good for 1000+ users

**Database (Supabase)**:
- Free tier: 500MB database, 2GB bandwidth
- Pro ($25/month): 8GB database, 50GB bandwidth

**Redis (Upstash)**:
- Free tier: 10,000 commands/day
- Pay-as-you-go: $0.2 per 100K commands

### Cost Optimization

1. **Start with 100% free tier** (as per pricing guide)
2. **Monitor usage** closely
3. **Upgrade components** as needed based on bottlenecks
4. **Expected costs** at scale:
   - 100 users: ~₹500/month ($7 Render)
   - 1000 users: ~₹2000/month ($25 Render + $25 Supabase)
   - 10000 users: ~₹10000/month (multiple instances + CDN)

---

## Support

If you encounter issues:

1. Check logs in Render/Vercel dashboards
2. Review this guide's troubleshooting section
3. Check Firebase Console for auth errors
4. Verify all environment variables are set correctly
5. Test each component individually (backend health, frontend load, auth flow)

---

## Security Best Practices

1. **Never commit secrets** to Git
2. **Use environment variables** for all sensitive data
3. **Rotate keys regularly** (every 90 days)
4. **Monitor for suspicious activity** in Firebase Console
5. **Keep dependencies updated** (`npm audit`, `pip check`)
6. **Use HTTPS only** (automatic on Render/Vercel)
7. **Implement rate limiting** (already configured)
8. **Validate all user inputs** (already implemented)

---

## Next Steps

After successful deployment:

1. **Set up custom domain** (optional)
2. **Configure email templates** in Firebase
3. **Set up monitoring alerts**
4. **Create backup strategy** for database
5. **Document API endpoints** for future reference
6. **Set up CI/CD pipeline** for automated deployments
7. **Implement analytics** to track usage
8. **Create user documentation**

---

**Deployment Status**: ✅ Ready for Production

**Last Updated**: April 19, 2026
