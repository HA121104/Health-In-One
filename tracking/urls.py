from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile_edit, name="profile_edit"),
    path("log/", views.log_today, name="log_today"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # I added a full history page so users can view more than just the recent chart.
    path("history/", views.history, name="history"),

    # I keep this route so users can open a specific day's score and recommendations.
    path("day/<str:date>/", views.view_day, name="view_day"),
]