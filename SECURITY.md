# Security Guidelines

## Credential Management

### Critical Secrets
Never commit these to version control:
- `META_APP_SECRET` - Used for webhook signature verification
- `META_PAGE_ACCESS_TOKEN` - Used to send messages via Graph API
- `GROQ_API_KEY` / `OLLAMA_HOST` credentials
- `POSTGRES_URL` with database password
- `KG_PASSWORD` for Neo4j
- `TELEGRAM_BOT_TOKEN`

### Best Practices

#### Development
1. Copy `.env.example` to `.env` and fill in your values
2. Never commit `.env` to git (protected by `.gitignore`)
3. Use separate credentials for dev and production
4. Rotate tokens regularly (every 60-90 days)

#### Production
1. **Use environment variables** instead of `.env` files
2. **Use secret managers**:
   - Railway: Built-in secret variables
   - Render: Environment variables in dashboard
   - Fly.io: `flyctl secrets set KEY=value`
   - AWS: Secrets Manager / Parameter Store
   - GCP: Secret Manager
   - Azure: Key Vault
3. **Enable signature verification**: Always set `META_APP_SECRET` to validate webhooks
4. **Use long-lived tokens**: Generate long-lived Page Access Tokens (60 days)
5. **Rotate credentials**: Set reminders to rotate before expiry

### Token Generation

#### Meta Page Access Token (Long-lived)
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer)
2. Select your app
3. Get User Access Token with permissions: `pages_messaging`, `instagram_manage_messages`
4. Exchange for long-lived token using:
   ```bash
   curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN"
   ```
5. Store the returned long-lived token as `META_PAGE_ACCESS_TOKEN`

#### Groq API Key
1. Visit [Groq Console](https://console.groq.com)
2. Create account (free tier available)
3. Generate API key
4. Set as `GROQ_API_KEY`

### Security Checklist Before Production

- [ ] All credentials removed from code and config files
- [ ] `.env` file in `.gitignore`
- [ ] Production secrets stored in secret manager
- [ ] `META_APP_SECRET` configured for webhook signature verification
- [ ] Changed default dashboard password in `nginx/.htpasswd`
- [ ] Updated IP allowlist in `nginx/allow_dash.conf/allow_dash.conf`
- [ ] HTTPS enabled (required for webhooks)
- [ ] CORS origins restricted (remove `allow_origins=["*"]`)
- [ ] Rate limiting configured on all endpoints
- [ ] Webhook signature verification enabled
- [ ] Database credentials secured
- [ ] Redis password set (if exposed)
- [ ] Long-lived tokens with auto-refresh configured
- [ ] Monitoring and alerting for token expiry
- [ ] Incident response plan documented

## Vulnerability Reporting

If you discover a security vulnerability, please email security@yourdomain.com instead of opening a public issue.

## Security Updates

- Check [Meta Security Advisory](https://developers.facebook.com/docs/whatsapp/security/) regularly
- Subscribe to dependency security alerts on GitHub
- Update dependencies monthly: `pip list --outdated`

## Compliance

### GDPR / Data Privacy
- Users can request data deletion via "DELETE MY DATA" command
- Privacy policy accessible at `/privacy`
- Data deletion instructions at `/data-deletion`
- Store only necessary data
- Implement data retention policies

### Meta Platform Policy
- Follow [Instagram Platform Policy](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/overview#instagram-user-data)
- Never share user data with third parties without consent
- Respect rate limits
- Handle user data securely

## Monitoring

Set up alerts for:
- Failed authentication attempts
- Webhook signature verification failures
- Unusual API call patterns
- Token expiration (30 days before)
- Database connection failures
- Elevated error rates
