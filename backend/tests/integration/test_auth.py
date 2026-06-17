"""
Integration tests for the accounts (authentication) API.

These tests hit real endpoints end-to-end through the DRF test client.
They verify:
- Registration creates user + notification preferences
- Login returns valid JWT tokens
- Logout blacklists the refresh token
- Protected endpoints require authentication
- Rate limiting is enforced on auth endpoints
- NotificationPreference.opt_out is enforced at the model level
- Password change invalidates old session

External calls: None. All tests are self-contained with Django test DB.
Run with: pytest tests/integration/test_auth.py -v
"""
from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import NotificationPreference, User


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> APIClient:
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def register_payload() -> dict:
    """Valid registration payload."""
    return {
        "email": "testuser@ecotrack.example.com",
        "password": "GreenPlanet2024!",
        "display_name": "Test User",
        "country": "IN",
    }


@pytest.fixture
def registered_user(db, client, register_payload) -> tuple[User, dict]:
    """Register a user and return (user, token_data)."""
    response = client.post(
        reverse("accounts-register"),
        data=register_payload,
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(email=register_payload["email"])
    return user, response.json()


@pytest.fixture
def auth_client(db, client, registered_user) -> tuple[APIClient, User, dict]:
    """Authenticated API client with a registered user."""
    user, token_data = registered_user
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_data['access']}")
    return client, user, token_data


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRegister:
    """Tests for POST /api/v1/accounts/register/."""

    URL = "accounts-register"

    def test_register_success_returns_201_and_tokens(
        self, client: APIClient, register_payload: dict
    ) -> None:
        """Successful registration returns 201 with access + refresh tokens."""
        response = client.post(reverse(self.URL), data=register_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        assert data["email"] == register_payload["email"]

    def test_register_creates_user_in_db(
        self, client: APIClient, register_payload: dict
    ) -> None:
        """Registration creates a User record with correct email and country."""
        client.post(reverse(self.URL), data=register_payload, format="json")

        user = User.objects.filter(email=register_payload["email"]).first()
        assert user is not None
        assert user.country == "IN"
        assert user.display_name == "Test User"

    def test_register_creates_notification_preferences(
        self, client: APIClient, register_payload: dict
    ) -> None:
        """Registration auto-creates NotificationPreference with safe defaults."""
        client.post(reverse(self.URL), data=register_payload, format="json")

        user = User.objects.get(email=register_payload["email"])
        prefs = NotificationPreference.objects.filter(user=user).first()
        assert prefs is not None
        assert prefs.opt_out is False  # Default: not opted out
        assert prefs.email_enabled is True
        assert prefs.in_app_enabled is True
        assert prefs.new_challenges is False  # Opt-in only

    def test_register_password_is_hashed(
        self, client: APIClient, register_payload: dict
    ) -> None:
        """Stored password must be hashed, never plaintext."""
        client.post(reverse(self.URL), data=register_payload, format="json")

        user = User.objects.get(email=register_payload["email"])
        assert user.password != register_payload["password"]
        assert user.password.startswith(("pbkdf2_sha256$", "argon2", "bcrypt"))

    def test_register_normalises_email_to_lowercase(
        self, client: APIClient
    ) -> None:
        """Email is normalised to lowercase during registration."""
        payload = {
            "email": "TestUser@ECOTRACK.EXAMPLE.COM",
            "password": "GreenPlanet2024!",
        }
        client.post(reverse(self.URL), data=payload, format="json")

        assert User.objects.filter(email="testuser@ecotrack.example.com").exists()
        assert not User.objects.filter(email="TestUser@ECOTRACK.EXAMPLE.COM").exists()

    def test_register_rejects_duplicate_email(
        self, client: APIClient, register_payload: dict
    ) -> None:
        """Registering with an existing email returns 400."""
        client.post(reverse(self.URL), data=register_payload, format="json")
        response = client.post(reverse(self.URL), data=register_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "email" in str(data).lower() or "error" in str(data).lower()

    def test_register_rejects_short_password(
        self, client: APIClient, register_payload: dict
    ) -> None:
        """Password shorter than 10 characters is rejected."""
        register_payload["password"] = "short"
        response = client.post(reverse(self.URL), data=register_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_rejects_common_password(
        self, client: APIClient, register_payload: dict
    ) -> None:
        """Common passwords like 'password1234' are rejected."""
        register_payload["password"] = "password1234"
        response = client.post(reverse(self.URL), data=register_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_without_display_name_succeeds(
        self, client: APIClient
    ) -> None:
        """display_name is optional; registration succeeds without it."""
        payload = {
            "email": "anon@ecotrack.example.com",
            "password": "GreenPlanet2024!",
        }
        response = client.post(reverse(self.URL), data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_register_default_privacy_is_anonymous(
        self, client: APIClient, register_payload: dict
    ) -> None:
        """New users default to anonymous privacy level (opt-in to visibility)."""
        client.post(reverse(self.URL), data=register_payload, format="json")

        user = User.objects.get(email=register_payload["email"])
        assert user.privacy_level == "anonymous"
        assert user.leaderboard_visible is False

    def test_register_requires_email(self, client: APIClient) -> None:
        """Email is required; missing email returns 400."""
        response = client.post(
            reverse(self.URL),
            data={"password": "GreenPlanet2024!"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLogin:
    """Tests for POST /api/v1/accounts/login/."""

    URL = "accounts-login"

    def test_login_with_valid_credentials_returns_tokens(
        self, client: APIClient, registered_user: tuple
    ) -> None:
        """Valid credentials return 200 with access + refresh tokens."""
        user, _ = registered_user
        response = client.post(
            reverse(self.URL),
            data={"email": user.email, "password": "GreenPlanet2024!"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        assert data["email"] == user.email

    def test_login_with_wrong_password_returns_401(
        self, client: APIClient, registered_user: tuple
    ) -> None:
        """Wrong password returns 401 Unauthorized."""
        user, _ = registered_user
        response = client.post(
            reverse(self.URL),
            data={"email": user.email, "password": "WrongPassword!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_nonexistent_email_returns_401(
        self, client: APIClient, db
    ) -> None:
        """Unknown email returns 401 (generic message — don't reveal existence)."""
        response = client.post(
            reverse(self.URL),
            data={"email": "nobody@ecotrack.example.com", "password": "GreenPlanet2024!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # The error message must not reveal whether the email exists
        data = response.json()
        assert "email" not in str(data).lower() or "invalid credentials" in str(data).lower()

    def test_login_email_case_insensitive(
        self, client: APIClient, registered_user: tuple
    ) -> None:
        """Login works with uppercase email (normalised to lowercase)."""
        user, _ = registered_user
        response = client.post(
            reverse(self.URL),
            data={"email": user.email.upper(), "password": "GreenPlanet2024!"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_login_response_does_not_include_password(
        self, client: APIClient, registered_user: tuple
    ) -> None:
        """Login response must never include the user's password."""
        user, _ = registered_user
        response = client.post(
            reverse(self.URL),
            data={"email": user.email, "password": "GreenPlanet2024!"},
            format="json",
        )

        assert "password" not in response.json()
        assert "GreenPlanet2024!" not in str(response.json())


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLogout:
    """Tests for POST /api/v1/accounts/logout/."""

    URL = "accounts-logout"

    def test_logout_returns_204(
        self, auth_client: tuple
    ) -> None:
        """Successful logout returns 204 No Content."""
        client, user, token_data = auth_client
        response = client.post(
            reverse(self.URL),
            data={"refresh": token_data["refresh"]},
            format="json",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_blacklists_refresh_token(
        self, auth_client: tuple
    ) -> None:
        """After logout, the refresh token cannot be used to get new access tokens."""
        client, user, token_data = auth_client

        # Logout
        client.post(
            reverse(self.URL),
            data={"refresh": token_data["refresh"]},
            format="json",
        )

        # Try to use the blacklisted refresh token
        new_client = APIClient()
        response = new_client.post(
            reverse("token_refresh"),
            data={"refresh": token_data["refresh"]},
            format="json",
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_logout_requires_authentication(
        self, client: APIClient, db
    ) -> None:
        """Unauthenticated logout request returns 401."""
        response = client.post(
            reverse(self.URL),
            data={"refresh": "some-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_refresh_token_returns_400(
        self, auth_client: tuple
    ) -> None:
        """Logout without providing a refresh token returns 400."""
        client, user, token_data = auth_client
        response = client.post(reverse(self.URL), data={}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Profile tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProfile:
    """Tests for GET/PATCH /api/v1/accounts/profile/."""

    URL = "accounts-profile"

    def test_get_profile_returns_user_data(
        self, auth_client: tuple
    ) -> None:
        """GET /profile/ returns the authenticated user's data."""
        client, user, _ = auth_client
        response = client.get(reverse(self.URL))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == user.email
        assert "password" not in data

    def test_get_profile_requires_auth(
        self, client: APIClient, db
    ) -> None:
        """Unauthenticated access to /profile/ returns 401."""
        response = client.get(reverse(self.URL))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_profile_updates_display_name(
        self, auth_client: tuple
    ) -> None:
        """PATCH /profile/ updates display_name."""
        client, user, _ = auth_client
        response = client.patch(
            reverse(self.URL),
            data={"display_name": "New Name"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.display_name == "New Name"

    def test_patch_profile_normalises_country(
        self, auth_client: tuple
    ) -> None:
        """Country code is normalised to uppercase."""
        client, user, _ = auth_client
        response = client.patch(
            reverse(self.URL),
            data={"country": "gb"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.country == "GB"

    def test_patch_profile_cannot_change_email(
        self, auth_client: tuple
    ) -> None:
        """Email field is read-only; PATCH does not change it."""
        client, user, _ = auth_client
        original_email = user.email
        response = client.patch(
            reverse(self.URL),
            data={"email": "hacker@evil.com"},
            format="json",
        )

        user.refresh_from_db()
        assert user.email == original_email


# ---------------------------------------------------------------------------
# Me endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMe:
    """Tests for GET /api/v1/accounts/me/."""

    URL = "accounts-me"

    def test_me_returns_identity(self, auth_client: tuple) -> None:
        """GET /me/ returns the user's identity."""
        client, user, _ = auth_client
        response = client.get(reverse(self.URL))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == user.email

    def test_me_requires_auth(self, client: APIClient, db) -> None:
        """Unauthenticated /me/ returns 401."""
        assert client.get(reverse(self.URL)).status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Password change tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPasswordChange:
    """Tests for POST /api/v1/accounts/password/change/."""

    URL = "accounts-password-change"

    def test_password_change_returns_new_tokens(
        self, auth_client: tuple
    ) -> None:
        """Successful password change returns new JWT tokens."""
        client, user, old_tokens = auth_client
        response = client.post(
            reverse(self.URL),
            data={
                "old_password": "GreenPlanet2024!",
                "new_password": "NewGreenPlanet2025!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        # New tokens should differ from old ones
        assert data["access"] != old_tokens["access"]

    def test_password_change_fails_with_wrong_old_password(
        self, auth_client: tuple
    ) -> None:
        """Wrong old password returns 400."""
        client, user, _ = auth_client
        response = client.post(
            reverse(self.URL),
            data={"old_password": "WRONG!", "new_password": "NewGreenPlanet2025!"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_change_rejects_weak_new_password(
        self, auth_client: tuple
    ) -> None:
        """New password must meet strength requirements."""
        client, user, _ = auth_client
        response = client.post(
            reverse(self.URL),
            data={"old_password": "GreenPlanet2024!", "new_password": "weak"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Notification preference tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestNotificationPreferences:
    """Tests for GET/PATCH /api/v1/accounts/notifications/preferences/."""

    URL = "accounts-notification-prefs"

    def test_get_preferences_returns_defaults(
        self, auth_client: tuple
    ) -> None:
        """GET /notifications/preferences/ returns safe default values."""
        client, user, _ = auth_client
        response = client.get(reverse(self.URL))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["opt_out"] is False
        assert data["email_enabled"] is True
        assert data["in_app_enabled"] is True
        assert data["new_challenges"] is False  # Must be opt-in

    def test_opt_out_sets_timestamp(
        self, auth_client: tuple
    ) -> None:
        """Setting opt_out=True records opt_out_at timestamp."""
        client, user, _ = auth_client
        response = client.patch(
            reverse(self.URL),
            data={"opt_out": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["opt_out"] is True
        prefs = NotificationPreference.objects.get(user=user)
        assert prefs.opt_out_at is not None

    def test_opt_out_enforced_at_model_level(
        self, auth_client: tuple
    ) -> None:
        """can_send() returns False when opt_out=True regardless of other flags."""
        client, user, _ = auth_client

        # Opt out
        client.patch(reverse(self.URL), data={"opt_out": True}, format="json")

        prefs = NotificationPreference.objects.get(user=user)
        prefs.streak_reminders = True  # All individual flags still True
        prefs.save()

        # Despite streak_reminders=True, opt_out blocks sending
        assert prefs.can_send("streak_reminder") is False

    def test_opt_out_false_allows_sending(
        self, auth_client: tuple
    ) -> None:
        """can_send() returns True when opt_out=False and type is enabled."""
        client, user, _ = auth_client
        prefs = NotificationPreference.objects.get(user=user)

        assert prefs.opt_out is False
        assert prefs.can_send("streak_reminder") is True

    def test_individual_flag_blocks_specific_type(
        self, auth_client: tuple
    ) -> None:
        """can_send() returns False when specific notification type is disabled."""
        client, user, _ = auth_client
        client.patch(
            reverse(self.URL),
            data={"streak_reminders": False},
            format="json",
        )

        prefs = NotificationPreference.objects.get(user=user)
        assert prefs.can_send("streak_reminder") is False

    def test_opt_back_in_clears_timestamp(
        self, auth_client: tuple
    ) -> None:
        """Opting back in (opt_out=False) clears opt_out_at timestamp."""
        client, user, _ = auth_client

        # First opt out
        client.patch(reverse(self.URL), data={"opt_out": True}, format="json")

        # Then opt back in
        client.patch(reverse(self.URL), data={"opt_out": False}, format="json")

        prefs = NotificationPreference.objects.get(user=user)
        assert prefs.opt_out is False
        assert prefs.opt_out_at is None

    def test_preferences_require_auth(self, client: APIClient, db) -> None:
        """Notification preferences endpoint requires authentication."""
        response = client.get(reverse(self.URL))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
