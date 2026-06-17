"""
Data models for the notifications app (Phase 6).

Stores delivered in-app notifications and manages message templates.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models


class NotificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    IN_APP = "in_app", "In-App"


class NotificationType(models.TextChoices):
    STREAK_REMINDER = "streak_reminder", "Streak Reminder"
    CHALLENGE_DEADLINE = "challenge_deadline", "Challenge Deadline"
    MONTHLY_SUMMARY = "monthly_summary", "Monthly Summary"
    NEW_CHALLENGE = "new_challenge", "New Challenge Published"


class Notification(models.Model):
    """Stores in-app notifications for users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )
    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} — {self.title} (Read: {self.read})"
