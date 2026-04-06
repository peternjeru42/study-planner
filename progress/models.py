from django.conf import settings
from django.db import models


class ProgressSnapshot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress_snapshots")
    week_start = models.DateField()
    completed_tasks = models.PositiveIntegerField(default=0)
    pending_tasks = models.PositiveIntegerField(default=0)
    study_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    deadline_compliance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    study_sessions_completed = models.PositiveIntegerField(default=0)
    tasks_completed_on_time = models.PositiveIntegerField(default=0)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-week_start",)
        unique_together = ("user", "week_start")

    def __str__(self):
        return f"{self.user.username} snapshot {self.week_start}"
