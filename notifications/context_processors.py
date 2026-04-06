from notifications.models import Notification


def notification_summary(request):
    if request.user.is_authenticated:
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        recent = Notification.objects.filter(user=request.user).select_related("assessment", "study_session")[:5]
        return {"unread_notification_count": unread, "recent_notifications": recent}
    return {"unread_notification_count": 0, "recent_notifications": []}
