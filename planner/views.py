from collections import OrderedDict
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from assessments.models import Assessment
from planner.models import StudyPlan, StudySession
from planner.services import generate_plan


def _group_sessions(plan):
    grouped = OrderedDict()
    if not plan:
        return grouped
    for session in plan.sessions.select_related("subject", "assessment"):
        grouped.setdefault(session.session_date, []).append(session)
    return grouped


@login_required
def weekly_plan_view(request):
    plan = StudyPlan.objects.filter(user=request.user, is_active=True).prefetch_related("sessions__subject", "sessions__assessment").first()
    return render(request, "planner/weekly_plan.html", {"plan": plan, "grouped_sessions": _group_sessions(plan)})


@login_required
def daily_plan_view(request, plan_date=None):
    current_date = datetime.strptime(plan_date, "%Y-%m-%d").date() if plan_date else None
    current_date = current_date or timezone.localdate()
    sessions = StudySession.objects.filter(study_plan__user=request.user, session_date=current_date).select_related(
        "subject", "assessment"
    )
    return render(request, "planner/daily_plan.html", {"plan_date": current_date, "sessions": sessions})


@login_required
def calendar_view(request):
    return render(request, "planner/calendar.html")


@login_required
def calendar_events_view(request):
    user = request.user
    assessment_events = [
        {
            "title": f"Deadline: {assessment.title}",
            "start": assessment.due_at.isoformat(),
            "url": f"/assessments/{assessment.pk}/edit/",
            "color": assessment.subject.color_tag,
        }
        for assessment in Assessment.objects.filter(user=user).select_related("subject")
    ]
    session_events = [
        {
            "title": f"Study: {session.assessment.title}",
            "start": datetime.combine(session.session_date, session.start_time).isoformat(),
            "end": datetime.combine(session.session_date, session.end_time).isoformat(),
            "color": session.subject.color_tag,
        }
        for session in StudySession.objects.filter(study_plan__user=user).select_related("subject", "assessment")
    ]
    return JsonResponse(assessment_events + session_events, safe=False)


@login_required
@require_POST
def generate_plan_view(request):
    plan = generate_plan(request.user, trigger_reason="manual_regeneration")
    messages.success(request, "Study plan generated.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": "ok", "plan_id": plan.pk, "notes": plan.notes})
    return redirect("planner:weekly")
