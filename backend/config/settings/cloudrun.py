"""
Production settings for EcoTrack on Render / Cloud Run.

Inherits from base.py and configures:
- TLS handled by the platform proxy (no redirect loops)
- DATABASE_URL parsed via dj-database-url
- WhiteNoise serves static files (no separate static host needed)
- In-memory cache fallback when REDIS_URL not set
- CORS for Render onrender.com URLs
"""
from decouple import Csv, config

from .base import *  # noqa: F401, F403

# ---- Production hardening (no sentry dependency at module level) ----
DEBUG = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# WhiteNoise middleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + MIDDLEWARE[2:]  # noqa: F405

# ---- Cloud Run: TLS is terminated at the load balancer ----
# Setting this True causes redirect loops on Cloud Run.
SECURE_SSL_REDIRECT = False  # type: ignore[assignment]

# Cloud Run sets X-Forwarded-Proto, so Django knows the original scheme
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---- Allowed hosts ----
# Accept Cloud Run auto-generated URLs + custom domains
ALLOWED_HOSTS = config(  # type: ignore[assignment]
    "DJANGO_ALLOWED_HOSTS",
    default="*",
    cast=Csv(),
)

# ---- Database: prefer DATABASE_URL, fall back to individual vars ----
_database_url = config("DATABASE_URL", default="")
if _database_url:
    import dj_database_url  # type: ignore[import]
    # ssl_require=False — Render's internal DB uses postgres:// without SSL
    # External DBs (Neon etc.) include sslmode=require in the URL itself
    DATABASES = {  # type: ignore[assignment]
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=60,
            ssl_require=False,
        )
    }

# ---- Cache: use Redis if available, otherwise in-memory ----
_redis_url = config("REDIS_URL", default="")
if _redis_url:
    CACHES = {  # type: ignore[assignment]
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _redis_url,
            "TIMEOUT": 300,
        }
    }
else:
    # Free-tier fallback — no Redis needed
    CACHES = {  # type: ignore[assignment]
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# ---- Static files via WhiteNoise ----
# WhiteNoise is already in MIDDLEWARE from production.py
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # type: ignore[assignment]

# ---- CORS: allow Render + Cloud Run URLs ----
CORS_ALLOWED_ORIGINS = config(  # type: ignore[assignment]
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=Csv(),
)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://ecotrack-.*\.onrender\.com$",   # Render
    r"^https://ecotrack-.*\.a\.run\.app$",     # Cloud Run
    r"^http://localhost:\d+$",                  # Local dev
]
CORS_ALLOW_ALL_ORIGINS = True  # Permissive for free-tier deploy

# ---- Email: use console backend if no RESEND_API_KEY set ----
if not config("RESEND_API_KEY", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # type: ignore[assignment]
