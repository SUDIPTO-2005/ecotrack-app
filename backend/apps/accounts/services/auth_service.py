"""
Authentication business logic for EcoTrack.

All auth operations live here — views call services, never implement
business logic directly. This makes unit testing easy (no HTTP layer)
and ensures consistent behaviour across any auth method we add later.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import NotificationPreference, User

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TokenPair:
    """Access + refresh token pair returned after successful auth."""

    access: str
    refresh: str
    user_id: int
    email: str
    display_name: str


class AuthService:
    """Handles user registration, login, logout, and credential changes.

    No HTTP request/response logic here — only business rules.
    """

    def register(
        self,
        email: str,
        password: str,
        display_name: str = "",
        country: str = "",
    ) -> User:
        """Register a new user and create their notification preferences.

        Validates password against Django's configured validators
        (min length 10, not too common, not too similar to email).

        Args:
            email: Unique email address (case-insensitive stored).
            password: Raw password — hashed before storage.
            display_name: Optional public display name.
            country: ISO 3166-1 alpha-2 country code.

        Returns:
            The newly created User instance.

        Raises:
            ValidationError: If email is taken or password fails validation.
        """
        email = email.lower().strip()

        if User.objects.filter(email=email).exists():
            raise ValidationError({"email": "A user with this email already exists."})

        # Validate password strength via Django's configured validators
        try:
            validate_password(password, user=User(email=email))
        except DjangoValidationError as exc:
            raise ValidationError({"password": list(exc.messages)}) from exc

        user = User.objects.create_user(
            username=email,  # username mirrors email for AbstractUser compatibility
            email=email,
            password=password,
            display_name=display_name,
            country=country.upper()[:2] if country else "",
        )

        # Create notification preferences with safe defaults
        NotificationPreference.objects.create(
            user=user,
            opt_out=False,
            email_enabled=True,
            in_app_enabled=True,
        )

        logger.info("User registered", extra={"user_id": user.id, "country": user.country})
        return user

    def login(self, email: str, password: str) -> TokenPair:
        """Authenticate a user and return a JWT token pair.

        Args:
            email: User's email address.
            password: Raw password to verify.

        Returns:
            TokenPair with access + refresh tokens and user metadata.

        Raises:
            AuthenticationFailed: If credentials are invalid or account inactive.
        """
        user = authenticate(username=email.lower().strip(), password=password)
        if user is None:
            # Generic message — don't reveal whether email exists
            raise AuthenticationFailed("Invalid credentials.")
        if not user.is_active:  # type: ignore[union-attr]
            raise AuthenticationFailed("This account has been deactivated.")

        tokens = self._issue_tokens(user)  # type: ignore[arg-type]
        logger.info("User logged in", extra={"user_id": user.pk})
        return tokens

    def logout(self, refresh_token: str) -> None:
        """Blacklist a refresh token, invalidating the session.

        After logout, the access token will expire naturally (short-lived);
        the refresh token is blacklisted so it cannot be used to get
        new access tokens.

        Args:
            refresh_token: The refresh token string to invalidate.

        Raises:
            ValidationError: If the token is invalid or already blacklisted.
        """
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("Refresh token blacklisted")
        except TokenError as exc:
            raise ValidationError({"refresh": str(exc)}) from exc

    def change_password(
        self, user: User, old_password: str, new_password: str
    ) -> TokenPair:
        """Change a user's password and issue fresh tokens.

        Verifies the old password before changing. Issues a new token
        pair after change so the session remains valid.

        Args:
            user: The authenticated user.
            old_password: Current password for verification.
            new_password: New password (validated against Django validators).

        Returns:
            New TokenPair for the user.

        Raises:
            ValidationError: If old password is wrong or new password is weak.
        """
        if not user.check_password(old_password):
            raise ValidationError({"old_password": "Current password is incorrect."})

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            raise ValidationError({"new_password": list(exc.messages)}) from exc

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        logger.info("Password changed", extra={"user_id": user.id})
        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenPair:
        """Generate a JWT access + refresh token pair for a user.

        Args:
            user: Authenticated User instance.

        Returns:
            TokenPair dataclass.
        """
        refresh = RefreshToken.for_user(user)
        return TokenPair(
            access=str(refresh.access_token),
            refresh=str(refresh),
            user_id=user.pk,
            email=user.email,
            display_name=user.display_name,
        )
