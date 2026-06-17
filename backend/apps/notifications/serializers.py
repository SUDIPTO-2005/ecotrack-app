"""
DRF serializers for the notifications app (Phase 6).
"""
from __future__ import annotations

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer representing delivered user notifications."""

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "content",
            "notification_type",
            "channel",
            "read",
            "created_at",
        ]
        read_only_fields = ["id", "title", "content", "notification_type", "channel", "created_at"]
