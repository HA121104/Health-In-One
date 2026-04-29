from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from tracking.models import DailyScore
from .models import Friendship


def get_friendship_between(user, other_user):
    """
    I use this helper to find an existing friendship/request in either direction.

    This matters because user A could send a request to user B, or user B could
    send one to user A. I want the app to recognise both as the same relationship.
    """
    return Friendship.objects.filter(
        Q(requester=user, addressee=other_user) |
        Q(requester=other_user, addressee=user)
    ).first()


def get_accepted_friendships(user):
    """
    I keep this helper so both the friends page and leaderboard can reuse the
    same definition of an accepted friendship.
    """
    return Friendship.objects.filter(
        Q(requester=user) | Q(addressee=user),
        status=Friendship.Status.ACCEPTED,
    )


def get_friend_user_ids(user):
    """
    I return the user IDs of accepted friends.

    A friendship can store the current user as requester or addressee, so I check
    both sides and return the opposite user each time.
    """
    friend_ids = set()

    for friendship in get_accepted_friendships(user):
        if friendship.requester_id == user.id:
            friend_ids.add(friendship.addressee_id)
        else:
            friend_ids.add(friendship.requester_id)

    return friend_ids


@login_required
def friends(request):
    """
    I created this page so users can search for other users, send friend requests,
    accept requests and manage their friends before using the leaderboard.
    """
    query = request.GET.get("q", "").strip()
    search_results = []

    if query:
        users = (
            User.objects
            .filter(Q(username__icontains=query) | Q(email__icontains=query))
            .exclude(id=request.user.id)
            .order_by("username")[:10]
        )

        for user in users:
            friendship = get_friendship_between(request.user, user)

            if not friendship:
                status_text = "Not friends"
                can_send = True
            elif friendship.status == Friendship.Status.ACCEPTED:
                status_text = "Already friends"
                can_send = False
            elif friendship.requester_id == request.user.id:
                status_text = "Request sent"
                can_send = False
            else:
                status_text = "Request received"
                can_send = False

            search_results.append({
                "user": user,
                "status_text": status_text,
                "can_send": can_send,
            })

    pending_received = Friendship.objects.filter(
        addressee=request.user,
        status=Friendship.Status.PENDING,
    ).select_related("requester")

    pending_sent = Friendship.objects.filter(
        requester=request.user,
        status=Friendship.Status.PENDING,
    ).select_related("addressee")

    accepted_friendships = get_accepted_friendships(request.user).select_related("requester", "addressee")

    friends_list = []
    for friendship in accepted_friendships:
        if friendship.requester_id == request.user.id:
            friend_user = friendship.addressee
        else:
            friend_user = friendship.requester

        friends_list.append({
            "friendship": friendship,
            "user": friend_user,
        })

    return render(
        request,
        "friends.html",
        {
            "query": query,
            "search_results": search_results,
            "pending_received": pending_received,
            "pending_sent": pending_sent,
            "friends_list": friends_list,
        },
    )


@login_required
def send_friend_request(request, user_id):
    """
    I only allow friend requests through POST so a request is not accidentally
    created just by opening a link.
    """
    if request.method != "POST":
        return redirect("friends")

    other_user = get_object_or_404(User, id=user_id)

    if other_user == request.user:
        messages.error(request, "You cannot add yourself as a friend.")
        return redirect("friends")

    existing = get_friendship_between(request.user, other_user)

    if existing:
        if existing.status == Friendship.Status.ACCEPTED:
            messages.info(request, "You are already friends with this user.")
        elif existing.addressee_id == request.user.id:
            # I accept the reverse request if the other user already sent one.
            existing.status = Friendship.Status.ACCEPTED
            existing.save()
            messages.success(request, "Friend request accepted.")
        else:
            messages.info(request, "A friend request has already been sent.")
    else:
        Friendship.objects.create(
            requester=request.user,
            addressee=other_user,
            status=Friendship.Status.PENDING,
        )
        messages.success(request, f"Friend request sent to {other_user.username}.")

    return redirect("friends")


@login_required
def accept_friend_request(request, friendship_id):
    """
    I allow the receiving user to accept a pending friend request.
    """
    if request.method != "POST":
        return redirect("friends")

    friendship = get_object_or_404(
        Friendship,
        id=friendship_id,
        addressee=request.user,
        status=Friendship.Status.PENDING,
    )

    friendship.status = Friendship.Status.ACCEPTED
    friendship.save()

    messages.success(request, f"You are now friends with {friendship.requester.username}.")
    return redirect("friends")


@login_required
def decline_friend_request(request, friendship_id):
    """
    I delete declined requests instead of storing another status because this is
    simpler and keeps the MVP/final feature easy to maintain.
    """
    if request.method != "POST":
        return redirect("friends")

    friendship = get_object_or_404(
        Friendship,
        id=friendship_id,
        addressee=request.user,
        status=Friendship.Status.PENDING,
    )

    friendship.delete()

    messages.info(request, "Friend request declined.")
    return redirect("friends")


@login_required
def remove_friend(request, friendship_id):
    """
    I remove the friendship record when a user removes a friend.

    This keeps the relationship simple: if the record is deleted, they are no
    longer connected and no longer appear on each other's leaderboard.
    """
    if request.method != "POST":
        return redirect("friends")

    friendship = get_object_or_404(
        Friendship.objects.filter(
            Q(requester=request.user) | Q(addressee=request.user),
            id=friendship_id,
            status=Friendship.Status.ACCEPTED,
        )
    )

    friendship.delete()

    messages.info(request, "Friend removed.")
    return redirect("friends")


@login_required
def leaderboard(request):
    """
    I rank the current user and their accepted friends by average score.

    I use the most recent 7 saved scores for each person so the leaderboard
    rewards consistency while still working even if users have not logged every day.
    """
    user_ids = get_friend_user_ids(request.user)
    user_ids.add(request.user.id)

    users = User.objects.filter(id__in=user_ids).order_by("username")

    rows = []

    for user in users:
        scores = DailyScore.objects.filter(user=user).order_by("-date")[:7]

        if not scores:
            rows.append({
                "username": user.username,
                "avg": None,
                "score_count": 0,
                "is_current_user": user.id == request.user.id,
            })
            continue

        average = sum(score.overall_score for score in scores) / len(scores)

        rows.append({
            "username": user.username,
            "avg": round(average, 1),
            "score_count": len(scores),
            "is_current_user": user.id == request.user.id,
        })

    # I put users with scores first, then rank by average score.
    rows.sort(
        key=lambda row: (
            row["avg"] is not None,
            row["avg"] if row["avg"] is not None else -1,
        ),
        reverse=True,
    )

    return render(request, "leaderboard.html", {"rows": rows})