from django.urls import path
from apps.dashboard.views import HistoryView, TrendsView, ComparisonView, ProjectionView

urlpatterns = [
    path("history/", HistoryView.as_view(), name="dashboard-history"),
    path("trends/", TrendsView.as_view(), name="dashboard-trends"),
    path("compare/", ComparisonView.as_view(), name="dashboard-compare"),
    path("projection/", ProjectionView.as_view(), name="dashboard-projection"),
]
