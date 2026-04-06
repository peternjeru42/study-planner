from django.contrib import admin

from notifications.services import run_notification_checks
from planner.models import PlannerLog, PlannerSettings, StudyPlan, StudySession
from planner.services import generate_plan


@admin.action(description="Regenerate plans for selected users")
def regenerate_plans(modeladmin, request, queryset):
    user_ids = queryset.values_list("user_id", flat=True).distinct()
    generated = 0
    for user_id in user_ids:
        plan = queryset.filter(user_id=user_id).first()
        if plan:
            generate_plan(plan.user, trigger_reason="admin_regeneration")
            generated += 1
    modeladmin.message_user(request, f"Regenerated {generated} plan(s).")


@admin.register(PlannerSettings)
class PlannerSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "urgency_weight",
        "assessment_weight",
        "effort_weight",
        "progress_gap_weight",
        "default_session_minutes",
    )


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "generated_at", "date_range_start", "date_range_end", "trigger_reason", "is_active")
    list_filter = ("is_active", "trigger_reason")
    search_fields = ("user__username",)
    actions = [regenerate_plans]


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ("assessment", "session_date", "start_time", "duration_minutes", "status", "priority_score")
    list_filter = ("status", "session_date")
    search_fields = ("assessment__title", "study_plan__user__username")


@admin.register(PlannerLog)
class PlannerLogAdmin(admin.ModelAdmin):
    list_display = ("user", "trigger_reason", "generated_at", "success_status")
    list_filter = ("success_status", "trigger_reason")
    search_fields = ("user__username", "notes")
    actions = ["run_notifications"]

    @admin.action(description="Run reminder simulation now")
    def run_notifications(self, request, queryset):
        created = run_notification_checks()
        self.message_user(request, f"Created {created} reminder(s).")
