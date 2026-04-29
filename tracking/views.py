from datetime import datetime

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import SignUpForm, ProfileForm, DailyHealthEntryForm
from .models import Profile, DailyHealthEntry, DailyScore


def home(request):
    """
    I redirect logged-in users to the dashboard so the app feels quicker to use.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


def signup(request):
    """
    I use Django's built-in signup form because it handles secure user creation.
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
    I allow the user to update profile data because the final ML model needs
    user context such as age, height, weight, activity level and health goal.
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
    I allow date selection for development/testing so I can quickly generate
    multiple days of history. In the final deployed version this can be locked
    to today's date if needed.
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
                # I update every metric so re-saving a past day correctly refreshes the score/advice.
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


@login_required
def dashboard(request):
    """
    The dashboard shows today's score, recommendations and historical chart data.
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

    return render(
        request,
        "dashboard.html",
        {
            "score_today": score_today,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "chart_dates": chart_dates,
            "reminder": reminder,
        },
    )


@login_required
def view_day(request, date: str):
    """
    I allow users to view a previous day's score and advice from history.
    """
    chosen_date = datetime.strptime(date, "%Y-%m-%d").date()

    score = DailyScore.objects.filter(user=request.user, date=chosen_date).first()

    return render(
        request,
        "view_day.html",
        {
            "score": score,
            "chosen_date": chosen_date,
        },
    )