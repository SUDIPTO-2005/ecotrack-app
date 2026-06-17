"""
User account models for EcoTrack.

Design decisions:
- Custom User extends AbstractUser so we keep Django's auth machinery
  (password hashing, permission system) while adding profile fields.
- NotificationPreference is a OneToOne child of User — checked before
  EVERY send in notification_service.py. opt_out is the master kill-switch;
  individual toggles (streak_reminders etc.) are secondary gates.
- privacy_level controls leaderboard and social-sharing visibility.
  Default is 'anonymous' — users opt IN to more visibility, never opt out.
- leaderboard_visible is a separate explicit opt-in flag (privacy_level
  alone isn't enough — users can be 'public' but still not want leaderboard).
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class PrivacyLevel(models.TextChoices):
    PUBLIC = "public", "Public (name visible to all)"
    FRIENDS = "friends", "Friends only"
    ANONYMOUS = "anonymous", "Anonymous (no name shown)"


class NotificationFrequencyCap(models.TextChoices):
    NONE = "none", "No cap (send as triggered)"
    DAILY = "daily", "At most once per day"
    WEEKLY = "weekly", "At most once per week"
    MONTHLY = "monthly", "At most once per month"


class User(AbstractUser):
    """
    Custom user model for EcoTrack.

    Extends AbstractUser with profile fields. Email is the primary
    identifier — username is kept for Django admin compatibility but
    not exposed in the API.

    Database indexes:
    - email: primary login lookup
    - country: used for leaderboard scoping
    """

    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Primary identifier and login credential.",
    )
    display_name = models.CharField(
        max_length=60,
        blank=True,
        help_text="Optional public name for leaderboard/challenges. Blank = anonymous.",
    )
    bio = models.TextField(
        max_length=300,
        blank=True,
        help_text="Optional short bio, 300 chars max.",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="Used for city-scoped leaderboard.",
    )
    country = models.CharField(
        max_length=2,
        blank=True,
        db_index=True,
        help_text="ISO 3166-1 alpha-2 country code. Used for national average comparison.",
    )
    privacy_level = models.CharField(
        max_length=20,
        choices=PrivacyLevel.choices,
        default=PrivacyLevel.ANONYMOUS,
        help_text="Controls how name/data appears in social features. Default: anonymous.",
    )
    leaderboard_visible = models.BooleanField(
        default=False,
        help_text="Explicit opt-in for leaderboard participation. False by default.",
    )
    avatar_url = models.URLField(
        blank=True,
        help_text="Profile picture URL (user-supplied or OAuth-provided).",
    )
    onboarding_complete = models.BooleanField(
        default=False,
        help_text="Whether the user has completed the onboarding calculator flow.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta(AbstractUser.Meta):
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["country"], name="idx_user_country"),
            models.Index(fields=["leaderboard_visible"], name="idx_user_leaderboard"),
        ]

    def __str__(self) -> str:
        return self.display_name or self.email

    @property
    def public_name(self) -> str:
        """Name to display in public contexts based on privacy_level.

        Returns display_name for public/friends, 'Anonymous User' otherwise.
        """
        if self.privacy_level == PrivacyLevel.ANONYMOUS or not self.display_name:
            return "Anonymous User"
        return self.display_name


class NotificationPreference(models.Model):
    """
    Per-user notification preferences.

    This model is the authoritative gate for all notification sends.
    notification_service.py checks opt_out and individual flags before
    EVERY send — the UI toggle is NOT the enforcement mechanism.

    Design principle: opt_out is a hard master kill-switch. When True,
    no notifications are sent regardless of individual flags. This is
    enforced at the data-model level, not just the UI, so it survives
    frontend bugs and future API changes.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )

    # Master kill-switch — checked first, before any individual flag
    opt_out = models.BooleanField(
        default=False,
        help_text="Global opt-out. When True, no notifications sent regardless of other settings.",
    )
    opt_out_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when user opted out. Retained for compliance audit.",
    )

    # Channel enablement
    email_enabled = models.BooleanField(
        default=True,
        help_text="Send notifications via email (requires Resend/SMTP config).",
    )
    in_app_enabled = models.BooleanField(
        default=True,
        help_text="Show in-app notification center badges.",
    )

    # Notification type toggles (secondary gates — only checked if opt_out=False)
    streak_reminders = models.BooleanField(
        default=True,
        help_text="Remind user when a streak is about to break.",
    )
    challenge_deadlines = models.BooleanField(
        default=True,
        help_text="Remind user of upcoming challenge deadlines.",
    )
    monthly_summary = models.BooleanField(
        default=True,
        help_text="Monthly footprint summary and progress report.",
    )
    new_challenges = models.BooleanField(
        default=False,
        help_text="Notify when new community challenges are published. Opt-in only.",
    )

    # Frequency cap (additional guard against over-messaging)
    frequency_cap = models.CharField(
        max_length=10,
        choices=NotificationFrequencyCap.choices,
        default=NotificationFrequencyCap.WEEKLY,
        help_text="Maximum notification frequency regardless of trigger count.",
    )

    last_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last sent notification. Used to enforce frequency_cap.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self) -> str:
        status = "opted out" if self.opt_out else "active"
        return f"{self.user} notifications ({status})"

    def can_send(self, notification_type: str) -> bool:
        """Check whether a notification of the given type can be sent.

        This is the canonical check — call this before every send.
        Order of evaluation:
        1. Master opt_out flag (hard stop)
        2. Individual notification type flag
        3. Frequency cap (time-based)

        Args:
            notification_type: One of 'streak_reminder', 'challenge_deadline',
                'monthly_summary', 'new_challenge'.

        Returns:
            True if the notification should be sent, False otherwise.
        """
        if self.opt_out:
            return False

        type_map = {
            "streak_reminder": self.streak_reminders,
            "challenge_deadline": self.challenge_deadlines,
            "monthly_summary": self.monthly_summary,
            "new_challenge": self.new_challenges,
        }
        if not type_map.get(notification_type, True):
            return False

        return self._frequency_cap_allows()

    def _frequency_cap_allows(self) -> bool:
        """Check if the frequency cap allows sending now."""
        if self.frequency_cap == NotificationFrequencyCap.NONE:
            return True
        if self.last_notified_at is None:
            return True

        now = timezone.now()
        delta = now - self.last_notified_at

        if self.frequency_cap == NotificationFrequencyCap.DAILY:
            return delta.total_seconds() >= 86_400
        if self.frequency_cap == NotificationFrequencyCap.WEEKLY:
            return delta.days >= 7
        if self.frequency_cap == NotificationFrequencyCap.MONTHLY:
            return delta.days >= 30
        return True

    def record_sent(self) -> None:
        """Update last_notified_at after a successful send."""
        self.last_notified_at = timezone.now()
        self.save(update_fields=["last_notified_at", "updated_at"])
