from django.contrib import admin
from .models import Profile, DailyHealthEntry, DailyScore

admin.site.register(Profile)
admin.site.register(DailyHealthEntry)
admin.site.register(DailyScore)