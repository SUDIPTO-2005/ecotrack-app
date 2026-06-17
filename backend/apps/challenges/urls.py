from django.urls import path
from apps.challenges.views import (
    ChallengeListView,
    ChallengeJoinView,
    ChallengeLeaveView,
    BadgesListView,
    LeaderboardView,
)

urlpatterns = [
    path("", ChallengeListView.as_view(), name="challenges-list"),
    path("<int:pk>/join/", ChallengeJoinView.as_view(), name="challenges-join"),
    path("<int:pk>/leave/", ChallengeLeaveView.as_view(), name="challenges-leave"),
    path("badges/", BadgesListView.as_view(), name="badges-list"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
]
