from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from assessments.models import Assessment
from notifications.models import Notification
from planner.forms import PlanPromptForm
from planner.models import StudyPlan, StudySession
from progress.services import compute_metrics, refresh_progress_snapshot


@login_required
def home_view(request):
    today = timezone.localdate()
    active_plan = StudyPlan.objects.filter(user=request.user, status=StudyPlan.Status.ACTIVE).prefetch_related("sessions").first()
    today_sessions = StudySession.objects.filter(
        study_plan__user=request.user,
        study_plan__status=StudyPlan.Status.ACTIVE,
        session_date=today,
    ).select_related("subject", "assessment")
    upcoming_deadlines = Assessment.objects.filter(user=request.user).exclude(
        status__in=[Assessment.Status.SUBMITTED, Assessment.Status.COMPLETED]
    )[:6]
    notifications = Notification.objects.filter(user=request.user)[:8]
    metrics = compute_metrics(request.user, reference_date=today)
    subject_progress = []
    for subject in request.user.subjects.all():
        total = subject.assessments.count()
        completed = subject.assessments.filter(status__in=[Assessment.Status.SUBMITTED, Assessment.Status.COMPLETED]).count()
        subject_progress.append(
            {"subject": subject, "percentage": int((completed / total) * 100) if total else 0, "pending": total - completed}
        )

    return render(
        request,
        "dashboard/home.html",
        {
            "active_plan": active_plan,
            "today_sessions": today_sessions,
            "upcoming_deadlines": upcoming_deadlines,
            "notifications": notifications,
            "metrics": metrics,
            "subject_progress": subject_progress,
            "assessment_status_choices": Assessment.Status.choices,
            "prompt_form": PlanPromptForm(request.user),
        },
    )


@login_required
def metrics_json(request):
    refresh_progress_snapshot(request.user)
    return JsonResponse(compute_metrics(request.user))


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, "dashboard/notifications.html", {"notifications": notifications})


@login_required
def notification_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect(request.GET.get("next") or "dashboard:notifications")
