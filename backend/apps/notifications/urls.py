from django.urls import path
from apps.notifications.views import (
    NotificationListView,
    NotificationReadView,
    NotificationReadAllView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications-list"),
    path("<int:pk>/read/", NotificationReadView.as_view(), name="notifications-read"),
    path("read-all/", NotificationReadAllView.as_view(), name="notifications-read-all"),
]
