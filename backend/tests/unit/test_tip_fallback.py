import pytest

from services.tip_fallback import TipFallbackEngine


@pytest.fixture
def engine():
    return TipFallbackEngine()

def test_generate_fallback_tips_with_all_categories(engine):
    breakdown = [
        {"category": "transport", "percentage": 40},
        {"category": "energy", "percentage": 25},
        {"category": "diet", "percentage": 15},
        {"category": "consumption", "percentage": 12},
        {"category": "waste", "percentage": 11}
    ]

    tips = engine.generate_fallback_tips(breakdown)
    assert len(tips) == 5

    categories = [t["category"] for t in tips]
    assert categories == ["transport", "energy", "diet", "consumption", "waste"]
    assert tips[0]["impact_level"] == "High"
    assert tips[4]["impact_level"] == "Low"

def test_generate_fallback_tips_below_threshold(engine):
    # Categories under 10% should be skipped
    breakdown = [
        {"category": "transport", "percentage": 5},
        {"category": "energy", "percentage": 8}
    ]

    tips = engine.generate_fallback_tips(breakdown)
    assert len(tips) == 1
    assert tips[0]["category"] == "general"
    assert tips[0]["impact_level"] == "Low"
