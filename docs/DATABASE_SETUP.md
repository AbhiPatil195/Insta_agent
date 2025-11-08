# Database Setup Guide

Complete guide for setting up PostgreSQL with pgvector for Insta Agent.

## Why Do You Need a Database?

Without a database, the bot:
- ❌ Cannot remember conversation history
- ❌ Cannot provide contextual responses
- ❌ No analytics or insights
- ❌ No RAG (Retrieval Augmented Generation)
- ✅ Only basic rule-based replies work

**For production, a database is STRONGLY RECOMMENDED.**

---

## Database Requirements

- **PostgreSQL 12+** (Recommended: 14 or higher)
- **pgvector extension** (for embeddings and RAG)
- **pgcrypto extension** (for UUID generation)
- **Connection pooling** (for production)
- **SSL/TLS** (for security)

---

## Option 1: Neon (Recommended - Free Tier)

Neon provides serverless PostgreSQL with generous free tier.

**Features:**
- ✅ Free tier: 512MB storage, 0.5GB RAM
- ✅ pgvector pre-installed
- ✅ Automatic backups
- ✅ Auto-scaling
- ✅ No credit card for free tier

**Setup Steps:**

1. **Create Account**: [neon.tech](https://neon.tech)

2. **Create Project**:
   - Click "Create a project"
   - Choose region closest to your app
   - Name: "insta-agent" (or your preference)

3. **Get Connection String**:
   ```
   Dashboard → Connection Details → Copy connection string
   Format: postgresql://user:password@host/dbname?sslmode=require
   ```

4. **Add to Environment**:
   ```bash
   POSTGRES_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```

5. **Run Migration**:
   
   **Option A: Using psql**
   ```bash
   # Install psql if needed
   # Mac: brew install postgresql
   # Ubuntu: sudo apt install postgresql-client
   # Windows: Download from postgresql.org
   
   # Connect and run migration
   psql "postgresql://user:password@host/dbname?sslmode=require" -f migrations/001_init.sql
   ```
   
   **Option B: Using Neon Console**
   - Go to SQL Editor in Neon dashboard
   - Copy contents of `migrations/001_init.sql`
   - Paste and execute

6. **Verify Setup**:
   ```sql
   -- Check extensions
   SELECT * FROM pg_extension WHERE extname IN ('vector', 'pgcrypto');
   
   -- Check tables
   \dt
   -- Should show: users, threads, messages, memory_embeddings, analytics
   
   -- Test vector column
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'memory_embeddings' AND column_name = 'embedding';
   ```

**Neon Tips:**
- Free tier is enough for development and small production
- Upgrade to Pro ($19/mo) for production with higher limits
- Enable connection pooling in Neon dashboard for better performance
- Use branching feature for dev/staging/prod databases

---

## Option 2: Supabase (Free Tier with Dashboard)

Supabase is an open-source Firebase alternative with PostgreSQL.

**Features:**
- ✅ Free tier: 500MB storage, 2GB bandwidth
- ✅ pgvector pre-installed
- ✅ Built-in auth & API (optional, not used by this app)
- ✅ Dashboard for data management
- ✅ Real-time subscriptions

**Setup Steps:**

1. **Create Account**: [supabase.com](https://supabase.com)

2. **Create Project**:
   - New project
   - Choose region
   - Set strong database password (save it!)
   - Wait for provisioning (~2 minutes)

3. **Get Connection String**:
   - Settings → Database → Connection string
   - Select "Session mode" or "Transaction mode"
   - Copy the connection string
   - Replace [YOUR-PASSWORD] with your actual password

4. **Connection String Format**:
   ```
   # Session mode (default)
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   
   # Connection pooling (recommended for production)
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:6543/postgres?pgbouncer=true
   ```

5. **Run Migration**:
   ```bash
   psql "your-connection-string" -f migrations/001_init.sql
   ```
   
   Or use Supabase SQL Editor:
   - SQL Editor (in dashboard) → New query
   - Paste `migrations/001_init.sql`
   - Run

6. **Verify in Dashboard**:
   - Table Editor → Should see all tables
   - Database → Extensions → Verify `vector` is enabled

**Supabase Tips:**
- Use connection pooler (port 6543) for production
- Free tier pauses after 1 week inactivity (Pro plan for always-on)
- Use Supabase dashboard to browse data
- Enable RLS (Row Level Security) if exposing data via Supabase API

---

## Option 3: Railway PostgreSQL

If deploying on Railway, use their managed PostgreSQL.

**Setup Steps:**

1. **Add PostgreSQL Service**:
   - In your Railway project: New → Database → PostgreSQL
   - Railway provisions it automatically

2. **Get Connection String**:
   - PostgreSQL service → Connect → Copy `DATABASE_URL`
   - Format: `postgresql://postgres:password@host:port/railway`

3. **Add to Environment**:
   - All services get `DATABASE_URL` automatically
   - Or manually set `POSTGRES_URL` = `DATABASE_URL`

4. **Run Migration**:
   - Connect via psql using the connection string
   - Run `migrations/001_init.sql`

**Railway PostgreSQL Tips:**
- Includes pgvector by default
- Automatic daily backups on Pro plan
- Use "Data" tab to view database in dashboard

---

## Option 4: Render PostgreSQL

**Setup Steps:**

1. **Create Database**:
   - New → PostgreSQL
   - Choose region
   - Select Free or Starter plan

2. **Get Connection Strings**:
   - **Internal**: For services in Render (faster)
   - **External**: For external access
   
   Use Internal URL in your app:
   ```
   postgresql://user:password@internal-hostname/dbname
   ```

3. **Add to Environment**:
   ```bash
   POSTGRES_URL=<Internal Database URL>
   ```

4. **Run Migration**:
   - Use External URL for psql access
   ```bash
   psql "External Database URL" -f migrations/001_init.sql
   ```

**Render PostgreSQL Tips:**
- Free tier: 90-day retention, 1GB storage
- Starter plan: $7/mo, better for production
- Enable high availability on paid plans

---

## Option 5: Self-Hosted with Docker

For development or self-hosting.

**docker-compose.yml** (already in repo, commented out):
```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: insta_agent
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**Setup:**
```bash
# Uncomment db service in docker-compose.yml
docker compose up -d db

# Connection string
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/insta_agent

# Run migration
docker compose exec db psql -U postgres -d insta_agent -f /path/to/001_init.sql
# Or: psql postgresql://postgres:postgres@localhost:5432/insta_agent -f migrations/001_init.sql
```

---

## Migration File Explained

The `migrations/001_init.sql` creates:

### 1. Extensions
```sql
create extension if not exists vector;    -- For pgvector (embeddings)
create extension if not exists pgcrypto;  -- For UUID generation
```

### 2. Users Table
Stores Instagram user profiles.
```sql
- id: Instagram user ID (bigint)
- ig_username: Instagram username
- language: Preferred language
- attributes: JSON for custom attributes
```

### 3. Threads Table
Conversation threads.
```sql
- id: UUID
- user_id: Foreign key to users
- last_intent: Last classified intent
- status: Thread status
```

### 4. Messages Table
Individual messages in conversations.
```sql
- id: UUID
- thread_id: Foreign key to threads
- role: 'user' | 'assistant' | 'system'
- text: Message content
- meta: JSON metadata
```

### 5. Memory Embeddings Table
Vector embeddings for RAG/semantic search.
```sql
- id: UUID
- user_id: User or 0 for global
- content: Text content
- embedding: vector(384) - 384-dimensional vector
- kind: 'message' | 'faq' | 'knowledge'
```

### 6. Analytics Table
Performance and usage metrics.
```sql
- id: UUID
- thread_id: Foreign key
- latency_ms: Response time
- model: LLM model used
- confidence: Intent confidence
- feedback: JSON feedback data
```

---

## Post-Migration Verification

Run these queries to verify setup:

```sql
-- Check extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'pgcrypto');

-- Check tables exist
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Verify vector column type
SELECT column_name, udt_name, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'memory_embeddings' AND column_name = 'embedding';
-- Should show: embedding | vector | null

-- Test UUID generation
SELECT gen_random_uuid();

-- Test vector operations
SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector AS distance;
```

---

## Connection Pooling (Production)

For high-traffic production, use connection pooling.

### PgBouncer (Recommended)

Most managed services provide this:
- **Neon**: Built-in, use pooled connection string
- **Supabase**: Use port 6543 with `?pgbouncer=true`
- **Railway/Render**: Built-in

### Configure Pool Size

In your app, limit concurrent connections:
```python
# In shared/db.py
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo=POSTGRES_URL,
    min_size=2,
    max_size=10,  # Adjust based on your plan limits
    timeout=30
)
```

---

## Database Maintenance

### Backups

**Managed Services**: Automatic backups included
- Neon: Point-in-time recovery
- Supabase: Daily backups on Pro
- Railway/Render: Automated backups

**Manual Backup:**
```bash
pg_dump POSTGRES_URL > backup-$(date +%Y%m%d).sql

# Restore
psql POSTGRES_URL < backup-20241108.sql
```

### Vacuum & Analyze

PostgreSQL maintenance (usually automatic):
```sql
-- Reclaim space and update statistics
VACUUM ANALYZE;

-- For specific tables
VACUUM ANALYZE messages;
VACUUM ANALYZE memory_embeddings;
```

### Monitor Size

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Table sizes
SELECT 
  table_name,
  pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
```

### Index Maintenance

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Rebuild if needed
REINDEX TABLE messages;
```

---

## Adding Indexes for Performance

For high volume, add these indexes:

```sql
-- Speed up thread lookups
CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads(user_id);

-- Speed up message queries
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- Speed up memory searches
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_user_id ON memory_embeddings(user_id);

-- Vector similarity search (HNSW index for faster queries)
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_vector 
ON memory_embeddings USING hnsw (embedding vector_cosine_ops);
```

Run after your database has significant data.

---

## FAQ Ingestion for RAG

To add knowledge base content:

1. **Create FAQ File**:
   ```markdown
   # docs/faq.md
   
   ## Pricing
   Our basic plan is $10/month...
   
   ## Support
   Contact us at support@...
   ```

2. **Run Ingestion Tool**:
   ```bash
   # Ensure POSTGRES_URL is set
   python -m tools.ingest_faq
   ```

3. **Verify**:
   ```sql
   SELECT content, kind FROM memory_embeddings WHERE user_id = 0;
   ```

Global FAQs (user_id = 0) are available to all users.

---

## Troubleshooting

### "extension vector does not exist"
```sql
-- Check if vector is available
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- If not available, you need a database that supports pgvector
-- Use Neon, Supabase, or pgvector/pgvector Docker image
```

### "connection refused"
- Check POSTGRES_URL is correct
- Verify SSL mode: Add `?sslmode=require` if needed
- Check firewall allows connections
- For managed services, whitelist your IP if required

### "too many connections"
- Use connection pooling
- Check concurrent connections limit for your plan
- Reduce max_size in connection pool

### Performance Issues
- Add indexes (see above)
- Use connection pooling
- Upgrade database plan (more CPU/RAM)
- Check slow queries: `SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;`

---

## Database Setup Checklist

- [ ] Database provisioned (Neon, Supabase, or other)
- [ ] pgvector extension available
- [ ] Connection string obtained
- [ ] POSTGRES_URL set in environment
- [ ] Migration `001_init.sql` executed successfully
- [ ] All tables created (users, threads, messages, memory_embeddings, analytics)
- [ ] Vector column verified
- [ ] Test connection from app works
- [ ] Backups configured (automatic on most platforms)
- [ ] Connection pooling enabled (for production)
- [ ] SSL/TLS enabled
- [ ] Indexes added (if high volume)

---

## Next Steps

After database setup:
1. ✅ Test worker processes messages and stores them
2. ✅ Check dashboard shows analytics
3. ✅ Try semantic search by sending similar messages
4. ✅ Ingest FAQ content for RAG
5. ✅ Monitor database size and performance

Your bot will now have full memory and context capabilities! 🚀
