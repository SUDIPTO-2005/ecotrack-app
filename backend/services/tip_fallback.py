"""
Rule-based recommendation engine for the AI Coach fallback channel (Phase 7).

Generates evidence-based, actionable reduction tips without external model calls.
"""
from __future__ import annotations

from decimal import Decimal


class TipFallbackEngine:
    """Generates structured advice based on user's highest footprint categories."""

    def generate_fallback_tips(self, category_breakdown: list[dict]) -> list[dict]:
        """
        Produce a list of structured reduction actions sorted by categories.

        Args:
            category_breakdown: List of category dict elements containing percentage and co2e_kg values.

        Returns:
            List of tips dict items containing 'category', 'action', and 'impact'.
        """
        tips = []

        # Sort breakdown by percentage descending
        sorted_cats = sorted(
            category_breakdown,
            key=lambda x: Decimal(str(x.get("percentage", 0))),
            reverse=True
        )

        for cat in sorted_cats:
            cat_name = cat.get("category")
            pct = float(cat.get("percentage", 0))

            if pct <= 10.0:
                continue

            if cat_name == "transport":
                tips.append({
                    "category": "transport",
                    "recommendation": "Consider combining car trips, carpooling, or swapping local drives for walking/cycling.",
                    "impact_level": "High"
                })
            elif cat_name == "energy":
                tips.append({
                    "category": "energy",
                    "recommendation": "Unplug vampire appliances, switch to LED lightbulbs, and check thermostatic thresholds.",
                    "impact_level": "Medium"
                })
            elif cat_name == "diet":
                tips.append({
                    "category": "diet",
                    "recommendation": "Incorporate more plant-based meals into your weekly diet (e.g., Meatless Mondays).",
                    "impact_level": "High"
                })
            elif cat_name == "consumption":
                tips.append({
                    "category": "consumption",
                    "recommendation": "Extend the lifespan of your electronic items and opt for thrift/second-hand clothing.",
                    "impact_level": "Medium"
                })
            elif cat_name == "waste":
                tips.append({
                    "category": "waste",
                    "recommendation": "Set up dedicated organic waste compost piles and audit your recycling stream accuracy.",
                    "impact_level": "Low"
                })

        # Return at least a default tip if user has a very low footprint
        if not tips:
            tips.append({
                "category": "general",
                "recommendation": "Keep tracking your carbon footprint periodically to maintain your low emissions profile.",
                "impact_level": "Low"
            })

        return tips
