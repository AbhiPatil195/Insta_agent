# Insta Agent (Free-tier Friendly)

Production-ready Instagram DM AI agent with FastAPI, Redis queue, and a worker that replies via Meta Graph API. Designed for free/near-free infra (Render/Railway/Fly.io, Neon/Supabase, Redis Cloud, Cloudflare Tunnel).

## Quick Start

1) Copy `.env.example` to `.env` and fill values (at least `META_VERIFY_TOKEN`, `META_PAGE_ACCESS_TOKEN`).

2) Build and run:

```bash
docker compose up -d --build
```

3) Dev tunneling: expose `nginx` at a stable HTTPS URL (Cloudflare Tunnel) and set your Meta Webhook callback to `https://<your-domain>/webhook` with the verify token you set.
   - Windows: run `scripts/dev_tunnel.ps1`
   - macOS/Linux: run `bash scripts/dev_tunnel.sh`

4) Verify: `GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=1234` returns `1234`.

## Services
- api: FastAPI webhook intake, HMAC signature verify, enqueue to Redis
- worker: consumes jobs, generates a simple reply (placeholder), sends via Meta API
- nginx: reverse proxy with basic rate limiting
- redis: queue/cache
- dash: Streamlit analytics dashboard (proxied at `/dash`)

## Meta Setup (Essentials)
- Create Meta App, add Instagram Graph API + Webhooks
- Connect IG Business account to a Facebook Page
- Permissions: `instagram_manage_messages`, `pages_messaging`
- Generate long-lived Page Access Token; set `META_PAGE_ACCESS_TOKEN`
- Set Webhook callback and verify token; subscribe to IG messages
  - If you have an Instagram Business Account ID, set `META_IG_BUSINESS_ID` to use `/{IG_BUSINESS_ID}/messages` endpoint; otherwise defaults to `/me/messages`.
  - Privacy URLs for App Review: `/privacy`, `/data-deletion` are exposed by the API.

## Production Deployment

**Ready to launch?** Follow these guides:

1. **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - Complete launch checklist ✅
2. **[docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)** - Deploy to Railway, Render, Fly.io, etc.
3. **[docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md)** - Setup PostgreSQL with pgvector
4. **[docs/DASHBOARD_SETUP.md](docs/DASHBOARD_SETUP.md)** - Secure dashboard configuration
5. **[SECURITY.md](SECURITY.md)** - Security best practices
6. **[docs/APP_REVIEW.md](docs/APP_REVIEW.md)** - Meta App Review submission guide

## Configuration

### LLM Provider
Set `LLM_PROVIDER` to `groq` (with `GROQ_API_KEY`) or `ollama` (with `OLLAMA_HOST`). Models configurable via `GROQ_MODEL`/`OLLAMA_MODEL`.

### Database
Use Neon/Supabase and set `POSTGRES_URL`. Run `migrations/001_init.sql` to enable `pgvector` and tables. See **[docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md)** for detailed guide.

### RAG + Memory
Worker stores user messages and uses vector search for context. Ingest FAQs with `python -m tools.ingest_faq`.

### Dashboard
Access Streamlit analytics at `http://localhost:8080/dash/`. See **[docs/DASHBOARD_SETUP.md](docs/DASHBOARD_SETUP.md)** for security setup.

## Dev Notes
- Webhook payloads are queued immediately; worker processes and replies.
- Signature verification uses `X-Hub-Signature-256` with your `META_APP_SECRET`.
- Sending replies uses `me/messages` with `messaging_product=instagram`.
- Embeddings use `fastembed` (BAAI/bge-small-en-v1.5, 384-dim) stored in `memory_embeddings` via `pgvector`.
- If Postgres or LLM is not configured, worker gracefully falls back to basic replies.
- Worker sends `mark_seen` and `typing_on` actions before replying.
- Intent detection uses Groq/Ollama if available; falls back to a rule-based classifier.
- App Review testing and curl examples: `docs/TESTING.md`.
 - Postman collection: `tools/postman_collection.json` (import into Postman; set variables).

## Running migrations (Neon/Supabase)
1) Connect with any Postgres client to your database.
2) Execute `migrations/001_init.sql`.
   - Ensure extensions `vector` and `pgcrypto` are allowed on your instance.

## Environment quick reference
- `META_VERIFY_TOKEN` (required for webhook verification)
- `META_PAGE_ACCESS_TOKEN` (required for sending messages)
- `META_APP_SECRET` (optional; enables webhook signature and appsecret_proof)
- `POSTGRES_URL` (optional; enables persistence + RAG)
- `LLM_PROVIDER` = `groq` | `ollama` | `none`
- `GROQ_API_KEY` or `OLLAMA_HOST` (depending on provider)
- `META_IG_BUSINESS_ID` (optional; recommended for Instagram messaging send API)
- `META_GRAPH_VERSION` (default `21.0`)

## Dashboard security
- HTTP Basic Auth protects `/dash/` using `nginx/.htpasswd` (default dev creds `admin`/`password`). Replace before production.
- IP allowlist: edit `nginx/allow_dash.conf` (defaults to `allow 127.0.0.1/32; deny all;`).

## FAQ ingestion for RAG
- Put markdown files in `docs/` (e.g., `docs/faq.md`).
- Set `POSTGRES_URL` and run: `python -m tools.ingest_faq`
- This indexes chunks into `memory_embeddings` under `user_id = 0` (global).
