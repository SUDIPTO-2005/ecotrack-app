"""
Views for the accounts app.

Views are deliberately thin — they validate input via serializers,
call the service layer, and return responses. Zero business logic here.

Throttling:
- RegisterView and LoginView use the 'auth' throttle class (10/min).
- All other views use the 'user' default (1000/hour).
"""
from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import NotificationPreference
from .serializers import (
    MeSerializer,
    NotificationPreferenceSerializer,
    PasswordChangeSerializer,
    TokenResponseSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)
from .services.auth_service import AuthService

logger = logging.getLogger(__name__)
_auth_service = AuthService()


class AuthRateThrottle(AnonRateThrottle):
    """Throttle for auth endpoints: 10 requests/minute."""
    scope = "auth"


class RegisterView(APIView):
    """POST /api/v1/accounts/register/ — create a new user account.

    Returns JWT tokens on success so the user is immediately logged in
    without a second request.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request: Request) -> Response:
        """Register a new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = _auth_service.register(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            display_name=serializer.validated_data.get("display_name", ""),
            country=serializer.validated_data.get("country", ""),
        )

        # Issue tokens immediately — no separate login needed after register
        tokens = _auth_service.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        return Response(
            TokenResponseSerializer(tokens).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/v1/accounts/login/ — authenticate and return JWT tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request: Request) -> Response:
        """Login with email and password."""
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = _auth_service.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        return Response(TokenResponseSerializer(tokens).data)


class LogoutView(APIView):
    """POST /api/v1/accounts/logout/ — blacklist the refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Logout by blacklisting the provided refresh token."""
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": {"code": "missing_field", "message": "'refresh' token is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _auth_service.logout(refresh_token)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/v1/accounts/me/ — lightweight auth check returning user identity."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return authenticated user's identity."""
        serializer = MeSerializer(request.user)
        return Response(serializer.data)


class ProfileView(APIView):
    """GET/PUT /api/v1/accounts/profile/ — read and update user profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Retrieve the authenticated user's full profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request: Request) -> Response:
        """Update the authenticated user's profile (full update)."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request: Request) -> Response:
        """Partially update the authenticated user's profile."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordChangeView(APIView):
    """POST /api/v1/accounts/password/change/ — change password."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Change password and return new tokens."""
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = _auth_service.change_password(
            user=request.user,  # type: ignore[arg-type]
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response(TokenResponseSerializer(tokens).data)


class NotificationPreferenceView(APIView):
    """GET/PUT /api/v1/accounts/notifications/preferences/ — manage notification settings."""

    permission_classes = [IsAuthenticated]

    def _get_prefs(self, request: Request) -> NotificationPreference:
        """Get or create the user's notification preferences."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        return prefs

    def get(self, request: Request) -> Response:
        """Retrieve current notification preferences."""
        prefs = self._get_prefs(request)
        return Response(NotificationPreferenceSerializer(prefs).data)

    def patch(self, request: Request) -> Response:
        """Update notification preferences (partial update supported)."""
        prefs = self._get_prefs(request)
        serializer = NotificationPreferenceSerializer(
            prefs, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
