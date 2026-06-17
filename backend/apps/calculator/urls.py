from django.urls import path
from apps.calculator.views import QuickEstimateView, DetailedEstimateView

urlpatterns = [
    path("estimate/", QuickEstimateView.as_view(), name="calculator-estimate"),
    path("detailed/", DetailedEstimateView.as_view(), name="calculator-detailed"),
]
