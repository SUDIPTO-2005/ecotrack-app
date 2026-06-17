"""
Views for the notifications app (Phase 6).

Exposes list, unread filter, and read toggles for user notifications.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """GET /api/v1/notifications/ — List current user's notifications."""

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """List user notifications."""
        unread_only = request.query_params.get("unread", "false").lower() == "true"
        queryset = Notification.objects.filter(user=request.user)

        if unread_only:
            queryset = queryset.filter(read=False)

        serializer = NotificationSerializer(queryset, many=True)
        return Response(serializer.data)


class NotificationReadView(APIView):
    """POST /api/v1/notifications/<id>/read/ — Mark a notification as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int) -> Response:
        """Mark notification as read."""
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "Notification not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.read = True
        notification.save(update_fields=["read"])
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(APIView):
    """POST /api/v1/notifications/read-all/ — Mark all notifications as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        """Mark all notifications as read."""
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
