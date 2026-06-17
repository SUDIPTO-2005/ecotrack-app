from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.ai_coach.models import AiUsageStat
from services.ai_coach import AiCoachService


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="coachuser",
        email="coachuser@example.com",
        password="TestPassword123!"
    )

@pytest.fixture
def coach_service():
    return AiCoachService()

def test_get_coaching_tips_no_key(db, test_user, coach_service, monkeypatch):
    # Test fallback triggers when API key is not set
    monkeypatch.setattr("django.conf.settings.ANTHROPIC_API_KEY", "")
    breakdown = [{"category": "transport", "percentage": 50}]

    result = coach_service.get_coaching_tips(test_user, breakdown)
    assert result["was_fallback"] is True
    assert result["model_version"] == "fallback"
    assert len(result["tips"]) > 0

@patch("anthropic.Anthropic")
def test_get_coaching_tips_success(mock_anthropic, db, test_user, coach_service, monkeypatch):
    monkeypatch.setattr("django.conf.settings.ANTHROPIC_API_KEY", "mock-key")

    # Mock Anthropic client messages.create response
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='[{"category": "transport", "recommendation": "Walk", "impact_level": "High"}]')]
    mock_message.usage.input_tokens = 100
    mock_message.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_message

    breakdown = [{"category": "transport", "percentage": 50}]
    result = coach_service.get_coaching_tips(test_user, breakdown)

    assert result["was_fallback"] is False
    assert result["model_version"] == "claude-3-haiku-20240307"
    assert result["tokens_used"] == 150
    assert result["tips"][0]["recommendation"] == "Walk"

def test_chat_with_coach_no_key(db, test_user, coach_service, monkeypatch):
    monkeypatch.setattr("django.conf.settings.ANTHROPIC_API_KEY", "")
    result = coach_service.chat_with_coach(test_user, "hello")
    assert result["was_fallback"] is True
    assert "EcoBot" in result["reply"] or "welcome" in result["reply"].lower()

@patch("anthropic.Anthropic")
def test_chat_with_coach_success(mock_anthropic, db, test_user, coach_service, monkeypatch):
    monkeypatch.setattr("django.conf.settings.ANTHROPIC_API_KEY", "mock-key")

    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="I am your coach.")]
    mock_client.messages.create.return_value = mock_message

    result = coach_service.chat_with_coach(test_user, "hello")
    assert result["was_fallback"] is False
    assert result["reply"] == "I am your coach."
@patch("anthropic.Anthropic")
def test_chat_with_coach_failure_fallback(mock_anthropic, db, test_user, coach_service, monkeypatch):
    # Anthropic client throws an exception
    monkeypatch.setattr("django.conf.settings.ANTHROPIC_API_KEY", "mock-key")

    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.side_effect = Exception("API error")

    result = coach_service.chat_with_coach(test_user, "hello")
    assert result["was_fallback"] is True
    assert "error" in result["reply"]

def test_check_cost_budget(db, coach_service):
    # Reset daily usage stats
    today = timezone.now().date()
    AiUsageStat.objects.filter(date=today).delete()

    # Cost starts under $5.00 limit
    assert coach_service.check_cost_budget() is True

    # Set daily cost above limit
    stat, _ = AiUsageStat.objects.get_or_create(date=today)
    stat.total_cost_usd = Decimal("6.00")
    stat.save()

    assert coach_service.check_cost_budget() is False

def test_record_usage(db, coach_service):
    today = timezone.now().date()
    AiUsageStat.objects.filter(date=today).delete()

    coach_service.record_usage(1000) # 1000 tokens

    stat = AiUsageStat.objects.get(date=today)
    assert stat.total_calls == 1
    assert stat.total_tokens == 1000
    assert stat.total_cost_usd > Decimal("0")
