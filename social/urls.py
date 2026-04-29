from django.urls import path
from . import views

urlpatterns = [
    # I keep the leaderboard separate from friend management so the social app stays organised.
    path("leaderboard/", views.leaderboard, name="leaderboard"),

    # I added a friends page because the final version needs a way to add users before comparing scores.
    path("friends/", views.friends, name="friends"),

    # These routes handle the friend request workflow.
    path("friends/send/<int:user_id>/", views.send_friend_request, name="send_friend_request"),
    path("friends/accept/<int:friendship_id>/", views.accept_friend_request, name="accept_friend_request"),
    path("friends/decline/<int:friendship_id>/", views.decline_friend_request, name="decline_friend_request"),
    path("friends/remove/<int:friendship_id>/", views.remove_friend, name="remove_friend"),
]