from django.urls import path
from apps.accounts.views import (
    RegisterView,
    LoginView,
    LogoutView,
    MeView,
    ProfileView,
    PasswordChangeView,
    NotificationPreferenceView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", LoginView.as_view(), name="accounts-login"),
    path("logout/", LogoutView.as_view(), name="accounts-logout"),
    path("me/", MeView.as_view(), name="accounts-me"),
    path("profile/", ProfileView.as_view(), name="accounts-profile"),
    path("password/change/", PasswordChangeView.as_view(), name="accounts-password-change"),
    path("notifications/preferences/", NotificationPreferenceView.as_view(), name="accounts-notification-prefs"),
]
