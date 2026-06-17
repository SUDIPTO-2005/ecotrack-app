"""
Data models for the challenges app (Phase 5).

Supports community challenges, user participations, streaks, badges,
and leaderboard ranking snapshots.
"""
from __future__ import annotations

from django.db import models
from django.conf import settings


class Challenge(models.Model):
    """Community carbon footprint reduction challenges."""

    title = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        help_text="e.g. 'transport', 'diet', 'energy'",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    target_reduction_pct = models.PositiveSmallIntegerField(
        help_text="Target percentage footprint reduction expected.",
        default=10,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return self.title


class ChallengeParticipant(models.Model):
    """Tracks user participation in a community challenge."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenge_participations",
    )
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    streak_days = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Challenge Participant"
        verbose_name_plural = "Challenge Participants"
        unique_together = [("user", "challenge")]

    def __str__(self) -> str:
        return f"{self.user} in {self.challenge}"


class Badge(models.Model):
    """Impact achievement badges."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(
        max_length=100,
        help_text="Icon reference name for frontend rendering.",
    )
    criteria = models.JSONField(
        help_text="JSON representation of requirements for badge awards.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"

    def __str__(self) -> str:
        return self.name


class UserBadge(models.Model):
    """Badges awarded to users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="badges",
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="awards",
    )
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Badge"
        verbose_name_plural = "User Badges"
        unique_together = [("user", "badge")]

    def __str__(self) -> str:
        return f"{self.user} awarded {self.badge.name}"


class LeaderboardSnapshot(models.Model):
    """
    Cached leaderboard records.
    
    Updated regularly via background task or cron, avoiding expensive live DB queries.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    rank = models.PositiveIntegerField()
    reduction_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    scope = models.CharField(
        max_length=20,
        default="global",
        help_text="Leaderboard scope: global, country, or city",
    )
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leaderboard Snapshot"
        verbose_name_plural = "Leaderboard Snapshots"
        ordering = ["scope", "rank"]
        unique_together = [("user", "scope")]

    def __str__(self) -> str:
        return f"[{self.scope}] #{self.rank}: {self.user.public_name} ({self.reduction_percentage}%)"
