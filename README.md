# 🌿 EcoTrack

> **Measure. Reduce. Connect.**  
> A production-grade personal carbon footprint tracking platform built with Django REST Framework and React.

[![CI](https://github.com/your-org/ecotrack/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/ecotrack/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-org/ecotrack/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/ecotrack)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![Django 5.x](https://img.shields.io/badge/django-5.x-green.svg)](https://djangoproject.com)

---

## Table of Contents

- [What is EcoTrack?](#what-is-ecotrack)
- [Value Proposition](#value-proposition)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start — Local Development](#quick-start--local-development)
- [Environment Variables Reference](#environment-variables-reference)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Build Phases Roadmap](#build-phases-roadmap)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

---

## What is EcoTrack?

EcoTrack is an open-source platform that helps individuals measure their personal carbon footprint across seven life domains (electricity, diet, transport, flights, home energy, consumer devices, and waste), track their progress over time, engage with friends and community challenges, and receive AI-powered personalised reduction advice.

It is designed to be:

- **Scientifically grounded** — all emission factors sourced from peer-reviewed literature and government datasets (see [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md)).
- **Ethically designed** — no dark patterns, no manipulative gamification, no offset sales. See [`docs/PROBLEM_STATEMENT.md`](docs/PROBLEM_STATEMENT.md).
- **Infrastructure-efficient** — runs on free tiers at small scale; every paid component has a working free-tier fallback (see [`docs/INFRA_NOTES.md`](docs/INFRA_NOTES.md)).
- **AI-safe** — rate-limited, sanitised, grounded AI coaching with transparent safety policies (see [`docs/AI_SAFETY_NOTES.md`](docs/AI_SAFETY_NOTES.md)).

---

## Value Proposition

| Problem | EcoTrack Solution |
|---------|------------------|
| People can't accurately quantify their footprint | Science-backed, category-level calculator with uncertainty ranges |
| One-time measurement doesn't drive sustained change | Continuous lifestyle logging, goal tracking, and weekly feedback loops |
| Individual action feels futile | Social leaderboard, community challenges, and aggregate impact visualisation |
| Generic advice doesn't stick | AI Eco-Coach personalised to the user's actual footprint profile |
| Offset market is opaque and untrustworthy | Curated informational directory — no sales, no affiliate links |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                  │
│                                                                         │
│   React SPA (Vite + TypeScript)    Mobile Browser (PWA-ready)           │
│   ├── Footprint Calculator         ├── Responsive Tailwind UI           │
│   ├── Lifestyle Log                └── Offline-capable (Phase 2)        │
│   ├── Dashboard & Charts                                                │
│   ├── Social Leaderboard                                                │
│   └── EcoCoach UI                                                       │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │  HTTPS / REST API (JSON)
                                │  + JWT Authentication
┌───────────────────────────────▼─────────────────────────────────────────┐
│                           API LAYER                                     │
│                                                                         │
│   Django 5 + Django REST Framework                                      │
│   ├── /api/v1/auth/          JWT auth (SimpleJWT)                       │
│   ├── /api/v1/emissions/     Footprint calculation & logging            │
│   ├── /api/v1/goals/         Goal management                            │
│   ├── /api/v1/social/        Friends & leaderboard                      │
│   ├── /api/v1/challenges/    Community challenges                       │
│   ├── /api/v1/coach/         EcoCoach AI tips (rate-limited)            │
│   ├── /api/v1/offsets/       Offset directory (read-only)               │
│   └── /api/v1/notifications/ Preferences & digest history               │
│                                                                         │
│   Gunicorn (WSGI) │ Whitenoise (static)                                 │
└──────────┬────────┴──────────────────────────────────────────────────── ┘
           │                              │                    │
┌──────────▼─────────┐    ┌───────────────▼──────┐  ┌─────────▼──────────┐
│  PostgreSQL (Neon)  │    │  Redis (Upstash)      │  │  Anthropic Claude  │
│  Primary datastore  │    │  Cache + rate-limit   │  │  AI Coach API      │
│  - User profiles    │    │  guard + Celery       │  │  (rate-limited,    │
│  - Footprint logs   │    │  broker (optional)    │  │   fallback avail.) │
│  - Goals, streaks   │    └───────────────────────┘  └────────────────────┘
│  - AI usage stats   │
│  - Challenge data   │    ┌──────────────────────────────────────────────┐
└─────────────────────┘    │  Async Tasks                                 │
                           │  Celery Beat (if Redis available)            │
                           │  OR GitHub Actions Cron (fallback)           │
                           │  ├── Weekly digest emails                    │
                           │  ├── Challenge aggregation                   │
                           │  └── Leaderboard cache refresh               │
                           └──────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend framework | Django | 5.x |
| REST API | Django REST Framework | 3.15.x |
| Authentication | SimpleJWT | 5.x |
| Database | PostgreSQL (Neon free tier) | 16 |
| Cache / broker | Redis (Upstash) | 7.x |
| Task queue | Celery | 5.x |
| AI | Anthropic Claude 3 Haiku | API v1 |
| Email | SendGrid (Anymail) / SMTP | — |
| Frontend | React + Vite + TypeScript | React 18 |
| Styling | Tailwind CSS | 3.x |
| Charts | Recharts | 2.x |
| Hosting | Railway / Fly.io / Render | — |
| CI/CD | GitHub Actions | — |

---

## Prerequisites

Ensure the following are installed on your development machine:

| Tool | Minimum version | Installation |
|------|----------------|-------------|
| Python | 3.12 | [python.org](https://python.org) |
| Node.js | 20 LTS | [nodejs.org](https://nodejs.org) |
| PostgreSQL | 15+ | [postgresql.org](https://postgresql.org) or use Docker |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |
| Docker (optional) | 24+ | [docker.com](https://docker.com) |

Optional but recommended:

- **Redis** (local) for full async task support — or use Upstash free tier.
- **Anthropic API key** for AI coach features — platform degrades gracefully without it.

---

## Quick Start — Local Development

### 1. Clone the repository

```bash
git clone https://github.com/your-org/ecotrack.git
cd ecotrack
```

### 2. Set up the Python environment

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows PowerShell

# Install Python dependencies
pip install -r requirements/development.txt
```

### 3. Configure environment variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your values (see Environment Variables Reference below)
# At minimum, set DJANGO_SECRET_KEY
```

### 4. Set up the database

```bash
# Run migrations
python manage.py migrate

# Load initial emission factor data
python manage.py loaddata fixtures/emission_factors.json
python manage.py loaddata fixtures/offset_projects.json

# (Optional) Load sample development data
python manage.py loaddata fixtures/sample_data.json

# Create a superuser for the admin panel
python manage.py createsuperuser
```

### 5. Start the development server

```bash
# Terminal 1 — Django backend (API)
python manage.py runserver

# Terminal 2 — React frontend (optional, for full-stack development)
cd frontend
npm install
npm run dev
```

**API:** http://localhost:8000/api/v1/  
**Admin panel:** http://localhost:8000/admin/  
**Frontend (if started):** http://localhost:5173/  
**API Docs (Swagger):** http://localhost:8000/api/schema/swagger-ui/  

### 6. (Optional) Start Celery worker and beat

```bash
# Requires Redis — set REDIS_URL in .env first

# Terminal 3 — Celery worker
celery -A ecotrack worker --loglevel=info

# Terminal 4 — Celery beat (task scheduler)
celery -A ecotrack beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 7. (Optional) Docker Compose — full stack

```bash
# Start all services (Django, PostgreSQL, Redis, Celery)
docker compose up --build

# In a separate terminal, run initial setup
docker compose exec web python manage.py migrate
docker compose exec web python manage.py loaddata fixtures/emission_factors.json
docker compose exec web python manage.py createsuperuser
```

---

## Environment Variables Reference

Copy `.env.example` to `.env` and fill in the values. Variables marked **Required** must be set; others have safe defaults for local development.

### Core Django

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | ✅ | — | 50+ character random string. Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_SETTINGS_MODULE` | ✅ | `ecotrack.settings.development` | Settings module. Use `ecotrack.settings.production` in production. |
| `DJANGO_DEBUG` | ❌ | `True` (dev) / `False` (prod) | Never set to `True` in production. |
| `ALLOWED_HOSTS` | ✅ | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames. |
| `CORS_ALLOWED_ORIGINS` | ❌ | `http://localhost:5173` | Comma-separated list of allowed CORS origins. |

### Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | `sqlite:///db.sqlite3` | Full database URL. PostgreSQL example: `postgresql://user:pass@host:5432/ecotrack` |

### Cache & Task Queue

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | ❌ | `None` | Redis connection URL. Example: `redis://default:token@upstash-host:6379`. If unset, falls back to in-memory cache and GitHub Actions cron instead of Celery. |

### AI Coach

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ❌ | `None` | Anthropic API key. If unset, AI coach falls back to rule-based tip generator. |
| `AI_WEEKLY_CALL_CAP` | ❌ | `50000` | Platform-wide maximum AI API calls per week. |
| `AI_DAILY_COST_ALERT_USD` | ❌ | `10.0` | Send admin alert when daily AI cost exceeds this amount in USD. |
| `AI_API_TIMEOUT_SECONDS` | ❌ | `10` | Timeout for Anthropic API calls in seconds. |

### Email

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENDGRID_API_KEY` | ❌ | `None` | SendGrid API key. If unset, falls back to SMTP or console backend. |
| `EMAIL_HOST` | ❌ | `smtp.gmail.com` | SMTP host for fallback email. |
| `EMAIL_PORT` | ❌ | `587` | SMTP port. |
| `EMAIL_HOST_USER` | ❌ | `None` | SMTP username. |
| `EMAIL_HOST_PASSWORD` | ❌ | `None` | SMTP password or app password. |
| `DEFAULT_FROM_EMAIL` | ❌ | `noreply@ecotrack.app` | Default sender email address. |

### File Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLOUDFLARE_R2_ACCESS_KEY` | ❌ | `None` | Cloudflare R2 access key. If unset, uses local file storage. |
| `CLOUDFLARE_R2_SECRET_KEY` | ❌ | `None` | Cloudflare R2 secret key. |
| `CLOUDFLARE_R2_BUCKET_NAME` | ❌ | `None` | Cloudflare R2 bucket name. |
| `CLOUDFLARE_R2_ENDPOINT_URL` | ❌ | `None` | Cloudflare R2 endpoint URL. |

### Monitoring

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | ❌ | `None` | Sentry DSN for error tracking. |

---

## Running Tests

EcoTrack uses **pytest** with **pytest-django** and **pytest-cov** for testing.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=ecotrack --cov-report=term-missing

# Run a specific app's tests
pytest ecotrack/emissions/tests/

# Run a specific test file
pytest ecotrack/emissions/tests/test_calculator.py

# Run tests matching a keyword
pytest -k "test_diet_calculation"

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run only fast unit tests (exclude slow integration tests)
pytest -m "not slow"

# Generate HTML coverage report
pytest --cov=ecotrack --cov-report=html
open htmlcov/index.html
```

### Test categories

| Marker | Description | Command |
|--------|-------------|---------|
| (no marker) | Fast unit tests | `pytest` |
| `@pytest.mark.slow` | Integration tests, DB-heavy tests | `pytest -m slow` |
| `@pytest.mark.integration` | End-to-end API tests | `pytest -m integration` |
| `@pytest.mark.ai` | AI coach tests (requires mock) | `pytest -m ai` |

### Test configuration

Tests use an in-memory SQLite database by default. The `conftest.py` at the project root provides:
- A `client` fixture (DRF `APIClient`)
- A `user_factory` fixture for creating test users
- A `footprint_factory` fixture for creating test footprint entries
- A `mock_anthropic` fixture for mocking the Anthropic API client

### Minimum coverage targets

| Module | Target |
|--------|--------|
| `emissions/` (calculator engine) | 95% |
| `ai_coach/` (rate limiting, sanitisation) | 90% |
| `notifications/` | 85% |
| `social/` | 80% |
| Overall | 80% |

CI fails if overall coverage drops below **80%**.

---

## Project Structure

```
ecotrack/                          # Django project root
│
├── ecotrack/                      # Project configuration package
│   ├── settings/
│   │   ├── base.py                # Shared settings
│   │   ├── development.py         # Local dev overrides
│   │   ├── production.py          # Production settings
│   │   └── testing.py             # Test-specific settings
│   ├── urls.py                    # Root URL configuration
│   ├── celery.py                  # Celery application config
│   └── wsgi.py                    # WSGI entry point
│
├── emissions/                     # Footprint calculation engine
│   ├── models.py                  # EmissionFactor, FootprintEntry, FootprintSummary
│   ├── serializers.py             # DRF serializers
│   ├── services.py                # FootprintCalculatorService
│   ├── views.py                   # API views (thin — no business logic)
│   ├── urls.py
│   ├── constants.py               # Emission factor values by category/version
│   ├── ar5_to_ar6_conversion.py   # GWP conversion utilities
│   ├── management/
│   │   └── commands/
│   │       └── recalculate_footprints.py
│   ├── migrations/
│   └── tests/
│       ├── test_calculator.py
│       ├── test_models.py
│       └── test_views.py
│
├── goals/                         # Goal setting and streak tracking
│   ├── models.py                  # Goal, GoalProgress, Streak
│   ├── serializers.py
│   ├── services.py                # GoalService, StreakService
│   ├── views.py
│   ├── urls.py
│   ├── migrations/
│   └── tests/
│
├── social/                        # Friends, leaderboard
│   ├── models.py                  # Friendship, LeaderboardEntry
│   ├── serializers.py
│   ├── services.py                # LeaderboardService
│   ├── views.py
│   ├── urls.py
│   ├── tasks.py                   # refresh_leaderboard_cache (Celery task)
│   ├── migrations/
│   └── tests/
│
├── challenges/                    # Community challenges
│   ├── models.py                  # Challenge, ChallengeMembership, ChallengeProgress
│   ├── serializers.py
│   ├── services.py                # ChallengeService
│   ├── views.py
│   ├── urls.py
│   ├── tasks.py                   # aggregate_daily_challenge_progress
│   ├── migrations/
│   └── tests/
│
├── ai_coach/                      # EcoCoach AI feature
│   ├── models.py                  # AiUsageStat
│   ├── serializers.py
│   ├── services.py                # EcoCoachService (AI + rate limiting)
│   ├── rule_based.py              # RuleBasedTipGenerator (zero-cost fallback)
│   ├── sanitisation.py            # AI output sanitisation (bleach)
│   ├── views.py
│   ├── urls.py
│   ├── prompts/
│   │   └── system.txt             # EcoCoach system prompt template
│   ├── tasks.py                   # prune_old_ai_usage_stats
│   ├── migrations/
│   └── tests/
│       ├── test_rate_limiting.py
│       ├── test_sanitisation.py
│       └── test_rule_based.py
│
├── notifications/                 # Email digests and in-app notifications
│   ├── models.py                  # NotificationPreference, NotificationLog
│   ├── serializers.py
│   ├── services.py                # NotificationService
│   ├── views.py                   # Opt-out endpoint
│   ├── urls.py
│   ├── tasks.py                   # send_weekly_digest_emails
│   ├── templates/
│   │   └── email/
│   │       ├── weekly_digest.html
│   │       └── weekly_digest.txt  # Plain-text fallback
│   ├── management/
│   │   └── commands/
│   │       └── send_weekly_digests.py
│   ├── migrations/
│   └── tests/
│
├── offsets/                       # Offset marketplace directory (read-only)
│   ├── models.py                  # OffsetProject, OffsetStandard
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── migrations/
│   └── tests/
│
├── users/                         # Custom user model and auth
│   ├── models.py                  # User (AbstractBaseUser)
│   ├── serializers.py
│   ├── services.py                # UserService
│   ├── views.py
│   ├── urls.py
│   ├── migrations/
│   └── tests/
│
├── admin_dashboard/               # Admin UI extensions
│   ├── views.py                   # AI usage dashboard, analytics
│   ├── urls.py
│   └── tests/
│
├── frontend/                      # React + Vite + TypeScript SPA
│   ├── src/
│   │   ├── api/                   # Axios API client
│   │   ├── components/            # Shared UI components
│   │   ├── features/              # Feature-level components
│   │   │   ├── calculator/
│   │   │   ├── dashboard/
│   │   │   ├── goals/
│   │   │   ├── social/
│   │   │   ├── coach/
│   │   │   └── challenges/
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── store/                 # Zustand state management
│   │   ├── types/                 # TypeScript types
│   │   └── utils/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── fixtures/                      # Django fixtures for initial data
│   ├── emission_factors.json
│   ├── offset_projects.json
│   └── sample_data.json           # Development sample data (gitignored in prod)
│
├── docs/                          # Project documentation
│   ├── DATA_SOURCES.md
│   ├── PROBLEM_STATEMENT.md
│   ├── INFRA_NOTES.md
│   └── AI_SAFETY_NOTES.md
│
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Test, lint, coverage on PR
│       ├── deploy.yml             # Deploy to Railway on main merge
│       └── cron_tasks.yml         # Celery fallback cron jobs
│
├── requirements/
│   ├── base.txt                   # Production dependencies
│   ├── development.txt            # Dev + test dependencies
│   └── testing.txt                # CI-only dependencies
│
├── docker-compose.yml             # Local full-stack development
├── Dockerfile
├── .env.example                   # Environment variable template
├── pyproject.toml                 # Ruff, mypy, pytest configuration
├── manage.py
└── README.md
```

---

## Build Phases Roadmap

### ✅ Phase 1 — Foundation (Current)

**Goal:** Core tracking, social features, and AI coach. Production-ready on free tiers.

| Feature | Status |
|---------|--------|
| Carbon Footprint Calculator (7 categories) | ✅ Complete |
| Lifestyle Log & History | ✅ Complete |
| Goal Setting & Streaks | ✅ Complete |
| Social Leaderboard & Friends | ✅ Complete |
| Emissions Breakdown Dashboard | ✅ Complete |
| Weekly Eco-Report (Email Digest) | ✅ Complete |
| Offset Marketplace Directory | ✅ Complete |
| AI Eco-Coach (EcoCoach) | ✅ Complete |
| Community Challenges | ✅ Complete |
| Admin & Transparency Dashboard | ✅ Complete |

### 🔄 Phase 2 — Mobile & Integrations (Q3 2025)

| Feature | Description |
|---------|-------------|
| Progressive Web App (PWA) | Offline support, install prompt, push notifications |
| Receipt scanning (OCR) | Estimate purchase footprint from photographed receipts |
| Smart meter integration | UK SMETS2 / US Green Button API for automatic electricity data |
| Google Maps integration | Auto-detect commute route for transport footprint estimation |
| Strava / fitness app sync | Import cycling/walking distances as negative transport offsets |
| Wearable device integration | Estimate transport mode from motion data |

### 🔮 Phase 3 — Enterprise & Policy (Q1 2026)

| Feature | Description |
|---------|-------------|
| Employer/school group accounts | Organisation-level dashboards without individual surveillance |
| Municipality partnerships | City-level challenge campaigns |
| Open API | Third-party integrations and data export |
| Carbon literacy certification | Gamified learning paths with shareable credentials |
| Policy advocacy module | Link footprint categories to relevant local/national policy campaigns |

---

## API Documentation

### Interactive docs

- **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/  
- **ReDoc:** http://localhost:8000/api/schema/redoc/  
- **OpenAPI schema (JSON):** http://localhost:8000/api/schema/

### Authentication

EcoTrack uses JWT authentication (SimpleJWT). All authenticated endpoints require an `Authorization: Bearer <access_token>` header.

```bash
# Obtain tokens
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'

# Response:
# { "access": "eyJ...", "refresh": "eyJ..." }

# Use access token
curl http://localhost:8000/api/v1/emissions/footprint/ \
  -H "Authorization: Bearer eyJ..."

# Refresh access token (15-minute expiry)
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ..."}'
```

### Key endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register/` | Create account |
| `POST` | `/api/v1/auth/token/` | Obtain JWT tokens |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh access token |
| `GET` | `/api/v1/emissions/footprint/` | Get user's footprint summary |
| `POST` | `/api/v1/emissions/entries/` | Log a new emission entry |
| `GET` | `/api/v1/emissions/entries/` | List logged entries (paginated) |
| `GET/POST` | `/api/v1/goals/` | List/create goals |
| `GET` | `/api/v1/social/leaderboard/` | Get friends leaderboard |
| `POST` | `/api/v1/social/friends/` | Send friend request |
| `GET` | `/api/v1/challenges/` | List active challenges |
| `POST` | `/api/v1/challenges/{id}/join/` | Join a challenge |
| `GET` | `/api/v1/coach/tip/` | Get AI coach tip (rate-limited) |
| `GET` | `/api/v1/offsets/` | List offset project directory |
| `GET/PUT` | `/api/v1/notifications/preferences/` | Get/update notification preferences |
| `GET` | `/api/v1/notifications/unsubscribe/{type}/{token}/` | One-click unsubscribe |

---

## Contributing

Contributions are welcome! Please read this section before opening a PR.

### Development workflow

1. **Fork** the repository and clone your fork.
2. **Create a branch** from `main`: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the code style guidelines below.
4. **Write tests** for all new functionality. Maintain ≥80% overall coverage.
5. **Run the full test suite** locally: `pytest --cov=ecotrack`
6. **Run the linter**: `ruff check . && ruff format --check .`
7. **Run type checking**: `mypy ecotrack/`
8. **Open a Pull Request** against `main` with a clear description of changes.

### Code style guidelines

- **Python:** Follow [PEP 8](https://peps.python.org/pep-0008/). Enforced by [Ruff](https://docs.astral.sh/ruff/).
- **Type hints:** All public functions and methods must have complete type annotations.
- **Docstrings:** All public functions and classes must have Google-style docstrings.
- **No business logic in views.** Views call services; services contain logic.
- **No dead code.** No commented-out code blocks in PRs.
- **No secrets in code.** All configuration via environment variables.
- **Tests required.** No PR without corresponding tests for new functionality.
- **Emission factors:** Any change to emission factor values requires an update to `docs/DATA_SOURCES.md` and a new data migration with a version bump.

### Running the linter

```bash
# Check for lint errors
ruff check .

# Auto-fix fixable errors
ruff check --fix .

# Check formatting
ruff format --check .

# Apply formatting
ruff format .

# Type checking
mypy ecotrack/ --strict
```

### Commit message format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(emissions): add natural gas emission factor for India
fix(ai_coach): prevent rate limit bypass via concurrent requests
docs(DATA_SOURCES): update DEFRA factors to 2024 edition
test(goals): add tests for streak reset logic
chore(deps): bump anthropic to 0.25.0
```

### Issue reporting

- **Bug reports:** Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md).
- **Feature requests:** Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md).
- **Security vulnerabilities:** Do **not** open a public issue. Email `security@ecotrack.app` with details.

### Code of conduct

EcoTrack follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By contributing, you agree to uphold this code.

---

## License

EcoTrack is released under the **MIT License**.

```
MIT License

Copyright (c) 2024 EcoTrack Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

See the [LICENSE](LICENSE) file for the full text.

---

### Third-party data licences

EcoTrack's emission factors are derived from publicly available datasets. See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for the complete licence compatibility matrix. Key notes:

- **DEFRA/BEIS 2023** data is used under the Open Government Licence v3.0.
- **Scarborough et al. 2023** data is used under CC BY 4.0.
- **WRAP** data is used for non-commercial purposes with attribution.
- No third-party datasets are redistributed; only derived emission factors are used within the application.

---

*EcoTrack — Helping individuals make sense of their carbon impact, one measurement at a time.*  
*Built with care in 🌍 · [ecotrack.app](https://ecotrack.app) · [docs](docs/) · [contributing](#contributing)*
