"""
Views for the data_sync app (Phase 4).

Exposes a protected sync webhook view that triggers the government data sync.
"""
from __future__ import annotations

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from services.government_data import GovernmentDataService

logger = logging.getLogger(__name__)
_gov_service = GovernmentDataService()


class GovDataSyncWebhookView(APIView):
    """
    POST /api/v1/internal/sync/national-averages/

    Protected sync webhook view to trigger OWID data sync.
    Protected by a shared secret key (DATA_SYNC_SECRET).
    """

    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        """Trigger government data sync."""
        secret = request.headers.get("X-Sync-Secret") or request.query_params.get("secret")
        expected_secret = getattr(settings, "DATA_SYNC_SECRET", None)

        if not expected_secret or secret != expected_secret:
            return Response(
                {"error": {"code": "forbidden", "message": "Invalid sync secret credentials."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        csv_url = request.data.get("csv_url") or getattr(settings, "OWID_DATA_URL", None)
        if not csv_url:
            return Response(
                {"error": {"code": "missing_url", "message": "No CSV URL provided or configured."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            results = _gov_service.sync_owid_data(csv_url)
            return Response(results, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Sync error occurred")
            return Response(
                {"error": {"code": "sync_failed", "message": str(exc)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
