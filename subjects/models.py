from django.conf import settings
from django.db import models


class Subject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subjects")
    subject_name = models.CharField(max_length=150)
    subject_code = models.CharField(max_length=30, blank=True)
    instructor_name = models.CharField(max_length=120, blank=True)
    semester = models.CharField(max_length=60, blank=True)
    class_schedule = models.CharField(max_length=255, blank=True)
    color_tag = models.CharField(max_length=7, default="#2C7A7B")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("subject_name",)
        unique_together = ("user", "subject_name", "subject_code")

    def __str__(self):
        return self.subject_name
