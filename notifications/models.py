from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        DEADLINE = "deadline", "Deadline Reminder"
        STUDY_SESSION = "study_session", "Study Session Reminder"
        OVERDUE = "overdue", "Overdue Alert"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-app"
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="notifications",
    )
    study_session = models.ForeignKey(
        "planner.StudySession",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="notifications",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    title = models.CharField(max_length=160)
    message = models.TextField()
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-scheduled_for", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "assessment", "study_session", "kind", "channel", "scheduled_for"),
                name="unique_notification_event",
            )
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"
