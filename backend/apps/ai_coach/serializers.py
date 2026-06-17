"""
DRF serializers for the ai_coach app (Phase 7).
"""
from __future__ import annotations

from datetime import timedelta

from rest_framework import serializers

from .models import AiCoachingSession


class CoachingTipsResponseSerializer(serializers.ModelSerializer):
    """Serializer representing coaching feedback sessions."""

    # Expose next_update_available as generated_at + 7 days
    next_update_available = serializers.SerializerMethodField()

    class Meta:
        model = AiCoachingSession
        fields = [
            "id",
            "tips",
            "generated_at",
            "next_update_available",
            "model_version",
            "was_fallback",
        ]
        read_only_fields = fields

    def get_next_update_available(self, obj: AiCoachingSession) -> str:
        next_update = obj.generated_at + timedelta(days=7)
        return next_update.isoformat()
