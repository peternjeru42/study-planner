from django.contrib import admin

from progress.models import ProgressSnapshot


@admin.register(ProgressSnapshot)
class ProgressSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "week_start", "completed_tasks", "pending_tasks", "study_hours", "completion_rate")
    list_filter = ("week_start",)
    search_fields = ("user__username",)
