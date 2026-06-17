"""
DRF serializers for the challenges app (Phase 5).
"""
from __future__ import annotations

from rest_framework import serializers

from .models import Challenge, ChallengeParticipant, Badge, UserBadge, LeaderboardSnapshot


class ChallengeSerializer(serializers.ModelSerializer):
    """Serializer representing community challenges."""

    participant_count = serializers.SerializerMethodField()
    is_joined = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = [
            "id",
            "title",
            "description",
            "category",
            "start_date",
            "end_date",
            "target_reduction_pct",
            "participant_count",
            "is_joined",
        ]
        read_only_fields = fields

    def get_participant_count(self, obj: Challenge) -> int:
        return obj.participants.count()

    def get_is_joined(self, obj: Challenge) -> bool:
        user = self.context.get("request").user if "request" in self.context else None
        if not user or user.is_anonymous:
            return False
        return obj.participants.filter(user=user).exists()


class ChallengeParticipantSerializer(serializers.ModelSerializer):
    """Serializer representing user participation."""

    challenge_details = ChallengeSerializer(source="challenge", read_only=True)

    class Meta:
        model = ChallengeParticipant
        fields = [
            "id",
            "challenge",
            "challenge_details",
            "joined_at",
            "completed_at",
            "streak_days",
        ]
        read_only_fields = ["id", "joined_at", "completed_at", "streak_days"]


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for badges."""

    class Meta:
        model = Badge
        fields = ["id", "name", "description", "icon", "criteria"]
        read_only_fields = fields


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for awarded user badges."""

    badge_details = BadgeSerializer(source="badge", read_only=True)

    class Meta:
        model = UserBadge
        fields = ["id", "badge", "badge_details", "awarded_at"]
        read_only_fields = fields


class LeaderboardSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for leaderboard rankings."""

    display_name = serializers.CharField(source="user.public_name", read_only=True)
    city = serializers.CharField(source="user.city", read_only=True)
    country = serializers.CharField(source="user.country", read_only=True)

    class Meta:
        model = LeaderboardSnapshot
        fields = [
            "rank",
            "display_name",
            "city",
            "country",
            "reduction_percentage",
            "scope",
        ]
        read_only_fields = fields
