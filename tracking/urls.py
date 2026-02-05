from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile_edit, name="profile_edit"),

    # I keep /log/ but allow selecting a date for demo/testing.
    path("log/", views.log_today, name="log_today"),

    path("dashboard/", views.dashboard, name="dashboard"),

    # NEW: view score + advice for a chosen date (for demoing historical advice)
    path("day/<str:date>/", views.view_day, name="view_day"),
]