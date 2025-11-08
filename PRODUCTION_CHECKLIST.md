# Production Launch Checklist

Complete this checklist before launching Insta Agent to production.

## 🔐 Security (CRITICAL)

- [ ] **Remove committed credentials**: Ensure `.env` is in `.gitignore` and never committed
- [ ] **Rotate exposed secrets**: If any credentials were committed, rotate them immediately
- [ ] **Change dashboard password**: Replace default `admin`/`password` in `nginx/.htpasswd`
  ```bash
  python scripts/update_dashboard_password.py
  ```
- [ ] **Update IP allowlist**: Edit `nginx/allow_dash.conf/allow_dash.conf` with production IPs
- [ ] **Enable webhook signature**: Set `META_APP_SECRET` for HMAC verification
- [ ] **HTTPS only**: Ensure production runs on HTTPS (required for Meta webhooks)
- [ ] **Restrict CORS**: Update `api/app/main.py` - remove `allow_origins=["*"]`
- [ ] **Database SSL**: Ensure `?sslmode=require` in `POSTGRES_URL`
- [ ] **Review privacy policy**: Update contact email in `/privacy` and `/data-deletion` pages
- [ ] **Security audit**: Review `SECURITY.md` checklist

## 📦 Infrastructure Setup

### Database
- [ ] PostgreSQL database provisioned (Neon, Supabase, or other)
- [ ] Database includes pgvector extension
- [ ] Migration `migrations/001_init.sql` executed
- [ ] All tables created and verified
- [ ] Connection string tested
- [ ] Backups configured
- [ ] Connection pooling enabled (for production)

### Redis
- [ ] Redis instance provisioned
- [ ] Connection string obtained
- [ ] Test connection works
- [ ] Persistence enabled (if needed)
- [ ] Password set (if exposed to internet)

### Services
- [ ] API service deployed and running
- [ ] Worker service deployed and running
- [ ] Nginx/proxy configured
- [ ] Dashboard service running (optional)
- [ ] All services can reach Redis
- [ ] All services can reach PostgreSQL

## 🔑 Meta Configuration

### App Setup
- [ ] Meta App created at [developers.facebook.com](https://developers.facebook.com)
- [ ] Instagram Graph API product added
- [ ] Webhooks product added
- [ ] App mode set to "Live" (after testing in Development mode)

### Permissions
- [ ] `instagram_manage_messages` permission requested/approved
- [ ] `pages_messaging` permission requested/approved
- [ ] Permissions are active for your app

### Accounts
- [ ] Instagram account converted to Business Account
- [ ] Instagram Business Account linked to Facebook Page
- [ ] Facebook Page connected to Meta App
- [ ] Page Access Token generated (long-lived, 60 days)
- [ ] Instagram Business Account ID obtained

### Webhook
- [ ] Webhook callback URL configured: `https://yourdomain.com/webhook`
- [ ] Verify token set (matches `META_VERIFY_TOKEN`)
- [ ] Webhook subscribed to "messages" field
- [ ] Webhook verification test passed
- [ ] Test message sent and received

## 🌍 Environment Variables

### Required
- [ ] `META_APP_ID` - Your app ID
- [ ] `META_APP_SECRET` - Your app secret (keep secure!)
- [ ] `META_VERIFY_TOKEN` - Webhook verification token
- [ ] `META_PAGE_ID` - Facebook Page ID
- [ ] `META_PAGE_ACCESS_TOKEN` - Long-lived token (keep secure!)
- [ ] `META_GRAPH_VERSION` - API version (21.0+)
- [ ] `REDIS_URL` - Redis connection string
- [ ] `POSTGRES_URL` - PostgreSQL connection string

### Strongly Recommended
- [ ] `META_IG_BUSINESS_ID` - Instagram Business Account ID
- [ ] `GROQ_API_KEY` - For LLM responses (or OLLAMA_HOST)
- [ ] `LLM_PROVIDER` - Set to `groq`, `ollama`, or `none`

### Optional
- [ ] `KG_URI`, `KG_USER`, `KG_PASSWORD` - Neo4j (if using)
- [ ] `TELEGRAM_BOT_TOKEN`, `HUMAN_CHAT_ID` - Human handoff
- [ ] `LOG_LEVEL` - Set to `INFO` for production
- [ ] `JSON_LOGS` - Set to `true` for structured logs

## 📝 Privacy & Compliance

- [ ] Privacy policy updated with accurate information
  - Contact email changed from `privacy@yourdomain.com`
  - Data retention period specified
  - Third-party services listed (Groq, Meta, hosting provider)
- [ ] Data deletion page updated with contact info
- [ ] Privacy policy URL accessible: `https://yourdomain.com/privacy`
- [ ] Data deletion URL accessible: `https://yourdomain.com/data-deletion`
- [ ] Data deletion command works: Test "DELETE MY DATA"
- [ ] Terms of Service created (if required)

## 🧪 Testing

### Functional Tests
- [ ] Health check works: `GET /health` returns healthy
- [ ] Detailed health works: `GET /health/detailed` shows all green
- [ ] Webhook verification works (Meta subscription test)
- [ ] Can receive incoming messages
- [ ] Bot responds to messages
- [ ] Data deletion command works
- [ ] Dashboard loads and shows data
- [ ] Analytics are being recorded

### Integration Tests
- [ ] Send text message → Get response
- [ ] Send greeting → Get contextual response
- [ ] Send support request → Get appropriate response
- [ ] Send multiple messages → Context is maintained
- [ ] Delete data command → Confirmation received
- [ ] Attachments handled gracefully

### Load Tests (Optional but Recommended)
- [ ] Test 10 concurrent messages
- [ ] Test webhook rate limiting
- [ ] Test Redis queue under load
- [ ] Verify no message loss

## 📊 Monitoring & Observability

- [ ] Log aggregation configured (Papertrail, Logtail, etc.)
- [ ] Error tracking setup (Sentry, Rollbar, etc.)
- [ ] Uptime monitoring configured (UptimeRobot, Pingdom)
- [ ] Health check endpoint monitored
- [ ] Alerts configured for:
  - Service down
  - High error rate
  - Database connection failures
  - Redis connection failures
  - Webhook verification failures
- [ ] Metrics collection enabled
- [ ] Dashboard accessible at `/dash/`

## 🔄 App Review (Meta)

If you need `instagram_manage_messages` permission:

- [ ] App Review submission prepared
- [ ] Screencast recorded showing:
  - Privacy and data deletion pages
  - Bot receiving and responding to messages
  - Data deletion command working
  - Dashboard showing analytics
- [ ] Test users added as Instagram Testers
- [ ] Test credentials provided in submission
- [ ] Permissions justification written
- [ ] App Review submitted
- [ ] Approval received (before going live)

## 🚀 Deployment

- [ ] Production environment selected (Railway, Render, Fly.io, etc.)
- [ ] All services deployed
- [ ] Custom domain configured (or using platform domain)
- [ ] SSL certificate active and valid
- [ ] DNS configured correctly
- [ ] Environment variables set in production
- [ ] Services restarted after config changes
- [ ] Logs show successful startup

## 📖 Documentation

- [ ] README.md reviewed and updated with your specifics
- [ ] Contact information updated in docs
- [ ] Deployment platform documented
- [ ] Environment variables documented
- [ ] Backup procedures documented
- [ ] Incident response plan created
- [ ] Runbook for common issues created

## 🛡️ Operational Readiness

- [ ] Backup strategy in place
- [ ] Database backups verified
- [ ] Recovery procedures tested
- [ ] Token expiry monitoring set up (60-day reminder)
- [ ] On-call rotation defined (if team)
- [ ] Incident response process defined
- [ ] Status page created (optional)

## 💰 Cost Management

- [ ] Estimated monthly costs calculated
- [ ] Billing alerts configured
- [ ] Resource limits set to prevent runaway costs
- [ ] Free tier limits understood
- [ ] Scaling thresholds defined

## ✅ Final Checks

- [ ] All services show "healthy" status
- [ ] End-to-end flow tested in production
- [ ] Team trained on operations (if applicable)
- [ ] Documentation accessible to team
- [ ] Support contacts saved
- [ ] Launch date/time scheduled
- [ ] Rollback plan prepared
- [ ] Post-launch monitoring plan ready

## 📅 Post-Launch

Within 24 hours:
- [ ] Monitor error rates
- [ ] Check response times
- [ ] Verify message volume is being handled
- [ ] Review logs for any issues
- [ ] Confirm dashboard is updating

Within 1 week:
- [ ] Review analytics and user feedback
- [ ] Optimize response templates if needed
- [ ] Check resource usage and costs
- [ ] Plan for scaling if needed

Within 1 month:
- [ ] Review Meta token expiry (refresh if < 30 days)
- [ ] Analyze conversation patterns
- [ ] Update knowledge base (FAQ ingestion)
- [ ] Performance optimization based on metrics

---

## Emergency Contacts

- **Meta Developer Support**: [developers.facebook.com/support](https://developers.facebook.com/support)
- **Your Hosting Platform**: [support page]
- **Database Provider**: [support page]
- **LLM Provider (Groq)**: [console.groq.com](https://console.groq.com)

---

## Quick Troubleshooting

**Messages not being received?**
1. Check webhook subscription is active
2. Verify callback URL is correct
3. Test `/webhook` endpoint manually
4. Check API logs for errors

**Worker not responding?**
1. Check worker service is running
2. Verify Redis connectivity
3. Check environment variables
4. Review worker logs

**Database errors?**
1. Verify POSTGRES_URL is correct
2. Check database is accessible
3. Ensure migrations ran successfully
4. Verify pgvector extension is enabled

---

## Sign-Off

Before going live, have your checklist reviewed by:

- [ ] Developer: All technical items complete
- [ ] Security: Security items verified
- [ ] Operations: Infrastructure ready
- [ ] Business: Privacy/compliance approved

**Signed off by**: ________________
**Date**: ________________
**Production launch authorized**: ☐ Yes

---

🎉 **Congratulations!** Once this checklist is complete, you're ready to launch!
