# Dashboard Setup Guide

The Insta Agent includes a Streamlit analytics dashboard accessible at `/dash/` with built-in security.

## Security Features

1. **HTTP Basic Authentication** - Username/password protection
2. **IP Allowlist** - Restrict access to specific IP addresses
3. **WebSocket Support** - For real-time Streamlit updates

## Initial Setup

### 1. Update Dashboard Credentials

⚠️ **IMPORTANT**: The default credentials (`admin`/`password`) MUST be changed before production.

#### Option A: Using Python Script (Recommended)
```bash
# Install required package
pip install passlib

# Run the password generator
python scripts/update_dashboard_password.py
```

#### Option B: Using htpasswd Command
```bash
# Install apache2-utils (Linux) or use Docker
htpasswd -Bc nginx/.htpasswd admin
```

#### Option C: Manual Edit
Generate a bcrypt hash and update `nginx/.htpasswd` manually.

### 2. Configure IP Allowlist

Edit `nginx/allow_dash.conf/allow_dash.conf`:

```nginx
# Allow your IP address
allow YOUR_IP_HERE/32;

# Allow localhost
allow 127.0.0.1/32;

# Deny all others
deny all;
```

**Find your IP address:**
```bash
curl ifconfig.me
```

**For production deployments:**
- Railway/Render: Check your platform's egress IP documentation
- Corporate: Get your office IP range from IT
- VPN: Use your VPN's IP range
- Home: Use your ISP-assigned IP (may change periodically)

### 3. Restart Nginx

```bash
docker compose restart nginx
```

## Accessing the Dashboard

1. Navigate to: `http://localhost:8080/dash/` (dev) or `https://yourdomain.com/dash/` (prod)
2. Enter your credentials when prompted
3. If blocked by IP: Add your IP to `allow_dash.conf`

## Dashboard Features

The dashboard displays:
- **Total Messages** - User and assistant message counts
- **Active Threads** - Number of conversation threads
- **Intent Breakdown** - Classification of user intents (greeting, support, sales, etc.)
- **Response Analytics** - Model performance, latency, confidence scores
- **Recent Conversations** - Latest message history

## Troubleshooting

### "403 Forbidden" Error
- **Cause**: Your IP is not in the allowlist
- **Fix**: Add your IP to `nginx/allow_dash.conf/allow_dash.conf`

### "401 Unauthorized" Error
- **Cause**: Invalid credentials
- **Fix**: Regenerate credentials using the script above

### Dashboard Not Loading
- **Check if dash service is running**: `docker compose ps dash`
- **Check logs**: `docker compose logs dash`
- **Verify Nginx config**: `docker compose exec nginx nginx -t`

### Connection Reset / WebSocket Errors
- **Cause**: Proxy settings incorrect
- **Fix**: Ensure `proxy_http_version 1.1` and upgrade headers are set in nginx.conf

## Production Recommendations

1. **Use HTTPS** - Never expose dashboard over plain HTTP in production
2. **Strong Passwords** - Use the random password generator
3. **Narrow IP Range** - Only allow necessary IPs
4. **Regular Rotation** - Change password every 90 days
5. **Audit Access** - Monitor nginx access logs for dashboard endpoint
6. **Consider VPN** - Host dashboard behind VPN for additional security

## Advanced: Disable Dashboard

If you don't need the dashboard:

1. Comment out the `/dash/` location block in `nginx/nginx.conf`
2. Stop the dash service: `docker compose stop dash`
3. Or remove it from `docker-compose.yml`

## Advanced: Custom Domain

To host dashboard at a subdomain (e.g., `dashboard.yourdomain.com`):

1. Create separate Nginx server block
2. Point subdomain DNS to your server
3. Configure SSL certificate (Let's Encrypt recommended)
4. Update authentication settings

Example config:
```nginx
server {
    listen 443 ssl http2;
    server_name dashboard.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        auth_basic "Dashboard Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        include /etc/nginx/allow_dash;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_pass http://dash:8501/;
    }
}
```
