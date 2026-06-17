from django.urls import path

from apps.ai_coach.views import CoachingTipsView, EcoChatView

urlpatterns = [
    path("tips/", CoachingTipsView.as_view(), name="ai-coach-tips"),
    path("chat/", EcoChatView.as_view(), name="ai-coach-chat"),
]
