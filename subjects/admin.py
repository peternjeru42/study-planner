from django.contrib import admin

from subjects.models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("subject_name", "subject_code", "user", "semester", "instructor_name")
    search_fields = ("subject_name", "subject_code", "user__username")
    list_filter = ("semester",)
