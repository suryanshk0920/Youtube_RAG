# TubeQuery - Hosting & Pricing Guide

Complete guide for hosting TubeQuery with cost analysis, free hosting options, and pricing strategy for the Indian market.

---

## Table of Contents
1. [Free Hosting Options (₹0/month)](#free-hosting-options)
2. [Paid Hosting Options](#paid-hosting-options)
3. [Cost Analysis](#cost-analysis)
4. [Pricing Strategy](#pricing-strategy)
5. [Revenue Projections](#revenue-projections)
6. [Deployment Guide](#deployment-guide)

---

## Free Hosting Options (₹0/month)

### ✅ RECOMMENDED: 100% Free Stack

This setup allows you to run TubeQuery completely free for the first 100-500 users!

#### **1. Frontend: Vercel (FREE)**
- **Plan**: Hobby (Free Forever)
- **Limits**: 
  - 100GB bandwidth/month
  - Unlimited deployments
  - Automatic HTTPS
  - Global CDN
- **Perfect for**: Next.js apps
- **Upgrade needed**: Only at 1000+ users
- **Link**: https://vercel.com

#### **2. Backend: Render (FREE)**
- **Plan**: Free Web Service
- **Limits**:
  - 512MB RAM
  - Spins down after 15 min inactivity
  - 750 hours/month (enough for 24/7)
  - Automatic HTTPS
- **Pros**: Easy Python deployment
- **Cons**: Cold starts (15-30 sec delay)
- **Link**: https://render.com

**Alternative: Railway (FREE)**
- **Plan**: Trial ($5 credit/month)
- **Limits**: 
  - 512MB RAM
  - $5 credit = ~500 hours
- **Pros**: No cold starts
- **Cons**: Credit expires monthly
- **Link**: https://railway.app

**Alternative: Fly.io (FREE)**
- **Plan**: Free tier
- **Limits**:
  - 3 shared-cpu VMs
  - 256MB RAM each
  - 160GB bandwidth
- **Pros**: No cold starts, global deployment
- **Link**: https://fly.io

#### **3. Database: Supabase (FREE)**
- **Plan**: Free tier
- **Limits**:
  - 500MB database
  - 2GB bandwidth
  - 50,000 monthly active users
  - Unlimited API requests
- **Perfect for**: PostgreSQL + Auth
- **Upgrade needed**: At 500MB data (~5000 users)
- **Link**: https://supabase.com

#### **4. Redis: Upstash (FREE)**
- **Plan**: Free tier
- **Limits**:
  - 10,000 commands/day
  - 256MB storage
  - Global replication
- **Perfect for**: Rate limiting, caching
- **Upgrade needed**: At 10k commands/day (~100 active users)
- **Link**: https://upstash.com

#### **5. Authentication: Firebase (FREE)**
- **Plan**: Spark (Free)
- **Limits**:
  - 50,000 monthly active users
  - Unlimited sign-ins
- **Perfect for**: User authentication
- **Link**: https://firebase.google.com

#### **6. Email: Resend (FREE)**
- **Plan**: Free tier
- **Limits**:
  - 3,000 emails/month
  - 100 emails/day
- **Perfect for**: Transactional emails
- **Upgrade needed**: At 3k emails/month
- **Link**: https://resend.com

**Alternative: SendGrid (FREE)**
- **Limits**: 100 emails/day (3,000/month)
- **Link**: https://sendgrid.com

#### **7. Domain: Free Options**

**Option A: Free Subdomain**
- `yourapp.vercel.app` (Vercel)
- `yourapp.onrender.com` (Render)
- `yourapp.fly.dev` (Fly.io)
- **Cost**: ₹0
- **Pros**: Instant, no setup
- **Cons**: Not professional

**Option B: Free .tk/.ml/.ga Domain**
- **Provider**: Freenom
- **Cost**: ₹0
- **Pros**: Custom domain
- **Cons**: Not professional, can be revoked
- **Link**: https://freenom.com

**Option C: Student Domain (if eligible)**
- **GitHub Student Pack**: Free .me domain for 1 year
- **Link**: https://education.github.com/pack

#### **8. SSL Certificate**
- **Let's Encrypt**: FREE (auto-configured by all platforms)

#### **9. Monitoring: Free Options**

**Sentry (Error Tracking)**
- **Free tier**: 5,000 errors/month
- **Link**: https://sentry.io

**PostHog (Analytics)**
- **Free tier**: 1M events/month
- **Link**: https://posthog.com

**Better Uptime (Monitoring)**
- **Free tier**: 1 monitor, 3-min checks
- **Link**: https://betteruptime.com

---

### 🎯 COMPLETE FREE STACK SUMMARY

| Service | Provider | Free Limit | Upgrade At |
|---------|----------|------------|------------|
| Frontend | Vercel | 100GB bandwidth | 1000+ users |
| Backend | Render | 750 hrs/month | 100+ concurrent |
| Database | Supabase | 500MB | 5000+ users |
| Redis | Upstash | 10k commands/day | 100+ active users |
| Auth | Firebase | 50k MAU | Never (generous) |
| Email | Resend | 3k emails/month | 100+ users |
| Domain | Vercel subdomain | Unlimited | When you want custom |
| SSL | Let's Encrypt | Unlimited | Never |
| Monitoring | Sentry + PostHog | 5k errors + 1M events | Scale phase |

**Total Monthly Cost: ₹0**
**Supports: 50-100 active users comfortably**

---

## Paid Hosting Options

### When to Upgrade?

Upgrade when you hit these limits:
- **100+ concurrent users** (backend needs more resources)
- **500MB database** (need Supabase Pro)
- **10k Redis commands/day** (need Upstash paid)
- **Cold starts affecting UX** (move from Render to Railway/Fly.io)

### Recommended Paid Stack (₹469/month)

#### **1. Backend: Railway Starter**
- **Cost**: $5/month (₹415)
- **Specs**: 512MB RAM, 1GB storage
- **Pros**: No cold starts, auto-scaling
- **Supports**: 100-200 users

#### **2. Domain: Cloudflare**
- **Cost**: ₹650/year (₹54/month)
- **Includes**: .com domain + free CDN
- **Pros**: Cheapest registrar, best DNS

#### **3. Everything Else: Still FREE**
- Vercel, Supabase, Upstash, Firebase, Resend

**Total: ₹469/month (~$5.65)**

---

### Growth Phase Stack (₹6,279/month)

For 100-500 users:

| Service | Plan | Cost |
|---------|------|------|
| Backend | Railway Pro | ₹1,660 ($20) |
| Frontend | Vercel Pro | ₹1,660 ($20) |
| Database | Supabase Pro | ₹2,075 ($25) |
| Redis | Upstash Paid | ₹830 ($10) |
| Email | Resend Paid | ₹1,660 ($20) |
| Domain | Cloudflare | ₹54/month |
| **TOTAL** | | **₹6,279/month** |

---

## Cost Analysis

### Per User Costs (Pro Plan)

#### **Variable Costs:**
- **LLM (OpenRouter)**: ₹52/month
  - 500 questions × 2500 tokens = 1.25M tokens
  - Cost: ~$0.625 = ₹52
- **YouTube API**: ₹0 (free tier)
- **Embeddings**: ₹0 (local model)

**Total Variable Cost: ₹52/user/month**

#### **Fixed Costs:**

**Free Tier (0-100 users):**
- Infrastructure: ₹0
- Domain: ₹54/month (optional)
- **Total: ₹54/month**

**Paid Tier (100-500 users):**
- Infrastructure: ₹6,279/month
- **Total: ₹6,279/month**

---

### Breakeven Analysis

#### **Scenario 1: Free Hosting**
- **Fixed costs**: ₹54/month (domain only)
- **Variable cost per user**: ₹52/month
- **Price**: ₹299/month
- **Profit per user**: ₹247/month

**Breakeven: 1 paying user** ✅

#### **Scenario 2: Paid Hosting (100 users)**
- **Fixed costs**: ₹6,279/month
- **Variable costs**: ₹5,200/month (100 × ₹52)
- **Total costs**: ₹11,479/month
- **Revenue**: ₹29,900/month (100 × ₹299)

**Profit: ₹18,421/month (62% margin)** ✅

#### **Scenario 3: Scale (500 users)**
- **Fixed costs**: ₹6,279/month
- **Variable costs**: ₹26,000/month (500 × ₹52)
- **Total costs**: ₹32,279/month
- **Revenue**: ₹1,49,500/month (500 × ₹299)

**Profit: ₹1,17,221/month (78% margin)** ✅

---

## Pricing Strategy

### Market Analysis (India)

**Competitors:**
- ChatGPT Plus: ₹1,650/month
- Claude Pro: ₹1,650/month
- Perplexity Pro: ₹1,650/month
- YouTube Premium: ₹149/month

**Our Positioning:** Affordable AI tool for YouTube content

---

### Recommended Pricing

#### **Free Plan**
- 3 videos/day
- 20 questions/day
- 7-day history
- Single videos only

#### **Pro Plan: ₹299/month**
- 50 videos/day
- 500 questions/day
- 1-year history
- Playlists & channels ✅
- Priority processing
- Export features

**Why ₹299?**
- 5.5x cheaper than ChatGPT Plus
- Under ₹300 psychological barrier
- 81% profit margin
- Sustainable for scaling

#### **Annual Plan: ₹2,999/year**
- Effective: ₹250/month
- Save ₹590 (20% discount)
- Better retention
- Upfront cash flow

#### **Lifetime Deal: ₹9,999** (Limited)
- One-time payment
- Lifetime access
- First 50 users only
- Creates urgency
- Covers ~41 months of costs

---

### Payment Gateway

#### **Razorpay (India)**
- **Transaction fee**: 2% per transaction
- **No setup/monthly fee**
- **Supports**: UPI, Cards, Netbanking, Wallets

**Example:**
- User pays ₹299
- Razorpay fee: ₹6 (2%)
- You receive: ₹293
- Your cost: ₹52 (LLM)
- **Net profit: ₹241 (81%)**

#### **Stripe (International)**
- **Transaction fee**: 2.9% + ₹2
- **For global expansion**

---

## Revenue Projections

### Conservative Estimates

#### **Month 1-3: Launch Phase**
- Free hosting (Render + Vercel)
- 10 paying users
- **Revenue**: ₹2,990/month
- **Costs**: ₹574/month (₹54 domain + ₹520 LLM)
- **Profit**: ₹2,416/month

#### **Month 4-6: Growth Phase**
- Still free hosting
- 50 paying users
- **Revenue**: ₹14,950/month
- **Costs**: ₹2,654/month (₹54 + ₹2,600 LLM)
- **Profit**: ₹12,296/month

#### **Month 7-12: Scale Phase**
- Upgrade to paid hosting
- 200 paying users
- **Revenue**: ₹59,800/month
- **Costs**: ₹16,679/month (₹6,279 infra + ₹10,400 LLM)
- **Profit**: ₹43,121/month

#### **Year 2: Established**
- 500 paying users
- **Revenue**: ₹1,49,500/month
- **Costs**: ₹32,279/month
- **Profit**: ₹1,17,221/month
- **Annual profit**: ₹14,06,652 (~$17,000)

---

### Aggressive Estimates (with marketing)

#### **Month 1-3:**
- 25 paying users
- **Profit**: ₹6,121/month

#### **Month 4-6:**
- 100 paying users
- **Profit**: ₹18,421/month

#### **Month 7-12:**
- 500 paying users
- **Profit**: ₹1,17,221/month

#### **Year 2:**
- 1,500 paying users
- **Revenue**: ₹4,48,500/month
- **Costs**: ₹1,03,279/month (₹25k infra + ₹78k LLM)
- **Profit**: ₹3,45,221/month
- **Annual profit**: ₹41,40,652 (~$50,000)

---

## Deployment Guide

### Phase 1: Free Hosting Setup (Week 1)

#### **Day 1-2: Frontend Deployment**

1. **Push code to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/tubequery-ui.git
git push -u origin main
```

2. **Deploy to Vercel**
- Go to https://vercel.com
- Click "Import Project"
- Connect GitHub
- Select `tubequery-ui` repo
- Configure:
  - Framework: Next.js
  - Root Directory: `tubequery-ui`
  - Environment Variables: Add from `.env.local`
- Deploy!

**Result**: `https://tubequery.vercel.app`

#### **Day 3-4: Backend Deployment**

1. **Create `render.yaml` in `tubequery/`**
```yaml
services:
  - type: web
    name: tubequery-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

2. **Deploy to Render**
- Go to https://render.com
- Click "New +"
- Select "Web Service"
- Connect GitHub
- Select `tubequery` repo
- Configure:
  - Root Directory: `tubequery`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
  - Add environment variables from `.env`
- Deploy!

**Result**: `https://tubequery-api.onrender.com`

#### **Day 5: Connect Frontend to Backend**

Update `tubequery-ui/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://tubequery-api.onrender.com
```

Redeploy frontend on Vercel (automatic on git push).

#### **Day 6-7: Testing**

- Test video ingestion
- Test chat functionality
- Test authentication
- Test limits
- Monitor Render logs for cold starts

---

### Phase 2: Custom Domain (Optional)

#### **Option A: Free Subdomain**
Use `tubequery.vercel.app` - works perfectly!

#### **Option B: Buy Domain (₹650/year)**

1. **Buy from Cloudflare**
- Go to https://cloudflare.com
- Search for domain (e.g., `tubequery.com`)
- Purchase (₹650/year)

2. **Configure Vercel**
- Go to Vercel project settings
- Add custom domain: `tubequery.com`
- Follow DNS instructions
- Add CNAME: `cname.vercel-dns.com`

3. **Configure Render**
- Go to Render service settings
- Add custom domain: `api.tubequery.com`
- Follow DNS instructions

**Result**: 
- Frontend: `https://tubequery.com`
- Backend: `https://api.tubequery.com`

---

### Phase 3: Upgrade to Paid (When Needed)

#### **When to Upgrade:**
- Cold starts affecting UX (>5 sec delays)
- Hitting Render's 750 hour limit
- 100+ concurrent users
- Need better performance

#### **Migration to Railway:**

1. **Create Railway account**
- Go to https://railway.app
- Connect GitHub

2. **Deploy backend**
- New Project → Deploy from GitHub
- Select `tubequery` repo
- Add environment variables
- Deploy!

3. **Update frontend**
- Change `NEXT_PUBLIC_API_URL` to Railway URL
- Redeploy

**Cost**: $5/month (₹415)
**Benefit**: No cold starts, better performance

---

## Monitoring & Maintenance

### Free Monitoring Tools

#### **1. Sentry (Error Tracking)**
```bash
# Install
pip install sentry-sdk
npm install @sentry/nextjs
```

Configure in code:
```python
import sentry_sdk
sentry_sdk.init(dsn="your-dsn")
```

#### **2. PostHog (Analytics)**
```bash
npm install posthog-js
```

Track events:
```typescript
posthog.capture('video_added')
posthog.capture('question_asked')
```

#### **3. Better Uptime (Uptime Monitoring)**
- Add your URLs
- Get alerts on downtime
- Free for 1 monitor

---

## Cost Optimization Tips

### 1. **Start 100% Free**
- Use Render (free tier) for first 100 users
- Accept cold starts initially
- Upgrade only when revenue justifies it

### 2. **Optimize LLM Costs**
- Use `openrouter/auto` (cheapest model)
- Cache common responses
- Limit context window size
- Consider Gemini Flash (cheaper)

### 3. **Optimize Database**
- Clean up old chat sessions (>7 days for free users)
- Archive old data
- Use database indexes

### 4. **Optimize Redis**
- Set TTL on all keys
- Clean up expired data
- Use Redis only for hot data

### 5. **Optimize Bandwidth**
- Enable Vercel image optimization
- Use CDN for static assets
- Compress API responses

---

## Recommended Launch Strategy

### **Week 1-4: MVP on Free Tier**
- Deploy on Render + Vercel (₹0)
- Use free subdomain
- Get first 10 users
- Validate product-market fit
- **Cost**: ₹0

### **Week 5-8: Add Custom Domain**
- Buy domain (₹650/year)
- Professional branding
- Start marketing
- Get to 50 users
- **Cost**: ₹54/month

### **Week 9-12: Upgrade Backend**
- Move to Railway (₹415/month)
- Better performance
- Scale to 200 users
- **Cost**: ₹469/month

### **Month 4+: Scale**
- Upgrade services as needed
- Optimize costs
- Reinvest profits
- **Cost**: Variable based on growth

---

## Conclusion

### **Start Free, Scale Smart**

1. **Launch Phase (0-100 users)**: 100% free hosting
2. **Growth Phase (100-500 users)**: ₹469/month
3. **Scale Phase (500+ users)**: ₹6,279/month

### **Key Takeaways:**

✅ You can launch with **₹0 monthly cost**
✅ Breakeven at just **1 paying user**
✅ 81% profit margin at scale
✅ Sustainable and scalable business model

### **Next Steps:**

1. Deploy on free tier (Render + Vercel)
2. Get first 10 users
3. Validate pricing (₹299/month)
4. Upgrade infrastructure as you grow
5. Reinvest profits into marketing

**Total investment to start: ₹0**
**Time to launch: 1 week**
**Breakeven: 1 user**

---

## Support & Resources

- **Vercel Docs**: https://vercel.com/docs
- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Railway Docs**: https://docs.railway.app
- **Razorpay Docs**: https://razorpay.com/docs

---

*Last Updated: April 2026*
*For questions: [Your Email]*
