"""
Badge awarding service for EcoTrack.

Centralises all badge criteria checks and award logic.
Called from calculator and challenge views after key user actions.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from apps.accounts.models import User

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Badge definitions — these match the data seeded by the seed_badges command
# ──────────────────────────────────────────────────────────────────────────────

BADGE_DEFINITIONS = [
    {
        "name": "First Step",
        "description": "Calculated your carbon footprint for the first time. Every journey starts with a single step! 🌱",
        "icon": "🌱",
        "criteria": {"type": "first_calculation"},
    },
    {
        "name": "Detail Oriented",
        "description": "Used the Detailed Calculator mode for a deeper, more accurate footprint breakdown. 🔬",
        "icon": "🔬",
        "criteria": {"type": "first_detailed_calculation"},
    },
    {
        "name": "Challenge Accepted",
        "description": "Joined your first community challenge. Teamwork makes the dream work! 🤝",
        "icon": "🤝",
        "criteria": {"type": "first_challenge_joined"},
    },
    {
        "name": "Streak Starter",
        "description": "Maintained a 3-day challenge streak. Consistency is key! 🔥",
        "icon": "🔥",
        "criteria": {"type": "streak_days", "min_days": 3},
    },
    {
        "name": "Eco Warrior",
        "description": "Maintained a 7-day challenge streak — a full week of impact! ⚔️",
        "icon": "⚔️",
        "criteria": {"type": "streak_days", "min_days": 7},
    },
    {
        "name": "Multi-Tracker",
        "description": "Logged 5 or more footprint calculations — you're tracking like a pro! 📊",
        "icon": "📊",
        "criteria": {"type": "calculation_count", "min_count": 5},
    },
    {
        "name": "Carbon Cutter",
        "description": "Joined 3 or more challenges — fighting climate change on all fronts! ✂️",
        "icon": "✂️",
        "criteria": {"type": "challenge_count", "min_count": 3},
    },
    {
        "name": "Low Carbon Hero",
        "description": "Calculated a footprint under 2,000 kg CO₂e per year — impressively green! 🦸",
        "icon": "🦸",
        "criteria": {"type": "low_footprint_annual_kg", "max_kg": 2000},
    },
    {
        "name": "EcoBot Fan",
        "description": "Chatted with EcoBot for the first time. Knowledge is power! 🤖",
        "icon": "🤖",
        "criteria": {"type": "first_chat"},
    },
]


def _award_badge(user: "User", badge_name: str) -> bool:
    """
    Award a badge to a user if they don't already have it.

    Returns True if newly awarded, False if already had it.
    """
    from apps.challenges.models import Badge, UserBadge

    try:
        badge = Badge.objects.get(name=badge_name)
    except Badge.DoesNotExist:
        logger.warning(f"Badge '{badge_name}' not found in DB — run seed_badges first.")
        return False

    _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
    if created:
        logger.info(f"🏅 Awarded badge '{badge_name}' to {user.email}")
    return created


def check_and_award_on_calculation(user: "User", mode: str) -> list[str]:
    """
    Check and award badges after a footprint calculation.

    Args:
        user: The user who just calculated.
        mode: 'quick' or 'detailed'

    Returns:
        List of newly awarded badge names.
    """
    from apps.calculator.models import FootprintEntry

    awarded = []
    entry_count = FootprintEntry.objects.filter(user=user).count()

    # First calculation ever
    if entry_count == 1:
        if _award_badge(user, "First Step"):
            awarded.append("First Step")

    # First detailed calculation
    if mode == "detailed":
        detailed_count = FootprintEntry.objects.filter(user=user, mode="detailed").count()
        if detailed_count == 1:
            if _award_badge(user, "Detail Oriented"):
                awarded.append("Detail Oriented")

    # 5+ calculations
    if entry_count >= 5:
        if _award_badge(user, "Multi-Tracker"):
            awarded.append("Multi-Tracker")

    # Low carbon hero: annualise the most recent entry and check
    try:
        latest = FootprintEntry.objects.filter(user=user).latest("date")
        if latest.period_days and latest.period_days > 0:
            annual_kg = float(latest.total_co2e_kg) * (365 / latest.period_days)
            if annual_kg < 2000:
                if _award_badge(user, "Low Carbon Hero"):
                    awarded.append("Low Carbon Hero")
    except FootprintEntry.DoesNotExist:
        pass

    return awarded


def check_and_award_on_challenge_join(user: "User") -> list[str]:
    """
    Check and award badges after a user joins a challenge.

    Returns:
        List of newly awarded badge names.
    """
    from apps.challenges.models import ChallengeParticipant

    awarded = []
    joined_count = ChallengeParticipant.objects.filter(user=user).count()

    # First challenge
    if joined_count == 1:
        if _award_badge(user, "Challenge Accepted"):
            awarded.append("Challenge Accepted")

    # 3+ challenges
    if joined_count >= 3:
        if _award_badge(user, "Carbon Cutter"):
            awarded.append("Carbon Cutter")

    return awarded


def check_and_award_on_streak(user: "User", streak_days: int) -> list[str]:
    """
    Check and award streak-based badges.

    Returns:
        List of newly awarded badge names.
    """
    awarded = []

    if streak_days >= 3:
        if _award_badge(user, "Streak Starter"):
            awarded.append("Streak Starter")

    if streak_days >= 7:
        if _award_badge(user, "Eco Warrior"):
            awarded.append("Eco Warrior")

    return awarded


def check_and_award_on_chat(user: "User") -> list[str]:
    """Award EcoBot Fan badge on first chat."""
    awarded = []
    if _award_badge(user, "EcoBot Fan"):
        awarded.append("EcoBot Fan")
    return awarded
