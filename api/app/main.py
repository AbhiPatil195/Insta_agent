import hashlib
import hmac
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import orjson
import asyncio

from shared.config import META_APP_SECRET, META_VERIFY_TOKEN, REDIS_URL
from .queue import get_redis, enqueue_event


app = FastAPI(title="Insta Agent Webhook API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await get_redis(REDIS_URL)  # initialize connection pool


@app.get("/health")
async def health():
    """Basic health check endpoint for load balancers."""
    return {"status": "healthy", "service": "api"}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with dependency status."""
    import time
    from .queue import get_redis
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "api",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check Redis connectivity
    try:
        r = await get_redis(REDIS_URL)
        await r.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check if required env vars are set
    required_vars = {
        "META_VERIFY_TOKEN": bool(META_VERIFY_TOKEN),
        "META_PAGE_ACCESS_TOKEN": bool(META_PAGE_ACCESS_TOKEN),
        "REDIS_URL": bool(REDIS_URL),
    }
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        health_status["checks"]["config"] = {
            "status": "unhealthy",
            "message": f"Missing: {', '.join(missing_vars)}"
        }
        health_status["status"] = "unhealthy"
    else:
        health_status["checks"]["config"] = {"status": "healthy", "message": "All required vars set"}
    
    return health_status


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == META_VERIFY_TOKEN:
        # Meta expects raw challenge as body
        return PlainTextResponse(content=challenge or "", status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")


def verify_signature(app_secret: str | None, raw_body: bytes, signature_header: str | None, legacy_header: str | None = None) -> bool:
    if not app_secret:
        # In dev, allow if no secret configured
        return True
    # Prefer v2 sha256, fallback to legacy sha1 header if present
    if signature_header and signature_header.startswith("sha256="):
        provided = signature_header.split("=", 1)[1]
        digest = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        if hmac.compare_digest(provided, digest):
            return True
    if legacy_header and legacy_header.startswith("sha1="):
        provided = legacy_header.split("=", 1)[1]
        digest = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha1).hexdigest()
        return hmac.compare_digest(provided, digest)
    return False


@app.post("/webhook")
async def receive_webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")
    sig1 = request.headers.get("X-Hub-Signature")

    if not verify_signature(META_APP_SECRET, raw, sig, sig1):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = orjson.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Push to Redis queue for async processing
    await enqueue_event(payload)
    return {"status": "queued"}


@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    """Comprehensive privacy policy for Meta App Review compliance."""
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Privacy Policy - Insta Agent</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; color: #333; }
                h1 { color: #1877f2; border-bottom: 3px solid #1877f2; padding-bottom: 10px; }
                h2 { color: #555; margin-top: 30px; }
                .last-updated { color: #666; font-style: italic; }
                .important { background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin: 20px 0; }
                ul { padding-left: 20px; }
                a { color: #1877f2; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Privacy Policy</h1>
            <p class="last-updated">Last Updated: November 8, 2025</p>
            
            <div class="important">
                <strong>Quick Summary:</strong> We use your Instagram messages to provide automated assistance. We do not sell your data. You can delete your data anytime by messaging "DELETE MY DATA".
            </div>
            
            <h2>1. Information We Collect</h2>
            <p>When you interact with our Instagram bot, we collect and process:</p>
            <ul>
                <li><strong>Message Content:</strong> Text messages you send via Instagram Direct Messages</li>
                <li><strong>Instagram User ID:</strong> Your unique Instagram identifier</li>
                <li><strong>Conversation Metadata:</strong> Timestamps, message sequence, conversation context</li>
                <li><strong>Intent Classification:</strong> Automated categorization of your requests (support, sales, greeting, etc.)</li>
            </ul>
            
            <h2>2. How We Use Your Information</h2>
            <p>We use collected data to:</p>
            <ul>
                <li>Provide automated responses to your Instagram messages</li>
                <li>Understand conversation context and provide relevant assistance</li>
                <li>Improve our AI assistant's accuracy and helpfulness</li>
                <li>Analyze service performance and user experience</li>
                <li>Comply with legal obligations</li>
            </ul>
            
            <h2>3. Data Storage and Security</h2>
            <ul>
                <li><strong>Location:</strong> Data stored on secure cloud infrastructure (PostgreSQL database)</li>
                <li><strong>Encryption:</strong> Data encrypted in transit (HTTPS/TLS) and at rest</li>
                <li><strong>Access:</strong> Restricted to authorized personnel and automated systems only</li>
                <li><strong>Retention:</strong> Data retained until you request deletion or account closure</li>
            </ul>
            
            <h2>4. Data Sharing and Third Parties</h2>
            <p>We do NOT sell your personal information. We may share data with:</p>
            <ul>
                <li><strong>Meta Platforms:</strong> To send/receive messages via Instagram API</li>
                <li><strong>AI Providers:</strong> Message content sent to LLM providers (Groq, Ollama) for response generation</li>
                <li><strong>Infrastructure Providers:</strong> Cloud hosting (for data storage and processing)</li>
                <li><strong>Legal Requirements:</strong> When required by law or to protect rights and safety</li>
            </ul>
            
            <h2>5. Your Rights (GDPR/CCPA)</h2>
            <p>You have the right to:</p>
            <ul>
                <li><strong>Access:</strong> Request a copy of your data</li>
                <li><strong>Deletion:</strong> Request deletion of your data (see section 7)</li>
                <li><strong>Correction:</strong> Request correction of inaccurate data</li>
                <li><strong>Portability:</strong> Receive your data in a structured format</li>
                <li><strong>Objection:</strong> Object to data processing</li>
                <li><strong>Withdraw Consent:</strong> Stop using the service anytime</li>
            </ul>
            
            <h2>6. Cookies and Tracking</h2>
            <p>Our Instagram bot does not use cookies or tracking technologies. We only process messages you explicitly send to us.</p>
            
            <h2>7. Data Deletion</h2>
            <p>You can request immediate data deletion by:</p>
            <ul>
                <li>Sending "DELETE MY DATA" via Instagram Direct Message</li>
                <li>Visiting our <a href="/data-deletion">Data Deletion Request page</a></li>
            </ul>
            <p>Deletion is processed automatically and removes all your messages, conversation history, and user profile from our systems.</p>
            
            <h2>8. Children's Privacy</h2>
            <p>Our service is not intended for users under 13 years of age (or 16 in the EU). We do not knowingly collect data from children.</p>
            
            <h2>9. International Data Transfers</h2>
            <p>Your data may be transferred to and processed in countries outside your residence. We ensure appropriate safeguards are in place.</p>
            
            <h2>10. Changes to Privacy Policy</h2>
            <p>We may update this policy periodically. Continued use after changes constitutes acceptance. Material changes will be notified via Instagram.</p>
            
            <h2>11. Meta Platform Compliance</h2>
            <p>This service complies with <a href="https://developers.facebook.com/docs/instagram-platform" target="_blank">Instagram Platform Policy</a> and <a href="https://developers.facebook.com/policy/" target="_blank">Meta Platform Terms</a>.</p>
            
            <h2>12. Contact Us</h2>
            <p>For privacy questions, data requests, or concerns:</p>
            <ul>
                <li>Instagram: Send a message to our business account</li>
                <li>Email: privacy@yourdomain.com</li>
            </ul>
            
            <p style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 14px;">
                This privacy policy is effective as of the last updated date above and applies to all users of the Insta Agent service.
            </p>
        </body>
        </html>
        """,
        status_code=200,
    )


@app.get("/data-deletion", response_class=HTMLResponse)
async def data_deletion():
    """Data deletion instructions for Meta App Review compliance."""
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Data Deletion Request - Insta Agent</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; color: #333; }
                h1 { color: #dc3545; border-bottom: 3px solid #dc3545; padding-bottom: 10px; }
                h2 { color: #555; margin-top: 30px; }
                .method-box { background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 20px 0; }
                .method-title { color: #dc3545; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
                .instant { background: #d1ecf1; border-color: #bee5eb; }
                .instant .method-title { color: #0c5460; }
                .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin: 20px 0; }
                .success { background: #d4edda; border-left: 4px solid #28a745; padding: 12px; margin: 20px 0; }
                ol { padding-left: 25px; }
                ul { padding-left: 20px; }
                code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
                a { color: #1877f2; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Data Deletion Request</h1>
            
            <p>We respect your privacy and provide easy ways to delete your data from our systems. Choose the method that works best for you:</p>
            
            <div class="method-box instant">
                <div class="method-title">🚀 Method 1: Instant Deletion (Recommended)</div>
                <p><strong>Deletion time: Immediate</strong></p>
                <ol>
                    <li>Open Instagram and go to your Direct Messages</li>
                    <li>Find the conversation with our bot</li>
                    <li>Send the exact message: <code>DELETE MY DATA</code></li>
                    <li>You'll receive an instant confirmation that your data has been deleted</li>
                </ol>
                <div class="success">
                    ✓ This method is fully automated and deletes your data immediately without any manual intervention.
                </div>
            </div>
            
            <div class="method-box">
                <div class="method-title">📧 Method 2: Email Request</div>
                <p><strong>Deletion time: Within 30 days</strong></p>
                <ol>
                    <li>Send an email to: <strong>privacy@yourdomain.com</strong></li>
                    <li>Subject: "Data Deletion Request"</li>
                    <li>Include your Instagram username or User ID</li>
                    <li>We'll process your request and confirm via email within 30 days</li>
                </ol>
            </div>
            
            <div class="method-box">
                <div class="method-title">💬 Method 3: Instagram Message</div>
                <p><strong>Deletion time: Within 30 days</strong></p>
                <ol>
                    <li>Send a direct message to our Instagram business account</li>
                    <li>State: "I request deletion of my data" (or similar)</li>
                    <li>We'll manually process your request and confirm deletion</li>
                </ol>
            </div>
            
            <h2>What Gets Deleted?</h2>
            <p>When you request data deletion, we permanently remove:</p>
            <ul>
                <li><strong>All Messages:</strong> Every message you've sent and received</li>
                <li><strong>Conversation History:</strong> Complete conversation threads</li>
                <li><strong>User Profile:</strong> Your user ID and associated metadata</li>
                <li><strong>Memory Embeddings:</strong> AI-generated semantic representations of your messages</li>
                <li><strong>Analytics Data:</strong> Response times, intent classifications, and performance metrics</li>
            </ul>
            
            <div class="warning">
                <strong>⚠️ Important:</strong> Data deletion is <strong>permanent and irreversible</strong>. Once deleted, we cannot recover your conversation history or preferences.
            </div>
            
            <h2>What's NOT Deleted?</h2>
            <ul>
                <li><strong>Meta's Records:</strong> Messages stored on Instagram's servers (controlled by Meta)</li>
                <li><strong>Backups:</strong> Data in backups may persist for up to 90 days per our retention policy</li>
                <li><strong>Aggregated Analytics:</strong> Anonymous, non-identifiable statistics (cannot be linked back to you)</li>
                <li><strong>Legal Requirements:</strong> Data we're required to retain by law</li>
            </ul>
            
            <h2>Verification Process</h2>
            <p>For automated deletion (Method 1), no verification is needed. For manual requests (Methods 2-3), we may ask for:</p>
            <ul>
                <li>Confirmation of your Instagram username</li>
                <li>Recent message content to verify identity</li>
                <li>Reason for deletion (optional, helps us improve)</li>
            </ul>
            
            <h2>Timeline</h2>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background: #f8f9fa;">
                    <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">Method</th>
                    <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">Processing Time</th>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Instagram Command ("DELETE MY DATA")</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Instant (< 1 minute)</strong></td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Email Request</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Up to 30 days</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Manual Message Request</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Up to 30 days</td>
                </tr>
            </table>
            
            <h2>After Deletion</h2>
            <p>Once your data is deleted:</p>
            <ul>
                <li>You can still use the bot - it will treat you as a new user</li>
                <li>Previous conversation context will be lost</li>
                <li>You can request deletion again anytime</li>
            </ul>
            
            <h2>Questions?</h2>
            <p>If you have questions about data deletion:</p>
            <ul>
                <li>Read our <a href="/privacy">Privacy Policy</a></li>
                <li>Email: privacy@yourdomain.com</li>
                <li>Message our Instagram business account</li>
            </ul>
            
            <p style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 14px;">
                This page complies with Meta Platform Policy and GDPR/CCPA data deletion requirements.
            </p>
        </body>
        </html>
        """,
        status_code=200,
    )
