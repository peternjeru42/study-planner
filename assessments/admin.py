from django.contrib import admin

from assessments.models import Assessment


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "user", "assessment_type", "due_at", "status", "weight")
    list_filter = ("assessment_type", "status")
    search_fields = ("title", "subject__subject_name", "user__username")
