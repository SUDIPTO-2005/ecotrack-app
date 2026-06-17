"""
Views for the challenges app (Phase 5).

Exposes views for challenges listings, joins, badges query,
and leaderboard ranking snapshots.
"""
from __future__ import annotations

from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Challenge,
    ChallengeParticipant,
    LeaderboardSnapshot,
    UserBadge,
)
from .serializers import (
    ChallengeParticipantSerializer,
    ChallengeSerializer,
    LeaderboardSnapshotSerializer,
    UserBadgeSerializer,
)


class ChallengeListView(APIView):
    """GET /api/v1/challenges/ — Active community challenges listing."""

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """List active and upcoming challenges."""
        today = date.today()
        # Retrieve challenges that end in the future
        challenges = Challenge.objects.filter(end_date__gte=today)
        serializer = ChallengeSerializer(challenges, many=True, context={"request": request})
        return Response(serializer.data)


class ChallengeJoinView(APIView):
    """POST /api/v1/challenges/<id>/join/ — Join a challenge."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int) -> Response:
        """Join the specified challenge."""
        challenge = get_object_or_404(Challenge, pk=pk)

        # Check if already joined
        participant, created = ChallengeParticipant.objects.get_or_create(
            user=request.user,
            challenge=challenge,
        )

        if not created:
            return Response(
                {"error": {"code": "already_joined", "message": "You have already joined this challenge."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ChallengeParticipantSerializer(participant, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChallengeLeaveView(APIView):
    """POST /api/v1/challenges/<id>/leave/ — Leave a challenge."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int) -> Response:
        """Leave the specified challenge."""
        challenge = get_object_or_404(Challenge, pk=pk)
        participant = ChallengeParticipant.objects.filter(user=request.user, challenge=challenge).first()

        if not participant:
            return Response(
                {"error": {"code": "not_joined", "message": "You are not a participant in this challenge."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BadgesListView(APIView):
    """GET /api/v1/challenges/badges/ — List badges awarded to the current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """List current user badges."""
        user_badges = UserBadge.objects.filter(user=request.user).order_by("-awarded_at")
        serializer = UserBadgeSerializer(user_badges, many=True)
        return Response(serializer.data)


class LeaderboardView(APIView):
    """GET /api/v1/challenges/leaderboard/ — Retrieve leaderboard rankings."""

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """Get leaderboard list filtered by scope."""
        # Validate that current user has opted in to leaderboard visiblity
        if not request.user.leaderboard_visible:
            return Response(
                {"error": {"code": "opt_in_required", "message": "You must opt-in to leaderboards to view rankings."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        scope = request.query_params.get("scope", "global")
        if scope not in ["global", "country", "city"]:
            scope = "global"

        # Filters by scope
        queryset = LeaderboardSnapshot.objects.filter(scope=scope)

        # Scopes filters
        if scope == "country":
            queryset = queryset.filter(user__country=request.user.country)
        elif scope == "city":
            queryset = queryset.filter(user__city=request.user.city)

        queryset = queryset.order_by("rank")[:50]
        serializer = LeaderboardSnapshotSerializer(queryset, many=True)
        return Response(serializer.data)
