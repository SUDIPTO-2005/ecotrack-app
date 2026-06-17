from django.urls import path
from apps.data_sync.views import GovDataSyncWebhookView

urlpatterns = [
    path("sync/national-averages/", GovDataSyncWebhookView.as_view(), name="data-sync-national-averages"),
]
