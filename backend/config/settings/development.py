"""
Development settings for EcoTrack.

Never use these settings in production. DEBUG is True, relaxed security.
"""
from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Use SQLite for quick local dev if POSTGRES_HOST is not set.
# Override with PostgreSQL for full feature testing.
if not config("POSTGRES_HOST", default=""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_dev.sqlite3",  # type: ignore[name-defined]  # noqa: F405
        }
    }

# Disable cache in dev for simplicity
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Celery: run tasks synchronously in dev (no worker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email: print to console in dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# DRF: enable browsable API in dev, and relax throttling for tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # type: ignore[name-defined]  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        "anon": "999999/hour",
        "user": "999999/hour",
        "auth": "999999/hour",
        "calculator": "999999/hour",
        "ai_coach": "999999/hour",
    },
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# Looser CORS for local dev
CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS += [  # type: ignore[name-defined]  # noqa: F405
    "django_extensions",  # Optional but useful
]
