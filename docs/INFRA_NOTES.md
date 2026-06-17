# EcoTrack — Infrastructure Notes

> **Document version:** 1.0.0  
> **Last reviewed:** 2026-06-17  
> **Maintained by:** EcoTrack Platform Engineering  
> **Audience:** DevOps engineers, engineering leads, finance stakeholders

---

## Table of Contents

1. [Infrastructure Philosophy](#infrastructure-philosophy)
2. [Feature × Paid-Tier Matrix](#feature--paid-tier-matrix)
3. [Free-Tier Fallbacks by Component](#free-tier-fallbacks-by-component)
4. [Monthly Cost Estimate Table](#monthly-cost-estimate-table)
5. [Celery → GitHub Actions Cron Fallback Pattern](#celery--github-actions-cron-fallback-pattern)
6. [AI Coach Cost Model (Claude Haiku)](#ai-coach-cost-model-claude-haiku)
7. [Redis / Upstash Usage Estimate](#redis--upstash-usage-estimate)
8. [Database Sizing](#database-sizing)
9. [Deployment Architecture](#deployment-architecture)
10. [Secrets & Environment Variable Management](#secrets--environment-variable-management)

---

## Infrastructure Philosophy

EcoTrack is designed with a **"free-first, scale-up"** infrastructure strategy:

1. **Every paid component has a working free-tier or self-hosted fallback.** The platform must remain fully functional — if degraded — with zero paid infrastructure spend. This is a budget resilience requirement, not just a cost-saving measure.

2. **No single point of failure on external paid APIs.** The AI coach, email provider, and push notification service each have a deterministic fallback that does not require an external API call.

3. **Async tasks are designed to be runnable as one-shot cron jobs**, not just as long-running Celery workers. This means any task scheduled via Celery can also be triggered by a GitHub Actions scheduled workflow, a systemd timer, or a Railway/Render cron job.

4. **Cost is always bounded.** Every AI, email, and storage cost has a hard cap enforced at the application layer (not just at the provider layer). Surprise bills are a product failure, not a DevOps failure.

---

## Feature × Paid-Tier Matrix

| # | Feature | Requires paid service? | Paid service(s) | Free-tier fallback |
|---|---------|----------------------|-----------------|-------------------|
| 1 | Carbon Footprint Calculator | ❌ No | — | Fully self-contained |
| 2 | Lifestyle Log & History | ❌ No | — | SQLite (dev) / PostgreSQL free tier (prod) |
| 3 | Goal Setting & Streaks | ❌ No | — | Fully self-contained |
| 4 | Social Leaderboard & Friends | ❌ No | — | Fully self-contained |
| 5 | Emissions Breakdown Dashboard | ❌ No | — | Fully self-contained |
| 6 | Weekly Eco-Report (Email) | ⚠️ Soft | SendGrid / Mailgun | Console email backend (dev); SMTP via free Gmail SMTP (small scale) |
| 7 | Offset Marketplace Directory | ❌ No | — | Static directory rendered from DB |
| 8 | AI Eco-Coach (EcoCoach) | ✅ Yes | Anthropic Claude API | Rule-based tip generator (deterministic, zero-cost) |
| 9 | Community Challenges | ❌ No | — | Fully self-contained |
| 10 | Admin Dashboard | ❌ No | — | Fully self-contained |
| — | Async task queue | ⚠️ Soft | Redis (Upstash) + Celery | GitHub Actions cron + management commands |
| — | Cache layer | ⚠️ Soft | Redis (Upstash) | Django in-memory cache (LocMemCache) / DB cache |
| — | File/media storage | ⚠️ Soft | Cloudflare R2 / AWS S3 | Local filesystem (dev) / Whitenoise (static files) |
| — | PostgreSQL | ⚠️ Soft | Neon / Railway / Render | SQLite (dev); Neon has a generous free tier |
| — | Application hosting | ⚠️ Soft | Railway / Render / Fly.io | Local Docker Compose |

**Legend:**  
✅ Yes — feature does not work without this paid service  
⚠️ Soft — free tier available; paid tier needed for scale or reliability  
❌ No — no paid dependency  

---

## Free-Tier Fallbacks by Component

### PostgreSQL (Neon Free Tier)

| Attribute | Neon Free Tier | Notes |
|-----------|---------------|-------|
| Storage | 512 MB | Sufficient for ~50k users at Phase 1 data volume |
| Compute | 0.25 vCPU, 1 GB RAM | Scales to 0 when idle (cold start ~500ms) |
| Connections | 100 | Use PgBouncer (bundled with Neon) |
| Branches | 10 | Use for staging environments |
| Fallback | SQLite | For local dev only; never SQLite in production |

**Connection string pattern:**
```
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/ecotrack?sslmode=require
```

### Redis / Upstash (Free Tier)

See [Redis / Upstash Usage Estimate](#redis--upstash-usage-estimate) section.

### Email (Development & Small-Scale Production)

| Scale | Backend | Config |
|-------|---------|--------|
| Local dev | `django.core.mail.backends.console.EmailBackend` | No config needed |
| CI testing | `django.core.mail.backends.dummy.EmailBackend` | No config needed |
| <500 emails/day | Django SMTP via Gmail | `EMAIL_HOST=smtp.gmail.com`, app password in env |
| Production | SendGrid / Mailgun | `EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend` |

**Fallback rule:** If `SENDGRID_API_KEY` is not set, `settings.py` automatically falls back to the console backend in DEBUG mode and raises a startup warning (not an error) in production.

### AI Coach (Rule-Based Fallback)

When `ANTHROPIC_API_KEY` is absent, the budget cap is reached, or the API returns a non-200 response, `EcoCoachService.get_tip()` falls back to `RuleBasedTipGenerator.generate()`. See [AI Coach Cost Model](#ai-coach-cost-model-claude-haiku) for full details.

### Static & Media Files

| Environment | Static files | Media files |
|-------------|-------------|-------------|
| Local dev | Django dev server (`runserver`) | `MEDIA_ROOT` on local disk |
| Production (free) | Whitenoise (`whitenoise.middleware.WhiteNoiseMiddleware`) | Local disk (not suitable for multi-instance) |
| Production (scaled) | Cloudflare R2 or AWS S3 via `django-storages` | Same bucket |

**Whitenoise** serves compressed, cache-busted static files with zero additional infrastructure. Suitable up to approximately 10k daily active users on a single-instance deployment.

---

## Monthly Cost Estimate Table

> All figures in **USD/month**. Assumes Railway hobby plan for hosting ($5/month base), Neon free tier for DB, Upstash free tier for Redis. AI cost is the dominant variable.

### At 1,000 Monthly Active Users (MAU)

| Component | Service | Cost |
|-----------|---------|------|
| App hosting (1 instance) | Railway Hobby | $5.00 |
| PostgreSQL | Neon Free | $0.00 |
| Redis / cache | Upstash Free (10k req/day) | $0.00 |
| Email (weekly digest × 1k) | SendGrid Free (100/day) | $0.00 |
| AI Coach (1 call/user/week × 1k users × 4 weeks) | Claude Haiku | ~$0.08 |
| CDN / static files | Cloudflare Free | $0.00 |
| Domain | Namecheap | ~$1.00 |
| **Total** | | **~$6.08/month** |

*AI cost calculation: 4,000 calls/month × ~500 input tokens × $0.00025/1k tokens + 4,000 calls × ~300 output tokens × $0.00125/1k tokens = $0.50 input + $1.50 output = ~$2.00. With hard cap at 4,000 calls, total AI cost ≤ $2.00.*

*Note: The $0.08 figure above uses conservative average token counts; see [AI Coach Cost Model](#ai-coach-cost-model-claude-haiku) for precise calculation.*

### At 10,000 Monthly Active Users (MAU)

| Component | Service | Cost |
|-----------|---------|------|
| App hosting (2 instances) | Railway Pro | $20.00 |
| PostgreSQL | Neon Pro (2 GB) | $19.00 |
| Redis / cache | Upstash Pay-as-you-go | ~$3.00 |
| Email (weekly digest × 10k) | SendGrid Essentials (50k/month) | $19.95 |
| AI Coach (1 call/user/week × 10k × 4 weeks) | Claude Haiku | ~$20.00 |
| CDN / static files | Cloudflare Free | $0.00 |
| Media storage (avatars, exports) | Cloudflare R2 (10 GB) | $0.15 |
| Domain + SSL | Namecheap | ~$1.00 |
| **Total** | | **~$83/month** |

### At 100,000 Monthly Active Users (MAU)

| Component | Service | Cost |
|-----------|---------|------|
| App hosting (4–8 instances, autoscale) | Railway Pro / Fly.io | ~$150.00 |
| PostgreSQL | Neon Pro (10 GB) or dedicated RDS | ~$69.00 |
| Redis / cache | Upstash Pro or ElastiCache | ~$25.00 |
| Celery workers (2–4 workers) | Railway | ~$40.00 |
| Email (weekly digest × 100k) | SendGrid Pro (100k/month) | $89.95 |
| AI Coach (hard weekly cap per user; assume 30% active) | Claude Haiku | ~$180.00 |
| CDN | Cloudflare Pro | $20.00 |
| Media storage (100 GB) | Cloudflare R2 | $1.50 |
| Monitoring (Sentry, Grafana Cloud) | Free tiers initially | ~$0.00 |
| Domain + SSL | Namecheap | ~$1.00 |
| **Total** | | **~$576/month** |

**Cost per MAU at scale:** ~$0.006/user/month at 100k MAU. Dominated by email (~$0.0009/user) and AI (~$0.0018/user/month at 30% active).

---

## Celery → GitHub Actions Cron Fallback Pattern

### Why this pattern exists

Running a persistent Celery worker 24/7 costs money and requires a Redis broker. For periodic tasks (weekly digest emails, challenge result aggregation, leaderboard refresh), a scheduled GitHub Actions workflow or a platform cron job (Railway, Render) is equally effective and costs nothing on the free tier.

### Design constraint

Every async task scheduled via Celery **must** be expressible as a Django management command that can be run as a one-shot process:

```
python manage.py send_weekly_digests
python manage.py aggregate_challenge_results
python manage.py refresh_leaderboard_cache
python manage.py cleanup_expired_sessions
```

### Celery configuration (production, when Redis is available)

```python
# ecotrack/celery.py
CELERY_BEAT_SCHEDULE = {
    "send_weekly_digests": {
        "task": "notifications.tasks.send_weekly_digest_emails",
        "schedule": crontab(hour=8, minute=0, day_of_week="monday"),
    },
    "aggregate_challenge_results": {
        "task": "challenges.tasks.aggregate_daily_challenge_progress",
        "schedule": crontab(hour=23, minute=55),
    },
    "refresh_leaderboard_cache": {
        "task": "social.tasks.refresh_leaderboard_cache",
        "schedule": crontab(minute="*/15"),  # every 15 minutes
    },
    "prune_old_ai_usage_stats": {
        "task": "ai_coach.tasks.prune_old_ai_usage_stats",
        "schedule": crontab(hour=2, minute=0, day_of_week="sunday"),
    },
}
```

### GitHub Actions cron fallback (when Redis/Celery is unavailable)

```yaml
# .github/workflows/cron_tasks.yml
name: Scheduled Tasks (Celery Fallback)

on:
  schedule:
    - cron: "0 8 * * 1"   # Weekly digest — Monday 08:00 UTC
    - cron: "55 23 * * *"  # Daily challenge aggregation — 23:55 UTC
    - cron: "0 2 * * 0"    # Weekly AI stat pruning — Sunday 02:00 UTC
  workflow_dispatch:        # Allow manual trigger for testing

jobs:
  weekly-digest:
    if: github.event.schedule == '0 8 * * 1' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python manage.py send_weekly_digests --dry-run=${{ vars.DRY_RUN || 'false' }}
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          EMAIL_HOST_USER: ${{ secrets.EMAIL_HOST_USER }}
          EMAIL_HOST_PASSWORD: ${{ secrets.EMAIL_HOST_PASSWORD }}
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
          DJANGO_SECRET_KEY: ${{ secrets.DJANGO_SECRET_KEY }}
          DJANGO_SETTINGS_MODULE: ecotrack.settings.production
```

### Task idempotency requirement

All management commands used in this pattern **must be idempotent**: running them twice in the same window must not send duplicate emails, double-count challenge progress, or create duplicate records. Implementation pattern:

```python
# notifications/management/commands/send_weekly_digests.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        week_start = get_current_week_start()
        # Idempotency guard: skip users who already received digest this week
        users = User.objects.filter(
            email_opt_in=True,
            last_digest_sent_at__lt=week_start,  # not yet sent this week
        )
        for user in users.iterator(chunk_size=100):
            send_digest_for_user(user)
            user.last_digest_sent_at = now()
            user.save(update_fields=["last_digest_sent_at"])
```

### Decision logic (runtime)

```
settings.CELERY_BROKER_URL set?
  ├── YES → Use Celery Beat for scheduling
  └── NO  → Log warning at startup; fall back to GitHub Actions cron
              (or manual management command invocation)
```

---

## AI Coach Cost Model (Claude Haiku)

### Pricing basis (as of 2024-Q1)

| Model | Input tokens | Output tokens |
|-------|-------------|---------------|
| Claude 3 Haiku | $0.25 / 1M tokens | $1.25 / 1M tokens |

*Always verify current pricing at: https://www.anthropic.com/pricing*

### Token budget per request

| Component | Tokens (est.) | Notes |
|-----------|--------------|-------|
| System prompt | ~400 | Fixed, cached by Anthropic prompt caching |
| User footprint context | ~200 | Serialised JSON footprint breakdown |
| User question / prompt | ~100 | Max enforced by frontend character limit |
| **Total input** | **~700** | |
| Response | ~350 | Max enforced by `max_tokens=500` parameter |

### Cost per API call

```
Input cost:  700 tokens × $0.25/1M  = $0.000175
Output cost: 350 tokens × $1.25/1M  = $0.000438
Total/call:                          = $0.000613
```

### Rate limiting implementation

```
┌──────────────────────────────────────────────────────────┐
│                   Rate Limit Enforcement                 │
│                                                          │
│  1. Request arrives at EcoCoachView                      │
│                                                          │
│  2. Check DB: AiUsageStat.objects.filter(                │
│       user=request.user,                                 │
│       week_start=current_week_start(),                   │
│     ).exists()                                           │
│                                                          │
│     ├── EXISTS → Return cached tip (or 429 with msg)     │
│     └── NOT EXISTS → Proceed to step 3                   │
│                                                          │
│  3. Check Redis (if available): user:{id}:ai_called_week │
│     ├── KEY EXISTS → Return 429 (double-check guard)     │
│     └── KEY ABSENT → Proceed to step 4                   │
│                                                          │
│  4. Call Anthropic API                                   │
│     ├── SUCCESS → Save AiUsageStat, set Redis key (TTL   │
│     │            = seconds until next Monday 00:00)      │
│     │            → Return tip to user                    │
│     └── FAILURE → Log error, return rule-based tip       │
│                                                          │
│  5. Admin dashboard: aggregate AiUsageStat by day/week   │
│     → alert if daily_cost > DAILY_AI_COST_ALERT_USD      │
└──────────────────────────────────────────────────────────┘
```

**Why DB + Redis double-check?**  
Redis is ephemeral. If Redis is flushed or unavailable, the DB check prevents unlimited AI calls. The DB record is the authoritative source of truth for rate limiting. Redis is only a fast pre-check to avoid a DB hit on every request.

### Hard weekly cap calculation

| MAU | Active AI users (est. 40%) | Calls/week | Cost/week | Cost/month |
|-----|--------------------------|------------|-----------|-----------|
| 1,000 | 400 | 400 | $0.25 | $1.00 |
| 10,000 | 4,000 | 4,000 | $2.45 | $9.80 |
| 100,000 | 40,000 | 40,000 | $24.52 | $98.08 |

**Hard cap setting:** `AI_WEEKLY_CALL_CAP` environment variable. When the platform-wide weekly total reaches this cap, all subsequent AI coach requests fall back to the rule-based generator and an admin alert is triggered. Default: 50,000 calls/week.

### Rule-based tip generator fallback

`RuleBasedTipGenerator` maintains a curated dictionary of ~80 tips keyed by (primary_category, diet_type, transport_mode). It selects a tip deterministically based on the user's top-emission category, rotated by week number to avoid repetition. Zero API calls, zero cost.

```python
# ai_coach/rule_based.py
class RuleBasedTipGenerator:
    """Deterministic tip generator used when AI API is unavailable or capped."""

    def generate(self, footprint_summary: FootprintSummary, week_number: int) -> str:
        """Return a tip string for the user's primary emission category."""
        category = footprint_summary.primary_category
        tips = TIP_LIBRARY.get(category, TIP_LIBRARY["general"])
        index = week_number % len(tips)
        return tips[index]
```

---

## Redis / Upstash Usage Estimate

### Upstash Free Tier Limits

| Limit | Value |
|-------|-------|
| Requests per day | 10,000 |
| Max data size | 256 MB |
| Max commands per second | 1,000 |
| Regions | 1 |

### EcoTrack Redis Usage by Feature

| Usage type | Key pattern | TTL | Estimated volume |
|-----------|------------|-----|-----------------|
| AI rate limit guard | `user:{id}:ai_called_week` | Until next Monday | 1 key/active AI user/week |
| Session cache | `session:{key}` | 2 weeks | 1 key/active session |
| Leaderboard cache | `leaderboard:{group_id}` | 15 minutes | 1 key/active group |
| Challenge aggregate cache | `challenge:{id}:progress` | 1 hour | 1 key/active challenge |
| Email dedup guard | `digest_sent:{user_id}:{week}` | 8 days | 1 key/user receiving digest |
| Django cache (misc) | `cache:{key}` | Varies | Low volume |

### Request volume estimate (1k MAU)

| Operation | Frequency | Daily requests |
|-----------|-----------|---------------|
| Session reads (page loads) | 5 page loads/active user/day × 400 DAU | 2,000 |
| Leaderboard cache reads | 2 reads/active user/day | 800 |
| AI rate check reads | 1/active AI user/day × 57 (400/7) | 57 |
| Cache writes | ~20% of reads | 571 |
| **Total** | | **~3,428/day** |

**Conclusion:** At 1k MAU, daily requests (~3,400) are well within the Upstash free tier (10,000/day). Paid tier becomes necessary at approximately 3k MAU.

### At 10k MAU

Estimated ~34,000 requests/day → requires Upstash Pay-as-you-go (~$3/month).

### Fallback when Redis is unavailable

```python
# ecotrack/cache.py
def get_cache_backend() -> BaseCache:
    """Return Redis cache if available, else in-memory cache."""
    if settings.REDIS_URL:
        return RedisCache(settings.REDIS_URL, {})
    return LocMemCache("ecotrack_fallback", {})
```

All cache operations use `django.core.cache.cache` (the configured default cache). If `REDIS_URL` is not set, Django automatically uses `LocMemCache` (in-memory, per-process). This means leaderboard caches won't be shared across multiple worker processes, but the platform remains functional.

---

## Database Sizing

### Row count estimates (per 1k MAU)

| Table | Rows/user | Total rows (1k MAU) | Avg row size | Total size |
|-------|----------|---------------------|-------------|-----------|
| `users_user` | 1 | 1,000 | 500 B | 0.5 MB |
| `emissions_footprintentry` | 30/month × 12 | 360,000 | 800 B | 288 MB |
| `emissions_emissionfactor` | — | ~500 | 300 B | 0.15 MB |
| `goals_goal` | 3 avg | 3,000 | 400 B | 1.2 MB |
| `social_friendship` | 5 avg | 5,000 | 200 B | 1 MB |
| `challenges_challengemembership` | 2 avg | 2,000 | 300 B | 0.6 MB |
| `ai_coach_aiusagestat` | 52/year | 52,000 | 400 B | 20.8 MB |
| `notifications_notificationlog` | 52/year | 52,000 | 300 B | 15.6 MB |
| **Total (1k MAU, 1 year)** | | | | **~328 MB** |

**PostgreSQL index overhead:** Approximately 30% on top of data size → ~425 MB total for 1k MAU after 1 year.  
**Neon free tier (512 MB):** Sufficient for ~1,200 MAU for 1 year. Neon's free storage limit triggers a warning at 75%; upgrade to Neon Launch ($19/month, 10 GB) is recommended at ~1,000 MAU.

---

## Deployment Architecture

```
                        ┌─────────────────────────────┐
                        │      Cloudflare CDN          │
                        │   (static files, DDoS)       │
                        └──────────────┬──────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │    Railway / Fly.io          │
                        │   Django ASGI (Gunicorn)     │
                        │   + Whitenoise (static)      │
                        └─────┬──────────────┬─────────┘
                              │              │
               ┌──────────────▼──┐    ┌──────▼──────────────┐
               │  Neon PostgreSQL │    │  Upstash Redis       │
               │  (primary DB)    │    │  (cache + broker)    │
               └─────────────────┘    └─────────────────────┘
                              │
               ┌──────────────▼──────────────┐
               │  Celery Worker (optional)    │
               │  OR GitHub Actions Cron      │
               │  (weekly digest, aggregation)│
               └─────────────────────────────┘
                              │
               ┌──────────────▼──────────────┐
               │  Anthropic Claude API        │
               │  (EcoCoach, rate-limited)    │
               └─────────────────────────────┘
```

### Single-process deployment (Phase 1 default)

For simplicity and cost, Phase 1 runs everything in a single Railway process:

- **Web:** `gunicorn ecotrack.wsgi:application --workers 2 --bind 0.0.0.0:$PORT`
- **Async tasks:** GitHub Actions cron (no Celery worker process)
- **Cache:** Upstash Redis (or in-memory fallback)

When traffic warrants it (>5k MAU), a separate Celery worker process is added.

---

## Secrets & Environment Variable Management

All secrets are stored in **Railway environment variables** (production) and **`.env` file** (local development, gitignored). Never hardcoded.

### Complete environment variable reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | ✅ | — | Django secret key (50+ chars) |
| `DJANGO_SETTINGS_MODULE` | ✅ | `ecotrack.settings.development` | Settings module path |
| `DJANGO_DEBUG` | ❌ | `False` | Enable Django debug mode |
| `ALLOWED_HOSTS` | ✅ | `localhost` | Comma-separated allowed hosts |
| `DATABASE_URL` | ✅ | `sqlite:///db.sqlite3` | PostgreSQL / SQLite URL |
| `REDIS_URL` | ❌ | `None` | Upstash Redis URL (omit for in-memory cache) |
| `ANTHROPIC_API_KEY` | ❌ | `None` | Claude API key (omit for rule-based fallback) |
| `AI_WEEKLY_CALL_CAP` | ❌ | `50000` | Platform-wide weekly AI call hard cap |
| `AI_DAILY_COST_ALERT_USD` | ❌ | `10.0` | Trigger admin alert above this daily AI spend |
| `SENDGRID_API_KEY` | ❌ | `None` | SendGrid API key for transactional email |
| `EMAIL_HOST` | ❌ | `smtp.gmail.com` | SMTP host (fallback) |
| `EMAIL_HOST_USER` | ❌ | `None` | SMTP username |
| `EMAIL_HOST_PASSWORD` | ❌ | `None` | SMTP password |
| `DEFAULT_FROM_EMAIL` | ❌ | `noreply@ecotrack.app` | Sender email address |
| `CLOUDFLARE_R2_ACCESS_KEY` | ❌ | `None` | R2 access key (omit for local file storage) |
| `CLOUDFLARE_R2_SECRET_KEY` | ❌ | `None` | R2 secret key |
| `CLOUDFLARE_R2_BUCKET_NAME` | ❌ | `None` | R2 bucket name |
| `SENTRY_DSN` | ❌ | `None` | Sentry error tracking DSN |
| `CORS_ALLOWED_ORIGINS` | ❌ | `http://localhost:3000` | CORS allowed origins |

### `.env.example` template

A `.env.example` file is committed to the repository. Developers copy it to `.env` and fill in their values. The `.env` file is gitignored globally.

---

*End of INFRA_NOTES.md — EcoTrack v1.0.0*
