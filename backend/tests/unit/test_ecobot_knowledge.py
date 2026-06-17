import pytest
from services.ecobot_knowledge import get_chatbot_response

def test_get_chatbot_response_exact_patterns():
    # Test transport category
    res = get_chatbot_response("tell me about fly and flight emissions")
    assert "Aviation & Carbon" in res

    # Test car category
    res = get_chatbot_response("car and drive emissions")
    assert "Car & Driving Emissions" in res

    # Test food category
    res = get_chatbot_response("eating meat and vegan diet")
    assert "Food & Diet Emissions" in res

def test_get_chatbot_response_keyword_fallbacks():
    # Test "carbon" fallback to "footprint"
    res = get_chatbot_response("carbon emissions")
    assert "understanding your carbon footprint" in res.lower()

    # Test "reduce" fallback to "tip"
    res = get_chatbot_response("how to reduce footprint")
    assert "top 10 actions to reduce" in res.lower()

def test_get_chatbot_response_generic_fallback():
    # Test generic query fallback
    res = get_chatbot_response("some totally random message")
    assert "Great question! I'm EcoBot, your carbon coach" in res
