from datetime import datetime

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import SignUpForm, ProfileForm, DailyHealthEntryForm
from .models import Profile, DailyHealthEntry, DailyScore


def home(request):
    """
    Simple landing page.
    I redirect logged-in users straight to the dashboard to save clicks.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


def signup(request):
    """
    Basic signup page.
    I create the user and log them in immediately so they can start using the app.
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
    Profile editing page (weight + activity level).
    I keep it minimal for interim MVP but it still enables personalised scoring.
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
    Daily entry form.

    For demo/testing I allow choosing the date in the form,
    but the dashboard 'today' score will always show the real current date.
    """
    today = timezone.localdate()

    # I pre-fill today's entry if it exists so the user can update it quickly.
    entry = DailyHealthEntry.objects.filter(user=request.user, date=today).first()

    if request.method == "POST":
        # I allow posting with any date for demo/testing.
        form = DailyHealthEntryForm(request.POST)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.user = request.user

            # I enforce update-or-create for the selected date to avoid duplicates.
            existing = DailyHealthEntry.objects.filter(user=request.user, date=saved.date).first()
            if existing:
                existing.calories_kcal = saved.calories_kcal
                existing.water_ml = saved.water_ml
                existing.sleep_hours = saved.sleep_hours
                existing.exercise_minutes = saved.exercise_minutes
                existing.save()  # triggers signals -> DailyScore update_or_create
            else:
                saved.save()  # triggers signals -> DailyScore update_or_create

            return redirect("dashboard")
    else:
        # Default the date picker to today for normal use.
        form = DailyHealthEntryForm(initial={"date": today})

    return render(request, "log_today.html", {"form": form})


@login_required
def dashboard(request):
    """
    Dashboard page:
    - shows today's overall score + advice
    - shows last 7 days chart
    - allows clicking a day on the chart to view that day's advice
    """
    today = timezone.localdate()

    score_today = DailyScore.objects.filter(user=request.user, date=today).first()

    last_7 = DailyScore.objects.filter(user=request.user).order_by("-date")[:7]
    last_7 = list(reversed(last_7))

    chart_labels = [s.date.strftime("%d %b") for s in last_7]
    chart_values = [s.overall_score for s in last_7]
    chart_dates = [s.date.strftime("%Y-%m-%d") for s in last_7]

    # I treat "logged today" as having either an entry OR a score for today's date.
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
    View a specific day's overall score and recommendations.
    This supports the demo feature: 'view previous days advice'.
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