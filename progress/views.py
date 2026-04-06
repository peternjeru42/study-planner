from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from assessments.models import Assessment
from planner.models import StudySession
from planner.services import generate_plan
from progress.services import refresh_progress_snapshot


@login_required
@require_POST
def session_status_update_view(request, pk):
    session = get_object_or_404(StudySession, pk=pk, study_plan__user=request.user)
    status = request.POST.get("status")
    if status not in StudySession.Status.values:
        return JsonResponse({"error": "Invalid status."}, status=400)
    session.status = status
    session.save(update_fields=["status", "updated_at"])
    if status == StudySession.Status.MISSED:
        generate_plan(request.user, trigger_reason="session_missed")
    refresh_progress_snapshot(request.user)
    return JsonResponse({"status": "ok", "session_status": session.status})


@login_required
@require_POST
def assessment_status_update_view(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk, user=request.user)
    status = request.POST.get("status")
    if status not in Assessment.Status.values:
        return JsonResponse({"error": "Invalid status."}, status=400)
    assessment.status = status
    assessment.completed_at = timezone.now() if status in [Assessment.Status.SUBMITTED, Assessment.Status.COMPLETED] else None
    assessment.save(update_fields=["status", "completed_at", "updated_at"])
    generate_plan(request.user, trigger_reason="assessment_status_changed")
    refresh_progress_snapshot(request.user)
    return JsonResponse({"status": "ok", "assessment_status": assessment.status})
