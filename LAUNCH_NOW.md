# 🚀 LAUNCH NOW - Quick Start Guide

This is your streamlined launch guide. Follow these steps in order.

## Phase 1: Local Setup (15 minutes)

### Step 1: Secure Dashboard (5 min)

```bash
# Change dashboard password
pip install passlib
python scripts/update_dashboard_password.py
```

**Save the password somewhere safe!**

### Step 2: Get Free Database (5 min)

**Option: Neon (Recommended - Easiest)**

1. Go to [neon.tech](https://neon.tech)
2. Sign up (no credit card needed)
3. Click "Create a project"
4. Copy the connection string
5. Add to your `.env`:
   ```bash
   POSTGRES_URL=postgresql://user:pass@host/neondb?sslmode=require
   ```

### Step 3: Run Database Migration (2 min)

```bash
# Install psql if needed (Windows users: download from postgresql.org)
psql "YOUR_POSTGRES_URL" -f migrations/001_init.sql
```

Or use Neon's SQL Editor in their dashboard.

### Step 4: Get Free LLM API Key (3 min)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free tier available)
3. Create API key
4. Add to `.env`:
   ```bash
   GROQ_API_KEY=gsk_xxxxxxxxxxxxx
   LLM_PROVIDER=groq
   ```

---

## Phase 2: Deploy to Railway (20 minutes)

**Why Railway?** Easiest deployment, free $5 credit, automatic HTTPS.

### Step 1: Create Railway Account (2 min)

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub

### Step 2: Install Railway CLI (2 min)

```bash
# Windows (PowerShell as Admin)
iwr https://railway.app/install.ps1 | iex

# After install, login
railway login
```

### Step 3: Push to GitHub (3 min)

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial production-ready commit"

# Create repo on GitHub and push
git remote add origin https://github.com/YOUR_USERNAME/insta-agent.git
git branch -M main
git push -u origin main
```

### Step 4: Deploy to Railway (10 min)

```bash
# In your project directory
cd e:\Coding\Agents\Insta_Agent
railway init
```

Then in Railway dashboard:
1. Click your project
2. **Add Redis**: New → Database → Redis
3. **Add API Service**: New → GitHub Repo → Select your repo → Select `Dockerfile.api`
4. **Add Worker Service**: New → GitHub Repo → Select your repo → Select `Dockerfile.worker`
5. **Add Nginx Service**: New → GitHub Repo → Select your repo → Select `docker-compose.yml` → Select nginx

### Step 5: Set Environment Variables (3 min)

For **API** and **Worker** services:

```bash
# Or do it in Railway dashboard UI (easier)
# Go to each service → Variables → Raw Editor → Paste:

META_APP_ID=1164637005628982
META_APP_SECRET=YOUR_NEW_SECRET_HERE
META_VERIFY_TOKEN=dev-verify-token-6bfe3c7a
META_PAGE_ID=897790356742040
META_IG_BUSINESS_ID=
META_PAGE_ACCESS_TOKEN=YOUR_NEW_TOKEN_HERE
META_GRAPH_VERSION=24.0
BRAND_PERSONA="Friendly, helpful, concise, emoji-friendly"
LANGS_SUPPORTED="en,hi,mr"
REDIS_URL=${{Redis.REDIS_URL}}
POSTGRES_URL=YOUR_NEON_URL_HERE
GROQ_API_KEY=YOUR_GROQ_KEY_HERE
GROQ_MODEL=llama-3.1-8b-instant
LLM_PROVIDER=groq
LOG_LEVEL=INFO
JSON_LOGS=true
```

**Note:** `${{Redis.REDIS_URL}}` is auto-filled by Railway

### Step 6: Get Your Domain (1 min)

1. Go to **Nginx** service → Settings → Networking
2. Click "Generate Domain"
3. You'll get: `https://your-app.up.railway.app`

**This is your webhook URL!**

---

## Phase 3: Configure Meta Webhook (10 minutes)

### Step 1: Generate New Tokens (SECURITY!) (5 min)

⚠️ **IMPORTANT:** Your current tokens in `.env` should be rotated.

1. Go to [Meta Developer Console](https://developers.facebook.com/apps)
2. Select your app
3. **Regenerate App Secret**:
   - Settings → Basic → App Secret → Reset
   - Save the new secret
4. **Generate New Page Access Token**:
   - Use [Graph API Explorer](https://developers.facebook.com/tools/explorer)
   - Select your app
   - Get Token → Page Access Token
   - Select your page
   - Exchange for long-lived token (see SECURITY.md)

### Step 2: Update Railway Variables (2 min)

Update these in Railway dashboard:
- `META_APP_SECRET` = new secret
- `META_PAGE_ACCESS_TOKEN` = new token

### Step 3: Configure Webhook (3 min)

1. Meta Dashboard → Your App → Webhooks → Instagram
2. Click "Edit" on callback URL
3. Set: `https://your-app.up.railway.app/webhook`
4. Verify Token: `dev-verify-token-6bfe3c7a` (or whatever you set)
5. Click "Verify and Save"
6. Subscribe to "messages" field

---

## Phase 4: Test & Launch! (10 minutes)

### Test 1: Health Check

```bash
curl https://your-app.up.railway.app/health/detailed
```

Should show all services healthy.

### Test 2: Privacy Pages

Visit in browser:
- `https://your-app.up.railway.app/privacy`
- `https://your-app.up.railway.app/data-deletion`

Should load properly.

### Test 3: Send Test Message

1. Open Instagram
2. Send DM to your business account: "Hello"
3. Check Railway logs: `railway logs`
4. Bot should respond!

### Test 4: Dashboard

1. Visit: `https://your-app.up.railway.app/dash/`
2. Login with your new credentials
3. Should show analytics

### Test 5: Data Deletion

1. Send DM: "DELETE MY DATA"
2. Should get confirmation

---

## ✅ You're Live!

Your bot is now running in production! 🎉

## Post-Launch Monitoring (First 24 hours)

### Check Logs
```bash
railway logs --service api
railway logs --service worker
```

### Monitor Uptime
Set up [UptimeRobot](https://uptimerobot.com) (free):
1. Create account
2. Add monitor: `https://your-app.up.railway.app/health`
3. Get email alerts if down

### Check Dashboard
Visit `/dash/` regularly to see:
- Message counts
- Response times
- Intent breakdown
- Any errors

---

## Quick Troubleshooting

**Webhook not working?**
```bash
# Test webhook verification
curl "https://your-app.up.railway.app/webhook?hub.mode=subscribe&hub.verify_token=dev-verify-token-6bfe3c7a&hub.challenge=test123"
# Should return: test123
```

**Worker not responding?**
```bash
# Check worker logs
railway logs --service worker

# Check Redis connection
railway logs --service redis
```

**Database errors?**
```bash
# Test connection
psql "$POSTGRES_URL" -c "SELECT 1;"

# Check tables exist
psql "$POSTGRES_URL" -c "\dt"
```

---

## Alternative: Quick Deploy to Render (if Railway has issues)

1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repo
4. Select Dockerfile.api
5. Add environment variables
6. Deploy!

Same process for worker (as Background Worker).

---

## Cost Estimate

With current setup:
- Railway: $5 free credit (lasts ~1 month)
- Neon: Free tier (sufficient for development)
- Groq: Free tier (good for testing)

**Total: $0 for first month, then ~$5-10/month**

---

## Next Steps After Launch

1. **Submit for App Review** (if you need permissions)
   - Follow `docs/APP_REVIEW.md`
   - Record screencast
   - Submit to Meta

2. **Add More Features**
   - Ingest FAQs: `python -m tools.ingest_faq`
   - Add custom intents
   - Improve responses

3. **Scale as Needed**
   - Monitor usage in dashboard
   - Upgrade Railway plan if needed
   - Add more workers if high volume

---

## Emergency Contacts

- **Railway Support**: [railway.app/discord](https://railway.app/discord)
- **Meta Support**: [developers.facebook.com/support](https://developers.facebook.com/support)
- **Neon Support**: [neon.tech/docs](https://neon.tech/docs)

---

## 🎉 Congratulations!

Your Instagram AI Agent is now live and handling messages!

Share your success:
- Test with friends
- Monitor performance
- Iterate and improve

**You did it!** 🚀
