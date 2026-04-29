from datetime import datetime, timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import SignUpForm, ProfileForm, DailyHealthEntryForm
from .models import Profile, DailyHealthEntry, DailyScore


def home(request):
    """
    I redirect logged-in users straight to the dashboard because the dashboard is
    the main page of the finished application.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


def signup(request):
    """
    I use Django's built-in signup form because it gives secure user creation
    without me having to write password handling manually.
    """
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect("profile_edit")
    else:
        form = SignUpForm()

    return render(request, "signup.html", {"form": form})


@login_required
def profile_edit(request):
    """
    I let the user update profile details because these values are used by the
    scoring engine and the ML recommendation model.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "profile.html", {"form": form})


@login_required
def log_today(request):
    """
    I keep date selection for now because it makes testing and generating history
    easier. In the final deployed version, this can be restricted to today's date.
    """
    today = timezone.localdate()

    if request.method == "POST":
        form = DailyHealthEntryForm(request.POST)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.user = request.user

            existing = DailyHealthEntry.objects.filter(
                user=request.user,
                date=saved.date
            ).first()

            if existing:
                # I update every metric so editing a previous day refreshes both the score and ML advice.
                existing.calories_kcal = saved.calories_kcal
                existing.water_ml = saved.water_ml
                existing.sleep_hours = saved.sleep_hours
                existing.exercise_minutes = saved.exercise_minutes
                existing.steps = saved.steps
                existing.screen_time_hours = saved.screen_time_hours
                existing.stress_level = saved.stress_level
                existing.mood_level = saved.mood_level
                existing.energy_level = saved.energy_level
                existing.fruit_veg_servings = saved.fruit_veg_servings
                existing.protein_grams = saved.protein_grams
                existing.save()
            else:
                saved.save()

            return redirect("dashboard")
    else:
        form = DailyHealthEntryForm(initial={"date": today})

    return render(request, "log_today.html", {"form": form})


def sort_predicted_improvements(predicted_improvements):
    """
    I sort predicted improvements by predicted gain so the most useful ML advice
    appears first on the dashboard.
    """
    if not predicted_improvements:
        return []

    return sorted(
        predicted_improvements.values(),
        key=lambda item: item.get("predicted_gain", 0),
        reverse=True,
    )


@login_required
def dashboard(request):
    """
    The dashboard shows the user's current daily score, ML-led recommendations,
    and a quick recent progress chart.
    """
    today = timezone.localdate()

    score_today = DailyScore.objects.filter(user=request.user, date=today).first()

    last_7 = DailyScore.objects.filter(user=request.user).order_by("-date")[:7]
    last_7 = list(reversed(last_7))

    chart_labels = [s.date.strftime("%d %b") for s in last_7]
    chart_values = [s.overall_score for s in last_7]
    chart_dates = [s.date.strftime("%Y-%m-%d") for s in last_7]

    has_entry_today = DailyHealthEntry.objects.filter(user=request.user, date=today).exists()
    has_score_today = score_today is not None

    reminder = None
    if not has_entry_today and not has_score_today:
        reminder = "Reminder: you haven't logged today's health metrics yet."

    today_improvements = []
    if score_today:
        today_improvements = sort_predicted_improvements(score_today.predicted_improvements)

    return render(
        request,
        "dashboard.html",
        {
            "score_today": score_today,
            "today_improvements": today_improvements,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "chart_dates": chart_dates,
            "reminder": reminder,
        },
    )


@login_required
def history(request):
    """
    I added this page because the final version needs longer-term history, not
    only a short recent dashboard chart.
    """
    today = timezone.localdate()
    selected_range = request.GET.get("range", "30")

    scores = DailyScore.objects.filter(user=request.user).order_by("-date")

    if selected_range in ["7", "30", "90"]:
        days = int(selected_range)
        start_date = today - timedelta(days=days - 1)
        scores = scores.filter(date__gte=start_date, date__lte=today)

    scores = list(scores)

    chart_scores = list(reversed(scores))
    chart_labels = [s.date.strftime("%d %b %Y") for s in chart_scores]
    chart_values = [s.overall_score for s in chart_scores]
    chart_dates = [s.date.strftime("%Y-%m-%d") for s in chart_scores]

    average_score = None
    best_score = None
    lowest_score = None

    if scores:
        values = [s.overall_score for s in scores]
        average_score = round(sum(values) / len(values), 1)
        best_score = max(values)
        lowest_score = min(values)

    return render(
        request,
        "history.html",
        {
            "scores": scores,
            "selected_range": selected_range,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "chart_dates": chart_dates,
            "average_score": average_score,
            "best_score": best_score,
            "lowest_score": lowest_score,
        },
    )


@login_required
def view_day(request, date: str):
    """
    I let users open a specific historical day so they can review both the score
    and the recommendations that were generated for that date.
    """
    chosen_date = datetime.strptime(date, "%Y-%m-%d").date()

    score = DailyScore.objects.filter(user=request.user, date=chosen_date).first()
    entry = DailyHealthEntry.objects.filter(user=request.user, date=chosen_date).first()

    improvements = []
    if score:
        improvements = sort_predicted_improvements(score.predicted_improvements)

    return render(
        request,
        "view_day.html",
        {
            "score": score,
            "entry": entry,
            "improvements": improvements,
            "chosen_date": chosen_date,
        },
    )