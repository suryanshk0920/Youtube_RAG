# TubeQuery Deployment Guide

Step-by-step guide to deploy TubeQuery on free hosting platforms.

---

## Option 1: Fly.io (Recommended - No Cold Starts)

### Prerequisites
- GitHub account
- Fly.io account (sign up at https://fly.io)
- `flyctl` CLI installed

### Step 1: Install Fly.io CLI

**Windows:**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**Mac/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

### Step 2: Login to Fly.io

```bash
fly auth login
```

### Step 3: Deploy Backend

```bash
# Navigate to backend folder
cd tubequery

# Launch app (first time)
fly launch --name tubequery-api --region bom

# When prompted:
# - Would you like to copy its configuration? → Yes
# - Would you like to set up a PostgreSQL database? → No (we use Supabase)
# - Would you like to set up an Upstash Redis database? → No (we have Upstash)
# - Would you like to deploy now? → No (set secrets first)
```

### Step 4: Set Environment Variables

```bash
# Set all your environment variables
fly secrets set GEMINI_API_KEY="your-key"
fly secrets set YOUTUBE_API_KEY="your-key"
fly secrets set OPENROUTER_API_KEY="your-key"
fly secrets set SUPABASE_URL="your-url"
fly secrets set SUPABASE_SERVICE_ROLE_KEY="your-key"
fly secrets set DATABASE_URL="your-database-url"
fly secrets set UPSTASH_REDIS_URL="your-redis-url"
fly secrets set UPSTASH_REDIS_TOKEN="your-token"
fly secrets set UPSTASH_REDIS_REST_URL="your-rest-url"
fly secrets set FIREBASE_SERVICE_ACCOUNT='{"type":"service_account",...}'
```

### Step 5: Deploy

```bash
fly deploy
```

### Step 6: Check Status

```bash
# Check if app is running
fly status

# View logs
fly logs

# Open in browser
fly open
```

Your backend will be available at: `https://tubequery-api.fly.dev`

### Step 7: Deploy Frontend to Vercel

```bash
# Navigate to frontend folder
cd ../tubequery-ui

# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# When prompted:
# - Set up and deploy? → Yes
# - Which scope? → Your account
# - Link to existing project? → No
# - Project name? → tubequery
# - Directory? → ./
# - Override settings? → No
```

### Step 8: Set Frontend Environment Variables

In Vercel dashboard:
1. Go to Project Settings → Environment Variables
2. Add:
   - `NEXT_PUBLIC_API_URL` = `https://tubequery-api.fly.dev`
   - `NEXT_PUBLIC_FIREBASE_API_KEY` = your Firebase API key
   - `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` = your auth domain
   - etc.

3. Redeploy: `vercel --prod`

Your frontend will be available at: `https://tubequery.vercel.app`

---

## Option 2: Render (Easiest - Has Cold Starts)

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy Backend on Render

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: tubequery-api
   - **Region**: Singapore (closest to India)
   - **Branch**: main
   - **Root Directory**: `tubequery`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

5. Add Environment Variables (click "Advanced"):
   - Add all variables from your `.env` file
   - Don't include `PORT` (Render sets this automatically)

6. Click "Create Web Service"

Wait 5-10 minutes for deployment.

Your backend will be at: `https://tubequery-api.onrender.com`

### Step 3: Deploy Frontend on Vercel

Same as Fly.io Step 7-8 above, but use Render URL:
- `NEXT_PUBLIC_API_URL` = `https://tubequery-api.onrender.com`

---

## Option 3: Railway (Best Performance - $5/month)

### Step 1: Install Railway CLI

```bash
npm i -g @railway/cli
```

### Step 2: Login

```bash
railway login
```

### Step 3: Deploy Backend

```bash
cd tubequery

# Initialize project
railway init

# Link to new project
railway link

# Add environment variables
railway variables set GEMINI_API_KEY="your-key"
railway variables set YOUTUBE_API_KEY="your-key"
# ... add all variables

# Deploy
railway up
```

### Step 4: Get Backend URL

```bash
railway domain
```

### Step 5: Deploy Frontend

Same as previous options, use Railway URL for `NEXT_PUBLIC_API_URL`.

---

## Troubleshooting

### Backend Issues

**Problem: "Module not found" error**
```bash
# Make sure requirements.txt is complete
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

**Problem: "Port already in use"**
- Fly.io/Render/Railway set PORT automatically
- Make sure your code uses: `port = int(os.getenv("PORT", 8000))`

**Problem: Database connection fails**
- Check DATABASE_URL format: `postgresql://user:pass@host:5432/db`
- Ensure Supabase allows connections from your hosting IP
- Check if connection pooling is enabled

**Problem: Cold starts on Render**
- This is normal for free tier
- First request takes 15-30 seconds
- Subsequent requests are fast
- Upgrade to paid tier ($7/month) to eliminate cold starts

### Frontend Issues

**Problem: "API request failed"**
- Check `NEXT_PUBLIC_API_URL` is correct
- Ensure backend is running: visit `https://your-api-url/health`
- Check CORS settings in backend

**Problem: "Firebase auth not working"**
- Verify all Firebase environment variables are set
- Check Firebase console for authorized domains
- Add your Vercel domain to Firebase authorized domains

**Problem: Build fails**
```bash
# Clear cache and rebuild
vercel --force
```

---

## Monitoring

### Check Backend Health

```bash
# Fly.io
fly logs
fly status

# Render
# View logs in dashboard

# Railway
railway logs
```

### Check Frontend

```bash
# Vercel
vercel logs
```

### Set Up Alerts

**Fly.io:**
```bash
fly monitor
```

**Render:**
- Dashboard → Settings → Notifications

**Vercel:**
- Dashboard → Settings → Notifications

---

## Scaling

### When to Upgrade?

**Free Tier Limits:**
- Fly.io: 3 VMs, 256MB RAM each
- Render: 750 hours/month, cold starts
- Railway: $5 credit/month
- Vercel: 100GB bandwidth

**Upgrade When:**
- Cold starts affecting UX (Render)
- Hitting bandwidth limits (Vercel)
- Need more RAM/CPU (all platforms)
- 100+ concurrent users

### Upgrade Costs

**Fly.io:**
- Shared CPU: $1.94/month per 256MB
- Dedicated CPU: $62/month per 1GB

**Render:**
- Starter: $7/month (no cold starts)
- Standard: $25/month (more resources)

**Railway:**
- Pay as you go: ~$5-20/month
- Pro: $20/month (more resources)

**Vercel:**
- Pro: $20/month (1TB bandwidth)

---

## Custom Domain Setup

### Step 1: Buy Domain

**Recommended: Cloudflare**
- Cheapest registrar
- Free CDN and DDoS protection
- Best DNS performance

**Cost:** ₹650/year for .com

### Step 2: Configure Backend Domain

**Fly.io:**
```bash
fly certs add api.yourdomain.com
```

**Render:**
1. Dashboard → Settings → Custom Domain
2. Add: `api.yourdomain.com`
3. Add CNAME record in Cloudflare

**Railway:**
1. Dashboard → Settings → Domains
2. Add custom domain
3. Add CNAME record

### Step 3: Configure Frontend Domain

**Vercel:**
1. Dashboard → Settings → Domains
2. Add: `yourdomain.com` and `www.yourdomain.com`
3. Add DNS records in Cloudflare:
   - A record: `76.76.21.21`
   - CNAME: `cname.vercel-dns.com`

### Step 4: Update Environment Variables

Update `NEXT_PUBLIC_API_URL` to your custom domain:
```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://api.yourdomain.com
```

Redeploy:
```bash
vercel --prod
```

---

## Cost Summary

### Free Tier (0-100 users)
- Backend: Fly.io/Render (FREE)
- Frontend: Vercel (FREE)
- Database: Supabase (FREE)
- Redis: Upstash (FREE)
- **Total: ₹0/month**

### With Custom Domain (0-100 users)
- Domain: Cloudflare (₹650/year)
- Everything else: FREE
- **Total: ₹54/month**

### Paid Tier (100-500 users)
- Backend: Railway ($20/month)
- Frontend: Vercel (FREE or $20/month)
- Database: Supabase Pro ($25/month)
- Redis: Upstash Paid ($10/month)
- Domain: ₹54/month
- **Total: ₹6,279/month**

---

## Quick Start Commands

### Deploy Everything (First Time)

```bash
# 1. Deploy backend to Fly.io
cd tubequery
fly launch --name tubequery-api --region bom
fly secrets set GEMINI_API_KEY="..." # Set all secrets
fly deploy

# 2. Deploy frontend to Vercel
cd ../tubequery-ui
vercel
# Set environment variables in dashboard
vercel --prod

# Done! Your app is live.
```

### Update Deployment

```bash
# Update backend
cd tubequery
fly deploy

# Update frontend
cd ../tubequery-ui
git push origin main  # Auto-deploys on Vercel
```

---

## Support

**Fly.io:**
- Docs: https://fly.io/docs
- Community: https://community.fly.io

**Render:**
- Docs: https://render.com/docs
- Support: support@render.com

**Vercel:**
- Docs: https://vercel.com/docs
- Support: https://vercel.com/support

**Railway:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

---

*Last Updated: April 2026*
