"""
Views for the dashboard app (Phase 3).

Exposes dashboard endpoints for retrieving:
- Footprint history: GET /api/v1/dashboard/history/
- Footprint trends (time series): GET /api/v1/dashboard/trends/
- Comparison with national/global averages: GET /api/v1/dashboard/compare/
- Dynamic annual projection bounds: GET /api/v1/dashboard/projection/
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Sum
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calculator.models import FootprintCategory, FootprintEntry
from apps.calculator.serializers import (
    AnnualProjectionSerializer,
    FootprintResultSerializer,
)
from services.calculator_service import CalculatorService


class HistoryView(APIView):
    """GET /api/v1/dashboard/history/ — Paginated footprint history for the user."""

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """Get list of historical footprint entries."""
        entries = FootprintEntry.objects.filter(user=request.user).order_by("-date", "-created_at")

        # Simple page number pagination
        page = self.request.query_params.get("page", 1)
        try:
            page = int(page)
        except ValueError:
            page = 1

        page_size = 20
        start = (page - 1) * page_size
        end = start + page_size

        count = entries.count()
        results = entries[start:end]

        serializer = FootprintResultSerializer(results, many=True)
        return Response({
            "count": count,
            "next": f"/api/v1/dashboard/history/?page={page + 1}" if end < count else None,
            "previous": f"/api/v1/dashboard/history/?page={page - 1}" if page > 1 else None,
            "results": serializer.data
        })


class TrendsView(APIView):
    """GET /api/v1/dashboard/trends/ — Time-series trends of carbon emissions."""

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """Get time-series trends grouped by category or month."""
        # Retrieve entries for the last 12 months
        cutoff = date.today() - timedelta(days=365)
        entries = FootprintEntry.objects.filter(user=request.user, date__gte=cutoff).order_by("date")

        history_data = []
        category_breakdown = {}

        # Aggregate category totals overall in the cutoff period
        categories = FootprintCategory.objects.filter(entry__user=request.user, entry__date__gte=cutoff)
        totals = categories.values("category").annotate(total_co2e=Sum("co2e_kg"))

        for total in totals:
            category_breakdown[total["category"]] = total["total_co2e"]

        for entry in entries:
            history_data.append({
                "id": entry.id,
                "date": entry.date.isoformat(),
                "total_co2e_kg": entry.total_co2e_kg,
                "total_co2e_tonnes": entry.total_co2e_tonnes,
                "mode": entry.mode,
            })

        return Response({
            "time_series": history_data,
            "overall_category_breakdown_kg": category_breakdown,
        })


class ComparisonView(APIView):
    """GET /api/v1/dashboard/compare/ — Compare user's footprint against national/global averages."""

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """Retrieve comparison figures."""
        user = request.user

        # User average annualised CO2e (kg) from recent calculations
        latest_entry = FootprintEntry.objects.filter(user=user).order_by("-date").first()
        user_annualised_tonnes = float(latest_entry.annualised_co2e_kg / 1000) if latest_entry else 0.0

        country_code = user.country or "IN"

        # Query synced NationalAverageDataset baseline averages
        from apps.data_sync.models import NationalAverageDataset

        country_names = {
            "IN": "India", "US": "United States", "GB": "United Kingdom",
            "DE": "Germany", "FR": "France", "CN": "China", "AU": "Australia",
            "CA": "Canada", "JP": "Japan", "BR": "Brazil",
        }
        country_name = country_names.get(country_code, country_code)

        db_average = NationalAverageDataset.objects.filter(
            country_code=country_code
        ).order_by("-year").first()

        if db_average:
            national_avg = float(db_average.per_capita_co2e_tonnes)
        else:
            # Simple national average mock mapping fallback
            national_averages = {
                "IN": 1.9,
                "US": 14.9,
                "GB": 4.7,
                "DE": 7.9,
            }
            national_avg = national_averages.get(country_code, 4.5)

        # Query global average ('WRL') from DB or fallback
        world_average = NationalAverageDataset.objects.filter(
            country_code="WRL"
        ).order_by("-year").first()

        global_avg = float(world_average.per_capita_co2e_tonnes) if world_average else 4.5

        return Response({
            "user_annualised_tonnes": user_annualised_tonnes,
            "country_code": country_code,
            "country_name": country_name,
            "national_average_tonnes": national_avg,
            "global_average_tonnes": global_avg,
            "paris_agreement_target_tonnes": 2.0,
        })


class ProjectionView(APIView):
    """GET /api/v1/dashboard/projection/ — Annual projection with dynamic confidence intervals."""

    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        """Get the projected annual footprint based on the user's latest footprint entry."""
        latest_entry = FootprintEntry.objects.filter(user=request.user).order_by("-date").first()
        if not latest_entry:
            return Response(
                {"error": {"code": "no_data", "message": "No calculations found to project from."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        svc = CalculatorService()
        projection = svc._compute_annual_projection(latest_entry.total_co2e_kg, latest_entry.period_days)

        return Response({
            "latest_entry_id": latest_entry.id,
            "latest_entry_date": latest_entry.date.isoformat(),
            "projection": AnnualProjectionSerializer(projection).data
        })
