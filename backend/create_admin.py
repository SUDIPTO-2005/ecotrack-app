"""
One-time script to create a default superuser on Render.
Run via: python manage.py shell < create_admin.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.cloudrun")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("ADMIN_USERNAME", "admin")
email = os.environ.get("ADMIN_EMAIL", "sudiptobhadra9c.jssp@gmail.com")
password = os.environ.get("ADMIN_PASSWORD", "EcoTrack@2026!")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser '{username}' created successfully!")
else:
    print(f"ℹ️ Superuser '{username}' already exists.")
