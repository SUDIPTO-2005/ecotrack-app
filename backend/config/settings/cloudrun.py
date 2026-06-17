"""
Cloud Run settings for EcoTrack.

Inherits from production.py and overrides settings specific to
running on Google Cloud Run (managed, stateless, TLS-terminated).

Key differences from generic production:
- SECURE_SSL_REDIRECT = False  (Cloud Run's load balancer handles TLS)
- DATABASE_URL env var parsed via dj-database-url
- WhiteNoise serves static files (no separate static host needed)
- In-memory cache fallback when REDIS_URL not set
"""
import os
from decouple import config, Csv

# ---- inherit all production hardening ----
from .production import *  # noqa: F401, F403

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
    DATABASES = {  # type: ignore[assignment]
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=60,
            ssl_require=True,
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

# ---- CORS: set at deploy time via env var ----
# e.g. CORS_ALLOWED_ORIGINS=https://ecotrack-frontend-xxxx-as.a.run.app
CORS_ALLOWED_ORIGINS = config(  # type: ignore[assignment]
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=Csv(),
)
# Also allow all Cloud Run preview URLs during initial setup
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://ecotrack-.*\.a\.run\.app$",
]

# ---- Email: use console backend if no RESEND_API_KEY set ----
if not config("RESEND_API_KEY", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # type: ignore[assignment]
