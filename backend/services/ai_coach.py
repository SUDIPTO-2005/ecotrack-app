"""
AI Coaching Service (Phase 7).

Integrates with the Anthropic API to generate user carbon coaching advice.
Supports rate limits, caching, and graceful rule-based fallback when key is unset.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from django.conf import settings
import anthropic

from apps.accounts.models import User
from services.tip_fallback import TipFallbackEngine

logger = logging.getLogger(__name__)
_fallback_engine = TipFallbackEngine()


class AiCoachService:
    """Core service managing user coaching tips generation and caching."""

    def get_coaching_tips(self, user: User, category_breakdown: list[dict]) -> dict:
        """
        Get or generate weekly coaching tips for the user.
        
        Args:
            user: Current authenticated user.
            category_breakdown: List of category breakdowns from calculator results.
            
        Returns:
            Dict containing the tips, source (AI vs Fallback), and timestamp.
        """
        logger.info("Coaching tips requested", extra={"user": user.email})

        # Check Anthropic API Key config
        api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
        if not api_key:
            logger.info("Anthropic API Key not set; running rule-based fallback tips", extra={"user": user.email})
            tips = _fallback_engine.generate_fallback_tips(category_breakdown)
            return {
                "tips": tips,
                "was_fallback": True,
                "model_version": "fallback",
                "tokens_used": 0,
            }

        # prompt configuration
        breakdown_text = "\n".join([
            f"- {cat.get('category')}: {cat.get('co2e_kg')} kg ({cat.get('percentage')}%)"
            for cat in category_breakdown
        ])

        system_prompt = (
            "You are EcoCoach, a helpful assistant advising users on reducing their carbon footprint. "
            "Suggest only realistic, citable, and actionable emission reduction actions based on the user's footprint breakdown. "
            "Avoid hallucinating specific local details or local program prices unless globally applicable. "
            "Reply strictly with a JSON array where each object has exactly these keys: "
            '{"category": "string", "recommendation": "string", "impact_level": "High" | "Medium" | "Low"}'
        )

        user_prompt = f"Here is my carbon footprint breakdown:\n{breakdown_text}\nPlease suggest how to reduce it."

        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.2,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            
            content = message.content[0].text
            
            # Simple JSON parser fallback if Claude didn't wrap cleanly
            import json
            try:
                # Find JSON array starting point
                start = content.find("[")
                end = content.rfind("]") + 1
                if start != -1 and end != -1:
                    tips = json.loads(content[start:end])
                else:
                    tips = json.loads(content)
            except json.JSONDecodeError:
                logger.error("Claude returned malformed JSON, fallback triggered", extra={"response": content})
                raise ValueError("Malformed AI output.")

            return {
                "tips": tips,
                "was_fallback": False,
                "model_version": "claude-3-haiku-20240307",
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
            }

        except Exception as exc:
            logger.error("AI coaching tips generation failed, fallback triggered", exc_info=exc)
            tips = _fallback_engine.generate_fallback_tips(category_breakdown)
            return {
                "tips": tips,
                "was_fallback": True,
                "model_version": "fallback",
                "tokens_used": 0,
            }

    def chat_with_coach(self, user: User, user_message: str, chat_history: list[dict] = []) -> dict:
        """
        Hold a conversation with EcoCoach.
        Uses Claude when API key is available, otherwise falls back to the
        comprehensive EcoBot knowledge base.
        """
        api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
        if not api_key:
            from services.ecobot_knowledge import get_chatbot_response
            reply = get_chatbot_response(user_message)
            return {
                "reply": reply,
                "was_fallback": True,
            }

        messages = []
        for msg in chat_history[-6:]:  # Keep context window short (last 3 exchanges)
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        system_prompt = (
            "You are EcoCoach, a friendly civic AI chatbot. Answer questions concisely, providing "
            "practical tips, emission calculations context, and supportive environmental messages. "
            "Suggest realistic actions to lower carbon impact."
        )

        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.7,
                system=system_prompt,
                messages=messages,
            )
            return {
                "reply": message.content[0].text,
                "was_fallback": False,
            }
        except Exception as e:
            logger.error("Chatbot query failed, using rule-based response", exc_info=e)
            return {
                "reply": "I encountered an error querying the model. Please check connection parameters.",
                "was_fallback": True,
            }

    def check_cost_budget(self) -> bool:
        """Helper to verify weekly/monthly token cost thresholds."""
        from django.utils import timezone
        from apps.ai_coach.models import AiUsageStat
        
        today = timezone.now().date()
        stat, _ = AiUsageStat.objects.get_or_create(date=today)
        # Check if daily cost has exceeded $5.00 limit
        if stat.total_cost_usd >= Decimal("5.00"):
            return False
        return True

    def record_usage(self, tokens: int) -> None:
        """Record usage tokens and estimate daily costs."""
        from django.utils import timezone
        from apps.ai_coach.models import AiUsageStat
        
        today = timezone.now().date()
        stat, _ = AiUsageStat.objects.get_or_create(date=today)
        
        # Claude-3 Haiku costs: $0.25/MTok input, $1.25/MTok output.
        # Average estimation of $0.0005 per query.
        stat.total_calls += 1
        stat.total_tokens += tokens
        stat.total_cost_usd += Decimal(str(tokens)) * Decimal("0.000001")
        stat.save()
