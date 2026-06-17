"""Admin configuration for the accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, NotificationPreference


class NotificationPreferenceInline(admin.StackedInline):
    """Inline notification preferences in the User admin."""

    model = NotificationPreference
    extra = 0
    readonly_fields = ["opt_out_at", "last_notified_at", "created_at"]
    fieldsets = [
        ("Master Control", {"fields": ["opt_out", "opt_out_at"]}),
        ("Channels", {"fields": ["email_enabled", "in_app_enabled"]}),
        (
            "Notification Types",
            {
                "fields": [
                    "streak_reminders",
                    "challenge_deadlines",
                    "monthly_summary",
                    "new_challenges",
                ]
            },
        ),
        ("Frequency", {"fields": ["frequency_cap", "last_notified_at"]}),
    ]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Extended User admin with EcoTrack profile fields."""

    inlines = [NotificationPreferenceInline]
    list_display = [
        "email",
        "display_name",
        "country",
        "privacy_level",
        "leaderboard_visible",
        "onboarding_complete",
        "is_active",
        "date_joined",
    ]
    list_filter = ["privacy_level", "leaderboard_visible", "country", "is_active", "onboarding_complete"]
    search_fields = ["email", "display_name", "city", "country"]
    ordering = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (  # type: ignore[operator]
        (
            "EcoTrack Profile",
            {
                "fields": [
                    "display_name",
                    "bio",
                    "city",
                    "country",
                    "avatar_url",
                    "privacy_level",
                    "leaderboard_visible",
                    "onboarding_complete",
                ]
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2"),
            },
        ),
    )
