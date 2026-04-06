from django.conf import settings
from django.db import models
from django.utils import timezone


class Assessment(models.Model):
    class AssessmentType(models.TextChoices):
        ASSIGNMENT = "assignment", "Assignment"
        QUIZ = "quiz", "Quiz"
        CAT = "cat", "CAT"
        EXAM = "exam", "Exam"
        PROJECT = "project", "Project"
        PRESENTATION = "presentation", "Presentation"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assessments")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="assessments")
    title = models.CharField(max_length=180)
    assessment_type = models.CharField(max_length=20, choices=AssessmentType.choices, default=AssessmentType.ASSIGNMENT)
    due_at = models.DateTimeField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("due_at", "title")

    def __str__(self):
        return self.title

    @property
    def is_done(self):
        return self.status in {self.Status.SUBMITTED, self.Status.COMPLETED}

    @property
    def is_overdue(self):
        return not self.is_done and self.due_at < timezone.now()
