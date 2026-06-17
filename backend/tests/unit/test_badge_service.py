import pytest
from decimal import Decimal
from django.utils import timezone
from apps.accounts.models import User
from apps.challenges.models import Badge, UserBadge
from apps.calculator.models import FootprintEntry
from apps.challenges.models import ChallengeParticipant, Challenge
from services.badge_service import (
    check_and_award_on_calculation,
    check_and_award_on_challenge_join,
    check_and_award_on_streak,
    check_and_award_on_chat,
    _award_badge
)

@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="badgesuser",
        email="badgesuser@example.com",
        password="TestPassword123!"
    )

@pytest.fixture
def seed_badges_db(db):
    badges = [
        "First Step", "Detail Oriented", "Challenge Accepted", 
        "Streak Starter", "Eco Warrior", "Multi-Tracker", 
        "Carbon Cutter", "Low Carbon Hero", "EcoBot Fan"
    ]
    for b in badges:
        Badge.objects.get_or_create(name=b, defaults={"description": "Test badge", "icon": "🏅", "criteria": {"type": "dummy"}})

def test_award_badge_nonexistent(test_user):
    # Testing nonexistent badge error logging
    assert not _award_badge(test_user, "Nonexistent Badge")

def test_check_and_award_on_calculation(db, test_user, seed_badges_db):
    # 1. Test first calculation ever
    FootprintEntry.objects.create(user=test_user, total_co2e_kg=Decimal("1500"), period_days=365, mode="quick")
    new_badges = check_and_award_on_calculation(test_user, mode="quick")
    assert "First Step" in new_badges
    assert "Low Carbon Hero" in new_badges  # 1500 kg/yr is < 2000

    # 2. Test first detailed calculation
    FootprintEntry.objects.create(user=test_user, total_co2e_kg=Decimal("3000"), period_days=365, mode="detailed")
    new_badges = check_and_award_on_calculation(test_user, mode="detailed")
    assert "Detail Oriented" in new_badges

    # 3. Add more to get to 5+ calculations
    for _ in range(3):
        FootprintEntry.objects.create(user=test_user, total_co2e_kg=Decimal("4000"), period_days=365, mode="quick")
    new_badges = check_and_award_on_calculation(test_user, mode="quick")
    assert "Multi-Tracker" in new_badges

def test_check_and_award_on_challenge_join(db, test_user, seed_badges_db):
    # Prepare challenges
    c1 = Challenge.objects.create(title="C1", category="energy", start_date=timezone.now().date(), end_date=timezone.now().date(), target_reduction_pct=10)
    c2 = Challenge.objects.create(title="C2", category="energy", start_date=timezone.now().date(), end_date=timezone.now().date(), target_reduction_pct=10)
    c3 = Challenge.objects.create(title="C3", category="energy", start_date=timezone.now().date(), end_date=timezone.now().date(), target_reduction_pct=10)

    # Join first challenge
    ChallengeParticipant.objects.create(user=test_user, challenge=c1)
    new_badges = check_and_award_on_challenge_join(test_user)
    assert "Challenge Accepted" in new_badges

    # Join 2 more challenges
    ChallengeParticipant.objects.create(user=test_user, challenge=c2)
    ChallengeParticipant.objects.create(user=test_user, challenge=c3)
    new_badges = check_and_award_on_challenge_join(test_user)
    assert "Carbon Cutter" in new_badges

def test_check_and_award_on_streak(db, test_user, seed_badges_db):
    # Test streak under 3
    assert not check_and_award_on_streak(test_user, 2)

    # Test streak >= 3
    new_badges = check_and_award_on_streak(test_user, 3)
    assert "Streak Starter" in new_badges

    # Test streak >= 7
    new_badges = check_and_award_on_streak(test_user, 7)
    assert "Eco Warrior" in new_badges

def test_check_and_award_on_chat(db, test_user, seed_badges_db):
    new_badges = check_and_award_on_chat(test_user)
    assert "EcoBot Fan" in new_badges
