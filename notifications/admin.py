from django.contrib import admin

from notifications.models import Notification
from notifications.services import run_notification_checks


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "kind", "channel", "scheduled_for", "sent_at", "is_read")
    list_filter = ("kind", "channel", "is_read")
    search_fields = ("title", "message", "user__username")
    actions = ["simulate_notifications"]

    @admin.action(description="Run notification simulation")
    def simulate_notifications(self, request, queryset):
        created = run_notification_checks()
        self.message_user(request, f"Created {created} notification(s).")
