from django.urls import path

from apps.calculator.views import DetailedEstimateView, QuickEstimateView

urlpatterns = [
    path("estimate/", QuickEstimateView.as_view(), name="calculator-estimate"),
    path("detailed/", DetailedEstimateView.as_view(), name="calculator-detailed"),
]
