"""
Integration tests for the Notifications API endpoints (Phase 6).
"""
from __future__ import annotations

import pytest
from django.urls import reverse
from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, NotificationPreference
from apps.notifications.models import Notification, NotificationType, NotificationChannel
from services.notification_service import NotificationService

_notify_svc = NotificationService()


@pytest.fixture
def registered_user(db) -> User:
    return User.objects.create_user(
        username="notify.tester@ecotrack.example.com",
        email="notify.tester@ecotrack.example.com",
        password="GreenPlanet2024!",
    )


@pytest.fixture
def auth_client(registered_user) -> APIClient:
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(registered_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.mark.django_db
class TestNotificationsAPI:
    """Tests for notifications listings, filters, and marking read actions."""

    def test_notification_list_success(self, auth_client, registered_user):
        """GET /api/v1/notifications/ returns user's notification list."""
        Notification.objects.create(
            user=registered_user,
            title="Challenge Starting",
            content="Zero waste week starts today!",
            notification_type=NotificationType.NEW_CHALLENGE,
        )

        url = reverse("notifications-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Challenge Starting"

    def test_notification_mark_read_success(self, auth_client, registered_user):
        """POST /api/v1/notifications/<id>/read/ marks notification as read."""
        notif = Notification.objects.create(
            user=registered_user,
            title="Read test",
            content="Sample nudge",
            notification_type=NotificationType.STREAK_REMINDER,
        )

        url = reverse("notifications-read", kwargs={"pk": notif.pk})
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        notif.refresh_from_db()
        assert notif.read is True

    def test_notification_read_all_success(self, auth_client, registered_user):
        """POST /api/v1/notifications/read-all/ marks all notifications as read."""
        Notification.objects.create(
            user=registered_user,
            title="Nudge 1",
            content="Sample 1",
            notification_type=NotificationType.CHALLENGE_DEADLINE,
        )
        Notification.objects.create(
            user=registered_user,
            title="Nudge 2",
            content="Sample 2",
            notification_type=NotificationType.CHALLENGE_DEADLINE,
        )

        url = reverse("notifications-read-all")
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Notification.objects.filter(user=registered_user, read=False).count() == 0


@pytest.mark.django_db
class TestNotificationEngineService:
    """Tests for the NotificationService logic and model-level preference verification."""

    def test_service_respects_opt_out(self, registered_user):
        """Service does not dispatch any nudges if opt_out is True."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=registered_user)
        prefs.opt_out = True
        prefs.save()

        success = _notify_svc.trigger_nudge(
            user=registered_user,
            notification_type="streak_reminder",
            title="Streak Danger",
            content="Log your footprint today!",
        )

        assert success is False
        assert Notification.objects.filter(user=registered_user).count() == 0

    def test_service_sends_email_and_in_app(self, registered_user):
        """Service successfully dispatches to email backend and creates DB in-app record."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=registered_user)
        prefs.email_enabled = True
        prefs.in_app_enabled = True
        prefs.save()

        mail.outbox = []

        success = _notify_svc.trigger_nudge(
            user=registered_user,
            notification_type="streak_reminder",
            title="Streak Danger",
            content="Log your footprint today!",
        )

        assert success is True
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Streak Danger"
        assert Notification.objects.filter(user=registered_user).count() == 1
