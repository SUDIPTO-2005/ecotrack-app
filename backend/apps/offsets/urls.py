from django.urls import path

from apps.offsets.views import OffsetProjectDetailView, OffsetProjectListView

urlpatterns = [
    path("", OffsetProjectListView.as_view(), name="offsets-list"),
    path("<int:pk>/", OffsetProjectDetailView.as_view(), name="offsets-detail"),
]
