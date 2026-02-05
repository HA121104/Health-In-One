from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import render
from django.utils import timezone

from tracking.models import DailyScore


@login_required
def leaderboard(request):
    """
    I rank users by the average score over the last 7 calendar days.
    """
    today = timezone.localdate()
    start = today - timedelta(days=6)

    leaderboard = (
        DailyScore.objects
        .filter(date__gte=start, date__lte=today)
        .values("user__username")
        .annotate(avg_score=Avg("overall_score"))
        .order_by("-avg_score")
    )

    return render(request, "leaderboard.html", {"leaderboard": leaderboard})