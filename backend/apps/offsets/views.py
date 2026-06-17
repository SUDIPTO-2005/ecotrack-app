"""
Views for the offsets app (Phase 8).

Exposes GET listing and details endpoints along with informational compliance disclaimers.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import OffsetProject
from .serializers import OffsetProjectSerializer

# Disclaimer notice to fulfill informational compliance requirements
DISCLAIMER_NOTICE = (
    "EcoTrack shows estimated offset costs for informational purposes only. "
    "We do not sell offsets, process payments, or guarantee any carbon retirement. "
    "To purchase verified offsets, follow the link to the registry's official listing."
)


class OffsetProjectListView(APIView):
    """
    GET /api/v1/offsets/ — List available carbon offset projects.

    Includes the mandatory compliance disclaimer in the API header / response.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """List offset projects."""
        projects = OffsetProject.objects.filter(is_available=True)
        serializer = OffsetProjectSerializer(projects, many=True)

        return Response({
            "disclaimer": DISCLAIMER_NOTICE,
            "results": serializer.data
        }, status=status.HTTP_200_OK)


class OffsetProjectDetailView(APIView):
    """GET /api/v1/offsets/<id>/ — Detailed project view."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int) -> Response:
        """Retrieve project detail information."""
        try:
            project = OffsetProject.objects.get(pk=pk, is_available=True)
        except OffsetProject.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "Offset project not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OffsetProjectSerializer(project)
        return Response({
            "disclaimer": DISCLAIMER_NOTICE,
            "project": serializer.data
        }, status=status.HTTP_200_OK)
