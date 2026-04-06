from datetime import time

from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    course = models.CharField(max_length=120, blank=True)
    year_of_study = models.PositiveSmallIntegerField(default=1)
    preferred_study_start_time = models.TimeField(default=time(hour=18))
    preferred_study_end_time = models.TimeField(default=time(hour=21))
    daily_study_goal_hours = models.DecimalField(max_digits=4, decimal_places=1, default=2.0)
    break_duration_minutes = models.PositiveIntegerField(default=15)
    reminder_enabled = models.BooleanField(default=True)
    reminder_lead_minutes = models.PositiveIntegerField(default=30)
    deadline_reminder_hours = models.PositiveIntegerField(default=24)
    timezone = models.CharField(max_length=64, default="Africa/Nairobi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} profile"
