from django.db import models
from django.contrib.auth.models import User


class Friendship(models.Model):
    """
    Minimal friendship model for the MVP.
    I’m keeping it simple so I can get the leaderboard working quickly.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_requests")
    addressee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_requests")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("requester", "addressee")