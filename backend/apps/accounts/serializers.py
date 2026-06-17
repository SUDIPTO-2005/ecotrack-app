"""
DRF serializers for the accounts app.

Serializers are the validation boundary — all input sanitisation
happens here, not in views or services.

Notes on security:
- Passwords are write-only; never included in response serialisation.
- Email is normalised to lowercase in the service layer, but we strip
  here too as an early guard.
- No raw SQL; all validation uses DRF/Django validators.
"""
from __future__ import annotations

from rest_framework import serializers

from .models import NotificationPreference, User


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for new user registration.

    Password validation (strength) is delegated to AuthService.register
    which calls Django's validate_password. Here we only validate
    required field presence and type.
    """

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        min_length=10,
        max_length=128,
        style={"input_type": "password"},
        help_text="Minimum 10 characters. Must not be too similar to your email.",
    )
    display_name = serializers.CharField(
        max_length=60,
        required=False,
        allow_blank=True,
        default="",
    )
    country = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
        help_text="ISO 3166-1 alpha-2 code, e.g. 'IN', 'GB', 'US'.",
    )

    def validate_email(self, value: str) -> str:
        """Normalise email to lowercase."""
        return value.lower().strip()

    def validate_display_name(self, value: str) -> str:
        """Strip whitespace and validate display name length."""
        return value.strip()

    def validate_country(self, value: str) -> str:
        """Convert to ISO-like 2-character code."""
        return value.upper()[:2] if value else ""


class UserLoginSerializer(serializers.Serializer):
    """Serializer for login credentials."""

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_email(self, value: str) -> str:
        return value.lower().strip()


class TokenResponseSerializer(serializers.Serializer):
    """Response shape for login/register endpoints that return tokens."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    display_name = serializers.CharField(read_only=True, allow_blank=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """Read/write serializer for user profile.

    Email is read-only after registration (changing email requires
    a separate verification flow, not implemented in MVP).
    Password is excluded — use PasswordChangeSerializer.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "display_name",
            "bio",
            "city",
            "country",
            "avatar_url",
            "privacy_level",
            "leaderboard_visible",
            "onboarding_complete",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined"]

    def validate_display_name(self, value: str) -> str:
        return value.strip()

    def validate_country(self, value: str) -> str:
        return value.upper()[:2] if value else ""


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences.

    user and audit fields are read-only. opt_out triggers a timestamp
    update (handled in the update method below).
    """

    class Meta:
        model = NotificationPreference
        fields = [
            "opt_out",
            "email_enabled",
            "in_app_enabled",
            "streak_reminders",
            "challenge_deadlines",
            "monthly_summary",
            "new_challenges",
            "frequency_cap",
            "last_notified_at",
            "opt_out_at",
            "updated_at",
        ]
        read_only_fields = ["last_notified_at", "opt_out_at", "updated_at"]

    def update(self, instance: NotificationPreference, validated_data: dict) -> NotificationPreference:
        """Override update to record opt_out_at timestamp."""
        from django.utils import timezone

        if "opt_out" in validated_data:
            if validated_data["opt_out"] and not instance.opt_out:
                # User is opting out — record timestamp
                instance.opt_out_at = timezone.now()
            elif not validated_data["opt_out"] and instance.opt_out:
                # User is opting back in — clear timestamp
                instance.opt_out_at = None

        return super().update(instance, validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=10,
        max_length=128,
        style={"input_type": "password"},
        help_text="Minimum 10 characters.",
    )


class MeSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the /me/ endpoint (auth check)."""

    class Meta:
        model = User
        fields = ["id", "email", "display_name", "onboarding_complete", "country"]
        read_only_fields = ["id", "email", "display_name", "onboarding_complete", "country"]
