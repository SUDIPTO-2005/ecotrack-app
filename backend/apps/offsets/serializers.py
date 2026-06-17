"""
DRF serializers for the offsets app (Phase 8).
"""
from __future__ import annotations

from rest_framework import serializers

from .models import OffsetProject


class OffsetProjectSerializer(serializers.ModelSerializer):
    """Serializer representing informational carbon offset projects."""

    class Meta:
        model = OffsetProject
        fields = [
            "id",
            "project_id",
            "name",
            "description",
            "registry",
            "price_per_tonne_usd",
            "certification",
            "project_url",
            "is_available",
        ]
        read_only_fields = fields
