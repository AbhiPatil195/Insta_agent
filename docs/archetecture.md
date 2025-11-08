# Architecture & Sequence Diagrams

This document outlines the key components of Insta Agent and the end‑to‑end request flows using sequence diagrams.

## Components
- Nginx reverse proxy (rate limiting, optional basic auth for dashboard)
- API (FastAPI): `/webhook`, `/health`, privacy/data-deletion pages
- Redis: queue for webhook events
- Worker: consumes queue, generates replies, calls Meta Graph API
- Meta Graph API: receives outgoing messages and actions
- Cloudflare Tunnel (dev): exposes local Nginx/API over HTTPS
- Optional: Postgres (pgvector) for memory/RAG, LLM provider (Groq/Ollama)

## Webhook Verification (GET)
```mermaid
sequenceDiagram
  participant Meta as Meta Webhooks
  participant CF as Cloudflare Tunnel
  participant NG as Nginx
  participant API as FastAPI API

  Meta->>CF: GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=1234
  CF->>NG: GET /webhook?...(forward)
  NG->>API: GET /webhook?...(forward)
  API->>API: Compare hub.verify_token with META_VERIFY_TOKEN
  API-->>NG: 200 body=hub.challenge
  NG-->>CF: 200 body=hub.challenge
  CF-->>Meta: 200 body=hub.challenge
```

Notes
- Verify token: `META_VERIFY_TOKEN`
- Endpoint: `GET /webhook` returns the raw `hub.challenge` when valid.

## Incoming DM Processing (POST)
```mermaid
sequenceDiagram
  participant IG as Instagram User
  participant Graph as Meta Graph API
  participant Meta as Meta Webhooks
  participant CF as Cloudflare Tunnel
  participant NG as Nginx
  participant API as FastAPI API (/webhook)
  participant R as Redis Queue
  participant W as Worker

  IG->>Graph: Send DM
  Graph-->>Meta: Deliver webhook event
  Meta->>CF: POST /webhook {entry:[...]}
  CF->>NG: POST /webhook
  NG->>API: POST /webhook
  API->>API: Verify X-Hub-Signature-256 with META_APP_SECRET (if set)
  API->>R: RPUSH insta_jobs (payload)
  R-->>API: OK
  API-->>NG: 200 {"status":"queued"}
  NG-->>CF: 200
  CF-->>Meta: 200

  W->>R: BRPOP insta_jobs
  R-->>W: payload
  W->>Graph: POST /me/messages sender_action=mark_seen (with META_PAGE_ACCESS_TOKEN)
  W->>Graph: POST /me/messages sender_action=typing_on
  W->>W: Generate reply
  alt With PG + LLM
    W->>PG: Search memory via pgvector (optional)
    PG-->>W: Relevant memory (optional)
    W->>LLM: Generate reply with context (optional)
    LLM-->>W: Reply text
  else Fallback
    W->>W: Rule‑based/basic reply
  end
  W->>Graph: POST /{IG_BUSINESS_ID or me}/messages text
  Graph-->>IG: Deliver reply
```

Notes
- Outbound endpoint: `/{META_IG_BUSINESS_ID}/messages` if `META_IG_BUSINESS_ID` is set, else `/me/messages`.
- Tokens: `META_PAGE_ACCESS_TOKEN` (+ `appsecret_proof` if `META_APP_SECRET` provided).
- Rate limiting: Nginx `limit_req` on `/webhook`.

## Dashboard Proxy (optional)
```mermaid
sequenceDiagram
  participant User as Browser
  participant NG as Nginx
  participant Dash as Streamlit (8501)

  User->>NG: GET /dash/
  NG->>NG: HTTP Basic Auth + IP allowlist
  NG->>Dash: Proxy / (8501)
  Dash-->>NG: 200 HTML
  NG-->>User: 200 HTML
```

Notes
- Basic auth: `nginx/.htpasswd` (replace defaults before prod).
- IP allowlist: `nginx/allow_dash.conf`.

## FAQ Ingestion (RAG)
```mermaid
sequenceDiagram
  participant Dev as Developer
  participant Tool as tools.ingest_faq
  participant PG as Postgres (pgvector)

  Dev->>Tool: python -m tools.ingest_faq
  Tool->>PG: Ensure extensions (vector, pgcrypto)
  Tool->>PG: Insert chunks into memory_embeddings (user_id=0)
  PG-->>Tool: OK
```

## Key Environment Variables
- `META_VERIFY_TOKEN` (webhook verification)
- `META_APP_SECRET` (signature/appsecret_proof)
- `META_PAGE_ACCESS_TOKEN` (required for sending messages)
- `META_IG_BUSINESS_ID` (optional; selects IG Business endpoint)
- `REDIS_URL`, `POSTGRES_URL` (optional for RAG), `LLM_PROVIDER` + provider keys

## Health & Ops
- API health: `GET /health` (proxied at `/health` via Nginx)
- Logs: `docker compose logs -f api worker`
- Tunnel (dev): Cloudflare quick tunnel exposes Nginx/API for Meta webhooks

