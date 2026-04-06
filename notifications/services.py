from datetime import datetime, timedelta

from django.utils import timezone

from assessments.models import Assessment
from notifications.models import Notification
from planner.models import PlannerSettings, StudySession


def _session_datetime(session):
    return timezone.make_aware(datetime.combine(session.session_date, session.start_time))


def create_notification(*, user, kind, title, message, scheduled_for, assessment=None, study_session=None):
    notification, created = Notification.objects.get_or_create(
        user=user,
        assessment=assessment,
        study_session=study_session,
        kind=kind,
        channel=Notification.Channel.IN_APP,
        scheduled_for=scheduled_for,
        defaults={"title": title, "message": message, "sent_at": timezone.now()},
    )
    if created and notification.sent_at is None:
        notification.sent_at = timezone.now()
        notification.save(update_fields=["sent_at"])
    return notification, created


def run_notification_checks(now=None):
    now = now or timezone.now()
    settings_obj = PlannerSettings.get_solo()
    created_count = 0

    assessments = Assessment.objects.exclude(status__in=[Assessment.Status.SUBMITTED, Assessment.Status.COMPLETED]).select_related(
        "user", "user__profile", "subject"
    )
    for assessment in assessments:
        profile = assessment.user.profile
        if not profile.reminder_enabled:
            continue
        lead_hours = profile.deadline_reminder_hours or settings_obj.deadline_reminder_hours
        reminder_time = assessment.due_at - timedelta(hours=lead_hours)
        if reminder_time <= now <= assessment.due_at:
            _, created = create_notification(
                user=assessment.user,
                assessment=assessment,
                kind=Notification.Kind.DEADLINE,
                title=f"Deadline approaching: {assessment.title}",
                message=f"{assessment.subject.subject_name} is due at {timezone.localtime(assessment.due_at):%d %b %Y %H:%M}.",
                scheduled_for=reminder_time,
            )
            created_count += int(created)
        if assessment.due_at < now:
            _, created = create_notification(
                user=assessment.user,
                assessment=assessment,
                kind=Notification.Kind.OVERDUE,
                title=f"Overdue: {assessment.title}",
                message=f"{assessment.title} is overdue. Update its status or regenerate your plan.",
                scheduled_for=assessment.due_at,
            )
            created_count += int(created)

    sessions = StudySession.objects.filter(status=StudySession.Status.SCHEDULED).select_related("study_plan__user", "assessment", "subject")
    for session in sessions:
        user = session.study_plan.user
        profile = user.profile
        if not profile.reminder_enabled:
            continue
        reminder_minutes = profile.reminder_lead_minutes or settings_obj.study_session_reminder_minutes
        session_start = _session_datetime(session)
        reminder_time = session_start - timedelta(minutes=reminder_minutes)
        if reminder_time <= now <= session_start:
            _, created = create_notification(
                user=user,
                study_session=session,
                assessment=session.assessment,
                kind=Notification.Kind.STUDY_SESSION,
                title=f"Study session soon: {session.session_title or (session.assessment.title if session.assessment else 'Study session')}",
                message=f"{session.subject.subject_name} starts at {session.start_time:%H:%M} for {session.duration_minutes} minutes.",
                scheduled_for=reminder_time,
            )
            created_count += int(created)

    return created_count
