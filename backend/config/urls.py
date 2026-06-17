"""EcoTrack root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # JWT auth
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # App routes (registered as apps are built in later phases)
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/calculator/", include("apps.calculator.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/challenges/", include("apps.challenges.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/ai-coach/", include("apps.ai_coach.urls")),
    path("api/v1/offsets/", include("apps.offsets.urls")),
    path("api/v1/internal/", include("apps.data_sync.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
