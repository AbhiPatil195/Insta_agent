# Production Deployment Guide

This guide covers deploying Insta Agent to production on various platforms.

## Prerequisites Checklist

Before deploying, ensure you have:

- [ ] Meta App created with Instagram Graph API enabled
- [ ] Instagram Business Account connected to Facebook Page
- [ ] Long-lived Page Access Token generated
- [ ] Webhook callback URL (will be your production domain)
- [ ] Database provisioned (Neon, Supabase, or other PostgreSQL)
- [ ] LLM provider API key (Groq recommended)
- [ ] All environment variables configured
- [ ] Changed default dashboard password
- [ ] Updated privacy policy contact email

## Platform-Specific Guides

### Option 1: Railway (Recommended for Beginners)

Railway provides easy deployment with automatic HTTPS and environment management.

**Cost**: ~$5-10/month on Hobby plan

**Steps:**

1. **Create Railway Account**: [railway.app](https://railway.app)

2. **Create New Project**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Initialize in your project directory
   cd Insta_Agent
   railway init
   ```

3. **Add Services**:
   - Click "New Service" → Deploy from GitHub repo
   - Railway will auto-detect docker-compose.yml
   - Or add services individually:
     - Redis (from template)
     - PostgreSQL (from template) 
     - API (from Dockerfile.api)
     - Worker (from Dockerfile.worker)
     - Nginx (from docker-compose)

4. **Configure Environment Variables**:
   - Go to each service → Variables
   - Add all vars from `.env.example`
   - Railway provides `DATABASE_URL` and `REDIS_URL` automatically

5. **Get Public Domain**:
   - Nginx service → Settings → Generate Domain
   - Or add custom domain in Settings → Domains

6. **Configure Meta Webhook**:
   - Set webhook URL: `https://your-railway-domain.up.railway.app/webhook`
   - Verify token from your env vars

7. **Deploy**:
   ```bash
   railway up
   ```

**Tips:**
- Use Railway's built-in PostgreSQL (includes pgvector)
- Enable "Always On" to prevent cold starts
- Use environment groups for dev/prod configs

---

### Option 2: Render

Great free tier for getting started, automatic deployments from GitHub.

**Cost**: Free tier available, paid ~$7/month for production

**Steps:**

1. **Create Render Account**: [render.com](https://render.com)

2. **Create PostgreSQL Database**:
   - New → PostgreSQL
   - Choose Free or Starter plan
   - Copy the Internal Database URL

3. **Create Redis Instance**:
   - New → Redis
   - Choose Free or Starter plan
   - Copy the Internal Redis URL

4. **Create Web Services**:

   **API Service:**
   - New → Web Service
   - Connect your GitHub repo
   - Build Command: `docker build -f Dockerfile.api -t api .`
   - Start Command: Leave empty (uses Dockerfile CMD)
   - Instance Type: Free or Starter
   - Add all environment variables
   - Health Check Path: `/health`
   
   **Worker Service:**
   - New → Background Worker
   - Connect your GitHub repo
   - Build Command: `docker build -f Dockerfile.worker -t worker .`
   - Start Command: Leave empty
   - Add environment variables (same as API)
   
   **Nginx Service (Optional):**
   - New → Web Service
   - If needed, deploy nginx separately
   - Or use Render's native routing

5. **Get Public URL**:
   - API service will get: `https://your-app.onrender.com`
   - Configure in Meta webhook settings

6. **Run Database Migration**:
   - Connect to Render PostgreSQL using any client
   - Run `migrations/001_init.sql`

**Tips:**
- Free tier sleeps after 15 min inactivity (use paid for production)
- Use Render's native environment groups
- Enable auto-deploy from main branch

---

### Option 3: Fly.io

Best for Docker-native deployments, global edge deployment.

**Cost**: ~$5-15/month

**Steps:**

1. **Install Fly CLI**:
   ```bash
   # Mac/Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Login and Create App**:
   ```bash
   fly auth login
   fly launch --no-deploy
   ```

3. **Configure Services**:
   
   Create `fly.toml` for each service:
   
   **API (fly.api.toml):**
   ```toml
   app = "insta-agent-api"
   primary_region = "iad"
   
   [build]
   dockerfile = "Dockerfile.api"
   
   [http_service]
   internal_port = 8000
   force_https = true
   
   [[services]]
   http_checks = []
   internal_port = 8000
   protocol = "tcp"
   
   [[services.ports]]
   force_https = true
   handlers = ["http"]
   port = 80
   
   [[services.ports]]
   handlers = ["tls", "http"]
   port = 443
   ```
   
   **Worker:**
   ```toml
   app = "insta-agent-worker"
   primary_region = "iad"
   
   [build]
   dockerfile = "Dockerfile.worker"
   ```

4. **Provision Dependencies**:
   ```bash
   # Redis
   fly redis create
   
   # PostgreSQL (use Neon/Supabase instead - easier)
   # Or: fly postgres create
   ```

5. **Set Secrets**:
   ```bash
   fly secrets set META_APP_SECRET=xxx META_PAGE_ACCESS_TOKEN=yyy --app insta-agent-api
   fly secrets set META_APP_SECRET=xxx META_PAGE_ACCESS_TOKEN=yyy --app insta-agent-worker
   ```

6. **Deploy**:
   ```bash
   fly deploy --config fly.api.toml
   fly deploy --config fly.worker.toml
   ```

7. **Get Domain**:
   ```bash
   fly info --app insta-agent-api
   # Shows: https://insta-agent-api.fly.dev
   ```

**Tips:**
- Use Fly's global regions for low latency
- Scale horizontally: `fly scale count 2`
- View logs: `fly logs`

---

### Option 4: DigitalOcean App Platform

Simple, managed platform with good pricing.

**Cost**: ~$12/month for basic setup

**Steps:**

1. **Create DO Account**: [digitalocean.com](https://digitalocean.com)

2. **Create App**:
   - Apps → Create App
   - Connect GitHub repo
   - Select branch

3. **Configure Components**:
   - Auto-detects Dockerfiles
   - Add API, Worker components
   - Add managed Redis & PostgreSQL

4. **Set Environment Variables**:
   - Settings → Environment Variables
   - Add all from `.env.example`

5. **Deploy**:
   - Click "Deploy"
   - Get app URL: `https://your-app.ondigitalocean.app`

---

## Post-Deployment Steps

### 1. Verify Health
```bash
curl https://your-domain.com/health
# Should return: {"status":"healthy","service":"api"}

curl https://your-domain.com/health/detailed
# Check all dependencies
```

### 2. Configure Meta Webhook
1. Go to Meta Developer Dashboard
2. Products → Webhooks → Instagram
3. Edit Callback URL: `https://your-domain.com/webhook`
4. Verify Token: (from your META_VERIFY_TOKEN)
5. Subscribe to Fields: messages

### 3. Test Webhook Verification
```bash
# Meta will call this during verification
curl "https://your-domain.com/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"
# Should return: test123
```

### 4. Run Database Migration
```bash
# Connect to your Postgres database
psql YOUR_DATABASE_URL

# Run migration
\i migrations/001_init.sql
```

### 5. Test End-to-End
1. Send a DM to your Instagram Business account
2. Check logs for incoming webhook
3. Verify bot responds
4. Check dashboard: `https://your-domain.com/dash/`

### 6. Monitor Performance
- Set up log aggregation (Papertrail, Logtail)
- Configure uptime monitoring (UptimeRobot, Pingdom)
- Enable error tracking (Sentry)

---

## Environment Variables for Production

**Required:**
```bash
META_APP_SECRET=your_app_secret
META_PAGE_ACCESS_TOKEN=your_long_lived_token
META_VERIFY_TOKEN=your_verify_token
META_PAGE_ID=your_page_id
META_IG_BUSINESS_ID=your_ig_business_id  # Recommended
REDIS_URL=redis://...
POSTGRES_URL=postgresql://...
```

**Recommended:**
```bash
GROQ_API_KEY=your_groq_key
LLM_PROVIDER=groq
LOG_LEVEL=INFO
JSON_LOGS=true  # For structured logging
```

**Optional:**
```bash
KG_URI=neo4j+s://...  # Neo4j knowledge graph
TELEGRAM_BOT_TOKEN=...  # Human handoff
```

---

## SSL/HTTPS Setup

Most platforms provide automatic HTTPS. For custom domains:

### Using Let's Encrypt (if self-hosting)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

Update nginx config:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # ... rest of config
}
```

---

## Scaling Considerations

### Horizontal Scaling
- **Worker**: Scale to N instances for high message volume
- **API**: Scale based on webhook traffic
- **Redis**: Use managed Redis with persistence
- **Database**: Use read replicas for heavy loads

### Vertical Scaling
- Start with 512MB RAM per service
- Monitor CPU/memory usage
- Upgrade as needed

### Rate Limiting
Default nginx config: 10 req/s per IP for /webhook
Adjust in `nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=webhook_zone:10m rate=20r/s;
```

---

## Troubleshooting

### Webhook Not Receiving Messages
- Check Meta webhook subscription is active
- Verify callback URL is correct and accessible
- Check signature verification (META_APP_SECRET)
- Review API logs for errors

### Worker Not Processing
- Check Redis connectivity
- Verify worker is running: `docker ps` or platform logs
- Check environment variables are set
- Review worker logs for errors

### Database Connection Issues
- Verify POSTGRES_URL is correct
- Check database allows connections from your IPs
- Run migration if tables missing
- Check pgvector extension is enabled

### LLM Errors
- Verify GROQ_API_KEY is valid
- Check rate limits on Groq
- Review worker logs for LLM errors
- Fallback to basic replies if LLM fails

---

## Maintenance

### Update Dependencies
```bash
# Check for updates
pip list --outdated

# Update requirements files
pip install --upgrade package-name
pip freeze > api/requirements.txt
```

### Rotate Credentials
- Meta tokens: Refresh every 60 days
- Dashboard password: Every 90 days
- Database password: Annually or on breach

### Backup Database
```bash
# Automated backups (most platforms provide this)
# Manual backup:
pg_dump YOUR_DATABASE_URL > backup.sql
```

### Monitor Token Expiry
Set calendar reminders 30 days before token expiration.

---

## Security Hardening

- [ ] Enable HTTPS only (no HTTP)
- [ ] Restrict CORS origins (remove wildcard)
- [ ] Set proper rate limits on all endpoints
- [ ] Use strong dashboard password
- [ ] Enable webhook signature verification
- [ ] Regularly update dependencies
- [ ] Monitor access logs
- [ ] Set up security alerts
- [ ] Use secret managers (not .env files)
- [ ] Enable database SSL
- [ ] Restrict database to app IPs only

---

## Cost Optimization

- Use free tiers where available (Neon, Supabase, Groq)
- Start small, scale as needed
- Use spot/preemptible instances if available
- Set resource limits to prevent runaway costs
- Monitor usage regularly

**Estimated Monthly Costs:**
- Minimal setup (free tiers): $0-5
- Basic production: $10-20
- High volume: $50-100+

---

## Support

If you encounter issues:
1. Check logs first
2. Review documentation
3. Test with `/health/detailed` endpoint
4. Verify all environment variables
5. Check Meta Developer Dashboard for webhook status

For Meta-specific issues, see [Meta Developer Support](https://developers.facebook.com/support/).
