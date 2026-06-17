"""
Views for the ai_coach app (Phase 7).

Exposes POST endpoint to retrieve coaching advice based on latest calculations.
"""
from __future__ import annotations

from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.calculator.models import FootprintEntry, FootprintCategory
from services.ai_coach import AiCoachService
from .models import AiCoachingSession
from .serializers import CoachingTipsResponseSerializer
import json

_coach_service = AiCoachService()


class CoachingTipsView(APIView):
    """
    POST /api/v1/ai-coach/tips/
    
    Generates weekly coaching recommendations based on the user's latest calculation.
    Enforces a strict rate-limit of 1 generation request per user per week, returning
    the cached response if called again within 7 days.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        """Fetch weekly coaching tips."""
        user = request.user

        # Cache check: Retrieve last coaching session from last 7 days
        cutoff = timezone.now() - timedelta(days=7)
        recent_session = AiCoachingSession.objects.filter(
            user=user,
            generated_at__gte=cutoff
        ).first()

        if recent_session:
            return Response(
                CoachingTipsResponseSerializer(recent_session).data,
                status=status.HTTP_200_OK
            )

        # Query user's latest footprint entry
        latest_entry = FootprintEntry.objects.filter(user=user).order_by("-date", "-created_at").first()
        if not latest_entry:
            return Response(
                {"error": {"code": "no_data", "message": "Please log a footprint calculation before requesting coaching."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prepare breakdown
        categories = FootprintCategory.objects.filter(entry=latest_entry)
        category_breakdown = [
            {"category": cat.category, "co2e_kg": float(cat.co2e_kg), "percentage": float(cat.percentage)}
            for cat in categories
        ]

        if not category_breakdown:
            return Response(
                {"error": {"code": "no_breakdown", "message": "Failed to retrieve category breakdown details."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Budget check
        if not _coach_service.check_cost_budget():
            # Gracefully downgrade to fallback if budget is exceeded
            results = {
                "tips": _coach_service._fallback_engine.generate_fallback_tips(category_breakdown),
                "was_fallback": True,
                "model_version": "fallback",
                "tokens_used": 0,
            }
        else:
            results = _coach_service.get_coaching_tips(user, category_breakdown)

        # Save to DB cache (normalise keys so they always match frontend expectations)
        session = AiCoachingSession.objects.create(
            user=user,
            tips=_normalize_tips(results["tips"]),
            model_version=results["model_version"],
            tokens_used=results["tokens_used"],
            was_fallback=results["was_fallback"],
        )

        if results["tokens_used"] > 0:
            _coach_service.record_usage(results["tokens_used"])

        return Response(
            CoachingTipsResponseSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )


def _normalize_tips(tips: list) -> list:
    """
    Ensure tip dicts use the canonical keys: category, recommendation, impact_level.
    Handles old-format keys (action/impact) from legacy Claude responses.
    """
    IMPACT_MAP = {
        "high": "High", "medium": "Medium", "low": "Low",
        "low-medium": "Low", "low_medium": "Low",
    }
    normalized = []
    for tip in tips:
        normalized.append({
            "category": tip.get("category", "general"),
            "recommendation": tip.get("recommendation") or tip.get("action", ""),
            "impact_level": IMPACT_MAP.get(
                str(tip.get("impact_level") or tip.get("impact", "")).lower()[:10],
                "Medium"
            ),
        })
    return normalized


class EcoChatView(APIView):
    """
    POST /api/v1/ai-coach/chat/

    Interactive EcoBot chatbot endpoint. Accepts a user message + optional
    conversation history and returns a contextual reply from Claude or the
    rule-based fallback engine.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        user_message = request.data.get("message", "").strip()
        chat_history = request.data.get("history", [])

        if not user_message:
            return Response(
                {"error": {"code": "empty_message", "message": "Message cannot be empty."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(user_message) > 1000:
            return Response(
                {"error": {"code": "too_long", "message": "Message must be under 1000 characters."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = _coach_service.chat_with_coach(
            user=request.user,
            user_message=user_message,
            chat_history=chat_history,
        )

        return Response({
            "reply": result["reply"],
            "was_fallback": result["was_fallback"],
        }, status=status.HTTP_200_OK)
