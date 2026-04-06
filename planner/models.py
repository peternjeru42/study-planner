from django.conf import settings
from django.db import models


class PlannerSettings(models.Model):
    urgency_weight = models.DecimalField(max_digits=4, decimal_places=2, default=0.40)
    assessment_weight = models.DecimalField(max_digits=4, decimal_places=2, default=0.25)
    effort_weight = models.DecimalField(max_digits=4, decimal_places=2, default=0.20)
    progress_gap_weight = models.DecimalField(max_digits=4, decimal_places=2, default=0.15)
    default_session_minutes = models.PositiveIntegerField(default=60)
    overload_threshold_minutes = models.PositiveIntegerField(default=180)
    deadline_reminder_hours = models.PositiveIntegerField(default=24)
    study_session_reminder_minutes = models.PositiveIntegerField(default=60)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Planner settings"

    @classmethod
    def get_solo(cls):
        settings_obj, _ = cls.objects.get_or_create(pk=1)
        return settings_obj

    def __str__(self):
        return "Planner Settings"


class StudyPlan(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_plans")
    title = models.CharField(max_length=160, default="AI Study Plan")
    prompt_text = models.TextField(blank=True)
    weekly_hours_goal = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    focus_subject = models.ForeignKey(
        "subjects.Subject",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="study_plans",
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    trigger_reason = models.CharField(max_length=60, default="manual")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-generated_at",)

    def __str__(self):
        return f"{self.user.username} plan {self.date_range_start} - {self.date_range_end}"


class StudySession(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        MISSED = "missed", "Missed"

    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name="sessions")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="study_sessions")
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="study_sessions",
        blank=True,
        null=True,
    )
    session_title = models.CharField(max_length=180, blank=True)
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    priority_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    order_index = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("session_date", "start_time", "order_index")

    def __str__(self):
        return f"{self.session_title or (self.assessment.title if self.assessment else 'Study session')} on {self.session_date}"


class PlannerLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="planner_logs")
    trigger_reason = models.CharField(max_length=60)
    generated_at = models.DateTimeField(auto_now_add=True)
    success_status = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-generated_at",)

    def __str__(self):
        return f"{self.user.username} {self.trigger_reason} @ {self.generated_at:%Y-%m-%d %H:%M}"
