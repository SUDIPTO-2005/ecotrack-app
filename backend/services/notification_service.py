"""
Notification and nudge service (Phase 6).

Triggers notifications checking user preferences at data-model level before send.
"""
from __future__ import annotations

import logging
from django.conf import settings
from django.core.mail import send_mail

from apps.accounts.models import User, NotificationPreference
from apps.notifications.models import Notification, NotificationChannel, NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    """Core notifications engine checking preferences and sending channels."""

    def trigger_nudge(self, user: User, notification_type: str, title: str, content: str) -> bool:
        """
        Evaluate user preferences and dispatch nudge across configured channels.
        
        Args:
            user: Recipient user.
            notification_type: Nudge type e.g., 'streak_reminder'.
            title: Message title.
            content: Detailed body message text.
            
        Returns:
            True if at least one notification was successfully triggered/sent.
        """
        logger.info("Evaluating notification send", extra={"user": user.email, "type": notification_type})

        # Get or create preferences
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)

        # Enforce preferences check at the service level
        if not prefs.can_send(notification_type):
            logger.info("Notification blocked by user preferences", extra={"user": user.email, "type": notification_type})
            return False

        sent = False

        # Channel 1: In-App notification
        if prefs.in_app_enabled:
            Notification.objects.create(
                user=user,
                title=title,
                content=content,
                notification_type=notification_type,
                channel=NotificationChannel.IN_APP,
            )
            sent = True

        # Channel 2: Email notification (console logging in dev settings, SMTP in prod)
        if prefs.email_enabled:
            try:
                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ecotrack.example.com")
                send_mail(
                    subject=title,
                    message=content,
                    from_email=from_email,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                sent = True
            except Exception as exc:
                logger.error("Failed to send email nudge", exc_info=exc)

        # Record last notification timestamp if successfully dispatched
        if sent:
            prefs.record_sent()

        return sent
