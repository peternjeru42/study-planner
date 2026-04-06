from django.contrib import admin

from accounts.models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "year_of_study", "daily_study_goal_hours", "reminder_enabled")
    search_fields = ("user__username", "user__email", "course")
