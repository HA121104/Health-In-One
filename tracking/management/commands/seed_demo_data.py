from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from social.models import Friendship
from tracking.models import DailyHealthEntry, Profile


class Command(BaseCommand):
    help = "Create demo users and historical health data for testing and final project demonstration."

    def handle(self, *args, **options):
        """
        I use a management command for demo data because users should not be able
        to create fake past/future entries through the normal website.

        This keeps the final user-facing app realistic while still allowing me
        to generate history data for testing, screenshots, reports and demos.
        """
        self.stdout.write("Creating demo data...")

        demo_users = self.create_demo_users()
        self.create_friendships(demo_users)
        self.create_health_entries(demo_users)

        self.stdout.write(self.style.SUCCESS("Demo data created successfully."))

    def create_demo_users(self):
        """
        I create a few demo accounts so the leaderboard and friends system can be
        tested without manually signing up multiple users each time.
        """
        users_data = [
            {
                "username": "demo_user",
                "email": "demo@example.com",
                "password": "demo12345",
                "profile": {
                    "age": 22,
                    "height_cm": 175,
                    "weight_kg": 72,
                    "activity_level": Profile.ActivityLevel.MODERATE,
                    "health_goal": Profile.HealthGoal.FITNESS,
                },
            },
            {
                "username": "active_friend",
                "email": "active@example.com",
                "password": "demo12345",
                "profile": {
                    "age": 25,
                    "height_cm": 180,
                    "weight_kg": 78,
                    "activity_level": Profile.ActivityLevel.ACTIVE,
                    "health_goal": Profile.HealthGoal.MUSCLE_GAIN,
                },
            },
            {
                "username": "casual_friend",
                "email": "casual@example.com",
                "password": "demo12345",
                "profile": {
                    "age": 21,
                    "height_cm": 168,
                    "weight_kg": 65,
                    "activity_level": Profile.ActivityLevel.LIGHT,
                    "health_goal": Profile.HealthGoal.GENERAL,
                },
            },
        ]

        created_users = []

        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={"email": data["email"]},
            )

            # I reset the password each time so the demo login details always work.
            user.set_password(data["password"])
            user.email = data["email"]
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)

            for field, value in data["profile"].items():
                setattr(profile, field, value)

            profile.save()
            created_users.append(user)

            if created:
                self.stdout.write(f"Created user: {user.username}")
            else:
                self.stdout.write(f"Updated user: {user.username}")

        return created_users

    def create_friendships(self, users):
        """
        I create accepted friendships so the friends-only leaderboard has useful
        data immediately after running this command.
        """
        main_user = users[0]

        for friend in users[1:]:
            friendship, _ = Friendship.objects.get_or_create(
                requester=main_user,
                addressee=friend,
                defaults={"status": Friendship.Status.ACCEPTED},
            )

            friendship.status = Friendship.Status.ACCEPTED
            friendship.save()

        self.stdout.write("Created accepted friendships for demo_user.")

    def create_health_entries(self, users):
        """
        I create 60 days of health entries for each demo user.

        Saving each DailyHealthEntry automatically triggers the Django signal,
        which creates the DailyScore and ML-led recommendations.
        """
        today = timezone.localdate()
        random.seed(42)

        for user in users:
            profile = user.profile

            for days_ago in range(59, -1, -1):
                entry_date = today - timedelta(days=days_ago)

                metrics = self.generate_metrics(profile, days_ago)

                entry, created = DailyHealthEntry.objects.update_or_create(
                    user=user,
                    date=entry_date,
                    defaults=metrics,
                )

                if created:
                    self.stdout.write(f"Created entry: {user.username} - {entry_date}")

    def generate_metrics(self, profile, days_ago):
        """
        I generate realistic but slightly varied metrics so the graphs and ML
        recommendations look believable rather than perfectly random.

        The values differ depending on activity level so each demo user has a
        distinct pattern.
        """
        activity = profile.activity_level

        if activity == Profile.ActivityLevel.ACTIVE:
            base_steps = 12000
            base_exercise = 60
            base_calories = 2700
        elif activity == Profile.ActivityLevel.MODERATE:
            base_steps = 8500
            base_exercise = 40
            base_calories = 2300
        elif activity == Profile.ActivityLevel.LIGHT:
            base_steps = 6000
            base_exercise = 25
            base_calories = 2100
        else:
            base_steps = 4000
            base_exercise = 15
            base_calories = 2000

        # I add a weekly rhythm so the generated data looks more realistic.
        weekday_factor = 1.15 if days_ago % 7 in [1, 2, 3, 4] else 0.85

        calories = int(random.normalvariate(base_calories, 350))
        water = int(random.normalvariate(2400, 650))
        sleep = round(random.normalvariate(7.4, 1.2), 1)
        exercise = int(random.normalvariate(base_exercise * weekday_factor, 20))
        steps = int(random.normalvariate(base_steps * weekday_factor, 2500))
        screen_time = round(random.normalvariate(6.0, 2.0), 1)
        stress = int(random.normalvariate(5, 2))
        mood = int(random.normalvariate(7, 2))
        energy = int(random.normalvariate(7, 2))
        fruit_veg = int(random.normalvariate(5, 2))
        protein = int(random.normalvariate(110, 35))

        return {
            # I clamp each value so generated entries stay inside the model validators.
            "calories_kcal": self.clamp_int(calories, 0, 8000),
            "water_ml": self.clamp_int(water, 0, 8000),
            "sleep_hours": self.clamp_float(sleep, 0, 16),
            "exercise_minutes": self.clamp_int(exercise, 0, 300),
            "steps": self.clamp_int(steps, 0, 60000),
            "screen_time_hours": self.clamp_float(screen_time, 0, 24),
            "stress_level": self.clamp_int(stress, 1, 10),
            "mood_level": self.clamp_int(mood, 1, 10),
            "energy_level": self.clamp_int(energy, 1, 10),
            "fruit_veg_servings": self.clamp_int(fruit_veg, 0, 15),
            "protein_grams": self.clamp_int(protein, 0, 350),
        }

    def clamp_int(self, value, minimum, maximum):
        """
        I clamp generated integer values because the database model has validators
        and I want the seed command to run without validation issues.
        """
        return max(minimum, min(maximum, int(value)))

    def clamp_float(self, value, minimum, maximum):
        """
        I clamp generated decimal values for the same reason as integer values:
        the demo data must remain valid and realistic.
        """
        return max(minimum, min(maximum, float(value)))